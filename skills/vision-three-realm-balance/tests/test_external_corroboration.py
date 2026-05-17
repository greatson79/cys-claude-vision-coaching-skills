"""학계 외부 출처 결정론 모듈 단위 테스트."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import external_corroboration as ext  # noqa: E402


class TestRegisteredSources(unittest.TestCase):
    def test_five_sources_registered(self):
        self.assertEqual(len(ext.list_sources()), 5)

    def test_unique_keys(self):
        keys = [s.key for s in ext.list_sources()]
        self.assertEqual(len(set(keys)), 5)

    def test_expected_keys_present(self):
        keys = {s.key for s in ext.list_sources()}
        for k in [
            "sdt_deci_ryan", "frankl_logotherapy", "seligman_perma",
            "ikigai_western_venn", "aristotle_eudaimonia",
        ]:
            self.assertIn(k, keys)

    def test_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            ext.get_source("not_a_real_key")

    def test_each_source_has_full_metadata(self):
        for s in ext.list_sources():
            self.assertTrue(s.model_name, msg=s.key)
            self.assertTrue(s.authors, msg=s.key)
            self.assertTrue(s.primary_text, msg=s.key)
            self.assertGreaterEqual(len(s.elements), 3, msg=s.key)
            self.assertGreaterEqual(len(s.citation_source_urls), 2, msg=s.key)
            # 박사님 3영역에 대한 매핑이 모두 존재
            for realm in (1, 2, 3):
                self.assertIn(realm, s.mapping_to_cys, msg=f"{s.key} realm={realm}")
                self.assertTrue(s.mapping_to_cys[realm], msg=f"{s.key} realm={realm}")


class TestURLFormat(unittest.TestCase):
    def test_all_urls_valid_format(self):
        self.assertTrue(ext.all_urls_valid())

    def test_url_format_helper(self):
        self.assertTrue(ext.verify_url_format("https://en.wikipedia.org/wiki/X"))
        self.assertTrue(ext.verify_url_format("http://example.org/path"))
        self.assertFalse(ext.verify_url_format(""))
        self.assertFalse(ext.verify_url_format("not a url"))
        self.assertFalse(ext.verify_url_format("https://"))


class TestMappings(unittest.TestCase):
    def test_frankl_attitudinal_to_realm3(self):
        m = ext.realms_for("frankl_logotherapy")
        self.assertIn("Attitudinal", m[3])

    def test_seligman_meaning_to_realm3(self):
        m = ext.realms_for("seligman_perma")
        self.assertIn("Meaning", m[3])

    def test_sdt_relatedness_to_realm2(self):
        m = ext.realms_for("sdt_deci_ryan")
        self.assertIn("Relatedness", m[2])

    def test_ikigai_realm3_acknowledges_gap(self):
        m = ext.realms_for("ikigai_western_venn")
        # 박사님 ③에 대응 영역이 없음을 명시적으로 표시해야 한다
        self.assertTrue("없음" in m[3] or "부재" in m[3] or "직접 매핑" in m[3])

    def test_aristotle_virtue_to_realm3(self):
        m = ext.realms_for("aristotle_eudaimonia")
        self.assertTrue("virtue" in m[3].lower() or "미덕" in m[3] or "Virtue" in m[3])


class TestRendering(unittest.TestCase):
    def test_render_single_includes_authors_and_urls(self):
        out = ext.render_corroboration("sdt_deci_ryan")
        self.assertIn("Deci", out)
        self.assertIn("Ryan", out)
        self.assertIn("https://", out)
        for label in ext.CYS_REALM_LABELS.values():
            self.assertIn(label, out)

    def test_render_all_contains_five_models(self):
        out = ext.render_all_corroboration()
        for s in ext.list_sources():
            self.assertIn(s.model_name.split(" ")[0], out)
        self.assertIn("박사님 모델의 차별점", out)

    def test_render_all_contains_disclaimer(self):
        out = ext.render_all_corroboration()
        # 박사님 책이 동료심사 학술지가 아님을 정직하게 명시
        self.assertIn("동료심사 학술지 출간이 아닙니다", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
