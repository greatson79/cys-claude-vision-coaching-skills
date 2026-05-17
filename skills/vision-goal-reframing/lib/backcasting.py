"""Backcasting 5단계 구조 검증.

Robinson 1982/1990 방법론에 따라 5년→1년→1분기→1주→내일의 5개 시점이
빠짐없이·올바른 단위 순서로 채워졌는지 결정론으로 검증한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


REQUIRED_HORIZONS = ["five_years", "one_year", "next_quarter", "one_week", "tomorrow"]
HORIZON_LABEL = {
    "five_years": "5년 후 (LTG)",
    "one_year": "1년 후 (STG)",
    "next_quarter": "다음 분기",
    "one_week": "1주 후",
    "tomorrow": "내일 아침",
}
MIN_CHARS = 5


@dataclass
class BackcastingReport:
    passed: bool
    missing: List[str] = field(default_factory=list)
    too_short: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    horizons: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return vars(self)


def validate_backcasting(horizons: Dict[str, str]) -> BackcastingReport:
    """5개 시점 컨텐츠가 모두 입력됐는지·내용이 비지 않았는지 확인."""
    rep = BackcastingReport(passed=False, horizons=horizons)

    for key in REQUIRED_HORIZONS:
        if key not in horizons:
            rep.missing.append(HORIZON_LABEL[key])
        elif not horizons[key] or len(horizons[key].strip()) < MIN_CHARS:
            rep.too_short.append(HORIZON_LABEL[key])

    if rep.missing:
        rep.errors.append(f"누락 시점: {', '.join(rep.missing)}")
    if rep.too_short:
        rep.errors.append(f"내용이 {MIN_CHARS}자 미만: {', '.join(rep.too_short)}")

    extra = [k for k in horizons.keys() if k not in REQUIRED_HORIZONS]
    if extra:
        rep.errors.append(f"허용되지 않은 시점 키: {', '.join(extra)} (REQUIRED_HORIZONS만 허용)")

    rep.passed = not rep.errors
    return rep


def render_backcasting(timeline: dict, contents: Dict[str, str]) -> str:
    """timeline(date_engine) + contents(사용자 입력)을 합쳐 출력."""
    nq = timeline["next_quarter"]
    out = []
    out.append(f"- **5년 후** ({timeline['five_years']['year']}년 {timeline['five_years']['quarter']}, {timeline['five_years']['iso_date']}): {contents.get('five_years','—')}")
    out.append(f"- **1년 후** ({timeline['one_year']['year']}년 {timeline['one_year']['quarter']}, {timeline['one_year']['iso_date']}): {contents.get('one_year','—')}")
    out.append(f"- **다음 분기** ({nq['year']}년 {nq['quarter']} {nq['quarter_months']}, {nq['start_iso']}~{nq['end_iso']}): {contents.get('next_quarter','—')}")
    out.append(f"- **1주 후** ({timeline['one_week']['iso_date']}, {timeline['one_week']['weekday_kr']}요일): {contents.get('one_week','—')}")
    out.append(f"- **내일 아침** ({timeline['tomorrow']['iso_date']}, {timeline['tomorrow']['weekday_kr']}요일): {contents.get('tomorrow','—')}")
    return "\n".join(out)


if __name__ == "__main__":
    import json
    sample = {
        "five_years": "단행본 5권 + 글로벌 강연 50회",
        "one_year": "첫 단행본 출간 + 강연 10회",
        "next_quarter": "골격 완성 + 출판사 미팅 3건",
        "one_week": "1~3장 골격 보강 + 출판사 5곳 조사",
        "tomorrow": "골격 현재 버전 30분 검토 + 보강 영역 3개 식별",
    }
    rep = validate_backcasting(sample)
    print(json.dumps(rep.as_dict(), ensure_ascii=False, indent=2))
