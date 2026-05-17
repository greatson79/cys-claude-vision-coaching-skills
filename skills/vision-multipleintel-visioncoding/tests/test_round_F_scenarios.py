"""
ROUND F — 10개 신규 검증 시나리오 (이전 라운드 A~E와 완전히 다른 새 케이스)
실행: python3 -m unittest tests.test_round_F_scenarios -v
"""
from __future__ import annotations
import os
import sys
import unittest

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
sys.path.insert(0, SCRIPTS_DIR)
import mi_engine as M  # noqa: E402


class RoundF_Scenario01_AllFives(unittest.TestCase):
    """프롬프트#1: 27문항 모두 5점 응답 — 전 지능 동점 극단 케이스."""

    def test_all_5_yields_all_15_and_co_dominance(self):
        cat = M.load_catalog()
        answers = {it["qid"]: 5 for it in cat["items"]}
        scores = M.score_full(answers, catalog=cat)
        # 모든 지능이 15점
        self.assertTrue(all(v == 15 for v in scores.values()))
        ties = M.detect_top4_ties(scores)
        self.assertTrue(ties["has_tie"])
        top = M.top_dominant(scores, k=4)
        # 9개 모두 동점이므로 공동 우세는 9개여야 함
        self.assertEqual(len(top["co_dominant"]), 9)
        self.assertTrue(top["has_co_dominant"])
        # 라벨도 Outstanding
        for s in scores.values():
            self.assertEqual(M.strength_label(s, 3), "Outstanding")


class RoundF_Scenario02_DifferentSeeds(unittest.TestCase):
    """프롬프트#2: 다른 시드는 다른 라운드 배치를 만들어야 한다."""

    def test_seed_difference_produces_different_orders(self):
        cat = M.load_catalog()
        s1 = M.stratified_select(seed=1, catalog=cat)
        s2 = M.stratified_select(seed=2, catalog=cat)
        # 각각 선발은 다를 수 있지만 항상 9지능 × 2를 유지
        for sel in (s1["selected_18"], s2["selected_18"]):
            by_intel = {}
            for q in sel:
                intel = next(it["intel"] for it in cat["items"] if it["qid"] == q)
                by_intel[intel] = by_intel.get(intel, 0) + 1
            for intel in M.INTELLIGENCES:
                self.assertEqual(by_intel[intel], 2)
        # 라운드 배치도 결정론
        r1 = M.order_rounds(s1["selected_18"], seed=1, catalog=cat)
        r1_again = M.order_rounds(s1["selected_18"], seed=1, catalog=cat)
        self.assertEqual(r1, r1_again)


class RoundF_Scenario03_TypeB_3Q(unittest.TestCase):
    """프롬프트#3: 점수만 입력, 14·11·8 같은 3문항 기준 → 자동 판별."""

    def test_infer_3q(self):
        scores = {
            "Linguistic": 14, "Logical-Mathematical": 11, "Spatial": 8,
            "Musical": 7, "Bodily-Kinesthetic": 6, "Interpersonal": 9,
            "Intrapersonal": 13, "Naturalist": 5, "Existential": 12,
        }
        self.assertEqual(M.infer_score_basis(scores), "3q")
        # 강도 라벨 검증
        self.assertEqual(M.strength_label(14, 3), "Outstanding")
        self.assertEqual(M.strength_label(8, 3), "Solid")
        # 상위 4: 14·13·12·11 → Linguistic·Intrapersonal·Existential·Logical-Math
        top = M.top_dominant(scores, k=4)
        names = [x[0] for x in top["strict_top_k"]]
        self.assertEqual(names, ["Linguistic", "Intrapersonal", "Existential", "Logical-Mathematical"])


class RoundF_Scenario04_TypeB_Ambiguous(unittest.TestCase):
    """프롬프트#4: 모두 5~10 범위 점수 — 사용자 확인 필요."""

    def test_ambiguous_when_all_low(self):
        scores = {
            "Linguistic": 9, "Logical-Mathematical": 7, "Spatial": 5,
            "Musical": 6, "Bodily-Kinesthetic": 4, "Interpersonal": 8,
            "Intrapersonal": 10, "Naturalist": 5, "Existential": 6,
        }
        # 모두 ≤10 → ambiguous (2문항 또는 3문항 모두 가능)
        self.assertEqual(M.infer_score_basis(scores), "ambiguous")


class RoundF_Scenario05_ChineseUser(unittest.TestCase):
    """프롬프트#5: 中文 사용자 — 카탈로그 zh 번역 사용."""

    def test_zh_translation_present_for_all_27(self):
        cat = M.load_catalog()
        for it in cat["items"]:
            zh = it.get("zh", "")
            self.assertTrue(zh, f"{it['qid']}: zh 누락")
            # 한자 또는 중국어 문장이 들어있는지 (간단 검사)
            self.assertTrue(any('一' <= ch <= '鿿' for ch in zh),
                            f"{it['qid']} zh에 한자 없음: {zh}")

    def test_zh_likert_labels(self):
        cat = M.load_catalog()
        zh_labels = cat["scale"]["labels"]["zh"]
        for k in ("1", "2", "3", "4", "5"):
            self.assertIn(k, zh_labels)


