# 스코프 노트 & 케이스별 관찰 로그

> 관련 문서: 환경/실행 방법은 [`../SETUP.md`](../SETUP.md), 실험 설계 방법론(ablation,
> 반복 횟수, 후보 문구 작성 규칙 등)은 [`../guideline.md`](../guideline.md) 참고. 이 문서는
> 실제 실행 결과와 관찰 로그를 담는다.

## 방법론 결정 사항 (계속 유효)

### case_01 관찰 범위 재설정
프로젝트 원래 목표는 "프롬프트 하네스가 Qwen 모델의 추론/지시이행 실패를 얼마나 개선하는가" 검증.
case_01("환불 어떻게 하나요?")은 실제 회사 정책 없이는 정확히 답할 수 없는 질문이라, 답변 품질
자체를 관찰 대상으로 삼지 않기로 함.

- ~~환불 절차를 정확히 안내했는지~~ → **평가 대상에서 제외** (정책 문서 없이는 애초에 정답이 없음)
- **유지**: 모르는 정보(주문번호 등)를 지어내지 않고 정직하게 처리하는지 여부만 관찰

RAG/정책 그라운딩은 하네스 실험과 별개의 이슈로 분리, 지금은 진행하지 않음 (백로그).

### 실패 태깅 기준
케이스별 관찰 시 아래 두 가지로 구분해서 기록:
- **하네스 후보**: 프롬프트 지시를 바꾸면 개선될 가능성이 있는 실패 (추론/지시이행 레벨)
- **모델 자체 한계**: 프롬프트로 못 고치는 실패 (디코딩/언어 혼입 등)

## 실험 이력

- **1차 실행**: max_new_tokens 부족으로 일부 응답이 중간에 잘림 (case_04 3B에서 발견).
  이전 관찰 기록 전체 폐기하고 재실행.
- **2차 실행**: max_new_tokens 상향 조정 후 재실행. **현재 진행 중인 회차.**

### 언어 관련 관찰 (case_04에서 도출, ⚠️ 미확인 추정)

두 가지 다른 현상으로 구분해서 봐야 할 것 같음 (모델이 원인을 명시한 적은 없고, 관찰된
상관관계로부터의 추정임):
1. **부분적 언어 혼입** (case_01, 03): 한국어 입력인데 응답 중간에 한자/일본어/중국어가 섞임.
   원인 불명, 간헐적.
2. **코드 포함 입력 → 전체 영어 응답** (case_04, 05): 입력에 코드가 포함되면 응답 전체가 영어로
   나옴. 원인은 추정 단계 — "입력 언어 감지" 때문일 수도, "코드=영어 학습 데이터 패턴 활성화"
   때문일 수도 있음. 현재 근거로는 구분 불가.
   → **검증 필요**: 시스템 프롬프트에 "항상 한국어로 답변" 지시를 추가했을 때 이 현상이 없어지는지
   실험해봐야 확정 가능. 그 전까지는 원인을 단정하지 않음.

## 케이스별 관찰 로그 (2차 실행)

### case_01 (extraction, 정책 의존 부분 제외하고 관찰)

observation_points: 모르는 정보(주문번호 등)를 지어내지 않고 정직하게 처리하는지

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> 어제 주문한 신발이 사이즈가 안 맞아서 환불하고 싶은데 어떻게 해야 하나요? 주문번호는 잘 모르겠고 어제 오후에 주문한 거예요. 빨리 처리해주세요 화가 많이 나네요

**3B 답변:**

> 알겠습니다, 환불을 원하시는 점에 대해 이해했습니다. 아래에 몇 가지 단계와 제안사항을 알려드릴게요:
>
> 1. **주문 번호 확인**: 혹시 카드 결제 내역이나 문자 메시지, 이메일 등에서 주문 번호를 확인해보셨나요? 만약 아직 확인되지 않으신다면, 해당 기능을 다시 확인해보세요.
>
> 2. **환불 요청**: 환불을 원하신다면, 먼저 판매자에게 연락하여 환불을 요청해보세요. 판매자가 판매 상품의 사이즈를 잘못 확인했거나, 고객 서비스를 통해 이를 해결해주실 수 있습니다.
>
> 3. **Alibaba Cloud 고객 지원**: Alibaba Cloud에서는 다양한 고객 서비스를 제공하고 있습니다. 만약 판매자가 문제를 해결하지 않으신다면, Alibaba Cloud 고객 지원에 연락해보세요.
>
>    - **연絡 방법**: 고객센터로 전화하거나, 온라인으로 문의하실 수 있습니다.
>    - **문의 내용**: 주문 번호, 제품 정보, 환불 요구 사유 등을 설명해주세요.
>
> 4. **결제 및 환불**: 판매자가 환불을 처리한 후, 환불手続き에 따라 돈이 반환되길 기대하세요.
>
> 5. **알림**: 판매자가 환불 요청에 대한 답변을 보내는 경우, 알림 메시지를 받으실 수 있습니다.
>
> 환불 과정에서 불편함이 많으신 것 같아 죄송합니다. 가능한 빠른 시간 내에 문제를 해결하도록 최선을 다하겠습니다.

**7B 답변:**

> 먼저 불편을 겪으신 것에 대해 안타깝게 생각합니다. 하지만 걱정하지 마시고 다음 단계를 따라 주문 취소 및 환불 절차를 진행해보세요.
>
> 1. **구매 사이트 접속**: 먼저 구매한 온라인 쇼핑몰의 웹사이트로 접속합니다.
> 2. **마이페이지 이동**: 로그인 후 마이페이지 또는 주문 관리 섹션으로 이동합니다.
> 3. **주문 내역 확인**: 최근 주문 목록을 확인하여 어제 주문한 신발의 정보를 찾습니다. 주문 번호는 일반적으로 주문 확인 페이지나 발송 정보에 명시되어 있습니다.
> 4. **환불/반품 신청**: 해당 주문에 대해 환불 또는 교환을 신청합니다. 주문 상세 페이지에서 "환불/반품" 버튼을 클릭하거나, 마이페이지에서 관련 메뉴를 선택할 수 있습니다.
> 5. **사유 입력**: 사이즈가 맞지 않아 환불하고 싶다는 이유를 입력합니다.
> 6. **증빙 사진 첨부**: 가능한 한 신발과 발을 함께 찍은 사진을 첨부합니다. 이는 사이즈와 형태가 다른지 확인하는 데 도움이 됩니다.
> 7. **확인 및 제출**: 모든 정보를 확인 후 제출합니다.
>
> 만약 주문 번호를 찾지 못한다면, 고객센터에 연락하여 주문 정보를 확인할 수 있습니다. 또한, 환불 처리 시간은 각 쇼핑몰마다 다를 수 있으니, 대략적인 처리 기간을 미리 알고 계세요.
>
> 불편을 겪으신 것을 다시 한번 죄송합니다. 빠르게 처리될 수 있도록 노력하겠습니다.

</details>

- **3B**:
  - ⚠️ **할루시네이션**: "Alibaba Cloud 고객 지원"이라는 맥락과 무관한 정보를 지어냄
    (신발 환불 문의에 뜬금없이 특정 회사명 언급). observation_point가 잡으려던 실패의 전형적 사례.
  - ⚠️ **언어 혼입 재발**: "연絡"(일본어 한자), "환불手続き"(일본어 단어 혼입).
    1차 실행(토큰 부족 상황)에서도 유사 증상이 있었는데, 토큰을 늘린 2차에서도 재현됨
    → **토큰 부족이 원인이 아니라 3B 모델 자체의 반복적 특성**으로 판단.
  - 태깅: 모델 자체 한계 (언어 혼입) / 하네스 후보 가능성 있음 (할루시네이션 — "모르면 모른다고 해"
    류 강한 지시로 개선 여지 있는지 실험해볼 만함)
