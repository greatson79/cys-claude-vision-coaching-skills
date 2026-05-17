"""vision-three-realm-balance 결정론 모듈 단위 테스트."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# 프로젝트 lib을 임포트하기 위한 경로 추가
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from lib import realm_balance as rb  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_ok_tokens(self):
        for tok in ["O", "o", "○", "예", "강함", "yes", "Y", "1", "true"]:
            self.assertEqual(rb.normalize_mark(tok), "O", msg=tok)

    def test_mid_tokens(self):
        for tok in ["△", "M", "mid", "보통", "애매", "부분", "0.5"]:
            self.assertEqual(rb.normalize_mark(tok), "M", msg=tok)

    def test_x_tokens(self):
        for tok in ["X", "x", "✗", "아니오", "약함", "no", "N", "0"]:
            self.assertEqual(rb.normalize_mark(tok), "X", msg=tok)

    def test_unknown_token_raises(self):
        with self.assertRaises(ValueError):
            rb.normalize_mark("???")

    def test_normalize_triple_length(self):
        with self.assertRaises(ValueError):
            rb.normalize_triple(["O", "O"])

    def test_conservative_collapse(self):
        self.assertEqual(rb.conservative_collapse(("M", "O", "M")), ("X", "O", "X"))
        self.assertEqual(rb.conservative_collapse(("O", "O", "O")), ("O", "O", "O"))


class TestDiagnose(unittest.TestCase):
    """SKILL.md '3단계 — 8개 패턴' 표와 1:1 일치하는지 검증."""

    EXPECTED = {
        ("O", "O", "O"): ("건강한 비전", "없음", ()),
        ("O", "O", "X"): ("정신적 가치 결여", "중", (3,)),
        ("O", "X", "O"): ("가족·세상 단절", "중", (2,)),
        ("X", "O", "O"): ("자기 기쁨 부재", "중", (1,)),
        ("O", "X", "X"): ("개인 욕망", "높음", (2, 3)),
        ("X", "O", "X"): ("자기희생·세상일", "높음", (1, 3)),
        ("X", "X", "O"): ("왜곡된 사명·질", "높음", (1, 2)),
        ("X", "X", "X"): ("비전 아님", "최고", (1, 2, 3)),
    }

    def test_all_eight_patterns(self):
        for triple, (name, risk, weak) in self.EXPECTED.items():
            d = rb.diagnose(triple)
            self.assertEqual(d.name, name, msg=f"{triple}")
            self.assertEqual(d.risk, risk, msg=f"{triple}")
            self.assertEqual(d.weak_realms, weak, msg=f"{triple}")

    def test_healthy_flag(self):
        self.assertTrue(rb.diagnose(("O", "O", "O")).is_healthy)
        for triple in [("O", "O", "X"), ("X", "X", "X"), ("X", "O", "X")]:
            self.assertFalse(rb.diagnose(triple).is_healthy, msg=triple)

    def test_mid_collapses_to_x(self):
        # △는 보수적으로 ✗ 처리 → ("O","M","O")는 ("O","X","O") = '가족·세상 단절'
        d = rb.diagnose(("O", "M", "O"))
        self.assertEqual(d.name, "가족·세상 단절")

    def test_korean_mark_input(self):
        d = rb.diagnose(("○", "○", "✗"))
        self.assertEqual(d.name, "정신적 가치 결여")

    def test_all_patterns_unique(self):
        names = [d.name for d in rb.all_patterns()]
        self.assertEqual(len(set(names)), 8)


class TestAddress(unittest.TestCase):
    def test_doctor_self_returns_doctor(self):
        for sig in [
            "최윤식 박사 본인 비전 점검",
            "박사님 본인 비전",
            "저는 최윤식 박사입니다",
            "박사님이 직접 점검",
        ]:
            self.assertEqual(rb.resolve_address(sig), "박사님", msg=sig)

    def test_default_is_dangsin(self):
        for sig in ["일반 사용자입니다", "청년부 학생", "", None, "30대 직장인"]:
            self.assertEqual(rb.resolve_address(sig), "당신", msg=sig)

    def test_no_doctor_for_plain_pastor(self):
        # 박사가 아닌 일반 목사·청년에게 박사님 호칭이 잘못 붙지 않아야 함
        self.assertEqual(rb.resolve_address("저는 부목사입니다"), "당신")


class TestClassifyInput(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(rb.classify_input_type(""), "EMPTY")
        self.assertEqual(rb.classify_input_type("   "), "EMPTY")
        self.assertEqual(rb.classify_input_type("저는 비전이 없어요"), "EMPTY")
        self.assertEqual(rb.classify_input_type("무엇을 비전으로 삼아야 할지 모르겠어요"), "EMPTY")

    def test_meta(self):
        for q in [
            "3겹 다이어그램이 뭔가요?",
            "이 도구 어떻게 활용?",
            "한 영역에 치우쳤는지 어떻게 알 수 있어요?",
        ]:
            self.assertEqual(rb.classify_input_type(q), "META", msg=q)

    def test_type_c(self):
        self.assertEqual(rb.classify_input_type("최윤식 박사 본인 비전을 점검하고 싶다"), "C")

    def test_type_b(self):
        for q in [
            "이 비전 후보 3개 중 어느 것이 가장 균형 잡혔나?",
            "비전 후보 A vs B 비교해주세요",
            "두 비전 중 둘 중 고르고 싶습니다",
        ]:
            self.assertEqual(rb.classify_input_type(q), "B", msg=q)

    def test_type_d(self):
        for q in [
            "교회 청년부 세미나 30분 진행 안내",
            "수련회 워크숍 흐름 짜주세요",
            "강의 도입부 어떻게 시작?",
        ]:
            self.assertEqual(rb.classify_input_type(q), "D", msg=q)

    def test_type_a_default(self):
        self.assertEqual(
            rb.classify_input_type("저는 청소년 진로 멘토링을 평생 하고 싶습니다"), "A"
        )


class TestSpecialCases(unittest.TestCase):
    def test_time_phased(self):
        hits = rb.detect_special_cases("10년 후 의사가 되고 20년 후 의료 선교사가 되겠다")
        self.assertTrue(any(h.name == "time_phased" for h in hits))

    def test_role_split(self):
        hits = rb.detect_special_cases("직장에서는 A를 추구하고 가정에서는 B를 추구")
        self.assertTrue(any(h.name == "role_split" for h in hits))

    def test_other_oriented(self):
        hits = rb.detect_special_cases("자녀가 의대에 가기를 바라는 게 제 비전입니다")
        self.assertTrue(any(h.name == "other_oriented" for h in hits))

    def test_eschatological(self):
        hits = rb.detect_special_cases("천국에서 영원히 하나님 영광을 찬양하는 것")
        self.assertTrue(any(h.name == "eschatological" for h in hits))

    def test_quantification(self):
        hits = rb.detect_special_cases("100점 만점으로 환산해서 점수화 해주세요")
        self.assertTrue(any(h.name == "quantification" for h in hits))

    def test_external_model(self):
        hits = rb.detect_special_cases("ikigai 모델과 비교해주세요")
        self.assertTrue(any(h.name == "external_model" for h in hits))

    def test_concept_compare(self):
        hits = rb.detect_special_cases("비전 vs 꿈 vs 목표 차이가 뭔가요")
        self.assertTrue(any(h.name == "concept_compare" for h in hits))

    def test_quick_mode(self):
        hits = rb.detect_special_cases("짧게 결과만 알려주세요")
        self.assertTrue(any(h.name == "quick_mode" for h in hits))

    def test_negative_vision(self):
        hits = rb.detect_special_cases("절대 가난해지지 않겠다는 게 제 비전")
        self.assertTrue(any(h.name == "negative_vision" for h in hits))

    def test_no_match(self):
        self.assertEqual(rb.detect_special_cases("저는 청소년 멘토가 되고 싶어요"), [])


class TestQuotes(unittest.TestCase):
    def test_all_quote_keys_resolvable(self):
        for key in rb.CYS_QUOTES:
            self.assertTrue(rb.get_quote(key))

    def test_verify_exact_match(self):
        for key, text in rb.CYS_QUOTES.items():
            self.assertTrue(rb.verify_quote(key, text), msg=key)

    def test_verify_paraphrase_rejected(self):
        # 한 글자만 바뀌어도 False
        bad = rb.CYS_QUOTES["role_opening"].replace("강한", "센")
        self.assertFalse(rb.verify_quote("role_opening", bad))

    def test_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            rb.get_quote("does_not_exist")

    def test_render_quote_contains_source(self):
        out = rb.render_quote("closing")
        self.assertIn("최윤식 박사", out)
        self.assertIn("미래준비학교", out)
        self.assertIn("2016", out)


class TestPrinciples(unittest.TestCase):
    def test_ten_principles(self):
        ps = rb.list_principles()
        self.assertEqual(len(ps), 10)
        keys = {p[0] for p in ps}
        # 핵심 10개 keyword 모두 존재
        for k in [
            "realm_names", "simultaneous", "ethics_only", "sacrifice_only",
            "desire_only", "healthy", "citation", "address",
            "no_hallucination", "no_page_guess",
        ]:
            self.assertIn(k, keys, msg=k)


class TestAnalyzeIntegration(unittest.TestCase):
    def test_empty_routes_to_clarity(self):
        r = rb.analyze("저는 비전이 없어요")
        self.assertEqual(r.input_type, "EMPTY")
        self.assertTrue(any("clarity" in n for n in r.notes))
        self.assertIsNone(r.diagnosis)

    def test_doctor_with_triple(self):
        r = rb.analyze(
            "박사님 본인 비전을 점검",
            triple=("O", "O", "O"),
        )
        self.assertEqual(r.address, "박사님")
        self.assertEqual(r.input_type, "C")
        self.assertIsNotNone(r.diagnosis)
        self.assertEqual(r.diagnosis.name, "건강한 비전")

    def test_b_type_no_diagnose(self):
        r = rb.analyze("후보 A, B, C 중 비교")
        self.assertEqual(r.input_type, "B")
        self.assertIsNone(r.diagnosis)

    def test_quantification_special_case(self):
        r = rb.analyze("이 비전을 100점 만점으로 점수화 해주세요")
        names = [c.name for c in r.special_cases]
        self.assertIn("quantification", names)


if __name__ == "__main__":
    unittest.main(verbosity=2)
