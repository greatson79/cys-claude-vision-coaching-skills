"""
ROUND-2 검증 — 이전 검증과 완전히 다른 10개 신규 프롬프트.

검증 의도:
  - 이전 round (test_strong_engine.py)는 엔진 구현 일치 테스트
  - 이번 round는 *사용자 시나리오*를 엔진이 결정론으로 처리하는지 확인
  - 각 케이스 별로 (a) 엔진 통과 (b) tricode 학계 표준 일치 (c) 일관성·차별성 평가 정합성 검증

10개 시나리오 — 의도적으로 다양한 사용자 페르소나·언어·동점·플랫·fallback 포함.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import strong_engine as se  # noqa: E402


class Round2Scenarios(unittest.TestCase):
    """10개 신규 시나리오 검증 — 학계 표준·결정론 일치 보장."""

    # ───────────── 시나리오 1: 야외 활동 좋아하는 농업 청년 ─────────────
    def test_scenario_01_farmer_youth(self):
        """입력: 야외·도구·자연을 선호하는 농업/조경 청년 (R 우세, S·E 보통, A·I·C 낮음)."""
        responses = {
            1: 5, 2: 2, 3: 2, 4: 4, 5: 3, 6: 2,
            7: 5, 8: 3, 9: 1, 10: 4, 11: 3, 12: 2,
            13: 4, 14: 2, 15: 1, 16: 5, 17: 4, 18: 3,
        }
        r = se.analyze(responses, lang="ko")
        # R=Q1+Q7+Q13 = 5+5+4 = 14
        # I=Q2+Q8+Q14 = 2+3+2 = 7
        # A=Q3+Q9+Q15 = 2+1+1 = 4
        # S=Q4+Q10+Q16 = 4+4+5 = 13
        # E=Q5+Q11+Q17 = 3+3+4 = 10
        # C=Q6+Q12+Q18 = 2+2+3 = 7
        self.assertEqual(r["scores"], {"R": 14, "I": 7, "A": 4, "S": 13, "E": 10, "C": 7})
        self.assertEqual(r["tricode"], "RSE")
        # 1·2위 R-S는 OPPOSITE → low consistency
        self.assertEqual(r["consistency"]["level"], "low")
        # 차별성 14-4=10 → high
        self.assertEqual(r["differentiation"]["level"], "high")
        # RSE는 DB에 있음
        self.assertFalse(r["careers"]["fallback_used"])
        self.assertEqual(r["careers"]["careers"], ["응급구조사", "체육교사", "경찰관"])

    # ───────────── 시나리오 2: 디자인+상담 융합 청소년 ─────────────
    def test_scenario_02_design_counsel_teen(self):
        """미술 디자인과 또래 상담 모두 좋아하는 고1 — A·S 동률, R·E 보통."""
        responses = {
            1: 3, 2: 3, 3: 5, 4: 5, 5: 3, 6: 2,
            7: 2, 8: 3, 9: 5, 10: 5, 11: 2, 12: 2,
            13: 2, 14: 3, 15: 4, 16: 4, 17: 3, 18: 2,
        }
        r = se.analyze(responses, lang="ko")
        # R=7 I=9 A=14 S=14 E=8 C=6
        self.assertEqual(r["scores"]["A"], 14)
        self.assertEqual(r["scores"]["S"], 14)
        # A,S 동률 1위 → 표준 순서로 A 먼저
        self.assertEqual(r["tricode"][0], "A")
        self.assertEqual(r["tricode"][1], "S")
        # 1·2위 A-S adjacent → high consistency
        self.assertEqual(r["consistency"]["level"], "high")

    # ───────────── 시나리오 3: 영업 사업가 (E 단독 우세) ─────────────
    def test_scenario_03_entrepreneur(self):
        """영업·창업 우세, 분석·정리 낮음."""
        responses = {
            1: 2, 2: 2, 3: 3, 4: 4, 5: 5, 6: 2,
            7: 2, 8: 2, 9: 3, 10: 4, 11: 5, 12: 2,
            13: 3, 14: 2, 15: 2, 16: 3, 17: 5, 18: 3,
        }
        r = se.analyze(responses, lang="ko")
        # R=7 I=6 A=8 S=11 E=15 C=7
        self.assertEqual(r["scores"]["E"], 15)
        self.assertEqual(r["tricode"][0], "E")
        # E-S 인접 → high consistency
        self.assertEqual(r["tricode"][1], "S")
        self.assertEqual(r["consistency"]["level"], "high")

    # ───────────── 시나리오 4: English 입력 — 데이터 사이언티스트 지망 ─────────────
    def test_scenario_04_english_data_scientist(self):
        """입력 언어 영어, I·R 우세 데이터 분석가 후보."""
        responses = {
            1: 4, 2: 5, 3: 3, 4: 3, 5: 2, 6: 4,
            7: 3, 8: 5, 9: 2, 10: 3, 11: 2, 12: 4,
            13: 4, 14: 5, 15: 2, 16: 2, 17: 3, 18: 3,
        }
        r = se.analyze(responses, lang="en")
        # I=15 R=11 C=11 A=7 S=8 E=7
        self.assertEqual(r["scores"]["I"], 15)
        self.assertEqual(r["tricode"][0], "I")
        # 2위: R=11, C=11 동률 → I와의 거리 R=adjacent(0), C=alternate(1) → R 먼저
        self.assertEqual(r["tricode"][1], "R")
        # 3위: 남은 C가 다음으로 점수 높음 (S=8, A=7, E=7, C=11)
        self.assertEqual(r["tricode"][2], "C")
        self.assertEqual(r["tricode"], "IRC")
        # I-R adjacent → high
        self.assertEqual(r["consistency"]["level"], "high")

    # ───────────── 시나리오 5: 中文 입력 — 회계+행정 ─────────────
    def test_scenario_05_chinese_accounting(self):
        """C·E 우세 회계 행정. 中文 출력 라벨 사용."""
        responses = {
            1: 2, 2: 3, 3: 2, 4: 3, 5: 4, 6: 5,
            7: 2, 8: 3, 9: 2, 10: 3, 11: 4, 12: 5,
            13: 2, 14: 3, 15: 2, 16: 3, 17: 4, 18: 5,
        }
        r = se.analyze(responses, lang="zh")
        # R=6 I=9 A=6 S=9 E=12 C=15
        self.assertEqual(r["scores"]["C"], 15)
        self.assertEqual(r["scores"]["E"], 12)
        self.assertEqual(r["tricode"][0], "C")
        self.assertEqual(r["tricode"][1], "E")
        # 3위: I=9, S=9 동률 → C-I=alternate(1), E-I=opposite(2) → I와 (C,E)의 최소 거리 1, S와 (C,E)의 최소 거리: C-S=alternate(1), E-S=adjacent(0) → S가 더 가까움
        # 그러나 정확히 보면 _tie_break_key는 fixed[]와의 *최소* 거리만 보므로
        # I: C와 alternate(1), E와 opposite(2) → 최소 1
        # S: C와 alternate(1), E와 adjacent(0) → 최소 0
        # → S가 더 가까움 → S 선택
        self.assertEqual(r["tricode"][2], "S")
        self.assertEqual(r["tricode"], "CES")
        # 中文 라벨 확인
        self.assertIn("常规型", r["bar_chart"])

    # ───────────── 시나리오 6: 日本語 입력 — 음악 교사 ─────────────
    def test_scenario_06_japanese_music_teacher(self):
        """A·S 우세 음악 교사 — 日本語 라벨."""
        responses = {
            1: 2, 2: 3, 3: 5, 4: 5, 5: 3, 6: 2,
            7: 3, 8: 3, 9: 5, 10: 5, 11: 3, 12: 2,
            13: 2, 14: 3, 15: 5, 16: 5, 17: 3, 18: 2,
        }
        r = se.analyze(responses, lang="ja")
        # A=15 S=15 → 동률 1위 → 표준 순서 A 먼저
        self.assertEqual(r["scores"]["A"], 15)
        self.assertEqual(r["scores"]["S"], 15)
        self.assertEqual(r["tricode"][0], "A")
        self.assertEqual(r["tricode"][1], "S")
        # 日本語 라벨 확인
        self.assertIn("芸術型", r["bar_chart"])

    # ───────────── 시나리오 7: 비표준 fallback 트라이코드 ─────────────
    def test_scenario_07_unusual_tricode_fallback(self):
        """SCR 같은 비표준 트라이코드 — dyad seed fallback."""
        # S 우세, C·R 중간 — 의도적으로 SCR 만들기
        # S=Q4+Q10+Q16, C=Q6+Q12+Q18, R=Q1+Q7+Q13
        # SCR이 되려면: S > C > R, 그리고 1·2위 거리(S-C) 인접하고, 2위·3위 C-R 인접
        responses = {
            1: 4, 2: 1, 3: 1, 4: 5, 5: 1, 6: 4,
            7: 3, 8: 1, 9: 1, 10: 5, 11: 1, 12: 4,
            13: 3, 14: 1, 15: 1, 16: 5, 17: 1, 18: 3,
        }
        r = se.analyze(responses, lang="ko")
        # R=10 I=3 A=3 S=15 E=3 C=11
        self.assertEqual(r["scores"]["S"], 15)
        self.assertEqual(r["scores"]["C"], 11)
        self.assertEqual(r["scores"]["R"], 10)
        self.assertEqual(r["tricode"], "SCR")
        # SCR이 DB에 없음 → SC dyad seed로 fallback
        self.assertTrue(r["careers"]["fallback_used"])
        self.assertEqual(r["careers"]["source"], "dyad_seed:SC")

    # ───────────── 시나리오 8: 완전 플랫 프로파일 ─────────────
    def test_scenario_08_flat_profile_all_3(self):
        """모든 응답이 3(보통) — 완전 평탄."""
        responses = {i: 3 for i in range(1, 19)}
        r = se.analyze(responses, lang="ko")
        # 전 영역 9점
        self.assertTrue(all(v == 9 for v in r["scores"].values()))
        # 트라이코드 RIA (전 동률 → 표준 순서)
        self.assertEqual(r["tricode"], "RIA")
        self.assertTrue(r["flat_profile"])
        # warnings에 플랫 안내
        self.assertTrue(any("평탄" in w or "flat" in w.lower() for w in r["warnings"]))
        # 차별성 0 → low
        self.assertEqual(r["differentiation"]["level"], "low")

    # ───────────── 시나리오 9: 박사님 본인 점검 (미래학자+목회자) ─────────────
    def test_scenario_09_doctor_user_profile(self):
        """박사님 예상 — I+S+A 우세."""
        responses = {
            1: 2, 2: 5, 3: 4, 4: 5, 5: 4, 6: 3,
            7: 3, 8: 5, 9: 4, 10: 5, 11: 3, 12: 2,
            13: 2, 14: 5, 15: 4, 16: 5, 17: 3, 18: 2,
        }
        r = se.analyze(responses, lang="ko")
        # R=7 I=15 A=12 S=15 E=10 C=7
        self.assertEqual(r["scores"]["I"], 15)
        self.assertEqual(r["scores"]["S"], 15)
        # I,S 동률 1위 → 표준 순서로 I 먼저
        self.assertEqual(r["tricode"][0], "I")
        # 2위: 남은 S=15 단독 최고
        self.assertEqual(r["tricode"][1], "S")
        # 3위: A=12 단독
        self.assertEqual(r["tricode"][2], "A")
        self.assertEqual(r["tricode"], "ISA")
        # I-S alternate (Hexagon 한 칸 건너) → mid consistency
        self.assertEqual(r["consistency"]["primary_class"], "ALTERNATE")
        self.assertEqual(r["consistency"]["level"], "mid")

    # ───────────── 시나리오 10: 응답 파싱 자연어 → 검증 → 결과 ─────────────
    def test_scenario_10_parse_natural_input(self):
        """자연어 응답 파싱 → analyze 전체 흐름."""
        text = """Q01: 5, Q02: 4, Q03: 2
