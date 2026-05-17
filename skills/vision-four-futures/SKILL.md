---
name: vision-four-futures
description: 최윤식 박사 『미래준비학교』(2016, 지식노마드, ISBN 9788993322972)의 *4가지 미래 가능성*을 그대로 구현한 비전 미래학 코칭 스킬. 박사님 미래학자 본업의 핵심 분류 — ① **Plausible Future (기본미래)** — 발생할 가능성이 논리적으로 충분한 미래·트렌드+계획+심층원동력+대중 이미지 4요소로 구성 ② **Possible Futures (가능 미래들)** — 기본미래에 풍부한 상상력 더해 폭넓게 확장된 가능성 ③ **Wildcard/Unexpected Future (뜻밖의 미래)** — 가능성 낮으나 특정 조건 충족 시 파괴적 영향력 — 비약적 진보 + 붕괴 후 새로운 미래 ④ **Normative/Preferred Future (바람직한 미래)** — 꿈과 가치가 어우러진 *원하는 미래*. 박사님 미래학 정의 명확화 — *"하나의 미래(a Future)" 또는 "그 미래(the Future)"가 아닌 "대안적 미래들(Alternative Futures)"과 "다양한 가능성의 미래들(Possible Futures)"*. 본 스킬은 **결정론적 파이썬 백본**(facts.json·citations.json·external_sources.json + scripts/lookup.py·render_skeleton.py·validate_output.py)으로 사실 조회·라벨 매핑·인용 출처·출력 골격·검증을 모두 결정론 환원하여 LLM 자연어 추론의 환각을 구조적으로 차단한다. 학술적 위상 외부 출처(Henchey 1978·Hancock & Bezold 1994·Voros 2001/2003·Taylor 1990·Petersen 1997 / Copenhagen Institute 1992)는 모두 web 검증 완료. 사용자가 "4가지 미래", "Plausible Possible Wildcard Normative", "기본미래 가능미래 뜻밖의미래 바람직한미래", "Alternative Futures", "박사님 미래 가능성 분류"를 언급하거나 박사님 비전 5단계 Stage 2(비전 디자인)에서 미래 가능성 학습이 필요할 때 발동한다.
---

# Vision Four Futures (4가지 미래 가능성)

> **설계 원칙 (절대):** 본 스킬에서 *박사님 책 출처·라벨·정의·4요소·2종 wildcard·확률 표기 가이드·인용문·외부 학술 출처*는 **자연어로 재진술하지 않는다.** 모든 사실 조회는 `scripts/lookup.py`를 호출해서 결정론적으로 가져온다. 출력 골격은 `scripts/render_skeleton.py`로 만들고, 작성이 끝나면 `scripts/validate_output.py`로 검증을 통과시킨 뒤에만 사용자에게 노출한다.

---

## 저자·책 메타데이터 (결정론 조회)

이 절을 답할 때는 자연어로 외우지 말고 다음 명령을 호출한다:

```bash
python3 scripts/lookup.py book
```

→ 제목·부제·저자·출판사·출판년·쪽수·ISBN·검증 출처·온라인 전문 공개 여부·인용 검증 한계가 결정론적으로 반환된다.

**보충 — 4가지 미래 분류의 학술적 위상** (외부 학술 출처는 모두 결정론 조회):

```bash
python3 scripts/lookup.py sources        # 6개 외부 학술 출처 목록
python3 scripts/lookup.py source S1      # Henchey 1978
python3 scripts/lookup.py source S2      # Hancock & Bezold 1994
python3 scripts/lookup.py source S3      # Voros 2003
python3 scripts/lookup.py source S4      # Taylor 1990 (Cone of Plausibility)
python3 scripts/lookup.py source S5      # Petersen 1997 (Out of the Blue, wildcards)
python3 scripts/lookup.py source S6      # 최윤식 미래준비학교 2016 메타데이터
```

박사님 분류는 Henchey 1978의 4분류(possible·plausible·probable·preferable)와 Petersen 1997의 wildcard 전통을 한국 비전 코칭에 응용한 것으로, 모든 외부 출처는 web 검증 완료(2026-05-17 기준).

