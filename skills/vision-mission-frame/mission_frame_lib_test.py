"""vision-mission-frame — 결정론적 헬퍼 라이브러리 테스트.

실행:
    python3 mission_frame_lib_test.py
"""

from __future__ import annotations

import sys
import unittest

import mission_frame_lib as lib


class HonorificTests(unittest.TestCase):
    def test_doctor(self):
        self.assertEqual(lib.select_honorific({"is_doctor": True}), "박사님")

    def test_title(self):
        self.assertEqual(lib.select_honorific({"title": "목사"}), "목사님")
        self.assertEqual(lib.select_honorific({"title": "교수님"}), "교수님")

    def test_name_only(self):
        self.assertEqual(lib.select_honorific({"name": "지수"}), "지수님")

    def test_default(self):
        self.assertEqual(lib.select_honorific(None), "선생님")
        self.assertEqual(lib.select_honorific({}), "선생님")

    def test_doctor_priority(self):
        # is_doctor=True가 title보다 우선
        self.assertEqual(
            lib.select_honorific({"is_doctor": True, "title": "목사"}),
            "박사님",
        )


class InputTypeTests(unittest.TestCase):
    def test_default_full_check(self):
        self.assertEqual(lib.classify_input_type("비전 프레임 점검해줘"), "A")
        self.assertEqual(lib.classify_input_type(""), "A")

    def test_type_d_doctor(self):
        self.assertEqual(lib.classify_input_type("박사님 본인 비전 점검"), "D")
        self.assertEqual(lib.classify_input_type("내가 박사인데 점검"), "D")

    def test_type_c_loop_only(self):
        self.assertEqual(lib.classify_input_type("강화 피드백 루프만 진단"), "C")
        self.assertEqual(lib.classify_input_type("두 축이 서로 강화되는지"), "C")
        self.assertEqual(lib.classify_input_type("(r) loop 점검"), "C")

    def test_type_b_spiritual(self):
        self.assertEqual(lib.classify_input_type("영적 직관력만 점검"), "B-spiritual")
        self.assertEqual(lib.classify_input_type("영감만 봐줘"), "B-spiritual")

    def test_type_b_rational(self):
        self.assertEqual(lib.classify_input_type("이성적 판단력만 점검"), "B-rational")
        self.assertEqual(lib.classify_input_type("정보만 봐줘"), "B-rational")
        self.assertEqual(lib.classify_input_type("예측 구성만"), "B-rational")

    def test_type_b_generic_falls_to_spiritual(self):
        # 한 축이라고만 한 경우 기본값으로 B-spiritual
        self.assertEqual(lib.classify_input_type("한 축만 봐줘"), "B-spiritual")

    def test_stages_for_type(self):
        self.assertEqual(lib.stages_for_type("A"), [1, 2, 3, 4, 5, 6])
        self.assertEqual(lib.stages_for_type("B-spiritual"), [1, 2, 3, 6])
        self.assertEqual(lib.stages_for_type("B-rational"), [1, 4, 6])
        self.assertEqual(lib.stages_for_type("C"), [1, 5])
        self.assertEqual(lib.stages_for_type("D"), [2, 4, 5, 6])


class ReligionContextTests(unittest.TestCase):
    def test_religious(self):
        self.assertEqual(lib.detect_religion_context("기도하면서 영감을"), "religious")
        self.assertEqual(lib.detect_religion_context("성경 묵상 중"), "religious")
        self.assertEqual(lib.detect_religion_context("교회 청년부 코칭"), "religious")

    def test_unknown(self):
        self.assertEqual(lib.detect_religion_context("내 비전 점검해줘"), "unknown")

    def test_explicit_override(self):
        self.assertEqual(
            lib.detect_religion_context("기도", explicit="secular"),
            "secular",
        )

    def test_criterion_mapping(self):
        self.assertEqual(lib.divine_value_criterion("religious"), "경전·신앙 기준")
        self.assertEqual(lib.divine_value_criterion("secular"), "윤리·도덕·양심 기준")
        self.assertIn("윤리", lib.divine_value_criterion("unknown"))


