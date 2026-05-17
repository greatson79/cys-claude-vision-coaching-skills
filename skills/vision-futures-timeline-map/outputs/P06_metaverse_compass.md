# P06 — 메타버스 스타트업을 위한 미래 나침반 만들어줘

## 1. 사용자 입력
> 메타버스 스타트업을 위한 미래 나침반 만들어줘

## 2. 엔진 분기 매핑
```json
classify_abcd => {"abcd_type": "C", "matched_keyword": "미래 나침반 만들어"}
```

## 3. SKILL.md 처리 흐름 → 유형 C 미래 나침반 모니터링 루틴만

> SKILL.md 유형 C 처리: 1단계(비전 분야 확인) → 5단계만 수행. 2~4단계 생략. 산출물: 매일·매주·분기별 모니터링 루틴 표 (분야 특화 구독 매체 목록 포함).

## 4. 산출물

### 1단계 — 비전 영역 확인
영역: **메타버스 스타트업** (사용자 명시).

### 5단계 — 미래 나침반 형성

박사님 책 직접 인용 (verify_quote=direct, id=futures_compass_definition):

> *"미래 나침반은 넓고 깊고 통합적인 사고의 틀, 폭넓게 멀리 보는 관찰력, 계속해서 세상의 변화를 관찰하는 모니터링 습관이다."* (『미래준비학교』, 2016)

### 모니터링 루틴 (Claude 코칭 — 박사님 책 규약 따름)

| 주기 | 활동 | 분야 특화 (메타버스 스타트업) |
|---|---|---|
| 매일 30~60분 | 미래 변화 단편 수집 | XR/VR/AR 뉴스 — Road to VR, UploadVR, MIXED, 한국 메타버스 산업협회 |
| 매주 1시간 | 미래 변화 정리 | Apple Vision Pro·Meta Quest·Pico 출시 동향, AI×메타버스 데모 |
| 매월 1회 | 약한 신호 5소스 점검 (엔진 카탈로그) | 학술지·씽크탱크·스타트업/특허·현장 관찰·이상 사건 |
| 분기 1회 | 미래지도 갱신 | 단·중·장기 시간축 재점검 |
| 연 1회 | 6힘 영역(STEEPS) 전반 재점검 | T(하드웨어/SDK)·E1(시장규모)·E2(전력) ·P(개인정보·아바타법) ·S1(소셜)·S2(가치 윤리) |

### 구독 매체 추천 (Claude 코칭 제안)
- 영문: VentureBeat AR/VR, The Information XR newsletter, IEEE VR proceedings
- 한글: 한국전자통신연구원(ETRI) 메타버스 보고서, KISDI 디지털 컨버전스 동향
- 커뮤니티: r/virtualreality, X 해시태그 #VisionPro #MetaQuest

### 박사님 책 인용 한 줄로 닫기
> *"미래지도는 미래 통합시나리오, 다양한 미래에 대한 가정들이다. 미래 나침반은 넓고 깊고 통합적인 사고의 틀이다."* (verify_quote=direct, id=futures_map_vs_compass)

## 5. 출처 검증
| 인용 | verify_quote | crosscheck |
|---|---|---|
| 미래 나침반 정의 | ✅ direct (futures_compass_definition) | 박사님 책 내부 정의 |
| 미래지도 vs 미래 나침반 | ✅ direct (futures_map_vs_compass) | 박사님 책 내부 정의 |

## 6. 박사님 책 외 내용 분리 표기
- 박사님 책 인용 2건은 verify_quote 통과 원문 그대로.
- 루틴 표의 분야 특화 항목·구독 매체 추천은 **Claude 코칭 제안** (박사님 책에 메타버스 구체 사례 없음, SKILL.md 절대원칙 #9 고지).

## 7. 자기 검증 체크리스트
- [x] 유형 C 분기 진입
- [x] 2~4단계 생략, 1단계+5단계만 수행 (SKILL.md 명시)
- [x] 박사님 책 인용 2건 모두 verify_quote=direct
- [x] 매일·매주·매월·분기·연 루틴 (박사님 책 규약)
- [x] 약한 신호 5소스는 엔진 카탈로그
- [x] 분야 특화·구독 매체는 코칭 제안 분리
