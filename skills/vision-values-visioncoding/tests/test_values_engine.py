"""vision-values-visioncoding 결정론 엔진 회귀 테스트.

본 테스트는 다음을 모두 검증한다 (실패하면 RuntimeError).
  - 데이터 무결성 (validate_data)
  - 매핑 조회 정확성 (MBTI·에니어그램·다중지능)
  - 카탈로그 외 가치 추가 차단
  - 17문항 진단 채점
  - 교집합 분석
  - 핵심 가치 3선 폴백 규칙 Step 1~5
  - 윙 인접성 검증
  - 모드 E 가중치 동률 처리
  - 출처 메타데이터 무결성

실행: python3 tests/test_values_engine.py
"""
from __future__ import annotations

import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import values_engine as ve  # noqa: E402


def check(name: str, cond: bool, details: str = "") -> bool:
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}{(' — ' + details) if details and not cond else ''}")
    return cond


def main() -> int:
    fails = 0

    # ── 1. 데이터 무결성 ──────────────────────────────────────────────
    v = ve.validate_data()
    if not check("data integrity (validate_data)", v["ok"], str(v["errors"])):
        fails += 1
    if not check("catalog size >= 80", v["catalog_count"] >= 80,
                 f"got {v['catalog_count']}"):
        fails += 1

    # ── 2. MBTI 매핑 정확성 (SKILL.md 본문과 1:1) ────────────────────
    mbti_expected = {
        "INFJ": ["Vision", "Wisdom", "Compassion", "Insight", "Integrity", "Service", "Hope"],
        "INTJ": ["Vision", "Strategy", "Wisdom", "Excellence", "Independence", "Truth", "Stewardship"],
        "ENTP": ["Creativity", "Curiosity", "Adventure", "Truth", "Innovation", "Freedom", "Vision"],
        "ISFP": ["Beauty", "Authenticity", "Compassion", "Freedom", "Harmony", "Sensitivity", "Peace"],
        "ESFJ": ["Service", "Community", "Harmony", "Hospitality", "Loyalty", "Tradition", "Love"],
    }
    for t, expected in mbti_expected.items():
        got = ve.mbti_values(t)
        if not check(f"MBTI[{t}] mapping", got == expected,
                     f"expected={expected} got={got}"):
            fails += 1

    # ── 3. 에니어그램 매핑 + 추구 세상 ────────────────────────────────
    enn_expected = {
        1: ["Justice", "Righteousness", "Order", "Integrity", "Discernment", "Truth", "Stewardship"],
        5: ["Knowledge", "Wisdom", "Discernment", "Creativity", "Truth", "Curiosity", "Independence"],
        9: ["Peace", "Harmony", "Humility", "Patience", "Reconciliation", "Acceptance", "Stability"],
    }
    for n, expected in enn_expected.items():
        if not check(f"Enneagram[{n}] mapping", ve.enneagram_values(n) == expected):
            fails += 1

    # ── 4. 윙 인접성 ─────────────────────────────────────────────────
    if not check("Enneagram 9 wings = [8,1]",
                 sorted(ve.enneagram_allowed_wings(9)) == [1, 8]):
        fails += 1
    if not check("Enneagram 1 wings = [9,2]",
                 sorted(ve.enneagram_allowed_wings(1)) == [2, 9]):
        fails += 1
    if not check("Enneagram 5 wings = [4,6]",
                 sorted(ve.enneagram_allowed_wings(5)) == [4, 6]):
        fails += 1

    # 인접하지 않은 윙은 거부
    try:
        ve.enneagram_with_wing(1, 5)
        check("non-adjacent wing rejected", False, "should have raised")
        fails += 1
    except ValueError:
        check("non-adjacent wing rejected", True)

    # ── 5. 다중지능 매핑 + alias 해소 ────────────────────────────────
    if not check("MI Linguistic mapping",
                 set(ve.mi_values(["Linguistic"])) ==
                 {"Truth", "Wisdom", "Communication", "Teaching", "Eloquence", "Clarity"}):
        fails += 1
    if not check("MI alias '언어' → Linguistic",
                 ve.resolve_mi_name("언어") == "Linguistic"):
        fails += 1
    if not check("MI alias '자기성찰' → Intrapersonal",
                 ve.resolve_mi_name("자기성찰") == "Intrapersonal"):
        fails += 1

    # ── 6. 17문항 간이 진단 채점 ─────────────────────────────────────
    enn_screen = ve.score_enneagram_screening([4, 5])
    if not check("Enneagram screening primary=4 wing=5 valid",
                 enn_screen["primary"] == 4 and enn_screen["wing_valid_for_primary"]):
        fails += 1
    enn_screen2 = ve.score_enneagram_screening([4, 7])  # 비인접
    if not check("Enneagram screening primary=4 wing=7 invalid (non-adjacent)",
                 not enn_screen2["wing_valid_for_primary"]):
        fails += 1

    mi_screen = ve.score_mi_screening([5, 3, 2, 4, 2, 4, 5, 3])
    # Linguistic=5, Intrapersonal=5, Musical=4, Interpersonal=4
    if not check("MI screening top3 ties resolved by input order",
                 mi_screen["top3"][:2] == ["Linguistic", "Intrapersonal"]):
        fails += 1

    # ── 7. 교집합 분석 ────────────────────────────────────────────────
    inter = ve.analyze_intersection(
        mbti_vals=["Vision", "Wisdom", "Truth"],
        enn_vals=["Truth", "Justice", "Order"],
        mi_vals=["Truth", "Wisdom", "Order"],
    )
    if not check("triple intersection = {Truth}",
                 inter.triple == ["Truth"]):
        fails += 1
    if not check("double intersection = {Order, Wisdom}",
                 sorted(inter.double) == ["Order", "Wisdom"]):
        fails += 1

    # ── 8. 핵심 가치 3선 폴백 — Step 3 (각 프레임워크 보증) ─────────
    # MBTI에만 등장하는 가치가 있을 때 3선에 반드시 들어가야 함
    r = ve.derive_core_three(
        mbti_vals=["Vision", "Wisdom", "Truth", "Excellence"],  # Excellence는 MBTI 고유
        enn_vals=["Wisdom", "Order", "Justice"],
        mi_vals=["Wisdom", "Truth", "Order"],
    )
    core = r["core_three"]
    # triple = Wisdom; double = Truth(mbti+mi), Order(enn+mi)
    # Step 1: Wisdom → Step 2: Truth, Order
    if not check("Step 1+2 → [Wisdom, Order, Truth] (tiebreak)",
                 set(core) == {"Wisdom", "Order", "Truth"}):
        fails += 1
    # 모든 프레임워크가 1개 이상 대변되는지
    fw = {
        "mbti": {"Vision","Wisdom","Truth","Excellence"},
        "enneagram": {"Wisdom","Order","Justice"},
        "mi": {"Wisdom","Truth","Order"},
    }
    for name, s in fw.items():
        if not check(f"Step 3: {name} represented in core",
                     any(c in s for c in core)):
            fails += 1

    # ── 9. 핵심 가치 3선 — Step 3 강제 대체 ──────────────────────────
    # triple 없음, double 4개(mbti+mi)로 3선이 모두 채워지면 enneagram 비대변 →
    # Step 3가 가장 약한 슬롯을 enneagram 가치로 대체해야 한다.
    r = ve.derive_core_three(
        mbti_vals=["Hope","Joy","Love","Authenticity"],
        enn_vals=["Justice","Order","Strength"],          # mbti·mi와 전혀 겹치지 않음
        mi_vals=["Hope","Joy","Love","Authenticity"],
    )
    if not check("Step 3 enforces enneagram coverage (replace weakest)",
                 any(c in {"Justice","Order","Strength"} for c in r["core_three"])):
        fails += 1
    if not check("Step 3 core size still 3",
                 len(r["core_three"]) == 3):
        fails += 1

    # ── 10. 모드 E 가중치 — Section A 동률 처리 ─────────────────────
    # double에 Section A(Wisdom) vs Section B(Excellence) 동률 → A 우선
    r = ve.derive_core_three(
        mbti_vals=["Wisdom", "Excellence"],
        enn_vals=["Wisdom", "Excellence"],
        mi_vals=None,
        mode_e=True,
    )
    # 둘 다 2개 교집합이지만 Wisdom(A) 우선
    if not check("Mode E: Section A preferred on tie (Wisdom > Excellence)",
                 r["core_three"][0] == "Wisdom"):
        fails += 1

    # ── 11. 카탈로그 외 가치 차단 (간접 — 데이터 무결성에서 이미 확인) ─
    if not check("All MBTI values in catalog (re-verify)",
                 all(v in ve.VALID_VALUES
                     for t in ve.MBTI["types"].values() for v in t["values"])):
        fails += 1
    if not check("All Enneagram values in catalog",
                 all(v in ve.VALID_VALUES
                     for t in ve.ENNEA["types"].values() for v in t["values"])):
        fails += 1
    if not check("All MI values in catalog",
                 all(v in ve.VALID_VALUES
                     for t in ve.MI["intelligences"].values() for v in t["values"])):
        fails += 1

    # ── 12. 잘못된 입력 거부 ─────────────────────────────────────────
    try:
        ve.mbti_values("ABCD")
        check("Invalid MBTI rejected", False); fails += 1
    except ValueError:
        check("Invalid MBTI rejected", True)

    try:
        ve.enneagram_values(10)
        check("Invalid enneagram rejected", False); fails += 1
    except ValueError:
        check("Invalid enneagram rejected", True)

    try:
        ve.resolve_mi_name("Telepathic")
        check("Invalid MI rejected", False); fails += 1
    except ValueError:
        check("Invalid MI rejected", True)

    try:
        ve.score_mi_screening([5]*7)
        check("MI screening wrong length rejected", False); fails += 1
    except ValueError:
        check("MI screening wrong length rejected", True)

    try:
        ve.score_mi_screening([6,3,2,4,2,4,5,3])
        check("MI screening out-of-range rejected", False); fails += 1
    except ValueError:
        check("MI screening out-of-range rejected", True)

    # ── 13. 출처 메타데이터 존재 ─────────────────────────────────────
    if not check("Sources: Riso-Hudson enneagram",
                 "Riso" in ve.SOURCES["enneagram"]["riso_hudson_nine_types"]["source"]):
        fails += 1
    if not check("Sources: Gardner MI",
                 "Gardner" in ve.SOURCES["multiple_intelligences"]["gardner_8_plus_1"]["source"]):
        fails += 1
    if not check("Sources: 2 Peter biblical",
                 "Peter" in ve.SOURCES["biblical"]["2_peter_1_5_7"]["passage"]
                 or "벧후" in ve.SOURCES["biblical"]["2_peter_1_5_7"]["passage"]):
        fails += 1

    # ── 14. 전체 프로파일 산출 ───────────────────────────────────────
    profile = ve.build_profile(mbti="INFJ", enneagram=1, wing=9,
                               mi=["Linguistic", "Intrapersonal", "Interpersonal"],
                               mode_e=True)
    if not check("build_profile returns core_three",
                 len(profile["core_three"]) >= 1):
        fails += 1
    if not check("build_profile mode_e_active=True",
                 profile["mode_e_active"] is True):
        fails += 1
    if not check("build_profile includes wing info",
                 profile["framework_values"]["enneagram"]["wing"]["wing"] == 9):
        fails += 1

    # ── 결과 ──────────────────────────────────────────────────────────
    print()
    print(f"=== {fails} FAILURE(S) ===" if fails else "=== ALL TESTS PASS ===")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
