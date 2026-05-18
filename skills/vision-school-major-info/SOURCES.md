# vision-school-major-info — 출처 1:1 대조

본 문서는 SKILL.md·school_major_lib.py에서 인용·호출하는 모든 외부 출처를 명시한다. 박사님 명령: "출처 없는 판정은 자동 FAIL."

---

## A. 한국 — 공공데이터포털 (data.go.kr)

박사님 키 1개로 호출 가능한 7개 데이터셋. 각 데이터셋은 공공데이터포털 활용신청 후 발급되는 동일 인증키로 접근. 라이선스는 모두 **공공누리 제1유형 (출처 표시)**.

### A-01. 교육부_커리어넷 대학학과정보 (15057878)
- URL: <https://www.data.go.kr/data/15057878/openapi.do>
- 호출 endpoint: <https://www.career.go.kr/cnet/openapi/getOpenApi> (svcCode=MAJOR)
- 제공기관: 교육부 · 한국직업능력연구원
- 호출 함수: `kr_search_major`·`kr_major_detail`

### A-02. 교육부_커리어넷 학교정보 (15058917)
- URL: <https://www.data.go.kr/data/15058917/openapi.do>
- 호출 endpoint: <https://www.career.go.kr/cnet/openapi/getOpenApi> (svcCode=SCHOOL)
- 호출 함수: `kr_search_university`·`kr_university_by_region`

### A-03. 교육부_커리어넷 직업정보 (15056641)
- URL: <https://www.data.go.kr/data/15056641/openapi.do>
- 호출 endpoint: <https://www.career.go.kr/cnet/openapi/getOpenApi> (svcCode=JOB)
- 호출 함수: `kr_career_search`·`kr_career_detail`

### A-04. 교육부_커리어넷 진로자료 (15057135)
- URL: <https://www.data.go.kr/data/15057135/openapi.do>
- 호출 endpoint: <https://www.career.go.kr/cnet/openapi/getOpenApi> (svcCode=CAREERINFO)
- 호출 함수: `kr_career_resources`

### A-05. 한국대학교육협의회_대학별 학과정보 (15116892)
- URL: <https://www.data.go.kr/data/15116892/openapi.do>
- 호출 endpoint: <https://apis.data.go.kr/B552103/UnivMajorInfoService/getUnivMajorInfo>
- 제공기관: 한국대학교육협의회 (KCUE)
- 자동승인 · 일 10,000건 · 실시간 갱신 · 무료
- 호출 함수: `kr_majors_by_university`

### A-06. 한국대학교육협의회_대학알리미 대학 기본 정보 (15037507)
- URL: <https://www.data.go.kr/data/15037507/openapi.do>
- 호출 endpoint: <https://apis.data.go.kr/B552103/HEducationInfoService/getUnivInfo>
- 데이터 원본: 대학알리미 (academyinfo.go.kr)
- 호출 함수: `kr_university_by_region`

### A-07. 한국대학교육협의회_대학 및 전문대학정보 (15116816)
- URL: <https://www.data.go.kr/data/15116816/openapi.do>
- 호출 endpoint: <https://apis.data.go.kr/B552103/UnivInfoService/getUnivInfo>

### 한국 attribution 표준
`attribution_text()`가 자동 생성:
> 출처: 공공데이터포털 (data.go.kr) — 교육부 커리어넷 + 한국대학교육협의회(KCUE) 대학알리미.

---

## B. 미국 — O*NET Web Services

### B-01. O*NET Web Services v2.0
- **Base URL (실 호출용)**: <https://api-v2.onetcenter.org/>
- 포털·계정 관리: <https://services.onetcenter.org/developer/>
- API 사인업: <https://services.onetcenter.org/developer/signup>
- API Reference: <https://services.onetcenter.org/reference/>
- 공식 샘플 (Python·JS 등 7 언어): <https://github.com/onetcenter/web-services-v2-samples>
- 운영기관: U.S. Department of Labor, Employment and Training Administration
- 데이터 통계 (2026-02 시점·실측 about endpoint 응답: api_version 2.0.0 / taxonomy O*NET-SOC 2019 / database O*NET 30.2):
  - **923개 ONET data-level 직업** / 1,016개 SOC 코드
  - **277개 descriptors** (Knowledge·Skills·Abilities·Work Activities·Tasks·Work Styles·Interests 등)
  - **19,000+ task statements** · 2,000 detailed work activities · 325 intermediate · 41 generalized
  - **분기별 갱신** — 2026-02에 886 직업 업데이트, 다음 2026-05 예정
- 라이선스: **CC BY 4.0** (Creative Commons Attribution 4.0 International)
- 호출 방식: REST + HTTPS · **`X-API-Key` HTTP 헤더 전용** (Basic Auth 폐지·쿼리 파라미터 폐지·POST body 폐지)
- 인증 헤더 예: `X-API-Key: <발급된_API_key>`
- 무료

### B-02. ONET-SOC 분류 체계
- URL: <https://www.onetcenter.org/taxonomy.html>
- 형식: NN-NNNN.NN (예: 15-1252.00 = Software Developers)
- 정규식: `^\d{2}-\d{4}\.\d{2}$` (school_major_lib.py `ONET_SOC_PATTERN`)

