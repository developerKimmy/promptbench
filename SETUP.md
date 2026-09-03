# 실행 환경 설정 가이드

`run_model.py`를 로컬 GPU에서 돌리기 위한 환경 구성 기록입니다.

> 관련 문서: 실험을 어떻게 설계할지(ablation, 반복 횟수, 후보 문구 작성 규칙 등)는
> [`guideline.md`](guideline.md), 실제 관찰 결과·재현성 검증 로그는
> [`baseline/scope-notes.md`](baseline/scope-notes.md) 참고.

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
```

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
export CUDA_HOME=/home/kimmy/miniconda3/envs/harness
export CXX=/home/kimmy/miniconda3/envs/harness/bin/x86_64-conda-linux-gnu-g++
export CC=/home/kimmy/miniconda3/envs/harness/bin/x86_64-conda-linux-gnu-gcc
```

이 세 변수는 **최초 1회 커널 컴파일에만** 필요합니다. 컴파일된 커널은
`~/.cache/gptqmodel/torch_extensions/`에 캐시되므로, 이후 실행부터는 이 변수들 없이도 정상 동작합니다.

> 만약 캐시가 지워지거나(`rm -rf ~/.cache/gptqmodel`), 다른 GPU/다른 CUDA 버전으로 옮기면
> 재컴파일이 필요하므로 위 환경변수를 다시 export 해야 합니다.

## 3. 실행

### 단발성 (프롬프트를 인자로 전달)

```bash
conda activate harness
cd /home/kimmy/project/promptbench
python run_model.py "프롬프트 내용" --max-new-tokens 128
python run_model.py "프롬프트 내용" --model Qwen/Qwen2.5-7B-Instruct-AWQ
```

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

### 배치 (JSON 질문 세트 → JSON 결과)

`--input`에 질문 세트 JSON 파일을, `--output`에 결과를 저장할 경로를 지정하면
모델을 한 번만 로드해서 모든 질문을 순차 처리하고 결과를 JSON으로 저장합니다.

입력 형식: 문자열 리스트이거나, 텍스트 필드가 있는 객체 리스트. 객체에서 텍스트를 찾을 때
`input` → `question` → `prompt` 순으로 키를 찾습니다. 객체의 다른 필드(`id` 등)는 그대로 유지되고
`answer` 필드만 추가됩니다.

```json
[
  "안녕, 너는 누구니?",
  {"question": "1+1은 뭐야?"},
  {"id": "case_01", "input": "..."}
]
```

실행:

```bash
python run_model.py --input questions.json --output answers.json --max-new-tokens 128

# 예: baseline/question.json ({"id", "input"} 형식) 처리
python run_model.py --input baseline/question.json --output baseline/3b/json/baseline.json --max-new-tokens 200
```

출력 형식 (`answers.json`) — 원본 객체 필드 + `answer`:

```json
[
  {"question": "1+1은 뭐야?", "answer": "..."},
  {"id": "case_01", "input": "...", "answer": "..."}
]
```

- `--input`을 쓰려면 `--output`도 반드시 같이 지정해야 함
- 채점/정답 비교 기능은 아직 없음 — 질문/응답 수집만 함
- `.md` 리포트가 자동으로 같이 생성됩니다. JSON은 `\n`이 이스케이프된 그대로 저장되지만
  (프로그램에서 읽을 때 정상 처리됨), 사람이 원본 파일을 에디터로 열어 눈으로 검토하기엔
  불편해서, 실제 줄바꿈으로 렌더링된 `.md` 리포트를 따로 남깁니다.
  - **`--output`의 부모 폴더 이름이 `json`이면** (예: `.../json/baseline.json`), `.md`는
    같은 이름으로 형제 폴더 `.../md/baseline.md`에 생성됩니다 (폴더가 없으면 자동 생성).
  - 그 외의 경로면 예전처럼 같은 폴더에 확장자만 바꿔서 생성됩니다 (예: `answers.json` → `answers.md`).

### 시스템 프롬프트 (`--system-prompt`)

단발성/대화형/배치 모든 모드에서 `--system-prompt "..."`로 시스템 프롬프트를 지정할 수 있습니다.
지정하지 않으면 기존과 동일하게 시스템 메시지 없이 동작합니다.

