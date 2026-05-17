"""strategy_calc.py 단위테스트 — 결정론 환원 검증.

각 함수의 정상·경계·예외 케이스를 모두 다룬다. 회귀 차단이 목적.
"""

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import strategy_calc as sc  # noqa: E402


class TestSmartGoal(unittest.TestCase):
    def test_full_smart_korean(self):
        r = sc.validate_smart_goal("2030년까지 단행본 5권을 출판한다")
        self.assertTrue(r.ok, r.reasons)
        self.assertTrue(r.detail["specific"])
        self.assertTrue(r.detail["measurable"])
        self.assertTrue(r.detail["time_bound"])

    def test_missing_deadline(self):
        r = sc.validate_smart_goal("단행본 5권을 출판한다")
        self.assertFalse(r.ok)
        self.assertIn("time:no_deadline", r.reasons)

    def test_missing_number(self):
        r = sc.validate_smart_goal("내년까지 단행본을 출판한다")
        self.assertFalse(r.ok)
        self.assertIn("measurable:no_quantifier", r.reasons)

    def test_too_short(self):
        r = sc.validate_smart_goal("출판")
        self.assertFalse(r.ok)

    def test_empty_input(self):
        r = sc.validate_smart_goal("")
        self.assertFalse(r.ok)
        self.assertIn("empty", r.reasons)

    def test_doran1981_variant(self):
        r = sc.validate_smart_goal("2030년까지 단행본 5권을 출판한다", modern=False)
        self.assertEqual(r.detail["variant"], "doran1981_original")
        self.assertEqual(
            r.detail["elements_definition"],
            ["Specific", "Measurable", "Assignable", "Realistic", "Time-related"],
        )

    def test_english_smart_ok(self):
        # 사용자 입력 언어 따름 원칙 — 영어 입력도 동사·기한·수치 검증 가능
        r = sc.validate_smart_goal("Publish 3 books by 2030 with clear chapters")
        self.assertTrue(r.ok, r.reasons)

    def test_english_no_verb_fail(self):
        r = sc.validate_smart_goal("3 books by 2030")
        self.assertFalse(r.ok)
        self.assertIn("specific:no_action_verb", r.reasons)

    def test_korean_ending_heuristic_dolbon_da(self):
        # 화이트리스트에 없는 한국어 동사도 -다 종결어미로 인식
        r = sc.validate_smart_goal("2030년까지 동네 어르신 30명을 매주 1회 방문 돌본다")
        self.assertTrue(r.ok, r.reasons)

    def test_korean_ending_heuristic_seomgin_da(self):
        r = sc.validate_smart_goal("2030년까지 손자녀 5명을 매일 기도로 섬긴다")
        self.assertTrue(r.ok, r.reasons)

    def test_korean_ending_heuristic_anchakshikinda(self):
        r = sc.validate_smart_goal("2030년까지 교회 1곳을 100명 규모로 안착시킨다")
        self.assertTrue(r.ok, r.reasons)

    def test_korean_no_verb_ending_fail(self):
        # 명사 종결 — 동사 없음으로 판정
        r = sc.validate_smart_goal("2030년까지 책 5권 발간 목표")
        self.assertFalse(r.ok)
        self.assertIn("specific:no_action_verb", r.reasons)


class TestCountValidation(unittest.TestCase):
    def test_ltg_ok_2(self):
        self.assertTrue(sc.validate_ltg_count(["a", "b"]).ok)

    def test_ltg_ok_4(self):
        self.assertTrue(sc.validate_ltg_count(["a", "b", "c", "d"]).ok)

    def test_ltg_too_few(self):
        r = sc.validate_ltg_count(["a"])
        self.assertFalse(r.ok)
        self.assertIn("ltg_count:1(expected 2-4)", r.reasons)

    def test_ltg_too_many(self):
        r = sc.validate_ltg_count(["a", "b", "c", "d", "e"])
        self.assertFalse(r.ok)

    def test_ltg_not_list(self):
        r = sc.validate_ltg_count("hello")  # type: ignore[arg-type]
        self.assertFalse(r.ok)

    def test_stg_3_per_ltg_ok(self):
        r = sc.validate_stg_count([["a", "b", "c"], ["d", "e", "f"]])
        self.assertTrue(r.ok)

    def test_stg_count_violation(self):
        r = sc.validate_stg_count([["a", "b"], ["c", "d", "e"]])
        self.assertFalse(r.ok)
        self.assertIn("ltg1_stg_count:2(expected 3-5)", r.reasons)

    def test_quarter_focus_ok(self):
        self.assertTrue(sc.validate_quarter_focus([2, 3, 1, 3]).ok)

    def test_quarter_focus_violation(self):
        r = sc.validate_quarter_focus([4, 2, 1, 0])
        self.assertFalse(r.ok)
        self.assertIn("Q1:4>3", r.reasons)

    def test_quarter_not_4_elements(self):
        r = sc.validate_quarter_focus([1, 2, 3])
        self.assertFalse(r.ok)


