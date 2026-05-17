"""
vision-progress-review 결정론 라이브러리 단위 테스트.

실행:
  python3 -m unittest tests.test_progress_review -v
또는:
  python3 tests/test_progress_review.py
"""
from __future__ import annotations

import json
import os
import sys
import unittest
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from scripts.progress_review import (  # noqa: E402
    AchievementVerdict,
    FormCompleteness,
    MissPatternVerdict,
    OKRVerdict,
    PivotDecision,
    Recommendation,
    PROGRESS_SOURCES,
    all_citations_block,
    auto_recommend,
    categorize_achievement,
    categorize_okr,
    check_forbidden_statements,
    completion_rate,
    detect_miss_pattern,
    first_sunday_of_month,
    fmt,
    format_citation,
    is_in_annual_window,
    iso_week_label,
    last_friday_of_month,
    last_week_monday_of_quarter,
    lookup_source,
    next_check_date,
    next_check_schedule_block,
    parse_date,
    pivot_trigger_check,
    quarter_end_date,
    quarter_of,
    render_annual_form,
    render_monthly_form,
    render_oneoff_form,
    render_quarterly_form,
    render_weekly_form,
    validate_form_completion,
)


class TestSources(unittest.TestCase):
    def test_all_sources_have_required_keys(self):
        for k, v in PROGRESS_SOURCES.items():
            self.assertEqual(v["key"], k)
            self.assertIn("author", v)
            self.assertIn("year", v)
            self.assertIn("title", v)
            self.assertTrue(v["verified"])

    def test_lookup_unknown_raises(self):
        with self.assertRaises(KeyError):
            lookup_source("nonexistent_2099")

    def test_format_citation_has_author_year_title(self):
        for k in PROGRESS_SOURCES:
            s = format_citation(k)
            self.assertIn(PROGRESS_SOURCES[k]["author"], s)
            self.assertIn(str(PROGRESS_SOURCES[k]["year"]), s)
            self.assertIn(PROGRESS_SOURCES[k]["title"], s)

    def test_all_citations_block_includes_every_source(self):
        block = all_citations_block()
        for k in PROGRESS_SOURCES:
            self.assertIn(k, block)

    def test_doran_smart_letters_complete(self):
        doran = lookup_source("doran_1981")
        self.assertEqual(set(doran["smart_letters"].keys()),
                         {"S", "M", "A", "R", "T"})

    def test_doerr_okr_bands_have_three(self):
        doerr = lookup_source("doerr_2018")
        self.assertEqual(len(doerr["okr_scoring_bands"]), 3)


class TestParseDate(unittest.TestCase):
    def test_valid_iso(self):
        self.assertEqual(parse_date("2026-05-17"), date(2026, 5, 17))

    def test_invalid_format(self):
        for bad in ["2026/05/17", "26-05-17", "May 17 2026", "", "2026-5-17"]:
            with self.assertRaises(ValueError):
                parse_date(bad)

    def test_invalid_calendar(self):
        with self.assertRaises(ValueError):
            parse_date("2026-02-30")

    def test_non_string(self):
        with self.assertRaises(ValueError):
            parse_date(20260517)  # type: ignore


class TestNextCheckDate(unittest.TestCase):
    def test_weekly_plus_7(self):
        self.assertEqual(next_check_date(date(2026, 5, 17), "weekly"),
                         date(2026, 5, 24))

    def test_monthly_plus_28(self):
        self.assertEqual(next_check_date(date(2026, 5, 17), "monthly"),
                         date(2026, 6, 14))

    def test_quarterly_plus_90(self):
        self.assertEqual(next_check_date(date(2026, 5, 17), "quarterly"),
                         date(2026, 8, 15))

    def test_annual_plus_365(self):
        self.assertEqual(next_check_date(date(2026, 5, 17), "annual"),
                         date(2027, 5, 17))

    def test_leap_year_handling(self):
        # 2024-02-29 + 365 = 2025-02-28
        self.assertEqual(next_check_date(date(2024, 2, 29), "annual"),
                         date(2025, 2, 28))

    def test_unknown_unit(self):
        with self.assertRaises(ValueError):
            next_check_date(date(2026, 5, 17), "decadal")


