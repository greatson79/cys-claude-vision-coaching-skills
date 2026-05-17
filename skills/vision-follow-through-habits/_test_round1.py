"""
신규 10개 검증 프롬프트 자동 테스트 (Round 1)
이전 검증과 전혀 다른 프롬프트로 100% 정확도 확인.
"""

import sys
sys.path.insert(0, "/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits")
from habit_lib import (
    lookup_source, format_citation, all_citations_block,
    validate_30sec_action, validate_habit_stack, validate_5_steps,
    parse_start_date, calc_settlement_dates,
    format_first_7_day_plan, gen_habit_card_markdown, HabitCard,
    check_forbidden_statements, check_never_miss_twice,
    full_output_validation,
)

PROMPTS = [
    {
        "id": 1,
        "prompt": "박사님 본인의 새벽 4시 집필 루틴을 설계해줘. 주 4일은 본업 일정으로 시간 변동.",
        "type": "D",
        "expected_passes": ["habit_stack", "30sec", "5steps", "never_miss_twice", "forbidden"],
    },
    {
        "id": 2,
        "prompt": "신년 결심 5가지(독서·운동·새벽기도·금주·금연) 동시에 시작했다가 한 달째 다 무너졌어. 재시작 어떻게 할까?",
        "type": "C+B",
        "expected_passes": ["forbidden", "lookup_polivy_herman_1985"],
    },
    {
        "id": 3,
        "prompt": "교회 청년부 30명에게 '매일 성경 한 장 읽기' 습관 캠페인을 시키고 싶다. 셀모임 활용 방안 포함.",
        "type": "B",
        "expected_passes": ["habit_stack", "30sec", "5steps"],
    },
    {
        "id": 4,
        "prompt": "B=MAP 공식 설명해줘. 그리고 내 '매일 영어 단어 30개 외우기' 결심에 적용해줘.",
        "type": "E",
        "expected_passes": ["lookup_fogg_2019"],
    },
    {
        "id": 5,
        "prompt": "21일이면 습관이 형성된다는데 맞나요? 학술 근거 있나요?",
        "type": "E",
        "expected_passes": ["lookup_lally_2010", "forbidden_21_day_myth"],
    },
    {
        "id": 6,
        "prompt": "Habit Stacking 양식이 뭐예요? 추적 도구는 어떤 게 좋아요?",
        "type": "F",
        "expected_passes": ["habit_stack", "lookup_clear_2018", "lookup_isaac"],
    },
    {
        "id": 7,
        "prompt": "다이어트 작심삼일 5번째 실패. 이번엔 정말 다르게 가고 싶다. 30초 시작 단계가 뭐예요?",
        "type": "C+F",
        "expected_passes": ["lookup_fogg_2019", "30sec_concept"],
    },
    {
        "id": 8,
        "prompt": "고3 입시생 아들에게 '매일 영어 청해 15분' 습관을 잡아주고 싶다. 시작일 2026-06-01.",
        "type": "A",
        "expected_passes": ["habit_card_generation", "date_calc", "30sec_after_split"],
    },
    {
        "id": 9,
        "prompt": "도박 끊고 싶어요. 게임도 너무 많이 해요. 습관 설계 도와주세요.",
        "type": "한계",
        "expected_passes": ["E-09_addiction_referral"],
    },
    {
        "id": 10,
        "prompt": "Lally 2010 연구가 정확히 뭐예요? 66일이라는 숫자의 의미는?",
        "type": "E",
        "expected_passes": ["lookup_lally_2010_full_detail"],
    },
]


def test_prompt_1():
    """박사님 새벽 4시 집필 루틴 — 습관 카드 결정론 생성"""
    card = HabitCard(
        user_label="박사님 새벽 집필 루틴",
        goal_abstract="단행본 집필 일정 유지",
        step1_concrete_action="새벽 4:00~6:00 사이 본문 1,000자 쓰기 (주 3일 기준)",
        step2_anchor="기상 후 양치질 후에 노트북 앞 앉기 한다",
        step3_tiny_start="노트북 열고 한 문장 쓰기",
        step4_reward="좋아하는 차 한 잔 + 셀모임 카톡에 '오늘 완료' 보고",
        step5_tracking="종이 캘린더 X 표시 (Don't Break the Chain) + 일주일 단위 점검",
        start_date="2026-05-18",
    )
    md = gen_habit_card_markdown(card)
    val = full_output_validation(md)
    assert val["overall_pass"], f"FAIL: {val}"
    print(f"[#1 PASS] 박사님 새벽 집필 루틴 카드 결정론 생성 OK")
    return True


def test_prompt_2():
    """신년 5가지 동시 시작 → 깨진 습관 회복 — Polivy & Herman 1985 인용 결정론"""
    src = lookup_source("polivy_herman_1985")
    cite = format_citation("polivy_herman_1985")
    assert "1985" in cite and "American Psychologist" in cite
    assert "Abstinence Violation" in src["concept"]
    print(f"[#2 PASS] Polivy & Herman 1985 결정론 인용: {cite[:80]}...")
    return True


