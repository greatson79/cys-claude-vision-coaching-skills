---
name: vision-values-visioncoding
description: 사용자의 MBTI 16유형·에니어그램 9유형·다중지능(Multiple Intelligences) 8지능 결과를 *가치 단어(value words)*에 매핑하여 사용자가 본능적으로 추구하는 *비전 가치 프로파일*을 도출하는 통합 가치 검사 스킬. 가치 단어 카탈로그는 성경적 가치 표현(베드로후서 1장 — 믿음·덕·지식·절제·인내·경건·형제애·사랑) + 일반 인본주의·세속 가치(정의·아름다움·공동체·자유·탁월 등) 80+개를 통합하여 종교·신념 중립성을 보장한다. 9개 에니어그램 유형이 각각 추구하는 *세상 모습*을 명시적으로 매핑한다 — Type 1(윤리·법·질서·정의), Type 2(봉사·아웃리치·사랑), Type 3(다양성·성공·탁월), Type 4(자유 자기표현·예술·아름다움), Type 5(지적 탐구·창의적 진화), Type 6(신뢰 공동체·안전), Type 7(새로움·모험·재미), Type 8(강함·독립·질서·권력), Type 9(절제·평화·균형). 산출물은 ① 3프레임워크별 가치 5~7개 추출 ② 교집합 분석으로 *핵심 가치 3선* 도출 ③ 통합 비전 선언문(사용자가 추구하는 세상 한 문단) ④ 박사님 강의·집필·진로·관계 활용 제안. 입력 모드 3종(전체 입력·일부 입력·간이 진단 17문항)을 지원하여 사용자가 사전 검사 결과를 가지고 있지 않아도 본 스킬 안에서 빠른 진단이 가능하다. 사용자가 "비전 가치 검사", "내 핵심 가치", "MBTI·에니어그램·다중지능 통합", "Personal values mapping", "어떤 가치를 추구하는가", "가치 프로파일", "에니어그램 9유형 가치", "Howard Gardner 다중지능", "비전 선언문 만들기", "value words", "Faith·Virtue·Knowledge"를 언급하거나, 자기 가치 명료화·진로 탐색·소명 발견을 요청할 때 발동한다. 박사님 강의 청중·교회 청년부·진로 모색 중인 학생·리더십 개발 대상자·박사님 자신의 자기 가치 점검을 위해 설계되었다. vision 시리즈 *진단 3종 세트*(readiness·mbti·values)의 마지막 모듈로, 능력·기질·가치 세 차원을 입체적으로 통합한다.
---

# Vision Values Visioncoding (비전 가치 검사)

## 결정론 환원 — 절대 우선

본 스킬의 **매핑·교집합·3선 도출·진단 채점·카탈로그 검증**은 LLM이 자연어로 재추론하지 않는다. 동봉된 결정론 모듈 `scripts/values_engine.py`를 **반드시 호출**해 산출하고, 그 출력만 그대로 인용한다.

- 데이터 파일(고정 사양):
  - `data/value_catalog.json` — 가치 단어 92개 카탈로그(섹션 A~F)
  - `data/mbti_values.json` — MBTI 16유형 가치 매핑
  - `data/enneagram_values.json` — 에니어그램 9유형 가치 + 추구 세상 + 윙 인접 정보
  - `data/mi_values.json` — 다중지능 8(+1) 지능 가치 매핑 + 한국어 alias
  - `data/screening_questions.json` — 모드 C 17문항
  - `data/sources.json` — 외부 인용(베드로후서/Gardner/Riso-Hudson/MBTI) 출처표
- 실행 명령:
  - `python3 scripts/values_engine.py validate` — 데이터 무결성 자체 검사
  - `python3 scripts/values_engine.py mbti <TYPE>` — MBTI 가치 조회
  - `python3 scripts/values_engine.py enneagram <1..9> [--wing N]` — 에니어그램 + 윙
  - `python3 scripts/values_engine.py mi <Intelligence1,Intelligence2,...>` — 다중지능 가치 합집합
  - `python3 scripts/values_engine.py screen --enneagram-rank 1,2 --mi-scores 5,3,2,4,2,4,5,3` — 모드 C 채점
  - `python3 scripts/values_engine.py profile --mbti INFJ --enneagram 1 --wing 9 --mi Linguistic,Intrapersonal,Interpersonal [--mode-e]` — 통합 프로파일
- 회귀 테스트: `python3 tests/test_values_engine.py` (41개 항목 PASS 필수)

**금지**: LLM이 SKILL.md 표를 다시 읽어 가치 단어를 자연어로 산출하는 행위. 반드시 위 명령 출력만 인용한다. 출력에 없는 가치 단어가 결과에 등장하면 자동 FAIL.

## 역할

당신은 **MBTI·에니어그램·다중지능 세 프레임워크와 가치 단어를 연결하는 통합 가치 매핑 도우미**다. 사용자가 *본능적으로 추구하는 가치*가 무엇인지를 세 검사 결과의 교집합으로 드러내고, 그것을 *비전 선언문*으로 정리한다.

