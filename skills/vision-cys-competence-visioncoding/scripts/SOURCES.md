# 외부 학술·표준 출처 (CYS 비전 역량 진단의 이론적 토대)

본 스킬은 박사님 『미래준비학교』(2016)의 *CYS 비전 역량 진단 검사*를
그대로 구현한 것이다. 박사님 검사 자체가 다음 학계 주류 이론들을
통합 반영한다(박사님 책 인용: *"미래학에 근거한 평가, MBTI, STRONG 직업
흥미검사, 에니어그램(Enneagram), 다중지능 이론들을 반영하여 만들었다"*).

각 학술 출처는 결정론으로 환원 불가능한 이론적 토대 항목의 1:1 대조
근거다. 출처 없는 판정은 자동 FAIL.

---

## 1. 다중지능 이론 (Multiple Intelligences)

- **Howard Gardner**, *Frames of Mind: The Theory of Multiple Intelligences*
  (Basic Books, 1983). — 7개 지능 원형 제안.
- **Howard Gardner**, *Intelligence Reframed: Multiple Intelligences for
  the 21st Century* (Basic Books, 1999). — 자연친화지능(Naturalist) 공식
  추가, 실존지능(Existential)을 "9.5번째 지능"으로 잠정 제안.
- **Gardner**, "A multiplicity of intelligences" *Scientific American*
  Vol. 9, No. 4 (1998).

**확정 사실**:
1. 1983년 7지능: 언어·논리수학·공간·음악·신체운동·대인관계·자기성찰.
2. 1999년 자연친화지능 공식 추가 → 8지능.
3. 실존지능은 Gardner 본인이 "잠정 제안(half a candidate)"으로
   표현했으며 공식 추가 아님 (Gardner 1999, pp. 60-66).

**본 스킬 적용**:
- 9지능 측정을 표시하되, 실존지능은 *"Gardner 잠정 제안"* 명시 필수.
- 박사님 책 "인간친화지능"은 Gardner 원어 *Interpersonal Intelligence*
  (대인관계지능)의 한국 학계 통용 번역.

---

## 2. 에니어그램 (Enneagram)

- **Don Richard Riso & Russ Hudson**, *Personality Types: Using the
  Enneagram for Self-Discovery* (Houghton Mifflin, 1996; rev. ed.).
- **Riso & Hudson**, *The Wisdom of the Enneagram* (Bantam, 1999).
- **Riso & Hudson**, *Riso-Hudson Enneagram Type Indicator (RHETI)*
  공식 검사지 (The Enneagram Institute).
- **Helen Palmer**, *The Enneagram: Understanding Yourself and the
  Others in Your Life* (HarperOne, 1991).

**확정 사실**:
1. 9유형 체계: 1 개혁가·2 조력자·3 성취자·4 개인주의자·5 탐구가·
   6 충성가·7 열정가·8 도전자·9 평화주의자.
2. 인접 유형 두 개 중 더 높은 점수가 *날개(wing)*. 표기법: `XwY`
   (예: 5w6, 5w4).
3. 동점 시 결정 규칙은 RHETI 공식 매뉴얼에 부재 → 본 스킬은
   결정론적 tie-break(낮은 번호 우선)을 명시적으로 채택.

**본 스킬 적용**:
- 박사님 데이터: 5번 78점, 4번 10점, 6번 20점 → 5w6 (검증: `enneagram_wing` 함수).

---

## 3. MBTI (Myers-Briggs Type Indicator)

- **Isabel Briggs Myers & Mary H. McCaulley**, *Manual: A Guide to the
  Development and Use of the Myers-Briggs Type Indicator* (Consulting
  Psychologists Press, 1985).
- **Isabel Briggs Myers**, *Gifts Differing: Understanding Personality
  Type* (Davies-Black, 1980).
- 출판·검사: *The Myers-Briggs Company* (구 CPP).

**확정 사실**: 4축 (E/I, S/N, T/F, J/P) × 2 = 16유형.

**본 스킬 적용**:
- vision-mbti-visioncoding 하위 스킬 결과를 비전 잠재력(성격)에 통합.
- 본 스킬은 MBTI 점수를 직접 계산하지 않고 입력만 수신.

---

## 4. STRONG 직업 흥미 검사 (Strong Interest Inventory)

- **E. K. Strong Jr.**, *Vocational Interests of Men and Women*
  (Stanford University Press, 1943). — 원판.
- **John L. Holland**, *Making Vocational Choices: A Theory of
  Vocational Personalities and Work Environments* (PAR, 1985; 3rd ed.
  1997). — Holland RIASEC 6코드 (Realistic, Investigative, Artistic,
  Social, Enterprising, Conventional).
- 현행판: *Strong Interest Inventory* (CPI/Pearson/Pearson VUE).

**확정 사실**: 6 RIASEC 일반 직업 흥미 + 30 기본 흥미 척도 +
244 직업 척도.

**본 스킬 적용**: 비전 기술력(관심사 검사) 영역에 vision-strong-visioncoding
하위 스킬 결과 통합.

---

## 5. 미래학 (Futures Studies)

- **Jerome C. Glenn & Theodore J. Gordon (eds.)**, *Futures Research
  Methodology, Version 3.0* (The Millennium Project, 2009). — 37개
  미래학 방법론 표준 교과서.
- **Wendell Bell**, *Foundations of Futures Studies* (Vols. 1-2,
  Transaction Publishers, 1997).
- **Sohail Inayatullah**, *Causal Layered Analysis* (Tamkang
  University Press, 2004).

**확정 사실**: 미래 통찰력(future foresight)은 환경 스캐닝·시나리오·
델파이 등 표준 미래학 기법으로 측정 가능한 인지 역량.

**본 스킬 적용**: 영역 A의 "미래 통찰력" 항목은 미래학 표준 인지
역량 측정 항목과 일치.

---

## 6. 4 Skill Balance (생각·언어·감성·몸·영성) — 박사님 고유 모델

박사님 『미래준비학교』(2016) 고유 모델이며 학계 표준은 아니다.
다만 5개 영역의 각 요소는 다음 학계 출처와 부분 일치한다:

- **생각·언어**: Gardner 다중지능 중 논리수학·언어지능 (Gardner 1983).
- **감성**: Daniel Goleman, *Emotional Intelligence* (Bantam, 1995).
- **몸**: Gardner 신체운동지능 (Bodily-Kinesthetic Intelligence).
- **영성**: Gardner 실존지능 잠정 제안 (Gardner 1999); Robert A.
  Emmons, *The Psychology of Ultimate Concerns: Motivation and
  Spirituality in Personality* (Guilford, 1999).

**본 스킬 적용**: 박사님 고유 모델을 *박사님 책 인용*으로 표기하고,
부분 일치하는 학계 출처도 함께 명시.

---

## 7. SMART 5역량 (미래인재 준비역량) — 박사님 고유 모델

박사님 『미래준비학교』 고유 분류 모델. 박사님 강의·집필에서 직접
정의되며, 일반화된 학계 출처와 직접 1:1 대응 없음.

**본 스킬 적용**: 박사님 책 출처만 표기. 외부 출처 부재 명시.

---

## 8. 영역 E 통합 비전 코드 점수 (가중 산출)

박사님 책에는 *세부 원점수 → 통합 비전 코드 점수* 변환의 정확한
가중치 공식이 명시되지 않음. 박사님 본인(A type) 데이터에서 역산:

- 비전 구상력: 세부 85 → 통합 79 (보정 계수 약 0.929)
- 비전 계획력: 세부 85 → 통합 75 (보정 계수 약 0.882)
- 비전 전략력: 세부 77.5 → 통합 73 (보정 계수 약 0.942)
- 비전 추진력·네트워킹력: 세부 점수 단순 평균 (검증됨).

**본 스킬 적용**:
- 박사님 본인 데이터는 박사님 책 원문 그대로 인용 (변환 공식 적용
  안 함).
- 사용자 데이터 적용 시에는 *검증 가능한 단순 평균*만 사용하며,
  검증 불가능한 영역(추진력·네트워킹력 외)은 *세부 원점수 = 통합
  점수*로 보수적 처리. 이 처리 규칙은 SKILL.md와 결정론 엔진에
  명시 (할루시네이션 차단).

---

## 9. 결정론으로 환원 불가능한 항목 처리 원칙

1. **이론적 정의·역사적 사실** → 위 학술 출처로 1:1 대조.
2. **점수 계산·범위 검증·날개 결정·평균·분류** → 결정론 함수
   (`cys_engine.py`)로 강제 환원.
3. **자유 입력(핵심 가치·비전 방향성 자유 기술)** → LLM이 입력 그대로
   인용 + 카테고리 매핑만 허용. 임의 추론·확대 해석 금지.
4. **박사님 본인 데이터** → 박사님 책 원문 그대로 인용. 변환·재산출
   금지.

출처 없는 판정은 자동 FAIL. 본 SOURCES.md에 등재되지 않은 외부
주장은 스킬 출력에 사용하지 않는다.
