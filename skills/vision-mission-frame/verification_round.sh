#!/bin/bash
# 최종 검증 10개 프롬프트 — 이전 회차와 *완전히 다른* 입력으로 결정론 라이브러리 작동 확인
# 각 프롬프트마다 0단계 결정론 작업(classify_input + honorific + detect_religion)을 호출하고,
# 본 작업 단계의 결과(three_realm·diagnose_loop·report_skeleton·verify_quote·detect_drift)를 검증.

set -e
PYTHON="python3 mission_frame_lib.py"
PASS=0
FAIL=0
TOTAL=0

run_test() {
    local label="$1"
    local cmd="$2"
    local expected_substring="$3"
    TOTAL=$((TOTAL+1))
    out=$(eval "$cmd" 2>&1)
    if echo "$out" | grep -q "$expected_substring"; then
        PASS=$((PASS+1))
        echo "PASS [$label]"
    else
        FAIL=$((FAIL+1))
        echo "FAIL [$label]"
        echo "  Expected substring: $expected_substring"
        echo "  Actual: $out"
    fi
}

echo "=== 최종 검증 라운드 — 10개 프롬프트 ==="

# 프롬프트 1 — 일반 회사원, 풀 점검 (A유형)
run_test "P1 풀 점검 분류" \
    "$PYTHON classify_input --text '비전 프레임 점검해주세요. 저는 일반 회사원입니다.'" \
    '"input_type": "A"'

# 프롬프트 2 — 박사님 본인 미래학자 영역 (D유형)
run_test "P2 D유형 분류" \
    "$PYTHON classify_input --text '박사님 본인 비전 점검 요청 — 미래학자 영역에서'" \
    '"input_type": "D"'

# 프롬프트 3 — 강화 피드백 루프만 (C유형)
run_test "P3 C유형 분류" \
    "$PYTHON classify_input --text '강화 피드백 루프만 진단해줘'" \
    '"input_type": "C"'

# 프롬프트 4 — 영적 직관력만 (B-spiritual)
run_test "P4 B-spiritual 분류" \
    "$PYTHON classify_input --text '영적 직관력만 봐줘 — 영감과 정신적 가치'" \
    '"input_type": "B-spiritual"'

# 프롬프트 5 — 이성적 판단력만 (B-rational)
run_test "P5 B-rational 분류" \
    "$PYTHON classify_input --text '이성적 판단력만 — 정보와 예측 구성'" \
    '"input_type": "B-rational"'

# 프롬프트 6 — 이름 호칭 결정
run_test "P6 이름 호칭" \
    "$PYTHON honorific --name 김도현" \
    "김도현님"

# 프롬프트 7 — 종교 컨텍스트 (교회 청년부 → religious)
run_test "P7 종교 컨텍스트" \
    "$PYTHON detect_religion --text '교회 청년부원입니다. 비전이 자라지 않는 것 같아요'" \
    '"religion_context": "religious"'

# 프롬프트 8 — 영적 직관력 약화 진단 (영감 부족)
run_test "P8 영적 약화 진단" \
    "$PYTHON diagnose_loop --spiritual weak --rational strong" \
    '"weak_axis_key": "spiritual"'

# 프롬프트 9 — 이성적 판단력 약화 진단 (미래 예측 부족)
run_test "P9 이성적 약화 진단" \
    "$PYTHON diagnose_loop --spiritual strong --rational weak" \
    '"weak_axis_key": "rational"'

# 프롬프트 10 — 비전 정의 매핑 ("가치 있는")
run_test "P10 정의 매핑" \
    "$PYTHON map_definition --phrase '가치 있는'" \
    '"axis": "영적 직관력'

# 추가 검증: 박사님 책 인용 검증 (할루시네이션 차단)
run_test "BONUS-1 허용 인용 PASS" \
    "$PYTHON verify_quote --text '외부로부터 주어지는 영감'" \
    '"match": true'

run_test "BONUS-2 비허용 인용 차단" \
    "$PYTHON verify_quote --text '박사님께서 비전이란 자기 발견이라고 하셨다'" \
    '"match": false'

# 추가 검증: 박사님 정의 변형 검출
run_test "BONUS-3 변형 검출" \
    "$PYTHON detect_drift --text '비전 프레임의 두 축은 정신적 직관력과 감정적 판단력이다'" \
    '"clean": false'

# 추가 검증: 도식 외 이모지 검출
run_test "BONUS-4 이모지 차단" \
    "$PYTHON emoji_check --text '비전이 자라요 🎉'" \
    '"clean": false'

# 추가 검증: 3겹 점검 결과 분류 (정신적 가치만)
run_test "BONUS-5 3겹 분류 (왜곡)" \
    "$PYTHON three_realm --self false --others false --moral true" \
    '왜곡된 사명'

echo ""
echo "=== 결과: $PASS/$TOTAL PASS ==="
[ "$FAIL" -eq 0 ] && echo "ALL PASS" || echo "FAIL: $FAIL"