class AuthorizedQuotesTests(unittest.TestCase):
    def test_quote_count(self):
        # 박사님 책 허용 인용은 최소 11개 (SKILL.md 명시)
        self.assertGreaterEqual(len(lib.AUTHORIZED_QUOTES), 11)

    def test_verify_match(self):
        # 정의문 일치
        result = lib.verify_quote(
            "비전 프레임이란 '가치 있는 + 시대적 + 소명'이 어떻게 성장하는지를 "
            "설명하기 위해 필자가 만든 단어이다."
        )
        self.assertTrue(result["match"])
        self.assertEqual(result["matched_index"], 0)

    def test_verify_partial_match(self):
        # 부분 인용 (안에 포함)
        result = lib.verify_quote("외부로부터 주어지는 영감")
        self.assertTrue(result["match"])

    def test_verify_punctuation_insensitive(self):
        # 공백·따옴표 차이 흡수
        result = lib.verify_quote(
            '비전 프레임이란 "가치 있는 + 시대적 + 소명"이 어떻게 성장하는지를 '
            '설명하기 위해 필자가 만든 단어이다.'
        )
        self.assertTrue(result["match"])

    def test_verify_unauthorized(self):
        # SKILL.md에 없는 가공된 인용 → 검출
        result = lib.verify_quote("박사님은 비전이란 결국 자기 발견이라 하셨다")
        self.assertFalse(result["match"])

    def test_verify_empty(self):
        self.assertFalse(lib.verify_quote("")["match"])


class MapDefinitionTests(unittest.TestCase):
    def test_three_phrases(self):
        r = lib.map_vision_definition_phrase("가치 있는")
        self.assertIn("영적 직관력", r["axis"])
        r = lib.map_vision_definition_phrase("시대적")
        self.assertIn("예측 구성", r["axis"])
        r = lib.map_vision_definition_phrase("소명")
        self.assertIn("정보", r["axis"])

    def test_invalid_phrase(self):
        r = lib.map_vision_definition_phrase("의미있는")
        self.assertIn("error", r)


class ThreeRealmTests(unittest.TestCase):
    def test_all_three(self):
        r = lib.classify_three_realm_check(True, True, True)
        self.assertEqual(r["status"], "PASS")
        self.assertIn("진정한 비전", r["label"])

    def test_only_self(self):
        r = lib.classify_three_realm_check(True, False, False)
        self.assertEqual(r["status"], "WARN")
        self.assertEqual(r["label"], "개인 욕망 (나만 기쁨)")

    def test_only_others(self):
        r = lib.classify_three_realm_check(False, True, False)
        self.assertIn("자기희생", r["label"])

    def test_only_moral(self):
        r = lib.classify_three_realm_check(False, False, True)
        self.assertIn("왜곡된 사명", r["label"])

    def test_self_plus_others(self):
        r = lib.classify_three_realm_check(True, True, False)
        self.assertIn("정신적 가치 누락", r["label"])

    def test_self_plus_moral(self):
        r = lib.classify_three_realm_check(True, False, True)
        self.assertIn("이웃·세상 부재", r["label"])

    def test_others_plus_moral(self):
        r = lib.classify_three_realm_check(False, True, True)
        self.assertIn("자기 부재", r["label"])

    def test_none(self):
        r = lib.classify_three_realm_check(False, False, False)
        self.assertEqual(r["status"], "FAIL")

    def test_all_warns_have_redefinition(self):
        # 모든 WARN 케이스에 재정의 안내 존재
        for flags in [(True, False, False), (False, True, False), (False, False, True),
                      (True, True, False), (True, False, True), (False, True, True)]:
            r = lib.classify_three_realm_check(*flags)
            self.assertIsNotNone(r["redefinition_prompt"], f"flags={flags}")


class LoopDiagnosisTests(unittest.TestCase):
    def test_balanced_strong(self):
        r = lib.diagnose_loop("strong", "strong")
        self.assertEqual(r["strong_axis"], "균형")
        self.assertEqual(r["weak_axis_key"], "없음")
        self.assertIn("Reinforcing", r["loop_status"])

    def test_spiritual_weak(self):
        r = lib.diagnose_loop("weak", "strong")
        self.assertIn("이성적", r["strong_axis"])
        self.assertEqual(r["weak_axis_key"], "spiritual")
        self.assertIn("해야 하는 일", r["weakness_symptoms"])

    def test_rational_weak(self):
        r = lib.diagnose_loop("strong", "weak")
        self.assertIn("영적", r["strong_axis"])
        self.assertEqual(r["weak_axis_key"], "rational")
        self.assertIn("막연한 꿈", r["weakness_symptoms"])

    def test_both_weak(self):
        r = lib.diagnose_loop("weak", "weak")
        self.assertIn("위기", r["loop_status"])

    def test_invalid_value(self):
        r = lib.diagnose_loop("unknown", "strong")
        self.assertIn("error", r)


