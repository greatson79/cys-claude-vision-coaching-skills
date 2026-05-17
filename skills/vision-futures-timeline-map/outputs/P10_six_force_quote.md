# P10 — 박사님 6대 영역 인용문 원문 보여줘

## 1. 사용자 입력
> 박사님 6대 영역 인용문 원문 보여줘

## 2. 엔진 분기 매핑
```json
classify_entry => {"entry_type": "quote_full_text", "matched_keywords": ["인용문 원문"]}
verify_quote("경제, 사회, 기술, 산업, 환경, 법, 정치, 제도, 글로벌 패권, 문화, 종교, 영성")
   => {"verified": true, "type": "direct", "id": "six_force_domains", "source": "『미래준비학교』, 2016 (6대 변화 영역 단락)"}
crosscheck_quote six_force_domains
   => MATCH (Aguilar 1967 ETPS → Fahey & Narayanan 1986 STEEP → Hines & Bishop 2015 STEEPS)
```

## 3. SKILL.md 처리 흐름 → 특정 인용문 원문 전체 요청 분기

> SKILL.md "특정 인용문의 원문 전체 요청인 경우" 절:
> 1) SKILL.md에 수록된 인용문을 그대로 제공.
> 2) "본 스킬에 수록된 인용문의 범위입니다. 전체 원문 확인은 박사님 책(『미래준비학교』 2016)을 직접 참조하시기 바랍니다"라고 고지.
> 3) SKILL.md에 있는 인용문 이외에 Claude가 추가·보완하거나 "..."의 빈 부분을 채우지 않는다.

## 4. 산출물

### 박사님 책 6대 영역 인용문 (verify_quote=direct, id=six_force_domains)

> *"경제, 사회, 기술, 산업, 환경, 법, 정치, 제도, 글로벌 패권, 문화, 종교, 영성 등의 영역에서 일어나는 미래 변화에 대한 방향 감각이 필요하다."*
> — 최윤식, 『미래준비학교』, 아시아미래연구소, 2016 (6대 변화 영역 단락)

### SKILL.md 명시 고지
> 본 스킬에 수록된 인용문의 범위입니다. 전체 원문 확인은 박사님 책(『미래준비학교』 2016)을 직접 참조하시기 바랍니다.

### 본 스킬의 STEEPS 박사님판 6축 매핑 (엔진 list_steeps, 박사님 책 원문 그대로)
| 코드 | 박사님판 영문 | 한글 | 박사님 책 원문 raw 도메인 |
|---|---|---|---|
| S1 | Society | 사회·문화 | 사회, 문화 |
| T  | Technology | 기술·산업혁신 | 기술, 산업 |
| E1 | Economy | 경제·금융 | 경제 |
| E2 | Environment | 환경·생태 | 환경 |
| P  | Politics | 정치·법·제도·글로벌 패권 | 법, 정치, 제도, 글로벌 패권 |
| S2 | Spirituality | 종교·영성·가치관 | 종교, 영성 |

### 외부 1차 출처 1:1 대조 (엔진 crosscheck_quote)
- Aguilar, Francis J., *Scanning the Business Environment*, Macmillan, 1967 (ETPS 원형)
- Fahey, Liam & Narayanan, V. K., *Macroenvironmental Analysis for Strategic Management*, West Publishing, 1986 (STEEP 확장)
- Hines, Andy & Bishop, Peter, *Thinking about the Future: Guidelines for Strategic Foresight*, 2nd ed., Hinesight, 2015 (STEEPS)
- 박사님판 6축은 학계 표준 STEEPS의 한국·신학 맥락 변형으로 1:1 대응 가능 (verdict=MATCH).

## 5. 출처 검증
| 항목 | verify_quote / crosscheck |
|---|---|
| 6대 영역 원문 | ✅ direct (six_force_domains) |
| 외부 학계 STEEPS 매핑 | ✅ MATCH (Aguilar 1967 / Hines & Bishop 2015) |

## 6. 박사님 책 외 내용 분리 표기
- 본문 인용은 박사님 책 원문 그대로.
- 외부 학계 출처는 1:1 대조 목적의 학계 표준 문헌 명시만 — Aguilar·Fahey & Narayanan·Hines & Bishop의 주장을 본문에 *추가*하지 않음 (할루시네이션 차단).

## 7. 자기 검증 체크리스트
- [x] quote_full_text 분기 진입
- [x] SKILL.md 명시 고지 문구 그대로 사용
- [x] 인용문 verify_quote=direct
- [x] 외부 1차 출처 1:1 crosscheck=MATCH
- [x] "..."의 빈 부분 채우지 않음 (SKILL.md 분기 절 준수)
- [x] STEEPS 6축은 엔진 list_steeps 출력 그대로
