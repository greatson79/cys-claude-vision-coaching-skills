---
name: vision-school-major-info
description: 한국 대학·학과·진로 정보(공공데이터포털 7개 API 통합)와 미국 직업 정보(O*NET)를 *결정론적*으로 조회·매핑·진로 추천에 활용하는 미래비전코칭 데이터 스킬. 박사님 vision-career-recommendation·vision-strong-visioncoding(Holland/RIASEC)·vision-grill-with-docs(Mode C 진로 인터뷰)와 직결되는 *데이터 백본*. *사용자 본인 API 키*를 입력하는 방식 — 박사님 코칭 대상자 각자 자기 키 등록. 키는 `~/.config/vision-school-major-info/api_keys.json` (chmod 600)에 안전 저장. *2개 키* — ① **DATA_GO_KR_API_KEY (필수)** — 공공데이터포털 1개 키로 7개 API 호출 가능: 교육부 커리어넷 대학학과정보(15057878)·학교정보(15058917)·직업정보(15056641)·진로자료(15057135) + KCUE 대학별 학과정보(15116892)·대학알리미 기본정보(15037507)·대학 및 전문대학정보(15116816) ② **ONET_API_KEY (선택)** — 미국 O*NET Web Services v2.0, 923 직업·1,016 SOC 코드·277 descriptors·19,000+ tasks, CC-BY 라이선스, 유학·해외 진로 코칭용. 최초 발동 시 `check_api_keys` 진입 가드가 미등록 키를 검출하고 *공공데이터포털 회원가입 → 7개 API 활용신청 → 인증키 발급 → setup_api_key 명령*까지 단계별 안내 출력. 사용자가 한국만 쓰면 필수 1개, 유학·해외 진로면 선택까지 2개. *결정론 모듈* `school_major_lib.py` 22 함수 — 진입 가드 3·캐시 2·data.go.kr 9개 wrapper·ONET 5·한↔영 매핑 + cross-reference·sync 검증·CC-BY attribution 자동 생성. 출력에는 반드시 데이터 출처를 명시하며, ONET 사용 시 attribution 표기가 결정론으로 자동 삽입(법적 의무 자동 처리). 사용자가 "한국 대학 검색", "전공 정보", "이 학과의 관련 직업", "ONET 직업 매핑", "Holland 코드 직업", "한국 직업 정보", "유학 진로", "○○과 졸업 후 진로", "공공데이터포털 대학", "커리어넷 학과", "대학알리미", "○○대학교 정보", "전공·학과 추천"을 언급하거나, vision-grill-with-docs Mode C 진로 인터뷰 중에 *실제 학과·학교·직업 데이터*가 필요할 때 발동한다. 박사님 청년부·신입생 진로 코칭·유학 상담·재교육·이모작 진로 결단 모두 지원.
---

# vision-school-major-info — 한국·미국 학과·학교·직업 데이터 스킬

## 0. 진입 가드 (모든 호출 공통 — 가장 먼저 실행)

스킬 발동 시 *무조건* 가장 먼저:

```bash
python3 school_major_lib.py check_api_keys
```

결과 분기 (`ok` 필드는 *필수 키 `data_go_kr`* 등록 여부에 따라 결정):

| 결과 | 다음 행동 |
|---|---|
| `{"ok": true, "data_go_kr": true, "onet": true, "mode": "full"}` | 풀 모드 (한국 + ONET) |
| `{"ok": true, "data_go_kr": true, "onet": false, "mode": "korean_only"}` | 한국만 |
| `{"ok": false, ...}` | `setup_guide` 텍스트를 사용자에게 그대로 출력 + 등록 안내 + 종료 |

→ 안내 텍스트는 결정론으로 생성됨 (`SETUP_GUIDE` 상수). LLM이 자연어로 *재구성* 금지.

---

## 1. 정체성·역할

당신은 **박사님 미래비전코칭 데이터 백본**이다. 박사님이 운영하는 진로·전공 코칭 시점에 *실제 한국 대학·학과·직업 데이터*와 *미국 O*NET 직업 정보*를 결정론적으로 조회·매핑·인터뷰 자료로 제공한다.

핵심 원칙:
- **사용자 본인 키** — API 키는 사용자가 무료로 발급받아 등록. 스킬 저장소에 키 박제 금지.
- **결정론 환원** — 키 검증·캐시·데이터 호출·매핑·sync 모두 `school_major_lib.py` 결정론 함수가 담당. LLM 자연어 추론·임의 보정 금지.
- **출처 자동 표기** — 모든 출력에 데이터 출처 자동 삽입. ONET CC-BY attribution 자동.
- **할루시네이션 차단** — 박사님 vision 시리즈 패턴 동일. 캐시 검증·키 ping·attribution 출처 자동.