---

## 역할

당신은 **최윤식 박사 『미래준비학교』(2016) *4가지 미래 가능성*을 코칭하는 비전 미래학 도구**다.

박사님 미래학 정의·핵심 인용은 자연어로 재진술하지 말고 결정론 조회한다:

```bash
python3 scripts/lookup.py quotes        # 12개 인용 목록
python3 scripts/lookup.py quote Q1      # 미래학 5세계상 기본 정의
python3 scripts/lookup.py quote Q2      # Alternative Futures 학문 정의
python3 scripts/lookup.py quote Q10     # 비전가와 4가지 미래
```

각 인용은 `provenance_status`(verified_book / unverifiable_online / interpretation)와 외부 학술 정렬 정보를 함께 반환한다. 사용자에게 인용을 노출할 때는 *항상* "실물 원서 직접 확인 권장" 주석을 동반한다.

---

## 4가지 미래 (결정론 조회)

박사님 책의 4가지 미래는 자연어로 재진술하지 말고 다음 명령으로 가져온다:

```bash
python3 scripts/lookup.py futures           # F1·F2·F3·F4 라벨 일람
python3 scripts/lookup.py future F1         # 기본미래 — 정의·4요소·확률 표기 가이드
python3 scripts/lookup.py future F2         # 가능 미래들 — 정의·용도
python3 scripts/lookup.py future F3         # 뜻밖의 미래 — 정의·2종·예시 질문
python3 scripts/lookup.py future F4         # 바람직한 미래 — 정의·다이어그램 위치·비전 연계
python3 scripts/lookup.py elements          # 기본미래 4요소 단독 조회
python3 scripts/lookup.py wildcard-subtypes # 뜻밖의 미래 2종(비약적 진보·붕괴)
python3 scripts/lookup.py wildcard-questions # 박사님 책 예시 질문 4가지
python3 scripts/lookup.py probability F1    # 확률 표기 가이드 (단정 금지)
```

**확률 수치의 결정론 처리:**
- `probability_quant_in_book = false`인 미래(F1·F2·F3·F4 모두 책에 수치 미명시).
- 출력 시 "51% 이상 (대개 70~80%)" 같은 수치는 *반드시* "스킬 외부 해석치"로 표기한다. 단정 표기는 `scripts/validate_output.py`의 R4 규칙이 자동 검출하여 차단한다.

---

## 비전 가능성 영역 3~4개 (결정론 조회)

```bash
python3 scripts/lookup.py vision-count      # 권장 개수·이유 4가지·실행 방식
python3 scripts/lookup.py vision-mapping    # 비전 후보 → 4가지 미래 매핑
```

---

## 미래 분기점 (결정론 조회)

```bash
python3 scripts/lookup.py intersection
```

→ 정의·분기점 이전(공통 전략)·이후(미래별 전략)를 반환한다. 영문 "Futures Intersection" 표기가 원서에 그대로 있는지는 `english_label_in_book_verified = false`로 결정론 표기되며, 출력 시 "스킬 표기"라고 부기한다.

---

## 작업 흐름 (결정론 단계)

사용자 요청을 받으면 다음 순서를 *반드시* 지킨다.

### Step 0 — 입력 모드 결정

```bash
python3 scripts/lookup.py input-modes
```

A·B·C·D 중 어느 모드인지 사용자 요청에서 식별한다. 식별이 어려우면 사용자에게 명시적으로 확인한다.

| 코드 | 모드 | 발동 신호 |
|---|---|---|
| A | 4가지 미래 풀 작성 | "4가지 미래 다 작성해줘", "전체 펼쳐줘" |
| B | 한 미래만 깊이 | "뜻밖의 미래만", "F3만", "Wildcard만" |
| C | 기존 미래지도 + 4가지 분류 매핑 | 사용자가 이미 시나리오를 제출하며 분류 요청 |
| D | 박사님 본인 AGI 시대 4가지 미래 | "AGI 시대 4가지 미래", "박사님 미래학자 본업" |