class TestSchedule(unittest.TestCase):
    def test_sunday_jumps_full_week(self):
        # 2026-05-17 is Sunday (weekday=6) — next Sunday should be 2026-05-24
        s = sc.calculate_review_schedule("2026-05-17")
        self.assertEqual(s["weekly"], "2026-05-24")

    def test_monday_next_sunday(self):
        # 2026-05-18 Monday → next Sunday 2026-05-24
        s = sc.calculate_review_schedule("2026-05-18")
        self.assertEqual(s["weekly"], "2026-05-24")

    def test_quarterly_q2_end(self):
        # May 2026 (Q2 ends in June 2026) — last Friday of June 2026 is 2026-06-26
        # Monday of that week is 2026-06-22
        s = sc.calculate_review_schedule("2026-05-17")
        self.assertEqual(s["quarterly"], "2026-06-22")

    def test_annual_with_birthday(self):
        s = sc.calculate_review_schedule("2026-05-17", birthday="1968-08-15")
        # 2026-08-15 is Saturday → Monday of that week is 2026-08-10
        self.assertEqual(s["annual"], "2026-08-10")

    def test_annual_default_december(self):
        s = sc.calculate_review_schedule("2026-05-17")
        # December 2026 first Monday — Dec 1, 2026 is Tuesday → first Monday Dec 7
        self.assertEqual(s["annual"], "2026-12-07")

    def test_monthly_last_friday(self):
        # May 2026 — last Friday is 2026-05-29
        s = sc.calculate_review_schedule("2026-05-17")
        self.assertEqual(s["monthly"], "2026-05-29")

    def test_invalid_date_format(self):
        with self.assertRaises(ValueError):
            sc.calculate_review_schedule("not-a-date")

    def test_date_object_input(self):
        s = sc.calculate_review_schedule(date(2026, 5, 17))
        self.assertEqual(s["weekly"], "2026-05-24")


class TestPivot(unittest.TestCase):
    def test_on_track(self):
        r = sc.check_pivot_trigger(85)
        self.assertEqual(r["status"], "on_track")

    def test_caution(self):
        r = sc.check_pivot_trigger(70)
        self.assertEqual(r["status"], "caution")

    def test_pivot_required_quarterly(self):
        r = sc.check_pivot_trigger(50)
        self.assertEqual(r["status"], "pivot_required")
        self.assertEqual(r["action"], "STG 재설계")

    def test_pivot_required_annual(self):
        r = sc.check_pivot_trigger(50, scope="annual")
        self.assertEqual(r["action"], "LTG 재설정")

    def test_boundary_80(self):
        self.assertEqual(sc.check_pivot_trigger(80)["status"], "on_track")

    def test_boundary_60(self):
        self.assertEqual(sc.check_pivot_trigger(60)["status"], "caution")

    def test_boundary_59(self):
        self.assertEqual(sc.check_pivot_trigger(59)["status"], "pivot_required")

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):
            sc.check_pivot_trigger(50, scope="weekly")

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            sc.check_pivot_trigger(150)

    def test_non_numeric(self):
        with self.assertRaises(TypeError):
            sc.check_pivot_trigger("seventy")  # type: ignore[arg-type]


class TestCitation(unittest.TestCase):
    def test_lookup_smart(self):
        c = sc.lookup_citation("SMART")
        self.assertEqual(c["author"], "George T. Doran")
        self.assertEqual(c["year"], 1981)
        self.assertEqual(c["venue"], "Management Review")
        self.assertEqual(c["volume"], 70)
        self.assertEqual(c["issue"], 11)
        self.assertEqual(c["pages"], "35-36")

    def test_lookup_gollwitzer(self):
        c = sc.lookup_citation("ImplementationIntentions")
        self.assertEqual(c["year"], 1999)
        self.assertEqual(c["venue"], "American Psychologist")
        self.assertEqual(c["volume"], 54)
        self.assertEqual(c["issue"], 7)

    def test_lookup_unknown(self):
        with self.assertRaises(KeyError):
            sc.lookup_citation("UnknownKey")

    def test_render_citation(self):
        s = sc.render_citation("SMART")
        self.assertIn("Doran", s)
        self.assertIn("1981", s)
        self.assertIn("70(11)", s)

    def test_list_keys(self):
        ks = sc.list_citation_keys()
        self.assertIn("SMART", ks)
        self.assertIn("PDCA", ks)
        self.assertIn("VisionReadinessQ08", ks)
        # _meta excluded
        self.assertNotIn("_meta", ks)


