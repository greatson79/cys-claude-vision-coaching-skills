#!/usr/bin/env python3
"""smart_engine.py 단위 테스트.

실행: python3 tests/test_smart_engine.py
종료코드: 0 = 모든 테스트 PASS, 1 = 하나라도 FAIL
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


class TestLoadData(unittest.TestCase):
    def test_load_data_returns_dict(self):
        data = eng.load_data()
        self.assertIsInstance(data, dict)

    def test_required_top_level_keys(self):
        data = eng.load_data()
        for k in [
            "competences", "deseco", "academic_sources",
            "training_methods", "book_quotes_verbatim", "source_book"
        ]:
            self.assertIn(k, data, f"missing top-level key: {k}")


class TestCompetences(unittest.TestCase):
    def setUp(self):
        self.data = eng.load_data()

    def test_exactly_five_competences(self):
        self.assertEqual(len(self.data["competences"]), 5)

    def test_competence_order(self):
        comps = eng.get_competences(self.data)
        self.assertEqual([c["key"] for c in comps], ["S", "M", "A", "R", "T"])

    def test_each_competence_has_required_fields(self):
        for c in self.data["competences"]:
            for f in ["key", "name_en", "name_ko", "book_heading", "details", "order"]:
                self.assertIn(f, c, f"{c.get('key')} missing {f}")

    def test_book_headings_use_imperative_form(self):
        endings = ["기르라", "갖추라", "높여라", "확보하라", "활용하라"]
        for c, expected_ending in zip(eng.get_competences(self.data), endings):
            self.assertTrue(
                c["book_heading"].endswith(expected_ending) or expected_ending in c["book_heading"],
                f"{c['key']} heading must end with '{expected_ending}'"
            )

    def test_get_competence_by_key(self):
        c = eng.get_competence(self.data, "S")
        self.assertEqual(c["name_en"], "Sense")

    def test_get_competence_lowercase(self):
        c = eng.get_competence(self.data, "s")
        self.assertEqual(c["key"], "S")

    def test_get_competence_invalid_raises(self):
        with self.assertRaises(ValueError):
            eng.get_competence(self.data, "X")


class TestDeSeCo(unittest.TestCase):
    def setUp(self):
        self.data = eng.load_data()

    def test_12_countries(self):
        d = self.data["deseco"]
        self.assertEqual(d["participating_countries_count"], 12)
        self.assertEqual(len(d["participating_countries"]), 12)

    def test_period(self):
        d = self.data["deseco"]
        self.assertEqual(d["start_year"], 1997)
        self.assertEqual(d["end_year"], 2003)

    def test_three_key_competencies(self):
        kc = self.data["deseco"]["key_competencies"]
        self.assertEqual(len(kc), 3)
        codes = {k["code"] for k in kc}
        self.assertEqual(codes, {"TOOLS", "GROUPS", "AUTONOMY"})

    def test_smart_to_deseco_SAT_maps_to_TOOLS(self):
        mapped = eng.smart_to_deseco(self.data, "SAT")
        codes = [m["code"] for m in mapped]
        self.assertIn("TOOLS", codes)

    def test_smart_to_deseco_R_maps_to_GROUPS(self):
        mapped = eng.smart_to_deseco(self.data, "R")
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["code"], "GROUPS")

    def test_smart_to_deseco_M_maps_to_AUTONOMY(self):
        mapped = eng.smart_to_deseco(self.data, "M")
        self.assertEqual(len(mapped), 1)
        self.assertEqual(mapped[0]["code"], "AUTONOMY")

    def test_deseco_to_smart_TOOLS(self):
        keys = eng.deseco_to_smart(self.data, "TOOLS")
        self.assertEqual(set(keys), {"S", "A", "T"})

    def test_deseco_to_smart_GROUPS(self):
        keys = eng.deseco_to_smart(self.data, "GROUPS")
        self.assertEqual(keys, ["R"])

    def test_deseco_to_smart_AUTONOMY(self):
        keys = eng.deseco_to_smart(self.data, "AUTONOMY")
        self.assertEqual(keys, ["M"])

    def test_invalid_deseco_raises(self):
        with self.assertRaises(ValueError):
            eng.deseco_to_smart(self.data, "INVALID")


class TestValidateScores(unittest.TestCase):
    def test_valid_scores(self):
        out = eng.validate_scores({"S": 1, "M": 5, "A": 10, "R": 3, "T": 7})
        self.assertEqual(out["A"], 10)

    def test_score_too_low(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": 0, "M": 5, "A": 10, "R": 3, "T": 7})

    def test_score_too_high(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": 1, "M": 5, "A": 11, "R": 3, "T": 7})

    def test_missing_key(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": 1, "M": 5, "A": 10, "R": 3})

    def test_extra_key(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": 1, "M": 5, "A": 10, "R": 3, "T": 7, "X": 9})

    def test_bool_score_rejected(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": True, "M": 5, "A": 10, "R": 3, "T": 7})

    def test_float_with_integer_value_accepted(self):
        out = eng.validate_scores({"S": 1.0, "M": 5, "A": 10, "R": 3, "T": 7})
        self.assertEqual(out["S"], 1)

    def test_float_non_integer_rejected(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": 1.5, "M": 5, "A": 10, "R": 3, "T": 7})

    def test_string_score_rejected(self):
        with self.assertRaises(ValueError):
            eng.validate_scores({"S": "5", "M": 5, "A": 10, "R": 3, "T": 7})

    def test_not_dict_rejected(self):
        with self.assertRaises(ValueError):
            eng.validate_scores([1, 5, 10, 3, 7])


class TestAssess(unittest.TestCase):
    def setUp(self):
        self.data = eng.load_data()

    def test_basic_assessment(self):
        r = eng.assess(self.data, {"S": 3, "M": 4, "A": 6, "R": 8, "T": 5})
        self.assertEqual(r["average"], 5.2)
        self.assertEqual(r["weakest"], ["S"])
        self.assertEqual(r["strongest"], ["R"])

    def test_weakest_ties(self):
        r = eng.assess(self.data, {"S": 2, "M": 5, "A": 2, "R": 8, "T": 5})
        self.assertEqual(r["weakest"], ["A", "S"])

    def test_strongest_ties(self):
        r = eng.assess(self.data, {"S": 3, "M": 9, "A": 6, "R": 9, "T": 5})
        self.assertEqual(r["strongest"], ["M", "R"])

    def test_all_equal(self):
        r = eng.assess(self.data, {"S": 5, "M": 5, "A": 5, "R": 5, "T": 5})
        self.assertEqual(r["average"], 5.0)
        self.assertEqual(r["weakest"], ["A", "M", "R", "S", "T"])
        self.assertEqual(r["strongest"], ["A", "M", "R", "S", "T"])

    def test_deseco_group_scores(self):
        r = eng.assess(self.data, {"S": 3, "M": 4, "A": 6, "R": 8, "T": 5})
        # TOOLS = S+A+T = 3+6+5 = 14
        # GROUPS = R = 8
        # AUTONOMY = M = 4
        self.assertEqual(r["deseco_group_scores"]["TOOLS"], 14)
        self.assertEqual(r["deseco_group_scores"]["GROUPS"], 8)
        self.assertEqual(r["deseco_group_scores"]["AUTONOMY"], 4)

    def test_deseco_group_averages(self):
        r = eng.assess(self.data, {"S": 3, "M": 4, "A": 6, "R": 8, "T": 5})
        # TOOLS avg = 14/3 = 4.67
        self.assertAlmostEqual(r["deseco_group_averages"]["TOOLS"], 4.67, places=2)
        self.assertEqual(r["deseco_group_averages"]["GROUPS"], 8.0)
        self.assertEqual(r["deseco_group_averages"]["AUTONOMY"], 4.0)

    def test_recommendations_present(self):
        r = eng.assess(self.data, {"S": 3, "M": 4, "A": 6, "R": 8, "T": 5})
        self.assertGreater(len(r["recommendations"]), 0)

    def test_min_score_boundary(self):
        r = eng.assess(self.data, {"S": 1, "M": 1, "A": 1, "R": 1, "T": 1})
        self.assertEqual(r["average"], 1.0)

    def test_max_score_boundary(self):
        r = eng.assess(self.data, {"S": 10, "M": 10, "A": 10, "R": 10, "T": 10})
        self.assertEqual(r["average"], 10.0)


class TestTenThousandHours(unittest.TestCase):
    def test_two_hours_daily_from_zero(self):
        r = eng.ten_thousand_hours(daily_hours=2, current_hours=0,
                                    start_date="2026-01-01")
        # 10000/2 = 5000 days
        self.assertEqual(r["days_to_complete"], 5000)
        self.assertEqual(r["start_date"], "2026-01-01")
        # 5000 / 365.25 = 13.69
        self.assertAlmostEqual(r["years_to_complete"], 13.69, places=2)

    def test_with_current_hours(self):
        r = eng.ten_thousand_hours(daily_hours=2, current_hours=1200,
                                    start_date="2026-01-01")
        # Remaining = 8800, /2 = 4400 days
        self.assertEqual(r["days_to_complete"], 4400)

    def test_zero_daily_hours_rejected(self):
        with self.assertRaises(ValueError):
            eng.ten_thousand_hours(daily_hours=0)

    def test_negative_daily_hours_rejected(self):
        with self.assertRaises(ValueError):
            eng.ten_thousand_hours(daily_hours=-1)

    def test_excess_daily_hours_rejected(self):
        with self.assertRaises(ValueError):
            eng.ten_thousand_hours(daily_hours=25)

    def test_negative_current_hours_rejected(self):
        with self.assertRaises(ValueError):
            eng.ten_thousand_hours(daily_hours=2, current_hours=-100)

    def test_already_completed(self):
        r = eng.ten_thousand_hours(daily_hours=2, current_hours=15000,
                                    start_date="2026-01-01")
        self.assertEqual(r["days_to_complete"], 0)
        self.assertEqual(r["completion_date"], "2026-01-01")

    def test_invalid_start_date(self):
        with self.assertRaises(ValueError):
            eng.ten_thousand_hours(daily_hours=2, start_date="not-a-date")

    def test_completion_date_calculation(self):
        r = eng.ten_thousand_hours(daily_hours=10, current_hours=0,
                                    start_date="2026-01-01")
        # 1000 days from 2026-01-01
        self.assertEqual(r["days_to_complete"], 1000)
        # Quick sanity check: end date is well-formed
        self.assertEqual(len(r["completion_date"]), 10)
        self.assertTrue(r["completion_date"].startswith("2028"))

    def test_academic_source_present(self):
        r = eng.ten_thousand_hours(daily_hours=2)
        self.assertIn("Ericsson", r["academic_source"])
        self.assertIn("1993", r["academic_source"])
        self.assertIn("Psychological Review", r["academic_source"])

    def test_caveat_present(self):
        r = eng.ten_thousand_hours(daily_hours=2)
        self.assertIn("deliberate practice", r["caveat"])


class TestQuoteLookup(unittest.TestCase):
    def setUp(self):
        self.data = eng.load_data()

    def test_valid_quote_key(self):
        q = eng.get_quote(self.data, "S_INTUITION_8090")
        self.assertIn("80~90%", q)

    def test_a_10000_hours_quote(self):
        q = eng.get_quote(self.data, "A_10000_HOURS")
        self.assertIn("1만 시간", q)

    def test_invalid_quote_raises(self):
        with self.assertRaises(KeyError):
            eng.get_quote(self.data, "NONEXISTENT")


class TestAcademicSources(unittest.TestCase):
    def setUp(self):
        self.data = eng.load_data()

    def test_ericsson_1993(self):
        s = eng.get_source(self.data, "ERICSSON_1993")
        self.assertEqual(s["year"], 1993)
        self.assertIn("Psychological Review", s["venue"])
        self.assertIn("363-406", s["venue"])

    def test_falkenstein_1990(self):
        s = eng.get_source(self.data, "ERN_1990")
        self.assertEqual(s["discoverer"], "Michael Falkenstein")
        self.assertEqual(s["year_first"], 1990)

    def test_galton_1907(self):
        s = eng.get_source(self.data, "GALTON_1907")
        self.assertEqual(s["year"], 1907)
        self.assertIn("Vox Populi", s["primary_citation"])

    def test_mortara_2009(self):
        s = eng.get_source(self.data, "MORTARA_2009")
        self.assertEqual(s["year"], 2009)
        self.assertIn("Cambridge", s["institution"])

    def test_carr_1961(self):
        s = eng.get_source(self.data, "CARR_1961")
        self.assertEqual(s["year"], 1961)
        self.assertIn("What is History", s["primary_citation"])

    def test_sartre_1940(self):
        s = eng.get_source(self.data, "SARTRE_1940")
        self.assertEqual(s["year"], 1940)
        self.assertIn("L'Imaginaire", s["primary_citation"])

    def test_getty_autobio(self):
        s = eng.get_source(self.data, "GETTY_AUTOBIO")
        self.assertIn("As I See It", s["primary_citation"])

    def test_ockham_razor(self):
        s = eng.get_source(self.data, "OCKHAM_RAZOR")
        self.assertIn("Frustra fit per plura", s["latin_quote"])

    def test_invalid_source_raises(self):
        with self.assertRaises(KeyError):
            eng.get_source(self.data, "NONEXISTENT_2025")


class TestTrainingMethods(unittest.TestCase):
    def setUp(self):
        self.data = eng.load_data()

    def test_S_has_3_trainings(self):
        t = eng.get_training(self.data, "S")
        self.assertEqual(t["training_count"], 3)
        self.assertEqual(len(t["items"]), 3)

    def test_A_has_7_trainings_plus_10k(self):
        t = eng.get_training(self.data, "A")
        self.assertEqual(t["training_count"], 7)
        self.assertEqual(len(t["items"]), 7)
        self.assertEqual(t["ten_thousand_hours"], 10000)

    def test_M_split_thinking_work(self):
        t = eng.get_training(self.data, "M")
        self.assertEqual(t["thinking_training_count"], 3)
        self.assertEqual(t["work_training_count"], 3)
        self.assertEqual(len(t["thinking"]), 3)
        self.assertEqual(len(t["work"]), 3)

    def test_T_has_3_trainings(self):
        t = eng.get_training(self.data, "T")
        self.assertEqual(t["training_count"], 3)


class TestCLI(unittest.TestCase):
    """End-to-end CLI test via subprocess."""

    def _run(self, args: list[str]) -> tuple[int, str, str]:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)] + args,
            capture_output=True, text=True
        )
        return result.returncode, result.stdout, result.stderr

    def test_cli_facts_competences(self):
        rc, out, err = self._run(["facts", "--query", "competences"])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertEqual(len(data), 5)

    def test_cli_facts_countries(self):
        rc, out, err = self._run(["facts", "--query", "countries"])
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["count"], 12)

    def test_cli_assess(self):
        rc, out, err = self._run([
            "assess", "--scores", '{"S":3,"M":4,"A":6,"R":8,"T":5}'
        ])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertEqual(data["average"], 5.2)

    def test_cli_tenkhour(self):
        rc, out, err = self._run([
            "tenkhour", "--daily-hours", "2",
            "--current-hours", "0",
            "--start-date", "2026-01-01"
        ])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertEqual(data["days_to_complete"], 5000)

    def test_cli_map_smart(self):
        rc, out, err = self._run(["map", "--smart-keys", "SAT"])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        codes = [m["code"] for m in data]
        self.assertIn("TOOLS", codes)

    def test_cli_map_deseco(self):
        rc, out, err = self._run(["map", "--deseco-code", "TOOLS"])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertEqual(set(data["smart_keys"]), {"S", "A", "T"})

    def test_cli_quote(self):
        rc, out, err = self._run(["quote", "--key", "A_10000_HOURS"])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertIn("1만 시간", data["quote"])

    def test_cli_invalid_score_returns_error(self):
        rc, out, err = self._run([
            "validate", "--scores", '{"S":11,"M":4,"A":6,"R":8,"T":5}'
        ])
        self.assertEqual(rc, 2)
        data = json.loads(err)
        self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