class TestScheduleBlock(unittest.TestCase):
    def test_weekly_only_weekly(self):
        b = next_check_schedule_block(date(2026, 5, 17), "weekly")
        self.assertIn("주간 점검: 2026-05-24", b)
        self.assertNotIn("월간 점검", b)

    def test_monthly_includes_weekly(self):
        b = next_check_schedule_block(date(2026, 5, 17), "monthly")
        self.assertIn("주간 점검: 2026-05-24", b)
        self.assertIn("월간 점검: 2026-06-14", b)
        self.assertNotIn("분기 점검", b)

    def test_quarterly_includes_lower(self):
        b = next_check_schedule_block(date(2026, 5, 17), "quarterly")
        self.assertIn("주간 점검: 2026-05-24", b)
        self.assertIn("월간 점검: 2026-06-14", b)
        self.assertIn("분기 점검: 2026-08-15", b)
        self.assertNotIn("연간 점검", b)

    def test_annual_includes_all(self):
        b = next_check_schedule_block(date(2026, 5, 17), "annual")
        for x in ["주간 점검: 2026-05-24",
                  "월간 점검: 2026-06-14",
                  "분기 점검: 2026-08-15",
                  "연간 점검: 2027-05-17"]:
            self.assertIn(x, b)


class TestCategorizeAchievement(unittest.TestCase):
    def test_above_80(self):
        for r in [80.0, 85.0, 99.9, 100.0]:
            v = categorize_achievement(r)
            self.assertEqual(v.symbol, "✓")

    def test_between_50_and_80(self):
        for r in [50.0, 65.0, 79.99]:
            v = categorize_achievement(r)
            self.assertEqual(v.symbol, "△")

    def test_below_50(self):
        for r in [0.0, 25.0, 49.99]:
            v = categorize_achievement(r)
            self.assertEqual(v.symbol, "✗")

    def test_out_of_range_raises(self):
        for bad in [-1, 100.01, 150]:
            with self.assertRaises(ValueError):
                categorize_achievement(bad)


class TestCategorizeOKR(unittest.TestCase):
    def test_red_band(self):
        for s in [0.0, 0.15, 0.39]:
            v = categorize_okr(s)
            self.assertEqual(v.band, "red")

    def test_yellow_band(self):
        for s in [0.4, 0.55, 0.69]:
            v = categorize_okr(s)
            self.assertEqual(v.band, "yellow")

    def test_green_band(self):
        for s in [0.7, 0.8, 1.0]:
            v = categorize_okr(s)
            self.assertEqual(v.band, "green")

    def test_too_easy_warning(self):
        v = categorize_okr(0.98)
        self.assertTrue(v.too_easy_warning)
        v = categorize_okr(0.7)
        self.assertFalse(v.too_easy_warning)

    def test_out_of_range(self):
        for bad in [-0.1, 1.01, 2.0]:
            with self.assertRaises(ValueError):
                categorize_okr(bad)


class TestPivotTrigger(unittest.TestCase):
    def test_kpi_above_50_no_trigger(self):
        v = pivot_trigger_check(60.0, "hypothesis")
        self.assertFalse(v.trigger)
        self.assertEqual(v.reason_code, "ok")

    def test_kpi_below_50_execution_no_pivot(self):
        v = pivot_trigger_check(30.0, "execution")
        self.assertFalse(v.trigger)
        self.assertEqual(v.reason_code, "execution_gap")

    def test_kpi_below_50_hypothesis_triggers(self):
        v = pivot_trigger_check(30.0, "hypothesis")
        self.assertTrue(v.trigger)
        self.assertEqual(v.reason_code, "hypothesis_fail")

    def test_kpi_below_50_external_triggers(self):
        v = pivot_trigger_check(30.0, "external")
        self.assertTrue(v.trigger)
        self.assertEqual(v.reason_code, "external_variable")

    def test_kpi_below_50_unknown_triggers_with_request(self):
        v = pivot_trigger_check(30.0, "unknown")
        self.assertTrue(v.trigger)
        self.assertEqual(v.reason_code, "unknown_cause")

    def test_invalid_cause(self):
        with self.assertRaises(ValueError):
            pivot_trigger_check(30.0, "vibes")


