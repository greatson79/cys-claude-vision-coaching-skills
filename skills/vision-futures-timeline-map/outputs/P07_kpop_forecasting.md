# P07 — Forecasting만으로 K-pop 글로벌 시장 미래 추정

## 1. 사용자 입력
> Forecasting만으로 K-pop 글로벌 시장 미래 추정

## 2. 엔진 분기 매핑
```json
classify_entry => {"entry_type": "methodology_only", "methodology": "forecasting", "matched_keywords": ["forecasting만"]}
current_year   => 2026
compute_intervals(2026) => 단기 2026~2031 / 중기 2031~2041 / 장기 2041~2056
list_methodologies.forecasting => "현재에서 미래로 트렌드를 투사 (Forecasting)" (박사님 책 다이어그램)
```

## 3. SKILL.md 처리 흐름 → 방법론 단독 분기 (Forecasting만)

> SKILL.md "방법론(Backcasting/Forecasting) 단독 지정 요청인 경우" 절: 비전 영역(K-pop 글로벌 시장) 확인 → Forecasting 관점으로 현재 트렌드를 작업 ①~④ 기준으로 단기→중기→장기로 투사. 완료 후 "두 방향을 통합한 전체 미래지도 작성을 이어서 진행하시겠습니까?" 제안.

## 4. 산출물 — Forecasting 단독 (현재(Y) → 미래)

### 박사님 책 다이어그램 정의 (엔진 list_methodologies)
> Forecasting = 현재에서 미래로 트렌드를 투사 (방향: 현재(Y) → 미래(Y+N))
> 출처: 『미래준비학교』, 2016 (기초 미래예측 프로세스 다이어그램)

### 시간축별 트렌드 투사 (Claude 코칭, K-pop 분야)
| 구간 | Forecasting 결과 (현재 → 미래) |
|---|---|
| 단기 2026~2031 | 4세대 그룹 글로벌 정착 / AI 보컬·작곡 정착 / 일본·동남아 음원 압도 / K팝 콘서트 IP 사업 확대 |
| 중기 2031~2041 | 가상 아이돌(VTuber·AI 아이돌) 주류화 / 다국적 멤버 그룹 비율 60%↑ / 음악 NFT·구독제 통합 / 트로트·발라드 글로벌 확장 |
| 장기 2041~2056 | K팝 정의 자체가 글로벌 K-스타일로 확장 / AI 1인 프로듀서 시대 / 메타버스 라이브 시장이 실물 콘서트 추월 가능성 |

### 작업 ①~④ 기준 투사 (Forecasting 관점 한정)
- ① 직면할 상황: 위 시간축 표 그대로
- ② 필요할 것: 다국어 IP·해외 자본 파트너십·AI 윤리 라이센스
- ③ 약한 신호 5소스 적용: 학술지(엔터테인먼트 산업 연구)·블로그/팬덤·스타트업/특허(AI 보컬·VTuber 플랫폼)·현장 관찰(콘서트 매진율·MD 매출)·이상 사건(스타 이슈·국가 규제)
- ④ 뜻밖의 미래: 비약적 진보=AI 가상 아이돌 완전 자율 작곡·공연 / 붕괴=K-pop 한류 차단 정책·팬덤 분열

### 완료 후 SKILL.md 명시 메시지
"두 방향을 통합한 전체 미래지도 작성을 이어서 진행하시겠습니까?"

## 5. 출처 검증

### 박사님 책 원문 인용 (verify_quote 통과)
- 작업 ③ 단락 재인용 (id=colin_powell_certainty, verify_quote=reindirect, crosscheck=MATCH with *My American Journey* Random House 1995):
  > *"100% 정확한 정보는 쓸모없다. 100% 확실하게 폭발이 일어날 것이라 말할 수 있을 때는 이미 늦기 때문이다."* — Colin Powell
  > 본 인용은 약한 신호 수집(작업 ③)이 Forecasting의 입력이 됨을 뒷받침한다.
- 미래 징후 직접 인용 (id=futures_signs, verify_quote=direct):
  > *"미래 징후는 미래 변화의 모습을 묘사하거나 미래에 발생할 수 있는 변화의 결과를 구성하는 퍼즐 조각이다."*

### 사실 주장별 출처 표
| 사실 주장 | 출처 |
|---|---|
| Forecasting 정의 | 엔진 list_methodologies → 박사님 책 다이어그램 |
| 시간축 1:2:3 비율 | 엔진 compute_intervals |
| 4가지 고려사항·약한 신호·Wildcard | 엔진 카탈로그 |
| Colin Powell 재인용 | verify_quote=reindirect, crosscheck=MATCH |
| 미래 징후 인용 | verify_quote=direct (futures_signs) |
| K-pop 구체 사건들 | **Claude 코칭 제안** — 박사님 책에 K-pop 직접 사례 없음 |

## 6. 박사님 책 외 내용 분리 표기
- K-pop 시장의 구체 트렌드·사건·예측은 모두 Claude 코칭 제안.
- 통계·시장 규모는 본 스킬 범위 밖 — 사용자가 정확한 수치를 원하면 IFPI·Statista·문화체육관광부 1차 자료 직접 확인 권장.

## 7. 자기 검증 체크리스트
- [x] methodology_only(forecasting) 분기 진입
- [x] Forecasting 정의 엔진 출력 그대로
- [x] 작업 ①~④를 Forecasting 관점으로 한정 (Backcasting 미사용)
- [x] 시간축은 엔진 compute_intervals
- [x] 분야 구체 사건은 코칭 제안 분리
- [x] 완료 후 SKILL.md 명시 메시지로 다음 단계 제안
