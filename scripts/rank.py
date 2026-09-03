import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

INDEX_PATH = ROOT / "derived" / "index.csv"
DERIVED_DIR = ROOT / "derived"

FAIL_JUDGMENTS = {"위반", "애매"}


# guideline.md 부록 B — 그대로 사용
def conservative_improvement(
    base_fail: int, base_n: int,
    cand_fail: int, cand_n: int,
    quantile: float = 0.20,      # 프로젝트 파라미터 (하위 분위수)
    n_samples: int = 200_000,
    seed: int = 0,
) -> dict:
    """
    baseline 실패율 - 후보 실패율의 사후분포에서 하위 분위수를 순위 점수로 반환.
    실패 카운트에는 2-2의 '위반' + '애매'를 모두 포함한다 (4-2 ①).
    Jeffreys 사전분포 Beta(0.5, 0.5) 사용.
    """
    rng = np.random.default_rng(seed)
    p_base = rng.beta(base_fail + 0.5, base_n - base_fail + 0.5, n_samples)
    p_cand = rng.beta(cand_fail + 0.5, cand_n - cand_fail + 0.5, n_samples)
    diff = p_base - p_cand                       # 양수 = 개선
    return {
        "score": float(np.quantile(diff, quantile)),   # 2차 키 (4-2 ④-2)
        "point": float(np.mean(diff)),                 # 3차 키 (4-2 ④-3)
        "p_improve": float(np.mean(diff > 0)),          # 참고용
    }


def rank_candidates(rows: list[dict]) -> list[dict]:
    """
    rows: 한 모델 안의 후보별 집계. 각 원소는
      {"candidate": str, "risk": "low"|"mid"|"high",
       "base_fail": int, "base_n": int, "cand_fail": int, "cand_n": int,
       "mid_side_effects": int}
    4-2 ④의 사전식 순서: 리스크 등급 -> 보수적 개선량 -> 점 추정 -> 중간 사이드이펙트 수
    """
    risk_order = {"low": 0, "mid": 1, "high": 2}
    out = []
    for r in rows:
        est = conservative_improvement(r["base_fail"], r["base_n"],
                                       r["cand_fail"], r["cand_n"])
        out.append({**r, **est})
    out.sort(key=lambda r: (risk_order[r["risk"]],
                            -r["score"], -r["point"], r["mid_side_effects"]))
    return out


def load_index():
    with open(INDEX_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pool_fail_n(rows, case_ids):
    """rows 중 case_id in case_ids 인 것만 풀링해서 (fail, n) 반환 (4-2 ②)."""
    filtered = [r for r in rows if r["case_id"] in case_ids]
    n = len(filtered)
    fail = sum(1 for r in filtered if r["judgment"] in FAIL_JUDGMENTS)
    return fail, n


def main():
    parser = argparse.ArgumentParser(description="guideline.md 4-2 ③ 보수적 개선량으로 후보 순위 계산")
    parser.add_argument("--model", required=True, choices=["3b", "7b"])
    parser.add_argument(
        "--risk",
        default=None,
        help="condition별 risk 등급(low/mid/high)을 'H:low,S:mid' 형식으로 지정. "
        "생략 시 전부 low로 취급 (2-4 리스크 분류는 아직 judge.py 스키마 밖이라 수동 입력)",
    )
    args = parser.parse_args()

    risk_map = {}
    if args.risk:
        for pair in args.risk.split(","):
            cid, level = pair.split(":")
            risk_map[cid] = level

    all_rows = [r for r in load_index() if r["model"] == args.model]
    baseline_rows = [r for r in all_rows if r["condition"] == "baseline"]

    by_condition = defaultdict(list)
    for r in all_rows:
        if r["condition"] != "baseline":
            by_condition[r["condition"]].append(r)

    table_rows = []
    for condition, rows in by_condition.items():
        target_case_ids = {r["case_id"] for r in rows if r["target_flag"] == "True"}
        if not target_case_ids:
            continue
        cand_fail, cand_n = pool_fail_n(rows, target_case_ids)
        base_fail, base_n = pool_fail_n(baseline_rows, target_case_ids)
        mid_side_effects = sum(1 for r in rows if r["side_effect"] == "중간")
        table_rows.append({
            "candidate": condition,
            "risk": risk_map.get(condition, "low"),
            "base_fail": base_fail, "base_n": base_n,
            "cand_fail": cand_fail, "cand_n": cand_n,
            "mid_side_effects": mid_side_effects,
        })

    ranked = rank_candidates(table_rows)

    out_path = DERIVED_DIR / f"ranking_{args.model}.csv"
    fieldnames = [
        "candidate", "risk", "base_fail", "base_n", "cand_fail", "cand_n",
        "score", "point", "p_improve", "mid_side_effects",
    ]
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in ranked:
            writer.writerow({k: row[k] for k in fieldnames})

    for row in ranked:
        print(
            f"{row['candidate']:>10} risk={row['risk']:<4} "
            f"score={row['score']:+.3f} point={row['point']:+.3f} "
            f"({row['cand_fail']}/{row['cand_n']} vs base {row['base_fail']}/{row['base_n']})"
        )
    print(f"-> {out_path}")


if __name__ == "__main__":
    main()