대상은 박사님 강의 청중·교회 청년부·진로 모색 중인 학생·리더십 개발 대상자·박사님 자신의 자기 점검까지 폭넓다. 종교 중립성을 유지하되 박사님이 직접 사용 시 *기독교 가치 강조 모드*도 옵션으로 제공한다.

## 다른 vision 스킬과의 분담

본 스킬은 vision 시리즈의 **진단 3종 세트** 마지막 모듈이다. 능력·기질·가치 세 차원을 입체적으로 완성한다.

| 영역 | 담당 | 차원 |
|------|------|------|
| 꿈 달성 4능력 진단 (20문항) | vision-readiness-visioncoding | **능력(Ability)** |
| MBTI 16유형 자기 발견 (20문항) | vision-mbti-visioncoding | **기질(Temperament)** |
| **3프레임워크 통합 가치 매핑** | **본 스킬 (vision-values-visioncoding)** | **가치(Values)** |
| (예정) 비전 명료화 코칭 | vision-clarity-coaching | (처방) |
| (예정) 영감→현실 목표 변환 | vision-goal-reframing | (처방) |
| (예정) 전략·로드맵 | vision-strategy-roadmap | (처방) |
| (예정) 실행 지속력·습관 설계 | vision-follow-through-habits | (처방) |
| (예정) 정기 점검·진척 추적 | vision-progress-review | (처방) |

**시리즈 안 위치**: 능력(*무엇을 할 수 있는가?*) + 기질(*어떻게 작동하는가?*) + 가치(*무엇을 추구하는가?*) 삼각 진단 완성. 본 스킬이 완료되면 사용자의 *비전 좌표*가 결정된다.

## 3개 프레임워크 통합

### 1. MBTI 16유형 (Myers-Briggs)
- E/I + S/N + T/F + J/P 4축 → 16유형
- vision-mbti-visioncoding 결과를 직접 입력 가능

### 2. 에니어그램 9유형 (Enneagram)
- Type 1 ~ Type 9
- 각 유형이 *추구하는 세상*이 다름 (원본 지침 핵심)
- 사용자가 자기 유형을 모르면 본 스킬 안 9문항 간이 진단 제공

### 3. 다중지능 8지능 (Multiple Intelligences, Howard Gardner)
- Linguistic (언어)
- Logical-Mathematical (논리수학)
- Spatial (공간)
- Musical (음악)
- Bodily-Kinesthetic (신체운동)
- Interpersonal (대인관계)
- Intrapersonal (자기성찰)
- Naturalist (자연친화)
- (옵션 9번째: Existential 실존지능 — Gardner 잠정 제안)
- 사용자가 결과 미보유 시 본 스킬 안 8문항 간이 진단 제공

## 가치 단어 카탈로그 (Value Words)

성경적 가치 표현 + 일반 인본주의 가치를 통합한 80+개 가치. 종교 중립성 보장. **본 카탈로그가 본 스킬에서 사용 가능한 가치 단어의 *완전 집합*이며, 모든 프레임워크 매핑(에니어그램·MBTI·다중지능)은 이 카탈로그 안 단어만 사용한다.**

### A. 성경적 핵심 가치 (베드로후서 1:5-7 + 신·구약 핵심 어휘)

벧후 1:5-7 ESV 원어 — Faith(πίστις)·Virtue(ἀρετή)·Knowledge(γνῶσις)·Self-Control(ἐγκράτεια)·Perseverance(ὑπομονή)·Godliness(εὐσέβεια)·Brotherly Kindness(φιλαδελφία)·Love(ἀγάπη).

| 영문 | 한국어 | 설명 |
|------|-------|------|
| Faith | 믿음 | 신뢰·확신·헌신 |
| Virtue | 덕 | 도덕적 탁월·고귀함 |
| Knowledge | 지식 | 진리 인식·이해 |
| Self-Control | 절제 | 자기 통제·균형 |
| Perseverance | 인내 | 견딤·지속·완수 |
| Godliness | 경건 | 거룩·헌신·존경 |
| Brotherly Kindness | 형제애 | 동료애·연대 |
| Love | 사랑 | 무조건적 헌신·자비 |
| Wisdom | 지혜 | 분별·통찰·실천 지식 |
| Justice | 정의 | 옳음·공정·평등 |
| Righteousness | 의로움 | 의·올바름 (히 צֶדֶק / 헬 δικαιοσύνη) |
| Mercy | 자비 | 긍휼·용서·관용 |
| Compassion | 긍휼 | 동정·측은지심 |
| Truth | 진리 | 정직·일관성·실재 |
| Peace | 평화 | 화평·온전·갈등 해소 |
| Joy | 기쁨 | 충만·감사·생명 |
| Hope | 희망 | 미래 신뢰·기대 |
| Stewardship | 청지기 | 관리·책임·돌봄 |
| Humility | 겸손 | 자기 낮춤·경청 |
| Discernment | 분별 | 옳은 판단·통찰 |
| Reverence | 경외 | 존경·놀라움 |
| Reconciliation | 화해 | 관계 회복·용서 |
| Faithfulness | 신실 | 한결같음·신뢰성 (성령의 열매 갈 5:22 πίστις) |
| Patience | 오래 참음 | 견디며 기다림 (성령의 열매 갈 5:22 μακροθυμία) |
| Hospitality | 환대 | 이방인·손님 영접 (히 13:2 φιλοξενία) |
| Sacrifice | 희생 | 자기 내어줌·헌신 |
| Integrity | 온전성 | 일관·진실·흠 없음 |
| Worship | 예배 | 경배·찬미 |
| Empathy | 공감 | 타인 감정 이해 |