Q04: 3, Q05: 5, Q06: 4
Q07: 5, Q08: 3, Q09: 2
Q10: 4, Q11: 5, Q12: 3
Q13: 5, Q14: 4, Q15: 2
Q16: 3, Q17: 5, Q18: 4"""
        parsed = se.parse_responses(text)
        self.assertEqual(len(parsed), 18)
        r = se.analyze(parsed, lang="ko")
        # R=15 I=11 A=6 S=10 E=15 C=11
        self.assertEqual(r["scores"]["R"], 15)
        self.assertEqual(r["scores"]["E"], 15)
        # R,E 동률 1위 → 표준 순서로 R 먼저
        self.assertEqual(r["tricode"][0], "R")
        self.assertEqual(r["tricode"][1], "E")
        # 3위: I=11, C=11 동률 → R-I=adjacent(0)·E-I=opposite(2) → min=0; R-C=adjacent(0)·E-C=adjacent(0) → min=0
        # 두 후보 모두 거리 0 → 표준 순서로 I 먼저 (I=1, C=5)
        self.assertEqual(r["tricode"][2], "I")
        self.assertEqual(r["tricode"], "REI")
        # REI가 DB에 없음 → RE dyad seed 적용
        self.assertTrue(r["careers"]["fallback_used"])
        self.assertEqual(r["careers"]["source"], "dyad_seed:RE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
