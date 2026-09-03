MODELS = {
    "3b": {"hf_id": "Qwen/Qwen2.5-3B-Instruct-AWQ", "quant": "AWQ 4bit"},
    "7b": {"hf_id": "Qwen/Qwen2.5-7B-Instruct-AWQ", "quant": "AWQ 4bit"},
}


def resolve_model(short_name):
    if short_name not in MODELS:
        raise KeyError(f"unknown model '{short_name}', expected one of {list(MODELS)}")
    return MODELS[short_name]