class TestAutoRecommend(unittest.TestCase):
    def test_overdue_largest_unit_wins(self):
        last = {
            "weekly": "2026-05-08",     # 9일 전 → overdue 2일
            "monthly": "2026-04-01",    # 46일 전 → overdue 18일
            "quarterly": "2026-02-01",  # 105일 전 → overdue 15일
            "annual": "2024-12-01",     # 약 532일 → overdue
        }
        v = auto_recommend(last, today="2026-05-17")
        self.assertEqual(v.recommended_unit, "annual")

    def test_no_overdue(self):
        last = {
            "weekly": "2026-05-14",      # 3일 전 → 미도래
            "monthly": "2026-05-01",     # 16일 전 → 미도래
            "quarterly": "2026-04-01",   # 46일 전 → 미도래
            "annual": "2026-01-01",      # 136일 전 → 미도래
        }
        v = auto_recommend(last, today="2026-05-17")
        self.assertIsNone(v.recommended_unit)
        self.assertGreater(len(v.upcoming_units), 0)

    def test_december_window_annual(self):
        last = {
            "weekly": "2026-12-01",
            "monthly": "2026-11-15",
            "quarterly": "2026-10-01",
            "annual": None,
        }
        v = auto_recommend(last, today="2026-12-20")
        self.assertEqual(v.recommended_unit, "annual")

    def test_only_weekly_overdue(self):
        last = {
            "weekly": "2026-05-08",
            "monthly": "2026-05-01",
            "quarterly": "2026-04-01",
            "annual": "2026-01-01",
        }
        v = auto_recommend(last, today="2026-05-17")
        self.assertEqual(v.recommended_unit, "weekly")

    def test_future_date_rejected(self):
        with self.assertRaises(ValueError):
            auto_recommend({"weekly": "2099-01-01"}, today="2026-05-17")


class TestMissPattern(unittest.TestCase):
    def test_zero_consecutive(self):
        v = detect_miss_pattern([True, True, False])
        self.assertEqual(v.consecutive_misses, 0)
        self.assertFalse(v.triggers_4_questions)
        self.assertFalse(v.triggers_never_miss_twice)

    def test_one_consecutive(self):
        v = detect_miss_pattern([False, True])
        self.assertEqual(v.consecutive_misses, 1)
        self.assertFalse(v.triggers_never_miss_twice)

    def test_two_consecutive_triggers_never_miss_twice(self):
        v = detect_miss_pattern([False, True, True])
        self.assertEqual(v.consecutive_misses, 2)
        self.assertTrue(v.triggers_never_miss_twice)
        self.assertFalse(v.triggers_4_questions)

    def test_three_consecutive_triggers_4_questions(self):
        v = detect_miss_pattern([True, True, True])
        self.assertEqual(v.consecutive_misses, 3)
        self.assertTrue(v.triggers_4_questions)
        self.assertTrue(v.triggers_never_miss_twice)

    def test_empty_log(self):
        v = detect_miss_pattern([])
        self.assertEqual(v.consecutive_misses, 0)

    def test_non_bool_raises(self):
        with self.assertRaises(TypeError):
            detect_miss_pattern([1, 0, 1])  # type: ignore


