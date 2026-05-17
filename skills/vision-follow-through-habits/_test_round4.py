"""
Round 4 — 통합 시나리오 + API 안정성 + ISBN/DOI 정확성.
이전 3개 라운드와 전혀 다른 프롬프트.
"""

import sys
sys.path.insert(0, "/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits")
import habit_lib as HL
from habit_lib import lookup_source, validate_habit_stack, parse_start_date, calc_settlement_dates, HABIT_SOURCES

SKILL_MD = "/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits/SKILL.md"


def t31_today_plus_70():
    """31. 박사님 새벽 4시 집필 + 시작일 2026-05-17 → 정확한 일자 계산"""
    d = parse_start_date("2026-05-17")
    dates = calc_settlement_dates(d)
    assert dates["day7_check"] == "2026-05-23"
    assert dates["day30_check"] == "2026-06-15"
    assert dates["day66_lally_median"] == "2026-07-21"
    assert dates["day90_settlement_review"] == "2026-08-14"
    print(f"[#31 PASS] 2026-05-17 시작 → 90일 정착 {dates['day90_settlement_review']}")


def t32_input_types_a_to_f():
    """32. 입력 유형 A~F 6종 모두 SKILL.md에 명시"""
    with open(SKILL_MD) as f:
        s = f.read()
    for code in ["**A**:", "**B**:", "**C**:", "**D**:", "**E**:", "**F**:"]:
        assert code in s, f"입력 유형 누락: {code}"
    print(f"[#32 PASS] 입력 유형 A~F 6종 모두 명시")


def t33_scenarios_4_kinds():
    """33. 박사님 활용 시나리오 4종 명시"""
    with open(SKILL_MD) as f:
        s = f.read()
    keywords = ["집필 루틴", "새벽 기도", "청년부", "가족"]
    missing = [k for k in keywords if k not in s]
    assert not missing, f"시나리오 누락: {missing}"
    print(f"[#33 PASS] 박사님 활용 시나리오 4종 명시")


def t34_doi_format():
    """34. Lally 2010 DOI 포맷 정확"""
    src = lookup_source("lally_2010")
    assert src["doi"] == "10.1002/ejsp.674"
    print(f"[#34 PASS] Lally 2010 DOI = {src['doi']}")


def t35_fogg_isbn():
    """35. Fogg Tiny Habits ISBN 13자리"""
    src = lookup_source("fogg_2019")
    isbn = src["isbn"].replace("-", "")
    assert len(isbn) == 13, f"ISBN 길이 오류: {isbn}"
    assert isbn == "9780358003326"
    print(f"[#35 PASS] Fogg ISBN-13 = {src['isbn']}")


def t36_clear_isbn():
    """36. Clear Atomic Habits ISBN 13자리"""
    src = lookup_source("clear_2018")
    isbn = src["isbn"].replace("-", "")
    assert len(isbn) == 13
    assert isbn == "9780735211292"
    print(f"[#36 PASS] Clear ISBN-13 = {src['isbn']}")


def t37_duhigg_isbn():
    """37. Duhigg Power of Habit ISBN 13자리"""
    src = lookup_source("duhigg_2012")
    isbn = src["isbn"].replace("-", "")
    assert len(isbn) == 13
    assert isbn == "9781400069286"
    print(f"[#37 PASS] Duhigg ISBN-13 = {src['isbn']}")


def t38_miss_recovery_simulation():
    """38. 빠진 날 회복 시뮬레이션 — 월요일 빠짐 → 화요일 같은 트리거에서 회복"""
    from habit_lib import gen_first_7_day_plan
    d = parse_start_date("2026-05-18")  # 월요일
    plan = gen_first_7_day_plan(d, "양치 후", "한 문장 쓰기")
    # Day 1 (월) 빠졌다면 Day 2 (화)에 같은 트리거(양치 후)에서 회복
    assert plan[0]["weekday"] == "월"
    assert plan[1]["weekday"] == "화"
    assert plan[0]["trigger"] == plan[1]["trigger"]
    assert "Never miss twice" in plan[1]["if_missed"]
    print(f"[#38 PASS] Day 1(월) 빠짐 → Day 2(화) 같은 트리거 회복 안내")


def t39_english_stack_format():
    """39. Habit Stacking 영어 양식 'After I X, I will Y' 결정론 추출"""
    res = validate_habit_stack("After I brush teeth, I will write one sentence")
    assert res["pass"], f"영어 양식 통과 안됨: {res}"
    print(f"[#39 PASS] 영어 Habit Stacking 양식 통과")


def t40_api_stability():
    """40. habit_lib 공개 API 9종 모두 정상 노출"""
    expected = ["lookup_source", "format_citation", "all_citations_block",
                "validate_30sec_action", "validate_habit_stack", "validate_5_steps",
                "parse_start_date", "calc_settlement_dates",
                "gen_first_7_day_plan", "format_first_7_day_plan",
                "gen_habit_card_markdown", "HabitCard",
                "check_forbidden_statements", "check_never_miss_twice",
                "full_output_validation"]
    missing = [a for a in expected if not hasattr(HL, a)]
    assert not missing, f"API 누락: {missing}"
    print(f"[#40 PASS] habit_lib API {len(expected)}종 모두 노출")


def run_all():
    tests = [t31_today_plus_70, t32_input_types_a_to_f, t33_scenarios_4_kinds,
             t34_doi_format, t35_fogg_isbn, t36_clear_isbn, t37_duhigg_isbn,
             t38_miss_recovery_simulation, t39_english_stack_format,
             t40_api_stability]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"[{t.__name__} FAIL] {e}")
        except Exception as e:
            print(f"[{t.__name__} EXCEPTION] {type(e).__name__}: {e}")
    print(f"\n=== Round 4 결과: {passed}/10 PASS ===")
    return passed == 10


if __name__ == "__main__":
    ok = run_all()
    raise SystemExit(0 if ok else 1)
