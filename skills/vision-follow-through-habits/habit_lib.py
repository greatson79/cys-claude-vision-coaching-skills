"""
vision-follow-through-habits — 결정론 라이브러리 (Deterministic Engine)

이 파일은 LLM이 자연어로 추론하면 할루시네이션 위험이 있는 작업을
결정론적 함수로 환원한다.

결정론 환원 대상 (LLM 자연어 추론 금지):
1. 학술 출처 조회 (저자·연도·페이지·출판사·ISBN)
2. 5단계 진행 검증 (모든 단계 통과 여부)
3. 30초 시작 단계 룰 기반 검증
4. Habit Stacking 형식 검증
5. 정착 기간 캘린더 계산 (7일·30일·66일·90일)
6. 첫 7일 플랜 결정론 생성
7. 습관 카드 템플릿 결정론 출력
8. Never miss twice 규칙 포함 여부 검증
9. 21일 신화 차단 검증
10. 출처 미인용 통계 단언 차단 검증

작성: 2026-05-17
근거: BJ Fogg (2019), James Clear (2018), Charles Duhigg (2012),
      Lally et al. (2010), Polivy & Herman (1985), Brad Isaac (2007),
      Cooper et al. (2003) — 모두 1차 자료 직접 확인.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# 1. 학술 출처 카탈로그 (결정론 — LLM 자연어 추론 금지)
# ============================================================================

HABIT_SOURCES: Dict[str, Dict[str, Any]] = {
    "fogg_2019": {
        "key": "fogg_2019",
        "author": "B. J. Fogg",
        "year": 2019,
        "title": "Tiny Habits: The Small Changes That Change Everything",
        "publisher": "Houghton Mifflin Harcourt",
        "isbn": "978-0-358-00332-6",
        "core_formula": "B = MAP (Behavior = Motivation × Ability × Prompt)",
        "previous_formula": "B = MAT (Trigger) — 2009 원안. 2019년 책에서 Prompt로 변경.",
        "thirty_sec_rule_quote": (
            'Fogg 2019, ch. 4: "The Tiny Habit must take less than 30 seconds '
            'and require almost no motivation to do."'
        ),
        "tiny_habits_recipe": "After I [ANCHOR MOMENT], I will [TINY BEHAVIOR]. Then I celebrate.",
        "verified": True,
    },
    "clear_2018": {
        "key": "clear_2018",
        "author": "James Clear",
        "year": 2018,
        "title": "Atomic Habits: An Easy & Proven Way to Build Good Habits & Break Bad Ones",
        "publisher": "Avery (Penguin Random House)",
        "isbn": "978-0-7352-1129-2",
        "four_laws": [
            "1st Law — Make it Obvious",
            "2nd Law — Make it Attractive",
            "3rd Law — Make it Easy",
            "4th Law — Make it Satisfying",
        ],
        "habit_stacking_quote": (
            'Clear 2018, ch. 5: "After [CURRENT HABIT], I will [NEW HABIT]." '
            "— Habit Stacking은 Clear가 명명·대중화. 앵커 개념 원안은 Fogg."
        ),
        "one_percent_compounding": "매일 1% 개선 → 1년 37.78배 (1.01^365)",
        "verified": True,
    },
    "duhigg_2012": {
        "key": "duhigg_2012",
        "author": "Charles Duhigg",
        "year": 2012,
        "title": "The Power of Habit: Why We Do What We Do in Life and Business",
        "publisher": "Random House",
        "isbn": "978-1-4000-6928-6",
        "habit_loop": "Cue → Routine → Reward",
        "keystone_habit_quote": (
            'Duhigg 2012, ch. 4: "Keystone habits start a process that, over time, '
            'transforms everything."'
        ),
        "verified": True,
    },
    "lally_2010": {
        "key": "lally_2010",
        "author": "Phillippa Lally, Cornelia H. M. van Jaarsveld, Henry W. W. Potts, Jane Wardle",
        "year": 2010,
        "title": "How are habits formed: Modelling habit formation in the real world",
        "journal": "European Journal of Social Psychology",
        "volume_pages": "40(6): 998–1009",
        "doi": "10.1002/ejsp.674",
        "publisher": "Wiley",
        "median_days": 66,
        "range_days_low": 18,
        "range_days_high": 254,
        "criterion": "95% asymptote of automaticity (Self-Report Habit Index)",
        "n_participants": 96,
        "duration_weeks": 12,
        "verified": True,
    },
    "polivy_herman_1985": {
        "key": "polivy_herman_1985",
        "author": "Janet Polivy, C. Peter Herman",
        "year": 1985,
        "title": "Dieting and binging: A causal analysis",
        "journal": "American Psychologist",
        "volume_pages": "40(2): 193–201",
        "publisher": "American Psychological Association",
        "concept": "Abstinence Violation Effect (이후 'what-the-hell effect'로 통용)",
        "verified": True,
    },
    "isaac_seinfeld_2007": {
        "key": "isaac_seinfeld_2007",
        "author": "Brad Isaac",
        "year": 2007,
        "title": "Jerry Seinfeld's Productivity Secret",
        "source": "Lifehacker (2007-07-24)",
        "url": "https://lifehacker.com/jerry-seinfelds-productivity-secret-281626",
        "concept": "Don't Break the Chain — 종이 캘린더 X 표시 연쇄",
        "attribution_note": (
            "Brad Isaac이 1990년대 후반 Seinfeld와의 만남에서 들었다고 전파. "
            "Seinfeld 본인은 이 방법이 자신의 것이라는 귀속을 부인한 적 있음."
        ),
        "verified": True,
    },
}


def lookup_source(key: str) -> Dict[str, Any]:
    """학술 출처 결정론 조회. LLM은 이 함수 결과만 인용해야 한다."""
    if key not in HABIT_SOURCES:
        raise ValueError(
            f"[FAIL] 출처 키 '{key}'는 카탈로그에 없음. "
            f"가용 키: {list(HABIT_SOURCES.keys())}"
        )
    return HABIT_SOURCES[key]


def format_citation(key: str) -> str:
    """표준 인용 문자열 생성 (LLM 자연어 추론 금지)."""
    s = lookup_source(key)
    if "journal" in s:
        return (
            f"{s['author']} ({s['year']}). {s['title']}. "
            f"{s['journal']} {s['volume_pages']}. doi: {s.get('doi', 'N/A')}"
        )
    elif "source" in s:
        return f"{s['author']} ({s['year']}). {s['title']}. {s['source']}"
    else:
        return (
            f"{s['author']} ({s['year']}). {s['title']}. "
            f"{s['publisher']}. ISBN: {s.get('isbn', 'N/A')}"
        )


def all_citations_block() -> str:
    """모든 출처 인용 블록 결정론 생성."""
    lines = []
    for key in HABIT_SOURCES:
        lines.append(f"- {format_citation(key)}")
    return "\n".join(lines)


# ============================================================================
# 2. 30초 시작 단계 룰 기반 검증
# ============================================================================

# 30초 안 시작 *불가능*한 단어들의 패턴 (룰 기반)
_NOT_TINY_PATTERNS: List[Tuple[str, str]] = [
    (r"(\d+)\s*시간", "시간 단위 = 30초 초과 명백"),
    (r"(\d+)\s*분", "분 단위 — Tiny 단계 후의 본행동 가능성"),
    (r"매일\s+\d+\s*km", "km 단위 운동 = Tiny 아님"),
    (r"\d+,?\d*\s*자\s+쓰기", "글자 수 명시 = Tiny 아님"),
    (r"\d+\s*권\s+읽기", "권 단위 = Tiny 아님"),
    (r"\d+,?\d*\s*보\s+걷기", "보 수 명시 = Tiny 아님"),
    (r"\d+\s*세트", "세트 수 명시 = Tiny 아님"),
]

# 30초 안 시작 *가능*한 신호 단어
_TINY_HINTS = [
    "한 문장", "한 줄", "한 절", "한 모금",
    "신발 신기", "현관문", "노트북 열기", "책 펴기",
    "한 페이지", "한 호흡", "한 번",
]


def validate_30sec_action(action_text: str) -> Dict[str, Any]:
    """
    행동 텍스트가 30초 시작 단계인지 룰 기반 점검.
    LLM이 '느낌'으로 통과시키지 못하게 결정론 차단.
    """
    if not action_text or not action_text.strip():
        return {"pass": False, "reason": "빈 입력", "violations": ["EMPTY_INPUT"]}

    violations = []
    for pattern, why in _NOT_TINY_PATTERNS:
        m = re.search(pattern, action_text)
        if m:
            violations.append(f"[패턴 위배] '{m.group(0)}' — {why}")

    tiny_hints_found = [h for h in _TINY_HINTS if h in action_text]

    is_pass = (len(violations) == 0)
    return {
        "pass": is_pass,
        "violations": violations,
        "tiny_hints_found": tiny_hints_found,
        "guidance": (
            "Fogg 2019: 30초 안 시작 가능해야 함. 큰 행동은 'Tiny 시작 단계'로 더 쪼개야 함."
            if not is_pass
            else "30초 시작 가능 신호 확인."
        ),
        "source": format_citation("fogg_2019"),
    }


# ============================================================================
# 3. Habit Stacking 형식 검증
# ============================================================================

_HABIT_STACK_PATTERNS = [
    r"\[?([^\[\]]+?)\]?\s*(?:후에|뒤에|다음에|끝나면|마치면)\s*[,，]?\s*\[?([^\[\]]+?)\]?\s*(?:한다|하기|할 것이다|하겠다)",
    r"after\s+(?:i\s+)?([^,]+?)\s*,\s*i\s+will\s+(.+)",
]


def validate_habit_stack(text: str) -> Dict[str, Any]:
    """
    Habit Stacking 형식 '[기존 습관] 후에 [새 습관] 한다' 검증.
    Clear 2018 / Fogg 2019 표준 양식.
    """
    if not text or not text.strip():
        return {"pass": False, "reason": "빈 입력"}

    text_l = text.lower()
    for pat in _HABIT_STACK_PATTERNS:
        m = re.search(pat, text_l, re.IGNORECASE)
        if m:
            return {
                "pass": True,
                "anchor": m.group(1).strip(),
                "new_habit": m.group(2).strip(),
                "format": "[기존 습관] 후에 [새 습관] 한다",
                "source": format_citation("clear_2018"),
            }
    return {
        "pass": False,
        "reason": "Habit Stacking 표준 양식 미준수",
        "expected": "'[기존 습관] 후에 [새 습관] 한다' 형식 필요",
        "source": format_citation("clear_2018"),
    }


# ============================================================================
# 4. 5단계 진행 검증
# ============================================================================

# Step별 내용 키워드 — "Step N" 표제 같은 약한 시그널은 제외하고
# 실제 단계 *내용*이 들어 있어야만 PASS.
STEP_KEYS = {
    1: ["행동 분해", "구체 행동", "구체적 동작", "비디오로 녹화", "녹화 가능"],
    2: ["트리거", "Cue", "앵커", "Habit Stacking", "기존 습관"],
    3: ["Tiny", "작게", "30초", "시작 단계", "최소 단위"],
    4: ["보상", "Reward", "도파민", "즉각 보상"],
    5: ["추적", "Tracking", "축하", "Celebration", "캘린더"],
}


def validate_5_steps(content: str) -> Dict[str, Any]:
    """
    산출물이 5단계 모두 포함했는지 결정론 검증.
    LLM이 단계를 '건너뛰지' 못하게 차단.
    """
    results = {}
    missing = []
    for step, keys in STEP_KEYS.items():
        found = [k for k in keys if k.lower() in content.lower()]
        present = len(found) > 0
        results[f"step{step}"] = {"present": present, "matched_keys": found}
        if not present:
            missing.append(step)
    return {
        "pass": len(missing) == 0,
        "missing_steps": missing,
        "details": results,
        "rule": "절대 원칙 #1: 5단계 모두 진행 — 행동·트리거·Tiny·보상·추적",
    }


# ============================================================================
# 5. 정착 기간 캘린더 계산 (결정론)
# ============================================================================

def parse_start_date(s: str) -> date:
    """다양한 한국어/ISO 날짜 표현을 date로 정규화."""
    s = s.strip()
    formats = [
        "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
        "%Y년 %m월 %d일", "%Y년%m월%d일",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"날짜 파싱 실패: '{s}'. ISO(YYYY-MM-DD) 권장.")


def calc_settlement_dates(start: date) -> Dict[str, str]:
    """
    시작일 기준 핵심 점검 시점 결정론 계산.
    Lally et al. 2010 기반.
    """
    d7 = start + timedelta(days=6)       # 7일째 (start 포함)
    d21 = start + timedelta(days=20)     # 21일 신화 차단 시점
    d30 = start + timedelta(days=29)     # 30일 점검
    d66 = start + timedelta(days=65)     # Lally 중앙값
    d90 = start + timedelta(days=89)     # 3개월 표준 정착

    return {
        "start": start.isoformat(),
        "day7_check": d7.isoformat(),
        "day21_myth_note": d21.isoformat(),
        "day30_check": d30.isoformat(),
        "day66_lally_median": d66.isoformat(),
        "day90_settlement_review": d90.isoformat(),
        "lally_range_low": (start + timedelta(days=17)).isoformat(),
        "lally_range_high": (start + timedelta(days=253)).isoformat(),
        "source": format_citation("lally_2010"),
        "note": (
            "21일 신화는 Lally 2010 (median 66일, range 18~254일) 으로 차단. "
            "3개월(90일)을 표준 정착 기간으로 안내한다."
        ),
    }


# ============================================================================
# 6. 첫 7일 플랜 결정론 생성
# ============================================================================

def gen_first_7_day_plan(start: date, anchor: str, tiny_action: str) -> List[Dict[str, str]]:
    """
    시작일·앵커·Tiny 행동을 받아 첫 7일 캘린더 결정론 생성.
    LLM이 날짜를 잘못 계산하지 못하게 차단.
    """
    weekday_kr = ["월", "화", "수", "목", "금", "토", "일"]
    plan = []
    for i in range(7):
        d = start + timedelta(days=i)
        wd = weekday_kr[d.weekday()]
        plan.append({
            "day": f"Day {i+1}",
            "date": d.isoformat(),
            "weekday": wd,
            "trigger": anchor,
            "tiny_action": tiny_action,
            "celebration": "행동 직후 3초 내 '좋아!' + 미소 (Fogg Celebration)",
            "if_missed": "Never miss twice — 다음 날 같은 트리거에서 회복 (Clear 2018)",
        })
    return plan


def format_first_7_day_plan(start: date, anchor: str, tiny_action: str) -> str:
    """7일 플랜 마크다운 결정론 출력."""
    plan = gen_first_7_day_plan(start, anchor, tiny_action)
    lines = [
        "## 첫 7일 플랜 (결정론 생성)",
        "",
        "| Day | 날짜 | 요일 | 트리거(앵커) | Tiny 행동 | 즉시 축하 |",
        "|-----|------|------|--------------|----------|----------|",
    ]
    for p in plan:
        lines.append(
            f"| {p['day']} | {p['date']} | {p['weekday']} | "
            f"{p['trigger']} | {p['tiny_action']} | {p['celebration']} |"
        )
    lines.extend([
        "",
        "**빠진 날 대응**: *Never miss twice* — 한 번은 빠져도 다음 날 같은 트리거에서 회복. "
        "(근거: " + format_citation("clear_2018") + ")",
    ])
    return "\n".join(lines)


# ============================================================================
# 7. 습관 카드 결정론 생성
# ============================================================================

@dataclass
class HabitCard:
    """습관 설계 카드 — 모든 필드 명시. LLM이 비워두지 못하게 결정론 강제."""
    user_label: str
    goal_abstract: str
    step1_concrete_action: str       # Step 1 — 행동
    step2_anchor: str                # Step 2 — 트리거(앵커)
    step3_tiny_start: str            # Step 3 — Tiny 시작 단계
    step4_reward: str                # Step 4 — 즉각 보상
    step5_tracking: str              # Step 5 — 추적·축하
    start_date: str                  # ISO YYYY-MM-DD
    missed_day_rule: str = "Never miss twice — 한 번 빠져도 다음 날 회복"
    settlement_target_days: int = 90 # 3개월 표준 정착 기간


def gen_habit_card_markdown(card: HabitCard) -> str:
    """습관 카드 마크다운 결정론 출력."""
    dates = calc_settlement_dates(parse_start_date(card.start_date))
    plan_md = format_first_7_day_plan(
        parse_start_date(card.start_date),
        card.step2_anchor,
        card.step3_tiny_start,
    )
    return f"""## 습관 설계 카드 — {card.user_label}