class TestCalendar(unittest.TestCase):
    def test_last_friday_of_may_2026(self):
        # 2026-05-29 is Friday
        self.assertEqual(last_friday_of_month(2026, 5), date(2026, 5, 29))

    def test_last_friday_of_dec_2024(self):
        # 2024-12-27 is Friday
        self.assertEqual(last_friday_of_month(2024, 12), date(2024, 12, 27))

    def test_first_sunday_of_jan_2026(self):
        # 2026-01-04 is Sunday
        self.assertEqual(first_sunday_of_month(2026, 1), date(2026, 1, 4))

    def test_quarter_ends(self):
        self.assertEqual(quarter_end_date(2026, 1), date(2026, 3, 31))
        self.assertEqual(quarter_end_date(2026, 2), date(2026, 6, 30))
        self.assertEqual(quarter_end_date(2026, 3), date(2026, 9, 30))
        self.assertEqual(quarter_end_date(2026, 4), date(2026, 12, 31))

    def test_quarter_of_dates(self):
        self.assertEqual(quarter_of(date(2026, 2, 14)), 1)
        self.assertEqual(quarter_of(date(2026, 5, 17)), 2)
        self.assertEqual(quarter_of(date(2026, 9, 30)), 3)
        self.assertEqual(quarter_of(date(2026, 10, 1)), 4)

    def test_last_week_monday_of_quarter(self):
        # 2026-12-31 is Thursday; that week's Monday = 2026-12-28
        self.assertEqual(last_week_monday_of_quarter(2026, 4), date(2026, 12, 28))

    def test_annual_window(self):
        self.assertTrue(is_in_annual_window(date(2026, 12, 5)))
        self.assertTrue(is_in_annual_window(date(2026, 1, 31)))
        self.assertFalse(is_in_annual_window(date(2026, 7, 1)))


class TestCompletionRate(unittest.TestCase):
    def test_full_completion(self):
        self.assertEqual(completion_rate(10, 10), 100.0)

    def test_partial(self):
        self.assertEqual(completion_rate(3, 4), 75.0)

    def test_zero_planned_returns_zero(self):
        self.assertEqual(completion_rate(0, 0), 0.0)

    def test_completed_exceeds_planned(self):
        with self.assertRaises(ValueError):
            completion_rate(11, 10)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            completion_rate(-1, 5)


class TestRenderForms(unittest.TestCase):
    def test_weekly_form_contains_required_sections(self):
        s = render_weekly_form(date(2026, 5, 17))
        for must in ["주간 점검", "지난 주 완수 현황", "다음 주 핵심 3개",
                     "Never miss twice", "다음 점검 일정"]:
            self.assertIn(must, s)

    def test_monthly_form_has_kpi_and_sscont(self):
        s = render_monthly_form(date(2026, 5, 29))
        self.assertIn("월간 점검 — 2026-05", s)
        self.assertIn("KPI 추이", s)
        self.assertIn("Stop", s)
        self.assertIn("Continue", s)
        self.assertIn("Derby & Larsen", s)  # Polaroid claim 제거 확인

    def test_quarterly_form_has_pivot_check(self):
        s = render_quarterly_form(date(2026, 6, 30))
        self.assertIn("분기 점검 — 2026 Q2", s)
        self.assertIn("Pivot 결정 점검", s)
        self.assertIn("Ries 2011", s)
        self.assertIn("Doerr 2018", s)

    def test_annual_form_has_5year_review(self):
        s = render_annual_form(date(2026, 12, 31))
        self.assertIn("연간 점검 — 2026", s)
        self.assertIn("LTG 궤도 점검", s)
        self.assertIn("5년 궤도 재검토", s)

    def test_oneoff_form_has_required_followup(self):
        s = render_oneoff_form("프로젝트 X 종료")
        self.assertIn("단발 회고", s)
        self.assertIn("다음 대상으로 이어갈 것", s)
        # 단발은 다음 점검 일정 없음
        self.assertNotIn("다음 점검 일정", s)