```bash
python run_model.py --input baseline/question.json \
  --output harness/ablation/lang/3b/json/result.json \
  --system-prompt "항상 한국어로만 답변하세요. 영어, 한자, 일본어, 중국어 단어를 섞지 마세요." \
  --max-new-tokens 512
```

프롬프트 수정만으로 관찰된 실패(언어 혼입, 할루시네이션 등)가 얼마나 개선되는지 실험할 때 사용합니다.
자세한 실험 결과는 `baseline/scope-notes.md` 참고.

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
- 배치 실행(`--input`/`--output`) 결과 JSON에는 각 항목마다 `gen_params` 필드가 자동으로 같이
  저장됩니다 (`max_new_tokens`도 함께). 어떤 조건으로 생성됐는지 결과 파일만 보고도 바로 확인할 수
  있습니다 (`guideline.md` 부록 A의 기록 스키마 요건).
- 값을 바꿔야 한다면(예: 다른 모델 채용 등) `model/inference.py`의 `GEN_PARAMS`를 직접 수정하고,
  이후 실행되는 모든 baseline/후보 데이터가 같은 값을 쓰는지 반드시 확인하세요.

### 결과 파일 구조: `baseline/` vs `harness/`

`baseline/`은 **시스템 프롬프트 없는 순수 무개입 결과만** 담습니다. 하네스 후보 실험은
`harness/` 아래 두 단계로 나눕니다 (자세한 방법론은 [`guideline.md`](guideline.md) 참고):

- **`harness/ablation/{후보명}/`** — 1단계: 각 후보를 baseline에 **단독으로만** 얹어 개별
  효과를 확인 (ablation). 아직 스태킹에 들어가지 않은 상태.
- **`harness/stacked/{순번}_{후보명}/`** — 2단계: ablation 결과를 보고 "효과 크고 리스크
  적은 순"으로 순서를 정해 누적. **언어 강제 지시는 규칙상 항상 마지막 번호로 고정.**

각 결과 폴더 안에서는 `json/`과 `md/`를 분리합니다 (파일이 많아지면 두 형식이 섞여 있으면
보기 어려워서 — `--output`을 `.../json/이름.json`으로 지정하면 위 규칙대로 `.md`가 자동으로
`.../md/이름.md`에 생성됩니다).

```
baseline/
  question.json             # 공통 입력 (모델 무관)
  scope-notes.md             # 관찰 로그 (모델 무관)
  3b/
    json/baseline.json       # 시스템 프롬프트 없는 기본 baseline
    md/baseline.md
    repro/                    # 재현성 검증용 반복 실행 결과
      json/baseline_1.json, baseline_2.json, ...
      md/baseline_1.md, baseline_2.md, ...
  7b/
    json/baseline.json
    md/baseline.md
    repro/
      json/...
      md/...

harness/
  ablation/
    lang/                    # 언어 강제 지시 후보 (단독 테스트, "항상 한국어로만 답변")
      3b/
        json/result.json
        md/result.md
        repro/
          json/result_1.json, result_2.json, ...
          md/result_1.md, result_2.md, ...
      7b/
        (동일 구조)
    {다음 후보명}/             # 새 후보(할루시네이션 억제 등)는 여기 단독 테스트로 먼저 추가
  stacked/                    # ablation 순서가 정해지면 여기 누적 (언어 지시는 항상 마지막)
```

`repro/`는 같은 조건을 여러 번 반복 실행해서 결과가 매번 재현되는지 확인할 때 씁니다 (언어 혼입처럼
확률적으로 나타나는 현상은 1회 실행만으로 결론 내리면 안 됨 — `baseline/scope-notes.md`의
"재현성 검증" 섹션 참고). 파일명은 `{조건}_{반복번호}.json`.

새 baseline 반복은 `baseline/{모델}/repro/json/baseline_{n}.json`, 새 ablation 후보는
`harness/ablation/{후보명}/{모델}/json/result.json` (+ `repro/json/result_{n}.json`)로
저장하세요. `.md`는 자동으로 형제 `md/` 폴더에 생성됩니다.

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