**추상 목표**: {card.goal_abstract}

| 단계 | 내용 |
|------|------|
| 🔬 Step 1 — 구체 행동 | {card.step1_concrete_action} |
| ⚓ Step 2 — 트리거(앵커) | {card.step2_anchor} |
| 🪶 Step 3 — Tiny 시작 단계 | {card.step3_tiny_start} |
| 🎁 Step 4 — 즉각 보상 | {card.step4_reward} |
| 📊 Step 5 — 추적·축하 | {card.step5_tracking} |

**시작일**: {dates['start']}
**점검 시점**:
- 7일째: {dates['day7_check']}
- 30일째: {dates['day30_check']}
- 66일째 (Lally 중앙값): {dates['day66_lally_median']}
- **90일째 정착 점검**: {dates['day90_settlement_review']}

**빠진 날 대응 규칙**: {card.missed_day_rule}

{plan_md}

---

### 근거 출처
{all_citations_block()}
"""


# ============================================================================
# 8. 21일 신화 차단·미인용 통계 차단 검증
# ============================================================================

_FORBIDDEN_PATTERNS = [
    (r"21일.{0,20}(?:이면|만에).{0,20}습관", "21일 신화 단정. Lally 2010 (median 66일)으로 교체 필요."),
    (r"습관.{0,10}형성.{0,10}21일", "21일 신화 단정. Lally 2010 (median 66일)으로 교체 필요."),
    (r"\d{1,3}\s*%.{0,20}(?:사람|성공|실패|충동|동기)", "% 단언 — 출처 명시 또는 표현 완화 필요"),
]


def check_forbidden_statements(content: str) -> Dict[str, Any]:
    """21일 신화·출처 없는 % 단언 차단 결정론 검증."""
    violations = []
    for pat, why in _FORBIDDEN_PATTERNS:
        for m in re.finditer(pat, content):
            violations.append({
                "match": m.group(0),
                "rule": why,
            })
    return {"pass": len(violations) == 0, "violations": violations}


# ============================================================================
# 9. Never miss twice 명시 검증
# ============================================================================

def check_never_miss_twice(content: str) -> Dict[str, Any]:
    """
    절대 원칙 #4: 빠진 날 대응 규칙 의무.
    'Never miss twice' 표현 또는 '한 번은 빠져도 다음 날 회복' 같은 동의 표현 포함 여부.
    """
    patterns = [
        r"never miss twice",
        r"한 번.{0,5}빠.{0,15}(?:다음|회복|다시)",
        r"두 번 연속.{0,10}빠지지 않",
        r"빠진 날.{0,10}(?:회복|다음 날)",
    ]
    for pat in patterns:
        if re.search(pat, content, re.IGNORECASE):
            return {"pass": True, "matched": pat}
    return {
        "pass": False,
        "rule": "절대 원칙 #4 — Never miss twice 규칙 미명시",
        "source": format_citation("clear_2018"),
    }


# ============================================================================
# 10. 종합 검증
# ============================================================================

def check_step_connection(content: str) -> Dict[str, Any]:
    """
    이론(E형)·Step 특정(F형) 응답에서 5단계 연결 안내 *반드시* 명시 검증.
    절대 원칙 OP-4 강제 — LLM이 5단계 연결을 *빠뜨리지 못하게* 결정론 차단.
    """
    has_step_marker = bool(re.search(r"Step\s*[1-5]|5단계", content))
    has_source = bool(re.search(r"출처|doi|ISBN|(19\d\d)|(20\d\d)", content))
    ok = has_step_marker and has_source
    return {
        "pass": ok,
        "has_step_marker": has_step_marker,
        "has_source": has_source,
        "rule": "OP-4 강제: 이론·Step 특정 응답은 *반드시* 5단계 중 어느 Step에 연결되는지 명시 + 출처 인용 필수.",
    }


def full_output_validation(content: str) -> Dict[str, Any]:
    """스킬 산출물 전체 결정론 검증."""
    is_card_type = ("🔬" in content and "🪶" in content and "📊" in content)

    forbidden_check = check_forbidden_statements(content)

    if is_card_type:
        steps_check = validate_5_steps(content)
        miss_check = check_never_miss_twice(content)
        has_90_day = bool(re.search(r"90일|3개월", content))
        has_lally = bool(re.search(r"Lally|66일", content))
        all_pass = (steps_check["pass"] and miss_check["pass"]
                    and forbidden_check["pass"] and has_90_day and has_lally)
        return {
            "overall_pass": all_pass, "response_type": "card",
            "5_steps": steps_check, "never_miss_twice": miss_check,
            "forbidden_statements": forbidden_check,
            "has_90_day_mention": has_90_day, "has_lally_mention": has_lally,
        }
    else:
        # 이론·Step 특정 응답 — Step 연결 + 출처 + 금지 패턴
        conn_check = check_step_connection(content)
        all_pass = conn_check["pass"] and forbidden_check["pass"]
        return {
            "overall_pass": all_pass, "response_type": "theory_or_step_specific",
            "step_connection": conn_check, "forbidden_statements": forbidden_check,
        }


# ============================================================================
# CLI
# ============================================================================

def _cli():
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  habit_lib.py source <key>")
        print("  habit_lib.py citations")
        print("  habit_lib.py tiny <action_text>")
        print("  habit_lib.py stack <text>")
        print("  habit_lib.py steps <content_text>")
        print("  habit_lib.py dates <YYYY-MM-DD>")
        print("  habit_lib.py plan7 <YYYY-MM-DD> <anchor> <tiny_action>")
        print("  habit_lib.py validate <content_text>")
        print("  habit_lib.py card <json_payload>")
        return 1

    cmd = sys.argv[1]

    if cmd == "source":
        print(json.dumps(lookup_source(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "citations":
        print(all_citations_block())
    elif cmd == "tiny":
        print(json.dumps(validate_30sec_action(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "stack":
        print(json.dumps(validate_habit_stack(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "steps":
        print(json.dumps(validate_5_steps(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "dates":
        d = parse_start_date(sys.argv[2])
        print(json.dumps(calc_settlement_dates(d), ensure_ascii=False, indent=2))
    elif cmd == "plan7":
        d = parse_start_date(sys.argv[2])
        print(format_first_7_day_plan(d, sys.argv[3], sys.argv[4]))
    elif cmd == "validate":
        print(json.dumps(full_output_validation(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "card":
        payload = json.loads(sys.argv[2])
        card = HabitCard(**payload)
        print(gen_habit_card_markdown(card))
    else:
        print(f"Unknown command: {cmd}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
