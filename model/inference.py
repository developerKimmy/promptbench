# guideline.md 0-A: baseline과 후보 실행 사이에 절대 달라지면 안 되는 값이라 코드에 고정.
# CLI로 노출하지 않는 이유도 동일 — 실행마다 실수로 다른 값이 들어갈 통로를 안 만들기 위함.
# 값은 Qwen2.5-{3B,7B}-Instruct-AWQ의 체크포인트 기본 generation_config.json과 동일.
GEN_PARAMS = {
    "do_sample": True,
    "temperature": 0.7,
    "top_k": 20,
    "top_p": 0.8,
    "repetition_penalty": 1.05,
}


def generate_response(tokenizer, model, prompt, max_new_tokens, system_prompt=None):
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    inputs = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", return_dict=True
    ).to(model.device)

    output = model.generate(**inputs, max_new_tokens=max_new_tokens, **GEN_PARAMS)
    return tokenizer.decode(output[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
