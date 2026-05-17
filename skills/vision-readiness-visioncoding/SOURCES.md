# vision-readiness-visioncoding — 출처·근거 문서

> SKILL.md '출처·근거 안내' 절을 보강하는 별도 문서. 각 설계 결정의 *유래·증거·결정론 환원 여부*를 1:1 명시.

## 1. 4가지 핵심 능력 프레임의 유래

| 능력 | 출처 | 비고 |
|------|------|------|
| Seeing the Big Picture (큰 그림 보기) | 박사님(최윤식 박사) 비전 코칭 강의·교재의 원본 지침. 구체 문항은 본 스킬 설계 시점에 작성. | 학계 표준 척도가 아닌 *코칭용 자기 인식 프레임* |
| Reframing Inspiration into Realistic Goals (영감→현실 목표 재구성) | 박사님 원본 지침 | 동 |
| Creating Strategies to Achieve Goals (목표 달성 전략 수립) | 박사님 원본 지침 | 동 |
| Following Through on Plans (계획 실행 지속력) | 박사님 원본 지침 | 동 |

**유사 학계 개념과의 관계** (참고용·1:1 동일성 주장 *아님*):
- Big Picture ↔ **systems thinking**(Senge, *The Fifth Discipline*, 1990; Doubleday)
- Reframing Goals ↔ **goal-setting theory**의 *specificity·proximity* 차원(Locke & Latham, "Building a Practically Useful Theory of Goal Setting," *American Psychologist*, 2002, 57(9):705-717)
- Creating Strategies ↔ **strategic planning** 분야의 *means-end* 분석
- Following Through ↔ **self-regulation**·**grit**(Duckworth, "Grit: Perseverance and passion for long-term goals," *Journal of Personality and Social Psychology*, 2007, 92(6):1087-1101)

위 학계 문헌은 4능력 프레임을 *지지하는 정황 증거*이지 본 도구의 검증된 타당도·신뢰도 근거가 아니다. 박사님 코칭 프레임 자체에 대한 학계 메타분석·표준화는 진행되지 않았다.

## 2. 0~10 척도의 유래

- 박사님 원본 지침: *"0~10 척도. 10 = 세계 최고, 1-3 = poor"*.
- 학계 일반: 11점 척도(0~10)는 **NRS(Numeric Rating Scale)**로 통증·만족·자기 평정에서 광범위 사용 (Hawker et al., "Measures of adult pain," *Arthritis Care & Research*, 2011, 63(S11):S240-S252).
- 본 스킬의 11점 NRS 변형은 0='Not Yet'(시작 전) 의미를 명시적으로 정의. 1~10이 표준 NRS 구간, 0은 사용자가 *경험·인식 자체가 없음*을 표현하는 보조 값.

## 3. 20문항 분포의 유래

- 박사님 원본 지침: *"각 능력당 5문항씩, 모두 다른 비유·다른 단어·다른 표현"*.
- 박사님 원본 지침: *"형식은 'I am good at [skill]' 1인칭 진술"*.
- 학계 일반: 단일 척도당 4~6 문항이면 내적 일관성 신뢰도 추정에 충분하다는 기준(Nunnally, *Psychometric Theory*, 3rd ed., McGraw-Hill, 1994, Ch. 7). 본 스킬은 5문항 채택.

## 4. 그래프 영어 표기의 유래

- 박사님 원본 지침 직접 인용: *"The variables in the graph, and the descriptions on each axis, should all be in English."*
- 본 스킬 SKILL.md 절대 원칙 5와 1:1 대응.

## 5. ASCII partial block 매핑의 결정론 환원

- 유래: Unicode Block Elements U+2580–U+259F. 1/8 단위로 채움 비율을 표현하는 표준 문자.
- 본 스킬의 매핑 표(SKILL.md 4단계 옵션 B)는 *반올림 방식 결정론*. `lib/readiness_engine.py`의 `partial_block_for(partial)` 함수가 단일 진실 원천.
- 테스트: `tests/test_readiness_engine.py::TestAsciiChart::test_partial_block_each_bucket`이 18개 경계값을 1:1 검산.

| 결정론 환원 항목 | 함수 | 테스트 |
|-----------------|------|--------|
| 점수 입력 파싱 (5종 형식) | `parse_scores` | `TestParsing` 9 케이스 |
| 0~10 범위 검증 | `validate_range` | `TestValidation::test_range_*` |
| 누락 검증 | `validate_completeness` | `TestValidation::test_completeness_*` |
| 능력별 평균 산출 | `calculate_skill_scores` | `TestAveraging` 3 케이스 |
| Composite 산출 | `calculate_composite` | `TestAveraging::test_example_from_skill_md` |
| 레벨 매핑 | `level_for` | `TestLevelMapping` 4 케이스 |
| 다음 단계 부기 | `next_level_hint` | `TestLevelMapping::test_next_level_hint` |
| 강점·성장 영역 분류 | `classify_strengths` | `TestClassification` |
| 처방 스킬 매핑 | `prescriptions_for` | `TestPrescriptions` |
| ASCII partial block | `partial_block_for` | `TestAsciiChart::test_partial_block_each_bucket` |
| ASCII 막대 단일 | `render_ascii_bar` | `TestAsciiChart::test_render_bar_examples` |
| ASCII 차트 전체 | `render_ascii_chart` | `TestAsciiChart::test_render_chart_includes_all_skills` |
| Mermaid 차트 | `render_mermaid_chart` | `TestMermaid` |
| 한 줄 요약 | `one_line_summary` | `TestSummary::test_one_line_format` |
| 재진단 변화 추적 | `compute_delta` | `TestDelta` |
| 요약 출력 | `render_minimal_summary` | `TestSummary::test_minimal_summary` |
| 통합 파이프라인 | `process` | `TestProcess` |