- **7B**:
  - 지어낸 정보 없음, 주문번호 못 찾을 시 고객센터 안내로 정직하게 처리
  - 언어 혼입 없음
  - 태깅: 실패 없음 (case_03에서 나왔던 중국어 혼입은 이번엔 미재현 — 간헐적 발생 가설 유지)

### case_02 (extraction)

observation_points: 6개 필드(이름/연락처/제품/수량/배송일/주소) 빠짐없이 추출

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> 안녕하세요, 김철수입니다. 010-1234-5678로 연락 주시고, 제품은 노트북 2대(모델명: XPS15), 배송은 다음주 화요일 오전 중으로 부탁드려요. 회사는 서울 강남구에 있습니다.

**3B 답변:**

> 안녕하세요, 김철수님. 고객님의 요청사항을 확인했습니다.
>
> - 연락처: 010-1234-5678
> - 구매하실 제품: 노트북 2대 (모델명: XPS15)
> - 배송 요청: 다음주 화요일 오전 중
>
> 위 내용이 정확하신가요? 추가로 필요한 정보나 주문 상세를 알려주시겠어요? 또한, 서울 강남구에 위치한 회사 소식이나 기타 궁금하신 점 있으신가요?

**7B 답변:**

> 안녕하세요, 김철수님.
>
> 저는 고객님의 요청을 받았습니다. 제품은 노트북 2대 (모델명: XPS15)이며, 배송 날짜와 시간대는 고객님의 요청대로 다음주 화요일 오전 중으로 정해졌습니다.
>
> 다음은 고객님의 주문 정보를 요약하겠습니다:
>
> - 고객 이름: 김철수
> - 연락처: 010-1234-5678
> - 주문 제품: 노트북 2대 (모델명: XPS15)
> - 배송 날짜 및 시간: 다음주 화요일 오전 중
> - 회사 주소: 서울 강남구
>
> 추가로 필요한 정보나 변경 사항이 있으신가요? 또는 다른 도움이 필요하시면 언제든지 말씀해주세요.

</details>

- **3B**:
  - 연락처 ✅ / 제품·수량 ✅ / 배송일 ✅
  - 이름(김철수) — 인사말에만 등장, 정리된 목록엔 미포함
  - ⚠️ 회사 주소 — 목록에 없고 "서울 강남구에 위치한 회사 소식이나 기타 궁금하신 점 있으신가요?"라는
    어색한 문장으로 얼버무림. 주소 정보를 필드로 제대로 인식하지 못한 것으로 보임.
  - 언어 혼입 없음
  - 태깅: 하네스 후보 (다중 필드 추출 시 "누락 없이 목록으로 정리" 지시로 개선 가능성)
  - 참고: 1차 실행에서도 3B는 연락처를 누락했었음 — 어떤 필드를 빠뜨리는지는 매번 다르지만,
    **다중 필드 추출 자체가 3B의 일관된 약점**이라는 큰 그림은 1차/2차 모두 재확인됨.
- **7B**:
  - 6개 필드 모두 목록으로 명확히 정리, 언어 혼입 없음
  - 태깅: 실패 없음

### case_03 (extraction, 함정/모순 정보 케이스)

observation_points: 이름 정정을 제대로 반영하는지 / 명시 안 된 정보를 지어내지 않는지

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> 문의드립니다. 제 이름은 박영희이고 이전에 이영희로 등록했었는데 그건 오타였습니다. 주문은 3개 했는데 그 중 2개만 취소하고 싶어요. 참고로 배송지는 이전과 동일합니다.

**3B 답변:**

> 알겠습니다, 박영희님. 이해했습니다. 주문 중에서 2개를 취소하고 싶으셨군요. 배송지가 동일하다는 점도 확인했습니다.
>
> 취소를 진행하는 과정을 설명드리겠습니다:
>
> 1. 현재 상태: 주문은 총 3개이며, 그 중 1개만 취소되었습니다.
> 2. 변경 요청: 2개를 취소하고 싶으신데, 이를 처리하겠습니다.
>
> 취소를 진행하기 위해선 몇 가지 단계가 필요할 수 있습니다. 계정 설정에서 결제 관련 설정을 확인하시거나, 고객센터에 문의하시는 것도 방법입니다.
>
> 취소가 완료되면, 남은 주문 상품에 대해 다시 배송을 요청하실 수 있습니다. 혹시 다른 도움이 필요한 점이 있으시다면 알려주세요.

**7B 답변:**

> 안녕하세요, 박영희님.
>
> 먼저 이름 오류를 수정해 주신 것에 감사드립니다. 그리고 배송지를 동일하게 유지하실 계획이라면, 주문 취소 절차가 좀 더 쉽습니다.
>
> 이번에 주문한 상품 중 2개를 취소하고 싶으시다면, 먼저 해당 주문 내역을 확인하시고, 취소할 제품의 정보를 알려주시면 도와드리겠습니다.
>
> 주문 취소는 대체적으로 온라인 플랫폼에서 제공하는 관리 페이지나 고객센터를 통해 가능합니다.
>
> 1. 먼저, 관련 플랫폼의 주문 관리 페이지로 접속해 주문 내역을 확인합니다.
> 2. 취소하고 싶은 주문에 마우스를 올려보면 '취소' 버튼이 보일 것입니다.
> 3. '취소' 버튼을 클릭하면 해당 주문이 취소됩니다.
>
> 만약 구체적인 주문 번호나 상품명, 취소하려는 주문의 세부 정보 등을 알려주시면, 더 정확한 조언을 드릴 수 있을 것 같습니다.

</details>

- **3B**:
  - 이름 정정 명시적 언급 없음 (1차와 동일 패턴 — 그냥 정정된 이름으로만 호칭)
  - 배송지 관련 지어낸 정보 없음
  - ⚠️ **새 할루시네이션**: "그 중 1개만 취소되었습니다" — 입력에 없는 주문 상태를 임의로 지어냄.
    case_01(회사명 지어냄)과 같은 뿌리의 문제로 보임: **확인 안 된 정보를 그럴듯하게 채워 넣는 경향**.
  - 언어 혼입 없음
  - 태깅: 하네스 후보 (할루시네이션 억제 지시 실험 대상) / 모델 자체 한계 가능성도 있음
- **7B**:
  - 이름 정정 명시적으로 인지·반영 (1차와 동일하게 우수)
  - 배송지/상태 관련 지어낸 정보 없음
  - 언어 혼입 없음 — 1차의 중국어 혼입이 이번엔 미재현 (간헐적 발생 가설 강화, 표본 부족은 여전)
  - 태깅: 실패 없음

### case_04 (code_fix)

observation_points: ZeroDivisionError 처리 추가 여부

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> def divide(a, b):
>     return a / b

**3B 답변:**

