"""유형 A/B/C/D 입력 라우터 — 결정론적 분기.

SKILL.md의 4유형(A: 비전 한 문장, B: clarity 산출물, C: LTG/STG 보유,
D: 첫 한 걸음만)을 LLM의 모호한 추론 없이 입력 신호로 매핑한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


# 명시 의도 신호 — 강한 신호이면 즉시 매핑
_INTENT_D = [
    r"첫\s*한\s*걸음", r"내일\s*아침", r"30\s*분\s*행동",
    r"first\s+step", r"tomorrow\s+morning",
]
_INTENT_C = [
    r"OKR\s*만\s*만들", r"OKR\s*만\s*해", r"OKR\s*변환",
    r"LTG.*STG", r"이미\s*목표", r"이미\s*plan",
]
_INTENT_B = [
    r"vision-clarity", r"clarity-coaching", r"명료화\s*산출", r"명료화\s*결과",
]


@dataclass
class RouteDecision:
    input_type: str           # A | B | C | D
    steps_to_run: List[str]   # ex: ["Step 1", "Step 2", ...]
    rationale: str


def _match_any(text: str, patterns) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def route(user_text: str, vision_clarity_output: bool = False, has_ltg_stg: bool = False) -> RouteDecision:
    """입력 신호 → 유형 결정.

    Args:
        user_text: 사용자 원본 요청.
        vision_clarity_output: vision-clarity-coaching 산출물 입력 여부 (외부 신호).
        has_ltg_stg: 이미 장기·단기 목표 보유 여부 (외부 신호).
    """
    if _match_any(user_text, _INTENT_D):
        return RouteDecision(
            "D", ["Step 5"],
            "유형 D — 사용자가 첫 한 걸음만 요청. Step 5 단독 실행."
        )
    if _match_any(user_text, _INTENT_C) or has_ltg_stg:
        return RouteDecision(
            "C", ["Step 4", "Step 5"],
            "유형 C — 이미 LTG/STG 보유. OKR 변환과 첫 걸음만 실행."
        )
    if _match_any(user_text, _INTENT_B) or vision_clarity_output:
        return RouteDecision(
            "B", ["Step 1 (간략)", "Step 2", "Step 3", "Step 4", "Step 5"],
            "유형 B — clarity-coaching 산출물 기반. Step 1은 요약 인용으로 처리."
        )
    return RouteDecision(
        "A", ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
        "유형 A 기본값 — 비전 원문만 입력. 5단계 풀 실행."
    )


if __name__ == "__main__":
    import json
    cases = [
        ("AGI 시대에 영성과 미래학을 잇는 비전을 목표로 바꿔줘", False, False),
        ("이미 LTG·STG 정해놓았으니 OKR만 만들어줘", False, True),
        ("내일 아침 첫 한 걸음만 잡아주세요", False, False),
        ("vision-clarity-coaching 산출물 결과를 가지고 왔습니다", True, False),
    ]
    for t, b, c in cases:
        d = route(t, b, c)
        print(t, "→", json.dumps(vars(d), ensure_ascii=False))
