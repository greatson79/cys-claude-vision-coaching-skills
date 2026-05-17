"""
vision-readiness-visioncoding 결정론 엔진 단위 테스트.

검증 범위:
  - 파싱 (5종 입력 형식)
  - 범위·누락 검증
  - 평균·composite 산출
  - 레벨 매핑 + next_level_hint
  - ASCII partial block 매핑 (SKILL.md 표 1:1 검산)
  - Mermaid 차트 형식
  - 강점·성장 영역 분류 경계값 (7.0 / 6.9)
  - 처방 스킬 매핑
  - 변화 추적 (재진단)
  - 한 줄 요약 형식
  - 통합 process() 파이프라인
  - 예외 케이스 (빈 입력·범위 위반·누락 등)
"""

import os
import sys
import json
import unittest
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lib"))

import readiness_engine as re_eng
from readiness_engine import (
    parse_scores,
    validate_range,
    validate_completeness,
    validate_all,
    calculate_skill_scores,
    calculate_composite,
    level_for,
    next_level_hint,
    classify_strengths,
    prescriptions_for,
    partial_block_for,
    render_ascii_bar,
    render_ascii_chart,
    render_mermaid_chart,
    one_line_summary,
    compute_delta,
    render_minimal_summary,
    process,
    ReadinessError,
    NUM_QUESTIONS,
    SKILL_NAMES_EN,
    PARTIAL_BLOCK_TABLE,
)


def full_scores_dict(value: int = 5) -> dict[int, int]:
    return {i: value for i in range(1, NUM_QUESTIONS + 1)}


class TestParsing(unittest.TestCase):

    def test_official_qNN_format(self):
        raw = "\n".join(f"Q{i:02d}: {i % 11}" for i in range(1, 21))
        result = parse_scores(raw)
        self.assertEqual(len(result), 20)
        for i in range(1, 21):
            self.assertEqual(result[i], i % 11)

    def test_comma_separated_20(self):
        raw = ", ".join(str(i % 11) for i in range(1, 21))
        result = parse_scores(raw)
        self.assertEqual(len(result), 20)
        for i in range(1, 21):
            self.assertEqual(result[i], i % 11)

    def test_korean_natural(self):
        raw = ", ".join(f"{i}번 {i % 11}점" for i in range(1, 21))
        result = parse_scores(raw)
        self.assertEqual(len(result), 20)
        self.assertEqual(result[5], 5)
        self.assertEqual(result[15], 4)

    def test_newline_separated(self):
        raw = "\n".join(str(i % 11) for i in range(1, 21))
        result = parse_scores(raw)
        self.assertEqual(len(result), 20)

    def test_q_no_zero_pad(self):
        raw = "\n".join(f"Q{i}: {i % 11}" for i in range(1, 21))
        result = parse_scores(raw)
        self.assertEqual(len(result), 20)

    def test_empty_input_raises(self):
        with self.assertRaises(ReadinessError):
            parse_scores("")
        with self.assertRaises(ReadinessError):
            parse_scores("   ")

    def test_no_digits_raises(self):
        with self.assertRaises(ReadinessError):
            parse_scores("abc def")

    def test_ambiguous_count_raises(self):
        # 명시 매핑 없음 + 숫자 19개 → 모호
        raw = ", ".join(str(i % 11) for i in range(1, 20))  # 19개만
        with self.assertRaises(ReadinessError):
            parse_scores(raw)

    def test_conflicting_duplicate(self):
        # Q01에 두 번 다른 점수
        raw = "Q01: 5, Q02: 7, Q03: 3, Q04: 4, Q05: 5, Q01: 9"
        with self.assertRaises(ReadinessError):
            parse_scores(raw)


class TestValidation(unittest.TestCase):

    def test_range_ok(self):
        validate_range(full_scores_dict(7))

    def test_range_negative(self):
        d = full_scores_dict(5)
        d[3] = -1
        with self.assertRaises(ReadinessError) as ctx:
            validate_range(d)
        self.assertIn("Q03", str(ctx.exception))

    def test_range_over(self):
        d = full_scores_dict(5)
        d[10] = 11
        with self.assertRaises(ReadinessError):
            validate_range(d)

    def test_completeness_missing(self):
        d = full_scores_dict(5)
        del d[7]
        del d[15]
        with self.assertRaises(ReadinessError) as ctx:
            validate_completeness(d)
        msg = str(ctx.exception)
        self.assertIn("Q07", msg)
        self.assertIn("Q15", msg)

    def test_completeness_extra(self):
        d = full_scores_dict(5)
        d[21] = 5
        with self.assertRaises(ReadinessError):
            validate_completeness(d)