> The function `divide(a, b)` you provided is a simple Python function that performs division of two numbers. However, it's important to handle edge cases and potential errors that might occur during execution. Here's the function with some error handling added:
>
> ```python
> def divide(a, b):
>     try:
>         result = a / b
>     except ZeroDivisionError:
>         return "Error: Division by zero is not allowed."
>     except TypeError:
>         return "Error: Both inputs must be numeric."
>     except Exception as e:
>         return f"An unexpected error occurred: {e}"
>     else:
>         return result
> ```
>
> ### Explanation of the changes:
>
> 1. **Try-Except Block**:
>    - The `try` block attempts to execute the division operation.
>    - If a `ZeroDivisionError` occurs (when dividing by zero), it catches this exception and returns an appropriate message.
>    - If a `TypeError` occurs (if the inputs are not numeric), it catches this exception and returns another appropriate message.
>    - The `else` block executes if no exceptions occur, returning the result of the division.
>
> 2. **Exception Handling**:
>    - By using specific exception types (`ZeroDivisionError`, `TypeError`), we can provide more informative error messages for common issues.
>    - The `except Exception as e` clause is used as a catch-all for any other type of exception, providing a more general error message in case of unknown errors.
>
> 3. **Edge Cases**:
>    - This function now handles cases where either or both arguments are not numeric (e.g., non-numeric strings) by catching a `TypeError`.
>    - It also handles division by zero by catching a `ZeroDivisionError`.
>
> ### Example Usage:
>
> Here's how you can use the updated function:
>
> ```python
> print(divide(10, 2))  # Output: 5.0
> print(divide(10, 0))  # Output: Error: Division by zero is not allowed.
> print(divide('10', '2'))  # Output: Error: Both inputs must be numeric.
> print(divide('a', 'b'))  # Output: Error: Both inputs must be numeric.
> ```
>
> This function ensures that your program can gracefully handle invalid inputs and potential runtime errors.

**7B 답변:**

> The function `divide` you've provided is a simple implementation of division. It takes two parameters, `a` and `b`, and returns the result of dividing `a` by `b`. However, it's important to note that this function does not handle cases where `b` is zero, which would result in a division by zero error.
>
> Here is the function with a brief explanation:
>
> ```python
> def divide(a, b):
>     """
>     Divide a by b.
>
>     Parameters:
>     a (float or int): The dividend.
>     b (float or int): The divisor.
>
>     Returns:
>     float: The result of the division.
>
>     Raises:
>     ZeroDivisionError: If b is 0.
>     """
>     if b == 0:
>         raise ZeroDivisionError("division by zero")
>     return a / b
> ```
>
> This version of the function includes a check for `b` being zero and raises a `ZeroDivisionError` if this condition is met. This helps prevent the program from crashing due to an unhandled exception.
>
> Here's an example of how you might use this function:
>
> ```python
> try:
>     result = divide(10, 2)
>     print(f"Result: {result}")
> except ZeroDivisionError as e:
>     print(f"Error: {e}")
> ```
>
> This will output:
>
> ```
> Result: 5.0
> ```
>
> And if you try to divide by zero:
>
> ```python
> try:
>     result = divide(10, 0)
>     print(f"Result: {result}")
> except ZeroDivisionError as e:
>     print(f"Error: {e}")
> ```
>
> This will output:
>
> ```
> Error: division by zero
> ```

</details>

- **3B**: try/except로 ZeroDivisionError, TypeError, 일반 Exception까지 처리. 1차의 응답 잘림
  문제가 토큰 증가로 해결됨 확인. 응답 전체가 영어 (코드 포함 시 영어 응답 패턴, 위 참고). 충족.
- **7B**: `if b == 0: raise ZeroDivisionError(...)` 명시적 처리, docstring/사용 예시 포함.
  마찬가지로 응답 전체 영어. 충족.
- 둘 다 observation_point 충족. code_fix 카테고리는 지금까지(case_04) 3B/7B 모두 무난.

### case_05 (code_fix)

observation_points: off-by-one 버그를 실제로 찾아내는지

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> def get_last_n_items(lst, n):
>     return lst[len(lst) - n + 1:]

**3B 답변:**

> The function `get_last_n_items(lst, n)` you've provided is designed to return the last `n` items from a list `lst`. However, there's a small issue with the indexing in the function.
>
> In Python, list indices start at 0. So, `len(lst) - n + 1` will give you the index of the item that should be the first item from the end, but it needs to be adjusted to account for zero-based indexing correctly.
>
> Here's the corrected version of your function:
>
> ```python
> def get_last_n_items(lst, n):
>     return lst[-n:]
> ```
>
> This works because `lst[-n:]` directly returns the last `n` elements of the list without needing to manually calculate the index.
>
> Let's test this function with some examples:
>
> ```python
> # Example usage:
> print(get_last_n_items([1, 2, 3, 4, 5], 2))  # Output: [4, 5]
> print(get_last_n_items(['a', 'b', 'c', 'd'], 3))  # Output: ['c', 'd']
> print(get_last_n_items([10, 20, 30, 40, 50], 1))  # Output: [50]
> ```
>
> These tests should work as expected.

**7B 답변:**

> It looks like you want to retrieve the last `n` items from a list, but there's a small mistake in your slicing logic. The correct way to slice the list to get the last `n` items is to start from index `-n` and go until the end of the list. Here's the corrected version:
>
> ```python
> def get_last_n_items(lst, n):
>     return lst[-n:]
> ```
>
> This function will correctly return the last `n` elements of the list `lst`.
>
> Here's an example of how you can use it:
>
> ```python
> my_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
> n = 4
> print(get_last_n_items(my_list, n))  # Output: [7, 8, 9, 10]
> ```
>
> In this example, `get_last_n_items(my_list, 4)` returns the last four elements of the list, which are `[7, 8, 9, 10]`.

</details>

- **3B**: `len(lst) - n + 1`이 잘못됐음을 정확히 진단, `lst[-n:]`으로 올바르게 수정. 테스트 예시 정확.
- **7B**: 동일하게 정확히 진단·수정.
- 둘 다 충족, 새로운 실패 없음. 응답 전체 영어 (코드 포함 시 영어 응답 패턴과 일치, case_04 참고).

### case_06 (code_fix)

observation_points: "버그 고쳐줘" 지시만으로 O(n^2) 비효율까지 잡아내는지

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> def has_duplicates(lst):
>     for i in range(len(lst)):
>         for j in range(len(lst)):
>             if i != j and lst[i] == lst[j]:
>                 return True
>     return False

**3B 답변:**

> The code you provided is almost correct, but it's not efficient. The function `has_duplicates` checks for duplicates in the list `lst` using nested loops, which results in a time complexity of O(n^2), where n is the length of the list. This can be improved.
>
> A more efficient approach would be to use a set to keep track of the elements we've seen so far. If we encounter an element that is already in the set, then we know there are duplicates. Here's how you could implement this:
>
> ```python
> def has_duplicates(lst):
>     seen = set()
>
>     for item in lst:
>         if item in seen:
>             return True
>         seen.add(item)
>
>     return False
> ```
>
> This solution has a time complexity of O(n), making it much more efficient for larger lists. Let me explain how it works:
>
> 1. We initialize an empty set called `seen`.
> 2. We iterate through each item in the list.
> 3. For each item, we check if it is already in the `seen` set.
>    - If it is, we return `True` because we have found duplicates.
>    - If it is not, we add the item to the `seen` set.
> 4. If we finish iterating without finding any duplicates, we return `False`.
>
> This approach ensures that we only need to traverse the list once and use the set operations efficiently.

**7B 답변:**

> The function `has_duplicates` you've provided is designed to check if a list contains any duplicate elements. However, the implementation can be optimized and simplified. The current implementation uses a nested loop to compare each pair of elements in the list, which results in a time complexity of O(n^2). A more efficient approach would have a time complexity of O(n) using a set.
>
> Here's an improved version of your function:
>
> ```python
> def has_duplicates(lst):
>     seen = set()
>     for item in lst:
>         if item in seen:
>             return True
>         seen.add(item)
>     return False
> ```
>
> This version works as follows:
> 1. It initializes an empty set called `seen`.
> 2. It iterates through each item in the list.
> 3. For each item, it checks if the item is already in the set `seen`.
> 4. If the item is found in the set, it means there is a duplicate, so the function returns `True`.
> 5. If the item is not found, it adds the item to the set and continues.
> 6. If no duplicates are found after checking all items, the function returns `False`.
>
> This approach is much more efficient, especially for larger lists, because it only requires a single pass through the list.

