"""Unit tests for the deterministic core. Run: python3 -m pytest -xvs (or plain run)."""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.catalog import (  # noqa: E402
    TYPE_KEYS,
    education_rank,
    get_age_category,
    jobs_in_type,
    load_catalog,
    normalize_education,
)
from lib.dedup import assert_no_duplicates  # noqa: E402
from lib.filter_jobs import classify_fit, select_top5  # noqa: E402
from lib.language import detect_language  # noqa: E402
from lib.output_validator import validate_markdown, validate_plan_structure  # noqa: E402
from lib.pipeline import UserProfile, build_plan  # noqa: E402
from lib.rationale import derive_profile_keys, find_matches  # noqa: E402
from lib.render import render_markdown  # noqa: E402


class TestCatalog(unittest.TestCase):
    def test_four_types_present(self):
        cat = load_catalog()
        for t in TYPE_KEYS:
            self.assertIn(t, cat["jobs"], f"Missing type {t}")
            self.assertGreaterEqual(len(cat["jobs"][t]), 20, f"{t} has fewer than 20 master entries")

    def test_education_synonyms(self):
        self.assertEqual(normalize_education("고졸"), "high")
        self.assertEqual(normalize_education("BACHELOR"), "bachelor")
        self.assertEqual(normalize_education("박사"), "doctorate")
        self.assertEqual(normalize_education("2년제"), "college2yr")
        self.assertIsNone(normalize_education("xyz"))

    def test_education_rank(self):
        self.assertLess(education_rank("high"), education_rank("bachelor"))
        self.assertLess(education_rank("bachelor"), education_rank("doctorate"))

    def test_age_category(self):
        self.assertEqual(get_age_category(15)["id"], "youth")
        self.assertEqual(get_age_category(30)["id"], "early_career")
        self.assertEqual(get_age_category(80)["id"], "elderly")

    def test_no_duplicate_ids_in_catalog(self):
        seen = set()
        for t in TYPE_KEYS:
            for j in jobs_in_type(t):
                self.assertNotIn(j["id"], seen, f"Duplicate id within catalog: {j['id']}")
                seen.add(j["id"])

    def test_all_jobs_have_required_fields(self):
        required = ["id", "ko", "en", "min_education", "min_age", "max_age"]
        for t in TYPE_KEYS:
            for j in jobs_in_type(t):
                for k in required:
                    self.assertIn(k, j, f"{t}/{j.get('id')} missing {k}")


class TestFilter(unittest.TestCase):
    def test_youth_fails_doctor(self):
        physician = next(j for j in jobs_in_type("high_pay") if j["id"] == "physician")
        v, _ = classify_fit(physician, age=15, education="middle")
        self.assertEqual(v, "fail")

    def test_high_school_fails_lawyer(self):
        lawyer = next(j for j in jobs_in_type("high_pay") if j["id"] == "lawyer_big_firm")
        v, _ = classify_fit(lawyer, age=30, education="high")
        self.assertEqual(v, "fail")

    def test_phd_passes_writer(self):
        writer = next(j for j in jobs_in_type("happy_fun") if j["id"] == "writer")
        v, _ = classify_fit(writer, age=45, education="doctorate")
        self.assertEqual(v, "pass")

    def test_elderly_fails_synbio(self):
        synbio = next(j for j in jobs_in_type("future") if j["id"] == "synbio_researcher")
        v, _ = classify_fit(synbio, age=80, education="doctorate")
        self.assertEqual(v, "fail")

    def test_borderline_education_one_below(self):
        ai_eth = next(j for j in jobs_in_type("future") if j["id"] == "ai_ethicist")
        v, _ = classify_fit(ai_eth, age=30, education="college2yr")
        self.assertEqual(v, "borderline")

    def test_unknown_when_no_filter_data(self):
        writer = next(j for j in jobs_in_type("happy_fun") if j["id"] == "writer")
        v, _ = classify_fit(writer, age=None, education=None)
        self.assertEqual(v, "unknown")

    def test_select_top5_always_returns_5(self):
        plan = select_top5("future", age=25, education="bachelor")
        self.assertEqual(len(plan["slots"]), 5)

    def test_faith_jobs_excluded_when_not_disclosed(self):
        plan = select_top5("retirement", age=65, education="bachelor", include_faith_jobs=False)
        ids = [j["id"] for j in plan["slots"]]
        faith_ids = {"church_lay_ministry", "seminary_lecturer", "mission_advisor", "christian_ngo_board", "interfaith_dialogue"}
        self.assertFalse(faith_ids & set(ids))


class TestDedup(unittest.TestCase):
    def test_pipeline_has_no_duplicates(self):
        prof = UserProfile(age=30, education="bachelor", raw_input="직업 추천")
        out = build_plan(prof)
        problems = assert_no_duplicates(out["plan"])
        self.assertEqual(problems, [], f"Duplicates found: {problems}")

    def test_all_types_have_5(self):
        prof = UserProfile(age=30, education="bachelor", raw_input="직업 추천")
        out = build_plan(prof)
        for t in TYPE_KEYS:
            self.assertEqual(len(out["plan"][t]["slots"]), 5, f"{t} has wrong slot count")


