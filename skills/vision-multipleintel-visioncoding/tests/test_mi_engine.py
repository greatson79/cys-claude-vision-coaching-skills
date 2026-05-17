"""
vision-multipleintel-visioncoding deterministic engine — comprehensive unit tests.

표준 라이브러리 unittest만 사용. python3 -m unittest 로 실행.
실행: cd skills/vision-multipleintel-visioncoding && python3 -m unittest tests.test_mi_engine -v
"""
from __future__ import annotations
import os
import sys
import unittest

# 스크립트 경로를 path에 추가
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)

import mi_engine as M  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_catalog_27_items(self):
        cat = M.load_catalog()
        self.assertEqual(len(cat["items"]), 27)

    def test_catalog_each_intel_has_3(self):
        cat = M.load_catalog()
        for intel in M.INTELLIGENCES:
            self.assertEqual(len(cat["intelligence_qids"][intel]), 3)

    def test_catalog_qids_unique(self):
        cat = M.load_catalog()
        qids = [it["qid"] for it in cat["items"]]
        self.assertEqual(len(qids), len(set(qids)))

    def test_catalog_has_all_translations(self):
        cat = M.load_catalog()
        for it in cat["items"]:
            for lang in ("ko", "en", "zh"):
                self.assertTrue(it.get(lang), f"{it['qid']} 누락: {lang}")


class StratifiedSelectTests(unittest.TestCase):
    def test_returns_18_and_9(self):
        r = M.stratified_select(seed=42)
        self.assertEqual(len(r["selected_18"]), 18)
        self.assertEqual(len(r["reserved_9"]), 9)

    def test_each_intel_exactly_2(self):
        cat = M.load_catalog()
        r = M.stratified_select(seed=42, catalog=cat)
        selected_set = set(r["selected_18"])
        for intel, qs in cat["intelligence_qids"].items():
            cnt = sum(1 for q in qs if q in selected_set)
            self.assertEqual(cnt, 2, f"{intel}: {cnt} != 2")

    def test_no_overlap_selected_reserved(self):
        r = M.stratified_select(seed=42)
        self.assertEqual(len(set(r["selected_18"]) & set(r["reserved_9"])), 0)

    def test_union_covers_27(self):
        r = M.stratified_select(seed=42)
        self.assertEqual(len(set(r["selected_18"]) | set(r["reserved_9"])), 27)

    def test_deterministic_same_seed(self):
        r1 = M.stratified_select(seed=123)
        r2 = M.stratified_select(seed=123)
        self.assertEqual(r1, r2)

    def test_different_seeds_yield_different(self):
        r1 = M.stratified_select(seed=1)
        r2 = M.stratified_select(seed=2)
        # 최소 한 가지는 다르다 (확률적으로 거의 확실)
        self.assertNotEqual(r1, r2)


class RoundsTests(unittest.TestCase):
    def test_round_no_duplicate_intel(self):
        cat = M.load_catalog()
        qid_to_intel = {it["qid"]: it["intel"] for it in cat["items"]}
        for seed in (1, 7, 42, 99, 1234):
            r = M.stratified_select(seed=seed, catalog=cat)
            rounds = M.order_rounds(r["selected_18"], seed=seed, catalog=cat)
            self.assertEqual(len(rounds), 6)
            for idx, rnd in enumerate(rounds):
                self.assertEqual(len(rnd), 3)
                intels = [qid_to_intel[q] for q in rnd]
                self.assertEqual(len(intels), len(set(intels)),
                                 f"seed={seed} round {idx+1} 중복: {intels}")

    def test_rounds_cover_all_18(self):
        cat = M.load_catalog()
        r = M.stratified_select(seed=42, catalog=cat)
        rounds = M.order_rounds(r["selected_18"], seed=42, catalog=cat)
        flat = [q for rnd in rounds for q in rnd]
        self.assertEqual(set(flat), set(r["selected_18"]))
        self.assertEqual(len(flat), 18)