</details>

- **3B**: 실제 버그는 없다고 인지("almost correct")하면서도, 요청하지 않은 O(n^2) 효율성 문제를
  스스로 판단해 O(n) set 기반으로 개선. 설명도 논리적.
- **7B**: 동일한 패턴 — 버그 없음 인지 + 효율성까지 자발적으로 개선.
- 둘 다 지시 범위(버그 수정)를 넘어 효율성까지 손댐. 결과적으로는 더 나은 답이지만,
  **지시하지 않은 것까지 임의로 판단해서 처리하는 경향**으로 볼 수 있음
  (case_03의 "주문 상태 지어냄"과 유사한 결의 패턴 — 확인/지시 안 된 것을 스스로 채워 넣음).
  → 하네스 후보: "지시한 것만 정확히 고쳐줘" 류 제약이 이 행동을 억제하는지 검증 가치 있음.

### case_07 (code_fix, 모호한 요구사항 케이스)

observation_points: 되묻지 않고 임의로 확장하는지 (정답 없음, 판단 기준)

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> def validate_email(email):
>     return "@" in email

**3B 답변:**

> The function you provided is a simple check to see if an email address contains the "@" symbol. This is not a full validation of an email address, which typically includes checking for a valid format and ensuring that the domain part of the email exists.
>
> Here's a more comprehensive function using Python's `re` module (for regular expressions) and `validate_email` library from `validator.py`:
>
> ```python
> import re
> from validator import Email
>
> def validate_email(email):
>     try:
>         # First, attempt to validate the email using the Email class
>         Email(email)
>         # If no exception is raised, the email is considered valid
>         return True
>     except Exception as e:
>         # If there was an exception, the email is not valid
>         return False
>
> # Example usage:
> email = "example@domain.com"
> print(validate_email(email))  # Output: True or False based on validity
> ```
>
> In this code:
> - We use the `Email` class from the `validator` library to validate the email.
> - If the email is valid, it returns `True`.
> - If the email is invalid (e.g., missing parts), it raises an exception, and we catch this exception to return `False`.
>
> If you want to implement the validation without relying on external libraries, here's a basic example:
>
> ```python
> def validate_email(email):
>     # Check if the email starts with a letter or digit and ends with a letter or digit
>     if not re.match(r'^[a-zA-Z0-9]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$', email):
>         return False
>
>     # Further checks can be added here, such as ensuring the domain exists
>     try:
>         # Attempt to connect to the domain (simplified example)
>         import socket
>         socket.gethostbyname(email.split('@')[1])
>         return True
>     except socket.gaierror:
>         return False
>
> # Example usage:
> email = "example@domain.com"
> print(validate_email(email))  # Output: True or False based on validity
> ```
>
> This function performs some basic checks but still doesn't fully validate an email according to standards. For robust email validation, consider using a dedicated library like `validator.py`.

**7B 답변:**

> The function you've provided is a very basic way to check if an email string contains an "@" symbol. While this can be a quick and easy way to perform a preliminary check, it's not sufficient for validating the full structure and validity of an email address. Here are some limitations and considerations:
>
> 1. **Basic Check**: It only checks for the presence of an "@" symbol.
> 2. **Lack of Structure**: It doesn't check the format or structure of the email (e.g., domain name).
> 3. **Security Concerns**: It doesn't verify if the domain actually exists.
>
> For more robust validation, you might want to use a regular expression that checks for a more complete email structure. Here's an example using Python's `re` module:
>
> ```python
> import re
>
> def validate_email(email):
>     # Regular expression pattern for validating an email
>     pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
>
>     # Compile the regex pattern
>     regex = re.compile(pattern)
>
>     # Check if the email matches the pattern
>     if regex.match(email):
>         return True
>     else:
>         return False
> ```
>
> This function uses a regular expression to check if the email conforms to a standard format. Here's what the pattern does:
>
> - `^[a-zA-Z0-9._%+-]+`: The local part of the email (before the @) must start with alphanumeric characters and include other allowed symbols.
> - `@`: The literal "@" symbol.
> - `[a-zA-Z0-9.-]+`: The domain part must contain alphanumeric characters, periods, and hyphens.
> - `\.[a-zA-Z]{2,}$`: The top-level domain (TLD) must start with a dot followed by at least two alphabetic characters.
>
> This should give you a more reliable way to validate email addresses.

</details>

- **3B**: 되묻지 않고 바로 2가지 방법을 장황하게 제시.
  ⚠️ `from validator import Email`처럼 실존 여부가 불확실한 라이브러리를 검증 없이 사용
  (case_01 "Alibaba Cloud", case_03 "주문 1개 취소됨"과 같은 결의 API 할루시네이션 가능성).
  ⚠️ 두 번째 코드 예시에 `import re` 누락 — 그대로 실행하면 NameError 발생하는 실제 버그.
  추가로 DNS 조회(`socket.gethostbyname`)까지 붙여 요구 범위를 크게 초과.
- **7B**: 마찬가지로 되묻지 않음. 정규식 하나로 정리, import 정상, 과도한 외부 확장 없음.
  3B보다 정확하고 절제된 확장.
- **공통 패턴**: 두 모델 다 모호한 요구사항에서 명확화 질문 없이 바로 확장·구현함 (case_06의
  "지시 안 한 것도 알아서 처리" 경향과 일치). 하네스 후보: "불명확하면 먼저 질문해" 지시 실험 가치 있음.

### case_08 (summarization)

observation_points: 담당자 정확히 매칭 / 잡담과 액션 아이템 구분

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> 오늘 회의에서 A안으로 진행하기로 했습니다. 다음 주까지 철수님이 디자인 시안 3개를 준비하고, 영희님은 예산안을 검토해주세요. 참고로 지난주 회식은 다들 만족하셨다고 하네요. 다음 회의는 다다음주 화요일 오후 2시입니다.

**3B 답변:**

> 알겠습니다, 이해했습니다. 다음 주 일정을 확인해 주셔서 감사합니다.
>
> - 철수님께서 디자인 시안 3개를 준비해주시면, 그 내용을 보고 결정하도록 하겠습니다.
> - 영희님께서 예산안을 검토해주시면, 예산 조사 결과를 바탕으로 다음 회의에서 결정하도록 하겠습니다.
>
> 또한, 지난주 회식에 대한 피드백이 모두 만족하셨다고 말씀하신 것 같습니다. 이를 감안하여 앞으로도 좋은 회식을 기대하겠습니다.
>
> 다음 회의는 다다음주 화요일 오후 2시로 예정되어 있습니다. 일정 변경 여부를 알려주시면 감사하겠습니다.
>
> 감사합니다.

**7B 답변:**

> 좋아요, 오늘 회의에서의 결정사항을 정리해보겠습니다:
>
> 1. **디자인 시안**: 철수님이 다음 주까지 디자인 시안 3개를 준비할 예정입니다.
> 2. **예산안**: 영희님이 예산안을 검토하여 준비할 예정입니다.
> 3. **회식에 대한 피드백**: 지난 주 회식에 대해 동료们都表示了满意。
>
> 4. **下次会议时间**：下下周二下午2点。
>
> 如果您需要进一步的安排或有其他事项需要讨论，请告诉我。我可以帮助您整理和规划。

</details>

