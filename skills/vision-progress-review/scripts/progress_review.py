"""
vision-progress-review — 결정론 라이브러리 (Deterministic Engine)

이 파일은 LLM이 자연어로 추론하면 할루시네이션 위험이 있는 작업을
결정론적 함수로 환원한다.

결정론 환원 대상 (LLM 자연어 추론 금지):
  1. 학술 출처 조회 (저자·연도·페이지·출판사·ISBN)
  2. 날짜 검증·파싱 (ISO 8601 YYYY-MM-DD 강제)
  3. 다음 점검 일정 계산 (주 +7 / 월 +28 / 분기 +90 / 연 +365)
  4. 양식 마지막 "다음 점검 일정" 블록 자동 산출
  5. 달성률 분류 (✓ ≥80%, △ 50-79%, ✗ <50%)
  6. OKR 점수 분류 (0.0-0.3 / 0.4-0.6 / 0.7-1.0; Doerr 2018)
  7. Pivot 트리거 판정 (분기 핵심 KPI ≤ 50% + 가설 자체 문제)
  8. 자동 추천 단위 산출 (마지막 점검일·오늘 기준)
  9. 빗나감 패턴 감지 (3회 연속 주간·2회 연속 마일스톤)
 10. "매월 마지막 금요일" 캘린더 계산
 11. 완수율 계산 (소수·반올림 규칙 통일)
 12. 양식 결정론 렌더링 (주·월·분기·연·단발)
 13. 양식 필수 항목 검증

작성: 2026-05-17
근거: Drucker (1954), Doran (1981), Grove (1983), Doerr (2018),
      Ries (2011), Clear (2018), Derby & Larsen (2006) — 1차 자료 직접 확인.
"""

from __future__ import annotations

import argparse
import calendar
import json
import re
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# 1. 학술 출처 카탈로그 (결정론 — LLM 자연어 추론 금지)
# ============================================================================

PROGRESS_SOURCES: Dict[str, Dict[str, Any]] = {
    "drucker_1954": {
        "key": "drucker_1954",
        "author": "Peter F. Drucker",
        "year": 1954,
        "title": "The Practice of Management",
        "publisher": "Harper & Brothers (New York)",
        "isbn_13": "978-0-06-091316-8",
        "relevance": (
            "MBO (Management by Objectives) 개념의 1차 출처. 11장 "
            '"Management by Objectives and Self-Control" 에서 정식화. '
            "현대 KPI 전통의 시조."
        ),
        "verified": True,
    },
    "doran_1981": {
        "key": "doran_1981",
        "author": "George T. Doran",
        "year": 1981,
        "title": "There's a S.M.A.R.T. Way to Write Management's Goals and Objectives",
        "journal": "Management Review",
        "volume_pages": "70(11): 35-36",
        "publisher": "AMA FORUM (American Management Association)",
        "smart_letters": {
            "S": "Specific — target a specific area for improvement",
            "M": "Measurable — quantify or at least suggest an indicator of progress",
            "A": "Assignable — specify who will do it",
            "R": "Realistic — state what results can realistically be achieved",
            "T": "Time-related — specify when the result(s) can be achieved",
        },
        "note": (
            "Doran 1981 원안의 'A·R'은 'Assignable·Realistic'. 후대에 "
            "'Achievable·Relevant'로 변형 정착(가장 보편). 본 스킬은 "
            "후대 통용 표기를 사용하되 1차 출처를 함께 명시한다."
        ),
        "verified": True,
    },
    "grove_1983": {
        "key": "grove_1983",
        "author": "Andrew S. Grove",
        "year": 1983,
        "title": "High Output Management",
        "publisher": "Random House (1983 초판) / Vintage (1995 개정)",
        "isbn_13": "978-0-679-76288-3",
        "relevance": (
            "OKR(Objectives and Key Results)의 원형(Intel iMBO). Grove가 "
            "Intel CEO 시절 Drucker MBO를 자기식으로 재정의·확장."
        ),
        "verified": True,
    },
    "doerr_2018": {
        "key": "doerr_2018",
        "author": "John Doerr",
        "year": 2018,
        "title": "Measure What Matters: How Google, Bono, and the Gates Foundation Rock the World with OKRs",
        "publisher": "Portfolio (Penguin)",
        "isbn_13": "978-0-525-53622-2",
        "okr_scoring_quote": (
            'Doerr 2018: "On a scale of 0.0 to 1.0, an average score of 0.7 '
            'is considered a success for a stretch OKR." (Google standard)'
        ),
        "okr_scoring_bands": {
            "0.0-0.3": "no real progress (red)",
            "0.4-0.6": "progress but short of completion (yellow)",
            "0.7-1.0": "delivered (green); consistent 1.0 = goal too easy",
        },
        "verified": True,
    },
    "ries_2011": {
        "key": "ries_2011",
        "author": "Eric Ries",
        "year": 2011,
        "title": "The Lean Startup: How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses",
        "publisher": "Crown Business",
        "isbn_13": "978-0-307-88791-7",
        "pivot_quote": (
            'Ries 2011, ch. 8: "A pivot is a structured course correction '
            'designed to test a new fundamental hypothesis about the product, '
            'strategy, and engine of growth."'
        ),
        "build_measure_learn": "Build → Measure → Learn (validated learning loop)",
        "verified": True,
    },
    "clear_2018": {
        "key": "clear_2018",
        "author": "James Clear",
        "year": 2018,
        "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones",
        "publisher": "Avery (Penguin Random House)",
        "isbn_13": "978-0-7352-1129-2",
        "never_miss_twice_quote": (
            'Clear 2018, ch. 16 "How to Stick with Good Habits Every Day": '
            '"Missing once is an accident. Missing twice is the start of a new habit."'
        ),
        "verified": True,
    },
    "derby_larsen_2006": {
        "key": "derby_larsen_2006",
        "author": "Esther Derby and Diana Larsen",
        "year": 2006,
        "title": "Agile Retrospectives: Making Good Teams Great",
        "publisher": "Pragmatic Bookshelf",
        "isbn_13": "978-0-9776-1664-6",
        "relevance": (
            "Stop/Start/Continue를 비롯한 다양한 회고 패턴을 Agile 표준 회고 "
            "도구로 정착시킨 1차 단행본. 'Stop/Start/Continue' 그 자체의 "
            "기원은 명확치 않으나(Polaroid 1970s 등 industrial folklore), "
            "현대 회고 도구 표준화의 학술 1차 자료는 Derby & Larsen 2006."
        ),
        "verified": True,
    },
}