class TestAveraging(unittest.TestCase):

    def test_all_fives(self):
        d = full_scores_dict(5)
        scores = calculate_skill_scores(d)
        for sk in scores:
            self.assertEqual(sk.score, 5.0)

    def test_example_from_skill_md(self):
        # SKILL.md 예시: BP=7.4, RG=6.2, CS=5.0, FT=8.0
        # 적당한 분배: BP 합 37 (7+8+7+8+7), RG 합 31 (6+6+7+6+6), CS 25, FT 40
        d = {}
        bp = [7, 8, 7, 8, 7]
        rg = [6, 6, 7, 6, 6]
        cs = [5, 5, 5, 5, 5]
        ft = [8, 8, 8, 8, 8]
        for i, v in enumerate(bp, start=1):
            d[i] = v
        for i, v in enumerate(rg, start=6):
            d[i] = v
        for i, v in enumerate(cs, start=11):
            d[i] = v
        for i, v in enumerate(ft, start=16):
            d[i] = v
        scores = calculate_skill_scores(d)
        self.assertAlmostEqual(scores[0].score, 7.4)
        self.assertAlmostEqual(scores[1].score, 6.2)
        self.assertAlmostEqual(scores[2].score, 5.0)
        self.assertAlmostEqual(scores[3].score, 8.0)
        comp = calculate_composite(scores)
        # (7.4+6.2+5.0+8.0)/4 = 6.65
        self.assertAlmostEqual(comp, 6.65, places=2)

    def test_zero_and_ten(self):
        d = full_scores_dict(0)
        for q in range(1, 6):  # BP 모두 10
            d[q] = 10
        scores = calculate_skill_scores(d)
        self.assertEqual(scores[0].score, 10.0)
        self.assertEqual(scores[1].score, 0.0)


class TestLevelMapping(unittest.TestCase):

    def test_each_integer(self):
        expected = {
            0: "Not Yet", 1: "Very Weak", 2: "Weak", 3: "Poor",
            4: "Developing", 5: "Average", 6: "Solid", 7: "Above Average",
            8: "Strong", 9: "Exceptional", 10: "World Class",
        }
        for i, label in expected.items():
            actual, _ = level_for(float(i))
            self.assertEqual(actual, label, f"점수 {i}")

    def test_decimal_truncation(self):
        # 7.4 → 정수부 7 → Above Average
        self.assertEqual(level_for(7.4)[0], "Above Average")
        self.assertEqual(level_for(7.9)[0], "Above Average")
        self.assertEqual(level_for(8.0)[0], "Strong")

    def test_next_level_hint(self):
        # 소수부 ≥ 0.5만 다음 단계 부기
        self.assertIsNone(next_level_hint(7.4))
        self.assertEqual(next_level_hint(7.5), "Strong")
        self.assertIsNone(next_level_hint(7.0))
        self.assertIsNone(next_level_hint(10.0))  # 더 위 없음
        self.assertEqual(next_level_hint(6.65), "Above Average")

    def test_out_of_range_raises(self):
        with self.assertRaises(ReadinessError):
            level_for(11.0)
        with self.assertRaises(ReadinessError):
            level_for(-0.1)


class TestClassification(unittest.TestCase):

    def test_seven_is_strength(self):
        # 점수 7.0 정확히는 강점
        d = full_scores_dict(7)
        scores = calculate_skill_scores(d)
        cls = classify_strengths(scores)
        self.assertEqual(len(cls["strengths"]), 4)
        self.assertEqual(len(cls["growth_areas"]), 0)

    def test_six_nine_is_growth(self):
        # 6.9는 성장
        d = full_scores_dict(7)
        # BP만 6.9 만들기: 합 34.5는 정수 불가 — 합 = 35로 7.0, 33 → 6.6, 34 → 6.8, 35 → 7.0
        # 6.9 만들기 불가능하므로 6.8로 검사
        for q in range(1, 6):
            d[q] = [7, 7, 7, 7, 7][q - 1]  # 합 35 → 7.0
        # 합 34 → 6.8
        d[1] = 6
        scores = calculate_skill_scores(d)
        self.assertAlmostEqual(scores[0].score, 6.8)
        cls = classify_strengths(scores)
        # BP는 성장 영역, 나머지는 강점
        growth_names = [s.name_en for s in cls["growth_areas"]]
        self.assertIn("Big Picture", growth_names)
        self.assertEqual(len(cls["strengths"]), 3)


