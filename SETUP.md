# 실행 환경 설정 가이드

`run_model.py`를 로컬 GPU에서 돌리기 위한 환경 구성 기록입니다.

> 관련 문서: 실험을 어떻게 설계할지(ablation, 반복 횟수, 후보 문구 작성 규칙 등)는
> [`guideline.md`](guideline.md), 실제 관찰 결과·재현성 검증 로그는
> [`notes/scope-notes.md`](notes/scope-notes.md) 참고.

## 요약

- 환경: conda `harness` 환경 (Python 3.12)
- GPU: NVIDIA RTX 3060 (6GB VRAM, Ampere / compute_86)
- 모델: `Qwen/Qwen2.5-3B-Instruct-AWQ` (기본), `Qwen/Qwen2.5-7B-Instruct-AWQ`도 정상 동작 확인

## 1. Python 패키지 설치

```bash
conda activate harness
pip install -r requirements.txt
```

`requirements.txt`:

```
torch==2.13.0
torchvision==0.28.0
transformers==5.16.1
accelerate==1.14.0
gptqmodel==7.3.5
pyyaml==6.0.3
numpy==2.2.6
```

`pyyaml`은 `config/layers.py`가 후보/고정 레이어 `.md` 파일의 frontmatter를 읽는 데,
`numpy`는 `scripts/rank.py`가 4-2 ③(보수적 개선량, Jeffreys 사전분포)을 계산하는 데 씁니다.

### 왜 `autoawq`가 아니라 `gptqmodel`인가?

이 프로젝트가 쓰는 `Qwen2.5-*-AWQ` 모델은 4bit AWQ 양자화 체크포인트입니다.
과거엔 `autoawq` 패키지가 AWQ 모델 로딩을 담당했지만, **`autoawq`는 공식적으로 deprecated** 되었고
(패키지 자체가 "마지막 테스트: torch 2.6.0 / transformers 4.51.3"이라고 명시), 최신 `transformers`(5.x)는
AWQ 로딩 시 `autoawq` 대신 `gptqmodel`을 요구하도록 바뀌었습니다.

`gptqmodel` 없이 AWQ 모델을 로드하면 아래 에러가 납니다:

```
ImportError: Loading an AWQ quantized model requires gptqmodel. Please install it with `pip install gptqmodel`
```

## 2. CUDA 컴파일러 (최초 1회 필요)

`gptqmodel`은 처음 모델을 로드할 때 GPU에 맞는 **Marlin 커널을 CUDA로 JIT 컴파일**합니다.
이때 시스템에 `nvcc`가 없거나 버전이 안 맞으면 실패합니다.

### 필요한 것

- `torch`가 사용하는 CUDA 버전과 **정확히 같은 버전의 `nvcc`** (여기서는 CUDA 13.0)
- 시스템 기본 `g++`가 아닌, **호환되는 버전의 host 컴파일러**
  (이 머신의 시스템 g++는 15.2.0으로 너무 최신이라 CUDA 13.0 헤더와 충돌 — `rsqrt`/`rsqrtf` exception spec 에러 발생)

### 설치 명령

```bash
conda install -n harness -y "cuda-nvcc=13.0.88" "cuda-nvvm-dev_linux-64=13.0" -c nvidia -c conda-forge
```

이 명령으로 conda가 nvcc와 함께 호환되는 크로스 컴파일러(`x86_64-conda-linux-gnu-g++`)도 같이 설치합니다.

### 최초 실행 시 환경변수

```bash
conda activate harness
export CUDA_HOME=$CONDA_PREFIX
export CXX=$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-g++
export CC=$CONDA_PREFIX/bin/x86_64-conda-linux-gnu-gcc
```

`harness` 환경을 activate한 상태에서 `$CONDA_PREFIX`가 그 환경의 설치 경로를 가리키므로,
사용자/머신마다 다른 conda 설치 위치를 하드코딩할 필요가 없습니다. 이 세 변수는 **최초 1회
커널 컴파일에만** 필요합니다. 컴파일된 커널은
`~/.cache/gptqmodel/torch_extensions/`에 캐시되므로, 이후 실행부터는 이 변수들 없이도 정상 동작합니다.

> 만약 캐시가 지워지거나(`rm -rf ~/.cache/gptqmodel`), 다른 GPU/다른 CUDA 버전으로 옮기면
> 재컴파일이 필요하므로 위 환경변수를 다시 export 해야 합니다.

## 3. 실행

### 단발성 (프롬프트를 인자로 전달)

```bash
conda activate harness
cd path/to/promptbench   # 이 저장소의 로컬 경로
python run_model.py "프롬프트 내용" --max-new-tokens 128
python run_model.py "프롬프트 내용" --model Qwen/Qwen2.5-7B-Instruct-AWQ

# 멀티라인/따옴표가 섞인 프롬프트는 쉘 이스케이핑이 번거로우니 파일로 넘기기
python run_model.py --prompt-file prompt.txt --max-new-tokens 128
```