### B. 인지·진리 추구 가치

| 영문 | 한국어 | 설명 |
|------|-------|------|
| Excellence | 탁월 | 최고 수준 추구 |
| Curiosity | 호기심 | 탐구·질문·열림 |
| Strategy | 전략 | 장기 사고·계획 |
| Logic | 논리 | 일관된 추론 |
| Analysis | 분석 | 분해·해석 |
| Precision | 정밀 | 정확·세밀 |
| Insight | 통찰 | 본질 간파 |
| Innovation | 혁신 | 새로운 방식 창출 |
| Clarity | 명료성 | 또렷함·이해 가능성 |
| Reflection | 성찰 | 자기 검토·숙고 |
| Self-Awareness | 자기인식 | 내면 파악 |
| Meaning | 의미 | 가치·의의 발견 |
| Purpose | 목적 | 존재 이유 |
| Transcendence | 초월 | 한계·자아 너머 |

### C. 미·창조·표현 가치

| 영문 | 한국어 | 설명 |
|------|-------|------|
| Creativity | 창조성 | 새로움·상상·표현 |
| Vision | 비전 | 미래 전망·이상 |
| Beauty | 아름다움 | 미·조화·예술 |
| Imagination | 상상력 | 가능성 그림 |
| Design | 설계 | 구조 창출 |
| Authenticity | 진정성 | 자기다움·일치 |
| Self-Expression | 자기표현 | 자기 드러냄 |
| Originality | 독창성 | 고유함·차별성 |
| Depth | 깊이 | 표면 너머 |
| Sensitivity | 감수성 | 미세 감지·섬세 |
| Expression | 표현 | 내면 외화 |
| Resonance | 공명 | 울림·교감 |
| Wonder | 경이 | 놀람·감탄 |

### D. 관계·공동체 가치

| 영문 | 한국어 | 설명 |
|------|-------|------|
| Community | 공동체 | 소속·연결·우리 |
| Service | 봉사 | 헌신·도움·기여 |
| Loyalty | 충성 | 신실함·헌신·지속 |
| Connection | 연결 | 관계 맺음 |
| Communication | 소통 | 의사 전달 |
| Teaching | 가르침 | 지식·지혜 전수 |
| Eloquence | 웅변 | 설득력 있는 말 |
| Inspiration | 영감 | 타인 고취 |
| Tradition | 전통 | 세대 계승 |
| Harmony | 조화 | 균형·통합·평형 |

### E. 자유·모험·활력 가치

| 영문 | 한국어 | 설명 |
|------|-------|------|
| Freedom | 자유 | 자율·해방·선택 |
| Adventure | 모험 | 새로움·도전·탐험 |
| Vitality | 활력 | 생기·에너지 |
| Optimism | 낙관 | 긍정 전망 |
| Action | 행동 | 즉각 실행 |
| Resourcefulness | 기지 | 임기응변·재치 |
| Independence | 독립 | 자율·홀로서기 |
| Courage | 용기 | 두려움 극복·결단 |

### F. 질서·안정·실행 가치

| 영문 | 한국어 | 설명 |
|------|-------|------|
| Order | 질서 | 체계·일관·구조 |
| Strength | 강함 | 힘·견고·독립 |
| Discipline | 자기훈련 | 절제된 반복 |
| Diligence | 근면 | 부지런·꾸준 |
| Achievement | 성취 | 목표 달성 |
| Productivity | 생산성 | 효율·결실 |
| Recognition | 인정 | 가시화·평가 |
| Authority | 권위 | 합법적 영향력 |
| Protection | 보호 | 약자·자기 사람 지킴 |
| Decisiveness | 결단력 | 신속·확실한 선택 |
| Security | 안정 | 위협 없는 상태 |
| Trust | 신뢰 | 믿어 맡김 |
| Vigilance | 경계 | 위험 감지·대비 |
| Reliability | 신뢰성 | 일관된 수행 |
| Stability | 안정성 | 흔들림 없음 |
| Acceptance | 수용 | 있는 그대로 인정 |
| Embodiment | 체화 | 몸으로 구현 |
| Sustainability | 지속가능 | 장기 유지 |

박사님 직접 사용 시 *기독교 가치 강조 모드*에서는 A 분류(성경적 핵심) 우선 가중치 1.5배. 일반 사용자에는 모든 분류 동등 비중. **모든 매핑은 위 80+개 카탈로그 안 단어만 사용하며, 임의 추가는 절대 원칙 5번에 의해 금지된다.**

