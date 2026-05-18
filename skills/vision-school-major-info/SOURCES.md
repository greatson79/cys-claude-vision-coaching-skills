# vision-school-major-info — 출처 1:1 대조

본 문서는 SKILL.md·school_major_lib.py에서 인용·호출하는 모든 외부 출처를 명시한다. 박사님 명령: "출처 없는 판정은 자동 FAIL."

---

## A. 한국 — 공공데이터포털 (data.go.kr)

박사님 키 1개로 호출 가능한 7개 데이터셋.

### A-01. 교육부_커리어넷 대학학과정보 (15057878)
- URL: <https://www.data.go.kr/data/15057878/openapi.do>
- 제공기관: 교육부 · 한국직업능력연구원
- 라이선스: 공공누리 제1유형 (출처 표시)
- 호출: `school_major_lib.py kr_search_major`

### A-02. 교육부_커리어넷 학교정보 (15058917)
- URL: <https://www.data.go.kr/data/15058917/openapi.do>
- 호출: `school_major_lib.py kr_search_university`

### A-03. 교육부_커리어넷 직업정보 (15056641)
- URL: <https://www.data.go.kr/data/15056641/openapi.do>
- 호출: `school_major_lib.py kr_career_search`

### A-04. 교육부_커리어넷 진로자료 (15057135)
- URL: <https://www.data.go.kr/data/15057135/openapi.do>

### A-05. 한국대학교육협의회_대학별 학과정보 (15116892)
- URL: <https://www.data.go.kr/data/15116892/openapi.do>
- 제공기관: 한국대학교육협의회 (KCUE)
- 자동승인 · 일 10,000건 · 실시간 갱신 · 무료

### A-06. 한국대학교육협의회_대학알리미 대학 기본 정보 (15037507)
- URL: <https://www.data.go.kr/data/15037507/openapi.do>
- 데이터 원본: 대학알리미 (academyinfo.go.kr)

### A-07. 한국대학교육협의회_대학 및 전문대학정보 (15116816)
- URL: <https://www.data.go.kr/data/15116816/openapi.do>

### 한국 attribution 표준
`attribution_text()`가 자동 생성:
> 출처: 공공데이터포털 (data.go.kr) — 교육부 커리어넷 + 한국대학교육협의회(KCUE) 대학알리미.

---

## B. 미국 — O*NET Web Services

### B-01. O*NET Web Services v2.0
- URL: <https://services.onetcenter.org/>
- API 사인업: <https://services.onetcenter.org/developer/signup>
- API Reference: <https://services.onetcenter.org/reference/>
- 운영기관: U.S. Department of Labor, Employment and Training Administration
- 데이터 통계 (2026-02):
  - **923개 ONET data-level 직업** / 1,016개 SOC 코드
  - **277개 descriptors** (Knowledge·Skills·Abilities·Work Activities·Tasks·Work Styles·Interests 등)
  - **19,000+ task statements** · 2,000 detailed work activities · 325 intermediate · 41 generalized
  - **분기별 갱신** — 2026-02에 886 직업 업데이트, 다음 2026-05 예정
- 라이선스: **CC BY 4.0** (Creative Commons Attribution 4.0 International)
- 호출 방식: REST + HTTPS, Basic Auth (username:password)
- 무료

### B-02. ONET-SOC 분류 체계
- URL: <https://www.onetcenter.org/taxonomy.html>
- 형식: NN-NNNN.NN (예: 15-1252.00 = Software Developers)

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

### C-02. ONET Interest Profiler
- URL: <https://www.onetcenter.org/IP.html>
- ONET가 채택한 Holland 6 영역 직업 분류 — 학계 표준.
- 박사님 `vision-strong-visioncoding`(RIASEC) ↔ ONET 직접 매핑.

`HOLLAND_ONET_KEYWORDS` 매핑 사전(school_major_lib.py 내장) — 각 Holland 코드별 ONET 검색 키워드 6개씩 (R/I/A/S/E/C 각 5~6 키워드 = 35개).

---

## D. 한↔영 학과명 매핑 사전 (시드)

`KO_EN_MAJOR_DICT` (school_major_lib.py 내장)
- 54개 한국 학과명 ↔ 영문 학과명
- 기준: 한국교육개발원 학과분류 + ONET Career One Stop 일반 명칭
- 박사님이 추가 항목 등록할 때는 school_major_lib.py에 직접 추가

---

## E. 인용 사용 규칙

1. 모든 한국 데이터 출력은 `attribution_text()` 반환을 응답에 포함.
2. 모든 ONET 데이터 출력은 `onet_attribution_text()` 반환을 응답에 포함 (CC-BY 4.0 의무).
3. 임의 출처(공식 명시 없는 데이터)를 만들어내는 것 금지 — 박사님 vision 시리즈 할루시네이션 차단 패턴.
4. 인용 검증: `validate_attribution_present(text)` 호출로 출력 텍스트에 attribution 누락 검출.
5. 신규 API 또는 데이터 소스 추가 시 본 문서 § A~D 중 해당 위치에 명시 추가 필수.