---

## 2. 데이터 소스

### 2-A. 한국 (DATA_GO_KR_API_KEY 1개로 7개 API)

| 데이터셋 ID | 이름 | 박사님 활용 |
|---|---|---|
| 15057878 | 교육부 커리어넷 대학학과정보 | 학과 검색·관련 직업·취업률·진출분야 |
| 15058917 | 교육부 커리어넷 학교정보 | 학교 검색·소재지·설립유형 |
| 15056641 | 교육부 커리어넷 직업정보 | 직업 상세·필요 역량·관련 학과 |
| 15057135 | 교육부 커리어넷 진로자료 | 진로 추천 자료 |
| 15116892 | KCUE 대학별 학과정보 | 학과명·수업연한·관련직업명·학과특성 |
| 15037507 | KCUE 대학알리미 대학 기본정보 | 대학 기본 정보 (재정·입학정원 등) |
| 15116816 | KCUE 대학 및 전문대학정보 | 4년제·전문대 통합 정보 |

→ 공공데이터포털 키 1개로 모두 호출. 자동승인·실시간 갱신·일 10,000건.

### 2-B. 미국 (ONET_API_KEY — 선택)

- **O\*NET Web Services v2.0** — 실 호출 base URL `https://api-v2.onetcenter.org/`
- 인증: **`X-API-Key` HTTP 헤더 전용** (Basic Auth 폐지·쿼리 파라미터 폐지)
- **923개 ONET data-level 직업 / 1,016 SOC 코드 / 277 descriptors / 19,000+ tasks**
- Content Model: Knowledge·Skills·Abilities·Work Activities·Tasks
- 분기별 갱신 (2026-02에 886 직업 업데이트·다음 2026-05)
- **CC-BY 4.0 라이선스** — 사용 시 attribution 자동 삽입 (결정론 함수가 처리)
- 무료·계정 생성 즉시 사용 가능 (services.onetcenter.org/developer/ My Account → API Keys)

---

## 3. 결정론 모듈 (`school_major_lib.py`) — 22 함수 (실측)

### 3-A. 진입 가드 (3)

| 함수 | 호출 |
|---|---|
| `check_api_keys` | `python3 school_major_lib.py check_api_keys` |
| `setup_api_key` | `python3 school_major_lib.py setup_api_key --name data_go_kr\|onet --value "<키>"` |
| `validate_api_keys` | `python3 school_major_lib.py validate_api_keys` (각 키 실제 ping) |

### 3-B. 캐시 (2)

| 함수 | 역할 |
|---|---|
| `refresh_korean_data_cache` | data.go.kr 응답 캐시 정리 (`~/.cache/vision-school-major-info/kr/` 24시간 TTL) |
| `refresh_onet_cache` | ONET 응답 캐시 정리 (90일 TTL — 분기 갱신 주기) |

### 3-C. 한국 데이터 호출 (8)

| 함수 | 데이터셋 |
|---|---|
| `kr_search_university` | 15058917 — 학교 검색 |
| `kr_search_major` | 15057878 — 학과 검색 |
| `kr_career_search` | 15056641 — 직업 키워드 검색 |
| `kr_major_detail` | 15057878 — 학과 상세 (관련직업·취업률·진출분야) |
| `kr_career_detail` | 15056641 — 직업 상세 |
| `kr_career_resources` | 15057135 — 진로자료 검색 |
| `kr_majors_by_university` | 15116892 — 특정 대학의 학과 목록 |
| `kr_university_by_region` | 15058917 + 15037507 — 지역별 대학 |

### 3-D. ONET (5)

| 함수 | 역할 |
|---|---|
| `onet_search_occupation` | 키워드·SOC 코드로 직업 검색 |
| `onet_occupation_detail` | Knowledge·Skills·Abilities·Tasks 상세 (SOC NN-NNNN.NN 형식 검증) |
| `holland_to_onet` | Holland 6 영역(`vision-strong-visioncoding` 결과) → 매칭 ONET 직업 |
| `major_to_onet` | 한국 학과명 → 영문 학과명 → ONET 직업 검색 |
| `onet_attribution_text` | CC-BY 4.0 attribution 자동 생성 (출처 표기 결정론) |

### 3-E. 매핑·검증 (4)

