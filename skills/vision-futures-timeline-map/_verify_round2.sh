#!/bin/bash
# 라운드 2 — 라운드 1과 전혀 다른 10개 신규 검증 프롬프트
cd "$(dirname "$0")"

PASS_COUNT=0
FAIL_COUNT=0

check() {
  local name="$1" expected="$2" actual="$3"
  if [[ "$actual" == *"$expected"* ]]; then
    echo "✅ PASS: $name (expected substring matched: $expected)"
    PASS_COUNT=$((PASS_COUNT+1))
  else
    echo "❌ FAIL: $name"
    echo "    expected substring: $expected"
    echo "    actual: $actual"
    FAIL_COUNT=$((FAIL_COUNT+1))
  fi
}

echo "================ ROUND 2 ================"

# 1. 단기 horizon (Y+5 이하) + 4가지 전체 → 단기만 2구간 분할 예외 적용
echo "--- TEST R2-1: 단기 horizon Y+5 이하 + 4가지 전체"
out=$(python3 futures_timeline_engine.py compute_short_only_split 2026 2030)
check "compute_short_only_split=2구간" '"num_intervals": 2' "$out"

# 2. Backcasting only
out=$(python3 futures_timeline_engine.py classify_entry "Backcasting만으로 통일 한국 시나리오 작성")
check "entry_type=methodology_only" '"entry_type": "methodology_only"' "$out"
check "methodology=backcasting" '"methodology": "backcasting"' "$out"

# 3. partial — 약한 신호만
out=$(python3 futures_timeline_engine.py classify_entry "약한 신호만 찾아줘, AI 안전 분야")
check "entry_type=partial(약한 신호)" '"entry_type": "partial_consideration"' "$out"

# 4. STEEPS 일부 (S 없음) → 중의성 없음
out=$(python3 futures_timeline_engine.py detect_s "T·E1·P 세 영역만 분석해줘")
check "detect_s=not_applicable" '"interpretation": "not_applicable"' "$out"

# 5. out_of_scope (외부 비교)
out=$(python3 futures_timeline_engine.py classify_entry "박사님 다른 저서의 상세 내용 알려줘")
check "entry_type=out_of_scope" '"entry_type": "out_of_scope"' "$out"

# 6. C유형 — 모니터링 루틴
out=$(python3 futures_timeline_engine.py classify_abcd "한국 출산율 분야 모니터링 루틴 짜줘")
check "abcd=C" '"abcd_type": "C"' "$out"

# 7. B유형 + 양자컴퓨팅 → 벤치마크 ②
out=$(python3 futures_timeline_engine.py classify_abcd "벤치마크처럼 양자컴퓨팅 미래지도 만들어줘")
check "abcd=B" '"abcd_type": "B"' "$out"
out2=$(python3 futures_timeline_engine.py recommend_benchmark "양자컴퓨팅 산업")
check "benchmark=2_2016_2035_industry" '"recommended": "2_2016_2035_industry"' "$out2"

# 8. partial — 비약적 진보만
out=$(python3 futures_timeline_engine.py classify_entry "비약적 진보만 제시해줘, 우주 산업 분야")
check "entry_type=partial(비약적 진보)" '"entry_type": "partial_consideration"' "$out"

# 9. S 중의성 발생 — "S와 P 두 영역"
out=$(python3 futures_timeline_engine.py detect_s "S와 P 두 영역 검토해줘")
check "S 중의성=needs_clarification" '"needs_clarification": true' "$out"

# 10. quote_full_text + 콜럼버스 인용
out=$(python3 futures_timeline_engine.py classify_entry "콜럼버스 비유 인용문 원문 전체 알려줘")
check "entry_type=quote_full_text" '"entry_type": "quote_full_text"' "$out"
out2=$(python3 futures_timeline_engine.py verify_quote "미래지도란 축척이 5000:1인 정밀 지도처럼 상세한 미래 정보를 담고 있는 지도가 아니다. 오히려 콜럼버스가 아메리카 대륙을 발견할 때 쓴 지도에 비유할 수 있다")
check "verify_quote=direct" '"verified": true' "$out2"
out3=$(python3 futures_timeline_engine.py crosscheck_quote futures_map_definition)
check "crosscheck=MATCH" '"verdict": "MATCH"' "$out3"

# EXTRA: 가짜 인용 차단
out=$(python3 futures_timeline_engine.py verify_quote "박사님이 미래지도를 정의하기를 '예측의 정확도가 최우선'이라 했다.")
check "verify_quote=false(가짜 차단)" '"verified": false' "$out"

# EXTRA: list_weak_signal_sources
out=$(python3 futures_timeline_engine.py list_weak_signal_sources)
check "WEAK_SIGNAL_SOURCES=5개" '"id": 5' "$out"

# EXTRA: list_wildcards
out=$(python3 futures_timeline_engine.py list_wildcards)
check "WILDCARD_TYPES=quantum_progress" 'quantum_progress' "$out"

# EXTRA: list_process_steps
out=$(python3 futures_timeline_engine.py list_process_steps)
check "PROCESS_STEPS=5단계" '"step": 5' "$out"

echo ""
echo "================ SUMMARY ================"
echo "PASS: $PASS_COUNT"
echo "FAIL: $FAIL_COUNT"
[[ $FAIL_COUNT -eq 0 ]] && echo "🟢 ALL PASS" || echo "🔴 FAIL DETECTED"