class TestPrescriptions(unittest.TestCase):

    def test_no_growth_no_prescriptions(self):
        d = full_scores_dict(9)
        scores = calculate_skill_scores(d)
        self.assertEqual(prescriptions_for(scores), [])

    def test_weakest_first(self):
        d = full_scores_dict(8)
        # BP 합 = 10 → 2.0
        for q in range(1, 6):
            d[q] = 2
        # RG 합 = 25 → 5.0
        for q in range(6, 11):
            d[q] = 5
        scores = calculate_skill_scores(d)
        pres = prescriptions_for(scores)
        # BP(2.0)이 가장 약함 → 1순위
        self.assertEqual(pres[0]["skill_en"], "Big Picture")
        self.assertEqual(pres[0]["prescriptions"][0], "vision-future-needs-prediction")
        self.assertEqual(pres[1]["skill_en"], "Reframing Goals")


class TestAsciiChart(unittest.TestCase):

    def test_partial_block_each_bucket(self):
        # SKILL.md 표 1:1 검산
        cases = [
            (0.00, "░"), (0.062, "░"),
            (0.063, "▏"), (0.187, "▏"),
            (0.188, "▎"), (0.312, "▎"),
            (0.313, "▍"), (0.437, "▍"),
            (0.438, "▌"), (0.562, "▌"),
            (0.563, "▋"), (0.687, "▋"),
            (0.688, "▊"), (0.812, "▊"),
            (0.813, "▉"), (0.937, "▉"),
            (0.938, "█"), (1.000, "█"),
        ]
        for val, expected in cases:
            actual = partial_block_for(val)
            self.assertEqual(actual, expected, f"val={val} 기대={expected} 실제={actual}")

    def test_render_bar_examples(self):
        # SKILL.md 예시
        # 7.4 → 7 full + 0.4 partial(▍) + 2 empty
        b = render_ascii_bar(7.4)
        self.assertEqual(b, "███████▍░░")
        # 6.2 → 6 full + ▎ + 3 empty
        b = render_ascii_bar(6.2)
        self.assertEqual(b, "██████▎░░░")
        # 5.0 → 5 full + ░ + 4 empty (정확히 정수 → partial=0 → ░ 한 칸)
        b = render_ascii_bar(5.0)
        self.assertEqual(b, "█████░░░░░")
        # 8.0
        b = render_ascii_bar(8.0)
        self.assertEqual(b, "████████░░")
        # 0.0
        b = render_ascii_bar(0.0)
        self.assertEqual(b, "░░░░░░░░░░")
        # 10.0
        b = render_ascii_bar(10.0)
        self.assertEqual(b, "██████████")

    def test_render_chart_includes_all_skills(self):
        d = full_scores_dict(7)
        scores = calculate_skill_scores(d)
        chart = render_ascii_chart(scores)
        for name in SKILL_NAMES_EN:
            self.assertIn(name, chart)
        self.assertIn("Vision Readiness Profile", chart)
        self.assertIn("X-Axis", chart)
        self.assertIn("Y-Axis", chart)

    def test_bar_out_of_range_raises(self):
        with self.assertRaises(ReadinessError):
            render_ascii_bar(11.0)
        with self.assertRaises(ReadinessError):
            render_ascii_bar(-0.5)


class TestMermaid(unittest.TestCase):

    def test_mermaid_format(self):
        d = full_scores_dict(6)
        scores = calculate_skill_scores(d)
        m = render_mermaid_chart(scores)
        self.assertIn("xychart-beta", m)
        self.assertIn('"Big Picture"', m)
        self.assertIn("```mermaid", m)
        self.assertIn("```", m.split("\n", 1)[1])
        self.assertIn("bar [6.0, 6.0, 6.0, 6.0]", m)