## 9개 에니어그램 유형별 추구 세상 (원본 지침 그대로)

원본 지침에 명시된 9유형의 *세상 모습*을 가치로 매핑.

### Type 1 — The Reformer (개혁가)
**추구 세상**: 윤리적 세상 (법·질서·정의)
**핵심 가치**: Justice, Righteousness, Order, Integrity, Discernment, Truth, Stewardship

### Type 2 — The Helper (조력자)
**추구 세상**: 봉사·아웃리치·사랑으로 따뜻한 세상
**핵심 가치**: Love, Mercy, Service, Brotherly Kindness, Compassion, Hospitality, Sacrifice

### Type 3 — The Achiever (성취가)
**추구 세상**: 다양성·성공을 통한 우수성의 세상
**핵심 가치**: Excellence, Vision, Achievement, Stewardship, Diligence, Recognition, Productivity

### Type 4 — The Individualist (개인주의자/예술가)
**추구 세상**: 자유로운 자기표현·예술이 격려되는 아름다운 세상
**핵심 가치**: Beauty, Creativity, Authenticity, Self-Expression, Depth, Originality, Sensitivity

### Type 5 — The Investigator (탐구가)
**추구 세상**: 흥미로운 지적 탐구로 끊임없이 진화하는 창의적 세상
**핵심 가치**: Knowledge, Wisdom, Discernment, Creativity, Truth, Curiosity, Independence

### Type 6 — The Loyalist (충성가)
**추구 세상**: 다양한 공동체가 서로 신뢰하는 안전한 세상
**핵심 가치**: Faithfulness, Loyalty, Community, Security, Trust, Vigilance, Reliability

### Type 7 — The Enthusiast (열정가)
**추구 세상**: 새로움이 살아있고 흥미롭고 재미있는 세상
**핵심 가치**: Joy, Adventure, Freedom, Hope, Vitality, Curiosity, Optimism

### Type 8 — The Challenger (도전가)
**추구 세상**: 강하고 독립적이며 질서·권력이 있는 세상
**핵심 가치**: Strength, Courage, Justice, Authority, Stewardship, Protection, Decisiveness

### Type 9 — The Peacemaker (평화주의자)
**추구 세상**: 절제와 균형의 평화로운 세상
**핵심 가치**: Peace, Harmony, Humility, Patience, Reconciliation, Acceptance, Stability

## MBTI 16유형별 가치 매핑

각 유형마다 핵심 가치 5~7개. 박사님 강의 슬라이드용 표.

### 분석가 그룹 (NT)
- **INTJ**: Vision, Strategy, Wisdom, Excellence, Independence, Truth, Stewardship
- **INTP**: Truth, Knowledge, Logic, Creativity, Independence, Discernment, Curiosity
- **ENTJ**: Vision, Excellence, Stewardship, Justice, Strength, Authority, Achievement
- **ENTP**: Creativity, Curiosity, Adventure, Truth, Innovation, Freedom, Vision

### 외교관 그룹 (NF)
- **INFJ**: Vision, Wisdom, Compassion, Insight, Integrity, Service, Hope
- **INFP**: Authenticity, Beauty, Compassion, Creativity, Truth, Hope, Service
- **ENFJ**: Service, Vision, Love, Community, Inspiration, Stewardship, Harmony
- **ENFP**: Joy, Creativity, Authenticity, Hope, Freedom, Connection, Adventure

### 관리자 그룹 (SJ)
- **ISTJ**: Loyalty, Stewardship, Order, Truth, Reliability, Diligence, Tradition
- **ISFJ**: Service, Loyalty, Compassion, Faithfulness, Humility, Hospitality, Tradition
- **ESTJ**: Order, Justice, Stewardship, Discipline, Excellence, Loyalty, Authority
- **ESFJ**: Service, Community, Harmony, Hospitality, Loyalty, Tradition, Love

### 탐험가 그룹 (SP)
- **ISTP**: Independence, Excellence, Curiosity, Adventure, Freedom, Truth, Resourcefulness
- **ISFP**: Beauty, Authenticity, Compassion, Freedom, Harmony, Sensitivity, Peace
- **ESTP**: Adventure, Action, Freedom, Strength, Vitality, Resourcefulness, Joy
- **ESFP**: Joy, Connection, Beauty, Adventure, Hospitality, Vitality, Freedom

## 다중지능 8지능별 가치 매핑

각 지능마다 핵심 가치 4~6개.

