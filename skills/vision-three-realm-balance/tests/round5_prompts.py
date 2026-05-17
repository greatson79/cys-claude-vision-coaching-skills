"""라운드 5 — 박사님 책 인용 정확성·SKILL.md 본문 일치·할루시네이션 차단 검증.

라운드 1·2·3·4에서 검증되지 않은 부분에 집중:
- SKILL.md 본문에 등장하는 5개 unique 박사님 인용 텍스트가 모두 결정론 등록과 일치
- 한 글자 변형도 verify_quote가 거부
- 절대 원칙 10개가 결정론 모듈에 등록
- 출처 표기가 항상 "최윤식 박사 『미래준비학교』(2016)"
- 페이지 번호 추측 금지 (페이지 키 부재)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import realm_balance as rb  # noqa: E402

SKILL_MD = Path(__file__).resolve().parent.parent / "SKILL.md"


CHECKS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, ok, detail))


def main() -> int:
    skill_text = SKILL_MD.read_text(encoding="utf-8")

    # T1: 5개 unique 박사님 인용이 모두 SKILL.md 본문에 *정확히* 등장
    for key, quote in rb.CYS_QUOTES.items():
        in_md = quote in skill_text
        check(f"T1.{key}: SKILL.md 본문에 원문 그대로 존재", in_md)

    # T2: verify_quote가 paraphrase를 거부 — '비전'을 '꿈'으로 한 번 바꾸면 거부되어야 함
    for key, quote in rb.CYS_QUOTES.items():
        bad = quote.replace("비전", "꿈", 1) if "비전" in quote else quote.replace("기쁨", "행복", 1)
        # 변형이 실제로 발생했는지 보장
        if bad == quote:
            bad = quote + " (추가)"
        check(
            f"T2.{key}: paraphrase 거부",
            not rb.verify_quote(key, bad),
            detail=f"bad={bad[:40]}...",
        )

    # T3: render_quote가 출처를 포함
    for key in rb.CYS_QUOTES:
        rendered = rb.render_quote(key)
        check(
            f"T3.{key}: render에 출처 '최윤식 박사 『미래준비학교』(2016)' 포함",
            "최윤식 박사 『미래준비학교』(2016)" in rendered,
        )

    # T4: 등록된 키 외에는 KeyError
    try:
        rb.get_quote("nonexistent_key_xyz")
        check("T4: 미등록 키 KeyError", False, "예외가 발생하지 않음")
    except KeyError:
        check("T4: 미등록 키 KeyError", True)

    # T5: 10개 절대 원칙이 모두 등록
    principles = rb.list_principles()
    check("T5: 절대 원칙 10개", len(principles) == 10, f"실제 {len(principles)}개")

    # T6: SKILL.md "절대 원칙" 섹션의 페이지 추측 금지 명시
    check(
        "T6: 페이지 추측 금지 명시",
        "페이지 번호를 *추측·날조* 금지" in skill_text or "페이지 단위 정보가 보존되어 있지 않으며" in skill_text,
    )

    # T7: SKILL.md가 결정론 호출 의무를 명시
    check(
        "T7: SKILL.md '결정론 호출 의무' 섹션 존재",
        "결정론 호출 의무" in skill_text and "rb.diagnose" in skill_text,
    )

    # T8: 8개 패턴 매트릭스가 SKILL.md 표와 일치하는 진단명 — 본문 표기와 1:1
    expected_names_in_md = [
        "건강한 비전", "정신적 가치 결여", "가족·세상 단절",
        "자기 기쁨 부재", "개인 욕망", "자기희생·세상일",
        "왜곡된 사명·질", "비전 아님",
    ]
    for name in expected_names_in_md:
        check(f"T8.{name}: SKILL.md 본문에 등장", name in skill_text)

    # T9: render_quote 출력 형식이 SKILL.md "출처 표시 규약"(따옴표 + 출처) 준수
    sample = rb.render_quote("closing")
    check(
        "T9: render 출력에 따옴표 + 출처 동시 포함",
        '"' in sample and "최윤식 박사" in sample,
    )

    # T10: 박사님 책 외 출처를 명시하지 않음 — render_quote가 외부 출처를 만들지 않음
    for key in rb.CYS_QUOTES:
        out = rb.render_quote(key)
        # 박사님 책 외 출처 토큰이 없는지 검증
        forbidden = ["Wikipedia", "Bavinck", "Calvin", "Augustine", "ikigai", "p.", "page"]
        no_other_src = not any(tok in out for tok in forbidden)
        check(f"T10.{key}: 박사님 책 외 출처 없음", no_other_src)

    passed = sum(1 for _, ok, _ in CHECKS if ok)
    failed = len(CHECKS) - passed
    print(f"PASSED: {passed} / {len(CHECKS)}")
    if failed:
        print("\nFAILURES:")
        for name, ok, detail in CHECKS:
            if not ok:
                print(f"  - {name}  {detail}")
        return 1
    print("\n전 항목 PASS — 라운드 5 통과 (인용·원칙·SKILL.md 일치 검증)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
