#!/bin/bash
# vision-school-major-info — 검증 라운드 (네트워크·API 키 없이도 작동하는 결정론 검증).
# 검증은 *항상* 격리된 빈 키 디렉터리를 사용해 박사님 실 키 등록 여부와 무관하게 결정론적이어야 한다.

cd "$(dirname "$0")"
VISION_SMI_TMP="$(mktemp -d -t vision-smi-verify-XXXXXX)"
export VISION_SMI_CONFIG_DIR="$VISION_SMI_TMP"
export VISION_SMI_KEYS_PATH="$VISION_SMI_TMP/api_keys.json"
export VISION_SMI_CACHE_DIR="$VISION_SMI_TMP/cache"
trap 'rm -rf "$VISION_SMI_TMP"' EXIT

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

check "S3 mode=none 표시" \
    "$PY check_api_keys" \
    '"mode": "none"'

# 2. attribution 자동 생성
check "S4 kr attribution data.go.kr" \
    "$PY attribution_text" \
    'data.go.kr'

check "S5 kr attribution 7 datasets" \
    "$PY attribution_text" \
    '15116892'

check "S6 kr attribution 공공누리 라이선스" \
    "$PY attribution_text" \
    '공공누리'

check "S7 onet attribution O*NET" \
    "$PY onet_attribution_text" \
    'O\*NET'

check "S8 onet attribution CC BY 4.0" \
    "$PY onet_attribution_text" \
    'CC BY 4.0'

check "S9 onet attribution USDOL" \
    "$PY onet_attribution_text" \
    'U.S. Department of Labor'

# 3. endpoint sync
check "S10 7개 endpoint 등록" \
    "$PY validate_api_endpoints_sync" \
    '"actual_kr": 7'

check "S11 endpoint sync ok" \
    "$PY validate_api_endpoints_sync" \
    '"ok": true'

check "S12 missing IDs 비어있음" \
    "$PY validate_api_endpoints_sync" \
    '"missing_dataset_ids": \[\]'

check "S13 extra IDs 비어있음" \
    "$PY validate_api_endpoints_sync" \
    '"extra_dataset_ids": \[\]'

# 4. Holland → ONET 매핑 (6 코드)
for code in R I A S E C; do
    check "S14-$code Holland $code 매핑" \
        "$PY holland_to_onet --code $code" \
        '"holland_code": "'"$code"'"'
done

check "S15 Holland 한글 라벨 포함" \
    "$PY holland_to_onet --code R" \
    'holland_label_ko'

check "S16 Holland 잘못된 코드 차단" \
    "$PY holland_to_onet --code Z" \
    '"ok": false'

# 5. 한↔영 학과명 매핑 (확장 사전 — 70+)
check "S17 컴퓨터공학 → Computer Science" \
    "$PY ko_en_major_dict --ko 컴퓨터공학" \
    '"en": "Computer Science"'

check "S18 신학 → Theology" \
    "$PY ko_en_major_dict --ko 신학" \
    '"en": "Theology"'

check "S19 의학 → Medicine" \
    "$PY ko_en_major_dict --ko 의학" \
    '"en": "Medicine"'

check "S20 항공우주공학 → Aerospace Engineering" \
    "$PY ko_en_major_dict --ko 항공우주공학" \
    '"en": "Aerospace Engineering"'

check "S21 인공지능 → Artificial Intelligence" \
    "$PY ko_en_major_dict --ko 인공지능" \
    '"en": "Artificial Intelligence"'

check "S22 데이터사이언스 → Data Science" \
    "$PY ko_en_major_dict --ko 데이터사이언스" \
    '"en": "Data Science"'

check "S23 사이버보안 → Cybersecurity" \
    "$PY ko_en_major_dict --ko 사이버보안" \
    '"en": "Cybersecurity"'

check "S24 전체 사전 70+" \
    "$PY ko_en_major_dict" \
    '"count":'

# 6. SOC 코드 형식 검증
check "S25 잘못된 SOC 형식 차단" \
    "$PY onet_occupation_detail --soc-code invalid" \
    '"ok": false'

check "S26 짧은 SOC 차단" \
    "$PY onet_occupation_detail --soc-code 15-1252" \
    'must be in format'

# 7. attribution 검증
check "S27 attribution 검증 — 출처 있음" \
    "$PY validate_attribution_present --text 'O*NET OnLine 출처'" \
    '"ok": true'

check "S28 attribution 검증 — 출처 없음" \
    "$PY validate_attribution_present --text '그냥 텍스트'" \
    '"ok": false'

check "S29 attribution 검증 — kr 출처" \
    "$PY validate_attribution_present --text '출처: 공공데이터포털'" \
    '"has_kr_attribution": true'

# 8. ONET 키워드 검증
check "S30 onet search 빈 키워드 차단" \
    "$PY onet_search_occupation --keyword ''" \
    '"ok": false'

# 9. 신규 한국 API 함수 (키 없이 호출 시 차단)
check "S31 kr_major_detail 키 없으면 차단" \
    "$PY kr_major_detail --keyword 컴퓨터공학" \
    'not registered'

check "S32 kr_career_detail 키 없으면 차단" \
    "$PY kr_career_detail --keyword 개발자" \
    'not registered'

check "S33 kr_career_resources 키 없으면 차단" \
    "$PY kr_career_resources --keyword 진로" \
    'not registered'

check "S34 kr_majors_by_university 키 없으면 차단" \
    "$PY kr_majors_by_university --univ-name 서울대학교" \
    'not registered'

check "S35 kr_university_by_region region 필수" \
    "$PY kr_university_by_region --region ''" \
    'required'

# 10. cross_reference_major_career
check "S36 cross_reference 한↔영 매핑" \
    "$PY cross_reference_major_career --ko-major 컴퓨터공학" \
    '"en_major": "Computer Science"'

check "S37 cross_reference 빈 학과명 차단" \
    "$PY cross_reference_major_career --ko-major ''" \
    '"ok": false'

# 11. 캐시 함수
check "S38 refresh_korean_data_cache ok" \
    "$PY refresh_korean_data_cache" \
    '"ttl_sec": 86400'

check "S39 refresh_onet_cache ok" \
    "$PY refresh_onet_cache" \
    '"ttl_sec": 7776000'

# 12. setup_api_key 입력 검증
check "S40 setup 잘못된 name" \
    "$PY setup_api_key --name xxx --value y 2>&1" \
    "invalid choice"

# 13. major_to_onet
check "S41 major_to_onet 컴퓨터공학 매핑" \
    "$PY major_to_onet --ko-major 컴퓨터공학" \
    '"en_major": "Computer Science"'

check "S42 major_to_onet 없는 학과 fail" \
    "$PY major_to_onet --ko-major 외계전공zzz없는학과" \
    '"ok": false'

# 14. 단위 테스트 통합
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
