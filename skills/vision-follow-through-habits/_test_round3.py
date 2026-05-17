"""
신규 10개 검증 — Round 3 (Round 1·2와 전혀 다른 경계 케이스).
SKILL.md 자체의 완전성·결정론 함수 경계 동작 검증.
"""

import sys, re
sys.path.insert(0, "/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits")
from habit_lib import (
    lookup_source, validate_habit_stack, parse_start_date,
    calc_settlement_dates, gen_first_7_day_plan,
    HABIT_SOURCES,
)

SKILL_MD = "/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits/SKILL.md"


def t21_stack_variant_punctuation():
    """21. Habit Stacking 양식 변형 — '양치한 후에, 글쓰기 한다' (쉼표 포함)"""
    res = validate_habit_stack("양치한 후에, 글쓰기 한다")
    assert res["pass"], f"양치한 후에 글쓰기 통과 안 됨: {res}"
    print(f"[#21 PASS] Habit Stacking 양식 변형(쉼표) 통과 — anchor='{res['anchor']}'")


def t22_polivy_pages():
    """22. Polivy & Herman 1985 페이지 범위 정확"""
    src = lookup_source("polivy_herman_1985")
    assert src["volume_pages"] == "40(2): 193–201"
    assert src["journal"] == "American Psychologist"
    print(f"[#22 PASS] Polivy 1985 페이지 정확 — {src['volume_pages']}")


def t23_seinfeld_denial_preserved():
    """23. Seinfeld 귀속 부인 명시 보존"""
    src = lookup_source("isaac_seinfeld_2007")
    assert "부인" in src["attribution_note"]
    assert "Brad Isaac" in src["author"]
    assert "1990년대 후반" in src["attribution_note"]
    print(f"[#23 PASS] Seinfeld 귀속 부인 명시 보존")


def t24_leap_year_handling():
    """24. 윤년 처리 — 2024-02-29 + 90일"""
    d = parse_start_date("2024-02-29")
    dates = calc_settlement_dates(d)
    # 2024-02-29 + 89일 = 2024-05-28
    assert dates["day90_settlement_review"] == "2024-05-28", f"윤년 계산 오류: {dates['day90_settlement_review']}"
    print(f"[#24 PASS] 윤년 2024-02-29 + 90일 = {dates['day90_settlement_review']}")


def t25_far_future_date():
    """25. 시작일 2050-01-01 정상 계산"""
    d = parse_start_date("2050-01-01")
    dates = calc_settlement_dates(d)
    assert dates["day66_lally_median"] == "2050-03-07"
    print(f"[#25 PASS] 먼 미래 2050-01-01 → 66일째 {dates['day66_lally_median']}")


def t26_weekday_korean():
    """26. 첫 7일 플랜 한글 요일"""
    d = parse_start_date("2026-05-18")  # 월요일
    plan = gen_first_7_day_plan(d, "양치 후", "한 문장 쓰기")
    expected_weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    actual = [p["weekday"] for p in plan]
    assert actual == expected_weekdays, f"요일 결정론 오류: {actual}"
    print(f"[#26 PASS] 7일 한글 요일 정확 — {actual}")


def t27_absolute_principles_in_skill_md():
    """27. SKILL.md에 절대 원칙 10개 모두 명시"""
    with open(SKILL_MD) as f:
        s = f.read()
    expected = ["5단계 모두 진행", "30초 시작 단계 의무", "트리거를 기존 습관에 앵커",
                "Never miss twice", "3개월 정착 기간", "작심삼일", "사용자 폄하 금지",
                "사실적 정확성", "결정론 함수 호출 의무", "의학·중독 한계"]
    missing = [p for p in expected if p not in s]
    assert not missing, f"누락 원칙: {missing}"
    print(f"[#27 PASS] 절대 원칙 10개 모두 SKILL.md에 명시")


def t28_output_format_3_kinds():
    """28. 출력 양식 3종(기본/E/F) 모두 SKILL.md에 명시"""
    with open(SKILL_MD) as f:
        s = f.read()
    assert "기본 산출물" in s
    assert "이론 설명 산출물" in s
    assert "Step 특정 질문 산출물" in s
    print(f"[#28 PASS] 출력 양식 3종(기본·이론·Step특정) 모두 명시")


def t29_error_codes_e01_to_e10():
    """29. 오류 코드 E-01~E-10 모두 SKILL.md에 명시"""
    with open(SKILL_MD) as f:
        s = f.read()
    missing = [f"E-{i:02d}" for i in range(1, 11) if f"E-{i:02d}" not in s]
    assert not missing, f"누락 오류 코드: {missing}"
    print(f"[#29 PASS] 오류 코드 E-01~E-10 모두 명시")


def t30_eight_check_items_all_present():
    """30. 박사님 8개 점검 항목 — description·목적·역할·고유 영역·운영원칙·기능과 원칙·출력 양식·오류 및 예외처리 모두 SKILL.md에 명시"""
    with open(SKILL_MD) as f:
        s = f.read()
    expected = ["description:", "## 목적과 의미", "## 역할", "## 고유 영역",
                "## 운영원칙", "5단계 습관 설계", "## 출력 양식", "## 오류 및 예외처리"]
    missing = [e for e in expected if e not in s]
    assert not missing, f"누락 8개 항목: {missing}"
    print(f"[#30 PASS] 박사님 8개 점검 항목 모두 SKILL.md에 명시")


def run_all():
    tests = [t21_stack_variant_punctuation, t22_polivy_pages,
             t23_seinfeld_denial_preserved, t24_leap_year_handling,
             t25_far_future_date, t26_weekday_korean,
             t27_absolute_principles_in_skill_md, t28_output_format_3_kinds,
             t29_error_codes_e01_to_e10, t30_eight_check_items_all_present]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"[{t.__name__} FAIL] {e}")
        except Exception as e:
            print(f"[{t.__name__} EXCEPTION] {type(e).__name__}: {e}")
    print(f"\n=== Round 3 결과: {passed}/10 PASS ===")
    return passed == 10


if __name__ == "__main__":
    ok = run_all()
    raise SystemExit(0 if ok else 1)