class TestForbiddenStatements(unittest.TestCase):
    def test_21day_myth_caught(self):
        v = check_forbidden_statements("21일이면 습관이 정착됩니다.")
        self.assertFalse(v["passed"])

    def test_unsourced_statistic_caught(self):
        v = check_forbidden_statements(
            "연구에 따르면 대부분의 사람이 빗나갑니다."
        )
        self.assertFalse(v["passed"])

    def test_sourced_statistic_passes(self):
        v = check_forbidden_statements(
            "연구에 따르면 Lally et al. 2010 평균 66일이 걸렸다."
        )
        self.assertTrue(v["passed"])

    def test_neutral_text_passes(self):
        v = check_forbidden_statements("이번 주 점검을 시작합니다.")
        self.assertTrue(v["passed"])

    def test_keyword_then_pct_caught(self):
        v = check_forbidden_statements("업계 평균 달성률은 75% 입니다.")
        self.assertFalse(v["passed"])

    def test_pct_then_keyword_caught(self):
        v = check_forbidden_statements("75%가 업계 평균 달성률입니다.")
        self.assertFalse(v["passed"])

    def test_unsourced_publication_caught(self):
        v = check_forbidden_statements("발표한 통계에서 80%가 성공했다.")
        self.assertFalse(v["passed"])

    def test_sourced_publication_passes(self):
        v = check_forbidden_statements(
            "Doerr가 발표한 OKR 점수 0.7은 stretch goal의 이상적 목표치다 (Doerr 2018)."
        )
        self.assertTrue(v["passed"])

    def test_population_claim_caught_d10(self):
        # ROUND D — D10 우회 시도
        v = check_forbidden_statements("대부분의 직장인 80% 가 성공합니다.")
        self.assertFalse(v["passed"])

    def test_majority_pct_caught(self):
        v = check_forbidden_statements("대다수의 사람들이 새해 계획의 90%를 포기한다.")
        self.assertFalse(v["passed"])

    def test_sourced_population_passes(self):
        # 출처가 phrase 뒤에 4자리 연도로 명시되면 통과
        v = check_forbidden_statements(
            "연구에 따르면 새해 결심자의 일부만 유지된다 (Norcross 2002)."
        )
        self.assertTrue(v["passed"])


class TestFormCompletion(unittest.TestCase):
    def test_empty_placeholders_detected(self):
        text = """## 주간 점검
- 완수: ___
- 핵심: ...
"""
        v = validate_form_completion(text)
        self.assertGreater(v.unfilled_count, 0)

    def test_filled_text_passes(self):
        text = "## 주간 점검\n- 완수: 책 1장 작성\n- 핵심: 강의안 수정"
        v = validate_form_completion(text)
        self.assertEqual(v.unfilled_count, 0)


class TestIntegration(unittest.TestCase):
    """SKILL.md 시나리오 → 결정론 호출 통합 확인."""

    def test_quarterly_flow_kpi_55_yellow_band(self):
        ach = categorize_achievement(55.0)
        self.assertEqual(ach.symbol, "△")
        okr = categorize_okr(0.55)
        self.assertEqual(okr.band, "yellow")
        pivot = pivot_trigger_check(55.0, "hypothesis")
        self.assertFalse(pivot.trigger)  # KPI > 50%

    def test_full_pivot_scenario(self):
        # KPI 35%, 가설 자체 문제 → Pivot 검토 + STG 재설계
        v = pivot_trigger_check(35.0, "hypothesis")
        self.assertTrue(v.trigger)
        self.assertIn("STG 재설계", v.next_action)

    def test_three_week_miss_triggers_full_response(self):
        # 3주 연속 미달 → 4질문 발동 + Never miss twice 경고도 같이
        v = detect_miss_pattern([False, True, True, True])
        self.assertTrue(v.triggers_4_questions)
        self.assertTrue(v.triggers_never_miss_twice)


if __name__ == "__main__":
    unittest.main(verbosity=2)