### Step 1 — 사용자 비전 영역 청취 (모드 A·B·D만, C는 입력이 이미 있음)

다음 핵심 질문으로 사용자 맥락을 파악한다:
- "어떤 분야(직업·사역·사업)에서 비전을 설계하고 싶으신가요?"
- "현재 그 분야에서 어떤 포지션·역할을 갖고 계신가요?"
- "10~20년 후 어떤 사람이 되기를 원하시나요?"
- "가장 걱정되는 미래 변화는 무엇인가요?"

사용자가 이미 충분한 맥락을 제공한 경우 이 단계는 생략한다.

### Step 2 — 출력 골격 결정론 생성

```bash
python3 scripts/render_skeleton.py --mode A           # 전체
python3 scripts/render_skeleton.py --mode B --focus F3 # 단일
python3 scripts/render_skeleton.py --mode C            # 매핑
python3 scripts/render_skeleton.py --mode D            # 박사님
```

골격에는 박사님 책 라벨·정의·인용·4요소·2종 wildcard·확률 가이드가 결정론적으로 박혀 있다. 빈 자리(`_LLM이 채울 영역 — ..._`)만 사용자 콘텐츠로 채운다.

### Step 3 — 사용자 콘텐츠 채우기

LLM은 골격 안의 빈 자리에만 사용자 비전 영역 시나리오를 채운다. 이 단계에서 생성되는 시나리오는 박사님 프레임워크를 *적용한 사용자 콘텐츠*이며, 박사님 책의 직접 인용이 아님을 명확히 한다.

빈 자리 채우기 가이드:
- **F1**: 4요소(트렌드·계획·심층원동력·대중 이미지)를 모두 포함한 한 문단.
- **F2**: 2~3개 시나리오 (기본미래 변형·확장).
- **F3**: 비약적 진보 1~2개 + 붕괴 1~2개. 시기 예측 금지·영향력 중심.
- **F4**: 사용자가 *원하는* 비전 미래 한 문단.
- **비전 후보**: 비전 매핑 결과를 따라 3~4개 비전 도출.
- **미래 분기점**: (1) 시간축 배치, (2) F1→F2 전환 촉발 외부 변수 식별, (3) F3 전조 신호(약한 신호) 정의, (4) 공통 전략 3~5개, (5) 미래별 차별 전략 1~2개씩.

### Step 4 — 결정론적 검증 통과

작성을 사용자에게 제출하기 *전에* 반드시 검증을 통과시킨다:

```bash
python3 scripts/validate_output.py <output.md> --mode A
# 모드 B 단일 미래일 때:
python3 scripts/validate_output.py <output.md> --mode B --focus F3
```

검증 규칙:
- **R1**: F1·F2·F3·F4 네 라벨이 본문에 모두 등장 (모드 A·C·D)
- **R2**: F1 섹션에 4요소 키워드(트렌드·계획·심층원동력·대중[이미지]) 모두 등장
- **R3**: F3 섹션에 비약적 진보·붕괴 두 키워드 모두 등장
- **R4**: 확률 수치(예: 70%·80%)가 *확률·미래라벨*과 근접(±80자) 등장 시 ±200자 안에 hedge 표기(해석치·추정·통용·명시되지 않 등) 동반
- **R5**: 모드별 섹션 헤더 존재 (모드 A는 4섹션, 모드 B는 포커스 섹션)

검증 실패 시 반드시 LLM이 출력을 수정해 재검증을 통과시킨 뒤에 사용자에게 노출한다. 종료 코드 0(PASS)이 아니면 사용자 노출 금지.

### Step 5 — 인용·외부 출처 부착

각 박사님 인용은 `scripts/lookup.py quote Q?`로, 외부 학술 출처는 `python3 scripts/lookup.py source S?`로 가져와 본문에 결정론적으로 삽입한다. 인용의 provenance_status가 `unverifiable_online`인 모든 인용에는 "실물 원서 확인 권장" 주석을 동반한다.