class TestQ08(unittest.TestCase):
    def test_exact_match(self):
        canonical = "I am good at trimming a giant dream into a first step I can take tomorrow morning"
        self.assertTrue(sc.verify_q08_canonical(canonical).ok)

    def test_with_quotes(self):
        self.assertTrue(sc.verify_q08_canonical(
            '"I am good at trimming a giant dream into a first step I can take tomorrow morning"').ok)

    def test_paraphrased_fail(self):
        r = sc.verify_q08_canonical("I'm good at making big dreams into tomorrow's small steps")
        self.assertFalse(r.ok)

    def test_translated_only_fail(self):
        r = sc.verify_q08_canonical("나는 큰 꿈을 내일 아침 첫 걸음으로 잘 쪼개는 사람이다")
        self.assertFalse(r.ok)

    def test_empty_fail(self):
        self.assertFalse(sc.verify_q08_canonical("").ok)


class TestFilter(unittest.TestCase):
    def test_clean_text(self):
        r = sc.filter_unsourced_entities("박사님 비전을 SMART(Doran 1981)으로 정리하면", "박사님 비전")
        self.assertTrue(r["ok"], r["violations"])

    def test_unsourced_korean_name(self):
        r = sc.filter_unsourced_entities(
            "박사님께서는 김철수 박사와 협력하셔서",
            "박사님 비전",
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("김철수" in v["token"] for v in r["violations"]))

    def test_unsourced_institution(self):
        r = sc.filter_unsourced_entities(
            "ABC출판사와 협력하여",
            "비전",
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any("ABC출판사" in v["token"] for v in r["violations"]))

    def test_user_mentioned_passes(self):
        r = sc.filter_unsourced_entities(
            "두란노출판사를 통해 진행",
            "두란노출판사",
        )
        self.assertTrue(r["ok"])

    def test_academic_authority_passes(self):
        r = sc.filter_unsourced_entities(
            "Drucker(1954)의 MBO와 Locke & Latham(1990)의 Goal Setting Theory를 참고",
            "",
        )
        self.assertTrue(r["ok"], r["violations"])

    def test_unsourced_year_fail(self):
        r = sc.filter_unsourced_entities(
            "2045년까지 완성하시면",
            "",
        )
        self.assertFalse(r["ok"])
        self.assertTrue(any(v["token"] == "2045" for v in r["violations"]))

    def test_user_year_passes(self):
        r = sc.filter_unsourced_entities(
            "2045년까지 완성하시면",
            "저는 2045년 은퇴를 목표로 합니다",
        )
        self.assertTrue(r["ok"])


class TestReadinessBranch(unittest.TestCase):
    def test_all_high(self):
        r = sc.readiness_branch({
            "BigPicture": 85, "Reframing": 75, "Strategy": 70, "FollowThrough": 80
        })
        self.assertTrue(r["ok"])
        self.assertEqual(r["branch"]["BigPicture"], "LTG 4개 권유")
        self.assertEqual(r["branch"]["FollowThrough"], "분기 점검 위주(자율성 부여)")

    def test_all_low(self):
        r = sc.readiness_branch({
            "BigPicture": 30, "Reframing": 25, "Strategy": 20, "FollowThrough": 35
        })
        self.assertEqual(r["branch"]["BigPicture"], "LTG 2개로 압축 권유")
        self.assertEqual(r["branch"]["Strategy"], "코치가 더 두꺼이 행동 계획 골격 제시")

    def test_normalized_keys(self):
        # Various spellings should be normalized
        r = sc.readiness_branch({
            "Big Picture": 85, "Re-framing": 75,
            "strategy": 70, "follow_through": 80
        })
        self.assertTrue(r["ok"])

    def test_missing_keys(self):
        r = sc.readiness_branch({"BigPicture": 85})
        self.assertFalse(r["ok"])
        self.assertIn("Reframing", r["missing"])

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            sc.readiness_branch({
                "BigPicture": 150, "Reframing": 75, "Strategy": 70, "FollowThrough": 80
            })


class TestFirstStep(unittest.TestCase):
    def test_korean_impl_intent(self):
        r = sc.validate_first_step("내일 아침 6시, 서재에서, 단행본 초안을 30분간 수행")
        self.assertTrue(r.ok, r.reasons)

    def test_english_impl_intent(self):
        r = sc.validate_first_step("When morning arises, I will write for 30 minutes")
        self.assertTrue(r.ok)

    def test_vague_fail(self):
        r = sc.validate_first_step("열심히 하기")
        self.assertFalse(r.ok)

    def test_empty_fail(self):
        self.assertFalse(sc.validate_first_step("").ok)

    def test_missing_location(self):
        r = sc.validate_first_step("내일 6시 운동")
        # 시간 + 동작은 있지만 "어디에서"가 없음 → 실패
        self.assertFalse(r.ok)


