#!/bin/bash
# vision-school-major-info — 검증 라운드 (네트워크·API 키 없이도 작동하는 결정론 검증).

set -e
cd "$(dirname "$0")"
PY="python3 school_major_lib.py"
PASS=0
FAIL=0
TOTAL=0

check() {
    local label="$1"
    local cmd="$2"
    local expect_sub="$3"
    TOTAL=$((TOTAL+1))
    out=$(eval "$cmd" 2>&1)
    if echo "$out" | grep -q "$expect_sub"; then
        PASS=$((PASS+1))
        echo "PASS [$label]"
    else
        FAIL=$((FAIL+1))
        echo "FAIL [$label]"
        echo "  expect: $expect_sub"
        echo "  actual: $(echo "$out" | head -3)"
    fi
}

echo "=== vision-school-major-info 검증 라운드 ==="
echo

# 1. 진입 가드 자동 안내
check "S1 미등록 → setup_guide 출력" \
    "$PY check_api_keys" \
    '공공데이터포털'

check "S2 미등록 → ok:false" \
    "$PY check_api_keys" \
    '"ok": false'

# 2. attribution 자동 생성 (할루시네이션 차단 패턴)
check "S3 kr attribution data.go.kr" \
    "$PY attribution_text" \
    'data.go.kr'

check "S4 kr attribution 7 datasets" \
    "$PY attribution_text" \
    '15116892'

check "S5 onet attribution O*NET" \
    "$PY onet_attribution_text" \
    'O\*NET'

check "S6 onet attribution CC BY 4.0" \
    "$PY onet_attribution_text" \
    'CC BY 4.0'

check "S7 onet attribution USDOL" \
    "$PY onet_attribution_text" \
    'U.S. Department of Labor'

# 3. endpoint sync 검증
check "S8 7개 endpoint 등록 확인" \
    "$PY validate_api_endpoints_sync" \
    '"actual_kr": 7'

check "S9 endpoint sync ok" \
    "$PY validate_api_endpoints_sync" \
    '"ok": true'

# 4. Holland → ONET 매핑 (학계 표준)
for code in R I A S E C; do
    check "S10-$code Holland $code 매핑" \
        "$PY holland_to_onet --code $code" \
        '"holland_code": "'"$code"'"'
done

# 5. 한↔영 학과명 매핑
check "S11 컴퓨터공학 → Computer Science" \
    "$PY ko_en_major_dict --ko 컴퓨터공학" \
    '"en": "Computer Science"'

check "S12 신학 → Theology" \
    "$PY ko_en_major_dict --ko 신학" \
    '"en": "Theology"'

check "S13 의학 → Medicine" \
    "$PY ko_en_major_dict --ko 의학" \
    '"en": "Medicine"'

check "S14 전체 사전 50개 이상" \
    "$PY ko_en_major_dict" \
    '"count":'

# 6. 잘못된 입력 차단
check "S15 잘못된 Holland 차단" \
    "$PY holland_to_onet --code Z" \
    '"ok": false'

check "S16 잘못된 SOC 형식 차단" \
    "$PY onet_occupation_detail --soc-code invalid" \
    '"ok": false'

check "S17 attribution 검증 — 출처 있음" \
    "$PY validate_attribution_present --text 'O*NET OnLine 출처'" \
    '"ok": true'

check "S18 attribution 검증 — 출처 없음" \
    "$PY validate_attribution_present --text '그냥 텍스트'" \
    '"ok": false'

# 7. 단위 테스트 통합
echo
echo "--- 단위 테스트 통합 ---"
unit_out=$(python3 school_major_lib_test.py 2>&1 | tail -3)
if echo "$unit_out" | grep -q "ALL PASS"; then
    PASS=$((PASS+1))
    TOTAL=$((TOTAL+1))
    echo "PASS [단위 테스트 ALL PASS]"
else
    FAIL=$((FAIL+1))
    TOTAL=$((TOTAL+1))
    echo "FAIL [단위 테스트]"
    echo "$unit_out"
fi

echo
echo "============================================================"
echo "vision-school-major-info 검증 결과: $PASS/$TOTAL PASS"
echo "============================================================"
if [ "$FAIL" -eq 0 ]; then
    echo "ALL PASS"
    exit 0
else
    echo "FAIL: $FAIL"
    exit 1
fi
