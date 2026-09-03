from pathlib import Path

from config.cli import parse_args
from model.loader import load_model
from model.inference import generate_response


def main():
    args = parse_args()
    if args.prompt is not None and args.prompt_file is not None:
        raise SystemExit("prompt와 --prompt-file은 동시에 줄 수 없습니다")

    prompt = args.prompt
    if args.prompt_file is not None:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()

    tokenizer, model = load_model(args.model)

    if prompt is not None:
        response = generate_response(tokenizer, model, prompt, args.max_new_tokens, args.system_prompt)
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