def lookup_source(key: str) -> Dict[str, Any]:
    """학술 출처 조회. 키가 없으면 KeyError."""
    if key not in PROGRESS_SOURCES:
        raise KeyError(
            f"Unknown source key: {key!r}. "
            f"Available: {sorted(PROGRESS_SOURCES.keys())}"
        )
    return PROGRESS_SOURCES[key]


def format_citation(key: str) -> str:
    """짧은 인용 문자열."""
    src = lookup_source(key)
    author = src["author"]
    year = src["year"]
    title = src["title"]
    journal = src.get("journal")
    if journal:
        vp = src.get("volume_pages", "")
        return f"{author} ({year}). {title}. {journal} {vp}."
    publisher = src.get("publisher", "")
    return f"{author} ({year}). {title}. {publisher}."


def all_citations_block() -> str:
    """모든 출처를 마크다운으로 출력."""
    lines = ["## 본 스킬 인용 출처 (1차 자료 검증)"]
    for k in PROGRESS_SOURCES:
        lines.append(f"- **{k}** — {format_citation(k)}")
    return "\n".join(lines)


# ============================================================================
# 2. 날짜 파싱·검증 (ISO 8601 YYYY-MM-DD 강제)
# ============================================================================

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_date(s: str) -> date:
    """YYYY-MM-DD 문자열을 date 로 변환. 형식 위반 즉시 예외."""
    if not isinstance(s, str) or not ISO_DATE_RE.match(s):
        raise ValueError(
            f"Date must be ISO 8601 'YYYY-MM-DD', got {s!r}"
        )
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid calendar date {s!r}: {e}") from e


def fmt(d: date) -> str:
    """date 를 YYYY-MM-DD 로."""
    return d.strftime("%Y-%m-%d")


# ============================================================================
# 3. 점검 단위 정의·다음 점검 일정 계산
# ============================================================================

UNIT_DAYS: Dict[str, int] = {
    "weekly": 7,
    "monthly": 28,
    "quarterly": 90,
    "annual": 365,
}

UNIT_LABEL_KO: Dict[str, str] = {
    "weekly": "주간 점검",
    "monthly": "월간 점검",
    "quarterly": "분기 점검",
    "annual": "연간 점검",
}

UNIT_EMOJI: Dict[str, str] = {
    "weekly": "✅",
    "monthly": "📅",
    "quarterly": "📊",
    "annual": "🌅",
}

UNIT_TIMEBOX_KO: Dict[str, str] = {
    "weekly": "권장 30분",
    "monthly": "권장 1시간",
    "quarterly": "권장 2시간",
    "annual": "권장 반나절",
}


def next_check_date(last: date, unit: str) -> date:
    """단위별 다음 점검 일정 (last + UNIT_DAYS[unit])."""
    if unit not in UNIT_DAYS:
        raise ValueError(
            f"Unknown unit {unit!r}; expected one of {sorted(UNIT_DAYS)}"
        )
    return last + timedelta(days=UNIT_DAYS[unit])


def next_check_schedule_block(current_check_date: date, current_unit: str) -> str:
    """
    양식 마지막에 들어가는 '다음 점검 일정' 블록을 결정론으로 산출.

    규칙: 현재 점검의 단위 이상 (큰 단위)까지 모두 산출.
      - weekly  → weekly
      - monthly → weekly + monthly
      - quarterly → weekly + monthly + quarterly
      - annual → weekly + monthly + quarterly + annual
    """
    if current_unit not in UNIT_DAYS:
        raise ValueError(
            f"Unknown unit {current_unit!r}; expected one of {sorted(UNIT_DAYS)}"
        )
    order = ["weekly", "monthly", "quarterly", "annual"]
    idx = order.index(current_unit)
    units_to_show = order[: idx + 1]
    lines = ["### 다음 점검 일정"]
    for u in units_to_show:
        d = next_check_date(current_check_date, u)
        lines.append(f"- 다음 {UNIT_LABEL_KO[u]}: {fmt(d)}")
    return "\n".join(lines)


# ============================================================================
# 4. 달성률 분류 (SMART의 Measurable; Doran 1981)
# ============================================================================

@dataclass
class AchievementVerdict:
    rate_pct: float          # 0~100 (반올림 전)
    rounded_pct: int         # 0~100 반올림
    symbol: str              # ✓ / △ / ✗
    band_label: str          # "달성" / "부분 달성" / "대폭 미달"
    explanation: str