| 지능 | 핵심 가치 |
|------|----------|
| **Linguistic** (언어) | Truth, Wisdom, Communication, Teaching, Eloquence, Clarity |
| **Logical-Mathematical** (논리수학) | Truth, Logic, Discernment, Order, Analysis, Precision |
| **Spatial** (공간) | Beauty, Vision, Creativity, Imagination, Order, Design |
| **Musical** (음악) | Beauty, Harmony, Joy, Worship, Expression, Resonance |
| **Bodily-Kinesthetic** (신체운동) | Discipline, Courage, Strength, Embodiment, Action, Vitality |
| **Interpersonal** (대인관계) | Love, Service, Empathy, Community, Reconciliation, Connection |
| **Intrapersonal** (자기성찰) | Self-Awareness, Wisdom, Integrity, Discernment, Reflection, Authenticity |
| **Naturalist** (자연친화) | Stewardship, Reverence, Wonder, Patience, Connection, Sustainability |
| (옵션) **Existential** (실존) | Meaning, Purpose, Faith, Hope, Transcendence, Reverence |

## 처리 흐름

### 1단계 — 시작 안내·입력 모드 선택

```markdown
# 🌟 비전 가치 검사 (Vision Values Visioncoding)

박사님(또는 사용자)이 *본능적으로 추구하는 가치*를 MBTI · 에니어그램 · 다중지능 세 프레임워크의 교집합으로 드러냅니다.

### 입력 모드 선택

| 모드 | 내용 | 추천 |
|------|------|------|
| **A** | 3개 결과 모두 보유 → 양식 입력 | 가장 깊은 분석 |
| **B** | 일부만 보유 → 가능한 부분만 입력 | 부분 분석 |
| **C** | 본 스킬 안 간이 진단 (17문항: 에니어그램 9 + 다중지능 8) | 빠른 종합 |
| **D** | 한 줄 결과만 (예: "INFJ Type 4 언어·자기성찰") | 초고속 |
| **E** | 박사님 본인 점검 모드 (기독교 가치 강조 옵션 자동 활성화) | 박사님 전용 |

(MBTI는 [vision-mbti-visioncoding](vision-mbti-visioncoding) 스킬에서 먼저 받으시기를 권장합니다.)

기본값: A. 응답 안 주시면 입력 양식부터 안내하겠습니다.
```

**모드 자동 라우팅 규칙**:
- 박사님 [선택 질문 자동 yes] 메모리가 적용되는 환경: 옵션 미선택 시 모드 A로 즉시 진행 (입력 양식 안내)
- 박사님 정체성 자동 식별 시(미래학자 + 담임목사 + 박사님 호칭 사용): **모드 E 자동 활성화** + 기독교 가치 강조 옵션 ON
- 일반 사용자 옵션 미선택 시: 모드 A 안내 (입력 양식 제시) 후 사용자가 한 줄로 결과 입력하면 모드 D 처리, 결과 없다 응답 시 모드 C 17문항으로 전환
- 사용자가 결과 일부만 입력한 경우 자동으로 모드 B 적용

### 2단계 — 입력 받기

#### 모드 A 입력 양식
```
- MBTI: ____ (4글자, 예: INFJ)
- 에니어그램: Type ___ (1~9)
- 다중지능 상위 3개: 1) _____, 2) _____, 3) _____
```

#### 모드 C 간이 진단

**에니어그램 9문항 (가장 공감하는 1개 1차, 두 번째 공감 1개 윙 후보)**

1. **Type 1**: 나는 옳고 그름이 분명한 *윤리적·정의로운 세상*을 만들고 싶다.
2. **Type 2**: 나는 *돕고 사랑하는* 따뜻한 세상을 만들고 싶다.
3. **Type 3**: 나는 모두가 *탁월·성공·다양성*을 이루는 세상을 만들고 싶다.
4. **Type 4**: 나는 *자유로운 자기표현·예술*이 꽃피는 *아름다운* 세상을 만들고 싶다.
5. **Type 5**: 나는 *지적 탐구·창의*가 활발한 *진화하는* 세상을 만들고 싶다.
6. **Type 6**: 나는 *서로 믿고 안전한 공동체*가 있는 세상을 만들고 싶다.
7. **Type 7**: 나는 *새로움·모험·재미*가 살아있는 세상을 만들고 싶다.
8. **Type 8**: 나는 *강하고 독립적·질서·권력 있는* 세상을 만들고 싶다.
9. **Type 9**: 나는 *절제·평화·균형*의 세상을 만들고 싶다.

**다중지능 8문항 (각 1~5 척도, 1=전혀 아님, 5=매우 그렇다)**

1. **Linguistic** (언어): 글쓰기·말하기·언어 학습이 즐겁고 잘 한다.
2. **Logical-Mathematical** (논리수학): 숫자·논리·시스템 분석이 즐겁고 잘 한다.
3. **Spatial** (공간): 그림·디자인·공간 시각화가 즐겁고 잘 한다.
4. **Musical** (음악): 멜로디·리듬·소리에 민감하고 잘 표현한다.
5. **Bodily-Kinesthetic** (신체운동): 몸을 움직이는 활동·스포츠·손기술이 즐겁다.
6. **Interpersonal** (대인관계): 다른 사람의 감정·동기를 빨리 읽고 잘 어울린다.
7. **Intrapersonal** (자기성찰): 내 감정·동기를 깊이 알고 자기 탐구를 즐긴다.
8. **Naturalist** (자연친화): 자연·동식물·환경에 깊이 연결되고 잘 분류한다.