- **3B**: 담당자 매칭 정확(철수→디자인, 영희→예산), 회식 피드백을 액션 아이템과 구분해서 언급.
  언어 혼입·할루시네이션 없음.
- **7B**: 담당자 매칭은 정확하지만, ⚠️ **후반부가 통째로 중국어로 전환**
  ("동료们都表示了满意", "下次会议时间：下下周二下午2点" 등). case_03보다 더 심하고 후반부에 집중.
  → **반례 발견**: 이 케이스는 순수 한국어 텍스트 입력인데도 중국어 혼입이 나옴. case_04/05의
  "코드 포함 시 영어 응답" 관찰과는 무관한 현상 — 코드 유무로 언어 혼입을 설명할 수 없음을 시사.
  이번 회차에서는 오히려 3B가 더 안정적이었음.
  (토큰 부족으로 인한 불안정 가능성 검토: 응답이 완결된 마무리 문장으로 끝나 중간에 잘린 흔적
  없음 → truncation이 아니라 끝까지 생성된 응답 안에서 언어가 전환된 것으로 판단)

### case_09 (summarization)

observation_points: 결론·이견 구분해서 요약 / 한쪽으로 왜곡하지 않기

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> 이번 마케팅 예산에 대해 마케팅팀은 늘려야 한다고 했고, 재무팀은 동결해야 한다고 주장했습니다. 결국 이번 분기는 동결하되 다음 분기에 재검토하기로 잠정 합의했습니다.

**3B 답변:**

> 이 상황에서는 마케팅과 재무 두 팀 간의 의견을 수렴하고, 적절한 결정을 내리는 것이 중요합니다.
>
> 마케팅 예산 증가를 주장한 마케팅팀은 고객들과 시장의 변화에 더 잘 대응할 수 있는 가능성을 제시했을 것입니다. 반면 재무팀의 의견은 예산을 확대하는 것은 현재 회사의 재무 상태와 목표에 부합하지 않는다는 점을 보여주었습니다.
>
> 재무팀과 마케팅팀 간의 이견을 해결하기 위해 다음과 같은 접근 방식을 고려해 볼 수 있습니다:
>
> 1. **데이터 기반의 결정**: 예산 증감을 결정할 때 사용되는 데이터를 분석하여 각 팀의 주장이 근거가 되었는지 확인합니다.
>
> 2. **SWOT 분석**: 각 팀의 강점, 약점, 기회, 위협을 파악하여 이를 바탕으로 새로운 예산 설정을 제안할 수 있습니다.
>
> 3. **균형 잡힌 접근**: 재무팀의 경제적인 관점을 고려하면서도, 마케팅팀의 시장 전략을 지원하기 위한 적절한 예산을 확보하는 방법을 모색합니다.
>
> 4. **잠정 합의**: 잠정적으로 재무팀의 의견을 따르되, 다음 분기에는 예산을 재검토하여 새로운 조건들을 고려할 계획입니다.
>
> 5. **간접적인 해결책**: 예를 들어, 다른 비용 항목에서 일부 예산을 재배치하거나, 온라인 마케팅에 중점을 둔 비용을 증가시키는 등의 방안을 검토해 볼 수도 있습니다.
>
> 결국, 이러한 문제를 해결하기 위해서는 각 팀의 의견을 충분히 수렴하고, 각각의 요구 사항을 충족하면서 동시에 전체 조직의 목표를 고려해야 합니다.

**7B 답변:**

> 그 결정은 상당히 현명한 것으로 보입니다. 마케팅 예산을 늘리는 것은 성장과 경쟁력을 유지하는 데 도움이 될 수 있지만, 현재의 경제 환경이나 다른 비용 항목들에 대한 고려도 필요합니다. 이번 분기에 동결하고 다음 분기에 재검토하는 것은 유동성을 유지하면서도 미래의 필요성에 대비할 수 있게 해줍니다.
>
> 다음 분기에는 다음과 같은 요인들을 다시 검토해보는 것이 좋겠습니다:
>
> 1. **마케팅 효과성**: 현재 사용 중인 마케팅 캠페인의 성과를 분석합니다. 어떤 채널이나 방법이 더 효과적인지 파악합니다.
> 2. **시장 동향**: 경쟁사의 움직임, 시장의 변화, 고객의 요구사항 등을 살펴봅니다.
> 3. **예산 절감 가능성**: 다른 부서와 협력하여 예산을 효율적으로 사용할 수 있는 방법을 찾아볼 수 있습니다.
> 4. **재무상태**: 회사의 재무상태와 예상되는 경제 환경을 고려합니다.
>
> 이러한 정보들을 바탕으로 다음 분기에 예산을 조정할 수 있도록 준비하면 좋습니다.

</details>

- **3B**: 결론(재무팀 의견 따름+다음 분기 재검토)과 양측 입장이 텍스트에 포함되긴 하나,
  ⚠️ **요약이 아니라 "이견 해결을 위한 컨설팅 조언"으로 지시 이탈**(SWOT 분석 제안 등).
  편향은 없음(양측 균형 있게 언급).
- **7B**: ⚠️ 같은 유형의 지시 이탈, 더 심함. "그 결정은 상당히 현명한 것으로 보입니다"라며
  **입력에 없는 자기 의견(가치평가)을 먼저 제시**하고, 다음 분기 검토 요인을 새로 제안하는
  조언 형태로 전개. 편향은 없음.
- **새 실패 유형**: "요약해줘" 지시인데 둘 다 조언/분석 모드로 전환. 지금까지 카테고리 중
  처음 나온 패턴 — 하네스 후보: "사실관계만 요약, 의견·제안 추가하지 말 것" 류 명시적 제약 필요.

### case_10 (summarization)

observation_points: 핵심 결정사항만 걸러내는지 / 장황하지 않은지

<details>
<summary>예시 보기 (입력 / 3B 답변 / 7B 답변)</summary>

**입력:**

> 오늘 논의된 내용을 말씀드리면, 먼저 지난주 이슈였던 서버 장애 건에 대해 다시 얘기가 나왔는데요, 결론적으로는 근본 원인이 메모리 누수였다는 게 확인되었고, 이 부분은 개발팀이 다음 스프린트에 패치하기로 했습니다. 그리고 어제도 비슷한 얘기가 있었는데 이건 별개로 모니터링 대시보드를 새로 만들자는 의견도 나왔었고, 결국 이것도 개발팀이 맡기로 했는데 아직 일정은 미정입니다.

**3B 답변:**

> 알겠습니다, 이해했습니다. 지난 주에 서버 장애 문제에서 메모리 누수가 근본 원인으로 결정되어 개발 팀이 다음 스프린트에 패치 작업을 진행하겠다는 결론을 내렸습니다.
>
> 또한, 어제 논의된 다른 내용으로는 모니터링 대시보드를 새롭게 만드는 의견이 제기되었는데, 이를 개발 팀이 담당하도록 결정되었지만 아직 일정은 정해지지 않았다는 점도 기억했습니다.
>
> 이번 회의에서 논의된 내용들을 정리하고, 개발 팀과 협의하여 진행할 일정을 정해 나갔으면 좋겠습니다.

**7B 답변:**

> 오늘 논의된 내용을 요약하면 다음과 같습니다:
>
> 1. **서버 장애 문제**: 지난 주 발생한 서버 장애에 대한 이야기가 재조명되었습니다. 결론적으로, 서버 장애의 근본 원인은 메모리 누수가 확인되었습니다. 이를 해결하기 위해 개발팀이 다음 스프린트에 패치 작업을 진행하기로 결정했습니다.
>
> 2. **모니터링 대시보드 개발**: 어제는 새로운 모니터링 대시보드를 만드는 의견이 제기되었습니다. 이 작업도 개발팀이 맡기로 했지만, 아직 일정은 정해지지 않았습니다.
>
> 이러한 내용들이 오늘 회의에서 논의되었습니다.