def categorize_achievement(rate_pct: float) -> AchievementVerdict:
    """달성률(0~100)을 ✓/△/✗ 로 분류.

    기준 (SKILL.md 분기 점검 절):
      ✓ ≥ 80%  (목표 거의 충족)
      △ 50% ≤ rate < 80% (부분 달성)
      ✗ < 50%  (대폭 미달)
    """
    if not isinstance(rate_pct, (int, float)):
        raise TypeError("rate_pct must be a number 0~100")
    if rate_pct < 0 or rate_pct > 100:
        raise ValueError(
            f"rate_pct must be in [0, 100], got {rate_pct}"
        )
    rounded = int(round(rate_pct))
    if rate_pct >= 80:
        return AchievementVerdict(
            rate_pct=rate_pct,
            rounded_pct=rounded,
            symbol="✓",
            band_label="달성",
            explanation="목표 거의 충족 (≥ 80%)",
        )
    if rate_pct >= 50:
        return AchievementVerdict(
            rate_pct=rate_pct,
            rounded_pct=rounded,
            symbol="△",
            band_label="부분 달성",
            explanation="50% ≤ 달성률 < 80%",
        )
    return AchievementVerdict(
        rate_pct=rate_pct,
        rounded_pct=rounded,
        symbol="✗",
        band_label="대폭 미달",
        explanation="달성률 < 50%",
    )


# ============================================================================
# 5. OKR 점수 분류 (Doerr 2018 / Google standard)
# ============================================================================

@dataclass
class OKRVerdict:
    score: float             # 0.0 ~ 1.0
    band: str                # "red" / "yellow" / "green"
    band_label_ko: str       # 한국어 라벨
    explanation: str
    too_easy_warning: bool


def categorize_okr(score: float) -> OKRVerdict:
    """OKR 점수(0.0~1.0)를 Google·Doerr 기준으로 분류.

    0.0~0.3: 진척 없음 (red)
    0.4~0.6: 진척 있으나 미완 (yellow)
    0.7~1.0: 성공 / 큰 진척 (green) — 0.7 이 stretch goal 이상적 목표치
    """
    if not isinstance(score, (int, float)):
        raise TypeError("score must be a number 0.0~1.0")
    if score < 0.0 or score > 1.0:
        raise ValueError(f"score must be in [0.0, 1.0], got {score}")
    if score < 0.4:
        return OKRVerdict(
            score=score,
            band="red",
            band_label_ko="진척 없음",
            explanation="0.0-0.3 (Doerr 2018): no real progress",
            too_easy_warning=False,
        )
    if score < 0.7:
        return OKRVerdict(
            score=score,
            band="yellow",
            band_label_ko="진척 있으나 미완",
            explanation="0.4-0.6 (Doerr 2018): progress but short of completion",
            too_easy_warning=False,
        )
    too_easy = score >= 0.95
    return OKRVerdict(
        score=score,
        band="green",
        band_label_ko="성공/큰 진척",
        explanation=(
            "0.7-1.0 (Doerr 2018): delivered; 0.7이 stretch goal의 이상적 목표치"
        ),
        too_easy_warning=too_easy,
    )


# ============================================================================
# 6. Pivot 트리거 판정 (Ries 2011)
# ============================================================================

@dataclass
class PivotDecision:
    trigger: bool                  # Pivot 검토 대상인지
    reason_code: str               # "hypothesis_fail" / "execution_gap" / "ok"
    explanation: str
    next_action: str


def pivot_trigger_check(
    kpi_rate_pct: float,
    cause_category: str,
) -> PivotDecision:
    """분기 KPI 달성률 + 미달 원인 카테고리로 Pivot 검토 여부 판정.

    Ries 2011 정의: Pivot 은 *제품·전략·성장엔진에 관한 새 핵심 가설을
    검증하기 위한* 구조적 방향 전환. 단순 실행 부족은 Pivot 아님.

    Args:
      kpi_rate_pct: 분기 핵심 KPI 달성률 (0~100)
      cause_category: 미달 원인 카테고리
        - "hypothesis"   : 가설 자체 문제 (제품·전략·성장엔진)
        - "execution"    : 실행 부족 (노력·시간·집중)
        - "external"     : 외부 환경 변수
        - "unknown"      : 미분류
    """
    if kpi_rate_pct < 0 or kpi_rate_pct > 100:
        raise ValueError(f"kpi_rate_pct must be 0~100, got {kpi_rate_pct}")
    valid_causes = {"hypothesis", "execution", "external", "unknown"}
    if cause_category not in valid_causes:
        raise ValueError(
            f"cause_category must be one of {sorted(valid_causes)}, "
            f"got {cause_category!r}"
        )
    if kpi_rate_pct > 50:
        return PivotDecision(
            trigger=False,
            reason_code="ok",
            explanation=(
                f"분기 핵심 KPI 달성률 {kpi_rate_pct:.0f}% > 50% — "
                "Pivot 트리거 임계 미도달"
            ),
            next_action="Stop/Start/Continue 회고로 미세 조정",
        )
    # kpi <= 50% 인 상황
    if cause_category == "execution":
        return PivotDecision(
            trigger=False,
            reason_code="execution_gap",
            explanation=(
                f"분기 핵심 KPI {kpi_rate_pct:.0f}% ≤ 50%이나 원인이 *실행 부족*. "
                "Ries 2011 정의상 Pivot 아님."
            ),
            next_action=(
                "시스템 보강 — vision-follow-through-habits 재실행 "
                "(Atomic Habits 4법칙 점검)"
            ),
        )
    if cause_category == "external":
        return PivotDecision(
            trigger=True,
            reason_code="external_variable",
            explanation=(
                f"분기 핵심 KPI {kpi_rate_pct:.0f}% ≤ 50% + 외부 변수 변화. "
                "환경 적응 재계획 필요."
            ),
            next_action=(
                "환경 변수 분석 → STG·LTG 재조정 검토 "
                "(필요 시 vision-clarity-coaching 재실행)"
            ),
        )
    if cause_category == "hypothesis":
        return PivotDecision(
            trigger=True,
            reason_code="hypothesis_fail",
            explanation=(
                f"분기 핵심 KPI {kpi_rate_pct:.0f}% ≤ 50% + 가설 자체 문제. "
                "Ries 2011 정의의 Pivot 조건 충족."
            ),
            next_action=(
                "STG 재설계 — 제품·전략·성장엔진의 새 핵심 가설 도출 "
                "→ vision-clarity-coaching·vision-goal-reframing 재실행"
            ),
        )
    # unknown
    return PivotDecision(
        trigger=True,
        reason_code="unknown_cause",
        explanation=(
            f"분기 핵심 KPI {kpi_rate_pct:.0f}% ≤ 50% + 원인 미분류. "
            "사용자에게 원인 카테고리 추가 입력 요청."
        ),
        next_action=(
            "사용자에게 미달 원인 4 카테고리(hypothesis/execution/external/unknown) "
            "중 선택 요청 후 재판정"
        ),
    )


