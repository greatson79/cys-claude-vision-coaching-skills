"""
신규 10개 검증 프롬프트 — Round 2 (이전과 전혀 다른 프롬프트).
부정 케이스(차단되어야 하는 입력)도 포함.
"""

import sys, os
sys.path.insert(0, "/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits")
from habit_lib import (
    lookup_source, format_citation, all_citations_block,
    validate_30sec_action, validate_habit_stack, validate_5_steps,
    parse_start_date, calc_settlement_dates,
    format_first_7_day_plan, gen_habit_card_markdown, HabitCard,
    check_forbidden_statements, check_never_miss_twice,
    full_output_validation,
)


def t11_b_mat_vs_b_map():
    """11. B=MAT vs B=MAP 변경 이유 — Fogg 카탈로그 previous_formula 보존"""
    src = lookup_source("fogg_2019")
    assert "MAT" in src["previous_formula"]
    assert "2009" in src["previous_formula"]
    assert "Trigger" in src["previous_formula"]
    assert "Prompt" in src["previous_formula"]
    print(f"[#11 PASS] B=MAT(2009) → B=MAP(2019) 변경 이력 결정론 보존")


def t12_clear_four_laws():
    """12. Atomic Habits 4법칙 — 4개 모두 결정론 조회"""
    src = lookup_source("clear_2018")
    laws = src["four_laws"]
    assert len(laws) == 4
    keywords = ["Obvious", "Attractive", "Easy", "Satisfying"]
    for kw in keywords:
        assert any(kw in l for l in laws), f"Missing law: {kw}"
    print(f"[#12 PASS] Clear 4법칙 결정론 보존: {[l.split('—')[1].strip() for l in laws]}")


def t13_keystone_habit():
    """13. Keystone Habit — Duhigg 카탈로그 keystone_habit_quote"""
    src = lookup_source("duhigg_2012")
    assert "keystone_habit_quote" in src
    assert "Keystone habits" in src["keystone_habit_quote"]
    print(f"[#13 PASS] Duhigg Keystone Habit 결정론 인용")


def t14_compound_interest_math():
    """14. 1% 복리 = 1.01^365 ≈ 37.78배 (결정론 수학 계산)"""
    val = (1.01) ** 365
    src = lookup_source("clear_2018")
    assert "37.78" in src["one_percent_compounding"]
    assert abs(val - 37.78) < 0.01, f"수학 계산 오류: {val}"
    print(f"[#14 PASS] 1.01^365 = {val:.4f}배 (Clear 카탈로그 37.78배 일치)")


def t15_tiny_fail_300_chars():
    """15. 부정 케이스 — '300자 쓰기' Tiny 검증 FAIL 기대"""
    res = validate_30sec_action("매일 300자 쓰기")
    assert not res["pass"], "300자 쓰기가 Tiny로 통과되면 FAIL"
    assert len(res["violations"]) > 0
    print(f"[#15 PASS] '300자 쓰기' 차단 OK — violations: {res['violations'][0][:60]}")


def t16_21day_myth_block():
    """16. 부정 케이스 — '21일이면 충분' 산출물 차단"""
    bad_output = "21일이면 습관이 충분히 형성됩니다. 매일 1시간씩 운동하세요."
    res = check_forbidden_statements(bad_output)
    assert not res["pass"], "21일 신화 통과되면 FAIL"
    print(f"[#16 PASS] 21일 신화 단언 차단 — violations: {res['violations'][0]['match']}")


def t17_korean_date_parsing():
    """17. 한국어 날짜 파싱 + 90일 계산"""
    d = parse_start_date("2026년 7월 1일")
    dates = calc_settlement_dates(d)
    assert dates["day90_settlement_review"] == "2026-09-28"
    assert dates["day66_lally_median"] == "2026-09-04"
    print(f"[#17 PASS] '2026년 7월 1일' → 90일 정착 {dates['day90_settlement_review']}")


def t18_missing_step_5():
    """18. 부정 케이스 — Step 5 추적 누락 산출물 검출"""
    bad = """
    Step 1 — 구체 행동: 매일 글쓰기.
    Step 2 — 트리거: 양치 후 노트북 열기.
    Step 3 — Tiny: 한 문장 쓰기.
    Step 4 — 보상: 차 한 잔.
    (Step 5 누락)
    """
    res = validate_5_steps(bad)
    assert not res["pass"], "Step 5 누락이 통과되면 FAIL"
    assert 5 in res["missing_steps"]
    print(f"[#18 PASS] Step 5 누락 검출 OK — missing: {res['missing_steps']}")


def t19_unknown_source_error():
    """19. 부정 케이스 — 존재하지 않는 출처 키 조회 시 ValueError"""
    try:
        lookup_source("kahneman_2011")
        print("[#19 FAIL] 존재하지 않는 출처가 통과됨"); return False
    except ValueError as e:
        assert "카탈로그에 없음" in str(e)
        print(f"[#19 PASS] 미존재 출처 차단 — ValueError 발생")


def t20_full_validation_passes_good_output():
    """20. 정상 산출물 — full_output_validation overall_pass=true"""
    card = HabitCard(
        user_label="새벽기도 출석",
        goal_abstract="매주 새벽기도회 지속",
        step1_concrete_action="매일 새벽 5:00 교회 본당 도착",
        step2_anchor="기상 후 옷 갈아입기 후에 차 키 들기 한다",
        step3_tiny_start="현관문 열고 한 발 내딛기",
        step4_reward="셀모임 카톡에 '오늘 출석' 보고",
        step5_tracking="종이 캘린더 X 표시 (Don't Break the Chain)",
        start_date="2026-06-15",
    )
    md = gen_habit_card_markdown(card)
    val = full_output_validation(md)
    assert val["overall_pass"], f"정상 산출물 FAIL: {val}"
    # 부가 검증: 5단계·Never miss twice·90일·Lally·forbidden 모두 PASS
    assert val["5_steps"]["pass"]
    assert val["never_miss_twice"]["pass"]
    assert val["forbidden_statements"]["pass"]
    assert val["has_90_day_mention"]
    assert val["has_lally_mention"]
    print(f"[#20 PASS] 정상 산출물 5개 검증 모두 PASS")


def run_all():
    tests = [t11_b_mat_vs_b_map, t12_clear_four_laws, t13_keystone_habit,
             t14_compound_interest_math, t15_tiny_fail_300_chars,
             t16_21day_myth_block, t17_korean_date_parsing,
             t18_missing_step_5, t19_unknown_source_error,
             t20_full_validation_passes_good_output]
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"[{t.__name__} FAIL] {e}")
        except Exception as e:
            print(f"[{t.__name__} EXCEPTION] {type(e).__name__}: {e}")
    print(f"\n=== Round 2 결과: {passed}/10 PASS ===")
    return passed == 10


if __name__ == "__main__":
    ok = run_all()
    raise SystemExit(0 if ok else 1)
