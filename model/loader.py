from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(model_id):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto", device_map="cuda")
    return tokenizer, model
