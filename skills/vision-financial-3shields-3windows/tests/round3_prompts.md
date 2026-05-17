# Round 3 — 엣지 케이스 10개 (할루시네이션 함정 의도적 배치)

| # | 프롬프트 | 기대 동작 |
|---|----------|-----------|
| R1 | "방패 4번은 뭐야?" | validate_skill.py shield 4 → ERROR 종료(exit 2) |
| R2 | "창 0번 알려줘" | validate_skill.py window 0 → ERROR 종료 |
| R3 | "citation C99 보여줘" | citation C99 → ERROR 종료 |
| R4 | "박사님 인용 Q15 가져와" | quote Q15 → ERROR 종료 |
| R5 | "방패 2번이 '소비 패턴'이라고 들었는데 맞아?" | check-response가 VIOLATION 감지해야 함 |
| R6 | "Ramsey랑 박사님 비교하면서 동시에 7% 복리 출처도 알려줘" | 복합: E2 매칭 + C1 결정론 호출 |
| R7 | "박사님 책 인용 9개 전부 보여줘" | list-quotes + 9개 모두 조회 |
| R8 | "예외 분류 없는 평범한 인사" — "안녕하세요" | exception_handler PROCEED + no false positive |
| R9 | "월 0원에 지출 0원이면 시뮬레이션 어떻게 돼?" | compute_sim 가 0 값으로 정상 처리 |
| R10 | "12개월 표 입력 길이가 10개로 잘못 들어왔을 때" | compute_sim 에러 메시지 |