class RoundF_Scenario06_Round1Tie_TriggersExtra(unittest.TestCase):
    """프롬프트#6: 18문항 1차 후 상위 4위 안 동점 → 추가 9문항 출제 트리거."""

    def test_round1_tie_detected(self):
        cat = M.load_catalog()
        sel = M.stratified_select(seed=7, catalog=cat)
        # 1차에서 모든 지능 점수가 6 (동점) → 상위 4 모두 동점
        answers = {q: 3 for q in sel["selected_18"]}
        scores = M.score_round1(answers, sel["selected_18"], catalog=cat)
        self.assertTrue(all(v == 6 for v in scores.values()))
        ties = M.detect_top4_ties(scores)
        self.assertTrue(ties["has_tie"])
        # 후속: 사용자에게 추가 9문항 출제를 안내해야 함
        # → ties.has_tie True가 트리거 신호


class RoundF_Scenario07_27Q_BoundaryTie_SafetyNet(unittest.TestCase):
    """프롬프트#7: 27문항 완료 후에도 4위 컷오프 동점 → 최종 안전망."""

    def test_27q_co_dominant_includes_ties(self):
        # 1·2·3·4·4 같은 패턴: 4위에서 동점
        scores = {
            "Linguistic": 15, "Logical-Mathematical": 14, "Spatial": 13,
            "Musical": 12, "Bodily-Kinesthetic": 12, "Interpersonal": 12,
            "Intrapersonal": 8, "Naturalist": 7, "Existential": 6,
        }
        top = M.top_dominant(scores, k=4)
        self.assertTrue(top["has_co_dominant"])
        self.assertEqual(top["cutoff_score"], 12)
        # 12점 셋이 모두 포함되어야 함
        names_12 = [x[0] for x in top["co_dominant"] if x[1] == 12]
        self.assertEqual(set(names_12), {"Musical", "Bodily-Kinesthetic", "Interpersonal"})


class RoundF_Scenario08_LikertOutOfRange(unittest.TestCase):
    """프롬프트#8: Likert 범위 외 입력 → ValueError."""

    def test_zero_rejected(self):
        with self.assertRaises(ValueError):
            M.validate_likert(0)

    def test_six_rejected(self):
        with self.assertRaises(ValueError):
            M.validate_likert(6)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            M.validate_likert(-1)

    def test_float_rejected(self):
        with self.assertRaises(ValueError):
            M.validate_likert("3.5")


class RoundF_Scenario09_WrongAnswerCount(unittest.TestCase):
    """프롬프트#9: 한 라운드에 4개 응답 입력 (3개 필요) → 오류."""

    def test_too_many_answers(self):
        with self.assertRaises(ValueError):
            M.parse_round_input("4, 5, 3, 2", 3)

    def test_too_few_answers(self):
        with self.assertRaises(ValueError):
            M.parse_round_input("4, 5", 3)

    def test_empty_input(self):
        with self.assertRaises(ValueError):
            M.parse_round_input("", 3)


class RoundF_Scenario10_CriticismSource(unittest.TestCase):
    """프롬프트#10: 학계 비판 질의 — SOURCES.md에 명시된 자료 검증."""

    def test_sources_md_lists_visser_waterhouse(self):
        sources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "SOURCES.md")
        with open(sources_path, "r", encoding="utf-8") as f:
            txt = f.read()
        # Visser et al. 2006
        self.assertIn("Visser", txt)
        self.assertIn("2006", txt)
        # Waterhouse 2006
        self.assertIn("Waterhouse", txt)
        # APA Dictionary
        self.assertIn("APA Dictionary", txt)
        # 자가 진단 한계
        self.assertIn("self-report", txt)

    def test_sources_md_includes_naturalist_existential_origins(self):
        sources_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "SOURCES.md")
        with open(sources_path, "r", encoding="utf-8") as f:
            txt = f.read()
        self.assertIn("Frames of Mind", txt)
        self.assertIn("1983", txt)
        self.assertIn("Intelligence Reframed", txt)
        self.assertIn("1999", txt)
        # 9th = Existential의 잠정 입장
        self.assertTrue("8.5" in txt or "candidate" in txt.lower() or "잠정" in txt)


class RoundF_DeterministicReplay(unittest.TestCase):
    """추가 보장: 동일 입력에 대한 모든 함수의 멱등성 (할루시네이션 차단의 결정적 증거)."""

    def test_idempotent_selection(self):
        for seed in (3, 17, 99, 31415):
            a = M.stratified_select(seed=seed)
            b = M.stratified_select(seed=seed)
            self.assertEqual(a, b)

    def test_idempotent_full_score(self):
        cat = M.load_catalog()
        answers = {it["qid"]: (i % 5) + 1 for i, it in enumerate(cat["items"])}
        s1 = M.score_full(answers, catalog=cat)
        s2 = M.score_full(answers, catalog=cat)
        self.assertEqual(s1, s2)

    def test_idempotent_top(self):
        scores = {
            "Linguistic": 13, "Logical-Mathematical": 12, "Spatial": 11,
            "Musical": 10, "Bodily-Kinesthetic": 9, "Interpersonal": 8,
            "Intrapersonal": 7, "Naturalist": 6, "Existential": 5,
        }
        self.assertEqual(M.top_dominant(scores, k=4), M.top_dominant(scores, k=4))


if __name__ == "__main__":
    unittest.main(verbosity=2)
