# Sources — vision-personal-future-research

본 파일은 `data/sources.json`에 등재된 외부 학계·기관 출처의 *원문 검증 자국*이다. 결정론 환원 원칙에 따라 **이 파일에 등재되지 않은 외부 인용은 산출 금지**.

새 출처를 추가할 때는:
1. `data/sources.json`에 항목 추가 (id·claim·source·certainty·data_points)
2. 본 파일에 동일 id로 *원문 자국* 추가 (책 페이지·URL·발표일)
3. `python3 lib/research_engine.py` self-check 통과 확인
4. `python3 -m unittest tests/test_engine.py` 통과 확인

## 박사님 책 원문 인용 (1차 자료)

- **저자**: 최윤식 박사 (한국 미래학자, 아시아미래연구소 소장)
- **저서**: 『미래준비학교』, 아시아미래연구소, 2016
- 본 스킬은 박사님 책의 *미래지도·STEEPS 12영역(경제·사회·기술·산업·환경·법·정치·제도·글로벌패권·문화·종교·영성)·작업 ①~④·콜럼버스 비유*를 직접 인용한다. 인용은 SKILL.md '박사님 책 핵심 인용' 절 그대로 사용한다.

## 학계·기관 출처 등재 목록 (id 기준)

각 항목은 `eng.get_source(domain, horizon, id)` 호출로 인출한다.

### Society
- `kr_singleperson_household` — 통계청 「장래가구추계(2020~2050)」 2022년 6월 발표. KOSIS 보도자료.
- `kr_tfr` — 통계청 인구동향조사 (2023년 합계출산율 0.72 잠정). OECD Society at a Glance 연간 보고서.
- `kr_multicultural` — 통계청 인구주택총조사·다문화인구동태통계 추이.
- `generations_theory` — Strauss & Howe (1991) *Generations: The History of America's Future, 1584 to 2069*, William Morrow. Mark McCrindle (2014~) *Generation Alpha* 명명.
- `kr_population_cliff` — 통계청 「장래인구추계(2020~2070)」 2022년 12월 발표 (중위 시나리오).
- `ai_education_transition` — OECD *Digital Education Outlook 2023*; UNESCO *AI and Education: Guidance for Policy-makers* (2021).
- `kr_aging_2050` — 통계청 「장래인구추계(2020~2070)」 2022년 12월 발표 (중위 시나리오 — 2050년 65세 이상 약 40%대).
- `low_fertility_norm` — UN DESA *World Population Prospects 2024*.

### Technology
- `genai_industry` — McKinsey *The state of AI in 2024* (연간 보고서). 최신판 확인 권장.
- `av_level4` — SAE International *SAE J3016 Taxonomy and Definitions for Terms Related to Driving Automation Systems for On-Road Motor Vehicles* (2014 초판, 후속 개정 J3016_202104 등).
- `quantum_computing` — IBM Quantum Roadmap (Condor 1,121 qubits 2023 발표); Google Quantum AI Willow 발표(2024).
- `agi_timing` — Grace, Stewart, Sandkühler, Thomas, Weinstein-Raun, Brauner (2024). *Thousands of AI authors on the future of AI*. arXiv:2401.02843. (2,778명 AI 연구자 설문 — High-Level Machine Intelligence 50% 도달 중앙값 2047년)
- `humanoid_robot` — Tesla Optimus 시연 (2022~), Figure AI Figure 01 (2024 발표), 레인보우로보틱스 휴머노이드 시연. IDC·MarketsandMarkets 시장 보고서.
- `bci` — Neuralink 1차 인간 임상 (PRIME Study, 첫 환자 N1 임플란트 2024년 1월 발표).
- `asi_debate` — Nick Bostrom (2014) *Superintelligence: Paths, Dangers, Strategies*, Oxford University Press. Geoffrey Hinton 2023년 5월 Google 사임 발언 (NYT 인터뷰). Yann LeCun 회의론 (다수 발언/논문).
- `lev` — Aubrey de Grey, Michael Rae (2007) *Ending Aging: The Rejuvenation Breakthroughs That Could Reverse Human Aging in Our Lifetime*, St. Martin's Press.

