from src.lgx import LGX

if __name__ == "__main__":

    lgx_instance = LGX(
        "behaviour/behaviour.lgx.yml",
        "applications/lgx.yml",
        "ahmadwaqar/smolvlm2-256m-video:fp16"
    )

    previous_step = "This will be the first step. Extract the description of the action being performed in this step."
    #for item in range():
    prompt = previous_step
    result = lgx_instance.infer_step(prompt, "./test_3.jpg").inferred_preds
    print(result)