# ============================================================================
# 7. 자동 추천 단위 산출
# ============================================================================

@dataclass
class Recommendation:
    recommended_unit: Optional[str]   # weekly/monthly/quarterly/annual 또는 None
    reason: str
    overdue_units: List[Tuple[str, int]]   # (unit, overdue_days)
    upcoming_units: List[Tuple[str, int]]  # (unit, remaining_days)


def auto_recommend(
    last_dates: Dict[str, Optional[str]],
    today: Optional[str] = None,
) -> Recommendation:
    """마지막 점검일·오늘 기준 자동 추천 단위 산출.

    Args:
      last_dates: { "weekly": "YYYY-MM-DD"|None, "monthly": ..., "quarterly": ..., "annual": ... }
      today: "YYYY-MM-DD" 또는 None (None 이면 시스템 today 사용)

    추천 우선순위: annual > quarterly > monthly > weekly (큰 단위 우선)
    어떤 단위도 도래하지 않으면 None 반환 + 잔여 일수 안내.
    """
    today_d = parse_date(today) if today else date.today()
    valid_units = ["annual", "quarterly", "monthly", "weekly"]

    overdue: List[Tuple[str, int]] = []
    upcoming: List[Tuple[str, int]] = []

    for unit in valid_units:
        raw = last_dates.get(unit)
        if raw is None or raw == "":
            continue
        last_d = parse_date(raw)
        if last_d > today_d:
            raise ValueError(
                f"last_dates[{unit!r}] = {raw} is in the future of today={fmt(today_d)}"
            )
        elapsed = (today_d - last_d).days
        threshold = UNIT_DAYS[unit]
        if elapsed >= threshold:
            overdue.append((unit, elapsed - threshold))
        else:
            upcoming.append((unit, threshold - elapsed))

    # 12월·1월 연간 특례 — annual 정보 없으면 가상 overdue 로 취급
    in_annual_window = today_d.month in (12, 1)
    annual_missing = last_dates.get("annual") in (None, "")
    if in_annual_window and annual_missing:
        overdue.append(("annual", 0))

    if overdue:
        # 가장 큰 단위 우선
        priority = {"annual": 0, "quarterly": 1, "monthly": 2, "weekly": 3}
        overdue.sort(key=lambda x: priority[x[0]])
        unit, over_d = overdue[0]
        if unit == "annual" and annual_missing and in_annual_window:
            reason = (
                f"현재 월이 {today_d.month}월 (연간 점검 권장 윈도우 12월·1월). "
                "직전 연간 점검 기록 없음."
            )
        else:
            reason = (
                f"{UNIT_LABEL_KO[unit]} 도래 (직전 점검 후 "
                f"{UNIT_DAYS[unit] + over_d}일 경과, "
                f"임계 {UNIT_DAYS[unit]}일 + 초과 {over_d}일)"
            )
        return Recommendation(
            recommended_unit=unit,
            reason=reason,
            overdue_units=overdue,
            upcoming_units=upcoming,
        )

    if not upcoming:
        return Recommendation(
            recommended_unit=None,
            reason=(
                "직전 점검 일자 정보 없음. 사용자에게 직접 단위 선택 요청."
            ),
            overdue_units=[],
            upcoming_units=[],
        )

    return Recommendation(
        recommended_unit=None,
        reason=(
            "도래한 점검 없음. 가장 가까운 다음 점검까지 잔여 일수 안내."
        ),
        overdue_units=[],
        upcoming_units=sorted(upcoming, key=lambda x: x[1]),
    )


# ============================================================================
# 8. 빗나감 패턴 감지 (Clear 2018 Never miss twice + 본 스킬 3회 룰)
# ============================================================================

@dataclass
class MissPatternVerdict:
    consecutive_misses: int
    triggers_4_questions: bool   # 3회 연속 → True
    triggers_never_miss_twice: bool  # 2회 연속 → True
    explanation: str
    next_action: str


