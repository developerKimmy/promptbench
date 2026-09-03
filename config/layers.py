import re
from pathlib import Path

import yaml

LAYERS_DIR = Path(__file__).resolve().parent.parent / "layers"
CANDIDATES_DIR = LAYERS_DIR / "candidates"
FIXED_DIR = LAYERS_DIR / "fixed"

FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n?(.*)", re.DOTALL)


def load_layer_file(path):
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text.strip()
    meta = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()
    return meta, body


def candidate_path(candidate_id):
    return CANDIDATES_DIR / f"{candidate_id}.md"


def load_candidate(candidate_id):
    path = candidate_path(candidate_id)
    if not path.exists():
        raise FileNotFoundError(
            f"candidate layer not found: {path} (layers/candidates/{candidate_id}.md 먼저 작성하세요)"
        )
    return load_layer_file(path)


def fixed_layer_text(name="lang"):
    path = FIXED_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"fixed layer not found: {path} (layers/fixed/{name}.md 먼저 작성하세요)"
        )
    _, body = load_layer_file(path)
    return body


def resolve_system_prompt(phase, condition):
    """phase: 'baseline' | 'phase1' | 'phase2'.
    Returns (system_prompt_or_None, fixed_layer_bool).
    guideline.md 4-1: phase1은 고정 레이어를 붙이지 않고, phase2는 스택 뒤에 항상 붙인다.
    """
    if phase == "baseline":
        return None, False
    if phase == "phase1":
        _, body = load_candidate(condition)
        return body, False
    if phase == "phase2":
        candidate_ids = condition.split("+")
        parts = [load_candidate(cid)[1] for cid in candidate_ids]
        parts.append(fixed_layer_text())
        return "\n\n".join(parts), True
    raise ValueError(f"unknown phase: {phase}")


def target_cases_for(condition):
    """조건(단일 후보 또는 '+'로 이은 스택)에 속한 후보들의 target_cases 합집합."""
    candidate_ids = condition.split("+")
    cases = set()
    for cid in candidate_ids:
        meta, _ = load_candidate(cid)
        cases.update(meta.get("target_cases", []))
    return cases