class LikertTests(unittest.TestCase):
    def test_valid_range(self):
        for v in (1, 2, 3, 4, 5, "3"):
            self.assertEqual(M.validate_likert(v), int(v))

    def test_invalid_range(self):
        for v in (0, 6, -1, 10):
            with self.assertRaises(ValueError):
                M.validate_likert(v)

    def test_invalid_type(self):
        for v in ("a", None, "3.5"):
            with self.assertRaises(ValueError):
                M.validate_likert(v)

    def test_parse_round_input_basic(self):
        self.assertEqual(M.parse_round_input("4, 3, 5", 3), [4, 3, 5])
        self.assertEqual(M.parse_round_input("4 3 5", 3), [4, 3, 5])
        self.assertEqual(M.parse_round_input("4;3;5", 3), [4, 3, 5])

    def test_parse_round_input_wrong_count(self):
        with self.assertRaises(ValueError):
            M.parse_round_input("4,3", 3)
        with self.assertRaises(ValueError):
            M.parse_round_input("4,3,5,2", 3)

    def test_parse_round_input_invalid_value(self):
        with self.assertRaises(ValueError):
            M.parse_round_input("4,3,9", 3)


class ScoreTests(unittest.TestCase):
    def test_score_round1_basic(self):
        cat = M.load_catalog()
        r = M.stratified_select(seed=42, catalog=cat)
        # 모든 응답 3
        answers = {q: 3 for q in r["selected_18"]}
        scores = M.score_round1(answers, r["selected_18"], catalog=cat)
        for intel in M.INTELLIGENCES:
            self.assertEqual(scores[intel], 6)  # 2문항 × 3

    def test_score_round1_missing(self):
        cat = M.load_catalog()
        r = M.stratified_select(seed=42, catalog=cat)
        answers = {q: 3 for q in r["selected_18"][:17]}  # 17개만
        with self.assertRaises(ValueError):
            M.score_round1(answers, r["selected_18"], catalog=cat)

    def test_score_full_basic(self):
        cat = M.load_catalog()
        answers = {it["qid"]: 4 for it in cat["items"]}
        scores = M.score_full(answers, catalog=cat)
        for intel in M.INTELLIGENCES:
            self.assertEqual(scores[intel], 12)  # 3문항 × 4

    def test_score_full_missing(self):
        cat = M.load_catalog()
        answers = {it["qid"]: 4 for it in cat["items"][:26]}
        with self.assertRaises(ValueError):
            M.score_full(answers, catalog=cat)

    def test_score_full_invalid_likert(self):
        cat = M.load_catalog()
        answers = {it["qid"]: 4 for it in cat["items"]}
        answers["Q01"] = 9
        with self.assertRaises(ValueError):
            M.score_full(answers, catalog=cat)


class TieTests(unittest.TestCase):
    def test_no_tie(self):
        scores = {
            "Linguistic": 14, "Logical-Mathematical": 13, "Spatial": 12,
            "Musical": 11, "Bodily-Kinesthetic": 10, "Interpersonal": 9,
            "Intrapersonal": 8, "Naturalist": 7, "Existential": 6,
        }
        r = M.detect_top4_ties(scores)
        self.assertFalse(r["has_tie"])
        self.assertEqual(len(r["expanded_top"]), 4)

    def test_boundary_tie(self):
        scores = {
            "Linguistic": 14, "Logical-Mathematical": 13, "Spatial": 12,
            "Musical": 11, "Bodily-Kinesthetic": 11, "Interpersonal": 9,
            "Intrapersonal": 8, "Naturalist": 7, "Existential": 6,
        }
        r = M.detect_top4_ties(scores)
        self.assertTrue(r["has_tie"])
        # 4위(11)와 같은 점수가 또 있어야 함
        self.assertEqual(len(r["expanded_top"]), 5)

    def test_internal_tie(self):
        scores = {
            "Linguistic": 14, "Logical-Mathematical": 14, "Spatial": 12,
            "Musical": 11, "Bodily-Kinesthetic": 10, "Interpersonal": 9,
            "Intrapersonal": 8, "Naturalist": 7, "Existential": 6,
        }
        r = M.detect_top4_ties(scores)
        self.assertTrue(r["has_tie"])

    def test_keys_validation(self):
        with self.assertRaises(ValueError):
            M.detect_top4_ties({"Linguistic": 14})


class LabelTests(unittest.TestCase):
    def test_3q_labels(self):
        cases = [
            (3, "Developing"), (5, "Developing"),
            (6, "Moderate"), (7, "Moderate"),
            (8, "Solid"), (9, "Solid"),
            (10, "Above Average"), (11, "Above Average"),
            (12, "Strong"), (13, "Strong"),
            (14, "Outstanding"), (15, "Outstanding"),
        ]
        for score, label in cases:
            self.assertEqual(M.strength_label(score, 3), label,
                             f"3Q score={score} → expected {label}")

    def test_2q_labels(self):
        cases = [
            (2, "Developing"), (3, "Moderate"), (4, "Solid"),
            (5, "Above Average"), (6, "Above Average"),
            (7, "Strong"), (8, "Strong"),
            (9, "Outstanding"), (10, "Outstanding"),
        ]
        for score, label in cases:
            self.assertEqual(M.strength_label(score, 2), label,
                             f"2Q score={score} → expected {label}")

    def test_range_errors(self):
        with self.assertRaises(ValueError):
            M.strength_label(16, 3)
        with self.assertRaises(ValueError):
            M.strength_label(1, 2)
        with self.assertRaises(ValueError):
            M.strength_label(8, 4)


