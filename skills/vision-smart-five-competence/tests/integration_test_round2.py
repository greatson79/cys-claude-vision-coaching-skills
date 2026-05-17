#!/usr/bin/env python3
"""End-to-end integration test — ROUND 2.

1차 검증(integration_test.py)과 완전히 다른 10개 자연어 프롬프트:
- 입력 모드 A/B/C/D/E 다양화
- 5단계 통합 시너지
- 잘못된 정의 교정
- 라틴 원문 인용
- 경계 조건 (거의 다 채운 1만 시간)
- 동률 모든 역량 동점
- 부분 입력 (current_hours만 있고 추가 학습 계획)

실행: python3 tests/integration_test_round2.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT = ROOT / "scripts" / "smart_engine.py"
sys.path.insert(0, str(ROOT / "scripts"))

import smart_engine as eng  # noqa: E402


def call(args: list[str]) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {"_error": result.stderr.strip(), "_rc": result.returncode}
    if not result.stdout.strip():
        return {"_empty": True}
    return json.loads(result.stdout)


class TestRound2NaturalLanguage(unittest.TestCase):
    """ROUND 2 — 1차 검증과 전혀 다른 케이스 10개"""

    @classmethod
    def setUpClass(cls):
        cls.data = eng.load_data()
        cls.log = []

    @classmethod
    def tearDownClass(cls):
        out = HERE / "integration_responses_round2.md"
        with out.open("w", encoding="utf-8") as fh:
            fh.write("# ROUND 2 통합 검증 응답 (1차와 전혀 다른 10개 프롬프트)\n\n")
            for entry in cls.log:
                fh.write(entry + "\n---\n\n")
        print(f"\n[round2 응답: {out}]")

    def _log(self, prompt_id, prompt, calls_logs, body):
        s = [f"## {prompt_id}", f"**Prompt**: {prompt}", "",
             "### Section A. 결정론 엔진 호출 로그"]
        s += [f"- `{c}`" for c in calls_logs]
        s += ["", "### Section D. 코칭 결과 검증"]
        s += body
        self.log.append("\n".join(s))

    # --- A1: 강점 장인화 (모드 C) - Sense 9, 나머지 5 ---
    def test_A1_strength_master_mode_C(self):
        prompt = ("Sense 9점, Method 5, Art 5, Relationship 5, Technology 5. "
                  "강점 역량을 장인 수준으로 키우는 모드 C 코칭 부탁드립니다.")
        assess = call(["assess", "--scores", '{"S":9,"M":5,"A":5,"R":5,"T":5}'])
        self.assertEqual(assess["average"], 5.8)
        self.assertEqual(assess["strongest"], ["S"])
        # weakest는 동률 4개
        self.assertEqual(sorted(assess["weakest"]), ["A", "M", "R", "T"])
        self.assertEqual(assess["deseco_group_scores"]["TOOLS"], 19)  # S+A+T = 9+5+5

        # 모드 C는 4단계 장인화 → 1만 시간 계획
        # Sense 장인화는 시뮬레이션/필터링/업데이트 깊이 코칭
        th = call(["tenkhour", "--daily-hours", "3", "--current-hours", "0",
                   "--start-date", "2026-05-17"])
        self.assertEqual(th["days_to_complete"], 3334)  # 10000/3 = 3333.33 → 3334
        self.assertEqual(th["years_to_complete"], 9.13)

        train = call(["facts", "--query", "training", "--key", "S"])
        self.assertEqual(train["training_count"], 3)

        self._log("A1", prompt, [
            "assess --scores '{\"S\":9,...}'",
            "tenkhour --daily-hours 3",
            "facts --query training --key S"
        ], [
            f"- 강점: {assess['strongest']} (9점) — 모드 C 4단계 장인화 활성화",
            f"- 1만 시간 (3h/일): {th['days_to_complete']}일 ({th['years_to_complete']}년) → {th['completion_date']}",
            f"- Sense 훈련 3가지 (장인화 깊이): {[t['ko'] for t in train['items']]}"
        ])

    # --- A2: 입력 모드 D - 신학생 직업 맞춤 ---
    def test_A2_mode_D_seminary_student(self):
        prompt = ("저는 신학생입니다. 박사님 SMART 5역량을 신학교 사역에 "
                  "어떻게 적용하면 좋을까요? (입력 모드 D)")
        # 모드 D는 5역량 카탈로그 + 사용자 직업 맥락 매칭
        comps = call(["facts", "--query", "competences"])
        self.assertEqual(len(comps), 5)

        deseco = call(["facts", "--query", "deseco"])
        self.assertEqual(deseco["participating_countries_count"], 12)

        # 신학생에게 가장 자주 매핑되는 박사님 verbatim 인용
        q_personhood = call(["quote", "--key", "R_PERSONHOOD"])
        self.assertIn("인성", q_personhood["quote"])
        q_humanity = call(["quote", "--key", "A_SKILLED_KNOWLEDGE"])

        self._log("A2", prompt, [
            "facts --query competences",
            "facts --query deseco",
            "quote --key R_PERSONHOOD",
            "quote --key A_SKILLED_KNOWLEDGE"
        ], [
            "- 5역량 신학생 사역 맞춤 적용 (모드 D):",
            f"  - S(Sense): 회중 상황 통찰 — *{comps[0]['book_heading']}*",
            f"  - M(Method): 신학 체계 + 사역 시간 관리 — *{comps[1]['book_heading']}*",
            f"  - A(Art): 설교·상담 장인화 (1만 시간) — *{comps[2]['book_heading']}*",
            f"  - R(Relationship): 회중 인성 — *{comps[3]['book_heading']}*",
            f"  - T(Technology): 미디어·영상 사역 도구 — *{comps[4]['book_heading']}*",
            f"- 박사님 인용 (인성): *\"{q_personhood['quote']}\"*"
        ])

    # --- A3: Sense 시뮬레이션 박사님 책 verbatim 검증 ---
    def test_A3_simulation_verbatim_check(self):
        prompt = ("Sense 훈련 중 비행기 조종사 비유가 박사님 책에 실제로 있나요? "
                  "원문 인용해주세요.")
        q = call(["quote", "--key", "S_SIMULATION"])
        self.assertIn("비행기 조종사", q["quote"])
        self.assertIn("시뮬레이션", q["quote"])

        train = call(["facts", "--query", "training", "--key", "S"])
        # S3가 시뮬레이션
        s3 = [t for t in train["items"] if t["id"] == "S3"][0]
        self.assertIn("시뮬레이션", s3["ko"])

        self._log("A3", prompt, [
            "quote --key S_SIMULATION",
            "facts --query training --key S"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- 훈련 ID S3: {s3['ko']} — {s3['summary']}",
            "- ✅ 박사님 책에 실재함 확인됨 (자연어 재구성 없음)"
        ])

    # --- A4: 부분 누적 1만 시간 (8500h, 6.5h/일) ---
    def test_A4_partial_accumulated_tenkhour(self):
        prompt = ("저는 이미 8500시간을 누적했고, 앞으로 매일 6.5시간씩 "
                  "투입할 예정입니다. 1만 시간 언제 채워지나요?")
        th = call(["tenkhour", "--daily-hours", "6.5", "--current-hours", "8500",
                   "--start-date", "2026-05-17"])
        # remaining = 1500, days = 1500/6.5 = 230.77 → 231
        self.assertEqual(th["days_to_complete"], 231)
        self.assertEqual(th["remaining_hours"], 1500.0)
        # 231/365.25 = 0.63
        self.assertAlmostEqual(th["years_to_complete"], 0.63, places=2)

        self._log("A4", prompt, [
            "tenkhour --daily-hours 6.5 --current-hours 8500 --start-date 2026-05-17"
        ], [
            f"- 남은 시간: {th['remaining_hours']}h",
            f"- 소요일수: {th['days_to_complete']}일 ({th['years_to_complete']}년)",
            f"- 완료 예정일: {th['completion_date']}"
        ])

    # --- A5: Jobs 2005 원문 vs 박사님 책 인용 일치 검증 ---
    def test_A5_jobs_2005_quote_consistency(self):
        prompt = ("박사님 책의 스티브 잡스 2005 스탠퍼드 졸업 연설 인용이 "
                  "원문과 일치하는지 확인 부탁드립니다.")
        src = call(["facts", "--query", "source", "--id", "JOBS_2005"])
        self.assertEqual(src["year"], 2005)
        self.assertEqual(src["event"], "Stanford University Commencement Address")
        self.assertIn("dots", src["quote_en"])
        self.assertIn("직관", src["book_quote_ko_paraphrase"])

        # 박사님 책 인용은 paraphrase(의역)임을 명시
        self.assertIn("note", src)
        self.assertIn("의역", src["note"])

        self._log("A5", prompt, ["facts --query source --id JOBS_2005"], [
            f"- 원문 (Stanford 2005): *\"{src['quote_en']}\"*",
            f"- 박사님 책 한국어 의역: *\"{src['book_quote_ko_paraphrase']}\"*",
            f"- 주의: {src['note']}"
        ])

    # --- A6: 잘못된 정의 교정 ---
    def test_A6_wrong_definition_correction(self):
        prompt = ("SMART의 A가 'Action', M이 'Money' 아닌가요?")
        comps = call(["facts", "--query", "competences"])
        # M은 Method, A는 Art
        m = [c for c in comps if c["key"] == "M"][0]
        a = [c for c in comps if c["key"] == "A"][0]
        self.assertEqual(m["name_en"], "Method")
        self.assertEqual(a["name_en"], "Art")

        q = call(["quote", "--key", "SMART_DESECO_MATCH"])
        self.assertIn("SMART 미래인재 역량", q["quote"])

        self._log("A6", prompt, [
            "facts --query competences",
            "quote --key SMART_DESECO_MATCH"
        ], [
            "- 박사님 SMART는 일반 SMART(Specific/Measurable/...)와 다릅니다.",
            f"  - M = **{m['name_en']}** ({m['name_ko']}) — *\"{m['book_heading']}\"* (Money 아님)",
            f"  - A = **{a['name_en']}** ({a['name_ko']}) — *\"{a['book_heading']}\"* (Action 아님)",
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*"
        ])

    # --- A7: 통합 시너지 - Sense+Art 강·Method 약 패턴 ---
    def test_A7_integration_synergy_pattern(self):
        prompt = ("저는 Sense 9, Art 8, Method 3, Relationship 6, Technology 5입니다. "
                  "5단계 통합 시너지 패턴은 어떻게 보시나요?")
        assess = call(["assess", "--scores", '{"S":9,"M":3,"A":8,"R":6,"T":5}'])
        self.assertEqual(assess["weakest"], ["M"])
        self.assertEqual(assess["strongest"], ["S"])
        self.assertEqual(assess["deseco_group_scores"]["TOOLS"], 22)  # S+A+T = 9+8+5
        self.assertEqual(assess["deseco_group_scores"]["AUTONOMY"], 3)  # M

        # Sense + Art = 직관 + 장인 (직관적 거장형) - 코칭 보조 해석
        self._log("A7", prompt, [
            "assess --scores '{\"S\":9,\"M\":3,\"A\":8,\"R\":6,\"T\":5}'"
        ], [
            f"- 5단계 통합 시너지 분석:",
            f"  - DeSeCo TOOLS={assess['deseco_group_scores']['TOOLS']} (강) / AUTONOMY={assess['deseco_group_scores']['AUTONOMY']} (약)",
            f"  - Sense({assess['scores']['S']}) + Art({assess['scores']['A']}) = **직관적 거장형** 패턴",
            f"  - 약점 Method({assess['scores']['M']})은 자율적 실행을 가로막음 → 우선 보강 권장",
            "- 주의: 통합 패턴은 박사님 책 직접 명시가 아닌 코칭 보조 해석 (SKILL.md 5단계 참조)"
        ])

    # --- A8: 5역량 모두 동률 (S=M=A=R=T=5) ---
    def test_A8_all_equal_balanced(self):
        prompt = ("S=5, M=5, A=5, R=5, T=5 — 모두 같은 5점입니다. "
                  "가장 균형 잡힌 상태인가요?")
        assess = call(["assess", "--scores", '{"S":5,"M":5,"A":5,"R":5,"T":5}'])
        self.assertEqual(assess["average"], 5.0)
        # 모두 동률이면 5개 모두 약점이자 강점
        self.assertEqual(sorted(assess["weakest"]), ["A", "M", "R", "S", "T"])
        self.assertEqual(sorted(assess["strongest"]), ["A", "M", "R", "S", "T"])
        self.assertEqual(assess["deseco_group_averages"]["TOOLS"], 5.0)
        self.assertEqual(assess["deseco_group_averages"]["GROUPS"], 5.0)
        self.assertEqual(assess["deseco_group_averages"]["AUTONOMY"], 5.0)

        self._log("A8", prompt, [
            "assess --scores '{\"S\":5,\"M\":5,\"A\":5,\"R\":5,\"T\":5}'"
        ], [
            f"- 균형 점수 5.0 / DeSeCo 그룹 모두 5.0 — 완전 균형",
            f"- 동률 처리: weakest={assess['weakest']}, strongest={assess['strongest']}",
            "- 균형은 좋으나 모든 역량이 평균(5/10)에 머물러 *장인 수준* 미달",
            "- 권장: 한 역량 선택 → 모드 C 1만 시간 장인화 시작 (Ericsson 1993)"
        ])

    # --- A9: 라틴 원문 verbatim - 오컴의 면도날 ---
    def test_A9_ockham_razor_latin(self):
        prompt = ("Method 훈련에서 인용된 오컴의 면도날 라틴 원문을 "
                  "그대로 알려주세요.")
        src = call(["facts", "--query", "source", "--id", "OCKHAM_RAZOR"])
        self.assertEqual(src["person"], "William of Ockham")
        self.assertIn("Frustra fit per plura", src["latin_quote"])

        q = call(["quote", "--key", "M_OCKHAM"])
        self.assertIn("적은 것으로", q["quote"])

        self._log("A9", prompt, [
            "facts --query source --id OCKHAM_RAZOR",
            "quote --key M_OCKHAM"
        ], [
            f"- 라틴 원문: *\"{src['latin_quote']}\"*",
            f"- 한국어 번역: *\"{src['translation_ko']}\"*",
            f"- 박사님 책 인용: *\"{q['quote']}\"*",
            f"- 출처: {src['primary_citation']} (c. {src['approx_year']})"
        ])

    # --- A10: 경계 조건 - 9999h 누적, 0.5h/일 ---
    def test_A10_boundary_almost_done(self):
        prompt = ("이미 9999시간 누적했습니다. 매일 0.5시간만 더 투입하면 "
                  "1만 시간 언제 채워지나요?")
        th = call(["tenkhour", "--daily-hours", "0.5", "--current-hours", "9999",
                   "--start-date", "2026-05-17"])
        # remaining = 1.0, days = 1/0.5 = 2
        self.assertEqual(th["remaining_hours"], 1.0)
        self.assertEqual(th["days_to_complete"], 2)
        # 2026-05-17 + 2일 = 2026-05-19
        self.assertEqual(th["completion_date"], "2026-05-19")

        self._log("A10", prompt, [
            "tenkhour --daily-hours 0.5 --current-hours 9999"
        ], [
            f"- 남은 시간: {th['remaining_hours']}h",
            f"- 소요일수: {th['days_to_complete']}일 → {th['completion_date']}",
            f"- 거의 완료 — Ericsson 1993의 deliberate practice 마무리 단계"
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
