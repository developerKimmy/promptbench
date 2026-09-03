import argparse
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

RUNS_DIR = ROOT / "runs"
JUDGMENTS_DIR = ROOT / "judgments"

JUDGMENT_KEYS = {"v": "위반", "a": "애매", "n": "위반 아님"}
SIDE_EFFECT_KEYS = {"0": "없음", "1": "경미", "2": "중간", "3": "중대"}


def parse_args():
    parser = argparse.ArgumentParser(description="조건을 가린 blind 판정 큐 (2-2, 2-3)")
    parser.add_argument("--phase", required=True, choices=["baseline", "phase1", "phase2"])
    parser.add_argument("--model", required=True, choices=["3b", "7b"])
    parser.add_argument("--condition", default=None, help="특정 조건만 판정 (생략 시 phase 전체)")
    parser.add_argument("--rejudge", action="store_true", help="2-3: 이미 판정된 항목 중 일부를 재판정")
    parser.add_argument("--frac", type=float, default=0.15, help="--rejudge일 때 재표본 비율 (기본 0.15)")
    return parser.parse_args()


def judgment_path(phase, model, condition, case_id, rejudge=False):
    base = JUDGMENTS_DIR / "rejudge" if rejudge else JUDGMENTS_DIR
    if condition is None:
        return base / phase / model / f"{case_id}.jsonl"
    return base / phase / model / condition / f"{case_id}.jsonl"


def load_jsonl(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(path, entry):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def collect_runs(phase, model, condition):
    """run 파일을 읽어 case_id별로 묶는다: {case_id: [(condition, run_dict, path), ...]}"""
    base = RUNS_DIR / phase / model
    if condition is not None:
        base = base / condition
    by_case = {}
    for run_path in sorted(base.rglob("run_*.json")):
        with open(run_path, encoding="utf-8") as f:
            run = json.load(f)
        by_case.setdefault(run["case_id"], []).append((run["condition"], run, run_path))
    return by_case


def prompt_judgment():
    while True:
        raw = input("판정 [v]위반 / [a]애매 / [n]위반아님 (건너뛰려면 s): ").strip().lower()
        if raw == "s":
            return None
        if raw in JUDGMENT_KEYS:
            return JUDGMENT_KEYS[raw]
        print("v/a/n/s 중 하나를 입력하세요.")


def prompt_side_effect():
    while True:
        raw = input("side_effect [0]없음 [1]경미 [2]중간 [3]중대: ").strip()
        if raw in SIDE_EFFECT_KEYS:
            return SIDE_EFFECT_KEYS[raw]
        print("0/1/2/3 중 하나를 입력하세요.")


def run_queue(items, phase, model, rejudge):
    """items: [(condition, run_dict, path), ...] — 이미 셔플된 상태로 전달."""
    print(f"{len(items)}개 항목. Ctrl+D로 언제든 중단 (지금까지 판정한 건 저장됨).\n")
    for condition, run, _ in items:
        case_id, run_idx = run["case_id"], run["run_idx"]
        print("-" * 60)
        print(f"[입력]\n{run.get('_case_input', '(케이스 원문 미포함)')}\n")
        print(f"[답변]\n{run['answer']}\n")
        try:
            judgment = prompt_judgment()
        except EOFError:
            print()
            break
        if judgment is None:
            continue
        side_effect = prompt_side_effect()
        note = input("메모 (엔터로 건너뛰기): ").strip()

        entry = {
            "run_idx": run_idx,
            "judgment": judgment,
            "side_effect": side_effect,
            "note": note,
            "judged_at": datetime.now(timezone.utc).isoformat(),
        }
        if rejudge:
            entry["blind"] = True
        out_path = judgment_path(phase, model, condition, case_id, rejudge=rejudge)
        append_jsonl(out_path, entry)
        print(f"저장됨 -> {out_path}")


def main():
    args = parse_args()
    cases_path = ROOT / "cases" / "cases.json"
    with open(cases_path, encoding="utf-8") as f:
        case_inputs = {c["id"]: c["input"] for c in json.load(f)}

    by_case = collect_runs(args.phase, args.model, args.condition)

    flat = []
    for case_id, entries in by_case.items():
        for condition, run, path in entries:
            run["_case_input"] = case_inputs.get(case_id, "")
            flat.append((condition, run, path))

    if args.rejudge:
        already = []
        for case_id, entries in by_case.items():
            for condition, run, path in entries:
                judged = load_jsonl(judgment_path(args.phase, args.model, condition, case_id))
                if any(j["run_idx"] == run["run_idx"] for j in judged):
                    already.append((condition, run, path))
        k = max(1, int(len(already) * args.frac)) if already else 0
        sample = random.sample(already, k) if k else []
        random.shuffle(sample)
        run_queue(sample, args.phase, args.model, rejudge=True)
        return

    pending = []
    for condition, run, path in flat:
        case_id = run["case_id"]
        judged = load_jsonl(judgment_path(args.phase, args.model, condition, case_id))
        if not any(j["run_idx"] == run["run_idx"] for j in judged):
            pending.append((condition, run, path))

    random.shuffle(pending)
    run_queue(pending, args.phase, args.model, rejudge=False)


if __name__ == "__main__":
    main()