class TopDominantTests(unittest.TestCase):
    def test_unique_top4(self):
        scores = {
            "Linguistic": 14, "Logical-Mathematical": 13, "Spatial": 12,
            "Musical": 11, "Bodily-Kinesthetic": 10, "Interpersonal": 9,
            "Intrapersonal": 8, "Naturalist": 7, "Existential": 6,
        }
        r = M.top_dominant(scores, k=4)
        self.assertEqual([x[0] for x in r["strict_top_k"]],
                         ["Linguistic", "Logical-Mathematical", "Spatial", "Musical"])
        self.assertFalse(r["has_co_dominant"])

    def test_co_dominant_at_boundary(self):
        scores = {
            "Linguistic": 14, "Logical-Mathematical": 13, "Spatial": 12,
            "Musical": 11, "Bodily-Kinesthetic": 11, "Interpersonal": 11,
            "Intrapersonal": 8, "Naturalist": 7, "Existential": 6,
        }
        r = M.top_dominant(scores, k=4)
        self.assertTrue(r["has_co_dominant"])
        # 11점이 3명, 4위 컷오프(11) 이상은 6명
        self.assertEqual(len(r["co_dominant"]), 6)
        self.assertEqual(r["cutoff_score"], 11)

    def test_alphabetic_tiebreak(self):
        scores = {k: 5 for k in M.INTELLIGENCES}
        scores["Linguistic"] = 10
        scores["Spatial"] = 10
        r = M.top_dominant(scores, k=2)
        # 10점이 2명: Linguistic, Spatial 알파벳 순
        names = [x[0] for x in r["strict_top_k"]]
        self.assertEqual(names, sorted(names))


class InferScoreBasisTests(unittest.TestCase):
    def test_3q_detected(self):
        scores = {k: 8 for k in M.INTELLIGENCES}
        scores["Linguistic"] = 14
        self.assertEqual(M.infer_score_basis(scores), "3q")

    def test_ambiguous(self):
        scores = {k: 6 for k in M.INTELLIGENCES}
        self.assertEqual(M.infer_score_basis(scores), "ambiguous")

    def test_out_of_range(self):
        with self.assertRaises(ValueError):
            M.infer_score_basis({"Linguistic": 20, **{k: 5 for k in M.INTELLIGENCES if k != "Linguistic"}})


class IntegrationTests(unittest.TestCase):
    """엔드투엔드 — 선발 → 응답 → 점수 → 라벨 → 상위4."""

    def test_round1_full_flow(self):
        cat = M.load_catalog()
        sel = M.stratified_select(seed=2025, catalog=cat)
        rounds = M.order_rounds(sel["selected_18"], seed=2025, catalog=cat)
        # 라운드별 (Q01 응답 5, Q02 응답 4, 그 외 응답 3) 같은 시뮬레이션
        answers = {}
        for q in sel["selected_18"]:
            if q == "Q01":
                answers[q] = 5
            elif q == "Q02":
                answers[q] = 4
            else:
                answers[q] = 3
        scores = M.score_round1(answers, sel["selected_18"], catalog=cat)
        # 모든 점수가 2~10 범위
        for s in scores.values():
            self.assertTrue(2 <= s <= 10)
        top = M.top_dominant(scores, k=4)
        self.assertEqual(len(top["strict_top_k"]), 4)
        # 합산 검증: Linguistic은 Q01·Q02 중 어떤 게 선발되었느냐에 따라 달라짐
        # 적어도 정확히 18응답을 사용했는지만 검증
        total_responses = sum(answers.values())
        self.assertEqual(total_responses, sum(scores.values()))

    def test_full_flow_27(self):
        cat = M.load_catalog()
        # 모든 응답 4
        answers = {it["qid"]: 4 for it in cat["items"]}
        scores = M.score_full(answers, catalog=cat)
        for intel, s in scores.items():
            self.assertEqual(s, 12)
            self.assertEqual(M.strength_label(s, 3), "Strong")


if __name__ == "__main__":
    unittest.main(verbosity=2)
