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


# ---------------------------------------------------------------------------
# 1. check_api_keys + setup_api_key (isolated temp config)
# ---------------------------------------------------------------------------

def _with_temp_config(test_fn):
    """일시적으로 KEYS_PATH·CONFIG_DIR을 tmp로 가리키고 테스트 실행."""
    saved_dir = L.CONFIG_DIR
    saved_path = L.KEYS_PATH
    with tempfile.TemporaryDirectory() as tmp:
        L.CONFIG_DIR = tmp
        L.KEYS_PATH = os.path.join(tmp, "api_keys.json")
        try:
            test_fn()
        finally:
            L.CONFIG_DIR = saved_dir
            L.KEYS_PATH = saved_path


def test_check_api_keys_empty():
    def fn():
        out = L.check_api_keys()
        expect("check 빈 상태 ok:false", not out["ok"])
        expect("check 빈 상태 mode=none", out["mode"] == "none")
        expect("check setup_guide 포함", "공공데이터포털" in out["setup_guide"])
    _with_temp_config(fn)


def test_setup_api_key_basic():
    def fn():
        out = L.setup_api_key("data_go_kr", "TEST_KEY_KR")
        expect("setup data_go_kr ok", out["ok"])
        expect("setup 파일 권한 600", out["file_mode"] in ("0o600", "0o400"))

        out = L.setup_api_key("onet", "username:password")
        expect("setup onet ok", out["ok"])

        # 두 키 등록 후 check
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
        out = L.setup_api_key("data_go_kr", 123)  # type: ignore
        expect("setup 비-str value 차단", not out["ok"])
    _with_temp_config(fn)


def test_check_api_keys_kr_only():
    def fn():
        L.setup_api_key("data_go_kr", "K")
        c = L.check_api_keys()
        expect("kr only mode", c["mode"] == "korean_only" and c["ok"])
    _with_temp_config(fn)


# ---------------------------------------------------------------------------
# 2. validate_api_endpoints_sync
# ---------------------------------------------------------------------------

def test_validate_endpoints():
    out = L.validate_api_endpoints_sync()
    expect("endpoints 7개 등록", out["ok"] and out["actual_kr"] == 7)
    expect("ONET base url", "services.onetcenter.org" in out["onet_base"])


# ---------------------------------------------------------------------------
# 3. holland_to_onet — 6 코드 모두
# ---------------------------------------------------------------------------

def test_holland_to_onet():
    for code in ("R", "I", "A", "S", "E", "C"):
        out = L.holland_to_onet(code)
        expect(f"holland {code} ok", out["ok"] and out["holland_code"] == code)
        expect(f"holland {code} 키워드 5개 이상", len(out["search_keywords"]) >= 5)
        expect(f"holland {code} attribution 포함", "O*NET" in out["attribution"]["rendered"])

    # 잘못된 코드
    expect("holland 잘못된 코드", not L.holland_to_onet("X")["ok"])
    expect("holland None", not L.holland_to_onet(None)["ok"])  # type: ignore


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

    # 전체 사전
    out = L.ko_en_major_dict()
    expect("ko_en 전체 사전", out["ok"] and out["count"] >= 50)

    # 없는 학과
    out = L.ko_en_major_dict("외계전공zzz")
    expect("ko_en 없는 학과", not out["ok"])


def test_major_to_onet():
    # ONET 키 없으면 매핑만 반환
    def fn():
        out = L.major_to_onet("컴퓨터공학")
        expect("major_to_onet ko→en 매핑 ok", out["ok"] and out["en_major"] == "Computer Science")
        # ONET 키 미등록 안내
        expect("major_to_onet onet 미등록 안내", "key not registered" in str(out.get("onet_search", {})))

        # 없는 학과
        bad = L.major_to_onet("외계전공zzz")
        expect("major_to_onet 없는 학과 fail", not bad["ok"])
    _with_temp_config(fn)


# ---------------------------------------------------------------------------
# 5. attribution — 결정론 자동 생성
# ---------------------------------------------------------------------------

def test_attribution():
    a = L.attribution_text()
    expect("kr attribution data.go.kr 명시", "data.go.kr" in a["rendered"])
    expect("kr attribution 7개 데이터셋", len(a["datasets"]) == 7)

    o = L.onet_attribution_text()
    expect("onet attribution O*NET 명시", "O*NET" in o["rendered"])
    expect("onet attribution CC BY 명시", "CC BY" in o["rendered"])
    expect("onet attribution USDOL 명시", "U.S. Department of Labor" in o["rendered"])

    # validate_attribution_present
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
    _with_temp_config(fn)


def test_onet_input_validation():
    # SOC 코드 형식
    expect("onet soc 잘못된 형식", not L.onet_occupation_detail("invalid")["ok"])
    expect("onet soc None", not L.onet_occupation_detail(None)["ok"])  # type: ignore
    # 빈 keyword
    expect("onet search 빈 키워드", not L.onet_search_occupation("")["ok"])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=== school_major_lib_test.py ===")
    test_check_api_keys_empty()
    test_setup_api_key_basic()
    test_setup_api_key_invalid()
    test_check_api_keys_kr_only()
    test_validate_endpoints()
    test_holland_to_onet()
    test_ko_en_major_dict()
    test_major_to_onet()
    test_attribution()
    test_kr_api_blocked_without_key()
    test_onet_input_validation()

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
