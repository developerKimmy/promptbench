import re
from pathlib import Path

import yaml

LAYERS_DIR = Path(__file__).resolve().parent.parent / "layers"
CANDIDATES_DIR = LAYERS_DIR / "candidates"
FIXED_DIR = LAYERS_DIR / "fixed"
FIXED_LAYERS_MANIFEST = Path(__file__).resolve().parent / "fixed_layers.yaml"

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


def fixed_layer_ids_for(model):
    """config/fixed_layers.yaml에서 모델별 고정 레이어 id 목록을 읽는다.
    guideline.md 용어 정의: "검증 완료"는 모델 단위로 성립하므로 고정 레이어 집합은
    모델별로 다를 수 있다. 목록이 없거나 비어 있으면 그 모델엔 고정 레이어가 없는 것.
    """
    if not FIXED_LAYERS_MANIFEST.exists():
        return []
    manifest = yaml.safe_load(FIXED_LAYERS_MANIFEST.read_text(encoding="utf-8")) or {}
    return manifest.get(model, [])


def fixed_layer_text(model):
    ids = fixed_layer_ids_for(model)
    bodies = []
    for layer_id in ids:
        path = FIXED_DIR / f"{layer_id}.md"
        if not path.exists():
            raise FileNotFoundError(
                f"fixed layer not found: {path} (layers/fixed/{layer_id}.md 먼저 작성하세요)"
            )
        _, body = load_layer_file(path)
        bodies.append(body)
    return "\n\n".join(bodies)


def resolve_system_prompt(phase, condition, model=None):
    """phase: 'baseline' | 'phase1' | 'phase2'.
    Returns (system_prompt_or_None, fixed_layer_bool).
    guideline.md 4-1: phase1은 고정 레이어를 붙이지 않고, phase2는 스택 뒤에 항상 붙인다.
    phase2는 모델별 고정 레이어 목록(config/fixed_layers.yaml)을 조회해야 해서 model이 필수다.
    """
    if phase == "baseline":
        return None, False
    if phase == "phase1":
        _, body = load_candidate(condition)
        return body, False
    if phase == "phase2":
        if model is None:
            raise ValueError("phase2는 model 인자가 필요합니다 (모델별 고정 레이어 조회용)")
        candidate_ids = condition.split("+")
        parts = [load_candidate(cid)[1] for cid in candidate_ids]
        fixed_text = fixed_layer_text(model)
        if fixed_text:
            parts.append(fixed_text)
        return "\n\n".join(parts), bool(fixed_text)
    raise ValueError(f"unknown phase: {phase}")


def target_cases_for(condition):
    """조건(단일 후보 또는 '+'로 이은 스택)에 속한 후보들의 target_cases 합집합."""
    candidate_ids = condition.split("+")
    cases = set()
    for cid in candidate_ids:
        meta, _ = load_candidate(cid)
        cases.update(meta.get("target_cases", []))
    return cases