### Economy
- `inflation_highrate` — IMF *World Economic Outlook* (2024 April, October 판본).
- `platform_capitalism` — Apple, Microsoft, Alphabet, Amazon, Meta 시가총액 (Bloomberg·Yahoo Finance 데이터).
- `cbdc` — Bank for International Settlements *2023 BIS survey on central bank digital currencies and crypto* (130개국 검토 보고).
- `ai_labor` — IMF Staff Discussion Note (2024) *Gen-AI: Artificial Intelligence and the Future of Work*. (선진국 일자리 60% 영향 추정)
- `ubi_pilots` — OECD Reports on UBI pilots; Finland Basic Income Experiment 2017~2018 결과; Stockton SEED 2019~2021 결과.
- `esg_disclosure` — EU CSRD (Corporate Sustainability Reporting Directive, 2024년 1월 시행); US SEC Climate Disclosure Rules (2024년 3월 채택).
- `defi_universal` — 학계·산업계 의견 갈림 (참고: FSB *Crypto-asset Regulation Recommendations* 2023).
- `polarization_vs_abundance` — Thomas Piketty (2014) *Capital in the Twenty-First Century*, Harvard University Press.

### Environment
- `extreme_weather` — IPCC AR6 Working Group I *Climate Change 2021: The Physical Science Basis* (2021); WG II (2022); WG III (2022); Synthesis Report (2023).
- `sea_level` — IPCC AR6 WG I Ch.9 (Ocean, Cryosphere and Sea Level Change). 2050년 0.15~0.29 m 추정 (SSP1-2.6 ~ SSP5-8.5).
- `food_price` — FAO Food Price Index (월간 발표, 1990 기준).
- `climate_refugees` — World Bank (2021) *Groundswell Part 2: Acting on Internal Climate Migration*. (2050년 최대 2.16억 명 추정)
- `renewable_share` — IEA *World Energy Outlook 2024*.
- `fusion_iter` — ITER Organization Public Communication (D-T 실험 일정 2035년 전후 공식 발표).
- `water_scarcity` — UN-Water/UNESCO *World Water Development Report 2024: Water for Prosperity and Peace*.
- `climate_threshold_15` — IPCC AR6 Synthesis Report (2023) — 현 추세 시 1.5°C는 2030년대 초중반 도달 가능성.
- `geoengineering` — National Academies of Sciences (2021) *Reflecting Sunlight: Recommendations for Solar Geoengineering Research and Research Governance*.
- `space_migration` — SpaceX Starship 개발(2020~); 학계 주류는 거주 가능 우주 이주 시점 미확정.

### Politics
- `us_china_hegemony` — CSIS (Center for Strategic and International Studies) China Power Project; Brookings China Reports.
- `korea_peninsula` — 전문가 의견 갈림 — KIDA·세종연구소·통일연구원 다수 보고서.
- `eu_political_fracture` — European Parliament 2024 Election Results (2024년 6월).
- `digital_rights_law` — EU Artificial Intelligence Act (Regulation (EU) 2024/1689); EU GDPR (2018); EU Digital Services Act (DSA, 2022).
- `aging_politics` — 통계청 인구추계 + 중앙선거관리위원회 선거인 통계.
- `ai_governance` — UN AI Advisory Body Final Report (2024); OECD AI Principles (2019, 2024 update).
- `multipolar_order` — Foreign Affairs 다수 분석 (대표: Hill·Stent·Mearsheimer 등).
- `new_international_order` — 시나리오 분기 — 학계 합의 없음 (Mearsheimer *The Great Delusion* 2018 등).
- `ai_robot_rights` — Luciano Floridi *The Ethics of Information* (2013); Nick Bostrom *Superintelligence* (2014); Mark Coeckelbergh *AI Ethics* (2020).