def detect_miss_pattern(miss_log: List[bool]) -> MissPatternVerdict:
    """주간 점검 단위의 빗나감 시계열을 분석.

    Args:
      miss_log: 과거→현재 시간 순. True = 미달/빗나감, False = 정상.

    규칙:
      - 마지막 부분의 연속 True 카운트
      - ≥ 2 → Never miss twice (Clear 2018 Ch.16) 발동
      - ≥ 3 → 빗나감 패턴 4가지 질문 가동 (SKILL.md "빗나감 패턴 분석")
    """
    if not isinstance(miss_log, list):
        raise TypeError("miss_log must be a list of bool")
    if not all(isinstance(x, bool) for x in miss_log):
        raise TypeError("miss_log entries must be bool")

    consecutive = 0
    for v in reversed(miss_log):
        if v:
            consecutive += 1
        else:
            break

    if consecutive >= 3:
        return MissPatternVerdict(
            consecutive_misses=consecutive,
            triggers_4_questions=True,
            triggers_never_miss_twice=True,
            explanation=(
                f"{consecutive}회 연속 빗나감 — SKILL.md 빗나감 패턴 분석 4가지 질문 가동"
            ),
            next_action=(
                "4가지 질문 순서대로: ①목표 크기 ②트리거·습관 ③비전 변화 ④외부 변수"
            ),
        )
    if consecutive == 2:
        return MissPatternVerdict(
            consecutive_misses=2,
            triggers_4_questions=False,
            triggers_never_miss_twice=True,
            explanation=(
                "2회 연속 빗나감 — Clear 2018 Ch.16 Never Miss Twice 경고선"
            ),
            next_action=(
                "다음 주기 즉시 회복 + 시스템 점검 시작 (한 번 더 빠지면 4질문 가동)"
            ),
        )
    if consecutive == 1:
        return MissPatternVerdict(
            consecutive_misses=1,
            triggers_4_questions=False,
            triggers_never_miss_twice=False,
            explanation=(
                'Clear 2018 Ch.16: "Missing once is an accident." 정상 분산'
            ),
            next_action="다음 주기 회복",
        )
    return MissPatternVerdict(
        consecutive_misses=0,
        triggers_4_questions=False,
        triggers_never_miss_twice=False,
        explanation="연속 빗나감 없음",
        next_action="현 시스템 유지",
    )


# ============================================================================
# 9. 캘린더 계산 — 매월 마지막 금요일·첫 일요일 등
# ============================================================================

WEEKDAY_KO = ["월", "화", "수", "목", "금", "토", "일"]


def last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """매월 마지막 특정 요일 (0=월요일 ... 6=일요일)."""
    if not 0 <= weekday <= 6:
        raise ValueError("weekday must be 0..6 (Mon..Sun)")
    last_day = calendar.monthrange(year, month)[1]
    d = date(year, month, last_day)
    while d.weekday() != weekday:
        d -= timedelta(days=1)
    return d