`prompt`(위치 인자)와 `--prompt-file`은 동시에 줄 수 없습니다.

### 대화형 (반복 실행, 모델은 한 번만 로드)

프롬프트 인자 없이 실행하면 모델을 한 번만 로드한 뒤 계속 입력을 받습니다.
매번 스크립트를 새로 켜서 모델을 재로딩할 필요가 없습니다.

```bash
python run_model.py
> 안녕
(응답)
> 1+1은 뭐야?
(응답)
> exit
```

- `exit` / `quit` 입력 또는 Ctrl+D로 종료
- 각 프롬프트는 독립적으로 처리됨 (이전 대화 맥락 기억 안 함)

### 시스템 프롬프트 (`--system-prompt`)

단발성/대화형 모드에서 `--system-prompt "..."`로 시스템 프롬프트를 지정할 수 있습니다.
지정하지 않으면 기존과 동일하게 시스템 메시지 없이 동작합니다. 즉석에서 문구를 시험해볼 때만
쓰고, `guideline.md` 절차를 따르는 정식 실험 데이터는 아래 `scripts/generate.py`로 생성하세요
(레이어 문구를 파일로 고정해야 재현·재사용이 되기 때문).

```bash
python run_model.py "코드 리뷰해줘: ..." --system-prompt "항상 한국어로만 답변하세요."
```

### 실험 데이터 생성 (`scripts/generate.py`)

`guideline.md`의 phase 구조(baseline / phase1 / phase2)를 그대로 따라 `cases/cases.json`의
케이스를 모델에 돌리고 결과를 `runs/` 아래 JSON으로 저장합니다. 시스템 프롬프트는 CLI로 직접
넘기지 않고, `layers/candidates/{id}.md`(후보)·`layers/fixed/lang.md`(고정 레이어) 파일에서
`config/layers.py`가 조립합니다 — 문구를 파일로 고정해 Phase 1/2 사이에 다시 쓰지 않기 위함
(guideline.md 1-e).

```bash
# baseline: 고정 레이어도 후보도 없음
python scripts/generate.py --phase baseline --model 3b --n 5

# phase1: 후보 하나만 단독으로 (고정 레이어 없음, guideline.md 4-1)
python scripts/generate.py --phase phase1 --model 3b --condition H --n 5

# phase2: '+'로 이은 스택 (고정 레이어가 항상 마지막에 자동으로 붙음)
python scripts/generate.py --phase phase2 --model 3b --condition H+S --n 5

# 국지적 증량 (guideline.md 3-3): 특정 케이스만 N 추가 생성 (기존 run_idx 뒤에 이어붙음)
python scripts/generate.py --phase phase1 --model 3b --condition H --case case_04 --n 5
```

- `--condition`은 baseline에는 불필요, phase1/phase2에는 필수
- 후보 문구는 먼저 `layers/candidates/{id}.md`로 작성해야 함 (frontmatter: `id`, `target_cases`)
- `--n`은 "추가로" 생성할 횟수 — 기존 `run_XXX.json`이 있으면 그 다음 번호부터 이어서 생성 (증분)
- 결과는 케이스마다 항상 전체를 돌림 (0-B 규칙) — `--case`는 예산 부족 시 반복 횟수만 조절하는
  3-3 증량 절차 전용이지, 케이스를 골라서 빼는 용도가 아님
- 각 실행 파일에는 부록 A 스키마에 필요한 필드(`model`, `condition`, `fixed_layer`, `case_id`,
  `run_idx`, `target_flag`, `gen_params` 등)가 자동으로 채워짐

### 판정 (`scripts/judge.py`)

`runs/`에 쌓인 결과를 조건을 가린 채(blind) 하나씩 보여주고 2-2의 3단계 판정(위반/애매/위반
아님)과 2-4 사이드이펙트 등급을 입력받아 `judgments/`에 저장합니다.

```bash
python scripts/judge.py --phase phase1 --model 3b
python scripts/judge.py --phase phase1 --model 3b --condition H   # 특정 조건만
python scripts/judge.py --phase phase1 --model 3b --rejudge --frac 0.15  # 2-3 재판정 표본
```

- 아직 판정 안 된 항목만 무작위 순서로 큐에 올라감 (Ctrl+D로 중단해도 지금까지 판정한 건 저장됨)
- `--rejudge`는 이미 판정된 항목 중 `--frac` 비율만큼 무작위로 다시 판정 큐에 올림 (결과는
  `judgments/rejudge/`에 별도 저장 — 원 판정을 덮어쓰지 않음)

### 집계 & 순위 (`scripts/build_index.py`, `scripts/rank.py`)

```bash
python scripts/build_index.py   # runs/ + judgments/ -> derived/index.csv (부록 A 스키마)
python scripts/rank.py --model 3b --risk H:low,S:mid   # -> derived/ranking_3b.csv
```

- `build_index.py`는 재실행 시 매번 전체를 다시 만듦 (증분 아님) — `runs/`/`judgments/`가
  갱신될 때마다 다시 돌리면 됨