### Spirituality
- `kr_church_decline` — 한국갤럽 「한국인의 종교 1984-2021」 (2021년 보고서, gallup.co.kr). 목회데이터연구소 「한국교회 추적조사 (Numbers)」 정기 보고서.
- `new_spirituality` — Pew Research Center *Religion in America* 시리즈 (pewresearch.org/religion).
- `meaning_seeking` — Viktor Frankl (1946) *...trotzdem Ja zum Leben sagen* / 영역본 *Man's Search for Meaning* (1959). Mihaly Csikszentmihalyi (1990) *Flow: The Psychology of Optimal Experience*, Harper & Row.
- `ai_human_meaning` — Yuval N. Harari (2017) *Homo Deus: A Brief History of Tomorrow*, Harper; Nick Bostrom (2014) *Superintelligence*, Oxford; 신학계 응답 *AI and Theology* 다수.
- `global_religion_shift` — Pew Research Center (2015) *The Future of World Religions: Population Growth Projections, 2010-2050*.
- `secularization_debate` — Peter L. Berger (1967) *The Sacred Canopy*, Doubleday; Steve Bruce (2002) *God is Dead: Secularization in the West*, Blackwell; Peter L. Berger ed. (1999) *The Desecularization of the World*, Eerdmans; Jürgen Habermas (2008) *Notes on a Post-Secular Society* in *New Perspectives Quarterly*.
- `digital_consciousness` — Giulio Tononi *Integrated Information Theory* (PLoS Comp Biol 2008); Stanislas Dehaene *Consciousness and the Brain* (2014), Viking.

### Wildcards
- `pandemic` — WHO; Johns Hopkins CSSE; Bill Gates (2015) TED talk "The next outbreak? We're not ready"; Anthony Fauci 학계 우려.
- `earthquake` — KIGAM(한국지질자원연구원) 활성단층 조사 보고서; USGS Cascadia 시나리오; 일본 지진조사연구추진본부 난카이 트로프 평가.
- `war_terror` — Stockholm International Peace Research Institute (SIPRI) *SIPRI Yearbook* 군비 데이터; CSIS 분석.
- `financial_crisis` — IMF *Global Financial Stability Report* (반기 발표).
- `ai_alignment_failure` — Nick Bostrom (2014) *Superintelligence*; Stuart Russell (2019) *Human Compatible: Artificial Intelligence and the Problem of Control*, Viking; OpenAI·Anthropic·DeepMind alignment 연구 published papers.
- `emp_cyber` — US EMP Commission Reports (2004, 2008, 2017 update).
- `spiritual_revival` — 평양 대부흥(1907) — Kim Inseo, William Newton Blair 회고록 등; 웨일스 부흥(1904) — Evan Roberts 운동.
- `tech_breakthrough` — Bostrom (2014); 핵융합·양자 RSA 등 low probability high impact 시나리오.

## 방법론 매핑 출처 (Claude 휴리스틱 응용)

다음은 박사님 책 직접 수록이 아닌 *Claude 휴리스틱* — 학계 표준 분류를 박사님 STEEPS와 *논리적 연관*으로 매핑.

- **Howard Gardner 다중지능**: Gardner (1983) *Frames of Mind: The Theory of Multiple Intelligences*, Basic Books; Gardner (1999) *Intelligence Reframed: Multiple Intelligences for the 21st Century*, Basic Books (Naturalist 추가, Existential 잠정 제시).
- **RIASEC**: John L. Holland (1985) *Making Vocational Choices: A Theory of Vocational Personalities and Work Environments*, Prentice-Hall.
- **MBTI**: Isabel Briggs Myers, Mary H. McCaulley (1985) *Manual: A Guide to the Development and Use of the Myers-Briggs Type Indicator*, Consulting Psychologists Press. (학계는 신뢰성 의문 — 본 스킬은 사용자 입력 결과를 *전제*로만 사용)
- **Enneagram**: Don Riso, Russ Hudson (1996) *Personality Types: Using the Enneagram for Self-Discovery*, Houghton Mifflin (학계 합의 도구 아님 — 사용자 입력 전제).

## 검증·갱신 절차

- 본 파일·`data/sources.json` 갱신 시 `python3 lib/research_engine.py`(self-check) 및 `python3 -m unittest tests/test_engine.py` 모두 통과 필수.
- 카탈로그 통계(한국 인구·기후·기술 일정)는 *작성 시점 기준*이며, 인용 사용 전 *최신 자료 확인 권장*. 본 스킬 산출물 헤더에 *"자료 갱신 권장"* 명시 (SKILL.md 절대 원칙 10).
