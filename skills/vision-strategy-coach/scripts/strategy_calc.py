"""vision-strategy-coach 결정론 모듈

LLM 자연어 추론으로는 할루시네이션을 구조적으로 차단할 수 없는 단계들을
결정론적 함수로 환원한다. SKILL.md의 작업 흐름은 이 모듈의 함수들을
강제 호출하도록 설계되어 있다.

환원 대상:
  1. SMART 5요소 검증 (validate_smart_goal)
  2. LTG 개수 범위 검증 (validate_ltg_count: 2~4)
  3. STG 개수 범위 검증 (validate_stg_count: 3~5, 분기당 ≤3)
  4. 점검 일정 날짜 계산 (calculate_review_schedule)
  5. Pivot 트리거 (check_pivot_trigger: 분기 60% 미달 → STG 재설계)
  6. 학술 인용 정확성 조회 (lookup_citation)
  7. vision-readiness Q08 원문 일치 검증 (verify_q08_canonical)
  8. 사용자 진술 외 고유명사 필터링 (filter_unsourced_entities)
  9. vision-readiness 점수 분기 처리 (readiness_branch)
  10. Gollwitzer Implementation Intention 형식 검증 (validate_first_step)
  11. 호칭 일관성 검증 (validate_honorific_consistency)
  12. 입력 유형 분류 (classify_input_mode: A~E)
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

# ────────────────────────────────────────────────────────────────
# 정본 데이터 로드
# ────────────────────────────────────────────────────────────────
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_CITATIONS_PATH = _DATA_DIR / "citations.json"


def _load_citations() -> dict[str, Any]:
    with _CITATIONS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


CITATIONS = _load_citations()


# ────────────────────────────────────────────────────────────────
# 결과 객체
# ────────────────────────────────────────────────────────────────
@dataclass
class ValidationResult:
    ok: bool
    reasons: list[str] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "reasons": list(self.reasons), "detail": dict(self.detail)}


# ────────────────────────────────────────────────────────────────
# 1) SMART 5요소 검증
# ────────────────────────────────────────────────────────────────
_NUM_RE = re.compile(r"\d+(?:[.,]\d+)?")
_KOR_NUM_UNIT_RE = re.compile(
    r"\d+\s*(?:권|편|회|개|명|건|시간|분|일|주|개월|달|월|분기|년|연|차|%|퍼센트|원|만|억)"
)
# 시간 기한: "YYYY-MM-DD", "YYYY년", "○○년 ○월", "20XX년", "내년", "다음해", "Q1~Q4", "by 2030"
_TIME_BOUND_RE = re.compile(
    r"(?:"
    r"\d{4}\s*년"  # 2030년
    r"|\d{4}-\d{1,2}(?:-\d{1,2})?"  # 2030-12-31
    r"|Q[1-4]"  # Q1
    r"|by\s+\d{4}"  # by 2030
    r"|\d+\s*(?:개월|년|주|일|분기)\s*내"  # 6개월 내
    r"|이번\s*(?:분기|연도|해|반기)"
    r"|올해\s*말|연말|월말|주말|상반기|하반기|다음해|내년"
    r")",
    re.IGNORECASE,
)
# 한국어 종결어미 휴리스틱 — 어절이 '다'로 끝나는 한글 어절을 동사·형용사로 인식.
# 한국어 동사는 명시 화이트리스트로 다 잡기 어려우므로(돌본다·섬긴다·안착시킨다 등),
# 어말 종결어미 -다 패턴으로 폭넓게 인정한다.
_KOR_VERB_ENDING_RE = re.compile(r"[가-힣]{1,5}다(?=[\s\.,!?)\]]|$)")


# 동사 패턴 — 한국어/영어 동시 지원.
# 주의: alternation 사이에 빈 매개(||)가 들어가면 정규식이 모든 위치에서
# 길이 0 매칭을 반환해 동사 존재 판정이 항상 True가 된다. 매개 결합 시
# 양 끝의 파이프를 정리한다.
_ACTION_VERB_RE = re.compile(
    r"(?:한다|하기|하다|완성|달성|작성|출판|출간|강의|구축|운영|"
    r"개설|개발|런칭|진행|학습|훈련|마치|마치다|마무리|이루|이루다|"
    r"이룰|성취|확보|확립|정착|시작|개시|마련|돌입|도달|확장|"
    r"늘리|증가|향상|개선|배포|제작|기록|수립|체결|제공|진행한다"
    r"|publish(?:es|ed|ing)?|write|writes|wrote|written|build|builds|built"
    r"|launch(?:es|ed|ing)?|achieve(?:s|d)?|reach(?:es|ed|ing)?"
    r"|complete(?:s|d)?|develop(?:s|ed|ing)?|create(?:s|d)?|deliver(?:s|ed|ing)?"
    r"|lead(?:s|ing)?|led|train(?:s|ed|ing)?|teach(?:es|ing)?|taught"
    r"|educate(?:s|d)?|mentor(?:s|ed|ing)?|coach(?:es|ed|ing)?"
    r"|establish(?:es|ed|ing)?|found(?:s|ed|ing)?|open(?:s|ed|ing)?|run(?:s|ning)?"
    r"|manage(?:s|d|ing)?|increase(?:s|d)?|reduce(?:s|d)?|improve(?:s|d)?"
    r"|expand(?:s|ed|ing)?|grow(?:s|ing)?|grew|grown|finish(?:es|ed|ing)?"
    r"|start(?:s|ed|ing)?|attend(?:s|ed|ing)?|host(?:s|ed|ing)?|present(?:s|ed|ing)?"
    r"|save(?:s|d)?|earn(?:s|ed|ing)?|hire(?:s|d|ing)?"
    r"|speak(?:s|ing)?|spoke|spoken|prepare(?:s|d)?|read(?:s|ing)?|study|studies|studied"
    r")",
    re.IGNORECASE,
)


def validate_smart_goal(text: str, *, modern: bool = True) -> ValidationResult:
    """LTG/STG 한 문장이 SMART 5요소를 만족하는지 결정론적 휴리스틱으로 검증.

    modern=True: Specific·Measurable·Achievable·Relevant·Time-bound (현대 변형)
    modern=False: Specific·Measurable·Assignable·Realistic·Time-related (Doran 1981 원본)

    완벽한 자연어 이해는 LLM에 위임하지 않고, 결정론적 패턴으로
    *최소 충족 신호*를 검증한다. 신호가 약하면 reasons에 기록.
    """
    reasons: list[str] = []
    if not isinstance(text, str) or not text.strip():
        return ValidationResult(False, ["empty"], {})

    t = text.strip()

    # Specific: 길이 ≥ 10자(한글 기준) + 동사 존재
    # 동사 존재는 (1) 화이트리스트 매칭 또는 (2) 한국어 -다 종결어미 매칭으로 인정.
    has_verb = bool(_ACTION_VERB_RE.search(t)) or bool(_KOR_VERB_ENDING_RE.search(t))
    is_specific = len(t) >= 10 and has_verb
    if not is_specific:
        if len(t) < 10:
            reasons.append("specific:too_short(<10chars)")
        if not has_verb:
            reasons.append("specific:no_action_verb")

    # Measurable: 수치 또는 수치+단위 존재
    has_number = bool(_NUM_RE.search(t))
    has_kor_unit = bool(_KOR_NUM_UNIT_RE.search(t))
    is_measurable = has_number or has_kor_unit
    if not is_measurable:
        reasons.append("measurable:no_quantifier")

    # Time-bound: 기한 표현 존재
    is_timebound = bool(_TIME_BOUND_RE.search(t))
    if not is_timebound:
        reasons.append("time:no_deadline")

    # Achievable/Realistic 및 Relevant 는 사용자 비전 핵심과의 정합성 판단이
    # 필요하므로 SKILL.md에서 LLM과 사용자 합의로 처리한다. 본 함수는
    # 객관적으로 검증 가능한 S·M·T 세 축을 강제한다.
    smt_ok = is_specific and is_measurable and is_timebound

    detail = {
        "specific": is_specific,
        "measurable": is_measurable,
        "time_bound": is_timebound,
        "variant": "modern" if modern else "doran1981_original",
        "elements_definition": (
            CITATIONS["SMART"]["modern_elements"] if modern else CITATIONS["SMART"]["original_elements"]
        ),
    }
    return ValidationResult(smt_ok, reasons, detail)


# ────────────────────────────────────────────────────────────────
# 2)·3) 개수 범위 검증
# ────────────────────────────────────────────────────────────────
def validate_ltg_count(goals: list[str]) -> ValidationResult:
    """LTG는 2~4개여야 한다. 너무 많으면 분산, 너무 적으면 협소."""
    n = len(goals) if isinstance(goals, list) else -1
    ok = 2 <= n <= 4
    reasons = [] if ok else [f"ltg_count:{n}(expected 2-4)"]
    return ValidationResult(ok, reasons, {"count": n, "min": 2, "max": 4})


def validate_stg_count(stgs_per_ltg: list[list[str]]) -> ValidationResult:
    """각 LTG당 STG는 3~5개. 분기 STG는 분기당 3개 이내."""
    if not isinstance(stgs_per_ltg, list):
        return ValidationResult(False, ["invalid_type"], {})

    reasons: list[str] = []
    detail: dict[str, Any] = {"per_ltg_counts": []}
    overall_ok = True
    for idx, stgs in enumerate(stgs_per_ltg):
        cnt = len(stgs) if isinstance(stgs, list) else -1
        detail["per_ltg_counts"].append(cnt)
        if not (3 <= cnt <= 5):
            overall_ok = False
            reasons.append(f"ltg{idx+1}_stg_count:{cnt}(expected 3-5)")
    return ValidationResult(overall_ok, reasons, detail)


def validate_quarter_focus(quarter_stg_counts: list[int]) -> ValidationResult:
    """각 분기에 핵심 STG는 3개 이내. quarter_stg_counts = [Q1, Q2, Q3, Q4]."""
    if not isinstance(quarter_stg_counts, list) or len(quarter_stg_counts) != 4:
        return ValidationResult(False, ["quarters_must_be_4"], {})
    reasons = []
    for i, c in enumerate(quarter_stg_counts):
        if c > 3:
            reasons.append(f"Q{i+1}:{c}>3")
    return ValidationResult(not reasons, reasons, {"quarters": list(quarter_stg_counts)})


# ────────────────────────────────────────────────────────────────
# 4) 점검 일정 날짜 계산
# ────────────────────────────────────────────────────────────────
def _parse_date(value: str | date | datetime) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(f"date_format_invalid:{value}(expected YYYY-MM-DD)") from e
    raise TypeError(f"unsupported_date_type:{type(value).__name__}")


def calculate_review_schedule(start: str | date | datetime, *, birthday: str | None = None) -> dict[str, str]:
    """주간·월간·분기·연간 점검 일정의 다음 발생일을 계산.

    - 주간: 다음 일요일 (start 포함 이후 첫 일요일, start가 일요일이면 7일 뒤)
    - 월간: 이번 달 마지막 금요일 (이미 지났으면 다음 달 마지막 금요일)
    - 분기: 현재 분기 마지막 주의 시작 월요일 (이미 지났으면 다음 분기)
    - 연간: birthday(YYYY-MM-DD) 주어지면 다음 생일 주의 월요일,
            없으면 다음 12월 첫 주 월요일

    모든 계산은 결정론적이며 LLM의 날짜 추정을 차단한다.
    """
    today = _parse_date(start)

    # 주간 — 다음 일요일
    days_to_sunday = (6 - today.weekday()) % 7
    if days_to_sunday == 0:
        days_to_sunday = 7
    next_weekly = today + timedelta(days=days_to_sunday)

    # 월간 — 이번 달 마지막 금요일 (이미 지났으면 다음 달)
    def _last_friday_of(year: int, month: int) -> date:
        if month == 12:
            first_next = date(year + 1, 1, 1)
        else:
            first_next = date(year, month + 1, 1)
        last_day = first_next - timedelta(days=1)
        offset = (last_day.weekday() - 4) % 7  # weekday: Mon=0 .. Fri=4
        return last_day - timedelta(days=offset)

    this_month_last_fri = _last_friday_of(today.year, today.month)
    if this_month_last_fri >= today:
        next_monthly = this_month_last_fri
    else:
        next_y, next_m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        next_monthly = _last_friday_of(next_y, next_m)

    # 분기 — 현재 분기의 마지막 월(3,6,9,12)의 마지막 주 월요일
    quarter_end_month = ((today.month - 1) // 3 + 1) * 3
    quarter_end_year = today.year
    last_fri_q = _last_friday_of(quarter_end_year, quarter_end_month)
    # 마지막 주 월요일: 그 주 금요일에서 4일 빼면 월요일
    q_last_monday = last_fri_q - timedelta(days=4)
    if q_last_monday >= today:
        next_quarterly = q_last_monday
    else:
        # 다음 분기
        if quarter_end_month == 12:
            next_q_end_y, next_q_end_m = quarter_end_year + 1, 3
        else:
            next_q_end_y, next_q_end_m = quarter_end_year, quarter_end_month + 3
        next_quarterly = _last_friday_of(next_q_end_y, next_q_end_m) - timedelta(days=4)

    # 연간
    if birthday:
        bd = _parse_date(birthday)
        cand = date(today.year, bd.month, bd.day) if (bd.month, bd.day) != (2, 29) else date(today.year, 2, 28)
        if cand < today:
            cand_year = today.year + 1
            cand = date(cand_year, bd.month, bd.day) if (bd.month, bd.day) != (2, 29) else date(cand_year, 2, 28)
        # 생일이 속한 주의 월요일
        next_annual = cand - timedelta(days=cand.weekday())
    else:
        # 12월 첫 주 월요일
        dec1 = date(today.year, 12, 1)
        dec_first_monday = dec1 + timedelta(days=(-dec1.weekday()) % 7)
        if dec_first_monday < today:
            dec1n = date(today.year + 1, 12, 1)
            dec_first_monday = dec1n + timedelta(days=(-dec1n.weekday()) % 7)
        next_annual = dec_first_monday

    return {
        "weekly": next_weekly.strftime("%Y-%m-%d"),
        "monthly": next_monthly.strftime("%Y-%m-%d"),
        "quarterly": next_quarterly.strftime("%Y-%m-%d"),
        "annual": next_annual.strftime("%Y-%m-%d"),
    }


# ────────────────────────────────────────────────────────────────
# 5) Pivot 트리거
# ────────────────────────────────────────────────────────────────
def check_pivot_trigger(progress_pct: float, *, scope: str = "quarterly") -> dict[str, Any]:
    """진척률에 따른 Pivot 트리거 결정.

    분기(quarterly):
      - ≥80%: on_track (권장 기준값)
      - 60~80% 미만: caution (재조정 검토)
      - <60%: pivot_required (STG 재설계)

    연간(annual): LTG 궤도 이탈 여부 판단 권유. <60%면 LTG 재설정 권고.
    """
    if not isinstance(progress_pct, (int, float)):
        raise TypeError("progress_pct_must_be_numeric")
    if not 0 <= progress_pct <= 100:
        raise ValueError(f"progress_pct_out_of_range:{progress_pct}(expected 0-100)")
    if scope not in ("quarterly", "annual"):
        raise ValueError(f"scope_invalid:{scope}")

    if progress_pct >= 80:
        status = "on_track"
        action = "유지 — 다음 주기 진행"
    elif progress_pct >= 60:
        status = "caution"
        action = "재조정 검토 — STG 일부 보강 또는 일정 조정"
    else:
        status = "pivot_required"
        action = "STG 재설계" if scope == "quarterly" else "LTG 재설정"

    return {
        "scope": scope,
        "progress_pct": progress_pct,
        "status": status,
        "action": action,
        "thresholds": {"on_track_min": 80, "caution_min": 60, "pivot_below": 60},
    }


# ────────────────────────────────────────────────────────────────
# 6) 학술 인용 조회
# ────────────────────────────────────────────────────────────────
def lookup_citation(key: str) -> dict[str, Any]:
    """정본 인용 데이터를 조회. 없으면 KeyError."""
    if key not in CITATIONS:
        raise KeyError(f"citation_key_not_found:{key}(available={sorted(k for k in CITATIONS if not k.startswith('_'))})")
    return dict(CITATIONS[key])


def render_citation(key: str) -> str:
    """본문 인용용 정형 문자열을 반환."""
    c = lookup_citation(key)
    return c.get("citation_full", "")


def list_citation_keys() -> list[str]:
    return sorted(k for k in CITATIONS if not k.startswith("_"))


# ────────────────────────────────────────────────────────────────
# 7) Q08 원문 일치 검증
# ────────────────────────────────────────────────────────────────
def verify_q08_canonical(text: str) -> ValidationResult:
    """vision-readiness Q08 원문이 의역·재작성 없이 정확히 인용되었는지 검증."""
    canonical = CITATIONS["VisionReadinessQ08"]["canonical_text_english"]
    if not isinstance(text, str):
        return ValidationResult(False, ["not_string"], {"canonical": canonical})
    # 인용 부호와 공백을 정규화 후 부분 일치 확인
    normalized = re.sub(r"\s+", " ", text.strip().strip('"“”‘’\''))
    contains = canonical.lower() in normalized.lower()
    return ValidationResult(
        contains,
        [] if contains else ["q08_canonical_text_missing_or_paraphrased"],
        {"canonical": canonical, "normalized_input": normalized},
    )


# ────────────────────────────────────────────────────────────────
# 8) 사용자 진술 외 고유명사 필터
# ────────────────────────────────────────────────────────────────
# 학술 인용으로 허용된 인명·기관명·서명 (citations.json 정본에서 추출)
def _allowed_authority_terms() -> set[str]:
    allowed: set[str] = set()
    for k, v in CITATIONS.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict):
            for fld in ("author", "originator", "popularizer", "title", "venue",
                        "publisher", "originator_title", "originator_publisher", "location"):
                val = v.get(fld)
                if isinstance(val, str):
                    # 합쳐진 어구를 그대로도 허용
                    allowed.add(val.strip())
                    # 작가 구분("X & Y", "X and Y")을 인명별로 분해
                    parts = re.split(r"[,&]| and ", val)
                    for p in parts:
                        p = p.strip()
                        if p:
                            allowed.add(p)
                    # 어구 안 개별 토큰도 단어 매칭에 대비해 추가 (예: "Goal Setting Theory" → Goal, Setting, Theory)
                    for tok in re.findall(r"[A-Z][a-zA-Z\-']{1,}", val):
                        allowed.add(tok)
    # 자주 등장하는 학자명·약어·표제어를 명시 화이트리스트에 추가
    allowed.update({
        "Doran", "Drucker", "Locke", "Latham", "Gollwitzer", "Shewhart", "Deming",
        "Kaplan", "Norton", "Boyatzis", "Senge", "Allen", "Heath",
        "George", "Peter", "Edwin", "Gary", "Walter", "Edwards", "Robert", "David",
        "Richard", "Chip", "Dan", "Plan-Do-Check-Act",
        "SMART", "MBO", "PDCA", "PDSA", "BSC", "KPI", "ICT", "GTD", "STG", "LTG",
        "Balanced", "Scorecard", "Intentional", "Change", "Theory",
        "Implementation", "Intentions", "Goal", "Setting",
        "Management", "Review", "American", "Psychologist",
        "Consulting", "Psychology", "Journal", "Harvard", "Business", "School", "Press",
        "Practice", "Fifth", "Discipline", "Getting", "Things", "Done", "Switch",
        "Doubleday", "Currency", "Penguin", "Books", "Broadway", "Prentice", "Hall",
        "Englewood", "Cliffs", "Boston", "York", "Washington", "Hudson", "Japan",
        "Vision", "Strategy", "Coach", "Step", "First", "Year", "Quarter",
        "Action", "Plan", "Plans", "Plan-Do-Check-Act",
        "Reframing", "Picture", "Follow-Through", "Through", "Big",
        "Q1", "Q2", "Q3", "Q4", "Year-1",
    })
    return allowed


_ALLOWED_AUTHORITY = _allowed_authority_terms()


# 시작·끝은 글자 또는 어포스트로피 — 중간만 하이픈 허용 (트레일링 - 제외)
# 이로써 "LTG-1"에서 "LTG"만 매칭되고 "LTG-"는 매칭되지 않는다.
_PROPER_NOUN_LATIN_RE = re.compile(r"\b[A-Z][a-zA-Z']+(?:-[A-Za-z]+)*\b")
# \b는 ASCII 단어 경계만 인식 — 한글과 숫자 사이에는 매칭 안 됨.
# 따라서 명시적 lookahead/lookbehind로 숫자 외 문자만 차단한다.
_YEAR_RE = re.compile(r"(?<!\d)(?:1[89]\d{2}|20\d{2})(?!\d)")
# 한글 인명 휴리스틱 — 성+이름 2~4자 + 직함(박사·교수·목사·집사·권사·장로·전도사) 또는 "씨"
_KOR_NAME_TITLE_RE = re.compile(r"[가-힣]{2,4}\s*(?:박사|교수|목사|집사|권사|장로|전도사|선생|작가)")
# 한국 기관·회사 휴리스틱 (생략적으로 "○○대학교·○○교회·○○출판사·○○협회")
_KOR_INSTITUTION_RE = re.compile(
    r"[가-힣A-Za-z]{2,}\s*(?:대학교|교회|출판사|북스|출판|협회|연구원|연구소|재단|학회|"
    r"기업|회사|주식회사|법인|센터|병원|학원|아카데미)"
)


def filter_unsourced_entities(coach_text: str, user_text: str) -> dict[str, Any]:
    """코치 산출문에 등장한 고유명사·연도가 사용자 진술 또는 허용된 학술 권위
    목록에 포함되는지 검증. 미포함 항목은 violations로 반환.

    이 함수는 SKILL.md의 출력 직전 체크리스트에서 호출되어,
    LLM 자연어 추론이 채워 넣었을 수 있는 "허락 없는 인명·기관·연도"를
    구조적으로 차단한다.
    """
    if not isinstance(coach_text, str):
        coach_text = ""
    if not isinstance(user_text, str):
        user_text = ""

    user_lower = user_text.lower()

    def _user_has(token: str) -> bool:
        return token.lower() in user_lower

    violations: list[dict[str, str]] = []

    # 1) 영문 고유명사
    for m in _PROPER_NOUN_LATIN_RE.finditer(coach_text):
        tok = m.group()
        if tok in _ALLOWED_AUTHORITY:
            continue
        if _user_has(tok):
            continue
        # 영어 일반 단어 false positive 줄이기 위해 길이 5 이상만 의심 (Doran 등은 위에서 통과)
        if len(tok) < 4:
            continue
        violations.append({"type": "latin_proper_noun", "token": tok})

    # 2) 한글 인명+직함
    for m in _KOR_NAME_TITLE_RE.finditer(coach_text):
        tok = m.group()
        if _user_has(tok):
            continue
        # 박사님 호칭은 정체성 호칭이므로 면제
        if tok.strip() in {"박사님", "박사"}:
            continue
        violations.append({"type": "korean_name_title", "token": tok})

    # 3) 한국 기관
    for m in _KOR_INSTITUTION_RE.finditer(coach_text):
        tok = m.group()
        if _user_has(tok):
            continue
        violations.append({"type": "korean_institution", "token": tok})

    # 4) 연도 — 학술 인용 연도이거나 사용자 진술 연도만 허용
    allowed_years = {str(v.get("year")) for v in CITATIONS.values()
                     if isinstance(v, dict) and v.get("year")}
    allowed_years.update({"1939", "1950", "1950s"})  # PDCA originator/popularizer
    for m in _YEAR_RE.finditer(coach_text):
        y = m.group()
        if y in allowed_years:
            continue
        if y in user_text:
            continue
        violations.append({"type": "year", "token": y})

    return {
        "ok": not violations,
        "violations": violations,
        "violation_count": len(violations),
    }


# ────────────────────────────────────────────────────────────────
# 9) vision-readiness 점수 분기
# ────────────────────────────────────────────────────────────────
def readiness_branch(scores: dict[str, float]) -> dict[str, Any]:
    """vision-readiness 4능력 점수 (Big Picture·Reframing·Strategy·Follow-Through)
    가 주어지면 SKILL.md의 분기 규칙에 따라 코칭 강도를 결정.

    점수 범위: 0~100 가정. 50을 기준점으로 high/low 결정.
    """
    if not isinstance(scores, dict):
        raise TypeError("scores_must_be_dict")

    canonical_keys = {"BigPicture", "Reframing", "Strategy", "FollowThrough"}
    normalized: dict[str, float] = {}
    for k, v in scores.items():
        kc = k.replace(" ", "").replace("-", "").replace("_", "")
        if kc.lower() == "bigpicture":
            normalized["BigPicture"] = float(v)
        elif kc.lower() == "reframing":
            normalized["Reframing"] = float(v)
        elif kc.lower() == "strategy":
            normalized["Strategy"] = float(v)
        elif kc.lower() == "followthrough":
            normalized["FollowThrough"] = float(v)

    missing = canonical_keys - set(normalized.keys())
    if missing:
        return {"ok": False, "missing": sorted(missing)}

    for k, v in normalized.items():
        if not 0 <= v <= 100:
            raise ValueError(f"{k}_out_of_range:{v}(expected 0-100)")

    branch = {
        "BigPicture": "LTG 4개 권유" if normalized["BigPicture"] >= 50 else "LTG 2개로 압축 권유",
        "Reframing": "표준 STG 분해" if normalized["Reframing"] >= 50 else "더 구체적·짧은 STG로 분해",
        "Strategy": "사용자 직접 작성 + 코치 점검" if normalized["Strategy"] >= 50 else "코치가 더 두꺼이 행동 계획 골격 제시",
        "FollowThrough": "분기 점검 위주(자율성 부여)" if normalized["FollowThrough"] >= 50 else "주간 점검을 더 짧고 자주",
    }
    return {"ok": True, "scores": normalized, "branch": branch}


# ────────────────────────────────────────────────────────────────
# 10) Gollwitzer Implementation Intention 형식 검증
# ────────────────────────────────────────────────────────────────
# 형식: "내일 아침 ○시, ○에서, ○를 ○분간 수행" 또는
# "When situation X arises, I will perform response Y"
_IMP_INTENTION_KOR_RE = re.compile(
    r"(?:내일|오늘|이번\s*주|월요일|화요일|수요일|목요일|금요일|토요일|일요일)"
    r".*?\d+\s*(?:시|분|시간)"
    r".*?(?:에서|에)"
)
_IMP_INTENTION_ENG_RE = re.compile(
    r"when\s+.+?\s+arises?,?\s+I\s+will\s+.+",
    re.IGNORECASE,
)


def validate_first_step(text: str) -> ValidationResult:
    """첫 한 걸음이 Gollwitzer 1999의 implementation intention 형식인지 확인."""
    if not isinstance(text, str) or not text.strip():
        return ValidationResult(False, ["empty"], {})

    is_kor = bool(_IMP_INTENTION_KOR_RE.search(text))
    is_eng = bool(_IMP_INTENTION_ENG_RE.search(text))
    ok = is_kor or is_eng
    reasons = []
    if not ok:
        reasons.append("first_step:missing_when_where_what")
    return ValidationResult(
        ok,
        reasons,
        {
            "korean_pattern_match": is_kor,
            "english_pattern_match": is_eng,
            "format_template": CITATIONS["ImplementationIntentions"]["format_template"],
        },
    )


# ────────────────────────────────────────────────────────────────
# 11) 호칭 일관성 검증
# ────────────────────────────────────────────────────────────────
_HONORIFIC_PATTERNS = {
    "박사님": re.compile(r"박사님"),
    "님": re.compile(r"[가-힣A-Za-z]{1,10}님"),
}


def validate_honorific_consistency(text: str, *, declared: str | None = None) -> ValidationResult:
    """선언된 호칭이 본문에서 일관되게 사용되는지 검증.

    declared=None 이면 첫 등장 호칭으로 기준 설정.
    """
    if not isinstance(text, str):
        return ValidationResult(False, ["not_string"], {})

    has_baksanim = bool(_HONORIFIC_PATTERNS["박사님"].search(text))
    nim_matches = set(m.group() for m in _HONORIFIC_PATTERNS["님"].finditer(text))
    nim_matches.discard("박사님")  # 박사님은 별도 분기

    detail = {
        "baksanim_present": has_baksanim,
        "other_nim_honorifics": sorted(nim_matches),
        "declared": declared,
    }

    if declared == "박사님":
        ok = has_baksanim and not nim_matches
        reasons = []
        if not has_baksanim:
            reasons.append("declared_baksanim_but_missing")
        if nim_matches:
            reasons.append(f"declared_baksanim_but_other_nim:{sorted(nim_matches)}")
        return ValidationResult(ok, reasons, detail)

    if declared and declared.endswith("님"):
        ok = declared in text and not has_baksanim
        reasons = []
        if declared not in text:
            reasons.append(f"declared_{declared}_but_missing")
        if has_baksanim:
            reasons.append(f"declared_{declared}_but_baksanim_present")
        return ValidationResult(ok, reasons, detail)

    # declared 미지정 — 단순 일관성: 박사님과 일반 ○○님 혼용 금지
    if has_baksanim and nim_matches:
        return ValidationResult(False, ["honorific_mixed:baksanim+other_nim"], detail)
    return ValidationResult(True, [], detail)


# ────────────────────────────────────────────────────────────────
# 12) 입력 유형 분류 (A·B·C·D·E)
# ────────────────────────────────────────────────────────────────
def classify_input_mode(
    *,
    has_vision_statement: bool,
    has_readiness: bool,
    has_mbti: bool,
    has_values: bool,
    has_strong: bool,
    has_career: bool,
    progress_check_only: bool,
    is_baksanim: bool,
) -> dict[str, Any]:
    """SKILL.md '입력 처리 — 5유형' 분기 결정.

    우선순위: E (박사님) > D (진척 점검 모드) > A (풀 입력) > B (비전만) > C (진단만)
    """
    diagnostics_count = sum([has_readiness, has_mbti, has_values, has_strong])

    if is_baksanim:
        mode = "E"
        description = "박사님 본인 — 진술된 정보 안에서만 결합 코칭"
    elif progress_check_only:
        mode = "D"
        description = "진척 점검 모드 — Step 5만 단독 진행"
    elif has_vision_statement and diagnostics_count >= 3 and has_career:
        mode = "A"
        description = "풀 입력 (이상적) — 5단계 정밀 코칭"
    elif has_vision_statement and not (diagnostics_count or has_career):
        mode = "B"
        description = "비전만 입력 — 명확화 질문 더 많이"
    elif not has_vision_statement and diagnostics_count >= 1:
        mode = "C"
        description = "진단만 입력 — Step 1을 비전 발굴에 더 시간 투자"
    elif has_vision_statement:
        mode = "B"
        description = "비전만 입력 (부분 진단 있어도) — Step 1 명확화 후 가용 진단 결합"
    else:
        mode = "C"
        description = "진단만 입력 — Step 1을 비전 발굴에 더 시간 투자"

    return {
        "mode": mode,
        "description": description,
        "signals": {
            "has_vision_statement": has_vision_statement,
            "diagnostics_count": diagnostics_count,
            "has_career": has_career,
            "progress_check_only": progress_check_only,
            "is_baksanim": is_baksanim,
        },
    }


# ────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────
def _print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def _cli() -> int:
    if len(sys.argv) < 2:
        print("usage: strategy_calc.py <command> [args...]", file=sys.stderr)
        print("commands: smart, ltg_count, stg_count, quarter_focus, schedule, pivot, "
              "citation, citations, q08, filter, readiness, first_step, honorific, mode",
              file=sys.stderr)
        return 2

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "smart":
            result = validate_smart_goal(args[0])
            _print(result.to_dict())
        elif cmd == "ltg_count":
            goals = json.loads(args[0])
            _print(validate_ltg_count(goals).to_dict())
        elif cmd == "stg_count":
            stgs = json.loads(args[0])
            _print(validate_stg_count(stgs).to_dict())
        elif cmd == "quarter_focus":
            qs = json.loads(args[0])
            _print(validate_quarter_focus(qs).to_dict())
        elif cmd == "schedule":
            start = args[0]
            bd = args[1] if len(args) > 1 else None
            _print(calculate_review_schedule(start, birthday=bd))
        elif cmd == "pivot":
            pct = float(args[0])
            scope = args[1] if len(args) > 1 else "quarterly"
            _print(check_pivot_trigger(pct, scope=scope))
        elif cmd == "citation":
            _print(lookup_citation(args[0]))
        elif cmd == "citations":
            _print(list_citation_keys())
        elif cmd == "q08":
            _print(verify_q08_canonical(args[0]).to_dict())
        elif cmd == "filter":
            coach = args[0]
            user = args[1] if len(args) > 1 else ""
            _print(filter_unsourced_entities(coach, user))
        elif cmd == "readiness":
            scores = json.loads(args[0])
            _print(readiness_branch(scores))
        elif cmd == "first_step":
            _print(validate_first_step(args[0]).to_dict())
        elif cmd == "honorific":
            text = args[0]
            declared = args[1] if len(args) > 1 else None
            _print(validate_honorific_consistency(text, declared=declared).to_dict())
        elif cmd == "mode":
            params = json.loads(args[0])
            _print(classify_input_mode(**params))
        else:
            print(f"unknown command: {cmd}", file=sys.stderr)
            return 2
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