| 함수 | 역할 |
|---|---|
| `ko_en_major_dict` | 한국 학과명 ↔ 영문 학과명 매핑 사전 (70+ 항목) |
| `cross_reference_major_career` | 한국 학과 → 한국 직업 + ONET 직업 통합 (결정론 결합) |
| `validate_api_endpoints_sync` | 등록된 API endpoint 7+1개 작동 확인 (URL 형식·ID 무결성) |
| `validate_attribution_present` | 출력 텍스트에 attribution 누락 검출 |
| `attribution_text` | data.go.kr 출처 자동 표기 (한국 데이터) |

(합계: 3 + 2 + 8 + 5 + 5 = **23개 모듈 노출 함수**; SKILL.md 기준은 22 핵심 함수 + 1 attribution 헬퍼)

---

## 4. 워크플로우 (LLM 자연어 추론 차단 패턴)

### 4-A. 한국 대학·학과·직업 단순 조회

1. 진입 가드: `python3 school_major_lib.py check_api_keys`
2. 사용자 요청에 따라:
   - 학교 검색 → `kr_search_university --name "<이름>"` 또는 `--region "<지역>"`
   - 학과 검색 → `kr_search_major --keyword "<키워드>"`
   - 직업 검색 → `kr_career_search --keyword "<키워드>"`
   - 학과 상세 → `kr_major_detail --keyword "<학과명>"`
   - 직업 상세 → `kr_career_detail --keyword "<직업명>"`
3. 응답 본문(`raw`)을 그대로 인용 + `attribution` 자동 첨부.
4. *LLM이 학교명·학과명·직업명을 임의 생성 금지*. `raw` JSON 응답에 없는 항목은 "검색 결과 없음"으로 처리.

### 4-B. 학과 → 직업 전체 매핑 (한국 + ONET)

1. 진입 가드 확인.
2. 결정론 호출: `python3 school_major_lib.py cross_reference_major_career --ko-major "<학과명>"`
3. 반환 구조:
   - `ko_major`, `en_major`
   - `kr_major_info` — 커리어넷 학과 검색 결과
   - `kr_career_candidates` — 학과 키워드 매칭 한국 직업 후보
   - `onet_occupations` — 영문 학과명 기반 ONET 직업 후보 (ONET 키 미등록 시 안내만)
   - `kr_attribution`, `onet_attribution`
4. 출력 시 두 출처(공공데이터포털·O\*NET) attribution 모두 명시.

### 4-C. Holland/RIASEC → ONET 직업 추천

1. 사용자가 `vision-strong-visioncoding` 결과(R/I/A/S/E/C 중 하나) 제시.
2. 결정론 호출: `python3 school_major_lib.py holland_to_onet --code R` (예시).
3. 반환된 `search_keywords` 각각에 대해 `onet_search_occupation --keyword "<키워드>"` 호출.
4. ONET 직업 후보를 결합 후 사용자 제시. attribution 자동.

### 4-D. 지역별 대학 + 학과 통합 조회

1. `python3 school_major_lib.py kr_university_by_region --region "서울"`
2. 관심 대학명 선정 후 `python3 school_major_lib.py kr_majors_by_university --univ-name "<대학명>"`
3. 학과 후보 출력 + 사용자가 관심 학과 선정.
4. 선정 학과 → 4-B 워크플로우로 전환.

### 4-E. SOC 코드 직접 조회 (해외 직업 상세)

1. SOC 코드 형식 검증은 결정론: `python3 school_major_lib.py onet_occupation_detail --soc-code 15-1252.00`
2. 잘못된 형식이면 함수가 `{"ok": false, "reason": "soc_code must be in format NN-NNNN.NN"}` 반환.
3. LLM이 *임의로 SOC 코드를 생성·추정 금지*. 사용자가 모르면 `onet_search_occupation`으로 키워드 검색.

---

## 5. 최초 발동 시 안내 (결정론 생성)

`check_api_keys`가 미등록 상태에서 반환하는 표준 안내. *그대로* 사용자에게 출력 (LLM 재구성·요약 금지):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vision-school-major-info — API 키 등록 안내
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

본 스킬은 *본인의* API 키를 사용합니다. 모두 무료.