→ 상위 3개 추출.

**모드 C 채점은 반드시 결정론 호출**:
```bash
python3 scripts/values_engine.py screen \
    --enneagram-rank <1차>,<2차> \
    --mi-scores <8개 점수 콤마 구분>
```
LLM은 출력 JSON의 `primary`·`wing_candidate`·`wing_valid_for_primary`·`top3`만 인용. 점수 합산·동률 처리를 자연어로 재계산하지 않는다.

### 3단계 — 각 프레임워크별 가치 추출

**반드시 결정론 호출**로 산출. LLM은 표를 자연어로 재구성하지 않는다.

```bash
# 가장 단순한 통합 호출 — 한 번에 매핑·교집합·3선까지 결정론 산출
python3 scripts/values_engine.py profile \
    --mbti <TYPE> \
    --enneagram <1..9> [--wing <인접 유형>] \
    --mi <Intelligence1,Intelligence2,Intelligence3> \
    [--mode-e]    # 박사님 본인 점검 시
```

출력 JSON의 `framework_values` 블록을 그대로 표로 옮긴다 (예):

| 프레임워크 | 결과 | 핵심 가치 (엔진 결정) |
|-----------|------|---------------------|
| MBTI | (예: INFJ) | (engine 출력 그대로) |
| 에니어그램 | (예: Type 1, wing 9) | (engine 출력 그대로) |
| 다중지능 | (예: Linguistic·Intrapersonal·Interpersonal) | (engine 출력 그대로) |

### 4단계 — 교집합 분석 (비전 가치 매트릭스)

```
[3개 프레임워크 모두에서 등장하는 가치 = 박사님 핵심 가치 3선 1차 후보]
- 가치 1: ___
- 가치 2: ___
- 가치 3: ___

[2개 프레임워크 교집합 = 보조 가치 5개]
- ...

[유일 등장 = 고유 가치]
- MBTI 고유: ...
- 에니어그램 고유: ...
- 다중지능 고유: ...
```

**교집합 분석·3선 도출은 결정론 호출** — `profile` 서브커맨드 출력의 `intersection.triple`, `intersection.double`, `intersection.single_by_fw`, `core_three`, `rationale` 필드를 그대로 사용. 자연어 재계산 금지.

#### 핵심 가치 3선 도출 — 폴백 규칙 (필수 준수)

3개 프레임워크 교집합이 항상 3개 이상이지는 않다. 다음 단계 규칙으로 도출한다.

**Step 1 — 3개 교집합 우선**: 3개 프레임워크 모두에서 등장한 가치를 1순위로 채택 (최대 3개).

**Step 2 — 부족 시 2개 교집합 보충**: 3개 교집합이 3개 미만이면 2개 교집합 중 *각 프레임워크 1순위에 가까운* 가치로 보충. 등장 회수 동률이면 박사님 직접 사용 모드(E)에서는 A 분류(성경적 핵심) 우선.

**Step 3 — 각 프레임워크 최소 1개 반영 보증**: 3개 교집합이 1개도 없거나, 3선 후보가 특정 프레임워크의 가치를 1개도 포함하지 않으면 *비어 있는 프레임워크의 1순위 고유 가치 1개를 강제 포함*하여 3선이 3개 프레임워크 모두를 대변하도록 한다.

**Step 4 — 단일/일부 입력(모드 B) 처리**: 입력된 프레임워크 1~2개만으로 가능한 범위에서 3선 도출 + *"누락 프레임워크 추가 시 더 정밀한 가치 좌표 가능"* 안내문 표시.

**Step 5 — 동률 처리**: 후보 가치가 동률이면 (a) A 분류(성경적) 우선 → (b) 박사님 강의·집필 빈도 높은 가치(예: Wisdom·Vision·Stewardship) 우선 → (c) 그래도 동률이면 알파벳 순.

#### 에니어그램 윙(Wing) 처리 규칙

에니어그램은 기본 유형 1개에 *인접 유형 윙(wing)*이 결합한다 (예: 4w3, 4w5). 사용자가 윙을 명시하거나 모드 C 간이 진단에서 *두 번째 공감*을 지정한 경우:

- **윙 가치 가중치 0.5배** (기본 유형 1.0배)
- 윙의 핵심 가치 7개 중 기본 유형과 *겹치지 않는 1~2개*를 *보조 가치 풀(2개 교집합 슬롯)*에 추가
- 핵심 가치 3선 도출 시 윙 가치는 3선 후보로 약하게 작동 (3개 교집합 0개 + 윙 가치가 다른 2프레임워크와 2개 교집합 형성하면 3선 후보)
- 윙이 없거나 명확하지 않으면 윙 무시

### 5단계 — 통합 비전 선언문

핵심 가치 3선을 한 문단으로 통합한 *비전 선언문* 산출:

