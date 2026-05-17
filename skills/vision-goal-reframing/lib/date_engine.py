"""Backcasting 시간선 결정론 계산 엔진.

LLM이 "5년 후·1년 후·다음 분기·1주 후·내일" 같은 표현을 자연어로 추론하면
연도·분기·날짜가 빗나갈 수 있다. 본 모듈은 모든 시간 계산을 표준 라이브러리로 처리한다.

사용 예:
    from lib.date_engine import build_timeline
    print(build_timeline("2026-05-17"))
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from dataclasses import dataclass, asdict
from typing import Optional


WEEKDAY_KR = ["월", "화", "수", "목", "금", "토", "일"]


@dataclass(frozen=True)
class TimePoint:
    label: str             # 예: "5년 후"
    code: str              # 예: "Y+5"
    iso_date: str          # YYYY-MM-DD
    year: int
    month: int
    day: int
    quarter: str           # "Q1".."Q4"
    quarter_months: str    # "1-3월" 등
    weekday_kr: str        # 월/화/...
    note: str = ""


def _parse(today: Optional[str]) -> _dt.date:
    if today is None:
        return _dt.date.today()
    return _dt.date.fromisoformat(today)


def _quarter_of(month: int) -> tuple[str, str]:
    if month in (1, 2, 3):
        return "Q1", "1-3월"
    if month in (4, 5, 6):
        return "Q2", "4-6월"
    if month in (7, 8, 9):
        return "Q3", "7-9월"
    return "Q4", "10-12월"


def _add_years(date: _dt.date, years: int) -> _dt.date:
    try:
        return date.replace(year=date.year + years)
    except ValueError:
        # 윤년 2/29 → 비윤년 변환 보정
        return date.replace(year=date.year + years, day=28)


def _first_day_of_next_quarter(today: _dt.date) -> _dt.date:
    q = (today.month - 1) // 3
    next_q_start_month = q * 3 + 4
    year = today.year
    if next_q_start_month > 12:
        year += 1
        next_q_start_month -= 12
    return _dt.date(year, next_q_start_month, 1)


def _last_day_of_quarter(d: _dt.date) -> _dt.date:
    q = (d.month - 1) // 3
    end_month = q * 3 + 3
    if end_month == 12:
        return _dt.date(d.year, 12, 31)
    return _dt.date(d.year, end_month + 1, 1) - _dt.timedelta(days=1)


def _to_point(label: str, code: str, d: _dt.date, note: str = "") -> TimePoint:
    q, qm = _quarter_of(d.month)
    return TimePoint(
        label=label,
        code=code,
        iso_date=d.isoformat(),
        year=d.year,
        month=d.month,
        day=d.day,
        quarter=q,
        quarter_months=qm,
        weekday_kr=WEEKDAY_KR[d.weekday()],
        note=note,
    )


def build_timeline(today: Optional[str] = None) -> dict:
    """Backcasting 5단계 시간선 — 기준일에서 결정론적으로 산출.

    반환:
      dict — 키: today, tomorrow, one_week, next_quarter, one_year, five_years
    """
    base = _parse(today)
    tomorrow = base + _dt.timedelta(days=1)
    one_week = base + _dt.timedelta(days=7)
    next_q_start = _first_day_of_next_quarter(base)
    next_q_end = _last_day_of_quarter(next_q_start)
    one_year = _add_years(base, 1)
    five_years = _add_years(base, 5)

    return {
        "today": asdict(_to_point("기준일 (오늘)", "T+0", base)),
        "tomorrow": asdict(_to_point("내일 아침", "T+1", tomorrow, note="첫 한 걸음 30분 행동")),
        "one_week": asdict(_to_point("1주 후", "T+7", one_week, note="이번 주 마일스톤")),
        "next_quarter": {
            "label": "다음 분기",
            "code": "Q+1",
            "start_iso": next_q_start.isoformat(),
            "end_iso": next_q_end.isoformat(),
            "year": next_q_start.year,
            "quarter": _quarter_of(next_q_start.month)[0],
            "quarter_months": _quarter_of(next_q_start.month)[1],
            "note": "3개월 후 골격 완성 수준의 중간 목표",
        },
        "one_year": asdict(_to_point("1년 후", "Y+1", one_year, note="STG(Short-Term Goal)")),
        "five_years": asdict(_to_point("5년 후", "Y+5", five_years, note="LTG(Long-Term Goal)")),
    }


def format_human(timeline: dict) -> str:
    """워크북 출력용 텍스트 포맷."""
    nq = timeline["next_quarter"]
    return "\n".join([
        f"- 5년 후 ({timeline['five_years']['iso_date']}, {timeline['five_years']['year']}년 {timeline['five_years']['quarter']}): LTG",
        f"- 1년 후 ({timeline['one_year']['iso_date']}, {timeline['one_year']['year']}년 {timeline['one_year']['quarter']}): STG",
        f"- 다음 분기 ({nq['start_iso']} ~ {nq['end_iso']}, {nq['year']}년 {nq['quarter']} = {nq['quarter_months']}): 분기 목표",
        f"- 1주 후 ({timeline['one_week']['iso_date']}, {timeline['one_week']['weekday_kr']}요일): 주간 마일스톤",
        f"- 내일 아침 ({timeline['tomorrow']['iso_date']}, {timeline['tomorrow']['weekday_kr']}요일): 30분 행동",
    ])


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    tl = build_timeline(arg)
    print(json.dumps(tl, ensure_ascii=False, indent=2))
    print()
    print(format_human(tl))
