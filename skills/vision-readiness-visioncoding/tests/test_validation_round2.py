"""
ROUND 2 검증 — 10개 임의 시나리오. 이전 단위 테스트와 *전혀 다른* 패턴.

목표: 결정론 엔진 + SKILL.md 흐름이 100% 정확하게 작동하는지 입증.
각 시나리오는 입력·기대 산출·검증 항목을 모두 명시. 자동 assertion.
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "lib"))

from readiness_engine import (
    process,
    parse_scores,
    validate_all,
    calculate_skill_scores,
    calculate_composite,
    level_for,
    next_level_hint,
    classify_strengths,
    prescriptions_for,
    render_ascii_bar,
    render_ascii_chart,
    render_mermaid_chart,
    one_line_summary,
    compute_delta,
    ReadinessError,
)


class TestScenario01_PerfectBalance(unittest.TestCase):
    """시나리오 1: 모든 능력 7.0 균등. 강점 4개, 성장 0개."""

    def test_balanced(self):
        raw = ", ".join("7" for _ in range(20))
        result = process(raw)
        for sk in result["skill_scores"]:
            self.assertEqual(sk.score, 7.0)
        self.assertEqual(result["composite"], 7.0)
        self.assertEqual(len(result["classify"]["strengths"]), 4)
        self.assertEqual(len(result["classify"]["growth_areas"]), 0)
        self.assertEqual(len(result["prescriptions"]), 0)
        for ls in result["level_summary"]:
            self.assertEqual(ls["level"], "Above Average")
            self.assertIsNone(ls["next_hint"])  # 7.0은 정확히 정수, 소수부 0


class TestScenario02_VisionaryDreamer(unittest.TestCase):
    """시나리오 2: BP만 높음(9.4) 나머지 낮음(2~3) — 큰 그림은 보이지만 실행 없음."""

    def test_dreamer_pattern(self):
        bp = [9, 10, 9, 10, 9]  # 합 47 → 9.4
        rg = [3, 3, 2, 3, 3]    # 합 14 → 2.8
        cs = [2, 3, 2, 3, 2]    # 합 12 → 2.4
        ft = [2, 2, 3, 2, 2]    # 합 11 → 2.2
        raw = ", ".join(str(x) for x in bp + rg + cs + ft)
        result = process(raw)
        self.assertAlmostEqual(result["skill_scores"][0].score, 9.4)
        self.assertAlmostEqual(result["skill_scores"][1].score, 2.8)
        self.assertAlmostEqual(result["skill_scores"][2].score, 2.4)
        self.assertAlmostEqual(result["skill_scores"][3].score, 2.2)
        # 강점: BP만. 나머지 3개는 성장.
        self.assertEqual(len(result["classify"]["strengths"]), 1)
        self.assertEqual(result["classify"]["strengths"][0].name_en, "Big Picture")
        # 가장 약한 처방 첫번째: FT(2.2)
        self.assertEqual(result["prescriptions"][0]["skill_en"], "Following Through")
        self.assertEqual(
            result["prescriptions"][0]["prescriptions"][0],
            "vision-follow-through-habits",
        )


class TestScenario03_LaborerPattern(unittest.TestCase):
    """시나리오 3: FT만 높음(10.0) 나머지 낮음 — 묵묵히 일하지만 방향 없는 패턴."""

    def test_laborer(self):
        bp = [1, 2, 1, 2, 1]  # 합 7 → 1.4
        rg = [2, 1, 2, 1, 2]  # 합 8 → 1.6
        cs = [3, 2, 3, 2, 3]  # 합 13 → 2.6
        ft = [10, 10, 10, 10, 10]  # 합 50 → 10.0
        raw = ", ".join(str(x) for x in bp + rg + cs + ft)
        result = process(raw)
        self.assertAlmostEqual(result["skill_scores"][0].score, 1.4)
        self.assertAlmostEqual(result["skill_scores"][3].score, 10.0)
        # FT 레벨: World Class
        ft_ls = [ls for ls in result["level_summary"] if ls["skill_en"] == "Following Through"][0]
        self.assertEqual(ft_ls["level"], "World Class")
        # BP 가장 약함이 아님 — BP=1.4, RG=1.6, CS=2.6
        # 가장 약한 것은 BP(1.4)
        self.assertEqual(result["prescriptions"][0]["skill_en"], "Big Picture")
        self.assertEqual(result["prescriptions"][0]["prescriptions"][0], "vision-future-needs-prediction")


class TestScenario04_RangeViolation(unittest.TestCase):
    """시나리오 4: 점수 -2, 11 포함 → ReadinessError."""

    def test_negative_score(self):
        raw = "Q01: -2, Q02: 5, Q03: 7, Q04: 4, Q05: 6, Q06: 5, Q07: 5, Q08: 5, Q09: 5, Q10: 5, Q11: 5, Q12: 5, Q13: 5, Q14: 5, Q15: 5, Q16: 5, Q17: 5, Q18: 5, Q19: 5, Q20: 5"
        with self.assertRaises(ReadinessError) as ctx:
            process(raw)
        self.assertIn("Q01", str(ctx.exception))

    def test_over_ten(self):
        raw = ", ".join(["5"] * 19 + ["11"])
        with self.assertRaises(ReadinessError) as ctx:
            process(raw)
        self.assertIn("Q20", str(ctx.exception))


class TestScenario05_MissingQuestions(unittest.TestCase):
    """시나리오 5: Q07·Q15·Q19 누락 → 정확한 누락 보고."""

    def test_missing(self):
        # Q01~Q20 중 7, 15, 19 누락
        parts = []
        for q in range(1, 21):
            if q in (7, 15, 19):
                continue
            parts.append(f"Q{q:02d}: 6")
        raw = ", ".join(parts)
        with self.assertRaises(ReadinessError) as ctx:
            process(raw)
        msg = str(ctx.exception)
        self.assertIn("Q07", msg)
        self.assertIn("Q15", msg)
        self.assertIn("Q19", msg)


class TestScenario06_ExtraQuestion(unittest.TestCase):
    """시나리오 6: Q21 추가 → 범위 밖 번호 보고."""

    def test_extra(self):
        parts = [f"Q{q:02d}: 5" for q in range(1, 22)]  # Q01~Q21
        raw = ", ".join(parts)
        with self.assertRaises(ReadinessError) as ctx:
            process(raw)
        self.assertIn("Q21", str(ctx.exception))


class TestScenario07_KoreanNaturalMixed(unittest.TestCase):
    """시나리오 7: '1번 8점, 2번 7점' 한국어 자연어 + 콤마."""

    def test_korean_natural(self):
        raw = ", ".join(f"{i}번 {(i % 9) + 1}점" for i in range(1, 21))
        result = process(raw)
        self.assertEqual(len(result["skill_scores"]), 4)
        # 점수 계산: i%9+1: 1→2, 2→3, ..., 8→9, 9→1, 10→2, ..., 20→3
        # BP=Q1~Q5: 2,3,4,5,6 합 20 → 4.0
        # RG=Q6~Q10: 7,8,9,1,2 합 27 → 5.4
        # CS=Q11~Q15: 3,4,5,6,7 합 25 → 5.0
        # FT=Q16~Q20: 8,9,1,2,3 합 23 → 4.6
        self.assertAlmostEqual(result["skill_scores"][0].score, 4.0)
        self.assertAlmostEqual(result["skill_scores"][1].score, 5.4)
        self.assertAlmostEqual(result["skill_scores"][2].score, 5.0)
        self.assertAlmostEqual(result["skill_scores"][3].score, 4.6)


class TestScenario08_QPrefixNoPad(unittest.TestCase):
    """시나리오 8: Q1~Q20 (zero-pad 없이)."""

    def test_q_no_pad(self):
        raw = "\n".join(f"Q{i}: {(i % 5) + 4}" for i in range(1, 21))
        # 점수: i%5+1: 1→5, 2→6, 3→7, 4→8, 5→4, 6→5, ...
        result = process(raw)
        # BP=Q1~Q5: 5,6,7,8,4 합 30 → 6.0
        self.assertAlmostEqual(result["skill_scores"][0].score, 6.0)


class TestScenario09_ExtremeMix(unittest.TestCase):
    """시나리오 9: 0과 10 극단 혼합. 그래프 양끝점·partial block 검증."""

    def test_extreme(self):
        bp = [0, 0, 0, 0, 0]  # 합 0 → 0.0
        rg = [10, 10, 10, 10, 10]  # 합 50 → 10.0
        cs = [5, 5, 5, 5, 5]  # 합 25 → 5.0
        ft = [10, 0, 10, 0, 10]  # 합 30 → 6.0
        raw = ", ".join(str(x) for x in bp + rg + cs + ft)
        result = process(raw)
        self.assertEqual(result["skill_scores"][0].score, 0.0)
        self.assertEqual(result["skill_scores"][1].score, 10.0)
        self.assertEqual(result["skill_scores"][2].score, 5.0)
        self.assertEqual(result["skill_scores"][3].score, 6.0)
        # 레벨: Not Yet, World Class, Average, Solid
        levels = {ls["skill_en"]: ls["level"] for ls in result["level_summary"]}
        self.assertEqual(levels["Big Picture"], "Not Yet")
        self.assertEqual(levels["Reframing Goals"], "World Class")
        self.assertEqual(levels["Creating Strategies"], "Average")
        self.assertEqual(levels["Following Through"], "Solid")
        # ASCII 그래프: BP는 빈칸, RG는 가득
        chart = result["ascii_chart"]
        self.assertIn("░░░░░░░░░░ 0.0", chart)
        self.assertIn("██████████ 10.0", chart)


class TestScenario10_ReDiagnosisWithDelta(unittest.TestCase):
    """시나리오 10: 재진단 — 이전 점수와 비교 델타 계산."""

    def test_redo(self):
        # 첫 진단 점수
        prev_skills = calculate_skill_scores(
            parse_scores(", ".join(["5"] * 20))
        )
        # 5.0 / 5.0 / 5.0 / 5.0
        self.assertEqual(prev_skills[0].score, 5.0)
        # 재진단: 점수 향상
        raw_new = ", ".join(["7"] * 20)
        new_result = process(raw_new)
        prev = {"BP": 5.0, "RG": 5.0, "CS": 5.0, "FT": 5.0}
        delta = compute_delta(new_result["skill_scores"], prev)
        # 4 능력 모두 +2.0 향상
        for skill_en in ["Big Picture", "Reframing Goals", "Creating Strategies", "Following Through"]:
            self.assertEqual(delta[skill_en]["delta"], 2.0)
            self.assertEqual(delta[skill_en]["direction"], "↑")


class TestScenario_CompositeAndOneLine(unittest.TestCase):
    """추가 정합성 검증: composite·한 줄 요약 일관성."""

    def test_consistency(self):
        # BP=8.0, RG=6.0, CS=4.0, FT=2.0 → composite=5.0
        bp = [8] * 5
        rg = [6] * 5
        cs = [4] * 5
        ft = [2] * 5
        raw = ", ".join(str(x) for x in bp + rg + cs + ft)
        result = process(raw)
        self.assertEqual(result["composite"], 5.0)
        self.assertIn("BP 8.0", result["one_line"])
        self.assertIn("RG 6.0", result["one_line"])
        self.assertIn("CS 4.0", result["one_line"])
        self.assertIn("FT 2.0", result["one_line"])
        self.assertIn("Composite 5.00", result["one_line"])


if __name__ == "__main__":
    unittest.main()
