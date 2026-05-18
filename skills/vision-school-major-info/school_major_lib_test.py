"""
school_major_lib.py 단위 테스트.

실행: python3 school_major_lib_test.py

네트워크 호출(실제 API)은 제외 — 박사님 키 등록 후에만 작동. CI에서는 키 검증·매핑·attribution만 검증.
"""

from __future__ import annotations

import os
import sys
import json
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import school_major_lib as L  # noqa: E402

PASS = 0
FAIL = 0


def expect(label: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS [{label}]")
    else:
        FAIL += 1
        print(f"FAIL [{label}]  {detail[:300]}")


def _with_temp_config(test_fn):
    """일시적으로 KEYS_PATH·CONFIG_DIR·CACHE_DIR을 tmp로 가리키고 테스트 실행."""
    saved_dir = L.CONFIG_DIR
    saved_path = L.KEYS_PATH
    saved_cache = L.CACHE_DIR
    with tempfile.TemporaryDirectory() as tmp:
        L.CONFIG_DIR = tmp
        L.KEYS_PATH = os.path.join(tmp, "api_keys.json")
        L.CACHE_DIR = os.path.join(tmp, "cache")
        try:
            test_fn()
        finally:
            L.CONFIG_DIR = saved_dir
            L.KEYS_PATH = saved_path
            L.CACHE_DIR = saved_cache


# ---------------------------------------------------------------------------
# 1. check_api_keys + setup_api_key
# ---------------------------------------------------------------------------

def test_check_api_keys_empty():
    def fn():
        out = L.check_api_keys()
        expect("check 빈 상태 ok:false", not out["ok"])
        expect("check 빈 상태 mode=none", out["mode"] == "none")
        expect("check setup_guide 포함", "공공데이터포털" in out["setup_guide"])
        expect("check missing_required = [data_go_kr]", out["missing_required"] == ["data_go_kr"])
    _with_temp_config(fn)


def test_setup_api_key_basic():
    def fn():
        out = L.setup_api_key("data_go_kr", "TEST_KEY_KR")
        expect("setup data_go_kr ok", out["ok"])
        expect("setup 파일 권한 600", out["file_mode"] in ("0o600", "0o400"))

        out = L.setup_api_key("onet", "username:password")
        expect("setup onet ok", out["ok"])

        c = L.check_api_keys()
        expect("check 둘 다 등록 ok", c["ok"] and c["data_go_kr"] and c["onet"])
        expect("check mode=full", c["mode"] == "full")
    _with_temp_config(fn)


def test_setup_api_key_invalid():
    def fn():
        out = L.setup_api_key("invalid_name", "x")
        expect("setup 잘못된 name 차단", not out["ok"])
        out = L.setup_api_key("data_go_kr", "")
        expect("setup 빈 value 차단", not out["ok"])
        out = L.setup_api_key("data_go_kr", "   ")
        expect("setup 공백 only value 차단", not out["ok"])
        out = L.setup_api_key("data_go_kr", 123)  # type: ignore
        expect("setup 비-str value 차단", not out["ok"])
        out = L.setup_api_key(None, "x")  # type: ignore
        expect("setup None name 차단", not out["ok"])
    _with_temp_config(fn)


def test_check_api_keys_kr_only():
    def fn():
        L.setup_api_key("data_go_kr", "K")
        c = L.check_api_keys()
        expect("kr only mode", c["mode"] == "korean_only" and c["ok"])
    _with_temp_config(fn)


def test_check_api_keys_onet_only():
    def fn():
        L.setup_api_key("onet", "u:p")
        c = L.check_api_keys()
        expect("onet only — ok:false (data_go_kr 필수)", not c["ok"])
        expect("onet only — mode=onet_only", c["mode"] == "onet_only")
    _with_temp_config(fn)


# ---------------------------------------------------------------------------
# 2. validate_api_endpoints_sync
# ---------------------------------------------------------------------------

def test_validate_endpoints():
    out = L.validate_api_endpoints_sync()
    expect("endpoints 7개 등록", out["ok"] and out["actual_kr"] == 7)
    expect("ONET base url HTTPS api-v2", out["onet_base"].startswith("https://api-v2.onetcenter.org"))
    expect("missing IDs 비어있음", out["missing_dataset_ids"] == [])
    expect("extra IDs 비어있음", out["extra_dataset_ids"] == [])
    expect("invalid URLs 비어있음", out["invalid_urls"] == [])


# ---------------------------------------------------------------------------
# 3. holland_to_onet — 6 코드 모두
# ---------------------------------------------------------------------------

def test_holland_to_onet():
    for code in ("R", "I", "A", "S", "E", "C"):
        out = L.holland_to_onet(code)
        expect(f"holland {code} ok", out["ok"] and out["holland_code"] == code)
        expect(f"holland {code} 키워드 5개 이상", len(out["search_keywords"]) >= 5)
        expect(f"holland {code} 한글 라벨", "형" in out["holland_label_ko"])
        expect(f"holland {code} attribution 포함", "O*NET" in out["attribution"]["rendered"])

    expect("holland 잘못된 코드", not L.holland_to_onet("X")["ok"])
    expect("holland 소문자도 처리", L.holland_to_onet("r")["ok"])
    expect("holland 공백 처리", L.holland_to_onet(" I ")["ok"])
    expect("holland None", not L.holland_to_onet(None)["ok"])  # type: ignore
    expect("holland 숫자", not L.holland_to_onet(1)["ok"])  # type: ignore


# ---------------------------------------------------------------------------
# 4. ko_en_major_dict — 한↔영 매핑
# ---------------------------------------------------------------------------

def test_ko_en_major_dict():
    out = L.ko_en_major_dict("컴퓨터공학")
    expect("ko_en 컴퓨터공학 → Computer Science", out["ok"] and out["en"] == "Computer Science")

    out = L.ko_en_major_dict("신학")
    expect("ko_en 신학 → Theology", out["ok"] and out["en"] == "Theology")

    out = L.ko_en_major_dict("간호학")
    expect("ko_en 간호학 → Nursing", out["ok"] and out["en"] == "Nursing")

    out = L.ko_en_major_dict("항공우주공학")
    expect("ko_en 항공우주공학 → Aerospace Engineering", out["ok"] and out["en"] == "Aerospace Engineering")

    out = L.ko_en_major_dict("인공지능")
    expect("ko_en 인공지능 → AI", out["ok"] and out["en"] == "Artificial Intelligence")

    out = L.ko_en_major_dict("데이터사이언스")
    expect("ko_en 데이터사이언스 → Data Science", out["ok"] and out["en"] == "Data Science")

    # 전체 사전
    out = L.ko_en_major_dict()
    expect("ko_en 전체 사전 70+", out["ok"] and out["count"] >= 70)

    # 부분 매칭 (확장된 사전에서는 매칭이 있을 수 있음)
    out = L.ko_en_major_dict("외계전공zzz없는학과")
    expect("ko_en 완전 없는 학과", not out["ok"])


def test_major_to_onet():
    def fn():
        out = L.major_to_onet("컴퓨터공학")
        expect("major_to_onet ko→en 매핑 ok", out["ok"] and out["en_major"] == "Computer Science")
        expect("major_to_onet onet 미등록 안내", "key not registered" in str(out.get("onet_search", {})))

        bad = L.major_to_onet("외계전공zzz없는학과")
        expect("major_to_onet 없는 학과 fail", not bad["ok"])

        bad = L.major_to_onet("")
        expect("major_to_onet 빈 문자열 fail", not bad["ok"])

        bad = L.major_to_onet(None)  # type: ignore
        expect("major_to_onet None fail", not bad["ok"])
    _with_temp_config(fn)


# ---------------------------------------------------------------------------
# 5. attribution — 결정론 자동 생성
# ---------------------------------------------------------------------------

def test_attribution():
    a = L.attribution_text()
    expect("kr attribution data.go.kr 명시", "data.go.kr" in a["rendered"])
    expect("kr attribution 7개 데이터셋", len(a["datasets"]) == 7)
    expect("kr attribution 공공누리 명시", "공공누리" in a["license"])

    o = L.onet_attribution_text()
    expect("onet attribution O*NET 명시", "O*NET" in o["rendered"])
    expect("onet attribution CC BY 명시", "CC BY" in o["rendered"])
    expect("onet attribution USDOL 명시", "U.S. Department of Labor" in o["rendered"])
    expect("onet attribution license=CC BY 4.0", o["license"] == "CC BY 4.0")

    expect(
        "validate text with kr attr",
        L.validate_attribution_present("출처: data.go.kr ...")["ok"],
    )
    expect(
        "validate text with onet attr",
        L.validate_attribution_present("O*NET® OnLine ...")["ok"],
    )
    expect(
        "validate text without attr",
        not L.validate_attribution_present("그냥 텍스트")["ok"],
    )
    expect(
        "validate non-string",
        not L.validate_attribution_present(None)["ok"],  # type: ignore
    )


# ---------------------------------------------------------------------------
# 6. 키 없이 API 호출 시 안전 차단
# ---------------------------------------------------------------------------

def test_kr_api_blocked_without_key():
    def fn():
        out = L.kr_search_university("서울대")
        expect("kr_search_university 키 없으면 차단", not out["ok"])
        out = L.kr_search_major("컴퓨터")
        expect("kr_search_major 키 없으면 차단", not out["ok"])
        out = L.kr_career_search("개발자")
        expect("kr_career_search 키 없으면 차단", not out["ok"])
        out = L.kr_major_detail(keyword="컴퓨터공학")
        expect("kr_major_detail 키 없으면 차단", not out["ok"])
        out = L.kr_career_detail(keyword="개발자")
        expect("kr_career_detail 키 없으면 차단", not out["ok"])
        out = L.kr_career_resources(keyword="진로")
        expect("kr_career_resources 키 없으면 차단", not out["ok"])
        out = L.kr_majors_by_university(univ_name="서울대학교")
        expect("kr_majors_by_university 키 없으면 차단", not out["ok"])
    _with_temp_config(fn)


def test_kr_required_arg_validation():
    def fn():
        L.setup_api_key("data_go_kr", "K")
        # kr_major_detail: major_seq나 keyword 필수
        out = L.kr_major_detail()
        expect("kr_major_detail 인자 없으면 fail", not out["ok"])
        out = L.kr_career_detail()
        expect("kr_career_detail 인자 없으면 fail", not out["ok"])
        out = L.kr_university_by_region(region=None)
        expect("kr_university_by_region region 필수", not out["ok"])
        out = L.kr_university_by_region(region="")
        expect("kr_university_by_region 빈 region 차단", not out["ok"])
    _with_temp_config(fn)


def test_onet_input_validation():
    expect("onet soc 잘못된 형식", not L.onet_occupation_detail("invalid")["ok"])
    expect("onet soc None", not L.onet_occupation_detail(None)["ok"])  # type: ignore
    expect("onet soc 빈 문자열", not L.onet_occupation_detail("")["ok"])
    expect("onet soc 형식 우회 시도", not L.onet_occupation_detail("15-1252")["ok"])
    expect("onet soc 형식 우회 시도2", not L.onet_occupation_detail("aa-bbbb.cc")["ok"])
    # 올바른 형식 통과 (네트워크 호출은 실패하더라도 형식 검증은 통과)
    out = L.onet_occupation_detail("15-1252.00")
    expect("onet soc 정확한 형식 통과", "must be in format" not in out.get("reason", ""))

    expect("onet search 빈 키워드", not L.onet_search_occupation("")["ok"])
    expect("onet search None", not L.onet_search_occupation(None)["ok"])  # type: ignore


# ---------------------------------------------------------------------------
# 7. 캐시
# ---------------------------------------------------------------------------

def test_cache_refresh():
    def fn():
        # 캐시 디렉터리 존재 안 함 상태
        out = L.refresh_korean_data_cache()
        expect("kr cache refresh ok", out["ok"] and out["ttl_sec"] == L.KR_CACHE_TTL_SEC)
        out = L.refresh_onet_cache()
        expect("onet cache refresh ok", out["ok"] and out["ttl_sec"] == L.ONET_CACHE_TTL_SEC)

        # 캐시 항목 강제 생성 (old + new)
        L._cache_put("kr", "old_item", {"data": "old"})
        L._cache_put("kr", "new_item", {"data": "new"})
        # old_item을 25시간 전으로 mtime 조작
        old_path = L._cache_path("kr", "old_item")
        old_time = time.time() - (25 * 3600)
        os.utime(old_path, (old_time, old_time))

        out = L.refresh_korean_data_cache(prune=True)
        expect("kr cache prune — old 제거", any("old_item" in p for p in out["pruned"]))
        expect("kr cache prune — new 유지", any("new_item" in k for k in out["kept"]))
    _with_temp_config(fn)


def test_cache_read_write():
    def fn():
        L._cache_put("test", "key1", {"val": 42})
        out = L._cache_get("test", "key1", ttl_sec=3600)
        expect("cache read/write 일치", out is not None and out["val"] == 42)

        # TTL 만료
        old_path = L._cache_path("test", "key1")
        old_time = time.time() - 7200
        os.utime(old_path, (old_time, old_time))
        out = L._cache_get("test", "key1", ttl_sec=3600)
        expect("cache TTL 만료 시 None", out is None)

        # 없는 키
        out = L._cache_get("test", "nonexistent", ttl_sec=3600)
        expect("cache 없는 키 None", out is None)
    _with_temp_config(fn)


# ---------------------------------------------------------------------------
# 8. cross_reference_major_career
# ---------------------------------------------------------------------------

def test_cross_reference_basic():
    def fn():
        # 키 없는 상태에서도 ko_major + en_major 매핑은 작동
        out = L.cross_reference_major_career("컴퓨터공학")
        expect("xref 매핑 ok", out["ok"] and out["en_major"] == "Computer Science")
        expect("xref kr_major_info 미등록 안내", not out["kr_major_info"]["ok"])

        # 빈 입력
        out = L.cross_reference_major_career("")
        expect("xref 빈 학과명 fail", not out["ok"])
        out = L.cross_reference_major_career(None)  # type: ignore
        expect("xref None 학과명 fail", not out["ok"])
    _with_temp_config(fn)


# ---------------------------------------------------------------------------
# 9. SETUP_GUIDE 무결성
# ---------------------------------------------------------------------------

def test_setup_guide_content():
    g = L.SETUP_GUIDE
    expect("guide 공공데이터포털 명시", "공공데이터포털" in g)
    expect("guide ONET 명시", "ONET" in g)
    # 7개 데이터셋 ID 모두 포함
    for ds_id in ("15057878", "15058917", "15056641", "15057135", "15116892", "15037507", "15116816"):
        expect(f"guide 데이터셋 {ds_id} 명시", ds_id in g)
    expect("guide setup_api_key CLI 명시", "setup_api_key" in g)


# ---------------------------------------------------------------------------
# 10. DATA_GO_KR_ENDPOINTS·DATASETS 정합성
# ---------------------------------------------------------------------------

def test_dataset_consistency():
    expect("ENDPOINTS·DATASETS 같은 키", set(L.DATA_GO_KR_ENDPOINTS.keys()) == set(L.DATA_GO_KR_DATASETS.keys()))
    expect("DATA_GO_KR_DATASETS 7개", len(L.DATA_GO_KR_DATASETS) == 7)
    for ds_id, url in L.DATA_GO_KR_ENDPOINTS.items():
        expect(f"endpoint {ds_id} HTTPS", url.startswith("https://"))


# ---------------------------------------------------------------------------
# 11. SOC 코드 정규식 직접 검증
# ---------------------------------------------------------------------------

def test_soc_pattern():
    valid = ["15-1252.00", "29-1141.00", "11-1011.00", "53-7062.07"]
    invalid = ["15-1252", "15-1252.0", "15-12521.00", "1-1252.00", "15.1252-00", "abc"]
    for s in valid:
        expect(f"SOC valid: {s}", L.ONET_SOC_PATTERN.match(s) is not None)
    for s in invalid:
        expect(f"SOC invalid: {s}", L.ONET_SOC_PATTERN.match(s) is None)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== school_major_lib_test.py ===")
    test_check_api_keys_empty()
    test_setup_api_key_basic()
    test_setup_api_key_invalid()
    test_check_api_keys_kr_only()
    test_check_api_keys_onet_only()
    test_validate_endpoints()
    test_holland_to_onet()
    test_ko_en_major_dict()
    test_major_to_onet()
    test_attribution()
    test_kr_api_blocked_without_key()
    test_kr_required_arg_validation()
    test_onet_input_validation()
    test_cache_refresh()
    test_cache_read_write()
    test_cross_reference_basic()
    test_setup_guide_content()
    test_dataset_consistency()
    test_soc_pattern()

    total = PASS + FAIL
    print()
    print(f"=== {PASS}/{total} PASS ===")
    if FAIL == 0:
        print("ALL PASS")
        return 0
    print(f"FAIL: {FAIL}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
