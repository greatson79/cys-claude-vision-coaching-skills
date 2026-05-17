"""strong_engine.py 단위 테스트.

각 결정론 함수의 PASS 조건:
- 점수 산출 정확 (3~15 범위)
- 트라이코드 동점 처리 — Hexagon 인접 → 표준 순서
- DB / dyad / 정의 결합 fallback 모두 동작
- 응답 검증 오류 케이스 모두 ValidationError
- 다국어 라벨 4종 (ko/en/zh/ja) 모두 로드
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import strong_engine as se  # noqa: E402


def _full(value: int) -> dict[int, int]:
    return {i: value for i in range(1, 19)}


class TestValidation(unittest.TestCase):
    def test_complete_valid(self):
        out = se.validate_responses(_full(3))
        self.assertEqual(len(out), 18)
        self.assertTrue(all(v == 3 for v in out.values()))

    def test_missing(self):
        bad = _full(3)
        del bad[7]
        with self.assertRaises(se.ValidationError) as ctx:
            se.validate_responses(bad)
        self.assertIn("누락", str(ctx.exception))

    def test_extra_key(self):
        bad = _full(3)
        bad[19] = 4
        with self.assertRaises(se.ValidationError) as ctx:
            se.validate_responses(bad)
        self.assertIn("범위 밖", str(ctx.exception))

    def test_out_of_range(self):
        bad = _full(3)
        bad[1] = 0
        bad[2] = 6
        bad[3] = -1
        with self.assertRaises(se.ValidationError):
            se.validate_responses(bad)

    def test_bool_rejected(self):
        bad = _full(3)
        bad[1] = True  # bool은 int 아님으로 처리
        with self.assertRaises(se.ValidationError):
            se.validate_responses(bad)

    def test_string_value_rejected(self):
        bad: dict[int, int] = _full(3)  # type: ignore[assignment]
        bad[1] = "4"  # type: ignore[assignment]
        with self.assertRaises(se.ValidationError):
            se.validate_responses(bad)

    def test_not_dict(self):
        with self.assertRaises(se.ValidationError):
            se.validate_responses([3] * 18)  # type: ignore[arg-type]


class TestScores(unittest.TestCase):
    def test_all_ones(self):
        scores = se.compute_scores(_full(1))
        for d in "RIASEC":
            self.assertEqual(scores[d], 3)

    def test_all_fives(self):
        scores = se.compute_scores(_full(5))
        for d in "RIASEC":
            self.assertEqual(scores[d], 15)

    def test_mixed(self):
        # R=Q1+Q7+Q13, I=Q2+Q8+Q14, A=Q3+Q9+Q15
        # S=Q4+Q10+Q16, E=Q5+Q11+Q17, C=Q6+Q12+Q18
        r = {
            1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 5,
            7: 5, 8: 4, 9: 3, 10: 2, 11: 1, 12: 5,
            13: 5, 14: 4, 15: 3, 16: 2, 17: 1, 18: 5,
        }
        scores = se.compute_scores(r)
        self.assertEqual(scores["R"], 15)
        self.assertEqual(scores["I"], 12)
        self.assertEqual(scores["A"], 9)
        self.assertEqual(scores["S"], 6)
        self.assertEqual(scores["E"], 3)
        self.assertEqual(scores["C"], 15)

    def test_percentages(self):
        scores = {"R": 15, "I": 9, "A": 3, "S": 12, "E": 6, "C": 11}
        p = se.compute_percentages(scores)
        self.assertAlmostEqual(p["R"], 100.0, places=1)
        self.assertAlmostEqual(p["A"], 0.0, places=1)
        self.assertAlmostEqual(p["I"], 50.0, places=1)


class TestTricode(unittest.TestCase):
    def test_simple_descending(self):
        scores = {"R": 12, "I": 14, "A": 8, "S": 10, "E": 7, "C": 6}
        self.assertEqual(se.compute_tricode(scores), "IRS")

    def test_tie_first_two_standard_order(self):
        # R과 I 동률 → 1위 결정에 fixed=[] → 표준 순서로 R 먼저
        scores = {"R": 14, "I": 14, "S": 10, "A": 8, "E": 7, "C": 6}
        self.assertEqual(se.compute_tricode(scores), "RIS")

    def test_tie_uses_hexagon_proximity(self):
        # 1위 R 확정 후, 2위 후보가 I(인접), S(대각) 동률 → I 우선
        scores = {"R": 15, "I": 12, "A": 5, "S": 12, "E": 3, "C": 4}
        self.assertEqual(se.compute_tricode(scores), "RIS")

    def test_three_way_tie_standard(self):
        # 모두 동률 → 1위·2위·3위 모두 표준 순서로 R, I, A
        scores = {"R": 9, "I": 9, "A": 9, "S": 9, "E": 9, "C": 9}
        self.assertEqual(se.compute_tricode(scores), "RIA")

    def test_three_top_tie_then_remainder(self):
        # S=A=E=12 동률, 나머지 모두 8
        scores = {"R": 8, "I": 8, "A": 12, "S": 12, "E": 12, "C": 8}
        # 1위: A,S,E 중 표준 순서 → A
        # 2위: 남은 S,E 중 A와의 거리 — A-S=adjacent, A-E=alternate → S
        # 3위: E
        self.assertEqual(se.compute_tricode(scores), "ASE")

    def test_doctor_user_scenario_strict_rules(self):
        # 박사님 예상: I+S+A
        scores = {"R": 5, "I": 14, "A": 11, "S": 13, "E": 8, "C": 6}
        self.assertEqual(se.compute_tricode(scores), "ISA")


class TestHexagonClasses(unittest.TestCase):
    def test_adjacent(self):
        self.assertEqual(se._pair_class("R", "I"), "ADJACENT")
        self.assertEqual(se._pair_class("I", "R"), "ADJACENT")
        self.assertEqual(se._pair_class("C", "R"), "ADJACENT")

    def test_alternate(self):
        self.assertEqual(se._pair_class("R", "A"), "ALTERNATE")
        self.assertEqual(se._pair_class("S", "C"), "ALTERNATE")

    def test_opposite(self):
        self.assertEqual(se._pair_class("R", "S"), "OPPOSITE")
        self.assertEqual(se._pair_class("I", "E"), "OPPOSITE")
        self.assertEqual(se._pair_class("A", "C"), "OPPOSITE")

    def test_invalid_same(self):
        with self.assertRaises(se.ValidationError):
            se._pair_class("R", "R")


class TestConsistency(unittest.TestCase):
    def test_high(self):
        c = se.consistency_label("RIA")  # R-I adjacent
        self.assertEqual(c["level"], "high")

    def test_mid(self):
        c = se.consistency_label("RAI")  # R-A alternate
        self.assertEqual(c["level"], "mid")

    def test_low(self):
        c = se.consistency_label("RSI")  # R-S opposite
        self.assertEqual(c["level"], "low")

    def test_invalid_tricode(self):
        with self.assertRaises(se.ValidationError):
            se.consistency_label("XYZ")
        with self.assertRaises(se.ValidationError):
            se.consistency_label("IR")


class TestDifferentiation(unittest.TestCase):
    def test_high_diff(self):
        scores = {"R": 15, "I": 7, "A": 5, "S": 3, "E": 6, "C": 8}
        d = se.differentiation_label(scores)
        self.assertEqual(d["diff"], 12)
        self.assertEqual(d["level"], "high")

    def test_mid_diff(self):
        scores = {"R": 12, "I": 10, "A": 9, "S": 8, "E": 7, "C": 6}
        d = se.differentiation_label(scores)
        self.assertEqual(d["diff"], 6)
        self.assertEqual(d["level"], "mid")

    def test_low_diff(self):
        scores = {"R": 10, "I": 10, "A": 9, "S": 8, "E": 8, "C": 7}
        d = se.differentiation_label(scores)
        self.assertEqual(d["diff"], 3)
        self.assertEqual(d["level"], "low")

    def test_flat_profile(self):
        self.assertTrue(se.is_flat_profile({"R": 10, "I": 10, "A": 9, "S": 8, "E": 8, "C": 7}))
        self.assertFalse(se.is_flat_profile({"R": 15, "I": 3, "A": 9, "S": 8, "E": 8, "C": 7}))


class TestCareers(unittest.TestCase):
    def test_db_hit(self):
        out = se.lookup_careers("IRS")
        self.assertFalse(out["fallback_used"])
        self.assertEqual(out["source"], "tricode_db")
        self.assertEqual(out["careers"], ["의사", "외과의사", "수의사"])

    def test_dyad_fallback(self):
        # AEC는 DB에 없음 → AE dyad seed로 fallback
        out = se.lookup_careers("AEC")
        self.assertTrue(out["fallback_used"])
        self.assertTrue(out["source"].startswith("dyad_seed:AE"))
        self.assertTrue(len(out["careers"]) > 0)

    def test_complete_unknown_dyad_returns_empty(self):
        # 모든 dyad가 정의되어 있어야 함 — 잘못된 트라이코드만 빈 결과 가능
        with self.assertRaises(se.ValidationError):
            se.lookup_careers("XYZ")

    def test_all_36_in_db(self):
        # 36개 트라이코드 모두 직업 3개씩
        self.assertEqual(len(se.TRICODES), 36)
        for code, careers in se.TRICODES.items():
            self.assertEqual(len(code), 3)
            for c in code:
                self.assertIn(c, "RIASEC")
            self.assertEqual(len(careers), 3, f"{code} 직업 개수 != 3")

    def test_all_30_dyads_in_seed(self):
        # 6P2 = 30 다이코드 모두 시드 존재
        self.assertEqual(len(se.DYAD_SEEDS), 30)
        for d1 in "RIASEC":
            for d2 in "RIASEC":
                if d1 == d2:
                    continue
                self.assertIn(d1 + d2, se.DYAD_SEEDS, f"{d1+d2} dyad 누락")


class TestParseResponses(unittest.TestCase):
    def test_q_prefixed(self):
        r = se.parse_responses("Q01: 4, Q02: 5, Q03: 3")
        self.assertEqual(r, {1: 4, 2: 5, 3: 3})

    def test_newlines(self):
        text = "Q01: 1\nQ02: 2\nQ03: 3\nQ04: 4\nQ05: 5\nQ06: 1\n"
        r = se.parse_responses(text)
        self.assertEqual(r, {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 1})

    def test_no_q_prefix(self):
        r = se.parse_responses("1:4 2:5 3:3")
        self.assertEqual(r, {1: 4, 2: 5, 3: 3})

    def test_no_match_raises(self):
        with self.assertRaises(se.ValidationError):
            se.parse_responses("hello world")

    def test_conflict_raises(self):
        with self.assertRaises(se.ValidationError):
            se.parse_responses("Q01: 4, Q01: 5")


class TestLanguage(unittest.TestCase):
    def test_ko(self):
        self.assertEqual(se.detect_language("안녕하세요"), "ko")

    def test_en(self):
        self.assertEqual(se.detect_language("Hello world"), "en")

    def test_zh(self):
        self.assertEqual(se.detect_language("我想做职业兴趣测试"), "zh")

    def test_ja(self):
        self.assertEqual(se.detect_language("興味検査をしたいです"), "ja")

    def test_mixed_ko_en(self):
        self.assertEqual(se.detect_language("Hello 안녕"), "ko")

    def test_i18n_languages_loaded(self):
        for lang in ("ko", "en", "zh", "ja"):
            self.assertIn(lang, se._I18N["languages"])
            self.assertEqual(len(se._I18N["languages"][lang]["scale"]), 5)


class TestAnalyze(unittest.TestCase):
    def test_full_pipeline(self):
        responses = {
            1: 4, 2: 5, 3: 3, 4: 3, 5: 2, 6: 2,
            7: 4, 8: 5, 9: 3, 10: 4, 11: 2, 12: 2,
            13: 4, 14: 4, 15: 2, 16: 3, 17: 3, 18: 2,
        }
        result = se.analyze(responses, lang="ko")
        self.assertEqual(result["scores"]["I"], 14)
        self.assertEqual(result["scores"]["R"], 12)
        self.assertEqual(result["tricode"], "IRS")
        self.assertEqual(result["consistency"]["level"], "high")  # I-R adjacent
        self.assertIn("careers", result)
        self.assertIn("bar_chart", result)

    def test_flat_warning(self):
        result = se.analyze(_full(3), lang="ko")
        self.assertTrue(result["flat_profile"])
        self.assertTrue(any("평탄" in w or "flat" in w.lower() for w in result["warnings"]))


class TestBarChart(unittest.TestCase):
    def test_ascii_contains_all_domains(self):
        scores = {"R": 12, "I": 14, "A": 8, "S": 10, "E": 7, "C": 6}
        chart = se.bar_chart_ascii(scores, lang="ko")
        for d in ("Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"):
            self.assertIn(d, chart)
        self.assertIn("★", chart)


if __name__ == "__main__":
    unittest.main(verbosity=2)
