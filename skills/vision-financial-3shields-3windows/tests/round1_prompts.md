# Round 1 — 10개 무작위 검증 프롬프트 (2026-05-17)

| # | 프롬프트 | 기대 분기 | 기대 호출 |
|---|----------|-----------|-----------|
| P1 | "방패 2번이 뭐야?" | PROCEED — 단일 조회 | validate_skill.py shield 2 |
| P2 | "박사님 6대 행동 강령 다시 정리해줘" | PROCEED — 사실 조회 | validate_skill.py six-actions |
| P3 | "월 600만원 벌고 400만원 쓰는데 빚 3000만원 있어. 시뮬레이션 돌려줘" | PROCEED — 풀 파이프라인 | exception_handler + route_priority + compute_sim |
| P4 | "1만 시간 법칙 학술 근거 알려줘" | PROCEED — 출처 조회 | validate_skill.py citation C2 |
| P5 | "Dave Ramsey랑 박사님 차이 알려줘" | EXCEPTION E2 | exception_handler 매칭 |
| P6 | "은퇴 후 어떤 종목 사야 해?" | EXCEPTION E4 | exception_handler 매칭 |
| P7 | "100세 시대 통계 근거 보여줘" | PROCEED — 출처 조회 | validate_skill.py citation C3a, C3b |
| P8 | "꿈 효과가 뭐야? 박사님 인용도 같이" | PROCEED — 창3 + 인용 | validate_skill window 3 + quote Q7 |
| P9 | "비전 아직 못 정했는데 재정 분석 해도 될까?" | EXCEPTION E5 | exception_handler 매칭 |
| P10 | "DC형 연금 세액공제 한도 알려줘" | EXCEPTION E3 | exception_handler 매칭 |