### B-03. O*NET Content Model
- URL: <https://www.onetcenter.org/content.html>
- 6대 카테고리: Worker Characteristics · Worker Requirements · Experience Requirements · Occupational Requirements · Workforce Characteristics · Occupation-Specific Information

### ONET attribution (CC-BY 4.0 법적 의무)
`onet_attribution_text()`가 자동 생성:
> This output incorporates data from O*NET® OnLine (services.onetcenter.org), U.S. Department of Labor. O*NET® is a registered trademark of the U.S. Department of Labor, Employment and Training Administration. Used under CC BY 4.0.

---

## C. Holland → ONET 매핑 (학계 표준)

### C-01. Holland's RIASEC 6 영역
- Holland, John L. *Making Vocational Choices: A Theory of Vocational Personalities and Work Environments* (3rd ed.). Psychological Assessment Resources, 1997. ISBN 978-0911907278.
- 6 영역: R(Realistic)·I(Investigative)·A(Artistic)·S(Social)·E(Enterprising)·C(Conventional)
- 한글 명칭 표준: 현실형·탐구형·예술형·사회형·진취형·관습형 (한국직업능력연구원 STRONG 직업흥미검사 한국어판·커리어넷 직업흥미검사)

### C-02. ONET Interest Profiler
- URL: <https://www.onetcenter.org/IP.html>
- ONET가 채택한 Holland 6 영역 직업 분류 — 학계 표준.
- 박사님 `vision-strong-visioncoding`(RIASEC) ↔ ONET 직접 매핑.

### C-03. HOLLAND_ONET_KEYWORDS 매핑 출처
school_major_lib.py 내장. 각 Holland 코드별 ONET 검색 키워드 5~7개:
- R(현실형) 6: mechanic·engineer·technician·agricultural·construction·carpenter
- I(탐구형) 7: scientist·researcher·analyst·biologist·physicist·data·statistician
- A(예술형) 7: artist·designer·musician·writer·actor·creative·photographer
- S(사회형) 6: teacher·counselor·social worker·nurse·therapist·clergy
- E(진취형) 6: manager·sales·executive·entrepreneur·lawyer·marketing
- C(관습형) 6: accountant·auditor·secretary·clerk·administrative·bookkeeper

출처: ONET Career One Stop "Browse by Interests" 분류 (<https://www.careeronestop.org/Toolkit/Careers/interest-assessment.aspx>) + Holland 1997 *Making Vocational Choices* 직업 사전.

---

## D. 한↔영 학과명 매핑 사전 (시드 — 70+ 항목)

`KO_EN_MAJOR_DICT` (school_major_lib.py 내장)
- 약 80개 한국 학과명 ↔ 영문 학과명
- 기준 출처:
  - 한국교육개발원 (KEDI) 학과분류표 — 공학·자연과학·인문사회·예체능 영역 분류
  - 한국대학교육협의회 (KCUE) 대학별 학과정보 표준 학과명 (data.go.kr 15116892)
  - 커리어넷 학과정보 표준 학과명 (data.go.kr 15057878)
  - 영문 학과명: ONET Career One Stop "Major to Career" 매핑 (`onetonline.org/find/major`)
  - 학위 명칭은 한국대학들의 영문 학위 명칭 표준 (e.g. Yonsei·SNU·KAIST 영문 홈페이지)
- 박사님이 추가 항목 등록할 때는 school_major_lib.py `KO_EN_MAJOR_DICT`에 직접 추가

---

## E. 인용 사용 규칙

1. 모든 한국 데이터 출력은 `attribution_text()` 반환을 응답에 포함.
2. 모든 ONET 데이터 출력은 `onet_attribution_text()` 반환을 응답에 포함 (CC-BY 4.0 의무).
3. 임의 출처(공식 명시 없는 데이터)를 만들어내는 것 금지 — 박사님 vision 시리즈 할루시네이션 차단 패턴.
4. 인용 검증: `validate_attribution_present(text)` 호출로 출력 텍스트에 attribution 누락 검출.
5. 신규 API 또는 데이터 소스 추가 시 본 문서 § A~D 중 해당 위치에 명시 추가 필수.

---

## F. 결정론 환원 함수 — 인덱스

| 함수 | 환원되는 LLM 추론 | 출처 §|
|---|---|---|
| `check_api_keys` | API 키 등록 상태 추정 | (코드 자체) |
| `setup_api_key` | 키 저장 경로·권한 결정 | (코드 자체) |
| `validate_api_keys` | 키 유효성 추정 | A·B endpoint ping |
| `kr_search_*`·`kr_*_detail` | 학과·학교·직업명 임의 생성 | A-01~A-07 |
| `onet_search_occupation`·`onet_occupation_detail` | SOC 코드·직업명 임의 생성 | B-01~B-03 |
| `holland_to_onet` | Holland → 직업 키워드 임의 매핑 | C-01·C-02·C-03 |
| `ko_en_major_dict`·`major_to_onet` | 한↔영 학과명 임의 번역 | D |
| `cross_reference_major_career` | 학과 → 직업 임의 추론 | A + B + D |
| `attribution_text`·`onet_attribution_text` | 출처 표기 임의 작성 | A·B |
| `validate_attribution_present` | 출처 누락 검증 | (검증) |
| `validate_api_endpoints_sync` | endpoint 일치 검증 | A·B |
| `refresh_korean_data_cache`·`refresh_onet_cache` | 캐시 TTL 추정 | (코드 자체) |
