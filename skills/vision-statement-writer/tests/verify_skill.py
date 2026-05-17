#!/usr/bin/env python3
"""vision-statement-writer 자동 무결성 테스트.

스크립트·assets·SKILL.md의 정합성을 결정론적으로 검증한다.

실행:
    python3 tests/verify_skill.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"
SKILL = ROOT / "SKILL.md"

EXPECTED_FIELD_IDS = [
    "F1_name",
    "F2_plausible",
    "F3_possible",
    "F4_unexpected",
    "F5_problem",
    "F6_interest",
    "F7_talent",
    "F8_personality",
    "F9_work",
    "F10_value",
    "F11_purposes",
    "F12_date",
]


def fail(msg: str, fails: list) -> None:
    fails.append(msg)


def test_assets_exist(fails: list) -> None:
    for name in ("facts.json", "citations.json", "external_sources.json"):
        if not (ASSETS / name).exists():
            fail(f"assets/{name} 누락", fails)


def test_facts_structure(fails: list) -> None:
    facts = json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))
    if facts.get("skill_name") != "vision-statement-writer":
        fail("facts.skill_name 불일치", fails)
    b = facts.get("book", {})
    if b.get("isbn13") != "9788993322972":
        fail("facts.book.isbn13 불일치", fails)
    if b.get("year") != 2016:
        fail("facts.book.year 불일치", fails)
    form = facts.get("vision_statement_form", {})
    fields = form.get("fields", [])
    if len(fields) != 12:
        fail(f"필드 수 {len(fields)} != 12", fails)
    ids = [f["id"] for f in fields]
    if ids != EXPECTED_FIELD_IDS:
        fail(f"필드 ID 순서 불일치: {ids}", fails)
    orders = [f["order"] for f in fields]
    if orders != list(range(1, 13)):
        fail(f"필드 order 순서 불일치: {orders}", fails)
    if form.get("structure_total_blanks") != 12:
        fail("structure_total_blanks != 12", fails)


def test_principles_count(fails: list) -> None:
    facts = json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))
    ps = facts.get("absolute_principles", [])
    if len(ps) < 11:
        fail(f"절대 원칙 수 {len(ps)} < 11", fails)


def test_validation_tools(fails: list) -> None:
    facts = json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))
    tools = facts.get("validation_tools", [])
    if len(tools) != 3:
        fail(f"검증 도구 수 {len(tools)} != 3", fails)
    ids = [t["id"] for t in tools]
    if ids != ["V1", "V2", "V3"]:
        fail(f"검증 도구 ID 불일치: {ids}", fails)
    excluded = facts.get("excluded_validation_tools_with_reason", [])
    if not any("5대 공리" in e.get("name", "") for e in excluded):
        fail("excluded_validation_tools_with_reason에 '5대 공리' 명시 없음", fails)


def test_preceding_subsequent(fails: list) -> None:
    facts = json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))
    pre = facts.get("preceding_skills", [])
    sub = facts.get("subsequent_skills", [])
    if len(pre) != 11:
        fail(f"선행 스킬 수 {len(pre)} != 11", fails)
    if len(sub) < 4:
        fail(f"후속 스킬 수 {len(sub)} < 4", fails)
    pre_ids = [s["skill"] for s in pre]
    must_have = [
        "vision-cys-competence-visioncoding",
        "vision-mission-frame",
        "vision-four-futures",
        "vision-futures-timeline-map",
        "vision-three-realm-balance",
        "vision-future-promise-five-criteria",
        "vision-multipleintel-visioncoding",
        "vision-mbti-visioncoding",
        "vision-enneagram-visioncoding",
        "vision-values-visioncoding",
        "vision-career-recommendation",
    ]
    for m in must_have:
        if m not in pre_ids:
            fail(f"선행 스킬 누락: {m}", fails)


def test_citations(fails: list) -> None:
    c = json.loads((ASSETS / "citations.json").read_text(encoding="utf-8"))
    cits = c.get("citations", [])
    if len(cits) < 5:
        fail(f"인용 수 {len(cits)} < 5", fails)
    ids = [q["id"] for q in cits]
    for must in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]:
        if must not in ids:
            fail(f"인용 ID 누락: {must}", fails)
    # Q1 — 박사님 책 결정적 인용
    q1 = next(q for q in cits if q["id"] == "Q1")
    if "통합 비전 선언문" not in q1["text_ko"]:
        fail("Q1 본문 핵심 키워드 누락", fails)


def test_external_sources(fails: list) -> None:
    s = json.loads((ASSETS / "external_sources.json").read_text(encoding="utf-8"))
    src = s.get("sources", [])
    if len(src) < 4:
        fail(f"외부 출처 수 {len(src)} < 4", fails)
    authors = [x["author"] for x in src]
    if "Howard Gardner" not in authors:
        fail("외부 출처에 Howard Gardner 누락", fails)
    needed_for_voros = any("Voros" in x.get("author", "") for x in src)
    if not needed_for_voros:
        fail("외부 출처에 Voros 누락(Futures Cone)", fails)


def test_lookup_cli(fails: list) -> None:
    cmds_must_succeed = [
        ["book"],
        ["author"],
        ["fields"],
        ["questions"],
        ["tools"],
        ["preceding-skills"],
        ["subsequent-skills"],
        ["input-modes"],
        ["multiple-intelligences"],
        ["principles"],
        ["quotes"],
        ["sources"],
        ["field", "F2_plausible"],
        ["tool", "V1"],
        ["quote", "Q1"],
        ["source", "MI1"],
    ]
    for c in cmds_must_succeed:
        r = subprocess.run(
            ["python3", str(SCRIPTS / "lookup.py"), *c],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            fail(f"lookup {' '.join(c)} 실패: {r.stderr}", fails)
    # 잘못된 ID는 에러로 빠져야 함.
    r = subprocess.run(
        ["python3", str(SCRIPTS / "lookup.py"), "field", "F99_fake"],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        fail("lookup field F99_fake 가 성공 — 잘못된 ID 검증 부재", fails)


def test_render_cli(fails: list) -> None:
    for mode in ("A", "C", "D"):
        r = subprocess.run(
            ["python3", str(SCRIPTS / "render_template.py"), "--mode", mode],
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            fail(f"render --mode {mode} 실패: {r.stderr}", fails)
        if "부름을 받았습니다" not in r.stdout and mode != "A":
            fail(f"render --mode {mode} 결문 누락", fails)
    # B 모드 — answers 파일 필요
    answers = {
        "F1_name": "테스트",
        "F2_plausible": "기본미래 사회 모습 한 문단입니다.",
        "F3_possible": "또 다른 가능성의 미래 한 문단입니다.",
        "F4_unexpected": "뜻밖의 미래 한 문단입니다.",
        "F5_problem": "사회 문제 한 문장입니다.",
        "F6_interest": "관심",
        "F7_talent": "재능 + 기술",
        "F8_personality": "INTJ 5번",
        "F9_work": "직업",
        "F10_value": "정의·평화",
        "F11_purposes": ["하나", "둘", "셋", "넷", "다섯"],
        "F12_date": "2026년 5월 17일",
    }
    tmp = Path("/tmp/vsw_verify_answers.json")
    tmp.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        ["python3", str(SCRIPTS / "render_template.py"), "--mode", "B", "--answers", str(tmp)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        fail(f"render --mode B 실패: {r.stderr}", fails)
    if "테스트" not in r.stdout or "부름을 받았습니다" not in r.stdout:
        fail("render --mode B 출력에서 사용자 답변 또는 결문 누락", fails)
    if "다섯" not in r.stdout:
        fail("render --mode B Purposes 5번째 항목 누락", fails)


def test_validate_cli(fails: list) -> None:
    good = {
        "F1_name": "홍길동",
        "F2_plausible": "기본미래 사회 모습 한 문단입니다. AGI 시대 한국.",
        "F3_possible": "또 다른 가능성의 미래 한 문단입니다.",
        "F4_unexpected": "뜻밖의 미래 한 문단입니다.",
        "F5_problem": "사회 문제 한 문장입니다.",
        "F6_interest": "관심사",
        "F7_talent": "재능 + 기술",
        "F8_personality": "INTJ 5번",
        "F9_work": "미래학 강연",
        "F10_value": "정의·평화·아름다움",
        "F11_purposes": ["A", "B", "C", "D", "E"],
        "F12_date": "2026년 5월 17일",
    }
    tmp = Path("/tmp/vsw_verify_good.json")
    tmp.write_text(json.dumps(good, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        ["python3", str(SCRIPTS / "validate_output.py"), "--answers", str(tmp)],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        fail(f"validate 정상 입력이 실패함: {r.stdout}\n{r.stderr}", fails)
    bad = dict(good)
    bad["F2_plausible"] = "TODO"
    bad["F12_date"] = "어제"
    tmpb = Path("/tmp/vsw_verify_bad.json")
    tmpb.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(
        ["python3", str(SCRIPTS / "validate_output.py"), "--answers", str(tmpb)],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        fail("validate 잘못된 입력이 PASS로 처리됨", fails)
    if "TODO" not in r.stdout and "placeholder" not in r.stdout:
        fail("validate placeholder 검증 누락", fails)


def test_skill_md_references_scripts(fails: list) -> None:
    text = SKILL.read_text(encoding="utf-8")
    if "scripts/lookup.py" not in text:
        fail("SKILL.md가 scripts/lookup.py를 참조하지 않음 (결정론 환원 누락)", fails)
    if "scripts/render_template.py" not in text:
        fail("SKILL.md가 scripts/render_template.py를 참조하지 않음", fails)
    if "scripts/validate_output.py" not in text:
        fail("SKILL.md가 scripts/validate_output.py를 참조하지 않음", fails)


def test_skill_md_consistency(fails: list) -> None:
    text = SKILL.read_text(encoding="utf-8")
    # ISBN 일관성
    if "9788993322972" not in text:
        fail("SKILL.md에 ISBN 9788993322972 누락", fails)
    # 양식 결문
    if "부름을 받았습니다" not in text:
        fail("SKILL.md에 결문 '부름을 받았습니다' 누락", fails)
    # 빈칸 12개 명시
    if "12" not in text or "빈칸" not in text:
        fail("SKILL.md에 12개 빈칸 명시 누락", fails)
    # 실존지능 명명 주의 — 우리 facts.json의 정책과 일치
    if "Existential" not in text:
        fail("SKILL.md에 Existential 명명 주의 누락", fails)


TESTS = [
    ("assets_exist", test_assets_exist),
    ("facts_structure", test_facts_structure),
    ("principles_count", test_principles_count),
    ("validation_tools", test_validation_tools),
    ("preceding_subsequent", test_preceding_subsequent),
    ("citations", test_citations),
    ("external_sources", test_external_sources),
    ("lookup_cli", test_lookup_cli),
    ("render_cli", test_render_cli),
    ("validate_cli", test_validate_cli),
    ("skill_md_references_scripts", test_skill_md_references_scripts),
    ("skill_md_consistency", test_skill_md_consistency),
]


def main() -> int:
    fails: list[str] = []
    passed = 0
    for name, fn in TESTS:
        before = len(fails)
        fn(fails)
        after = len(fails)
        if after == before:
            print(f"PASS {name}")
            passed += 1
        else:
            print(f"FAIL {name}")
            for f in fails[before:after]:
                print(f"   {f}")
    print()
    print(f"=== {passed}/{len(TESTS)} 테스트 통과, 실패 {len(fails)}건 ===")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
