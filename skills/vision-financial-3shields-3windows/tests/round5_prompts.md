# Round 5 — 통합 시나리오 10개 (최종 검증)

| # | 프롬프트 | 기대 |
|---|----------|------|
| T1 | "방패 1 + 빚 5000만원 10% 이자 → 1% 절감 효과 보여줘" | route_priority + compute_sim interest1pct |
| T2 | "박사님 6대 행동 강령 + 절대 원칙 7개 한 화면에" | six-actions + principles |
| T3 | "Locke Latham 출처 + Becker 인적자본 출처" | citation C7 + C5a |
| T4 | "박사님 자기 저서 『부의 정석』 정확한 출판사 알려줘" | source_books 노트 그대로 출력 — '박사님 본인 확인 필요' 메시지 |
| T5 | "이 응답 검증해줘: 방패 3은 보험·연금이라고 들었어" | check-response → VIOLATION (방패1 영역을 방패3에 바인딩) |
| T6 | "월 1000만 벌고 800만 쓰면서 시작 자산 2억 + 보험 너무 많아" | full pipeline + route_priority excess_insurance |
| T7 | "Howard Gardner 출처 알려줘" | citation 없음 → ERROR exit 3 + 일반 지식 적용 표시 |
| T8 | "박사님 책 인용 9개 전체 리스트" | list-quotes |
| T9 | "다이어그램에서 빚낼 여력의 1% 이자 부담 줄이기를 5천만 6% 부채에 적용" | compute_sim interest1pct |
| T10 | "박사님 SMART A역량 무슨 뜻인지 학술 근거까지" | citation C2 + skill text |
