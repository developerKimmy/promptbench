# 구식 포맷 데이터 마이그레이션 계획

> 배경: 2026-09-06 대화에서 "phase1 H에 lang이 붙어있었나" 질문을 확인하는 과정에서,
> 최상위 `baseline/`, `harness/ablation/lang/`이 `runs/` 표준 스키마로 이관되지 않은 채
> 남아있다는 게 드러남. 실제로 데이터를 다시 생성하기 전, 원인·해결방안·계획만 먼저
> 문서화한다. 재생성(GPU 추론) 자체는 별도 승인 후 진행.

## 1. 원인 분석

### 1-1. 두 세대의 스키마가 공존한다

프로젝트는 커밋 `9f35f42`("Restructure into guideline.md-driven experiment tooling")에서
ad-hoc 실험 방식을 `guideline.md` 기반 하네스로 전면 재설계했다. 이 재설계로 다음이 새로
생겼다:

- `config/layers.py`의 `resolve_system_prompt()` — phase별 시스템 프롬프트 조립 규칙
- `scripts/generate.py` — 실행 1건마다 `runs/{phase}/{model}/{condition}/{case_id}/run_{idx}.json`
  형식으로 저장 (스키마: `phase`, `condition`, `fixed_layer`, `case_id`, `run_idx`, `gen_params`,
  `system_prompt` 등 — `guideline.md` 부록 A 기준)
- `scripts/judge.py`, `scripts/build_index.py` — **`runs/` 디렉토리만, `run_*.json` 파일명
  패턴만** 스캔 (`RUNS_DIR.rglob("run_*.json")`)

재설계 이전 데이터는 다른 위치·다른 스키마로 존재한다:

- `baseline/{3b,7b}/{json,repro/json}/*.json` — 파일명 `baseline.json`/`baseline_N.json`,
  배열 형태, `system_prompt`/`phase`/`fixed_layer` 필드 없음, N=10, case_01~10만 (당시엔
  case_11~13이 없었음)
- `harness/ablation/lang/{3b,7b}/{json,repro/json}/*.json` — 위와 동일한 구식 스키마

### 1-2. 재설계 이후 마이그레이션이 부분적으로만 이뤄졌다

커밋 `a270262`에서 **3B baseline만** 신규 스키마로 재생성됐다 (`runs/baseline/3b/`,
N=5, 13케이스 — case_11~13 held-out 케이스 포함). 이후 관심이 바로 후보 H의 phase1
검증(`runs/phase1/{3b,7b}/H/`)으로 넘어가면서, 다음 두 가지는 신규 스키마로 재생성된 적이
없다:

- **7B baseline** — `runs/baseline/7b/`가 아예 존재하지 않음
- **lang ablation (3B+7B 전체)** — lang은 3B에서 고정 레이어로 확정됐고 7B에서는
  2026-09-04에 "후보로 재분류"하기로 결정됐지만(`config/fixed_layers.yaml`), 그 결정의
  근거였던 재현 실험 자체가 구식 스키마 파일을 사람이 다시 읽어서 나온 것이지(`notes/scope-notes.md`
  1006~1008줄), 신규 하네스로 재생성된 게 아니다. `layers/candidates/`에도 `lang.md`가
  없어서 (`layers/fixed/lang.md`만 존재) `scripts/generate.py --phase phase1 --condition lang`
  자체가 지금은 실행 불가능하다.

**근본 원인 한 줄 요약**: 재설계 커밋이 "앞으로의 실험 도구"만 새로 만들고, "과거 실험
데이터의 재생성"까지는 스코프에 넣지 않았다. 이후 작업 우선순위가 신규 후보(H) 검증으로
넘어가면서 이월 작업으로 방치됐다.

## 2. 현재 상태 요약