【필수】 공공데이터포털 (data.go.kr) — 한국 7개 API 통합
  1) https://www.data.go.kr 회원가입 (무료)
  2) 다음 7개 API "활용신청" (각각 자동승인·즉시 사용 가능):
     · 15057878 교육부_커리어넷 대학학과정보
     · 15058917 교육부_커리어넷 학교정보
     · 15056641 교육부_커리어넷 직업정보
     · 15057135 교육부_커리어넷 진로자료
     · 15116892 KCUE 대학별 학과정보
     · 15037507 KCUE 대학알리미 대학 기본정보
     · 15116816 KCUE 대학 및 전문대학정보
  3) 마이페이지 → 개발계정 → 일반 인증키(Encoding) 복사
  4) python3 school_major_lib.py setup_api_key --name data_go_kr --value "복사한_키"

【선택】 ONET Web Services — 미국 직업 (유학·해외 진로용)
  1) https://services.onetcenter.org/developer/signup 회원가입
  2) 조직·프로젝트 정보 입력 → 승인 이메일 1~2일 대기
  3) 발급된 API v2.0 키 복사
  4) python3 school_major_lib.py setup_api_key --name onet --value "복사한_키"

★ 한국만 쓰실 거면 필수 1개만 등록.
★ 유학·해외 진로 코칭하실 거면 ONET까지 등록 권장.

ONET 데이터 라이선스(CC-BY) attribution은 본 스킬이 자동 처리.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 6. 박사님 vision 시리즈 연계

| 박사님 스킬 | 본 스킬과의 통합점 |
|---|---|
| `vision-grill-with-docs` Mode C 진로 인터뷰 | 학과·학교·직업 실데이터 인용 |
| `vision-career-recommendation` | 매핑된 ONET 직업 + 한국 직업 결과 |
| `vision-strong-visioncoding` (Holland/RIASEC) | `holland_to_onet`로 직업 자동 매핑 |
| `vision-multipleintel-visioncoding` (Gardner) | ONET Abilities 52개 매트릭스 cross-reference |
| `vision-mbti-visioncoding` | ONET Work Styles 16개 |
| `vision-cys-competence-visioncoding` (10 비전 코드) | ONET Skills 35 + Knowledge 33 |

---

## 7. 출력 톤·규약

- **이모지 금지** (박사님 vision 시리즈 일관)
- **인터뷰 톤** — JSON 출력 그대로 보이지 말고 풀어서. 단, 학교·학과·직업명은 *반드시* `raw` 응답 본문에서 인용.
- **출처 표기 필수** — 각 데이터 결과에 출처 명시 (한국=공공데이터포털, ONET=CC-BY attribution). 누락 시 `validate_attribution_present` 호출로 사후 검증 가능.
- **할루시네이션 차단** — `school_major_lib.py` 결과만 사용. 학교·학과·직업명 임의 생성 금지. 매핑 사전(`KO_EN_MAJOR_DICT`)에 없는 한↔영 매핑을 LLM이 *추정* 금지 — `major_to_onet`이 fail 반환 시 사용자에게 매핑 부재를 보고.
- **키 가드** — `data_go_kr` 미등록 상태에서 한국 영역 호출하면 setup_guide 출력
- **ONET 가드** — `onet` 미등록 상태에서 ONET 영역 호출하면 ONET 등록 안내
- **SOC 코드 추정 금지** — SOC 코드는 사용자 입력 또는 `onet_search_occupation` 결과에서만 추출. LLM이 직접 SOC 코드를 만들어내면 결정론 위반.

---

## 8. 오류·예외 처리 (결정론)

| 상황 | 처리 |
|---|---|
| 키 미등록 | `setup_guide` 출력 + 종료 (LLM 재구성 금지) |
| 키 무효 (ping 실패) | `validate_api_keys` → `ok:false` + 사용자에게 재발급 안내 |
| HTTP 비-200 | `{"ok":false, "status":N, "raw":body}` 반환 — LLM이 *없는 결과를 만들어내지 말 것* |
| 형식 검증 실패 (SOC·Holland·학과명) | 함수가 `{"ok":false, "reason":...}` 반환. 사용자에게 형식 안내. |
| 한↔영 매핑 사전 부재 | `major_to_onet` fail — 사용자에게 사전 부재 보고. LLM 임의 번역 금지. |
| 네트워크 타임아웃 | `_http_get` 20초 타임아웃 후 `status:-1` + 예외명 반환 |
| 캐시 손상 | `_cache_get`이 None 반환 → 실시간 호출로 자동 폴백 |

---

## 9. 종료 조건

- 사용자 명시적 종료
- 데이터 조회·매핑·인터뷰 자료 제공 완료
- API 키 미등록으로 진입 가드 실패 시 안내 후 종료