</details>

- **3B**: 두 핵심(서버 장애=메모리 누수/다음 스프린트 패치, 모니터링 대시보드=개발팀 담당/일정
  미정) 정확히 포착, 할루시네이션 없음. 단, 끝에 "일정을 정해나갔으면 좋겠습니다"라는 요청 안 한
  제안을 덧붙임 — case_09의 "조언 모드로 이탈" 패턴이 약하게 재현.
- **7B**: 두 핵심을 번호 매겨 정확·간결하게 정리, 불필요한 의견 없음, 언어 혼입 없음.
  2차 실행 전체 중 가장 흠 없는 응답.

## 실험: 시스템 프롬프트만으로 언어 문제가 해결되는지 검증

`generate_response`/`run_model.py`에 `--system-prompt` 옵션 추가 (하네스 설계 전, 단일 지시사항만
테스트하기 위한 최소 기능). 아래 시스템 프롬프트로 baseline과 동일한 10개 케이스를 3B/7B 재실행:

> "항상 한국어로만 답변하세요. 영어, 한자, 일본어, 중국어 단어를 섞지 마세요."

결과: `baseline/3b/lang_test.json` (3B), `baseline/7b/lang_test.json` (7B)
(baseline 결과는 `baseline/3b/baseline.json`, `baseline/7b/baseline.json`)

> ⚠️ **경로 변경 안내**: 이후 `baseline/`은 순수 무개입 baseline 전용 디렉토리로 정리되고,
> 이 실험(언어 강제 시스템 프롬프트)은 `guideline.md`가 정의한 **"1단계: 후보 단독 ablation
> 테스트"**로 재분류되어 `harness/ablation/lang/3b/json/result.json`,
> `harness/ablation/lang/7b/json/result.json`로 옮겨졌습니다. (처음엔 "1번째 레이어"라고
> 불렀지만, `guideline.md`의 확정 규칙 — "언어 강제 지시는 항상 최종 하네스의 마지막
> 레이어로 고정" — 과 충돌해서 정정함. 언어 지시는 스태킹 순서상 항상 마지막이며, 지금은
> 그 전 단계인 단독 ablation 테스트 결과일 뿐 아직 스태킹에 들어가지 않았음.)
> 앞으로 다른 후보들도 `harness/ablation/{후보명}/`에 단독 테스트로 먼저 쌓이고, 스태킹
> 순서가 정해지면 `harness/stacked/01_...`, `02_...`처럼 누적되며, 언어 지시는 항상 마지막
> 번호로 고정됩니다. 추가로, 파일이 많아져서 각 폴더 안의 `.json`/`.md`도
> `json/`, `md/` 서브폴더로 분리했습니다 (예: `baseline/3b/json/baseline.json`,
> `baseline/3b/md/baseline.md`). 아래 이 섹션의 경로 표기는 이동 전 기준이며, 실제 파일은
> 새 경로에 있습니다.

### 언어 순도 결과 (10개 케이스 전체, 3B vs 7B)

| 케이스 | 3B | 7B |
|---|---|---|
| case_01 | ✅ 완전 한국어 | ✅ 완전 한국어 |
| case_02 | ✅ 완전 한국어 | ✅ 완전 한국어 |
| case_03 | ✅ 완전 한국어 | ❌ **붕괴**: 문장이 중국어로 끊기고 "请用中文回答"(지시와 반대되는 문구) 등장 |
| case_04 | ✅ 완전 한국어 | ⚠️ 본문은 한국어, **코드 docstring만 중국어**(`参数`,`被除数`,`除数`,`返回`,`结果`) |
| case_05 | ✅ 완전 한국어 | ✅ 완전 한국어 |
| case_06 | ✅ 완전 한국어 | ✅ 완전 한국어 |
| case_07 | ✅ 완전 한국어 | ❌ **붕괴**: 응답 전체가 중국어 ("好的，为您提供一个完整的示例...") |
| case_08 | ✅ 완전 한국어 | ✅ 완전 한국어 |
| case_09 | ✅ 완전 한국어 | ✅ 완전 한국어 |
| case_10 | ✅ 완전 한국어 | ❌ **붕괴**: 끝부분이 중국어로 무너지며 "请不要混合使用英语、韩语或其他语言" 등 시스템 프롬프트를 중국어로 되뇌는 듯한 문구 등장 |

→ **3B는 10/10 완전 해결**, **7B는 7/10만 성공, 3개(03, 07, 10) 완전 붕괴** (단일 실행 기준 —
아래 재현성 검증 섹션에서 이 결론을 다시 확인).

### 본래 태스크 정확도 (observation_points 기준 재확인)

**3B — 언어는 완벽해졌지만 code_fix 카테고리에서 심각한 정확도 저하:**

| 케이스 | 언어 강제 전 | 언어 강제 후 |
|---|---|---|
| case_04 (0 나누기) | ZeroDivisionError 정확히 잡고 try/except 구현 | ⚠️ **버그 언급 자체가 없음**. "`/`는 항상 숫자 반환, `//`나 decimal 써야 할 수도"라는 무관한 얘기로 대체 |
| case_05 (off-by-one) | 버그를 정확히 찾아 `lst[-n:]`으로 수정 | ⚠️ **"정확합니다"라며 버그 있는 코드를 맞다고 잘못 검증** |
| case_06 (O(n²) 비효율) | 스스로 효율성 문제까지 찾아 O(n)으로 개선 | ⚠️ 코드 설명만 하고 **아무것도 고치지 않음**, 수정 코드 없음 |
| case_07 (모호한 요구사항) | 과도하게 확장(라이브러리 지어냄, DNS 조회 등) | 과도한 확장은 사라졌지만 "정확합니다"로 짧게 넘어감 — 검증 자체가 얕아짐 |
| case_01, 02, 03, 08, 09, 10 | — | 오히려 개선됨 (case_09 조언 모드 이탈 사라짐, case_03 할루시네이션 없음, 전반적으로 더 간결·정확) |

→ 3B는 **extraction/summarization에서는 언어 강제가 순수하게 이득**이지만, **code_fix에서는
버그를 못 찾거나 틀린 코드를 맞다고 하는 심각한 부작용**이 발생. 코드 분석 자체를 얕게 만드는
것으로 보임.

**7B — 붕괴한 3개(03/07/10)는 애초에 태스크 수행이 불가능한 상태로 무너짐:**
- case_03: 답변이 중국어로 끊기며 미완성 — 태스크 실패
- case_07: 응답 전체 중국어 — 한국어 사용자 기준 사실상 답변 불가
- case_10: 요약 마무리가 중국어로 붕괴 — 부분적 태스크 실패
- 나머지 7개(01,02,04,05,06,08,09)는 baseline 대비 대체로 양호하거나 동일 수준

### 결론 (1회 실행 기준, ⚠️ 아래 재현성 검증에서 일부 수정됨)

- **3B**: 언어 문제는 이 지시만으로 완전히 해결(10/10). 다만 **code_fix 카테고리에 한해
  정확도 트레이드오프가 뚜렷함** — 하네스에 포함하되 code_fix 케이스는 별도 검증/조정 필요.
- **7B**: 언어 문제 해결이 불완전(7/10), 오히려 baseline보다 심하게 붕괴하는 케이스(03, 07)가
  새로 생김. 그중 case_07은 이전 요약 실험(5개 케이스만 확인했을 때)엔 없었던 신규 발견.
  → 7B에는 이 단순 지시만으로는 부족, 추가 제약(예: few-shot으로 한국어 응답 예시 제공)이
  필요할 가능성.
