#!/usr/bin/env python3
"""
vision-four-futures 회귀 테스트.

이 테스트는 스킬의 결정론적 골격이 부서지지 않는지를 매 변경마다 확인한다.
모든 테스트가 통과해야 스킬이 사용 가능 상태이다.

실행:
    python3 tests/verify_skill.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SCRIPTS = ROOT / "scripts"

PY = sys.executable


def run(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        input=stdin,
    )


def assert_true(cond: bool, msg: str) -> None:
    if not cond:
        print(f"  FAIL: {msg}")
        FAILURES.append(msg)
    else:
        print(f"  ok: {msg}")


FAILURES: list[str] = []


def test_facts_schema() -> None:
    print("\n[TEST] facts.json 스키마")
    f = json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))
    assert_true(f["book"]["isbn13"] == "9788993322972", "ISBN-13 일치")
    assert_true(f["book"]["year"] == 2016, "출판년 2016")
    assert_true(set(f["book"]["authors"]) == {"최윤식", "최현식"}, "저자 2인")
    assert_true(len(f["futures"]) == 4, "futures 4개")
    ids = [x["id"] for x in f["futures"]]
    assert_true(ids == ["F1", "F2", "F3", "F4"], f"F1~F4 순서: got {ids}")
    f1 = f["futures"][0]
    assert_true(f1["korean_label"] == "기본미래", "F1 한국어")
    assert_true(f1["english_label"] == "Plausible Future", "F1 영어")
    assert_true(len(f1["elements"]) == 4, "F1 4요소")
    assert_true(
        [e["korean"] for e in f1["elements"]]
        == ["트렌드", "계획", "심층원동력", "현재 대중이 가지고 있는 미래에 대한 이미지"],
        "F1 4요소 순서 정확",
    )
    f3 = f["futures"][2]
    assert_true(f3["korean_label"] == "뜻밖의 미래", "F3 한국어")
    assert_true(len(f3["subtypes"]) == 2, "F3 2종")
    assert_true(
        [s["korean"] for s in f3["subtypes"]]
        == ["비약적 진보에 의한 새로운 미래", "붕괴 후 새로운 미래"],
        "F3 2종 순서 정확",
    )
    assert_true(len(f["absolute_principles"]) == 8, "절대 원칙 8개")
    assert_true(len(f["input_modes"]) == 4, "입력 모드 4유형")


def test_citations_schema() -> None:
    print("\n[TEST] citations.json 스키마")
    c = json.loads((ASSETS / "citations.json").read_text(encoding="utf-8"))
    cits = c["citations"]
    assert_true(len(cits) == 12, f"인용 12개: got {len(cits)}")
    ids = [x["id"] for x in cits]
    expected = [f"Q{i}" for i in range(1, 13)]
    assert_true(ids == expected, f"Q1~Q12 순서: got {ids}")
    for q in cits:
        assert_true(
            q["provenance_status"] in ("verified_book", "unverifiable_online", "interpretation"),
            f"{q['id']} provenance 표기 유효",
        )


def test_external_sources_schema() -> None:
    print("\n[TEST] external_sources.json 스키마")
    s = json.loads((ASSETS / "external_sources.json").read_text(encoding="utf-8"))
    srcs = s["sources"]
    assert_true(len(srcs) == 6, f"외부 출처 6개: got {len(srcs)}")
    ids = [x["id"] for x in srcs]
    assert_true(ids == ["S1", "S2", "S3", "S4", "S5", "S6"], f"S1~S6 순서: got {ids}")


def test_lookup_book() -> None:
    print("\n[TEST] lookup.py book")
    r = run([PY, str(SCRIPTS / "lookup.py"), "book"])
    assert_true(r.returncode == 0, "book 명령 종료 코드 0")
    assert_true("9788993322972" in r.stdout, "ISBN 포함")
    assert_true("2016" in r.stdout, "출판년 포함")


def test_lookup_futures_all() -> None:
    print("\n[TEST] lookup.py futures + future F1~F4")
    for fid in ["F1", "F2", "F3", "F4"]:
        r = run([PY, str(SCRIPTS / "lookup.py"), "future", fid])
        assert_true(r.returncode == 0, f"future {fid} 종료 코드 0")
    r = run([PY, str(SCRIPTS / "lookup.py"), "futures"])
    for ko in ["기본미래", "가능 미래들", "뜻밖의 미래", "바람직한 미래"]:
        assert_true(ko in r.stdout, f"futures 출력에 '{ko}' 포함")


def test_lookup_invalid_future() -> None:
    print("\n[TEST] lookup.py future F5 (잘못된 ID 오류 처리)")
    r = run([PY, str(SCRIPTS / "lookup.py"), "future", "F5"])
    assert_true(r.returncode != 0, "F5는 KeyError로 종료")
    assert_true("Unknown future id" in r.stderr or "Unknown future id" in r.stdout,
                "오류 메시지 명시")


def test_lookup_elements() -> None:
    print("\n[TEST] lookup.py elements")
    r = run([PY, str(SCRIPTS / "lookup.py"), "elements"])
    for kw in ["트렌드", "계획", "심층원동력", "대중"]:
        assert_true(kw in r.stdout, f"elements에 '{kw}' 포함")


def test_lookup_wildcard_subtypes() -> None:
    print("\n[TEST] lookup.py wildcard-subtypes")
    r = run([PY, str(SCRIPTS / "lookup.py"), "wildcard-subtypes"])
    assert_true("비약적 진보" in r.stdout, "비약적 진보")
    assert_true("붕괴" in r.stdout, "붕괴")
    assert_true("시기 예측" in r.stdout, "시기 예측 원칙")


def test_lookup_quote() -> None:
    print("\n[TEST] lookup.py quote")
    r = run([PY, str(SCRIPTS / "lookup.py"), "quote", "Q1"])
    assert_true(r.returncode == 0, "Q1 종료 코드 0")
    assert_true("Plausible World" in r.stdout, "Q1 본문 'Plausible World' 포함")


def test_lookup_source() -> None:
    print("\n[TEST] lookup.py source S5 (Petersen)")
    r = run([PY, str(SCRIPTS / "lookup.py"), "source", "S5"])
    assert_true("Petersen" in r.stdout, "S5에 Petersen 포함")
    assert_true("Out of the Blue" in r.stdout, "S5에 책 제목 포함")


def test_render_skeleton_modes() -> None:
    print("\n[TEST] render_skeleton.py 모든 모드")
    for mode in ["A", "C", "D"]:
        r = run([PY, str(SCRIPTS / "render_skeleton.py"), "--mode", mode])
        assert_true(r.returncode == 0, f"mode {mode} 종료 코드 0")
        assert_true("9788993322972" in r.stdout, f"mode {mode} ISBN 포함")
    for fid in ["F1", "F2", "F3", "F4"]:
        r = run([PY, str(SCRIPTS / "render_skeleton.py"),
                 "--mode", "B", "--focus", fid])
        assert_true(r.returncode == 0, f"mode B focus {fid} 종료 코드 0")


def test_validate_passes_skeleton() -> None:
    print("\n[TEST] validate_output.py — 스킬 골격은 PASS")
    skel = run([PY, str(SCRIPTS / "render_skeleton.py"), "--mode", "A"]).stdout
    r = run([PY, str(SCRIPTS / "validate_output.py"), "-", "--mode", "A"], stdin=skel)
    assert_true(r.returncode == 0, f"validate 종료 코드 0\n--- stdout ---\n{r.stdout}")
    assert_true("OVERALL: PASS" in r.stdout, "전체 PASS")


def test_validate_catches_bad_probability() -> None:
    print("\n[TEST] validate_output.py — 단정 확률 표기 검출")
    bad = (
        "# 4가지 미래\n"
        "## F1 기본미래 (Plausible Future)\n"
        "기본미래의 확률은 70~80%이다. 4요소(트렌드·계획·심층원동력·대중 이미지).\n"
        "## F2 가능 미래들 (Possible Futures)\n대안.\n"
        "## F3 뜻밖의 미래 (Wildcard Future)\n비약적 진보. 붕괴.\n"
        "## F4 바람직한 미래 (Normative Future)\n원하는 미래.\n"
    )
    r = run([PY, str(SCRIPTS / "validate_output.py"), "-", "--mode", "A"], stdin=bad)
    assert_true(r.returncode == 1, "단정 표기는 FAIL")
    assert_true("R4" in r.stdout, "R4 위반 노출")


def test_validate_catches_missing_elements() -> None:
    print("\n[TEST] validate_output.py — 4요소 누락 검출")
    bad = (
        "# 4가지 미래\n"
        "## F1 기본미래 (Plausible Future)\n"
        "트렌드만 있고 다른 요소 없음.\n"
        "## F2 가능 미래들 (Possible Futures)\n대안.\n"
        "## F3 뜻밖의 미래 (Wildcard Future)\n비약적 진보. 붕괴.\n"
        "## F4 바람직한 미래 (Normative Future)\n원하는 미래.\n"
    )
    r = run([PY, str(SCRIPTS / "validate_output.py"), "-", "--mode", "A"], stdin=bad)
    assert_true(r.returncode == 1, "4요소 누락은 FAIL")
    assert_true("R2" in r.stdout, "R2 위반 노출")


def test_validate_catches_missing_wildcard_subtypes() -> None:
    print("\n[TEST] validate_output.py — wildcard 2종 누락 검출")
    bad = (
        "# 4가지 미래\n"
        "## F1 기본미래 (Plausible Future)\n"
        "트렌드·계획·심층원동력·대중 이미지.\n"
        "## F2 가능 미래들 (Possible Futures)\n대안.\n"
        "## F3 뜻밖의 미래 (Wildcard Future)\n비약적 진보만 있음.\n"
        "## F4 바람직한 미래 (Normative Future)\n원하는 미래.\n"
    )
    r = run([PY, str(SCRIPTS / "validate_output.py"), "-", "--mode", "A"], stdin=bad)
    assert_true(r.returncode == 1, "wildcard 2종 누락은 FAIL")
    assert_true("R3" in r.stdout, "R3 위반 노출")


def test_skill_md_has_python_callouts() -> None:
    print("\n[TEST] SKILL.md 결정론 호출 포함 검증")
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for cmd in [
        "python3 scripts/lookup.py book",
        "python3 scripts/lookup.py futures",
        "python3 scripts/lookup.py elements",
        "python3 scripts/lookup.py wildcard-subtypes",
        "python3 scripts/lookup.py vision-count",
        "python3 scripts/lookup.py intersection",
        "python3 scripts/lookup.py principles",
        "python3 scripts/lookup.py input-modes",
        "python3 scripts/render_skeleton.py",
        "python3 scripts/validate_output.py",
    ]:
        assert_true(cmd in skill, f"SKILL.md에 '{cmd}' 호출 포함")


def main() -> int:
    tests = [
        test_facts_schema,
        test_citations_schema,
        test_external_sources_schema,
        test_lookup_book,
        test_lookup_futures_all,
        test_lookup_invalid_future,
        test_lookup_elements,
        test_lookup_wildcard_subtypes,
        test_lookup_quote,
        test_lookup_source,
        test_render_skeleton_modes,
        test_validate_passes_skeleton,
        test_validate_catches_bad_probability,
        test_validate_catches_missing_elements,
        test_validate_catches_missing_wildcard_subtypes,
        test_skill_md_has_python_callouts,
    ]
    for t in tests:
        t()
    print()
    if FAILURES:
        print(f"=== {len(FAILURES)} 실패 ===")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("=== 모든 회귀 테스트 PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