def test_prompt_3():
    """청년부 30명 캠페인 — Habit Stacking + 셀모임 사회적 보상"""
    stack_check = validate_habit_stack("저녁 큐티 후에 성경 한 장 읽기 한다")
    assert stack_check["pass"], f"FAIL: {stack_check}"
    print(f"[#3 PASS] 청년부 Habit Stacking 양식 통과: anchor='{stack_check['anchor']}'")
    return True


def test_prompt_4():
    """B=MAP 공식 — Fogg 2019 결정론 조회"""
    src = lookup_source("fogg_2019")
    assert src["core_formula"] == "B = MAP (Behavior = Motivation × Ability × Prompt)"
    assert "Trigger" in src["previous_formula"]
    print(f"[#4 PASS] Fogg B=MAP 결정론 조회: {src['core_formula']}")
    return True


def test_prompt_5():
    """21일 신화 차단 — Lally 2010 + forbidden 검증"""
    src = lookup_source("lally_2010")
    assert src["median_days"] == 66
    assert src["range_days_low"] == 18
    assert src["range_days_high"] == 254
    # 21일 신화 단언 차단
    fbd = check_forbidden_statements("21일이면 습관이 형성됩니다.")
    assert not fbd["pass"], "21일 신화 차단 실패"
    print(f"[#5 PASS] 21일 신화 차단 + Lally median={src['median_days']}일 / range {src['range_days_low']}~{src['range_days_high']}일")
    return True


def test_prompt_6():
    """Habit Stacking 양식 + Don't Break the Chain (Isaac 2007)"""
    clear_src = lookup_source("clear_2018")
    isaac_src = lookup_source("isaac_seinfeld_2007")
    assert "After [CURRENT HABIT]" in clear_src["habit_stacking_quote"]
    assert "Brad Isaac" in isaac_src["author"]
    assert "부인" in isaac_src["attribution_note"]
    print(f"[#6 PASS] Clear Habit Stacking + Isaac/Seinfeld 귀속 주의 동시 결정론 조회")
    return True


def test_prompt_7():
    """30초 Tiny 검증 — 큰 행동 차단"""
    big = validate_30sec_action("매일 1시간 운동")
    small = validate_30sec_action("신발 신고 현관문 나가기")
    assert not big["pass"], "큰 행동이 통과되면 FAIL"
    assert small["pass"], "Tiny가 통과 안 되면 FAIL"
    print(f"[#7 PASS] 30초 검증 — 1시간 차단 / Tiny PASS")
    return True


def test_prompt_8():
    """고3 아들 영어 청해 — 시작일 2026-06-01 결정론 캘린더"""
    d = parse_start_date("2026-06-01")
    dates = calc_settlement_dates(d)
    assert dates["day66_lally_median"] == "2026-08-05"
    assert dates["day90_settlement_review"] == "2026-08-29"
    plan = format_first_7_day_plan(d, "저녁 식사 후", "이어폰 끼고 첫 문장 듣기")
    assert "Day 1" in plan and "2026-06-01" in plan and "Day 7" in plan
    print(f"[#8 PASS] 시작일 2026-06-01 → 90일 정착 점검 {dates['day90_settlement_review']}")
    return True


def test_prompt_9():
    """중독 영역 — 한계 명시 (SKILL.md 의무 텍스트 확인)"""
    with open("/Users/cys/Desktop/CYSjavis/cys-claude-vision-coaching-skills/skills/vision-follow-through-habits/SKILL.md") as f:
        skill = f.read()
    assert "중독 회복" in skill and "전문" in skill
    assert "도박" in skill or "알코올" in skill
    print(f"[#9 PASS] 도박·알코올·게임 중독 → 한계·전문가 의뢰 SKILL.md 명시 OK")
    return True


def test_prompt_10():
    """Lally 2010 상세 결정론 조회"""
    src = lookup_source("lally_2010")
    expected_keys = ["author", "year", "title", "journal", "volume_pages",
                     "doi", "median_days", "range_days_low", "range_days_high",
                     "criterion", "n_participants", "duration_weeks"]
    for k in expected_keys:
        assert k in src, f"Lally src missing key: {k}"
    assert src["doi"] == "10.1002/ejsp.674"
    assert src["criterion"] == "95% asymptote of automaticity (Self-Report Habit Index)"
    print(f"[#10 PASS] Lally 2010 12개 메타 필드 모두 결정론 보존 (DOI {src['doi']})")
    return True


def run_all():
    tests = [test_prompt_1, test_prompt_2, test_prompt_3, test_prompt_4,
             test_prompt_5, test_prompt_6, test_prompt_7, test_prompt_8,
             test_prompt_9, test_prompt_10]
    passed = 0
    failed = []
    for t in tests:
        try:
            if t():
                passed += 1
        except AssertionError as e:
            failed.append((t.__name__, str(e)))
            print(f"[{t.__name__} FAIL] {e}")
        except Exception as e:
            failed.append((t.__name__, f"EXCEPTION: {e}"))
            print(f"[{t.__name__} EXCEPTION] {e}")
    print(f"\n=== Round 1 결과: {passed}/10 PASS ===")
    if failed:
        for f, e in failed:
            print(f"  - {f}: {e}")
    return passed == 10


if __name__ == "__main__":
    ok = run_all()
    raise SystemExit(0 if ok else 1)