| 실험 | 위치 | 스키마 | 케이스 수 | judge.py/build_index.py 인식 |
|---|---|---|---|---|
| 3B baseline | `runs/baseline/3b/` | 신규 | 13 (case_01~13) | O |
| 7B baseline | `baseline/7b/{json,repro}/` | 구식 | 10 (case_01~10) | **X** |
| 3B lang | `harness/ablation/lang/3b/{json,repro}/` | 구식 | 10 (case_01~10 추정) | **X** |
| 7B lang | `harness/ablation/lang/7b/{json,repro}/` | 구식 | 10 (case_01~10 추정) | **X** |
| 3B phase1 H | `runs/phase1/3b/H/` | 신규 | 10 | O |
| 7B phase1 H | `runs/phase1/7b/H/` | 신규 | 13 | O |

## 3. 왜 문제가 되는가

- **판정 자동화 공백**: `scripts/judge.py`의 정식 blind 판정과 `scripts/rank.py`의 순위
  산정(`guideline.md` 4-2)이 baseline·lang 데이터를 입력으로 요구하는데, 7B baseline과
  lang 전체가 그 입력 풀에 없다. 지금까지의 7B 관련 판단(`harness/ablation/H/7b/md/failure_review.md`)은
  전부 "사람이 구식 파일을 직접 훑은 예비 검토"이지 정식 판정이 아니다 — `guideline.md`
  2-3(캘리브레이션)·4-2(사후분포 순위) 절차를 아직 못 밟은 상태.
- **케이스 커버리지 불일치**: 구식 데이터는 case_01~10뿐이라, held-out 케이스(case_11~13)에
  대한 baseline·lang 비교가 원천적으로 없다. 새 후보를 이 케이스들로 검증하려 해도 비교할
  baseline이 없다.
- **lang을 정식 후보로 재판정할 방법이 없음**: 7B에서 lang을 후보로 재분류하기로
  결정(`notes/scope-notes.md` 2026-09-04)했지만, `layers/candidates/lang.md`가 없어서
  `scripts/generate.py`로 phase1 재검증 자체가 불가능하다. 즉 "후보로 취급한다"는 결정이
  도구 상으로는 아직 실행 불가능한 상태로 남아있다.
- **감사 추적(audit trail)은 구식 파일에만 있음**: `7b: []` 결정의 근거가 되는 재현
  수치(가짜 user 턴 0/10 → 3~4/10)는 구식 파일을 사람이 직접 읽어서 나온 것이라, 그
  파일들을 지우면 결정 근거를 재검증할 방법이 사라진다 (이전 턴에서 지적한 부분).

## 4. 해결 방안

세 가지 옵션을 검토했고, **C안(단계적 마이그레이션)을 권장**한다.

**A안 — 전체 즉시 재생성**: 7B baseline + 3B/7B lang을 한 번에 신규 스키마·13케이스로
재생성. 가장 깔끔하지만 GPU 시간이 한 번에 많이 들고, `layers/candidates/lang.md` 부재
같은 선행 이슈를 한꺼번에 해결해야 해서 착수 지연 위험이 있다.

**B안 — 방치**: 구식 데이터를 그대로 두고 필요할 때마다 사람이 수동으로 읽는다. 지금까지
해온 방식의 연장인데, `guideline.md`가 정의한 정식 절차(2-3, 4-2)를 영구히 우회하게 되고
held-out 케이스는 계속 비교 불가 상태로 남는다. 권장하지 않음.

**C안 — 단계적 마이그레이션 (권장)**: 의존 관계 순서대로 하나씩 신규 스키마로 옮기고,
각 단계마다 구식 데이터와 대조해서 회귀가 없는지 확인한 뒤 다음 단계로 간다. 아래 5번
계획이 이 방식을 구체화한 것.

## 5. 마이그레이션 계획

### 순서 (의존 관계 기준)

```
0. layers/candidates/lang.md 작성 (전제조건 — 이게 없으면 1도 못함)
   ↓
1. 7B baseline 재생성 (runs/baseline/7b/, 13케이스, N=5)
   ↓
2. 3B lang phase1 재생성 (runs/phase1/3b/lang/, 10케이스, N=5)
   3. 7B lang phase1 재생성 (runs/phase1/7b/lang/, 13케이스, N=5)   [2, 3은 병렬 가능]
   ↓
4. 구식 데이터와 신규 데이터 대조 (아래 "검증 기준" 참고)
   ↓
5. 대조 통과 시 구식 디렉토리 아카이브 처리
```

