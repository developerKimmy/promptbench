import json
from pathlib import Path

from config.cli import parse_args
from model.loader import load_model
from model.inference import generate_response, GEN_PARAMS


QUESTION_KEYS = ("input", "question", "prompt")


def question_text(item):
    if isinstance(item, str):
        return item
    for key in QUESTION_KEYS:
        if key in item:
            return item[key]
    raise KeyError(f"item has none of {QUESTION_KEYS}: {item}")


def load_questions(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_markdown_report(results, path):
    lines = ["# Batch Results\n"]
    for i, result in enumerate(results, start=1):
        title = result.get("id", f"item_{i}")
        lines.append(f"## {title}\n")
        lines.append("**Input:**\n")
        lines.append(f"{question_text(result)}\n")
        lines.append("**Answer:**\n")
        lines.append(f"{result['answer']}\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def markdown_path_for(output_path):
    output_path = Path(output_path)
    if output_path.parent.name == "json":
        return output_path.parent.parent / "md" / output_path.with_suffix(".md").name
    return output_path.with_suffix(".md")


def run_batch(tokenizer, model, input_path, output_path, max_new_tokens, system_prompt=None):
    items = load_questions(input_path)
    results = []
    for item in items:
        question = question_text(item)
        answer = generate_response(tokenizer, model, question, max_new_tokens, system_prompt)
        print(f"> {question}\n{answer}\n")
        base = item if isinstance(item, dict) else {"question": item}
        # guideline.md 부록 A: 실행 1건마다 gen_params를 같이 남긴다 (0-A 고정 조건 추적용)
        result = {**base, "answer": answer, "max_new_tokens": max_new_tokens, "gen_params": GEN_PARAMS}
        results.append(result)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    md_path = markdown_path_for(output_path)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    write_markdown_report(results, md_path)


def main():
    args = parse_args()
    if args.input is not None and args.output is None:
        raise SystemExit("--input requires --output")

    tokenizer, model = load_model(args.model)

    if args.input is not None:
        run_batch(tokenizer, model, args.input, args.output, args.max_new_tokens, args.system_prompt)
        return

    if args.prompt is not None:
        response = generate_response(tokenizer, model, args.prompt, args.max_new_tokens, args.system_prompt)
        print(response)
        return

    print(f"Model loaded ({args.model}). Type a prompt and press Enter. Ctrl+D or 'exit' to quit.")
    while True:
        try:
            prompt = input("> ").strip()
        except EOFError:
            print()
            break
        if not prompt:
            continue
        if prompt in ("exit", "quit"):
            break
        response = generate_response(tokenizer, model, prompt, args.max_new_tokens, args.system_prompt)
        print(response)


if __name__ == "__main__":
    main()