## 6. 결정론 환원 *불가* 항목과 그 처리

본 스킬의 다음 단계는 결정론으로 환원 *불가*하며, LLM 자연어 추론이 담당한다. 단, 입력값은 모두 결정론 모듈의 산출물로 *고정*되어 할루시네이션 여지를 최소화한다.

| 단계 | 환원 불가 이유 | 할루시네이션 방지 장치 |
|------|---------------|----------------------|
| 5단계 한국어 코칭 해설 (강점·성장·다음 단계 설명) | 자연어 코칭 톤·맥락 적용은 텍스트 생성 본연의 영역 | 점수·레벨·처방 스킬은 모두 결정론 산출물을 *그대로 인용*만. "점수 패턴 동적 해석" 단계에서 임의로 점수를 *바꾸거나 만들어내지 않는다*는 절대 원칙 9가 적용 |
| 박사님(또는 사용자) 맥락 통합 | 개인 맥락 적용은 자연어 영역 | "박사님 정체성"·"강의 활용"은 SKILL.md '맥락 통합' 절의 *명시 인용*만 허용. 신상·일정 등 *알 수 없는 정보 추측 금지* |
| 청중 연령대 따른 톤 조정 | 자연어 영역 | 톤 조정은 단어 선택뿐, 점수·해석 내용은 결정론 모듈 결과 그대로 |

## 7. 외부 표준 문항지와의 관계

본 스킬의 20문항은 다음 외부 도구에서 *가져오지 않았다*. 동시에, *우열·대체 관계를 주장하지도 않는다*.

- **VIA Survey of Character Strengths** (Peterson & Seligman, *Character Strengths and Virtues*, Oxford UP, 2004): 24 성격 강점 측정. 본 스킬과 측정 대상 다름.
- **Gallup CliftonStrengths** (Rath, *StrengthsFinder 2.0*, 2007, Gallup Press): 34 재능 테마. 상용 도구.
- **Grit Scale** (Duckworth & Quinn, "Development and Validation of the Short Grit Scale (Grit-S)," *Journal of Personality Assessment*, 2009, 91(2):166-174): Follow-Through와 일부 개념 중복하지만 본 스킬은 별도 문항 사용.
- **Big Five Inventory** (John & Srivastava, 1999): 성격 5요인. 본 스킬과 별개.

사용자가 *임상·진로 결정의 단일 근거*로 본 스킬을 사용하면 안 된다. SKILL.md '출처·근거 안내' 절대 원칙 10 (자가 진단 도구 명시)이 이 한계를 사용자에게 항상 노출.

## 8. 처방 스킬 매핑의 근거

각 능력 약점에 대응하는 1순위 처방 스킬은 *동일 저자(박사님) 비전 시리즈 내부 구조* 기반.

| 약점 능력 | 1순위 처방 | 2순위 처방 | 근거 |
|----------|-----------|-----------|------|
| Big Picture | vision-future-needs-prediction | vision-futures-timeline-map | 두 스킬 모두 *장기 시야·미래 추세 분석*을 직접 다룸 (스킬 디스크립션 확인) |
| Reframing Goals | vision-goal-reframing | vision-statement-writer | 스킬명에 직접 명시 |
| Creating Strategies | vision-strategy-coach | vision-eight-training-areas | 전자는 전략 코칭, 후자는 박사님 8영역 훈련 프레임 |
| Following Through | vision-follow-through-habits | vision-progress-review | 스킬명에 직접 명시 |

처방 스킬 매핑은 결정론 모듈 `PRESCRIPTION_MAP` 상수에 고정. 임의 변경 금지.

## 9. 검증되지 않은 사항 (사용자 안내 의무)

다음은 본 스킬의 *명시적 한계*이며, 사용자에게 솔직히 안내해야 한다:

1. **Cronbach's α 등 신뢰도 검증 부재**: 본 도구의 내적 일관성·검사-재검사 신뢰도는 측정되지 않았다.
2. **타당도 검증 부재**: 4능력 구성 타당도(예: 확증적 요인분석)는 수행되지 않았다.
3. **규준 집단(normative sample) 부재**: 점수 백분위·표준화 점수는 가용하지 않다. "또래 상위 10%" 같은 라벨은 일반적 NRS 해석 관례에 따른 *근사적 표현*이지 표준화 통계가 아니다.
4. **문화·연령 차이**: 십대~성인 적용을 의도하나, 특정 연령군에서의 차별적 기능(DIF) 검증은 없었다.
5. **단일 시점 자가 보고**: 자가 보고 척도의 일반적 한계(사회적 바람직성 편향, 자기 인식 정확도 한계)가 동일 적용된다.

이 한계들은 SKILL.md '출처·근거 안내'·'절대 원칙 10' 절과 일관된다.

## 10. SKILL.md 수정·관리 원칙

본 SOURCES.md를 *수정할 때마다* SKILL.md '출처·근거 안내' 절이 일관 유지되는지 *반드시* 확인. 두 문서의 핵심 진술이 어긋나면 SOURCES.md를 단일 진실 원천으로 본다.