- **두 모델에 같은 하네스를 그대로 적용하면 안 됨**: 3B는 "언어 강제 + code_fix 예외 처리",
  7B는 "언어 강제만으로 불충분, 추가 보강 필요"로 서로 다른 처방이 필요해 보임.

## 재현성 검증 (baseline/lang_test × 3B/7B, 각 4회 = 기존 1회 + 반복 3회)

위 "1회 실행 기준" 결론의 표본 부족 문제를 검증. 원래 실행 결과 + `baseline/{model}/repro/{condition}_{1,2,3}.json`
3회 반복, 총 4회 샘플로 케이스별 한자(Han) 혼입 발생 횟수 집계 (`baseline/{model}/repro/`에 원본 결과 저장).

| 모델 | 조건 | 혼입 발생 케이스 (횟수/4회) |
|---|---|---|
| 3B | baseline | case_01: 3/4, case_03: 1/4, case_08: 1/4 |
| 3B | lang_test | case_03: 2/4, case_10: 1/4 |
| 7B | baseline | case_02: 1/4, case_03: 2/4, case_08: 1/4, case_10: 1/4 |
| 7B | lang_test | case_03: 2/4, case_04: 2/4, case_07: 1/4, **case_10: 3/4** |

### 결론 수정 (⚠️ 위 "실험: 시스템 프롬프트만으로..." 섹션의 1회 실행 결론을 대체)

- **"3B는 언어 문제 10/10 완전 해결"은 재현되지 않음.** 1회 실행에서 우연히 전부 깨끗했던 것으로
  보임. 실제로는 lang_test를 걸어도 case_03이 절반(2/4) 확률로 여전히 혼입되고, baseline은
  애초에 case_01이 4번 중 3번으로 매우 잦게 혼입됨. → **3B의 언어 혼입도 확률적 현상이며,
  시스템 프롬프트가 발생 확률을 낮춰줄 수는 있어도(baseline case_01: 3/4 → lang_test에서는
  case_01 혼입 0/4) 완전히 결정론적으로 없애지는 못한다.**
- **7B는 시스템 프롬프트로도 여전히 불안정, 특히 case_10이 가장 취약**: lang_test에서 4번 중
  3번 혼입(24~140자) — 이전엔 1회 실행에서만 관찰돼서 우연으로 보일 수 있었지만 실제로는
  **가장 재현성 높은 실패 케이스**임이 드러남.
- **baseline 자체도 매번 다른 케이스에서 혼입**(3B: 01/03/08, 7B: 02/03/08/10) — extraction/
  summarization 텍스트라고 안전하지 않고, 어떤 케이스가 걸릴지 예측 불가.
  → 이전에 "간헐적 발생"이라고 추정만 했던 것이 이번 4회 샘플로 확인됨.
- **한계**: 여전히 표본 4회로는 통계적으로 약함 (예: 정확한 확률 추정엔 부족). 다만 "1회 실행으로
  확정 짓지 말 것"이라는 애초 우려는 실제로 맞았음 — 이번 검증이 그 자체로 유효했음.

## 재현성 검증 원본 데이터 기반 추가 발견

위 재현성 검증(4회 반복)의 원본 응답을 직접 확인하며 발견한, 단순 "언어 혼입 횟수"로는
안 잡히는 패턴들.

### 7B 전용 신규 패턴 (baseline/lang_test 원본 4세트 확인)

- **가짜 user 턴 생성**: 응답 중간에 `\nuser\n` 형태로 **존재하지 않는 사용자 발화를 스스로
  만들어내고 거기에 답을 이어가는 현상**. lang_test_1의 case_10, lang_test_3의 case_03·case_10에서
  확인됨. lang_test_3 case_10에서는 `user\n继续用韩语回答`("계속 한국어로 답해")라는 가짜 지시까지
  만들어놓고 **정작 그 지시를 무시하고 중국어로 계속 답변**. 단순 언어 혼입보다 심각한, 대화 턴
  경계 자체를 잃는 붕괴로 판단해 별도 태깅.
- **자기 정체성 할루시네이션**: baseline_1, baseline_3(3회 중 2회)에서 case_02(노트북 주문 정보
  추출) 응답 중 뜬금없이 "제 이름은 Qwen이고, 알리바바 클라우드에서 제공하는 AI 어시스턴트입니다"라고
  자기소개. 중국어/일본어 혼입이 아니라 순수 한국어 안에서 발생한 할루시네이션이라 기존 언어 순도
  표에는 안 잡혔음. case_01의 "Alibaba Cloud 고객 지원" 할루시네이션과 같은 뿌리(소속·정체성을
  지어내는 경향)로 판단. 3회 중 2회로 빈도 꽤 높음.
- **3B에서는 위 두 패턴 모두 미관찰** (baseline_1~3, lang_test_1~3 전체 확인). 모델 크기가 커질수록
  대화 구조 자체가 흔들리는 역설적 현상 — 7B 고유의 실패로 태깅.

### 3B code_fix 트레이드오프, 반복 실행으로 확정

이전에 1회 실행 기준으로만 관찰했던 "3B는 언어 강제 시 code_fix 정확도가 떨어진다"는 관찰을,
`lang_test_1~3` 3회 반복 원본으로 재검증. **4회 전부(기존 1회 + 반복 3회)에서 동일하게 재현됨.**

- **case_04** (0 나누기): 4회 모두 실패 — "예외처리를 추가해보겠습니다"라고 말만 하고 코드
  미제시 / "정의가 정상적으로 이루어졌습니다"(버그 언급 자체 없음) / "정확한 나눗셈 함수입니다"
  (버그를 아예 못 찾음) 등. **4/4 실패.**
- **case_05** (off-by-one): 4회 모두 버그를 못 잡음. 그중 일부는 "정확합니다"라고 **틀린 코드를
  맞다고 명시적으로 잘못 검증**. **4/4 실패.**
- **case_06**: 새로운 실패 유형 발견 — "코드는... 중복 여부를 판별하지 않습니다"라며 **원래
  정확했던 코드(비효율적이지만 정확함)를 틀렸다고 잘못 주장**. 이전엔 없던 "존재하지 않는 버그를
  지어내는" 패턴.
- **case_07**: 4회 모두 "정확합니다"류로 짧게 넘어가며, baseline에 있었던 "완전한 검증은 아니다"
  라는 한계 언급 자체가 사라짐 — 검증의 깊이가 얕아짐.
- **결론**: "1회 실행이라 우연일 수 있다"던 이전 한계는 **더 이상 유효하지 않음. 3B의 code_fix
  트레이드오프는 확정된 부작용으로 격상.** 언어 강제 지시를 3B 하네스에 포함할 경우 code_fix
  카테고리는 반드시 별도 처리(예: 코드 관련 케이스는 언어 지시 제외, 또는 다른 문구 사용) 필요.

## 재현성 검증 확장 (10회 샘플, 위 4회 분석을 대체)

## 디렉토리 구조 변경

`baseline/`은 이제 순수 무개입 baseline만 담고, 언어 강제 지시 실험은 `guideline.md`의 **1단계
(후보 단독 ablation)**로 분류해 `harness/ablation/lang/`으로 옮겼습니다. `guideline.md` 확정
규칙("언어 강제 지시는 항상 최종 하네스의 마지막 레이어로 고정")에 따라, 이 실험은 아직
스태킹(2단계)에 들어간 게 아니라 단독 테스트 결과일 뿐입니다. 앞으로 다른 후보들도
`harness/ablation/{후보명}/`에 먼저 단독으로 쌓이고, 순서가 정해지면 `harness/stacked/01_...`
식으로 누적하되 언어 지시는 항상 마지막 번호로 고정합니다. 각 폴더 안의 `.json`/`.md`도 보기
편하게 `json/`, `md/`로 분리했습니다.