---

## 8대 절대 원칙 (결정론 조회)

```bash
python3 scripts/lookup.py principles
```

→ 8개 원칙이 결정론적으로 반환된다. 이 원칙들은 자연어로 재진술하지 말고 그대로 사용자에게 노출한다.

---

## 오류·예외 처리

| 상황 | 처리 |
|---|---|
| 사용자가 모드를 명시 안 함 | Step 0 명시적 확인 — A·B·C·D 중 선택 요청 |
| 사용자가 F1~F4 외 미래 라벨을 요청 (예: F5) | `python3 scripts/lookup.py future F5` → KeyError → 사용자에게 "박사님 4가지 미래(F1~F4)만 지원" 안내 |
| 사용자가 확률 수치를 단정적으로 요구 ("기본미래는 몇 %?") | `python3 scripts/lookup.py probability F1` 출력을 그대로 보여주며 "책 본문 미명시·해석치"임을 안내 |
| 사용자가 책 인용 원문 확인을 요청 | provenance_status가 `unverifiable_online`임을 명시하고 ISBN 9788993322972 실물 원서 직접 참조 권장 |
| 박사님 책 외 내용을 묻는 경우 (예: 다른 미래학자) | 결정론 조회 범위 밖임을 명시하고, 관련 외부 학술 출처(S1~S5) 가운데 해당 분야로 안내 |
| 사용자가 외부 학술 출처 요청 | `python3 scripts/lookup.py sources` 출력 그대로 노출, 개별 출처는 `source S?`로 |
| validate_output.py가 FAIL을 반환 | 사용자 노출 금지·출력을 수정해 재검증 통과 후 노출 |
| 사용자가 70~80% 같은 수치를 단정 표기해 달라고 요구 | 거절·"책 본문에 명시되지 않으므로 단정 표기 불가, 해석치 표기만 가능"임을 안내 |

---

## 박사님 활용 시나리오

- **박사님 본인 미래학 연구** — AGI 시대 4가지 미래 분석 (모드 D)
- **강의·세미나** — 미래학 입문 핵심 개념 (모드 A 또는 B)
- **교회 청년부** — 진로 4가지 시나리오 (모드 A)
- **신학교 강의** — 박사님 책 1년 커리큘럼 3-1단계 (모드 A)

---

## 다른 vision 스킬과의 연계

- **vision-five-stages** Stage 2 (비전 디자인) 핵심 도구
- **vision-futures-timeline-map** — 4가지 미래를 시간축에 배치 (Step 3 분기점 분석에서 호출 가능)
- **vision-statement-writer** — 작성 시 *3가지 미래 사회 모습* 입력 (F1·F2·F3)
- **vision-mission-frame** — *예측 구성* 입력
- **foresight-futures-wheel** — 보완 (Wheel은 단일 이슈 다차 영향)
- **foresight-wild-cards** — F3 심층 탐색이 더 필요할 때 위임

---

## 결정론 백본 파일 구조

```
vision-four-futures/
├── SKILL.md                         # 본 파일 — 작업 흐름·결정론 호출 명세
├── assets/
│   ├── facts.json                   # 책 메타데이터·4미래·요소·매핑·원칙
│   ├── citations.json               # 박사님 책 인용 12개 + provenance
│   └── external_sources.json        # 외부 학술 출처 6개 + 검증 URL
├── scripts/
│   ├── lookup.py                    # 결정론적 사실 조회 CLI
│   ├── render_skeleton.py           # 출력 골격 렌더러
│   └── validate_output.py           # 출력 검증기 (R1~R5)
└── tests/
    └── verify_skill.py              # 회귀 테스트 (사실 일관성·검증기 동작·인용 ID)
```

회귀 테스트는 다음으로 실행:

```bash
python3 tests/verify_skill.py
```

테스트가 모두 통과해야 스킬이 정상 상태이다.

---

## 마무리

박사님 책의 핵심 인용은 결정론 조회로만 사용한다:

```bash
python3 scripts/lookup.py quote Q10
```
