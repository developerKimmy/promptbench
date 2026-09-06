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
0. layers/candidates/lang.md 작성 (target_cases: [], D2 확정)
   layers/candidates/_null.md 작성 (통제 조건, D6 확정 — 이미 완료)
   ↓
1. 7B baseline 재생성 (N=5) + 7B _null 재생성 (N=5, D6, 같은 세션)
   ↓
2. 3B lang phase1 재생성 (N=5)
   3. 7B lang phase1 재생성 (N=10, D1)   [2, 3은 병렬 가능]
   ↓
4. 구식 데이터와 신규 데이터 대조 (아래 "검증 기준" 참고)
   ↓
5. 대조 통과 시 구식 디렉토리 아카이브 처리
```

**주의 — `--n`은 `generate.py`의 필수 인자**(`required=True`). 아래 각 단계 명령에
`--n <값>` 반드시 포함해야 함 (값은 "D1" 참고).

## 코드 레벨 함정 (2026-09-06 코드 확인으로 발견)

- `rank.py:101-103`: `target_case_ids = {r["case_id"] for r in rows if r["target_flag"] == "True"}`
  다음 `if not target_case_ids: continue`. `lang.md`에 `target_cases`가 비어 있으면
  모든 run의 `target_flag`가 `False`가 되어 lang 조건 전체가 **에러 없이 조용히**
  순위표에서 빠진다. → 0-1단계에서 `target_cases`를 반드시 채워야 함.
- `judgments/`, `derived/`는 이미 존재하지만(디렉토리 자체는 있음) **내용이 0건**
  (`derived/index.csv`, `derived/ranking_3b.csv`는 헤더만, `judgments/`는 판정 파일
  없음). 현재 생성된 run 180개(baseline 65 + phase1 115)에 대한 정식 판정이
  하나도 없는 상태 — 마이그레이션과 별개로 이미 쌓여있는 백로그.

### 0단계 — `layers/candidates/lang.md` 작성

`layers/fixed/lang.md`의 본문을 그대로 가져오되, 후보 파일 스키마(frontmatter: `id`,
`target_cases`)에 맞춰 작성. `target_cases: []`로 둔다 (D2, 아래 "Day 0 결정" 참고).

**주의 — 파일 안에 설명 주석을 넣지 말 것**: `config/layers.py`의 `load_layer_file`은
frontmatter(`---` 두 줄 사이) 뒤의 나머지 전체를 그대로 시스템 프롬프트 본문으로 쓴다.
HTML 주석이든 뭐든 frontmatter 밖에 적으면 **모델에게 그대로 전송된다** (`_null.md`
작성 중 실제로 이 실수를 할 뻔해서 확인함). lang이 "이미 3B에서는 확정, 7B에서만
재검증 중"인 특수 상태라는 설명은 파일에 안 넣고 `notes/scope-notes.md`에만 남긴다
(H.md도 같은 방식 — 파일엔 지시문뿐이고 근거는 scope-notes.md에 있음).

### 1단계 — 7B baseline (+ D6 통제 조건)

```
python scripts/generate.py --phase baseline --model 7b --n 5
python scripts/generate.py --phase phase1 --condition _null --model 7b --n 5
```
`--n`은 필수 인자라 값 없이 실행하면 즉시 에러. 13케이스 전체(0-B 규칙: 항상 전체 케이스
실행 — `--case`를 생략하면 자동으로 전체, 별도 지정 불필요/불가). `_null`은 D6의 통제
조건 — 같은 GPU 세션에 묶어서 돌린다. 기존 구식 baseline(N=10, case_01~10)과 사례가
겹치는 case_01~10 구간에서 실패 패턴이 방향성이라도 일치하는지 대조 (완전 재현은 기대하지
않음 — 샘플링 자체가 확률적이므로).

### 2·3단계 — lang phase1 (3B, 7B)

```
python scripts/generate.py --phase phase1 --condition lang --model 3b --n 5
python scripts/generate.py --phase phase1 --condition lang --model 7b --n 10
```
둘 다 `--case` 생략이므로 13케이스 전체 생성 (구 데이터의 10케이스와 다름 — 3B도 13케이스로
새로 돈다는 뜻). N은 D1대로 3B=5, 7B=10 (비대칭 — 3-4상 문제 없음). 7B는 특히 "가짜 user
턴 생성" 재현율(구식 데이터 기준 3~4/10)이 신규 스키마에서도 같은 방향으로 나오는지가 핵심
확인 대상 — 이게 재현 안 되면 `config/fixed_layers.yaml`의 `7b: []` 결정 자체를
재검토해야 함.

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

## 6. Day 0 결정 (확정 — 2026-09-06)

| # | 항목 | 결정 |
|---|---|---|
| D1 | 7B의 N | **분리**: 7B baseline은 N=5(사전 근거 없음, 탐색용). 7B lang은 N=10(구식 데이터에서 이미 중대 사이드이펙트 3~4/10 재현 확인됨 — 3-2 트리거가 첫 라운드에 걸릴 게 뻔해 5로 시작하면 왕복만 늘어남). 3-4가 "baseline과 후보 N은 같을 필요 없다"고 명시하므로 위반 아님 |
| D2 | lang의 `target_cases` | **`[]`로 확정.** case_02는 넣지 않음 — H도 동일 사유로 이미 제외돼 있었음(`notes/scope-notes.md` 2026-09-04), 2026-09-06 항목에서 원인(baseline system 슬롯 부재로 인한 벤더 페르소나 자동 주입)까지 코드로 확인 완료 |
| D3 | lang의 "재검증용 후보" 상태 기록 위치 | **`guideline.md` 비수정.** 파일 자체에도 주석 넣지 않음(위 "0단계" 주의 참고) — `notes/scope-notes.md`에만 기록, H.md와 같은 컨벤션 |
| D4 | 판정 백로그(180건) 처리 시점 | **마이그레이션 이후 한꺼번에.** `judge.py:145`가 이미 `random.shuffle(pending)`으로 blind 셔플을 기본 동작으로 하므로, 생성을 다 끝내고 한 번에 돌리는 쪽이 이중작업을 피함 |
| D5 | `target_cases` 모델별 분리 스키마 문제 | **별개 이슈로 유지, 이번 마이그레이션 범위 밖.** 스키마를 고쳐도 D2의 confound 자체는 안 풀림 — `harness/ablation/H/7b/md/failure_review.md` "정리 필요한 것" 참고 |
| D6 | baseline system 슬롯 confound 통제 | **`layers/candidates/_null.md`(중립 더미, `target_cases: []`) 신설, 7B만 우선 (13케이스×N=5=65 run).** baseline 생성 코드는 안 고침(0-A 정의 유지, 기존 데이터 무효화 방지). 3B는 동일 증상 미관찰이라 보류 — 근거: `notes/scope-notes.md` 2026-09-06 항목 |

경위와 근거는 전부 `notes/scope-notes.md` 2026-09-06 항목("baseline system 슬롯 부재가
만드는 confound")에 있음. `guideline.md` 0-A/부록A에도 `chat_template_sha` 기록,
system 슬롯 존재 여부 고정 조건이 반영됨.

## 7. 총 생성량 (D1·D6 반영)

| 단계 | 모델 | 조건 | 케이스 | N | run 수 |
|---|---|---|---|---|---|
| 1 | 7B | baseline | 13 | 5 | 65 |
| 1' | 7B | _null (D6) | 13 | 5 | 65 |
| 2 | 3B | lang | 13 | 5 | 65 |
| 3 | 7B | lang | 13 | 10 | 130 |
| **합계** | | | | | **325 run** |

3B `_null`(D6 보류), 7B lang N 추가 증량(3-2 트리거 시)은 미포함.
