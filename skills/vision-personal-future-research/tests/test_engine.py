"""
vision-personal-future-research 결정론 엔진 테스트.

Runs without pytest dependency — uses `unittest` from stdlib.

  python3 -m unittest tests/test_engine.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import research_engine as eng  # noqa: E402


class TestValidation(unittest.TestCase):
    def test_mbti_valid(self):
        self.assertTrue(eng.validate_mbti("INTJ").ok)
        self.assertTrue(eng.validate_mbti("intj").ok)
        self.assertTrue(eng.validate_mbti(" enfp ").ok)

    def test_mbti_invalid(self):
        self.assertFalse(eng.validate_mbti("IxNJ").ok)
        self.assertFalse(eng.validate_mbti("ABCD").ok)
        self.assertFalse(eng.validate_mbti("INT").ok)
        self.assertFalse(eng.validate_mbti("INTJX").ok)

    def test_enneagram(self):
        self.assertTrue(eng.validate_enneagram("5").ok)
        self.assertTrue(eng.validate_enneagram("5w4").ok)
        self.assertTrue(eng.validate_enneagram("9w1").ok)
        self.assertFalse(eng.validate_enneagram("10").ok)
        self.assertFalse(eng.validate_enneagram("0").ok)
        self.assertFalse(eng.validate_enneagram("5w").ok)
        self.assertFalse(eng.validate_enneagram("xyz").ok)

    def test_mi_validation(self):
        v = eng.validate_multiple_intelligence({"Logical-Mathematical": 9})
        self.assertTrue(v.ok)
        self.assertTrue(any("expected 9" in w for w in v.warnings))

    def test_strong_validation(self):
        v = eng.validate_strong({"R": 5, "I": 7, "A": 8, "S": 6, "E": 4, "C": 3})
        self.assertTrue(v.ok)
        v = eng.validate_strong({"R": "high"})
        self.assertFalse(v.ok)

    def test_minimum_input(self):
        d = {"MBTI": "INTJ"}
        self.assertFalse(eng.check_minimum_input(d, False).ok)
        d = {"MBTI": "INTJ", "Enneagram": "5w4"}
        self.assertTrue(eng.check_minimum_input(d, True).ok)
        d = {"MBTI": "INTJ", "Enneagram": "5w4", "Values": ["진리"]}
        self.assertTrue(eng.check_minimum_input(d, False).ok)


class TestMapping(unittest.TestCase):
    def test_top_n_with_ties(self):
        scores = {"A": 9, "B": 9, "C": 8, "D": 7}
        top = eng.top_n_with_ties(scores, 1)
        self.assertEqual({k for k, _ in top}, {"A", "B"})

    def test_mi_mapping(self):
        out = eng.map_multiple_intelligence({"Logical-Mathematical": 10, "Linguistic": 5})
        self.assertGreater(out["Technology"], 0)
        self.assertGreater(out["Economy"], 0)

    def test_existential_provisional(self):
        out_prov = eng.map_multiple_intelligence({"Existential": 10})
        out_full = eng.map_multiple_intelligence({"Existential": 10}, existential_full_weight=True)
        self.assertLess(out_prov["Spirituality"], out_full["Spirituality"])
        self.assertAlmostEqual(out_prov["Spirituality"] * 2, out_full["Spirituality"])

    def test_riasec_mapping(self):
        out = eng.map_riasec({"R": 10, "I": 8, "A": 5, "S": 4, "E": 3, "C": 2})
        self.assertGreater(out["Technology"], 0)
        self.assertGreater(out["Environment"], 0)

    def test_values_mapping(self):
        out = eng.map_values(["정의", "공동체", "영성"])
        self.assertGreater(out["Politics"], 0)
        self.assertGreater(out["Society"], 0)
        self.assertGreater(out["Spirituality"], 0)

    def test_mbti_pattern(self):
        self.assertIn("비약적", eng.mbti_response_pattern("INTJ") or "")
        self.assertIn("영적", eng.mbti_response_pattern("INFP") or "")
        self.assertIn("현실", eng.mbti_response_pattern("ISTJ") or "")
        self.assertIn("생활", eng.mbti_response_pattern("ESFP") or "")
        self.assertIsNone(eng.mbti_response_pattern("XYZW"))

    def test_enneagram_pattern(self):
        self.assertIn("정의", eng.enneagram_response_pattern("1w2") or "")
        self.assertIn("위기", eng.enneagram_response_pattern("6") or "")
        self.assertIn("의미", eng.enneagram_response_pattern("5w4") or "")
        self.assertIsNone(eng.enneagram_response_pattern("xyz"))

    def test_job_domain(self):
        out = eng.map_job_domain(["법조"])
        self.assertEqual(out["Politics"], 1.0)
        self.assertEqual(out["Society"], 0.5)


class TestWeightAggregation(unittest.TestCase):
    def test_cap_and_normalize_sums_100(self):
        raw = {"Society": 100, "Technology": 0, "Economy": 0, "Environment": 0, "Politics": 0, "Spirituality": 0}
        out = eng.cap_and_normalize(raw)
        self.assertAlmostEqual(sum(out.values()), 100.0, places=1)
        # 상한 캡 50%
        self.assertLessEqual(out["Society"], 50.01)

    def test_cap_excess_redistributed(self):
        raw = {"Society": 80, "Technology": 10, "Economy": 5, "Environment": 0, "Politics": 0, "Spirituality": 5}
        out = eng.cap_and_normalize(raw)
        self.assertLessEqual(out["Society"], 50.01)
        self.assertAlmostEqual(sum(out.values()), 100.0, places=1)

    def test_cap_uniform_fallback_for_empty(self):
        raw = {d: 0.0 for d in eng.STEEPS_DOMAINS}
        out = eng.cap_and_normalize(raw)
        self.assertAlmostEqual(sum(out.values()), 100.0, places=1)
        for v in out.values():
            self.assertAlmostEqual(v, 100.0 / 6, places=1)

    def test_cys_recoefficient(self):
        base = {d: 10.0 for d in eng.STEEPS_DOMAINS}
        out = eng.apply_cys_recoefficient(
            base,
            {"vision_direction": "강", "vision_potential": "강"},
            "Technology",
        )
        self.assertGreater(out["Technology"], 10.0)

    def test_vision_split_detection(self):
        evenly = {d: 100.0 / 6 for d in eng.STEEPS_DOMAINS}
        out = eng.detect_vision_split(evenly)
        self.assertTrue(out["is_split"])
        concentrated = {"Society": 60, "Technology": 30, "Economy": 5, "Environment": 0, "Politics": 0, "Spirituality": 5}
        out = eng.detect_vision_split(concentrated)
        self.assertFalse(out["is_split"])


class TestAgeAndTime(unittest.TestCase):
    def test_vision_ratio_all_bands(self):
        for age in [5, 15, 25, 35, 55, 75, 90]:
            r = eng.vision_ratio_for_age(age)
            self.assertEqual(r["short_pct"] + r["mid_pct"] + r["long_pct"], 100)

    def test_vision_ratio_invalid(self):
        with self.assertRaises(ValueError):
            eng.vision_ratio_for_age(-1)
        with self.assertRaises(ValueError):
            eng.vision_ratio_for_age(200)

    def test_time_axis(self):
        out = eng.absolute_time_axis(2026)
        self.assertEqual(out["short"]["start_year"], 2026)
        self.assertEqual(out["short"]["end_year"], 2031)
        self.assertEqual(out["mid"]["end_year"], 2041)
        self.assertEqual(out["long"]["end_year"], 2056)


class TestComposite(unittest.TestCase):
    def test_composite(self):
        s = eng.composite_score(30, "short", "high")
        self.assertAlmostEqual(s, 30 * 1.5 * 1.5)

    def test_composite_invalid(self):
        with self.assertRaises(ValueError):
            eng.composite_score(30, "weird", "high")
        with self.assertRaises(ValueError):
            eng.composite_score(30, "short", "very_high")

    def test_priority_ranking(self):
        scores = [10, 20, 30, 40, 50, 60]
        self.assertEqual(eng.rank_priority(60, all_scores=scores), "★★★")
        self.assertEqual(eng.rank_priority(10, all_scores=scores), "★")

    def test_card_count(self):
        self.assertEqual(eng.card_count_for_mode("standard"), (10, 15))


class TestSources(unittest.TestCase):
    def test_get_source(self):
        s = eng.get_source("Society", "short", "kr_tfr")
        self.assertIsNotNone(s)
        self.assertIn("통계청", s["source"])

    def test_unregistered_source(self):
        self.assertIsNone(eng.get_source("Society", "short", "made_up_claim"))

    def test_all_source_ids(self):
        ids = eng.all_source_ids()
        self.assertIn("kr_tfr", ids)
        self.assertIn("agi_timing", ids)
        self.assertGreater(len(ids), 30)

    def test_wildcards(self):
        wc = eng.list_wildcards()
        self.assertGreater(len(wc), 5)
        ids = {w["id"] for w in wc}
        self.assertIn("pandemic", ids)


class TestPipeline(unittest.TestCase):
    def _full_input(self):
        return {
            "MBTI": "INTJ",
            "Enneagram": "5w4",
            "MultipleIntelligence": {
                "Logical-Mathematical": 9,
                "Linguistic": 8,
                "Intrapersonal": 8,
                "Existential": 8,
                "Spatial": 6,
                "Bodily-Kinesthetic": 4,
                "Musical": 4,
                "Interpersonal": 6,
                "Naturalist": 5,
            },
            "STRONG": {"I": 9, "A": 7, "S": 5, "R": 4, "E": 4, "C": 3},
            "Values": ["진리", "지혜", "영성", "정의", "공동체"],
            "CYS": {"vision_direction": "강", "vision_potential": "강"},
            "Readiness": {"big_picture": 8},
        }

    def test_compute_weights_full(self):
        res = eng.compute_weights(self._full_input(), vision_candidate=True, target_recoef_domain="Technology")
        self.assertTrue(res.validation["ok"])
        self.assertAlmostEqual(sum(res.weights_pct.values()), 100.0, places=1)
        self.assertGreater(res.weights_pct["Technology"], 0)
        self.assertIsNotNone(res.response_patterns["MBTI"])

    def test_compute_weights_insufficient(self):
        res = eng.compute_weights({"MBTI": "INTJ"}, vision_candidate=False)
        self.assertFalse(res.validation["ok"])

    def test_build_cards(self):
        res = eng.compute_weights(self._full_input(), vision_candidate=True)
        cards = eng.build_change_cards(res.weights_pct)
        self.assertGreater(len(cards), 10)
        cards = eng.select_top_cards(cards, mode="standard")
        cards = eng.ensure_six_domain_min_one(cards)
        domains = {c.domain for c in cards}
        self.assertEqual(domains, set(eng.STEEPS_DOMAINS))

    def test_determinism(self):
        i = self._full_input()
        a = eng.compute_weights(i, vision_candidate=True, target_recoef_domain="Technology").weights_pct
        b = eng.compute_weights(i, vision_candidate=True, target_recoef_domain="Technology").weights_pct
        self.assertEqual(a, b)

    def test_missing_notice(self):
        out = eng.missing_diagnosis_notice(["MBTI", "Enneagram"])
        self.assertIn("CYS", out["missing"])
        self.assertEqual(out["missing_count"], 5)
        self.assertTrue(out["warn_insufficient_differentiation"])


class TestSelfCheck(unittest.TestCase):
    def test_self_check_passes(self):
        out = eng.self_check()
        self.assertTrue(out["ok"], msg=f"self_check failed: {out['issues']}")
        self.assertGreater(out["source_count"], 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
