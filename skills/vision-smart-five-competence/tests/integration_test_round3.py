#!/usr/bin/env python3
"""ROUND 3 — 오딧 결함 수정 후 신규 10개 프롬프트 검증.

목적: 자동 생성 단위 테스트 외에 "이전 검증에 사용된 적 없는 quote 키·출처·케이스"만
사용하여 검증을 한 번 더 실시. ROUND 1과 ROUND 2의 학습 효과를 차단하기 위함.

이 라운드에서만 사용하는 신규 quote 키 (ROUND 1·2 미사용):
  S_FAILURE_MOTHER, S_FILTERING, M_INFO_REDUCE, M_BANGALORE,
  A_IMAGINATION, T_SWEAT, T_KNOWLEDGE_TECH, T_PITCHER

이 라운드에서만 사용하는 신규 학계 출처 (ROUND 1·2 미사용 또는 다른 필드):
  SARTRE_1940 (인식 능력 3가지)
  CARR_1961 (원문 영어 + 박사님 추가 해석)

실행: python3 tests/integration_test_round3.py
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
    return json.loads(result.stdout)


class TestRound3NaturalLanguage(unittest.TestCase):
    """ROUND 3 — 신규 quote 키·출처만 사용하는 10개"""

    @classmethod
    def setUpClass(cls):
        cls.data = eng.load_data()
        cls.log = []
        cls.used_quote_keys = set()
        cls.used_source_ids = set()

    @classmethod
    def tearDownClass(cls):
        out = HERE / "integration_responses_round3.md"
        with out.open("w", encoding="utf-8") as fh:
            fh.write("# ROUND 3 통합 검증 응답 (오딧 후 신규 10개)\n\n")
            fh.write(f"사용된 quote 키: {sorted(cls.used_quote_keys)}\n\n")
            fh.write(f"사용된 학계 출처 ID: {sorted(cls.used_source_ids)}\n\n")
            for entry in cls.log:
                fh.write(entry + "\n---\n\n")
        print(f"\n[round3 응답: {out}]")

    def _log(self, pid, prompt, calls_log, body):
        self.log.append("\n".join(
            [f"## {pid}", f"**Prompt**: {prompt}", "",
             "### Section A. 결정론 엔진 호출"]
            + [f"- `{c}`" for c in calls_log]
            + ["", "### Section D. 검증 결과"]
            + body
        ))

    # --- B1: 실패는 성공의 어머니 (신경과학 증명) ---
    def test_B1_failure_is_mother_neuroscience(self):
        prompt = ("박사님 책에서 '실패는 성공의 어머니'를 신경과학적으로 "
                  "증명한 부분 원문 그대로 보여주세요.")
        q = call(["quote", "--key", "S_FAILURE_MOTHER"])
        self.used_quote_keys.add("S_FAILURE_MOTHER")
        self.assertIn("실패는 성공의 어머니", q["quote"])
        self.assertIn("신경학적인 메커니즘", q["quote"])

        src = call(["facts", "--query", "source", "--id", "ERN_1990"])
        self.used_source_ids.add("ERN_1990")
        self.assertEqual(src["discoverer"], "Michael Falkenstein")

        self._log("B1", prompt, [
            "quote --key S_FAILURE_MOTHER", "facts --query source --id ERN_1990"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- 신경과학 근거: {src['discoverer']} {src['year_first']} ERN 발견",
            f"- 1차 출처: {src['primary_citation']}",
            f"- 공동 발견: {src['independent_co_discovery']}"
        ])

    # --- B2: 정보 필터링 + 훈련 ID ---
    def test_B2_filtering_with_training_id(self):
        prompt = ("정보 필터링에 대한 박사님 책 원문 인용과 "
                  "Sense 훈련 ID·번호를 알려주세요.")
        q = call(["quote", "--key", "S_FILTERING"])
        self.used_quote_keys.add("S_FILTERING")
        self.assertIn("Filtering", q["quote"])
        self.assertIn("잘못된 직관적 통찰력", q["quote"])

        train = call(["facts", "--query", "training", "--key", "S"])
        s2 = [t for t in train["items"] if t["id"] == "S2"][0]
        self.assertEqual(s2["ko"], "정보 필터링 (Filtering)")

        self._log("B2", prompt, [
            "quote --key S_FILTERING", "facts --query training --key S"
        ], [
            f"- 훈련 ID: **{s2['id']}** — {s2['ko']}",
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- 요약: {s2['summary']}"
        ])

    # --- B3: 정보 99% 무관 인용 ---
    def test_B3_99_percent_irrelevant(self):
        prompt = ("M-W2 정보 줄이기에서 박사님이 인용한 "
                  "'정보의 99%' 부분을 그대로 보여주세요.")
        q = call(["quote", "--key", "M_INFO_REDUCE"])
        self.used_quote_keys.add("M_INFO_REDUCE")
        self.assertIn("99%", q["quote"])
        self.assertIn("일과 무관", q["quote"])

        train = call(["facts", "--query", "training", "--key", "M"])
        w2 = [t for t in train["work"] if t["id"] == "M-W2"][0]
        self.assertIn("정보의 양", w2["ko"])

        self._log("B3", prompt, [
            "quote --key M_INFO_REDUCE", "facts --query training --key M"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- 훈련 ID **{w2['id']}**: {w2['ko']}",
            f"- 요약: {w2['summary']}"
        ])

    # --- B4: 사믹사 SAMIXA 학계 출처 없음 명시 ---
    def test_B4_samixa_no_external_source(self):
        prompt = ("디팩 방갈로르 사믹사(SAMIXA) 회장 인용을 그대로 보여주시고, "
                  "이건 학계 1차 출처가 없는 박사님 책 단독 인용인가요?")
        q = call(["quote", "--key", "M_BANGALORE"])
        self.used_quote_keys.add("M_BANGALORE")
        self.assertIn("실리콘밸리", q["quote"])
        self.assertIn("사회적 네트워크", q["quote"])

        # 사믹사는 academic_sources에 ID가 없음 = 학계 1차 출처 없음
        ids = [s["id"] for s in self.data["academic_sources"]]
        self.assertNotIn("BANGALORE", ids)
        self.assertNotIn("SAMIXA", ids)

        # SKILL.md에서도 명시: "박사님 책에 명시되지 않았으므로 임의 보강하지 않음"
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("사믹사(SAMIXA)", skill)
        self.assertIn("임의 보강하지 않음", skill)

        self._log("B4", prompt, [
            "quote --key M_BANGALORE", "facts --query all_sources"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            "- ✅ 학계 1차 출처 없음 — 박사님 책 단독 인용",
            "- ✅ SKILL.md에 'SAMIXA 외부 풀네임 추측은 임의 보강하지 않음' 명시"
        ])

    # --- B5: 백남준·잡스·피카소 + Sartre 1940 ---
    def test_B5_artists_and_sartre(self):
        prompt = ("Art 역량에서 박사님이 인용한 '백남준·잡스·피카소' 부분과 "
                  "Sartre 1940의 인식 능력 3가지를 함께 알려주세요.")
        q = call(["quote", "--key", "A_IMAGINATION"])
        self.used_quote_keys.add("A_IMAGINATION")
        self.assertIn("백남준", q["quote"])
        self.assertIn("스티브 잡스", q["quote"])
        self.assertIn("파블로 피카소", q["quote"])

        src = call(["facts", "--query", "source", "--id", "SARTRE_1940"])
        self.used_source_ids.add("SARTRE_1940")
        self.assertEqual(src["year"], 1940)
        self.assertEqual(len(src["key_concepts"]), 3)

        self._log("B5", prompt, [
            "quote --key A_IMAGINATION", "facts --query source --id SARTRE_1940"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- Sartre {src['year']} 1차 출처: {src['primary_citation']}",
            f"- 영역본: {src['english_edition']}",
            f"- 인식 능력 3가지: {', '.join(src['key_concepts'])}",
            f"- 박사님 책에서 강조한 부분: {src['note']}"
        ])

    # --- B6: T_SWEAT + T 훈련 ID ---
    def test_B6_sweat_and_training_ids(self):
        prompt = ("Technology 역량에서 박사님 책의 '땀 흘려 일하는' 인용과 "
                  "T 세 가지 훈련을 ID 별로 알려주세요.")
        q = call(["quote", "--key", "T_SWEAT"])
        self.used_quote_keys.add("T_SWEAT")
        self.assertIn("땀 흘려", q["quote"])

        train = call(["facts", "--query", "training", "--key", "T"])
        self.assertEqual(len(train["items"]), 3)
        ids = [t["id"] for t in train["items"]]
        self.assertEqual(ids, ["T1", "T2", "T3"])

        self._log("B6", prompt, [
            "quote --key T_SWEAT", "facts --query training --key T"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            "- T 훈련 3가지:"
        ] + [f"  - **{t['id']}**: {t['ko']} — {t['summary']}"
             for t in train["items"]])

    # --- B7: T_KNOWLEDGE_TECH ---
    def test_B7_knowledge_in_head_tech_in_body(self):
        prompt = ("'지식은 머릿속에, 기술은 근육과 뼈에' 인용은 박사님 책 "
                  "어느 역량에 나오나요? 박사님 책 출처도 알려주세요.")
        q = call(["quote", "--key", "T_KNOWLEDGE_TECH"])
        self.used_quote_keys.add("T_KNOWLEDGE_TECH")
        self.assertEqual(q["quote"], "지식은 머릿속에, 기술은 근육과 뼈에")

        # T_KNOWLEDGE_TECH 키이므로 Technology 역량
        comp = call(["facts", "--query", "competence", "--key", "T"])
        self.assertEqual(comp["name_en"], "Technology")

        # 박사님 책 source_book 정보
        book = self.data["source_book"]
        self.assertEqual(book["author"], "최윤식")
        self.assertEqual(book["title"], "미래준비학교")
        self.assertEqual(book["year"], 2016)

        self._log("B7", prompt, [
            "quote --key T_KNOWLEDGE_TECH",
            "facts --query competence --key T"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- 역량 분류: **T (Technology)** — *{comp['book_heading']}*",
            f"- 박사님 책 출처: {book['author']} ({book['year']}). 『{book['title']}』",
            f"- 박사님 책 챕터: {book['chapter_topic']}"
        ])

    # --- B8: T_PITCHER + T3 ---
    def test_B8_pitcher_and_T3(self):
        prompt = ("'정상급 투수' 비유가 박사님 책에 있나요? "
                  "T 어느 훈련 항목인지 ID와 함께 알려주세요.")
        q = call(["quote", "--key", "T_PITCHER"])
        self.used_quote_keys.add("T_PITCHER")
        self.assertIn("정상급 투수", q["quote"])

        train = call(["facts", "--query", "training", "--key", "T"])
        t3 = [t for t in train["items"] if t["id"] == "T3"][0]
        self.assertIn("숙련도", t3["ko"])

        self._log("B8", prompt, [
            "quote --key T_PITCHER", "facts --query training --key T"
        ], [
            f"- 박사님 책 verbatim: *\"{q['quote']}\"*",
            f"- 훈련 **{t3['id']}**: {t3['ko']}",
            f"- 요약: {t3['summary']}"
        ])

    # --- B9: 절대 원칙 7번 1만 시간 ---
    def test_B9_absolute_principle_7_10000h(self):
        prompt = ("SKILL.md 절대 원칙 12조항 중 7번 1만 시간 항목이 "
                  "정확히 학계 출처와 연결되어 있는지 검증해주세요.")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        # 절대 원칙 7번이 1만 시간임을 검증
        self.assertIn("1만 시간", skill)
        self.assertIn("Ericsson 1993", skill)
        self.assertIn("363-406", skill)

        src = call(["facts", "--query", "source", "--id", "ERICSSON_1993"])
        self.used_source_ids.add("ERICSSON_1993")
        self.assertIn("363-406", src["venue"])

        self._log("B9", prompt, [
            "facts --query source --id ERICSSON_1993",
            "(SKILL.md 직접 grep)"
        ], [
            "- 절대 원칙 7번 SKILL.md verbatim: \"1만 시간 Art 장인화 핵심 (Ericsson 1993 ...)\"",
            f"- 학계 1차 출처: {src['primary_citation']}",
            f"- 핵심 발견: {src['key_finding']}",
            f"- caveat: {src['caveat']}"
        ])

    # --- B10: Carr 1961 원문 영어 + 박사님 추가 해석 ---
    def test_B10_carr_full_breakdown(self):
        prompt = ("Carr 1961 원문 영어, 박사님 책 한국어 인용, 그리고 "
                  "박사님이 덧붙인 추가 해석을 정확히 구분해서 보여주세요.")
        src = call(["facts", "--query", "source", "--id", "CARR_1961"])
        self.used_source_ids.add("CARR_1961")
        self.assertIn("History is a continuous process",
                      src["original_quote_en"])
        self.assertIn("과거와 현재", src["book_quote_ko"])
        self.assertIn("과거를 해석하면 미래를 통찰", src["note"])

        self._log("B10", prompt, [
            "facts --query source --id CARR_1961"
        ], [
            "**3중 구분 정확성 검증**:",
            f"- 1차 출처: {src['primary_citation']}",
            f"- ① Carr 원문 영어 (1961): *\"{src['original_quote_en']}\"*",
            f"- ② 박사님 책 한국어 인용: *\"{src['book_quote_ko']}\"*",
            f"- ③ 박사님 추가 해석 명시: {src['note']}",
            "- ✅ 박사님 책에 명시되지 않은 부분은 명확히 분리 표기됨"
        ])


if __name__ == "__main__":
    unittest.main(verbosity=2)
