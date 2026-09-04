import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import transformers  # noqa: E402

from config.layers import resolve_system_prompt, target_cases_for  # noqa: E402
from config.models import resolve_model  # noqa: E402
from model.inference import GEN_PARAMS, generate_response  # noqa: E402
from model.loader import load_model  # noqa: E402

CASES_PATH = ROOT / "cases" / "cases.json"
RUNS_DIR = ROOT / "runs"


def parse_args():
    parser = argparse.ArgumentParser(description="guideline.md 절차대로 실험 데이터를 생성한다")
    parser.add_argument("--phase", required=True, choices=["baseline", "phase1", "phase2"])
    parser.add_argument("--model", required=True, choices=["3b", "7b"])
    parser.add_argument(
        "--condition",
        default=None,
        help="phase1: 후보 ID 하나 (예: H). phase2: '+'로 이은 스택 ID (예: H+S). baseline은 불필요.",
    )
    parser.add_argument(
        "--case",
        default=None,
        help="특정 케이스 ID만 생성 (국지적 증량용, 3-3). 생략하면 전체 케이스 (0-B 기본).",
    )
    parser.add_argument("--n", type=int, required=True, help="추가로 생성할 실행 수")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    return parser.parse_args()


def load_cases():
    with open(CASES_PATH, encoding="utf-8") as f:
        return json.load(f)


def run_dir(phase, model, condition, case_id):
    if phase == "baseline":
        return RUNS_DIR / phase / model / case_id
    return RUNS_DIR / phase / model / condition / case_id


def next_run_idx(directory):
    if not directory.exists():
        return 1
    existing = [p.stem for p in directory.glob("run_*.json")]
    indices = [int(name.split("_")[1]) for name in existing]
    return max(indices, default=0) + 1


def main():
    args = parse_args()
    if args.phase != "baseline" and not args.condition:
        raise SystemExit(f"--phase {args.phase}는 --condition이 필요합니다")

    system_prompt, fixed_layer = resolve_system_prompt(args.phase, args.condition, args.model)

    all_cases = load_cases()
    if args.case is not None:
        cases = [c for c in all_cases if c["id"] == args.case]
        if not cases:
            raise SystemExit(f"case '{args.case}'를 cases/cases.json에서 찾을 수 없습니다")
    else:
        cases = all_cases

    target_cases = target_cases_for(args.condition) if args.condition else set()

    model_info = resolve_model(args.model)
    tokenizer, model = load_model(model_info["hf_id"])

    for case in cases:
        case_id = case["id"]
        directory = run_dir(args.phase, args.model, args.condition, case_id)
        directory.mkdir(parents=True, exist_ok=True)
        start_idx = next_run_idx(directory)

        for offset in range(args.n):
            run_idx = start_idx + offset
            answer = generate_response(
                tokenizer, model, case["input"], args.max_new_tokens, system_prompt
            )
            record = {
                "model": args.model,
                "hf_id": model_info["hf_id"],
                "quant": model_info["quant"],
                "runtime_version": transformers.__version__,
                "phase": args.phase,
                "condition": args.condition,
                "fixed_layer": fixed_layer,
                "case_id": case_id,
                "run_idx": run_idx,
                "target_flag": case_id in target_cases,
                "gen_params": GEN_PARAMS,
                "system_prompt": system_prompt,
                "max_new_tokens": args.max_new_tokens,
                "answer": answer,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            out_path = directory / f"run_{run_idx:03d}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            print(f"[{case_id}] run_{run_idx:03d} -> {out_path}")


if __name__ == "__main__":
    main()