- `rank.py`의 `--risk`는 2-4 리스크 등급(낮음/중간/큼)을 조건별로 수동 지정 (아직 자동 분류
  기능은 없음, 생략하면 전부 `low`로 취급). 4-2 ③의 보수적 개선량(부록 B)으로 정렬

### 생성 파라미터 (`GEN_PARAMS`)

`model/inference.py`에 다음 값이 상수로 고정되어 있고, `--system-prompt`와 달리 **CLI로 노출되지
않습니다**:

```python
GEN_PARAMS = {
    "do_sample": True,
    "temperature": 0.7,
    "top_k": 20,
    "top_p": 0.8,
    "repetition_penalty": 1.05,
}
```

- 값은 `Qwen2.5-3B-Instruct-AWQ`/`Qwen2.5-7B-Instruct-AWQ` 체크포인트에 딸린
  `generation_config.json` 기본값과 동일합니다 (두 모델 모두 같음, `GenerationConfig.from_pretrained`로 확인).
- **왜 코드에 고정하고 CLI 옵션으로 안 만들었는가**: `guideline.md`의 0-A(실행 환경 고정 조건)에 따라
  baseline과 후보 실행 사이에 이 값들이 달라지면 비교 자체가 무효가 됩니다. CLI 옵션으로 열어두면
  실행마다 실수로 다른 값을 넘길 통로가 생기므로, 아예 코드에 박아서 그런 실수가 원천적으로
  불가능하게 만들었습니다.
- `scripts/generate.py`로 만든 실행 파일마다 `gen_params` 필드가 자동으로 같이 저장됩니다
  (`max_new_tokens`도 함께). 어떤 조건으로 생성됐는지 결과 파일만 보고도 바로 확인할 수
  있습니다 (`guideline.md` 부록 A의 기록 스키마 요건).
- 값을 바꿔야 한다면(예: 다른 모델 채용 등) `model/inference.py`의 `GEN_PARAMS`를 직접 수정하고,
  이후 실행되는 모든 baseline/후보 데이터가 같은 값을 쓰는지 반드시 확인하세요.

### 파일 구조

```
cases/cases.json            # 공통 입력 케이스 (모델 무관)
notes/scope-notes.md         # 관찰 로그 (모델 무관)

layers/
  candidates/{id}.md         # 후보 레이어 (frontmatter: id, target_cases)
  fixed/lang.md               # 고정 레이어 (guideline.md 4-1, 항상 스택 마지막)

runs/                        # scripts/generate.py 출력 (원본 생성 결과, 판정 전)
  baseline/{model}/{case_id}/run_001.json, run_002.json, ...
  phase1/{model}/{condition}/{case_id}/run_001.json, ...
  phase2/{model}/{stack_id}/{case_id}/run_001.json, ...   # stack_id 예: H+S

judgments/                   # scripts/judge.py 출력 (부록 A의 judgment/side_effect 등)
  {phase}/{model}/[condition/]{case_id}.jsonl
  rejudge/{phase}/{model}/[condition/]{case_id}.jsonl     # 2-3 재판정 표본 (원본과 별도)

derived/                     # scripts/build_index.py, scripts/rank.py 출력 (재생성 가능, git 미추적)
  index.csv                  # runs + judgments 조인 (부록 A 스키마)
  ranking_{model}.csv         # rank.py 결과 (4-2 순위)
```

`condition`은 phase1에서는 후보 ID 하나(`H`), phase2에서는 `+`로 이은 스택 ID(`H+S`)입니다.
baseline에는 조건이 없어 `condition` 레벨 디렉토리가 빠집니다. 같은 (phase, model, condition,
case_id) 조합에 반복 생성하면 `run_XXX.json` 번호가 이어서 붙습니다 (3-3 증량 시 재사용).

> `harness` 환경엔 `python`이 `python3`(3.12)를 가리키는 심볼릭 링크로 이미 걸려 있어 `python3` 대신 `python`으로 써도 됩니다.

## 4. basic-ai 환경과의 차이 (문제 원인)

이전에 쓰던 `basic-ai` conda 환경은 계속 실패해서 삭제됐습니다. 삭제 전 확인된 패키지 목록 기준으로:

| 패키지 | basic-ai | harness (현재) |
|---|---|---|
| torch | 2.13.0 | 2.13.0 |
| transformers | 5.14.1 | 5.16.1 |
| accelerate | 1.14.0 | 1.14.0 |
| autoawq | 0.2.9 | (설치 안 함, 불필요) |
| gptqmodel | **없음** | 7.3.5 |
| CUDA 컴파일러 (nvcc, 버전 일치) | 확인 안 됨 | 있음 (13.0.88) |

`gptqmodel`이 없었기 때문에 basic-ai에서 AWQ 모델을 로드하면 harness에서 처음 겪었던 것과
동일한 `ImportError`로 바로 실패했을 것으로 추정됩니다. (basic-ai는 원인 조사 전에 사용자가 직접 삭제하여
완전한 확인은 불가능했습니다.)