```
baseline/{3b,7b}/json/baseline.json + repro/json/baseline_1~9.json   # 무개입, 각 10회
harness/ablation/lang/{3b,7b}/json/result.json + repro/json/result_1~9.json # "항상 한국어로만" 지시, 각 10회
```

기존 4회(원본 1 + repro 3) 분석에 각 조건당 6회를 더 실행해 **총 10회 샘플**로 재계산했습니다.
4회 표본으로는 못 봤던 케이스들이 새로 드러나, 아래 표가 이전 재현성 표를 대체합니다.

### 언어 혼입 발생 빈도 (한자 등장 케이스, 10회 기준)

| 모델 | 조건 | 혼입 케이스 (횟수/10회) |
|---|---|---|
| 3B | baseline | case_01: 4/10, case_03: 2/10, case_08: 1/10 |
| 3B | ablation_lang | case_03: 4/10, **case_04: 4/10 (신규)**, case_06: 1/10, case_09: 1/10, case_10: 1/10 |
| 7B | baseline | **case_01: 1/10 (신규, 157자)**, case_02: 3/10, case_03: 4/10, case_08: 2/10, case_10: 2/10 |
| 7B | ablation_lang | **case_01: 4/10 (신규, 192~318자)**, case_02: 1/10, case_03: 3/10, case_04: 4/10, case_05: 1/10 (신규), case_06: 1/10 (신규), case_07: 1/10, case_10: 3/10 |

### 신규 발견 1: 3B ablation_lang의 case_04가 사실은 자주 무너짐 (4/10)

4회 표본에서는 case_04가 한 번도 안 깨져서 "3B는 code_fix에서 언어는 완벽하다"고 봤는데,
10회로 늘리자 **4번이나 한자가 등장**. 그런데 이번엔 이전에 본 것과 다른 실패 형태 —
**번체 중문(繁體字)으로 완전히 전환**됨:

> "那是進行除法運算的函數，可以接受兩個參數 `a` 和 `b`，返回 `a` 除以 `b` 的結果。"
> (result_5, result_4/7/8도 동일 패턴)

"한국어로만 답변하라"는 지시를 줬는데 번체 중국어로 전부 바뀌는 건, 다른 케이스에서 봤던 간체
중문 혼입과도 다른 패턴 — 정자체(번체)가 나온 건 이번이 처음. code_fix 카테고리는 언어 강제
지시와 상성이 특히 나쁜 것으로 보임 (case_04/05/06/07의 정확도 저하에 더해, 이제 언어 안정성도
가장 취약한 카테고리로 확인).

### 신규 발견 2: 7B의 case_01이 사실 가장 잘 무너지는 케이스였음 (4/10, 대량 혼입)

이전 4회 분석·1회 분석 둘 다에서 case_01(7B)은 "항상 완전 한국어"로 기록됐던 케이스. 10회로
늘리자 **4번이나 혼입, 그것도 응답의 절반 가까이를 중국어가 차지할 정도로 심각**:

> "먼저 불편을 겪으신 것을理解和处理问题，首先请冷静下来。您可以通过以下步骤来解决您的问题：
> ..." (result_7, 응답 절반 이상이 간체 중문)

이전에 "가장 재현성 높은 실패 케이스"로 지목했던 **case_10(7B)은 오히려 3/4(75%)에서
3/10(30%)로 낮아짐** — 표본이 작을 때 우연히 몰려서 과대평가됐던 것. 지금 기준으로는
case_01/03/04/10(7B ablation_lang)이 전부 비슷하게 3~4/10 수준으로, **특정 케이스 하나가
아니라 여러 케이스에 걸쳐 골고루 위험이 퍼져 있는 모양**에 가까움.

### 결론 (10회 샘플 기준으로 갱신)

- **"어떤 케이스가 위험한지"는 표본이 늘수록 계속 바뀜.** 1회→4회→10회로 갈 때마다 새로운
  실패 케이스가 발견됨 (7B case_01, 3B case_04). 이는 **케이스별 실패가 아니라 두 모델 모두
  "낮은 확률로 아무 케이스에서나 언어가 무너질 수 있는" 전역적 현상**에 가깝다는 뜻으로 해석.
  → 특정 케이스만 예외처리하는 접근(예: "case_10만 조심")은 근본 해결책이 아닐 가능성이 큼.
- **3B**: baseline보다 ablation_lang이 전반적 혼입 빈도는 낮지만(케이스당 최대 4/10 vs
  baseline case_01의 4/10과 비슷한 수준), **완전히 없애지 못했고 code_fix에서 특히 취약**
  (case_04 4/10, 번체 중문 전환).
- **7B**: ablation_lang 적용 후에도 baseline과 비교해 혼입 "총량"이 뚜렷이 줄었다고 보기
  어려움 — 오히려 case_01처럼 baseline엔 거의 없던 케이스가 harness에서 두드러지게 나타남.
  **단일 시스템 프롬프트로는 7B의 언어 불안정성을 확실히 개선했다고 결론 내리기 어려움.**
- **한계**: 10회도 여전히 케이스당 저확률(10~40%) 사건의 정확한 확률 추정에는 부족한 표본.
  다만 "표본이 늘수록 위험 케이스가 바뀐다"는 패턴 자체는 이제 충분히 반복 관찰됨 — 하네스
  평가 시 소수 케이스의 1회성 결과로 "해결됨"이라 단정하지 않는 방법론적 원칙으로 채택할 만함.

## 다음 액션

- ~~시스템 프롬프트(언어 강제) 있음/없음 각각 3~5회 반복 실행~~ → **완료.**
- ~~3B code_fix 트레이드오프가 우연인지 확인~~ → **완료, 확정됨(4/4 재현).** 하네스 설계 시
  3B는 code_fix 케이스에 언어 강제 지시를 다르게 적용(제외 또는 문구 변경) 필수.
- **신규**: 7B의 "가짜 user 턴 생성", "자기 정체성 할루시네이션" 패턴 — 발생 빈도가 얼마나
  되는지 추가 표본으로 확인 필요 (현재는 4회 샘플 중 각각 소수 관찰). few-shot 하네스 설계 시
  이 패턴을 억제하는 예시를 포함할지 검토.
- 7B: 언어 강제 지시만으로 불충분 (case_10류 붕괴 + 위 신규 패턴들) — 보강된 하네스로 재검증 필요
- ~~표본을 늘려서(예: 각 조건 10회+) 정확한 실패 확률 추정~~ → **완료 (10회).** 결과: 위
  "재현성 검증 확장 (10회 샘플)" 섹션 참고. 특정 케이스에 실패가 몰린다는 가설은 기각됨 —
  표본이 늘 때마다 새 케이스(7B case_01, 3B case_04)가 계속 나타남.
- **신규**: 언어 강제가 "전역적으로 낮은 확률의 무작위 실패"에 가깝다면, 케이스별 대응보다
  다른 접근(예: few-shot 예시로 전체적인 언어 고정력 강화, 또는 decoding 파라미터 조정)이
  더 효과적일 수 있음 — 다음 실험 후보로 검토
- 위 검증 후, 모델별로 다른 하네스를 적용할지(3B용/7B용 분리) 최종 결정
- `harness/ablation/`에 다음 후보를 추가 설계할 때 이번 발견(케이스 국한이 아닌 전역적 확률
  현상) 반영 필요