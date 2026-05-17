"""라운드 6 — 외부 학계 출처 5종의 결정론·SKILL.md 통합 검증.

박사님 책 외 학계 주류 모델 1:1 대조가:
- 결정론 모듈에 정확히 등록됨
- URL 형식이 유효함
- SKILL.md가 호출 의무를 명시함
- 박사님 책이 동료심사 학술지가 아님을 정직하게 명시함
을 확인한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import external_corroboration as ext  # noqa: E402

SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"

CHECKS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))


def main() -> int:
    skill_text = SKILL_MD.read_text(encoding="utf-8")

    # X1: 5종 학계 모델이 모두 등록됨
    sources = ext.list_sources()
    check("X1: 5종 학계 출처 등록", len(sources) == 5)

    # X2: 각 모델이 박사님 원 ①②③에 모두 매핑됨
    for s in sources:
        all_realms = all(r in s.mapping_to_cys for r in (1, 2, 3))
        check(f"X2.{s.key}: 원 ①②③ 매핑 완전성", all_realms)

    # X3: 모든 URL이 유효한 형식
    check("X3: 모든 URL 유효 형식", ext.all_urls_valid())

    # X4: SKILL.md가 외부 학계 호출 의무를 명시
    check(
        "X4: SKILL.md '외부 학계 출처 호출 의무' 명시",
        "external_corroboration" in skill_text and "ext.render_corroboration" in skill_text,
    )

    # X5: SKILL.md가 5종 학계 모델 슬러그를 명시
    for key in ["sdt_deci_ryan", "frankl_logotherapy", "seligman_perma",
                "ikigai_western_venn", "aristotle_eudaimonia"]:
        check(f"X5.{key}: SKILL.md에 슬러그 등장", key in skill_text)

    # X6: render_all_corroboration에 박사님 책 *동료심사 학술지 아님* 정직 명시
    out = ext.render_all_corroboration()
    check(
        "X6: 박사님 책이 동료심사 학술지 아님 정직 명시",
        "동료심사 학술지 출간이 아닙니다" in out,
    )

    # X7: Frankl Attitudinal Values가 박사님 원 ③에 1:1 대응으로 표시
    check(
        "X7: Frankl Attitudinal ↔ 박사님 ③ 1:1 대응 표시",
        "1:1 대응" in ext.realms_for("frankl_logotherapy")[3],
    )

    # X8: 서양식 ikigai의 박사님 ③ 공백이 차별점으로 명시
    check(
        "X8: 서양식 ikigai의 박사님 ③ 공백 = 박사님 차별점 명시",
        "차별점" in out and ("ikigai" in out.lower() or "Ikigai" in out),
    )

    # X9: SDT·PERMA·Aristotle·Frankl·Ikigai 1차 자료 출처 모두 포함
    primary_text_keywords = ["American Psychologist", "Beacon Press", "Free Press",
                             "Nicomachean", "Purpose Venn"]
    for kw in primary_text_keywords:
        check(f"X9.{kw}: 1차 자료 키워드 포함", kw in out)

    # X10: 학계 권위 URL (위키피디아·Stanford·APA 등) 포함
    authoritative_domains = [
        "en.wikipedia.org",
        "selfdeterminationtheory.org",
        "plato.stanford.edu",
        "apa.org",
        "ppc.sas.upenn.edu",
    ]
    for dom in authoritative_domains:
        check(f"X10.{dom}: 권위 도메인 URL 등록", dom in out)

    passed = sum(1 for _, ok, _ in CHECKS if ok)
    failed = len(CHECKS) - passed
    print(f"PASSED: {passed} / {len(CHECKS)}")
    if failed:
        print("\nFAILURES:")
        for name, ok, detail in CHECKS:
            if not ok:
                print(f"  - {name}  {detail}")
        return 1
    print("\n전 항목 PASS — 라운드 6 통과 (외부 학계 출처 5종 검증)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