class TestSummary(unittest.TestCase):

    def test_one_line_format(self):
        d = full_scores_dict(7)
        scores = calculate_skill_scores(d)
        comp = calculate_composite(scores)
        line = one_line_summary(scores, comp, when=date(2026, 5, 17))
        self.assertEqual(line, "2026-05-17 | BP 7.0 / RG 7.0 / CS 7.0 / FT 7.0 / Composite 7.00")

    def test_minimal_summary(self):
        d = full_scores_dict(5)
        for q in range(1, 6):  # BP 모두 9
            d[q] = 9
        for q in range(16, 21):  # FT 모두 2
            d[q] = 2
        scores = calculate_skill_scores(d)
        comp = calculate_composite(scores)
        s = render_minimal_summary(scores, comp)
        self.assertIn("Big Picture", s)
        self.assertIn("Following Through", s)
        self.assertIn("vision-follow-through-habits", s)


class TestDelta(unittest.TestCase):

    def test_compute_delta(self):
        d = full_scores_dict(6)
        scores = calculate_skill_scores(d)
        prev = {"BP": 5.0, "RG": 7.0, "CS": 6.0}
        delta = compute_delta(scores, prev)
        self.assertEqual(delta["Big Picture"]["delta"], 1.0)
        self.assertEqual(delta["Big Picture"]["direction"], "↑")
        self.assertEqual(delta["Reframing Goals"]["delta"], -1.0)
        self.assertEqual(delta["Reframing Goals"]["direction"], "↓")
        self.assertEqual(delta["Creating Strategies"]["delta"], 0.0)
        self.assertEqual(delta["Creating Strategies"]["direction"], "→")
        self.assertNotIn("Following Through", delta)  # prev에 없음


class TestProcess(unittest.TestCase):

    def test_full_pipeline(self):
        raw = ", ".join("7" for _ in range(20))
        result = process(raw)
        self.assertEqual(len(result["skill_scores"]), 4)
        self.assertEqual(result["composite"], 7.0)
        self.assertEqual(len(result["classify"]["strengths"]), 4)
        self.assertEqual(result["prescriptions"], [])
        self.assertIn("Vision Readiness Profile", result["ascii_chart"])

    def test_full_pipeline_skill_md_example(self):
        # SKILL.md 예시 7.4 / 6.2 / 5.0 / 8.0
        parts = []
        for v in [7, 8, 7, 8, 7]:  # BP 7.4
            parts.append(str(v))
        for v in [6, 6, 7, 6, 6]:  # RG 6.2
            parts.append(str(v))
        for v in [5, 5, 5, 5, 5]:  # CS 5.0
            parts.append(str(v))
        for v in [8, 8, 8, 8, 8]:  # FT 8.0
            parts.append(str(v))
        result = process(", ".join(parts))
        scores = result["skill_scores"]
        self.assertAlmostEqual(scores[0].score, 7.4)
        self.assertAlmostEqual(scores[1].score, 6.2)
        self.assertAlmostEqual(scores[2].score, 5.0)
        self.assertAlmostEqual(scores[3].score, 8.0)
        self.assertAlmostEqual(result["composite"], 6.65, places=2)
        # 강점: BP(7.4), FT(8.0). 성장: RG(6.2), CS(5.0)
        strong_names = [s.name_en for s in result["classify"]["strengths"]]
        self.assertIn("Big Picture", strong_names)
        self.assertIn("Following Through", strong_names)
        self.assertEqual(len(strong_names), 2)
        # 처방: CS(5.0)가 가장 약함 → 1순위
        self.assertEqual(result["prescriptions"][0]["skill_en"], "Creating Strategies")


class TestProcessMeans(unittest.TestCase):

    def test_means_basic(self):
        from readiness_engine import process_means
        r = process_means(6.2, 5.8, 4.9, 7.1)
        self.assertEqual(r["input_mode"], "means_only")
        self.assertIn("audience_note", r)
        self.assertEqual(r["skill_scores"][0].score, 6.2)
        self.assertEqual(r["skill_scores"][3].score, 7.1)
        self.assertAlmostEqual(r["composite"], 6.0, places=2)
        # raw_items 빈 리스트
        for sk in r["skill_scores"]:
            self.assertEqual(sk.raw_items, [])

    def test_means_range_violation(self):
        from readiness_engine import process_means
        with self.assertRaises(ReadinessError):
            process_means(11.0, 5.0, 5.0, 5.0)
        with self.assertRaises(ReadinessError):
            process_means(5.0, -1.0, 5.0, 5.0)


if __name__ == "__main__":
    unittest.main()
