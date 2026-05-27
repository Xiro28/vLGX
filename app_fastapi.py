import base64
import io
import os
import uuid
from pathlib import Path
from typing import Optional, Dict

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from src.lgx import LGX
import pypdfium2 as pdfium
from PIL import Image


# Modelli Pydantic
class UploadResponse(BaseModel):
    session_id: str
    total_pages: int
    status: str


class PageResponse(BaseModel):
    page_id: int
    result: Optional[str] = None
    status: str
    message: Optional[str] = None


class SessionInfo(BaseModel):
    session_id: str
    total_pages: int
    pages_processed: int
    progress: str


# Configurazione FastAPI
app = FastAPI(
    title="PDF Analyzer API",
    description="API per analizzare PDF con LGX",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurazione
UPLOAD_FOLDER = "./uploads"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Crea cartella uploads se non esiste
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

# Dizionario per mantenere lo stato dei PDF in elaborazione
pdf_sessions: Dict = {}

# Inizializza LGX
lgx_instance = LGX(
    "behaviour/behaviour.lgx.yml",
    "applications/lgx.yml",
    "gemma4:31b"
)


def pdf_to_images(pdf_path: str, dpi: int = 300) -> list:
    """Converte PDF in lista di immagini PIL"""
    try:
        pdf = pdfium.PdfDocument(pdf_path)
        images = []
        scale = dpi / 72

        for page in pdf:
            bitmap = page.render(scale=scale)
            img = bitmap.to_pil()
            images.append(img.convert("RGB"))

        return images
    except Exception as e:
        raise Exception(f"Errore nella lettura del PDF: {str(e)}")


def image_to_base64(image: Image.Image) -> str:
    """Converte immagine PIL a base64 JPEG"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG", quality=90)
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "sessions_active": len(pdf_sessions)
    }


@app.post("/upload_pdf", response_model=UploadResponse, tags=["Upload"])
async def upload_pdf(pdf: UploadFile = File(...)):
    """
    Endpoint per caricare un PDF
    
    Returns:
        - session_id: ID univoco della sessione
        - total_pages: Numero di pagine del PDF (escludendo le prime 2)
        - status: "success" se tutto va bene
    
    Raises:
        HTTPException 400: File non valido
        HTTPException 413: File troppo grande
    """
    try:
        # Verifica il tipo di file
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Il file deve essere un PDF"
            )
        
        # Verifica la dimensione del file
        content = await pdf.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File troppo grande. Massimo: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Salva il file
        session_id = str(uuid.uuid4())
        filename = f"{session_id}_{pdf.filename}"
        pdf_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(pdf_path, "wb") as f:
            f.write(content)
        
        # Converte PDF in immagini
        try:
            all_images = pdf_to_images(pdf_path)
            images = all_images[2:] if len(all_images) > 2 else []
        except Exception as e:
            os.remove(pdf_path)
            raise HTTPException(
                status_code=400,
                detail=f"Errore nell'elaborazione del PDF: {str(e)}"
            )
        
        if not images:
            os.remove(pdf_path)
            raise HTTPException(
                status_code=400,
                detail="Il PDF non contiene pagine valide dopo le prime 2"
            )
        
        # Inizializza la sessione
        pdf_sessions[0] = {
            'pdf_path': pdf_path,
            'images': images,
            'results': {},
            'current_page': 0,
            'total_pages': len(images)
        }
        
        return UploadResponse(
            session_id=0,
            total_pages=len(images),
            status="success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore server: {str(e)}"
        )


@app.get("/get_page/{session_id}/{page_id}", response_model=PageResponse, tags=["Analysis"])
async def get_page(session_id: str, page_id: int):
    """
    Endpoint per ottenere l'analisi di una pagina
    
    Args:
        session_id: ID della sessione (dalla risposta di upload_pdf)
        page_id: Numero della pagina (0-indexed)
    
    Returns:
        - page_id: Numero della pagina
        - result: Testo dell'analisi (o null se non ancora elaborato)
        - status: "success" se elaborato, "completed" se tutte le pagine sono finite
        - message: Messaggio aggiuntivo
    
    Raises:
        HTTPException 404: Sessione non trovata
        HTTPException 400: ID pagina non valido
    """
    try:
        # Verifica che la sessione esista
        if session_id not in pdf_sessions:
            raise HTTPException(
                status_code=404,
                detail="Sessione non trovata"
            )
        
        session = pdf_sessions[session_id]
        total_pages = session['total_pages']
        
        # Se la pagina è fuori range
        if page_id >= total_pages:
            return PageResponse(
                page_id=-1,
                result=None,
                status="completed",
                message="Tutte le pagine sono state elaborate"
            )
        
        if page_id < 0:
            raise HTTPException(
                status_code=400,
                detail="ID pagina non valido"
            )
        
        # Se il risultato è già stato calcolato, ritornalo subito
        if page_id in session['results']:
            return PageResponse(
                page_id=page_id,
                result=session['results'][page_id],
                status="success"
            )
        
        # Elabora la pagina
        try:
            image = session['images'][page_id]
            base64_image = image_to_base64(image)
            
            # Costruisci il prompt usando i risultati precedenti
            previous_results = []
            for i in range(page_id):
                if i in session['results']:
                    previous_results.append(session['results'][i])
            
            prompt = "Describe the actions being performed in this image."
            if previous_results:
                prompt += "\n" + "\n".join(previous_results)
            
            # Esegui l'inferenza
            result = lgx_instance.infer_step(prompt, base64_image).extracted_preds
            
            # Salva il risultato
            session['results'][page_id] = result
            
            return PageResponse(
                page_id=page_id,
                result=result,
                status="success"
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Errore nell'elaborazione della pagina: {str(e)}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore server: {str(e)}"
        )


@app.get("/session/{session_id}", response_model=SessionInfo, tags=["Session"])
async def get_session_info(session_id: str):
    """
    Endpoint per ottenere informazioni sulla sessione
    
    Returns:
        - session_id: ID della sessione
        - total_pages: Numero totale di pagine
        - pages_processed: Numero di pagine elaborate
        - progress: Progresso in formato "X/Y"
    """
    try:
        if session_id not in pdf_sessions:
            raise HTTPException(
                status_code=404,
                detail="Sessione non trovata"
            )
        
        session = pdf_sessions[session_id]
        
        return SessionInfo(
            session_id=session_id,
            total_pages=session['total_pages'],
            pages_processed=len(session['results']),
            progress=f"{len(session['results'])}/{session['total_pages']}"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore server: {str(e)}"
        )


@app.delete("/session/{session_id}", tags=["Session"])
async def delete_session(session_id: str):
    """
    Endpoint per eliminare una sessione e liberare le risorse
    
    Returns:
        - status: "success" se l'operazione è riuscita
        - message: Messaggio di conferma
    """
    try:
        if session_id not in pdf_sessions:
            raise HTTPException(
                status_code=404,
                detail="Sessione non trovata"
            )
        
        session = pdf_sessions[session_id]
        
        # Elimina il file PDF
        if os.path.exists(session['pdf_path']):
            os.remove(session['pdf_path'])
        
        # Elimina la sessione
        del pdf_sessions[session_id]
        
        return {
            "status": "success",
            "message": "Sessione eliminata"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore server: {str(e)}"
        )


@app.get("/sessions", tags=["Session"])
async def list_sessions():
    """
    Endpoint per ottenere la lista di tutte le sessioni attive
    
    Returns:
        - count: Numero di sessioni attive
        - sessions: Lista di sessioni con info base
    """
    return {
        "count": len(pdf_sessions),
        "sessions": [
            {
                "session_id": sid,
                "total_pages": session['total_pages'],
                "pages_processed": len(session['results'])
            }
            for sid, session in pdf_sessions.items()
        ]
    }


@app.get("/", tags=["Root"])
async def root():
    """Endpoint root con informazioni API"""
    return {
        "name": "PDF Analyzer API",
        "version": "1.0.0",
        "description": "API per analizzare PDF con LGX",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler personalizzato per HTTPException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app_fastapi:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