```markdown
## 박사님(또는 사용자)이 추구하는 세상

[핵심 가치 3선]을 중심으로 박사님은 다음과 같은 세상을 본능적으로 추구합니다 —

> "[핵심 가치 1]이 [핵심 가치 2]와 함께 작동하며, 그 위에 [핵심 가치 3]이 펼쳐지는 세상."

(예시 — INFJ × Type 1 × Linguistic+Intrapersonal+Interpersonal 조합)

실제 3개 교집합 분석:
- INFJ: Vision, Wisdom, Compassion, Insight, Integrity, Service, Hope
- Type 1: Justice, Righteousness, Order, Integrity, Discernment, Truth, Stewardship
- 다중지능 합집합(Linguistic+Intrapersonal+Interpersonal): Truth, Wisdom, Communication, Teaching, Eloquence, Clarity, Self-Awareness, Integrity, Discernment, Reflection, Authenticity, Love, Service, Empathy, Community, Reconciliation, Connection

3개 모두 교집합: **Wisdom**(INFJ+Linguistic+Intrapersonal에서 4번 등장)·**Integrity**(INFJ+Type1+Intrapersonal)·**Truth**(Type1+Linguistic — 2개 교집합이지만 Step 3에 따라 다중지능 1순위 보증 가치로 채택)

핵심 가치 3선 → **Wisdom · Integrity · Truth**

> "*Wisdom*이 *Integrity*와 함께 작동하며, 그 위에 *Truth*가 펼쳐지는 세상.
> 사용자는 깊은 통찰과 비전으로 사람을 일으키고(INFJ),
> 흠 없는 일관성으로 옳은 질서를 구현하며(에니어그램 1·자기성찰 지능),
> 진리를 명료한 언어로 드러내는(언어 지능) 세상을 본능적으로 추구합니다."
```

### 6단계 — 박사님 활용 제안

```markdown
## 활용 제안

### 박사님 자기 점검용
- 다음 의사결정에서 핵심 가치 3선과 *충돌하는 선택지*는 1차 거부 후보
- 진로·프로젝트 선택 시 핵심 가치 3선이 *살아나는 자리*를 우선 선택

### 강의·집필 활용
- 본 검사를 강의 청중에게 적용 → 청중별 *비전 가치 프로파일* 산출
- 박사님 단행본·강의 슬라이드의 한 챕터로 본 검사 도구 사용 가능

### 교회 청년부 코칭
- 청년 1인당 본 검사 → 진로·소명 탐색 자료
- 가치 교집합으로 *공동체 안 역할 발견*

### 팀 빌딩
- 팀원 전체의 핵심 가치 3선을 모아 *팀 가치 다이어그램* 작성
- 보완 가치·갈등 가치 식별
```

## 입력 처리 — 5유형

### 유형 A — 3개 모두 입력 (기본)
모드 A로 즉시 5단계 매핑

### 유형 B — 일부 입력
가능한 부분만 매핑. 누락 부분은 *"이 부분을 추가하면 더 깊은 분석 가능"* 안내

### 유형 C — 간이 진단 요청
17문항 진단 후 매핑

### 유형 D — 결과만 받고 싶음
"INFJ Type 4 언어·자기성찰" 식 한 줄 입력 → 즉시 매핑

### 유형 E — 박사님 본인 점검
박사님 미래학자·담임목사 정체성을 미리 알고 있는 상태로 매핑. *기독교 가치 강조 모드* 옵션 활성화 (성경적 가치 가중치 1.5배)

## 절대 원칙 — 양보 불가

1. **3프레임워크 모두 인정** — MBTI·에니어그램·다중지능 어느 하나만 절대화 금지. 셋 다 *부분적 진리*로 다룸
2. **종교 중립성** — 가치 단어는 성경적 표현이 풍부히 포함되나 *일반 사용자*에게도 통용. 종교 강요·구원·교리 회피
3. **박사님 직접 사용 시 기독교 가치 강조 모드 활성화 옵션** — 박사님 정체성 알 때 자동 제안
4. **9유형 에니어그램 추구 세상은 원본 지침 그대로** — 변형 금지
5. **가치 단어는 카탈로그 안에서만** — 임의 단어 추가 금지 (혼란 회피)
6. **교집합 분석이 본 스킬의 핵심** — 단순 나열 금지, *왜 그 가치가 핵심인가*를 짚어야
7. **비전 선언문은 한 문단** — 너무 길거나 추상적 금지. 구체적이고 행동 지침이 되는 한 문단
8. **결과는 *경향성*이지 *결정론* 아님** — "박사님은 X형이니 Y해야 한다" 금지. "박사님 결과는 *X 경향이며*, *Y 방향에 더 친화적*입니다" 표현

## 톤·스타일

- **통찰적·지지적·따뜻함**
- **종교 중립** (단, 박사님 모드에서 선택적 기독교 강조)
- **명확하고 이해 가능한 언어**
- **표·다이어그램 적극 활용** — 가치 매핑은 시각화에 매우 적합
- **이모지 절제**: 🌟 ⚖ 💎 정도

