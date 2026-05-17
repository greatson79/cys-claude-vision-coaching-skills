# P09 — 박사님 vs 토플러 미래학 비교 미래지도

## 1. 사용자 입력
> 박사님 vs 토플러 미래학 비교 미래지도

## 2. 엔진 분기 매핑
```json
classify_entry => {"entry_type": "out_of_scope", "matched_keywords": ["박사님 vs"]}
```

## 3. SKILL.md 처리 흐름 → SKILL.md 범위 외 분기

> SKILL.md "SKILL.md 범위 외 내용 요청인 경우" 절:
> 1) 고지: "해당 내용은 본 스킬(『미래준비학교』 2016 기반)에 수록되지 않았습니다. 수록된 범위 내에서만 안내드릴 수 있습니다."
> 2) SKILL.md 내에서 가장 근접한 내용 제공.
> 3) "더 상세한 비교·분석은 해당 저서를 직접 참조하시기 바랍니다" 안내.
> 4) "박사님 책 기반으로 미래지도 작성을 시작하시겠습니까?" 제안.

## 4. 산출물

### (a) SKILL.md 명시 고지 (그대로)
> 해당 내용은 본 스킬(『미래준비학교』 2016 기반)에 수록되지 않았습니다. 수록된 범위 내에서만 안내드릴 수 있습니다.

### (b) SKILL.md 내 가장 근접한 내용
- 박사님 책에서 외부 미래학자는 작업 ④ 단락에 **Peter Schwartz** 재인용이 유일하게 수록되어 있습니다 (verify_quote=reindirect, id=peter_schwartz_skeleton).
  > *"미래의 골격이 될 거대한 흐름의 방향을 바꿀 뜻밖의 강력한 사건들은 그 기본적인 행동 유형을 살피다 보면 필연적으로 드러나게 마련이다."* — Peter Schwartz (Global Business Network 공동창업, 시나리오 플래닝 전문가)
  > crosscheck=MATCH: *The Art of the Long View: Planning for the Future in an Uncertain World*, Doubleday Currency, 1991.
- **Alvin Toffler**는 박사님 책 본 스킬 범위(SKILL.md 수록 인용 DB) 안에서는 인용되어 있지 않습니다. 본 스킬은 박사님 책 직접 인용 또는 박사님 책 재인용에 한정해 답합니다(절대원칙 #7·#8).
- 따라서 "박사님 vs 토플러" 비교는 본 스킬 범위 밖이며, Claude가 자체 학습 지식으로 토플러를 인용하는 것은 SKILL.md 절대원칙에 따라 금지됩니다.

### (c) 안내
> 더 상세한 비교·분석은 토플러의 *Future Shock* (Random House, 1970), *The Third Wave* (William Morrow, 1980), *Powershift* (Bantam Books, 1990) 등 해당 저서를 직접 참조하시기 바랍니다. 본 스킬은 박사님 책 범위 안에서만 안내할 수 있음을 양해 부탁드립니다.

### (d) 제안
> 박사님 책 기반으로 미래지도 작성을 시작하시겠습니까?

## 5. 출처 검증
| 인용 | verify_quote | crosscheck |
|---|---|---|
| Peter Schwartz 재인용 | ✅ reindirect (peter_schwartz_skeleton) | MATCH (Schwartz 1991, *The Art of the Long View*) |
| Toffler 저서명 (서지만 명시) | 인용 본문 없음 — 외부 저서 *지칭만* 허용 (사용자 안내 차원) | n/a |

## 6. 박사님 책 외 내용 분리 표기
- 토플러의 사상·주장은 본 답변에 인용되지 않음 (할루시네이션 차단).
- Toffler 저서명은 "사용자가 외부 자료를 직접 참조"하도록 안내하는 서지 정보로만 명시 (사상 인용 아님).

## 7. 자기 검증 체크리스트
- [x] out_of_scope 분기 진입
- [x] SKILL.md 명시 고지 문구 그대로 사용
- [x] 박사님 책 재인용 1건(Peter Schwartz)만 verify_quote+crosscheck로 인용
- [x] Toffler의 주장·사상은 본문에 인용하지 않음 (할루시네이션 차단)
- [x] 외부 저서 직접 참조 안내
- [x] 박사님 책 기반 미래지도 작성 제안
