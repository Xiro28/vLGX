from src.lgx import LGX

if __name__ == "__main__":

    lgx_instance = LGX(
        "behaviour/behaviour.lgx.yml",
        "applications/lgx.yml",
        "gemma4:e2b"
    )

    previous_step = "Describe the actions being performed in this image."
    #for item in range():
    prompt = previous_step
    result = lgx_instance.infer_step(prompt, "./test_3.jpg").inferred_preds
    print(result)

