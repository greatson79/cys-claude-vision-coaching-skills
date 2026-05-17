"""OKR 결정론 검증기.

Doerr (Measure What Matters, 2018) + Google re:Work 그레이딩 척도에 따라
- Objective 1개 존재 여부
- Key Results 3~5개 범위
- 각 KR 측정성(숫자·단위 보유)
- 채점 시 색대역(0.0~0.3 red, 0.4~0.6 yellow, 0.7~1.0 green) 산출
까지 자연어 추론 없이 처리한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


# Python re의 \b는 한글 인접 시 작동하지 않음 → 문자열 기반 검사를 병행한다.
_MEASURABLE_REGEX = re.compile(
    r"\d|(권|회|명|개|건|쪽|페이지|편|장|분|시간|일|주|개월|년|kg|km|%|퍼센트|만|억|원|"
    r"book|page|hour|day|week|month|year|percent)",
    flags=re.IGNORECASE,
)


@dataclass
class KRCheck:
    text: str
    measurable: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class OkrReport:
    objective: str
    key_results: List[KRCheck]
    okr_type: str          # "committed" or "aspirational"
    passed: bool
    errors: List[str]

    def as_dict(self) -> dict:
        return {
            "objective": self.objective,
            "okr_type": self.okr_type,
            "passed": self.passed,
            "errors": self.errors,
            "key_results": [vars(k) for k in self.key_results],
        }


def validate_okr(
    objective: str,
    key_results: List[str],
    okr_type: str = "aspirational",
) -> OkrReport:
    """OKR 구조 검증.

    Args:
        objective: 정성적·영감적 목표 1문장.
        key_results: 측정 가능 결과 지표 리스트.
        okr_type: "committed" | "aspirational"
    """
    errors: List[str] = []

    if not objective or len(objective.strip()) < 5:
        errors.append("Objective가 비었거나 너무 짧음(>=5자)")

    if okr_type not in ("committed", "aspirational"):
        errors.append(f"okr_type은 'committed' 또는 'aspirational'이어야 함 (입력: {okr_type})")

    n = len(key_results)
    if n < 3:
        errors.append(f"Key Results가 {n}개. 최소 3개 필요 (Doerr 권장 범위 3~5)")
    elif n > 5:
        errors.append(f"Key Results가 {n}개. 최대 5개 권장 (Doerr 권장 범위 3~5)")

    checks: List[KRCheck] = []
    for i, kr in enumerate(key_results, 1):
        issues: List[str] = []
        if len(kr.strip()) < 5:
            issues.append("너무 짧음")
        m = bool(_MEASURABLE_REGEX.search(kr))
        if not m:
            issues.append("수치·단위 누락 — 측정 불가")
        checks.append(KRCheck(text=kr, measurable=m, issues=issues))
        if issues:
            errors.append(f"KR{i}: {', '.join(issues)}")

    return OkrReport(
        objective=objective,
        key_results=checks,
        okr_type=okr_type,
        passed=(len(errors) == 0),
        errors=errors,
    )


def grade_band(score: float) -> dict:
    """Google re:Work + Doerr 색대역 분류 (0.0~1.0)."""
    if not (0.0 <= score <= 1.0):
        return {"band": "INVALID", "color": "n/a", "note": "0.0~1.0 범위를 벗어남"}
    if score <= 0.3:
        return {"band": "red", "color": "🔴", "note": "주의 — 계획·자원·실행 재검토 필요"}
    if score <= 0.6:
        return {"band": "yellow", "color": "🟡", "note": "진척 미흡 — 보완 조치 필요"}
    return {"band": "green", "color": "🟢", "note": "이상적 — Doerr 0.7~1.0 sweet spot"}


def expected_score(okr_type: str) -> float:
    """Google 공식 — committed = 1.0, aspirational = 0.7."""
    return 1.0 if okr_type == "committed" else 0.7


def render_okr(report: OkrReport) -> str:
    out = [f"**Objective** ({report.okr_type}): {report.objective}", "", "**Key Results**:"]
    for i, kr in enumerate(report.key_results, 1):
        mark = "✓" if kr.measurable else "✗"
        out.append(f"- KR{i} [{mark}]: {kr.text}")
        if kr.issues:
            out.append(f"  - 보완: {', '.join(kr.issues)}")
    out.append("")
    out.append(f"**채점 기대치**: {expected_score(report.okr_type)} ({report.okr_type})")
    if report.errors:
        out.append("")
        out.append("**검증 오류**:")
        for e in report.errors:
            out.append(f"- {e}")
    return "\n".join(out)


if __name__ == "__main__":
    import json
    r = validate_okr(
        objective="2027년 안에 AGI 미래학 단행본 첫 권을 출간하여 한국 미래학 담론에 기여한다",
        key_results=[
            "2027 Q1까지 골격 + 6장 초고 완성",
            "2027 Q2까지 12장 초고 완성",
            "2027 Q3까지 출판사 계약 체결",
            "2027 Q4까지 초판 1,000부 출간 + 강연 3회 진행",
        ],
        okr_type="aspirational",
    )
    print(json.dumps(r.as_dict(), ensure_ascii=False, indent=2))
    print()
    print(render_okr(r))
    print()
    print("score 0.72 →", grade_band(0.72))
    print("score 0.5  →", grade_band(0.5))
    print("score 0.15 →", grade_band(0.15))
