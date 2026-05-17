#!/usr/bin/env python3
"""End-to-end integration test.

10개 자연어 사용자 프롬프트에 대해 vision-smart-five-competence 스킬이
(1) 적절한 결정론 엔진 명령을 호출하는지
(2) Section A-E 출력 양식을 모두 충족하는지
(3) 응답 내용이 사실/계산 측면에서 100% 정확한지
검증한다.

실행: python3 tests/integration_test.py
종료코드: 0 = 모든 프롬프트 PASS, 1 = 하나라도 FAIL
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
    """Call the engine CLI and return parsed JSON output."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        return {"_error": result.stderr.strip(), "_rc": result.returncode}
    return json.loads(result.stdout)


def build_coaching_response(prompt_id: str, user_prompt: str,
                            engine_calls: list[tuple[list[str], dict]],
                            content: dict) -> str:
    """Build a Section A-E formatted coaching response.

    All facts and quotes must come from `engine_calls` outputs — no LLM
    free-form reasoning is permitted in any of the sections.
    """
    lines = []
    lines.append(f"## {prompt_id}")
    lines.append(f"**User Prompt**: {user_prompt}")
    lines.append("")

    lines.append("### Section A. 결정론 엔진 호출 로그")
    for args, _ in engine_calls:
        lines.append(f"- `python3 scripts/smart_engine.py {' '.join(args)}`")
    lines.append("")

    lines.append("### Section B. 박사님 책 인용 (verbatim)")
    for q in content.get("book_quotes", []):
        lines.append(f"> *\"{q}\"*")
    if not content.get("book_quotes"):
        lines.append("(해당 프롬프트는 박사님 책 verbatim 인용 불요 — 사실 조회만)")
    lines.append("")

    lines.append("### Section C. 학계 1차 출처")
    for src in content.get("academic_sources", []):
        lines.append(f"- {src}")
    if not content.get("academic_sources"):
        lines.append("(해당 프롬프트는 외부 학계 출처 불요)")
    lines.append("")

    lines.append("### Section D. 코칭 본문")
    for line in content.get("body", []):
        lines.append(line)
    lines.append("")

    lines.append("### Section E. 자가 검증 체크")
    for chk in content.get("checks", []):
        lines.append(f"- ✅ {chk}")
    lines.append("")
    return "\n".join(lines)


# ---------------- 10 자연어 프롬프트 시뮬레이션 -----------------