class TestHonorific(unittest.TestCase):
    def test_baksanim_consistent(self):
        r = sc.validate_honorific_consistency(
            "박사님의 비전을 박사님과 함께 정리하겠습니다",
            declared="박사님",
        )
        self.assertTrue(r.ok)

    def test_baksanim_mixed_with_other_nim(self):
        r = sc.validate_honorific_consistency(
            "박사님 비전을 윤식님께",
            declared="박사님",
        )
        self.assertFalse(r.ok)

    def test_general_user_other_nim(self):
        r = sc.validate_honorific_consistency(
            "윤식님 비전을 윤식님과 함께",
            declared="윤식님",
        )
        self.assertTrue(r.ok)

    def test_general_user_baksanim_leak(self):
        r = sc.validate_honorific_consistency(
            "윤식님 비전을 박사님 라는 호칭으로",
            declared="윤식님",
        )
        self.assertFalse(r.ok)

    def test_no_declaration_no_conflict(self):
        r = sc.validate_honorific_consistency("일반 응답")
        self.assertTrue(r.ok)

    def test_no_declaration_mixed(self):
        r = sc.validate_honorific_consistency("박사님과 윤식님께서")
        self.assertFalse(r.ok)


class TestModeClassification(unittest.TestCase):
    def test_full_input_A(self):
        r = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=True, has_mbti=True,
            has_values=True, has_strong=True, has_career=True,
            progress_check_only=False, is_baksanim=False,
        )
        self.assertEqual(r["mode"], "A")

    def test_vision_only_B(self):
        r = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=False, has_mbti=False,
            has_values=False, has_strong=False, has_career=False,
            progress_check_only=False, is_baksanim=False,
        )
        self.assertEqual(r["mode"], "B")

    def test_diagnostics_only_C(self):
        r = sc.classify_input_mode(
            has_vision_statement=False, has_readiness=True, has_mbti=True,
            has_values=False, has_strong=False, has_career=False,
            progress_check_only=False, is_baksanim=False,
        )
        self.assertEqual(r["mode"], "C")

    def test_progress_check_D(self):
        r = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=True, has_mbti=True,
            has_values=True, has_strong=True, has_career=True,
            progress_check_only=True, is_baksanim=False,
        )
        self.assertEqual(r["mode"], "D")

    def test_baksanim_E(self):
        r = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=True, has_mbti=True,
            has_values=True, has_strong=True, has_career=True,
            progress_check_only=False, is_baksanim=True,
        )
        self.assertEqual(r["mode"], "E")

    def test_baksanim_priority_over_progress(self):
        r = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=True, has_mbti=True,
            has_values=True, has_strong=True, has_career=True,
            progress_check_only=True, is_baksanim=True,
        )
        self.assertEqual(r["mode"], "E")  # E > D


class TestIntegrationFlow(unittest.TestCase):
    """비전→행동 5단계 전체 흐름의 결정론적 검증 체크"""

    def test_full_strategy_doc_validation(self):
        # 가상의 사용자 시나리오 — 박사님이 단행본·강의 비전을 제시
        user_vision = "박사님 비전: 2030년까지 미래학 단행본 3권 출판"

        # Step 2: LTG
        ltgs = [
            "2030년까지 미래학 단행본 3권을 출판한다",
            "2028년까지 강의 50회 실시한다",
        ]
        self.assertTrue(sc.validate_ltg_count(ltgs).ok)
        for g in ltgs:
            self.assertTrue(sc.validate_smart_goal(g).ok, sc.validate_smart_goal(g).reasons)

        # Step 3: STG
        stgs = [
            ["2027년 1권 출판", "2028년 2권 출판", "2029년 3권 출판"],
            ["2026년 강의 15회", "2027년 강의 20회", "2028년 강의 15회"],
        ]
        self.assertTrue(sc.validate_stg_count(stgs).ok)
        self.assertTrue(sc.validate_quarter_focus([2, 2, 2, 1]).ok)

        # Step 4: 첫 한 걸음
        first_step = "내일 아침 6시, 서재에서, 단행본 1장 초안을 60분간 작성"
        self.assertTrue(sc.validate_first_step(first_step).ok)

        # Step 5: 점검 일정
        schedule = sc.calculate_review_schedule("2026-05-17", birthday="1968-08-15")
        self.assertIn("weekly", schedule)
        self.assertIn("annual", schedule)

        # Pivot 시나리오 — 65% 진척률
        pivot = sc.check_pivot_trigger(65)
        self.assertEqual(pivot["status"], "caution")

        # 산출물 텍스트 안에 사용자 진술 외 인명이 없는지
        coach_doc = (
            "박사님의 비전을 SMART(Doran 1981)와 PDCA(Shewhart 1939)로 정리합니다. "
            "2030년까지 단행본 3권 출판이라는 LTG는 측정 가능합니다."
        )
        filt = sc.filter_unsourced_entities(coach_doc, user_vision)
        self.assertTrue(filt["ok"], filt["violations"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
