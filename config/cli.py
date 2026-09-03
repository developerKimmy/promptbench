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
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HF model id (default: %(default)s)")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument(
        "--input",
        help="Path to a JSON file containing questions to run in batch (a list of strings, "
        "or a list of objects with a 'question' or 'prompt' key). Requires --output.",
    )
    parser.add_argument(
        "--output",
        help="Path to write batch results as JSON (list of {question, answer}). Requires --input.",
    )
    parser.add_argument(
        "--system-prompt",
        default=None,
        help="Optional system prompt prepended to every request (single-shot, interactive, and batch).",
    )
    return parser.parse_args()