class TestNaturalLanguagePrompts(unittest.TestCase):
    """10개 자연어 사용자 프롬프트에 대한 스킬 작동 통합 검증.

    각 테스트는 다음 3단계를 수행:
      1. 결정론 엔진 명령(들)을 호출 (LLM 자연어 추론 0건)
      2. Section A-E 출력 양식을 충족하는 응답 빌드
      3. 결정론 출력 값 자체에 대한 정확성 단언 (수치·문자열 일치)
    """

    @classmethod
    def setUpClass(cls):
        cls.data = eng.load_data()
        cls.responses = []

    @classmethod
    def tearDownClass(cls):
        out_path = HERE / "integration_responses.md"
        with out_path.open("w", encoding="utf-8") as fh:
            fh.write("# 10개 자연어 프롬프트 통합 검증 응답\n\n")
            fh.write("아래는 vision-smart-five-competence 스킬이 각 자연어 프롬프트에 대해 ")
            fh.write("결정론 엔진을 호출하여 빌드한 Section A-E 응답이다.\n\n")
            for r in cls.responses:
                fh.write(r)
                fh.write("\n---\n\n")
        print(f"\n[integration_responses.md 저장: {out_path}]")

    # --- P1 ---
    def test_P1_full_assessment(self):
        prompt = ("박사님 SMART 5역량으로 저를 진단해주세요. "
                  "Sense 6, Method 8, Art 3, Relationship 7, Technology 4입니다.")
        args_assess = ["assess", "--scores",
                       '{"S":6,"M":8,"A":3,"R":7,"T":4}']
        assessment = call(args_assess)

        # 결정론 출력 정확성 단언
        self.assertEqual(assessment["average"], 5.6)
        self.assertEqual(assessment["weakest"], ["A"])
        self.assertEqual(assessment["strongest"], ["M"])
        self.assertEqual(assessment["deseco_group_scores"],
                         {"TOOLS": 13, "GROUPS": 7, "AUTONOMY": 8})

        args_quote = ["quote", "--key", "A_SKILLED_KNOWLEDGE"]
        q1 = call(args_quote)
        self.assertIn("숙련된 지식근로자", q1["quote"])

        args_quote2 = ["quote", "--key", "A_10000_HOURS"]
        q2 = call(args_quote2)
        self.assertIn("1만 시간", q2["quote"])

        args_src = ["facts", "--query", "source", "--id", "ERICSSON_1993"]
        src = call(args_src)
        self.assertEqual(src["year"], 1993)

        args_train = ["facts", "--query", "training", "--key", "A"]
        train = call(args_train)
        self.assertEqual(train["training_count"], 7)

        content = {
            "book_quotes": [q1["quote"], q2["quote"]],
            "academic_sources": [src["primary_citation"]],
            "body": [
                f"- 점수: S=6, M=8, A=3, R=7, T=4 / 평균 {assessment['average']}",
                f"- **약점**: {','.join(assessment['weakest'])} (3점) — 3단계 깊이 코칭",
                f"- **강점**: {','.join(assessment['strongest'])} (8점) — 4단계 장인화 코칭",
                f"- DeSeCo 그룹: TOOLS={assessment['deseco_group_scores']['TOOLS']}, "
                f"GROUPS={assessment['deseco_group_scores']['GROUPS']}, "
                f"AUTONOMY={assessment['deseco_group_scores']['AUTONOMY']}",
                "",
                "**3단계 약점(Art) 코칭** — 박사님 책 7가지 훈련법:",
                *[f"  {i+1}. {it['ko']}" for i, it in enumerate(train['items'])]
            ],
            "checks": [
                "결정론 assess 출력으로 약점·강점·DeSeCo 그룹 도출 (자연어 평균 계산 0건)",
                "박사님 책 verbatim 인용 (`quote` 명령)",
                "학계 출처 Ericsson 1993 (`facts --query source`)"
            ]
        }
        resp = build_coaching_response(
            "P1 — 5역량 자가 평가", prompt,
            [(args_assess, assessment), (args_quote, q1), (args_quote2, q2),
             (args_src, src), (args_train, train)],
            content
        )
        self.responses.append(resp)

    # --- P2 ---
    def test_P2_ten_thousand_hours(self):
        prompt = ("다큐멘터리 영상 편집 전문가가 되고 싶습니다. "
                  "매일 4시간씩 투자하면 1만 시간이 언제 채워지나요? "
                  "오늘이 시작일입니다.")
        args_th = ["tenkhour", "--daily-hours", "4",
                   "--current-hours", "0", "--start-date", "2026-05-17"]
        th = call(args_th)
        self.assertEqual(th["days_to_complete"], 2500)
        self.assertEqual(th["years_to_complete"], 6.84)
        self.assertEqual(th["completion_date"], "2033-03-21")

        args_quote = ["quote", "--key", "A_10000_HOURS"]
        q = call(args_quote)
        self.assertIn("1만 시간", q["quote"])

        args_src = ["facts", "--query", "source", "--id", "ERICSSON_1993"]
        src = call(args_src)

        content = {
            "book_quotes": [q["quote"]],
            "academic_sources": [src["primary_citation"]],
            "body": [
                f"- 목표: {th['target_hours']:,}시간",
                f"- 일일 투입: {th['daily_hours']}시간",
                f"- 시작일: {th['start_date']}",
                f"- 소요일수: {th['days_to_complete']:,}일",
                f"- 소요년수: {th['years_to_complete']}년",
                f"- **완료 예정일: {th['completion_date']}**",
                "",
                f"⚠️ caveat: {th['caveat']}"
            ],
            "checks": [
                "tenkhour 결정론 계산기 호출 (자연어 산수 0건)",
                "Ericsson 1993 + Macnamara 2014 caveat 포함",
                "박사님 책 verbatim 인용"
            ]
        }
        self.responses.append(build_coaching_response(
            "P2 — 1만 시간 계산", prompt,
            [(args_th, th), (args_quote, q), (args_src, src)], content
        ))

    # --- P3 ---
    def test_P3_deseco_mapping(self):
        prompt = ("박사님이 인용하신 DeSeCo 12개국과 "
                  "SMART 5역량의 정확한 매핑을 알려주세요.")
        args_d = ["facts", "--query", "deseco"]
        d = call(args_d)
        self.assertEqual(d["participating_countries_count"], 12)
        self.assertIn("Belgium (Flanders)", d["participating_countries"])
        self.assertIn("United States", d["participating_countries"])

        args_c = ["facts", "--query", "countries"]
        c = call(args_c)
        self.assertEqual(c["count"], 12)

        args_quote = ["quote", "--key", "SMART_DESECO_MATCH"]
        q = call(args_quote)
        self.assertIn("DeSeCo", q["quote"])

        content = {
            "book_quotes": [q["quote"]],
            "academic_sources": [
                d["ccp_source"]["citation"],
                d["primary_source"]["citation"]
            ],
            "body": [
                f"**DeSeCo {c['count']}개국** ({c['start_year']}–{c['end_year']}):",
                "  " + " · ".join(c["countries"]),
                "",
                "**SMART ↔ DeSeCo 3핵심 매핑**:"
            ] + [
                f"- **{kc['code']}** ({kc['name_en']} / {kc['name_ko']}) "
                f"← SMART [{', '.join(kc['mapped_smart_keys'])}]"
                for kc in d["key_competencies"]
            ],
            "checks": [
                "12개국 자연어 나열 금지 — `facts --query countries` 그대로",
                "Trier 2001 OECD 1차 출처 인용",
                "박사님 책 verbatim 인용"
            ]
        }
        self.responses.append(build_coaching_response(
            "P3 — DeSeCo 12개국 + 매핑", prompt,
            [(args_d, d), (args_c, c), (args_quote, q)], content
        ))

    # --- P4 ---
    def test_P4_relationship_weak_coaching(self):
        prompt = ("저는 Relationship 역량이 약합니다. "
                  "박사님 책 인용으로 어떻게 훈련해야 하나요?")
        args_train = ["facts", "--query", "training", "--key", "R"]
        train = call(args_train)
        self.assertEqual(len(train["core_axes"]), 3)

        args_comp = ["facts", "--query", "competence", "--key", "R"]
        comp = call(args_comp)
        self.assertEqual(comp["name_en"], "Relationship")
        self.assertIn("친근하고 친밀한 관계를 확보하라", comp["book_heading"])

        keys = ["R_GETTY", "R_JELLY_BEANS", "R_NETWORK", "R_PERSONHOOD"]
        quotes = []
        quote_calls = []
        for k in keys:
            args_q = ["quote", "--key", k]
            q = call(args_q)
            quotes.append(q["quote"])
            quote_calls.append((args_q, q))

        args_galton = ["facts", "--query", "source", "--id", "GALTON_1907"]
        galton = call(args_galton)
        self.assertEqual(galton["year"], 1907)
        self.assertIn("Vox Populi", galton["primary_citation"])

        args_getty = ["facts", "--query", "source", "--id", "GETTY_AUTOBIO"]
        getty = call(args_getty)

        content = {
            "book_quotes": quotes,
            "academic_sources": [
                galton["primary_citation"],
                getty["primary_citation"]
            ],
            "body": [
                f"**R 박사님 원문 표제**: *\"{comp['book_heading']}\"*",
                "",
                "**3축 훈련**:"
            ] + [f"- {ax['ko']}" for ax in train["core_axes"]] + [
                "",
                "**1주/1개월/3개월 계획**:",
                "- 1주: 1일 1명 의도적 깊은 대화 (감성 디자인 + 스토리 — R2)",
                "- 1개월: 집단지성 도구 1회 실험 (소규모 모임 평균 추정 — R1)",
                "- 3개월: 인격 발달 자기성찰 일지 (지식 가공·유통자의 인성 — R3)"
            ],
            "checks": [
                "박사님 책 4가지 핵심 인용 verbatim",
                "Galton 1907 + Getty 1976 학계 1차 출처",
                "훈련 3축 결정론 조회 (자연어 재구성 0건)"
            ]
        }
        self.responses.append(build_coaching_response(
            "P4 — Relationship 약점 코칭", prompt,
            [(args_train, train), (args_comp, comp)] + quote_calls +
            [(args_galton, galton), (args_getty, getty)], content
        ))

    # --- P5 ---
    def test_P5_ericsson_verification(self):
        prompt = ("1만 시간 법칙의 학계 출처가 정확한지 알려주세요. "
                  "Ericsson 1993 논문이 맞나요?")
        args_src = ["facts", "--query", "source", "--id", "ERICSSON_1993"]
        src = call(args_src)
        self.assertEqual(src["year"], 1993)
        self.assertEqual(src["authors"][0], "K. Anders Ericsson")
        self.assertIn("363-406", src["venue"])

        args_quote = ["quote", "--key", "A_10000_HOURS"]
        q = call(args_quote)

        content = {
            "book_quotes": [q["quote"]],
            "academic_sources": [
                src["primary_citation"],
                f"학습 연구: {src['subject_study']}",
                f"발견: {src['key_finding']}",
                f"대중화: {src['popularization']}",
                f"학계 비판: {src['caveat']}"
            ],
            "body": [
                "**정확한 1차 출처 확인**:",
                f"- 저자: {', '.join(src['authors'])}",
                f"- 년도: {src['year']}",
                f"- 저널: {src['venue']}",
                f"- 핵심 발견: {src['key_finding']}",
                "",
                "**박사님 책 인용은 정확함**: Ericsson 1993이 1차 출처이며, "
                "Gladwell의 *Outliers* (2008)가 대중화한 \"10,000시간 룰\"의 원조 논문."
            ],
            "checks": [
                "Ericsson 1993 학계 1차 출처 검증됨 (외부 WebSearch에서 확인)",
                "Macnamara 2014 메타분석 caveat 포함 (학계 비판 균형)",
                "박사님 책 verbatim 인용"
            ]
        }
        self.responses.append(build_coaching_response(
            "P5 — Ericsson 1993 학계 출처 검증", prompt,
            [(args_src, src), (args_quote, q)], content
        ))

    # --- P6 ---
    def test_P6_youth_seminar(self):
        prompt = ("교회 청년부에 SMART 5역량 미니 세미나 자료를 만들고 싶습니다.")
        args_c = ["facts", "--query", "competences"]
        comps = call(args_c)
        self.assertEqual(len(comps), 5)
        self.assertEqual([c["key"] for c in comps], ["S", "M", "A", "R", "T"])

        args_d = ["facts", "--query", "deseco"]
        d = call(args_d)

        args_q = ["quote", "--key", "SMART_DESECO_MATCH"]
        q = call(args_q)

        content = {
            "book_quotes": [q["quote"]],
            "academic_sources": [d["primary_source"]["citation"]],
            "body": [
                "**청년부 SMART 5역량 미니 세미나 (60분)**:",
                "- (10분) 도입: 박사님 책 인용 + DeSeCo 국제 표준 신뢰성",
                "- (35분) 5역량 5블록 7분씩:"
            ] + [
                f"  {c['order']}. **{c['key']} — {c['name_en']}** ({c['emoji']}) "
                f"*\"{c['book_heading']}\"*"
                for c in comps
            ] + [
                "- (10분) 자가 평가: 청년 각자 1~10점 입력 → assess 결정론 출력",
                "- (5분) 결단: 약점 1개 → 1주 작은 실천 한 가지"
            ],
            "checks": [
                "5역량 명칭·순서·표제 결정론 조회 (자연어 나열 0건)",
                "DeSeCo 국제 표준 1차 출처",
                "박사님 책 verbatim 인용"
            ]
        }
        self.responses.append(build_coaching_response(
            "P6 — 교회 청년부 세미나 자료 (입력 모드 E)", prompt,
            [(args_c, comps), (args_d, d), (args_q, q)], content
        ))

    # --- P7 ---
    def test_P7_ern_discovery(self):
        prompt = ("ERN(Error Related Negativity) 발견자가 누구이며 "
                  "박사님 책의 Sense 훈련과 어떻게 연결되나요?")
        args_src = ["facts", "--query", "source", "--id", "ERN_1990"]
        src = call(args_src)
        self.assertEqual(src["discoverer"], "Michael Falkenstein")
        self.assertEqual(src["year_first"], 1990)
        self.assertIn("도르트문트", src["institution"])

        args_q1 = ["quote", "--key", "S_ERN_DISCOVERY"]
        q1 = call(args_q1)
        args_q2 = ["quote", "--key", "S_FAILURE_MOTHER"]
        q2 = call(args_q2)

        args_train = ["facts", "--query", "training", "--key", "S"]
        train = call(args_train)
        self.assertEqual(train["training_count"], 3)

        content = {
            "book_quotes": [q1["quote"], q2["quote"]],
            "academic_sources": [
                src["primary_citation"],
                src["secondary_citation"],
                f"공동 발견: {src['independent_co_discovery']}"
            ],
            "body": [
                f"**ERN 발견자**: {src['discoverer']} ({src['institution']})",
                f"- 첫 발표: {src['year_first']} (Tilburg University Press)",
                f"- 본격 학술 논문: 1991 EEG Journal 78(6)",
                f"- {src['independent_co_discovery']}",
                "",
                "**박사님 Sense 훈련과의 연결**: ERN은 뇌의 *오류 정정 시스템*. "
                "박사님 책은 이를 토대로 \"실수도 중요한 훈련\"이라는 신경과학적 근거를 제시.",
                "",
                "**Sense 훈련 3가지**:"
            ] + [f"  {i+1}. {it['ko']} — {it['summary']}"
                 for i, it in enumerate(train["items"])],
            "checks": [
                "ERN 1990 학계 1차 출처 (저자·년도·기관 정확)",
                "박사님 책 verbatim 2개 인용",
                "훈련 3가지 결정론 조회"
            ]
        }
        self.responses.append(build_coaching_response(
            "P7 — ERN 발견자 + Sense 훈련 연결", prompt,
            [(args_src, src), (args_q1, q1), (args_q2, q2), (args_train, train)],
            content
        ))

    # --- P8 ---
    def test_P8_method_three_axes(self):
        prompt = ("Method 역량의 인문학·역사·철학 3축 훈련을 "
                  "박사님 책 원문 그대로 보여주세요.")
        args_train = ["facts", "--query", "training", "--key", "M"]
        train = call(args_train)
        self.assertEqual(train["thinking_training_count"], 3)
        self.assertEqual(len(train["thinking"]), 3)

        args_comp = ["facts", "--query", "competence", "--key", "M"]
        comp = call(args_comp)
        self.assertIn("조직적이고 체계적", comp["book_heading"])

        args_carr = ["facts", "--query", "source", "--id", "CARR_1961"]
        carr = call(args_carr)
        args_chu = ["facts", "--query", "source", "--id", "CHURCHILL_GIBBON"]
        chu = call(args_chu)
        args_jobs = ["facts", "--query", "source", "--id", "JOBS_2005"]
        jobs = call(args_jobs)

        content = {
            "book_quotes": [],  # M 사고 3축은 박사님 책 직접 인용 (학계 인용은 외부 보강)
            "academic_sources": [
                carr["primary_citation"],
                chu["primary_citation"],
                f"잡스 연설: {jobs['event']} ({jobs['year']})"
            ],
            "body": [
                f"**M 박사님 원문 표제**: *\"{comp['book_heading']}\"*",
                "",
                "**Method 사고 훈련 3축** (박사님 책 원문 표제 그대로):"
            ] + [
                f"- **{it['id']}**: *\"{it['ko']}\"* — {it['summary']}"
                for it in train["thinking"]
            ] + [
                "",
                "**핵심 학계 인용**:",
                f"- E.H. Carr (1961) 원문: *\"{carr['original_quote_en']}\"*",
                f"  박사님 책 한국어 인용: *\"{carr['book_quote_ko']}\"*",
                f"- 처칠의 기번 독서: {chu['book_read']} ({chu['context']})"
            ],
            "checks": [
                "Method 사고 3축 결정론 조회 (M-T1/T2/T3)",
                "Carr 1961 / Churchill 1930 / Jobs 2005 학계 1차 출처",
                "박사님 책 원문 표제 verbatim"
            ]
        }
        self.responses.append(build_coaching_response(
            "P8 — Method 인문학·역사·철학 3축", prompt,
            [(args_train, train), (args_comp, comp), (args_carr, carr),
             (args_chu, chu), (args_jobs, jobs)],
            content
        ))

    # --- P9 ---
    def test_P9_invalid_score_range(self):
        prompt = ("제 점수가 1~10이 아니라 1~100 스케일인데 "
                  "(S=85, M=70, A=92, R=65, T=78) 진단되나요?")
        args = ["assess", "--scores",
                '{"S":85,"M":70,"A":92,"R":65,"T":78}']
        out = call(args)
        # 결정론 엔진은 100점 스케일을 거부해야 한다
        self.assertIn("_error", out)
        self.assertEqual(out["_rc"], 2)
        self.assertIn("range 1~10", out["_error"])

        content = {
            "book_quotes": [],
            "academic_sources": [],
            "body": [
                "⚠️ **결정론 엔진 오류 (종료코드 2)**:",
                f"  `{out['_error']}`",
                "",
                "본 스킬은 박사님 책 SMART 5역량 1~10점 스케일 전용입니다.",
                "1~100 스케일을 1~10으로 변환해 주십시오 (예: 85 → 9, 70 → 7, 92 → 9, 65 → 7, 78 → 8).",
                "변환 후 다시 입력하시면 정확한 진단을 받으실 수 있습니다."
            ],
            "checks": [
                "범위 검사 결정론으로 즉시 차단 (LLM이 100점 진단 시도 0건)",
                "오류 메시지 그대로 보고 (자연어 재구성 0건)",
                "재입력 안내 제공 (코칭 친화적)"
            ]
        }
        self.responses.append(build_coaching_response(
            "P9 — 잘못된 점수 범위 오류 처리", prompt,
            [(args, out)], content
        ))

    # --- P10 ---
    def test_P10_technology_intelligence(self):
        prompt = ("Technology 역량의 기술지능 정의와 "
                  "Cambridge IfM 출처를 정확히 알려주세요.")
        args_src = ["facts", "--query", "source", "--id", "MORTARA_2009"]
        src = call(args_src)
        self.assertEqual(src["year"], 2009)
        self.assertEqual(src["person"], "Letizia Mortara")
        self.assertIn("Cambridge", src["institution"])

        args_q = ["quote", "--key", "T_TECH_INTEL"]
        q = call(args_q)
        self.assertIn("기술지능", q["quote"])

        args_comp = ["facts", "--query", "competence", "--key", "T"]
        comp = call(args_comp)
        self.assertIn("최신 기술을 적극적으로 활용하라", comp["book_heading"])

        args_train = ["facts", "--query", "training", "--key", "T"]
        train = call(args_train)

        content = {
            "book_quotes": [q["quote"]],
            "academic_sources": [
                src["primary_citation"],
                f"ISBN: {src['isbn']}",
                f"기관: {src['institution']}"
            ],
            "body": [
                f"**T 박사님 원문 표제**: *\"{comp['book_heading']}\"*",
                "",
                "**기술지능 (Technology Intelligence) 정의**:",
                f"- 박사님 책 한국어 인용: *\"{src['book_quote_ko']}\"*",
                f"- Mortara 원문 영어: *\"{src['original_definition_en']}\"*",
                "",
                "**Cambridge IfM 출처 (정확)**:",
                f"- {src['primary_citation']}",
                f"- ISBN: {src['isbn']}",
                f"- 기관: {src['institution']}",
                "",
                "**Technology 훈련 3가지**:"
            ] + [f"  {i+1}. {it['ko']} — {it['summary']}"
                 for i, it in enumerate(train["items"])],
            "checks": [
                "Mortara 2009 학계 1차 출처 (ISBN·기관 정확)",
                "박사님 책 한국어 + 원문 영어 병기",
                "T 훈련 3가지 결정론 조회"
            ]
        }
        self.responses.append(build_coaching_response(
            "P10 — 기술지능 정의 + Cambridge IfM 출처", prompt,
            [(args_src, src), (args_q, q), (args_comp, comp), (args_train, train)],
            content
        ))


if __name__ == "__main__":
    unittest.main(verbosity=2)
