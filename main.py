import os 

from src.lgx import LGX
from src.core.predicate.predicate_container import PredicateContainer


if __name__ == "__main__":

    os.environ["LGX_SKIP_OLLAMA"] = "true"
    
    lgx_instance = LGX(
        "behaviour/behaviour.lgx.yml",
        "applications/lgx.yml",
        "gemma4:e2b"
    )

    PredicateContainer.add_predicate('step(5).')
    PredicateContainer.add_predicate('step(6).')
    PredicateContainer.add_predicate('main_action(5, "The user needs to click on the Submit button to complete the form submission process.").')

    previous_step = "Describe the actions being performed in this image."
    #for item in range():
    prompt = previous_step
    result = lgx_instance.infer_step(prompt, "./test_3.jpg").inferred_preds
    print(result)