class DriftDetectionTests(unittest.TestCase):
    def test_clean(self):
        text = "영적 직관력은 영감과 정신적 가치로 구성된다. 이성적 판단력과 (R) 강화 피드백 루프로 작동한다."
        r = lib.detect_doctrinal_drift(text)
        self.assertTrue(r["clean"])

    def test_drift_axis1_rewrite(self):
        text = "비전 프레임의 두 축은 정신적 직관력과 감정적 판단력이다"
        r = lib.detect_doctrinal_drift(text)
        self.assertFalse(r["clean"])

    def test_drift_reverse_loop(self):
        text = "(R) 약화 피드백 루프로 비전이 자란다"
        r = lib.detect_doctrinal_drift(text)
        self.assertFalse(r["clean"])

    def test_definition_format_check(self):
        text = "비전 = 가치 있는 시대적 소명"
        r = lib.detect_doctrinal_drift(text)
        self.assertFalse(r["clean"])


class LinkedSkillsTests(unittest.TestCase):
    def test_spiritual_recs(self):
        recs = lib.recommend_linked_skills("spiritual")
        skills = [r["skill"] for r in recs]
        self.assertIn("vision-clarity-coaching", skills)
        self.assertIn("vision-three-realm-balance", skills)

    def test_rational_recs(self):
        recs = lib.recommend_linked_skills("rational")
        skills = [r["skill"] for r in recs]
        self.assertIn("vision-cys-competence-visioncoding", skills)
        self.assertIn("vision-futures-timeline-map", skills)

    def test_post_frame_only(self):
        recs = lib.recommend_linked_skills(None, "post_frame")
        skills = [r["skill"] for r in recs]
        self.assertIn("vision-statement-writer", skills)

    def test_both_mode_dedup(self):
        recs = lib.recommend_linked_skills(None, "both")
        skills = [r["skill"] for r in recs]
        # 중복 없음
        self.assertEqual(len(skills), len(set(skills)))


class ReportValidationTests(unittest.TestCase):
    def test_full_skeleton_passes(self):
        skel = lib.format_report_skeleton("박사님", "A")
        r = lib.validate_report_structure(skel)
        self.assertTrue(r["valid"], f"missing={r.get('missing')}")

    def test_partial_skeleton_passes_partial(self):
        skel = lib.format_report_skeleton("박사님", "C")
        r = lib.validate_report_structure(skel, partial=True)
        self.assertTrue(r["valid"], f"missing={r.get('missing')}")

    def test_empty_fails(self):
        r = lib.validate_report_structure("")
        self.assertFalse(r["valid"])

    def test_missing_sections_detected(self):
        r = lib.validate_report_structure("# 점검 보고서\n## 영적 직관력")
        self.assertFalse(r["valid"])
        self.assertGreater(len(r["missing"]), 0)


class EmojiCheckTests(unittest.TestCase):
    def test_clean(self):
        r = lib.emoji_check("도식: ○ △ ✗ ↑↓")
        self.assertTrue(r["clean"])

    def test_with_emoji(self):
        r = lib.emoji_check("축하해요 🎉")
        self.assertFalse(r["clean"])


class FormatReportTests(unittest.TestCase):
    def test_full_contains_required_terms(self):
        skel = lib.format_report_skeleton("박사님", "A")
        for sec in ("영적 직관력", "이성적 판단력", "(R) 강화 피드백 루프", "가치 있는", "시대적", "소명"):
            self.assertIn(sec, skel)

    def test_loop_only_skeleton(self):
        skel = lib.format_report_skeleton("박사님", "C")
        self.assertIn("(R) 강화 피드백 루프", skel)

    def test_partial_skeleton_spiritual(self):
        skel = lib.format_report_skeleton("박사님", "B-spiritual")
        self.assertIn("영적 직관력", skel)

    def test_partial_skeleton_rational(self):
        skel = lib.format_report_skeleton("박사님", "B-rational")
        self.assertIn("이성적 판단력", skel)


if __name__ == "__main__":
    unittest.main(verbosity=2)
