# P01 — 이 스킬의 정의를 한 문단으로 알려줘

## 1. 사용자 입력
> 이 스킬의 정의를 한 문단으로 알려줘

## 2. 엔진 분기 매핑
```json
classify_entry => {"entry_type": "concept_only", "matched_keywords": ["이 스킬의 정의", "스킬의 정의", "정의를 한 문단", "한 문단으로 알려"]}
```

## 3. SKILL.md 처리 흐름 → 개념 설명 분기

## 4. 산출물 (한 문단 정의)

vision-futures-timeline-map은 최윤식 박사 『미래준비학교』(2016)의 *미래지도(Futures Timeline Map)* 도구를 그대로 구현한 비전 코칭 스킬로, 사용자가 자신의 비전 영역에 대한 *맞춤 미래지도*를 단·중·장기 시간축으로 작성하도록 돕는다. 박사님 책의 핵심 비유 — *"미래지도란 축척이 5000:1인 정밀 지도처럼 상세한 미래 정보를 담고 있는 지도가 아니다. 오히려 콜럼버스가 아메리카 대륙을 발견할 때 쓴 지도에 비유할 수 있다... 중요한 것은 콜럼버스가 형편없고 엉망인 지도를 가지고 신대륙을 발견해냈다는 점이다."* — 를 토대로, ① 미래에 직면할 상황 ② 나에게 필요할 것 ③ 보잘것없는 정보 ④ 뜻밖의 미래 4가지 고려사항을 STEEPS 박사님판 6대 변화 영역(사회·기술·경제·환경·정치·영성)에 걸쳐 채워 넣는다.

→ "미래지도 작성을 시작하시겠습니까?"

## 5. 출처 검증
| 인용 | verify_quote | type | source |
|---|---|---|---|
| 콜럼버스 비유 | ✅ verified=true | direct | 『미래준비학교』, 아시아미래연구소, 2016 (콜럼버스 비유 단락) |

외부 1:1 대조: `crosscheck_quote futures_map_definition` → MATCH (Hines & Bishop, *Thinking about the Future*, 2nd ed., 2015 — directional vs precise 구분).

## 6. 박사님 책 외 내용
없음. 모든 사실 주장이 박사님 책 verify_quote 통과 인용 + 스킬 자체의 description 요약.

## 7. 자기 검증 체크리스트
- [x] 인용문 verify_quote=true
- [x] 외부 출처 1:1 crosscheck=MATCH
- [x] 박사님 책 외 사실 주장 없음
- [x] SKILL.md 진입 유형(concept_only) 그대로 적용
- [x] 코칭 제안 분리 표기 불필요(개념 설명만)