### 0단계 — `layers/candidates/lang.md` 작성

`layers/fixed/lang.md`의 본문을 그대로 가져오되, 후보 파일 스키마(frontmatter:
`target_cases` 등)에 맞춰 작성. **주의**: `guideline.md` 1-e에 따르면 후보 문구는
고정 레이어가 담당하는 내용(출력 언어)을 언급하면 안 되는데, lang 자체가 언어 지시이므로
이 규칙의 예외로 남긴다는 점을 frontmatter나 주석에 명시해야 함 (재검증용 후보이지 stacking용
신규 후보가 아니므로).

### 1단계 — 7B baseline

```
python scripts/generate.py --phase baseline --model 7b
```
13케이스 전체(0-B 규칙: 항상 전체 케이스 실행) × N=5(3-4: Phase 1 시작 N, 3B와 동일값
재사용 — 3-5 "N 산정 규칙은 모델 공통"). 기존 구식 baseline(N=10, case_01~10)과 사례가
겹치는 case_01~10 구간에서 실패 패턴이 방향성이라도 일치하는지 대조 (완전 재현은 기대하지
않음 — 샘플링 자체가 확률적이므로).

### 2·3단계 — lang phase1 (3B, 7B)

```
python scripts/generate.py --phase phase1 --condition lang --model 3b
python scripts/generate.py --phase phase1 --condition lang --model 7b
```
7B는 특히 "가짜 user 턴 생성" 재현율(구식 데이터 기준 3~4/10)이 신규 스키마에서도
같은 방향으로 나오는지가 핵심 확인 대상 — 이게 재현 안 되면 `config/fixed_layers.yaml`의
`7b: []` 결정 자체를 재검토해야 함.

### 4단계 — 검증 기준

- 케이스별 실패 방향(악화/개선/무변화)이 구식 데이터와 같은 방향인지 (수치 일치는 요구하지
  않음, N도 다르고 확률적 생성이므로)
- 구식 데이터에서 관찰된 핵심 현상 2건이 재현되는지:
  1. 7B baseline: case_02 자기 정체성 할루시네이션 (구식 6/10)
  2. 7B lang: 가짜 user 턴 생성 (구식 3~4/10)
- 불일치 시: 방치가 아니라 원인 규명 우선 (환경 차이? 생성 파라미터 차이? 진짜 우연?) —
  `guideline.md` 0-A 고정 조건 재확인부터 시작

### 5단계 — 구식 디렉토리 처리

신규 데이터가 4단계 검증을 통과한 뒤에만 진행. 즉시 삭제하지 않고 `archive/` 하위로 이동
(예: `archive/pre-restructure/baseline/`, `archive/pre-restructure/harness-ablation-lang/`)
— 감사 추적(3번 항목)은 git 히스토리에도 남지만, 디렉토리 이동만으로도 "현재 유효한
데이터가 아님"이 명확해짐. 완전 삭제는 별도로 다시 논의.

## 6. 아직 열린 질문 (진행 전 확인 필요)

- 7B baseline·lang의 N을 3B와 동일하게 5로 시작할지, 아니면 7B가 구식 데이터에서 이미
  "중대 사이드이펙트 재현 확인"까지 간 상태이므로 3-2 규칙상 증량된 N(예: 10, 시작 N의
  2배)으로 바로 시작할지 — `guideline.md` 3-2는 "경계선/애매/중대 사이드이펙트가 나오면
  그 조합만 증량"이라 규정하므로, 이미 알려진 결과가 있는 조합은 처음부터 증량 N으로
  시작하는 게 3-2의 취지에 더 맞을 수 있음.
- `layers/candidates/lang.md`를 만들면 `layers/candidates/`에 H와 함께 나란히 놓이는데,
  lang은 스태킹 후보가 아니라 "이미 3B에서는 확정, 7B에서만 재검증 중"인 특수 상태다.
  후보 파일 스키마에 이 상태를 어떻게 표시할지 (`guideline.md` 개정 없이 note로만 남길지,
  아니면 가이드라인에 "재검증용 후보" 카테고리를 추가할지) 결정 필요.
