import json
import sys
from csv import DictWriter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.layers import target_cases_for  # noqa: E402

RUNS_DIR = ROOT / "runs"
JUDGMENTS_DIR = ROOT / "judgments"
DERIVED_DIR = ROOT / "derived"

FIELDS = [
    "model", "condition", "fixed_layer", "case_id", "run_idx",
    "gen_params", "target_flag", "judgment", "hedge_tag", "obs_points",
    "side_effect", "auto_metrics", "rejudged", "note",
]


def load_judgment(phase, model, condition, case_id, run_idx):
    if condition is None:
        jsonl_path = JUDGMENTS_DIR / phase / model / f"{case_id}.jsonl"
    else:
        jsonl_path = JUDGMENTS_DIR / phase / model / condition / f"{case_id}.jsonl"
    if not jsonl_path.exists():
        return {}
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("run_idx") == run_idx:
                return entry
    return {}


def load_rejudgment(phase, model, condition, case_id, run_idx):
    if condition is None:
        jsonl_path = JUDGMENTS_DIR / "rejudge" / phase / model / f"{case_id}.jsonl"
    else:
        jsonl_path = JUDGMENTS_DIR / "rejudge" / phase / model / condition / f"{case_id}.jsonl"
    if not jsonl_path.exists():
        return None
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if entry.get("run_idx") == run_idx:
                return entry
    return None


def build_rows():
    rows = []
    target_cache = {}
    for run_path in sorted(RUNS_DIR.rglob("run_*.json")):
        with open(run_path, encoding="utf-8") as f:
            run = json.load(f)

        phase, model, condition = run["phase"], run["model"], run["condition"]
        case_id, run_idx = run["case_id"], run["run_idx"]

        target_flag = run.get("target_flag")
        if target_flag is None and condition is not None:
            if condition not in target_cache:
                target_cache[condition] = target_cases_for(condition)
            target_flag = case_id in target_cache[condition]

        judgment_entry = load_judgment(phase, model, condition, case_id, run_idx)
        rejudgment_entry = load_rejudgment(phase, model, condition, case_id, run_idx)

        rows.append({
            "model": model,
            "condition": condition if condition is not None else "baseline",
            "fixed_layer": run.get("fixed_layer", False),
            "case_id": case_id,
            "run_idx": run_idx,
            "gen_params": json.dumps(run.get("gen_params", {}), ensure_ascii=False),
            "target_flag": target_flag,
            "judgment": judgment_entry.get("judgment"),
            "hedge_tag": judgment_entry.get("hedge_tag"),
            "obs_points": json.dumps(judgment_entry.get("obs_points"), ensure_ascii=False)
            if judgment_entry.get("obs_points") is not None else "",
            "side_effect": judgment_entry.get("side_effect"),
            "auto_metrics": json.dumps(judgment_entry.get("auto_metrics"), ensure_ascii=False)
            if judgment_entry.get("auto_metrics") is not None else "",
            "rejudged": rejudgment_entry.get("judgment") if rejudgment_entry else "",
            "note": judgment_entry.get("note", ""),
        })
    return rows


def main():
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    rows = build_rows()
    out_path = DERIVED_DIR / "index.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)}개 행 -> {out_path}")


if __name__ == "__main__":
    main()