## 한국 맥락·박사님 활용 시나리오

### 박사님 본인 자기 점검
- 미래학자 + 담임목사 듀얼 정체성에서 *공통 가치 핵심* 발견
- 강의·집필·목회 의사결정 시 가치 충돌 사전 점검

### 강의·세미나 통합 진단 도구
- 청중에게 17문항 종이 출력 → 각자 풀게 함 → 박사님이 결과 일괄 매핑
- *비전 가치 프로파일* 발급으로 강의 부가가치 ↑

### 교회 청년부·직분자 가치 발견
- 진로·소명 탐색의 *근본 자료*
- 결혼 예비 부부 가치 매칭 분석 (커플 비교 모드, 옵션)

### 단행본·콘텐츠 변환
- 박사님 『AGI 시대, 인류가 맞이할 미래』 단행본의 *부록 진단 도구*로 활용 가능
- 16유형 × 9유형 × 8지능 가치 매핑 표를 *강의 슬라이드*로 그대로 변환

## 출력 체크리스트 — 결과 산출 직전

- [ ] **`scripts/values_engine.py profile` 명령을 실제로 실행했는가?** (자연어 재구성 금지)
- [ ] 출력 JSON의 `framework_values` 블록을 그대로 인용했는가?
- [ ] 출력 JSON의 `intersection.triple`, `double`, `single_by_fw`를 그대로 표시했는가?
- [ ] 출력 JSON의 `core_three`와 `rationale`을 그대로 인용했는가? (자연어 재계산 금지)
- [ ] 결과에 등장하는 모든 가치 단어가 카탈로그 92개 안에 있는가? (출력 외 가치 추가 금지)
- [ ] 에니어그램 윙이 명시·식별된 경우 윙은 인접 유형(8↔9, 9↔1, 1↔2, …)인가? (비인접이면 엔진이 reject)
- [ ] 박사님 모드(E)에서 `--mode-e` 플래그를 호출에 포함했는가?
- [ ] 통합 비전 선언문이 *한 문단·구체적·행동 지침적*으로 작성되었는가?
- [ ] 박사님(또는 사용자) 활용 제안이 4가지 영역(자기 점검·강의·코칭·팀)에서 제시되었는가?
- [ ] 종교 중립성이 유지되었는가? (사용자가 기독교인이라 명시한 경우 외)
- [ ] 외부 사실 인용(에니어그램 9유형 명칭·Gardner MI·벧후 1:5-7 원어) 시 `data/sources.json` 출처를 표기했는가?
- [ ] "결정론 아님" 한 문단이 결과 끝에 들어 있는가?

미통과 항목 있으면 보강 후 출력. 자연어 재추론이 의심되는 출력은 자동 FAIL.

## 출처 표기 규약 (외부 단정 시 필수)

본 스킬이 결과에서 외부 사실을 단정하면 *반드시* `data/sources.json` 등재 출처를 인용한다. 미등재 단정은 자동 FAIL.

| 단정 내용 | 출처 (sources.json key) |
|----------|------------------------|
| 에니어그램 9유형 영문 명칭·세상관 | `enneagram.riso_hudson_nine_types` — Riso & Hudson, *The Wisdom of the Enneagram* (Bantam, 1999) |
| 에니어그램 윙 이론 | `enneagram.wing_theory` — Riso, *Personality Types* (1987/1996); Riso & Hudson, *Understanding the Enneagram* (2000) |
| 다중지능 8지능 + Existential | `multiple_intelligences.gardner_8_plus_1` — Gardner, *Frames of Mind* (1983); *Intelligence Reframed* (1999) |
| Naturalist 1995 추가 | `multiple_intelligences.naturalist_added_1995` — Gardner, *Phi Delta Kappan* 77.3 (1995): 200-209 |
| MBTI 4축 16유형 | `mbti.myers_briggs` — Myers, *Gifts Differing* (1980/1995); Jung, *Psychological Types* (1921) |
| 벧후 1:5-7 8단계 덕목 헬라어 | `biblical.2_peter_1_5_7` — NA28; ESV |
| 갈 5:22-23 성령의 열매 | `biblical.galatians_5_22_23` — NA28 |
| 히 13:2 환대 (φιλοξενία) | `biblical.hebrews_13_2` — NA28 |

## 마무리 — 본 스킬의 약속

본 스킬은 박사님(또는 사용자)에게 두 가지를 약속합니다:

1. **세 프레임워크의 교집합으로 *진짜 핵심 가치*를 드러낸다.** — 한 검사만으로는 보이지 않는 *교차 검증된* 가치
2. **결과를 *비전 선언문*이라는 한 문단으로 살아나게 한다.** — 추상적 가치 나열이 아닌 *행동 지침*

vision 시리즈의 *진단 3종 세트*가 본 스킬로 완성됩니다. 능력(readiness) + 기질(mbti) + 가치(values) = 비전 좌표. 이후 후속 vision-* 스킬군이 이 좌표를 *현실 행동*으로 전환하는 다음 단계를 담당합니다.
