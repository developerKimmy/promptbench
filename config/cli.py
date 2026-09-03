import argparse

DEFAULT_MODEL = "Qwen/Qwen2.5-3B-Instruct-AWQ"


def parse_args():
    parser = argparse.ArgumentParser(description="Run a prompt through a local model")
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="User prompt to send to the model. Omit to start an interactive session.",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Path to a file containing the prompt, as an alternative to the positional "
        "prompt arg (handy for multi-line or quote-heavy prompts). Mutually exclusive with it.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HF model id (default: %(default)s)")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Optional system prompt prepended to every request (single-shot and interactive).",
    )
    return parser.parse_args()