def first_weekday_of_month(year: int, month: int, weekday: int) -> date:
    """매월 첫 특정 요일."""
    if not 0 <= weekday <= 6:
        raise ValueError("weekday must be 0..6 (Mon..Sun)")
    d = date(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


def last_friday_of_month(year: int, month: int) -> date:
    """매월 마지막 금요일 (월간 점검 권장일)."""
    return last_weekday_of_month(year, month, weekday=4)


def first_sunday_of_month(year: int, month: int) -> date:
    """매월 첫 일요일 (월간 점검 대체 권장일)."""
    return first_weekday_of_month(year, month, weekday=6)


def quarter_end_date(year: int, q: int) -> date:
    """분기 마지막 날짜 (Q1=3/31, Q2=6/30, Q3=9/30, Q4=12/31)."""
    if q not in (1, 2, 3, 4):
        raise ValueError(f"q must be 1..4, got {q}")
    end_months = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    m, d = end_months[q]
    return date(year, m, d)


def last_week_monday_of_quarter(year: int, q: int) -> date:
    """분기 마지막 주의 월요일 (분기 점검 권장 시작일)."""
    end = quarter_end_date(year, q)
    # end가 속한 ISO 주의 월요일
    return end - timedelta(days=end.weekday())


def is_in_annual_window(d: date) -> bool:
    """12월·1월 연간 점검 윈도우 여부."""
    return d.month in (12, 1)


def quarter_of(d: date) -> int:
    """date 가 속한 분기 (1..4)."""
    return (d.month - 1) // 3 + 1


def iso_week_label(d: date) -> str:
    """주차 라벨: 'YYYY-MM-DD' + ISO weekday (월=1 ... 일=7)."""
    iso_year, iso_week, iso_dow = d.isocalendar()
    return f"{fmt(d)} ({WEEKDAY_KO[d.weekday()]}, {iso_year}-W{iso_week:02d})"


# ============================================================================
# 10. 완수율 계산
# ============================================================================

def completion_rate(completed: int, planned: int) -> float:
    """완수율(0~100) — 0÷0 은 0.0 으로."""
    if completed < 0 or planned < 0:
        raise ValueError("counts must be non-negative")
    if completed > planned:
        raise ValueError(
            f"completed ({completed}) > planned ({planned}) — 불가능"
        )
    if planned == 0:
        return 0.0
    return round(100.0 * completed / planned, 2)


# ============================================================================
# 11. 양식 결정론 렌더링
# ============================================================================

def render_weekly_form(check_date: date, week_label: Optional[str] = None) -> str:
    label = week_label or iso_week_label(check_date)
    return f"""## 주간 점검 — {label}

### 지난 주 완수 현황
- 계획한 행동 N개 중 ___개 완수 (___%)
- 완수: ✓ ___, ___, ___
- 미완수: ✗ ___, ___ (이유: ___)

### 한 줄 회고
- 가장 잘 된 일:
- 가장 막힌 일:
- 패턴 신호:

### 다음 주 핵심 3개
1. ...
2. ...
3. ...

### 빠진 날 대응 (Never miss twice — Clear, *Atomic Habits* Ch.16)
- 빠진 행동을 *내일·다음 주*에 어떻게 회복할까?

{next_check_schedule_block(check_date, "weekly")}
""".strip() + "\n"


def render_monthly_form(check_date: date) -> str:
    yymm = check_date.strftime("%Y-%m")
    return f"""## 월간 점검 — {yymm}

### 마일스톤 달성도
| STG | 마일스톤 | 달성 | 평가 |
|-----|---------|------|------|
| ... | ... | ✓/△/✗ | ... |

### KPI 추이
- KPI A: 전월 → 이달 → 변화 (절대값·증감률)
- KPI B: ...

### 4주 합산 행동 완수율
___%  ← scripts/progress_review.py completion_rate 로 산출

### 패턴 식별
- 잘 되는 패턴 (요일·시간·환경):
- 막히는 패턴:
- 시스템 개선 가능점:

### 다음 달 조정 — Stop/Start/Continue (Derby & Larsen 2006 *Agile Retrospectives* 표준화)
- **Stop**: 그만 둘 행동·STG (성과에 기여 안 함)
- **Start**: 새로 시작할 것 (이번 달에 빠진 자리)
- **Continue**: 그대로 진행 (효과 입증된 것)

{next_check_schedule_block(check_date, "monthly")}
""".strip() + "\n"


def render_quarterly_form(check_date: date) -> str:
    yyqq = f"{check_date.year} Q{(check_date.month - 1) // 3 + 1}"
    return f"""## 분기 점검 — {yyqq}

### STG 진척률
| STG | 목표 | 실제 | 달성률 | 평가 |
|-----|------|------|-------|------|
| ... | ... | ... | __% | ✓/△/✗ |

**평가 기준** (SMART 의 *Measurable* — Doran 1981; 본 스킬 categorize_achievement 호출):
- ✓ 달성률 ≥ 80%  (목표 거의 충족)
- △ 50% ≤ 달성률 < 80% (부분 달성)
- ✗ 달성률 < 50% (대폭 미달)

### OKR 점수 (Doerr 2018; categorize_okr 호출)
- KR1: 0.0 ~ 1.0
- KR2: ...
- 평균: ___
- **해석 (Doerr 2018 Google standard)**:
  - 0.0-0.3 진척 없음 (red)
  - 0.4-0.6 진척 있으나 미완 (yellow)
  - 0.7-1.0 성공 / 큰 진척 (green) — 0.7이 stretch goal 이상적 목표치

### Stop / Start / Continue 회고 (Derby & Larsen 2006)
- **Stop**: 더 이상 의미 없는 행동/STG
- **Start**: 새로 시작할 STG
- **Continue**: 그대로 가는 STG

### Pivot 결정 점검 (Ries 2011; pivot_trigger_check 호출)
> "A pivot is a structured course correction designed to test a new fundamental
> hypothesis about the product, strategy, and engine of growth." — Ries 2011 ch.8

- 분기 핵심 KPI 달성률 ≤ 50% + 원인 카테고리 (hypothesis/execution/external/unknown)
  → pivot_trigger_check 로 판정
- 환경 변화로 LTG 자체 점검 필요한가?
- 비전 핵심은 그대로인가? (변했다면 vision-clarity-coaching 재실행)

### 다음 분기 STG 3~5개
1. ...
2. ...

### 한 문단 회고
[지난 분기 가장 큰 발견·교훈]

{next_check_schedule_block(check_date, "quarterly")}
""".strip() + "\n"


def render_annual_form(check_date: date) -> str:
    yyyy = check_date.year
    return f"""## 연간 점검 — {yyyy}

### LTG 궤도 점검
| LTG | 5년 목표 | 1년 진척 | 5년 궤도 |
|-----|---------|---------|---------|
| ... | ... | ... | On track / Behind / Ahead / Pivot |

### 4분기 통합
- 분기별 핵심 성취 4선
- 분기별 핵심 학습 4선

### 비전 핵심 재확인
- 작년 비전 한 문장 vs 올해 비전 한 문장
- 변경됐다면 *왜*?
- 그대로라면 더 깊이 들어간 부분은?

### 다음 해 LTG·STG 재설정
- LTG 조정 (필요 시)
- 다음 해 1년 STG 4~6개

### 5년 궤도 재검토
- 5년 후 도달 가능한가?
- 가속할 부분 / 늦출 부분
- 새 변수 (개인·가족·시장·미래)

### 한 해 일기 한 페이지
[감사·성장·아쉬움·내년 다짐]

{next_check_schedule_block(check_date, "annual")}
""".strip() + "\n"


def render_oneoff_form(label: str) -> str:
    return f"""## 단발 회고 — {label}

### 회고 대상
- 무엇에 대한 회고인가? (프로젝트·이벤트·한 해·전환점)
- 기간: [시작~종료]
- 원래 목표:

### 결과 vs 목표
- 달성:
- 미달:
- 예상 못한 부산물:

### Stop / Start / Continue (Derby & Larsen 2006)
- Stop:
- Start:
- Continue:

### 가장 큰 학습 한 줄
-

### 다음 대상으로 이어갈 것 (반복 주기 없는 단발 회고이므로 *필수* 항목)
-

### (신년 회고일 경우 추가) 비전 재선언
- 작년 비전 한 문장:
- 올해 비전 한 문장:
- 변경 이유 / 깊어진 지점:
""".strip() + "\n"


# ============================================================================
# 12. 양식 필수 항목 검증 (사용자 입력 마크다운에서 빈칸/Placeholder 잔존 검사)
# ============================================================================

PLACEHOLDER_PATTERNS = [
    re.compile(r"\.\.\."),
    re.compile(r"___"),
    re.compile(r"\[YYYY-MM-DD\]"),
    re.compile(r"\[YYYY\]"),
    re.compile(r"\[YYYY-MM\]"),
    re.compile(r"\[YYYY Q_\]"),
]


@dataclass
class FormCompleteness:
    total_placeholders: int
    unfilled_count: int
    completion_pct: float
    unfilled_lines: List[Tuple[int, str]]


def validate_form_completion(filled_text: str) -> FormCompleteness:
    """양식 마크다운에 placeholder 가 얼마나 채워졌는지 검증."""
    if not isinstance(filled_text, str):
        raise TypeError("filled_text must be str")
    lines = filled_text.splitlines()
    unfilled: List[Tuple[int, str]] = []
    total = 0
    for idx, line in enumerate(lines, start=1):
        for pat in PLACEHOLDER_PATTERNS:
            if pat.search(line):
                unfilled.append((idx, line))
                total += 1
                break
    return FormCompleteness(
        total_placeholders=total,
        unfilled_count=total,
        completion_pct=0.0 if total == 0 else 0.0,
        unfilled_lines=unfilled,
    )


# ============================================================================
# 13. 할루시네이션 차단 — 출처 없는 통계·기준 단언 차단
# ============================================================================

_STAT_KEYWORDS = r"(?:성공률|달성률|완수율|업계 평균|산업 평균|업종 평균|평균치|업계 표준|산업 표준)"
FORBIDDEN_PATTERNS = [
    # 임의 통계 단언 — 양방향: %숫자 + 키워드 OR 키워드 + %숫자
    re.compile(r"(\d{1,3}\.?\d*)\s*%.{0,40}" + _STAT_KEYWORDS),
    re.compile(_STAT_KEYWORDS + r".{0,40}(\d{1,3}\.?\d*)\s*%"),
    # "평균 N주/N개월/N일 + 정착/달성" — 학술 출처 없는 임의 정착 기간
    re.compile(r"평균.{0,10}(\d+)\s*(?:주|개월|일).{0,15}(?:정착|달성)"),
    # 21일 신화
    re.compile(r"21일.{0,10}(?:습관|정착|완성)"),
    # 66일 신화도 출처 없으면 차단 (Lally 2010 인용 없이 단언 시)
    re.compile(r"(?<!Lally )(?<!Lally\s)66일.{0,15}(?:습관|정착)(?!.{0,40}Lally)"),
    # 출처 없는 "연구에 따르면" "통계에 의하면" — 80자 내 연도(4자리) 없으면 차단
    re.compile(r"(?:연구에 따르면|통계에 의하면|학자들은|전문가들은)(?!.{0,80}\d{4})"),
    # 출처 없는 "~에서 발표한" + 숫자 — 발표 기관 명시 없는 통계
    re.compile(r"(?:발표한|발표된|조사된)\s.{0,30}\d{1,3}\s*%(?!.{0,40}\(.{0,40}\d{4})"),
    # 출처 없는 모집단 단정 통계 — "대부분/대다수/많은 사람 ... N%" 형태
    re.compile(r"(?:대부분|많은 사람|많은 사람들|대다수|소수|일부|일반인)(?:의|이|가|들이|들의)?.{0,30}\d{1,3}\s*%(?!.{0,60}\d{4})"),
    # 출처 없는 행위 통계 — "N% ... 성공/실패/달성/포기/완수" + 4자리 연도 부재
    re.compile(r"\d{1,3}\s*%.{0,30}(?:성공한다|실패한다|달성한다|포기한다|완수한다|성공합니다|실패합니다|성공한|실패한|성공하|실패하)(?!.{0,80}\d{4})"),
]


def check_forbidden_statements(content: str) -> Dict[str, Any]:
    """출처 없는 임의 통계·"21일 신화" 등 차단."""
    hits = []
    for pat in FORBIDDEN_PATTERNS:
        for m in pat.finditer(content):
            hits.append({"pattern": pat.pattern, "snippet": m.group(0)})
    return {
        "passed": len(hits) == 0,
        "violations": hits,
    }


# ============================================================================
# 14. CLI
# ============================================================================

def _cli():
    parser = argparse.ArgumentParser(
        prog="progress_review.py",
        description="vision-progress-review 결정론 엔진",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("citation", help="출처 인용 출력")
    p.add_argument("key", choices=sorted(PROGRESS_SOURCES.keys()))

    sub.add_parser("citations-all", help="모든 출처 출력")

    p = sub.add_parser("next-check", help="다음 점검 일정 계산")
    p.add_argument("--last", required=True, help="마지막 점검일 YYYY-MM-DD")
    p.add_argument("--unit", required=True, choices=sorted(UNIT_DAYS.keys()))

    p = sub.add_parser("schedule-block", help="양식 다음 점검 일정 블록")
    p.add_argument("--check-date", required=True, help="현재 점검일 YYYY-MM-DD")
    p.add_argument("--unit", required=True, choices=sorted(UNIT_DAYS.keys()))

    p = sub.add_parser("achievement", help="달성률 분류")
    p.add_argument("--rate", required=True, type=float)

    p = sub.add_parser("okr", help="OKR 점수 분류")
    p.add_argument("--score", required=True, type=float)

    p = sub.add_parser("pivot", help="Pivot 트리거 판정")
    p.add_argument("--kpi", required=True, type=float)
    p.add_argument("--cause", required=True,
                   choices=["hypothesis", "execution", "external", "unknown"])

    p = sub.add_parser("recommend", help="자동 추천 단위")
    p.add_argument("--last", required=True,
                   help='JSON: {"weekly":"YYYY-MM-DD","monthly":...}')
    p.add_argument("--today", default=None)

    p = sub.add_parser("miss-pattern", help="빗나감 패턴 감지")
    p.add_argument("--log", required=True,
                   help='JSON 배열: [false,true,true] (과거→현재)')

    p = sub.add_parser("last-friday", help="매월 마지막 금요일")
    p.add_argument("--year", required=True, type=int)
    p.add_argument("--month", required=True, type=int)

    p = sub.add_parser("first-sunday", help="매월 첫 일요일")
    p.add_argument("--year", required=True, type=int)
    p.add_argument("--month", required=True, type=int)

    p = sub.add_parser("quarter-end", help="분기 마지막 날짜")
    p.add_argument("--year", required=True, type=int)
    p.add_argument("--quarter", required=True, type=int, choices=[1, 2, 3, 4])

    p = sub.add_parser("quarter-last-week-monday", help="분기 마지막 주 월요일")
    p.add_argument("--year", required=True, type=int)
    p.add_argument("--quarter", required=True, type=int, choices=[1, 2, 3, 4])

    p = sub.add_parser("annual-window", help="12월·1월 연간 윈도우 여부")
    p.add_argument("--date", required=True)

    p = sub.add_parser("completion-rate", help="완수율 계산")
    p.add_argument("--completed", required=True, type=int)
    p.add_argument("--planned", required=True, type=int)

    p = sub.add_parser("render-form", help="양식 결정론 출력")
    p.add_argument("--unit", required=True,
                   choices=["weekly", "monthly", "quarterly", "annual", "oneoff"])
    p.add_argument("--date", default=None, help="YYYY-MM-DD (oneoff 외 필수)")
    p.add_argument("--label", default="회고 대상", help="oneoff 라벨")

    p = sub.add_parser("validate-form", help="양식 placeholder 검증")
    p.add_argument("--file", required=True)

    p = sub.add_parser("check-forbidden", help="할루시네이션 차단 검사")
    p.add_argument("--file", required=True)

    args = parser.parse_args()

    if args.cmd == "citation":
        print(format_citation(args.key))
    elif args.cmd == "citations-all":
        print(all_citations_block())
    elif args.cmd == "next-check":
        d = next_check_date(parse_date(args.last), args.unit)
        print(fmt(d))
    elif args.cmd == "schedule-block":
        print(next_check_schedule_block(parse_date(args.check_date), args.unit))
    elif args.cmd == "achievement":
        v = categorize_achievement(args.rate)
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
    elif args.cmd == "okr":
        v = categorize_okr(args.score)
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
    elif args.cmd == "pivot":
        v = pivot_trigger_check(args.kpi, args.cause)
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
    elif args.cmd == "recommend":
        last = json.loads(args.last)
        v = auto_recommend(last, args.today)
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
    elif args.cmd == "miss-pattern":
        log = json.loads(args.log)
        v = detect_miss_pattern(log)
        print(json.dumps(asdict(v), ensure_ascii=False, indent=2))
    elif args.cmd == "last-friday":
        print(fmt(last_friday_of_month(args.year, args.month)))
    elif args.cmd == "first-sunday":
        print(fmt(first_sunday_of_month(args.year, args.month)))
    elif args.cmd == "quarter-end":
        print(fmt(quarter_end_date(args.year, args.quarter)))
    elif args.cmd == "quarter-last-week-monday":
        print(fmt(last_week_monday_of_quarter(args.year, args.quarter)))
    elif args.cmd == "annual-window":
        print(json.dumps({"in_window": is_in_annual_window(parse_date(args.date))}))
    elif args.cmd == "completion-rate":
        print(completion_rate(args.completed, args.planned))
    elif args.cmd == "render-form":
        if args.unit == "oneoff":
            print(render_oneoff_form(args.label))
        else:
            if not args.date:
                raise SystemExit("--date required for non-oneoff units")
            d = parse_date(args.date)
            renderers = {
                "weekly": render_weekly_form,
                "monthly": render_monthly_form,
                "quarterly": render_quarterly_form,
                "annual": render_annual_form,
            }
            print(renderers[args.unit](d))
    elif args.cmd == "validate-form":
        with open(args.file, encoding="utf-8") as f:
            txt = f.read()
        v = validate_form_completion(txt)
        out = {
            "total_placeholders": v.total_placeholders,
            "unfilled_count": v.unfilled_count,
            "unfilled_lines": v.unfilled_lines[:20],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.cmd == "check-forbidden":
        with open(args.file, encoding="utf-8") as f:
            txt = f.read()
        v = check_forbidden_statements(txt)
        print(json.dumps(v, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
