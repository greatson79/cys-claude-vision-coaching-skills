"""vision-goal-reframing 결정론 toolkit 단위 테스트."""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from lib import (  # noqa: E402
    date_engine,
    smart_validator,
    okr_validator,
    backcasting,
    citations,
    input_router,
    workbook,
    run,
)


class TestDateEngine(unittest.TestCase):
    def test_timeline_basic(self):
        tl = date_engine.build_timeline("2026-05-17")
        self.assertEqual(tl["today"]["iso_date"], "2026-05-17")
        self.assertEqual(tl["tomorrow"]["iso_date"], "2026-05-18")
        self.assertEqual(tl["one_week"]["iso_date"], "2026-05-24")
        self.assertEqual(tl["one_year"]["iso_date"], "2027-05-17")
        self.assertEqual(tl["five_years"]["iso_date"], "2031-05-17")
        self.assertEqual(tl["next_quarter"]["start_iso"], "2026-07-01")
        self.assertEqual(tl["next_quarter"]["end_iso"], "2026-09-30")
        self.assertEqual(tl["next_quarter"]["quarter"], "Q3")

    def test_quarter_wrap_q4_to_q1(self):
        tl = date_engine.build_timeline("2026-11-15")
        self.assertEqual(tl["next_quarter"]["start_iso"], "2027-01-01")
        self.assertEqual(tl["next_quarter"]["end_iso"], "2027-03-31")
        self.assertEqual(tl["next_quarter"]["quarter"], "Q1")

    def test_leap_year_feb29(self):
        tl = date_engine.build_timeline("2024-02-29")
        # 5년 후는 2029-02-28로 안전 보정
        self.assertEqual(tl["five_years"]["iso_date"], "2029-02-28")

    def test_today_attributes(self):
        tl = date_engine.build_timeline("2026-05-17")
        self.assertEqual(tl["today"]["weekday_kr"], "일")
        self.assertEqual(tl["today"]["quarter"], "Q2")


class TestSmartValidator(unittest.TestCase):
    def test_all_pass(self):
        r = smart_validator.validate_smart(
            "2027-12-31까지 단행본 1권 출간",
            resources_note="6장 완성, 주 10시간",
            vision_link="비전 1차 결실",
        )
        self.assertTrue(r.passed_all)

    def test_time_bound_fails_when_missing(self):
        r = smart_validator.validate_smart(
            "단행본 출간", resources_note="x", vision_link="y"
        )
        self.assertFalse(r.axes[4].passed)

    def test_measurable_korean_units(self):
        # Measurable 단독 평가 — Time-bound가 숫자를 동반하므로 분리
        cases = [
            ("강연 10회", True),
            ("후학 5명 양성", True),
            ("초판 1000부 판매", True),
            ("열심히 노력하기", False),  # 수치 단위 일체 없음
            ("최선을 다한다", False),
        ]
        for txt, expected in cases:
            r = smart_validator.validate_smart(txt, "자원있음", "비전연결")
            self.assertEqual(r.axes[1].passed, expected, txt)


class TestOkrValidator(unittest.TestCase):
    def test_too_few_krs(self):
        r = okr_validator.validate_okr("test obj", ["one KR 1개"])
        self.assertFalse(r.passed)
        self.assertTrue(any("최소 3개" in e for e in r.errors))

    def test_too_many_krs(self):
        krs = [f"KR{i} 5권" for i in range(6)]
        r = okr_validator.validate_okr("test obj", krs)
        self.assertFalse(r.passed)
        self.assertTrue(any("최대 5개" in e for e in r.errors))

    def test_grade_bands(self):
        self.assertEqual(okr_validator.grade_band(0.2)["band"], "red")
        self.assertEqual(okr_validator.grade_band(0.5)["band"], "yellow")
        self.assertEqual(okr_validator.grade_band(0.7)["band"], "green")
        self.assertEqual(okr_validator.grade_band(1.0)["band"], "green")
        self.assertEqual(okr_validator.grade_band(1.5)["band"], "INVALID")

    def test_expected_scores(self):
        self.assertEqual(okr_validator.expected_score("committed"), 1.0)
        self.assertEqual(okr_validator.expected_score("aspirational"), 0.7)


class TestBackcasting(unittest.TestCase):
    def test_missing_horizon_fails(self):
        rep = backcasting.validate_backcasting({"five_years": "x" * 10})
        self.assertFalse(rep.passed)
        self.assertEqual(len(rep.missing), 4)

    def test_full_passes(self):
        rep = backcasting.validate_backcasting({
            "five_years": "long term goal here",
            "one_year": "short term goal here",
            "next_quarter": "quarter target here",
            "one_week": "week target here",
            "tomorrow": "tomorrow morning step here",
        })
        self.assertTrue(rep.passed)

    def test_extra_key_rejected(self):
        rep = backcasting.validate_backcasting({
            "five_years": "x" * 10, "one_year": "x" * 10,
            "next_quarter": "x" * 10, "one_week": "x" * 10,
            "tomorrow": "x" * 10, "ten_years": "should not be allowed",
        })
        self.assertFalse(rep.passed)


class TestCitations(unittest.TestCase):
    def test_core_references_present(self):
        for k in citations.CORE_REFERENCES:
            rec = citations.get_record(k)
            self.assertIn("citation", rec)
            self.assertIn("source_urls", rec)

    def test_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            citations.get_record("DEFINITELY_NOT_REGISTERED")


class TestRouter(unittest.TestCase):
    def test_type_d(self):
        d = input_router.route("내일 아침 첫 한 걸음만 잡아주세요")
        self.assertEqual(d.input_type, "D")

    def test_type_c_via_flag(self):
        d = input_router.route("OKR 변환 부탁", has_ltg_stg=True)
        self.assertEqual(d.input_type, "C")

    def test_type_b_via_flag(self):
        d = input_router.route("도와주세요", vision_clarity_output=True)
        self.assertEqual(d.input_type, "B")

    def test_type_a_default(self):
        d = input_router.route("비전을 목표로")
        self.assertEqual(d.input_type, "A")


class TestRunIntegration(unittest.TestCase):
    def test_full_workbook(self):
        payload = {
            "today_iso": "2026-05-17",
            "user_text": "비전을 목표로",
            "inspiration_quote": "X 영역에서 Y를 통해 Z를 이루다",
            "smart_goal": "2027-12-31까지 책 1권 출간",
            "smart_resources": "주 10시간",
            "smart_vision_link": "비전 1차 결실",
            "backcasting": {
                "five_years": "책 5권 강연 50회",
                "one_year": "책 1권 출간",
                "next_quarter": "골격 완성",
                "one_week": "1장 보강",
                "tomorrow": "골격 30분 검토",
            },
            "okr": {
                "objective": "1권 출간",
                "key_results": [
                    "Q1 골격 6장",
                    "Q2 12장 초고",
                    "Q3 출판사 계약",
                ],
                "okr_type": "aspirational",
            },
            "first_step": {
                "what": "검토", "when": "06:30", "where": "서재",
                "how": "노션", "why": "보강 식별",
            },
        }
        out = run.run(payload)
        self.assertEqual(out["errors"], [])
        self.assertIsNotNone(out["workbook_markdown"])
        # 워크북에 모든 핵심 인용이 등장하는지
        wb = out["workbook_markdown"]
        for key_name in citations.CORE_REFERENCES:
            self.assertIn(key_name, wb)


if __name__ == "__main__":
    unittest.main()
