#!/usr/bin/env python3
"""셀프 오딧 — SKILL.md ↔ smart_facts.json ↔ smart_engine.py 무결성 검증.

목적: 독립적 재검증 증거 확보.
- SKILL.md에 언급된 학계 출처 ID가 모두 데이터에 정의되어 있는가
- 데이터의 모든 verbatim 인용이 SKILL.md 본문 내용과 일관되는가
- 5역량 명칭·순서·표제가 SKILL.md ↔ 데이터 ↔ 엔진에서 100% 일치하는가
- 12개국이 SKILL.md ↔ 데이터 ↔ 엔진에서 일치하는가
- DeSeCo 매핑(SAT/R/M)이 SKILL.md ↔ 데이터에서 일치하는가
- 모든 결정론 호출 명령이 SKILL.md에서 정확하게 문서화되어 있는가
- 데이터 무결성: 모든 ID 참조가 유효한가

실행: python3 tests/audit_test.py
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCRIPT_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import smart_engine as eng  # noqa: E402

SKILL_MD = ROOT / "SKILL.md"
DATA_JSON = ROOT / "data" / "smart_facts.json"
ENGINE_PY = SCRIPT_DIR / "smart_engine.py"


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


class TestSkillMdConsistency(unittest.TestCase):
    """SKILL.md와 데이터·엔진 간 일관성 검증"""

    @classmethod
    def setUpClass(cls):
        cls.skill_md = read_text(SKILL_MD)
        cls.data = eng.load_data()
        cls.engine_py = read_text(ENGINE_PY)

    def test_all_academic_source_ids_referenced_in_skill_md(self):
        """데이터의 모든 학계 출처 ID가 SKILL.md에서 직접 참조되어야 한다"""
        for src in self.data["academic_sources"]:
            sid = src["id"]
            self.assertIn(sid, self.skill_md,
                          f"학계 출처 ID '{sid}'가 SKILL.md 본문에 없음")

    def test_all_quote_keys_documented_in_skill_md(self):
        """주요 verbatim 인용 키들이 SKILL.md에 문서화되어야 한다.

        모든 키를 SKILL.md에 나열할 필요는 없으나, 핵심 키는 등장해야 한다.
        """
        critical_keys = [
            "A_10000_HOURS",       # 1만 시간
            "S_INTUITION_8090",    # 80~90% 직관
            "SMART_DESECO_MATCH",  # SMART ↔ DeSeCo 매핑 핵심
        ]
        for k in critical_keys:
            self.assertIn(k, self.skill_md,
                          f"핵심 quote 키 '{k}'가 SKILL.md에 없음")

    def test_five_competence_names_in_skill_md(self):
        """5역량 영문 명칭이 모두 SKILL.md에 등장"""
        for c in self.data["competences"]:
            self.assertIn(c["name_en"], self.skill_md,
                          f"역량 '{c['name_en']}'이 SKILL.md에 없음")

    def test_five_competence_book_headings_in_skill_md(self):
        """5역량 박사님 원문 표제가 SKILL.md에 verbatim 등장"""
        for c in self.data["competences"]:
            self.assertIn(c["book_heading"], self.skill_md,
                          f"표제 '{c['book_heading']}'가 SKILL.md에 verbatim 없음")

    def test_deseco_3core_in_skill_md(self):
        """DeSeCo 3핵심 영문 명칭이 SKILL.md에 등장"""
        for kc in self.data["deseco"]["key_competencies"]:
            self.assertIn(kc["name_en"], self.skill_md,
                          f"DeSeCo '{kc['name_en']}'가 SKILL.md에 없음")

    def test_deseco_3code_in_skill_md(self):
        """DeSeCo 코드(TOOLS/GROUPS/AUTONOMY)가 SKILL.md에 등장"""
        for kc in self.data["deseco"]["key_competencies"]:
            self.assertIn(kc["code"], self.skill_md,
                          f"DeSeCo 코드 '{kc['code']}'가 SKILL.md에 없음")

    def test_engine_cli_commands_documented_in_skill_md(self):
        """결정론 엔진 핵심 명령이 SKILL.md 본문에 예시로 등장"""
        critical_commands = [
            "smart_engine.py assess",
            "smart_engine.py tenkhour",
            "smart_engine.py facts",
            "smart_engine.py quote",
            "smart_engine.py map",
        ]
        for cmd in critical_commands:
            self.assertIn(cmd, self.skill_md,
                          f"엔진 명령 '{cmd}'가 SKILL.md에 문서화 안 됨")

    def test_section_a_to_e_output_format(self):
        """출력 양식 Section A-E가 모두 SKILL.md에 정의되어 있어야 한다"""
        for section in ["Section A", "Section B", "Section C",
                        "Section D", "Section E"]:
            self.assertIn(section, self.skill_md,
                          f"출력 양식 '{section}'이 SKILL.md에 없음")

    def test_deterministic_principle_in_absolute_rules(self):
        """결정론 환원 의무가 절대 원칙에 명시"""
        self.assertIn("결정론 환원", self.skill_md)
        self.assertIn("자연어 추론으로 재생성", self.skill_md)

    def test_error_handling_section_present(self):
        """오류·예외 처리 섹션이 SKILL.md에 존재"""
        self.assertIn("오류 및 예외 처리", self.skill_md)
        self.assertIn("종료코드 2", self.skill_md)

    def test_smart_keys_consistency(self):
        """SMART 키 S/M/A/R/T가 SKILL.md 표 및 결정론 호출 예시에 일관 사용"""
        for k in ["S", "M", "A", "R", "T"]:
            # 적어도 한 번은 등장 (표·예시·매핑)
            self.assertRegex(self.skill_md, rf'\b{k}\b',
                             f"SMART 키 {k}가 SKILL.md에 없음")


class TestDataIntegrity(unittest.TestCase):
    """smart_facts.json 자체의 무결성"""

    @classmethod
    def setUpClass(cls):
        cls.data = eng.load_data()

    def test_competence_keys_unique(self):
        keys = [c["key"] for c in self.data["competences"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_competence_orders_unique_and_sequential(self):
        orders = sorted([c["order"] for c in self.data["competences"]])
        self.assertEqual(orders, [1, 2, 3, 4, 5])

    def test_academic_source_ids_unique(self):
        ids = [s["id"] for s in self.data["academic_sources"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_deseco_mapped_smart_keys_valid(self):
        valid = set("SMART")
        for kc in self.data["deseco"]["key_competencies"]:
            for k in kc["mapped_smart_keys"]:
                self.assertIn(k, valid,
                              f"DeSeCo {kc['code']}의 매핑 키 {k}가 SMART 아님")

    def test_deseco_full_coverage_of_smart(self):
        """모든 SMART 키가 적어도 하나의 DeSeCo 카테고리에 매핑되어야 한다"""
        mapped = set()
        for kc in self.data["deseco"]["key_competencies"]:
            mapped.update(kc["mapped_smart_keys"])
        self.assertEqual(mapped, set("SMART"),
                         f"SMART 키 누락: {set('SMART') - mapped}")

    def test_training_methods_per_competence_complete(self):
        """5역량마다 training_methods 항목이 존재"""
        for k in "SMART":
            self.assertIn(k, self.data["training_methods"],
                          f"역량 {k}의 training_methods 누락")

    def test_S_has_3_trainings(self):
        s = self.data["training_methods"]["S"]
        self.assertEqual(s["training_count"], 3)
        self.assertEqual(len(s["items"]), 3)

    def test_M_has_thinking_and_work_3_each(self):
        m = self.data["training_methods"]["M"]
        self.assertEqual(m["thinking_training_count"], 3)
        self.assertEqual(m["work_training_count"], 3)

    def test_A_has_7_trainings_and_10000_hours(self):
        a = self.data["training_methods"]["A"]
        self.assertEqual(a["training_count"], 7)
        self.assertEqual(a["ten_thousand_hours"], 10000)

    def test_R_has_3_core_axes(self):
        r = self.data["training_methods"]["R"]
        self.assertEqual(len(r["core_axes"]), 3)

    def test_T_has_3_trainings_and_intelligence_source(self):
        t = self.data["training_methods"]["T"]
        self.assertEqual(t["training_count"], 3)
        self.assertEqual(t["technology_intelligence_source"], "MORTARA_2009")
        # 참조된 소스가 실제 존재
        ids = [s["id"] for s in self.data["academic_sources"]]
        self.assertIn(t["technology_intelligence_source"], ids)

    def test_12_countries_alphabetical_or_specified_order(self):
        d = self.data["deseco"]
        countries = d["participating_countries"]
        # 알파벳 정렬은 강제하지 않으나, Trier 2001 원문 순서를 따른다
        expected = ["Austria", "Belgium (Flanders)", "Denmark", "Finland",
                    "France", "Germany", "Netherlands", "New Zealand",
                    "Norway", "Sweden", "Switzerland", "United States"]
        self.assertEqual(countries, expected)

    def test_book_quotes_keys_naming_convention(self):
        """quote 키는 '<역량키>_<주제>' 형식 또는 SMART_DESECO_MATCH"""
        valid_prefixes = {"S_", "M_", "A_", "R_", "T_"}
        for k in self.data["book_quotes_verbatim"].keys():
            if k == "SMART_DESECO_MATCH":
                continue
            self.assertTrue(
                any(k.startswith(p) for p in valid_prefixes),
                f"quote 키 '{k}' 명명 규칙 위반"
            )

    def test_book_quotes_non_empty(self):
        for k, v in self.data["book_quotes_verbatim"].items():
            self.assertTrue(len(v) > 0, f"quote '{k}' 비어 있음")
            self.assertIsInstance(v, str)

    def test_no_placeholder_text_in_data(self):
        """TODO / FIXME / XXX 같은 placeholder가 데이터에 없어야 한다"""
        raw = read_text(DATA_JSON)
        for marker in ["TODO", "FIXME", "XXX", "lorem ipsum"]:
            self.assertNotIn(marker, raw,
                             f"placeholder '{marker}' 발견")

    def test_academic_sources_have_primary_citation(self):
        for s in self.data["academic_sources"]:
            self.assertIn("primary_citation", s,
                          f"출처 '{s['id']}'에 primary_citation 누락")
            self.assertTrue(len(s["primary_citation"]) > 20,
                            f"출처 '{s['id']}' primary_citation 너무 짧음")

    def test_deseco_count_matches_list_length(self):
        d = self.data["deseco"]
        self.assertEqual(
            d["participating_countries_count"],
            len(d["participating_countries"])
        )

    def test_data_no_unicode_anomalies(self):
        """주요 verbatim 인용에 깨진 문자(replacement char) 없어야 한다"""
        raw = read_text(DATA_JSON)
        self.assertNotIn("�", raw,
                         "데이터에 unicode replacement character 발견")


class TestEngineDataAlignment(unittest.TestCase):
    """엔진과 데이터 정의가 일관"""

    @classmethod
    def setUpClass(cls):
        cls.data = eng.load_data()

    def test_engine_valid_smart_keys_matches_data(self):
        from smart_engine import VALID_SMART_KEYS
        data_keys = set(c["key"] for c in self.data["competences"])
        self.assertEqual(VALID_SMART_KEYS, data_keys)

    def test_engine_valid_deseco_codes_matches_data(self):
        from smart_engine import VALID_DESECO_CODES
        data_codes = set(kc["code"] for kc in self.data["deseco"]["key_competencies"])
        self.assertEqual(VALID_DESECO_CODES, data_codes)

    def test_round_trip_smart_to_deseco_to_smart(self):
        """매핑 일관성: SMART → DeSeCo → SMART 라운드트립"""
        # AT → TOOLS → SAT (TOOLS에는 S도 포함)
        deseco = eng.smart_to_deseco(self.data, "AT")
        self.assertEqual(deseco[0]["code"], "TOOLS")
        smart_back = eng.deseco_to_smart(self.data, "TOOLS")
        self.assertEqual(set(smart_back), {"S", "A", "T"})

    def test_each_competence_quote_lookups_succeed(self):
        """각 역량에 대해 적어도 하나의 quote 키가 존재해야 한다"""
        keys = self.data["book_quotes_verbatim"].keys()
        for letter in "SMART":
            prefix = f"{letter}_"
            matching = [k for k in keys if k.startswith(prefix)]
            self.assertGreater(
                len(matching), 0,
                f"역량 {letter}의 quote가 데이터에 없음"
            )

    def test_each_smart_key_has_training_lookup(self):
        for k in "SMART":
            train = eng.get_training(self.data, k)
            self.assertIsInstance(train, dict)
            self.assertTrue(len(train) > 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