class TestLanguage(unittest.TestCase):
    def test_korean_detected(self):
        self.assertEqual(detect_language("안녕하세요 직업 추천해주세요"), "ko")

    def test_english_detected(self):
        self.assertEqual(detect_language("Please recommend a career for me"), "en")

    def test_mixed_directive_last_wins(self):
        self.assertEqual(detect_language("hello world 한국어로 답해주세요"), "ko")
        self.assertEqual(detect_language("안녕하세요 respond in english please"), "en")

    def test_empty(self):
        self.assertEqual(detect_language(""), "ko")


class TestValidator(unittest.TestCase):
    def test_plan_structure_ok(self):
        prof = UserProfile(age=30, education="bachelor", raw_input="직업 추천")
        out = build_plan(prof)
        self.assertEqual(validate_plan_structure(out["plan"]), [])

    def test_short_markdown_fails(self):
        ok, problems = validate_markdown("# 짧은 글", expected_language="ko")
        self.assertFalse(ok)
        self.assertTrue(any("short" in p.lower() for p in problems))

    def test_full_markdown_ok(self):
        md = """# 직업 추천 결과

## Type 1 — Future Jobs 🚀
### 1. AI 윤리 컨설턴트
설명""" + ("가" * 300) + """
### 2. SMR 기술자
설명""" + ("가" * 100) + """
### 3. 정밀의료 데이터 사이언티스트
설명
### 4. 기후 적응 도시 설계자
설명
### 5. Human-AI Interaction Designer
설명

## Type 2 — Happy & Fun 😊
### 1. 작가
설명
### 2. 큐레이터
설명
### 3. 음악치료사
설명
### 4. 사진작가
설명
### 5. 여행 작가
설명

## Type 3 — Retirement Volunteering ⛪
### 1. 청년 커리어 멘토
설명
### 2. NGO 자문
설명
### 3. 도슨트
설명
### 4. 학교 밖 청소년 멘토
설명
### 5. 환경 보전
설명

## Type 4 — High-Pay Current 💰
### 1. 의사
설명
### 2. 변호사
설명
### 3. 회계사
설명
### 4. 빅테크 SW 엔지니어
설명
### 5. C-Suite Advisor
설명

## 직무 형태(Work Type)
조직 내 vs 프리랜서 등 안내.

## 한계·주의
시뮬레이션 한계 명시.

## 다음 단계
vision-clarity-coaching 다음 단계 안내.
""" + ("가" * 500)
        ok, problems = validate_markdown(md, expected_language="ko")
        self.assertTrue(ok, f"Validator should pass; got {problems}")


class TestRationale(unittest.TestCase):
    def test_mbti_keys_present(self):
        p = derive_profile_keys({"mbti": "INFJ"})
        self.assertIn("mbti", p)
        self.assertTrue(any(k in p["mbti"] for k in ("intrapersonal", "service", "ai", "policy")))

    def test_enneagram_keys_present(self):
        p = derive_profile_keys({"enneagram": "1"})
        self.assertIn("ethics", p["enneagram"])

    def test_riasec_keys_present(self):
        p = derive_profile_keys({"riasec": "IRC"})
        self.assertTrue(any(k in p["riasec"] for k in ("research", "data")))

    def test_matches_intersection(self):
        m = find_matches(["ai", "ethics", "policy"], ["ai", "policy", "service"])
        self.assertEqual(m, ["ai", "policy"])


class TestRenderer(unittest.TestCase):
    def test_render_produces_valid_markdown(self):
        prof = UserProfile(age=30, education="bachelor", mbti="INFJ", enneagram="1", raw_input="직업 추천")
        plan = build_plan(prof)
        md = render_markdown(plan, {
            "age": prof.age, "education": prof.education, "mbti": prof.mbti, "enneagram": prof.enneagram,
            "raw_input": prof.raw_input,
        })
        ok, problems = validate_markdown(md, expected_language="ko")
        self.assertTrue(ok, f"rendered markdown failed validate: {problems}")

    def test_render_never_invents_jobs(self):
        prof = UserProfile(age=30, education="bachelor", raw_input="직업 추천")
        plan = build_plan(prof)
        md = render_markdown(plan, {"age": 30, "education": "bachelor", "raw_input": "직업 추천"})
        from lib.catalog import jobs_in_type, TYPE_KEYS
        all_catalog_ko = set()
        for t in TYPE_KEYS:
            for j in jobs_in_type(t):
                all_catalog_ko.add(j["ko"])
        # Every "### N. {ko} ({en})" heading's ko part must be in catalog (or placeholder text)
        import re
        # Renderer formats as "### N. {ko} ({en})". Take everything before the FINAL
        # space+"(" that introduces the English name. Korean titles themselves may
        # contain parenthetical clauses like "SMR(소형원자로) 기술자".
        for m in re.finditer(r"^###\s+\d+\.\s+(.+?)\s+\([A-Za-z][^)]*\)\s*$", md, re.MULTILINE):
            title = m.group(1).strip()
            self.assertIn(title, all_catalog_ko, f"Unknown job title in render: {title}")
        # Also accept placeholder lines (no English suffix)
        for m in re.finditer(r"^###\s+\d+\.\s+(현재 직접 적합 직업 부족.*)$", md, re.MULTILINE):
            pass  # placeholders are allowed


if __name__ == "__main__":
    unittest.main(verbosity=2)
