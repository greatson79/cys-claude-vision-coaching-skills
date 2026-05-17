"""SMART 5축 결정론 검증기.

Doran (1981) 원안 + 현대 코칭판 두 축 매핑을 모두 보장하며,
각 축의 필수 입력 유무·측정 단위·기한 형식을 정규식으로 점검한다.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


# 수치 측정 단위 — 한국어/영어 혼용 광범위 패턴
# 주의: Python re의 \b는 한글 인접 시 단어 경계로 작동하지 않음 → \b 사용 금지.
_MEASURABLE_PATTERNS = [
    r"\d+(\.\d+)?",  # 숫자 (단독)
    r"\d+\s*(권|회|명|번|쪽|페이지|건|개|장|편|분|시간|일|주|개월|년|kg|m|km|%|퍼센트|만|억|원|달러|USD|KRW)",
    r"\d+\s*(book|books|lecture|lectures|article|articles|page|pages|hour|hours|day|days|week|weeks|month|months|year|years|kg|km|percent|%)",
]

_TIME_BOUND_PATTERNS = [
    r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}",                                  # 2026-12-31
    r"\d{4}\s*년(\s*\d{1,2}\s*월(\s*\d{1,2}\s*일)?)?",                  # 2026년 12월 31일
    r"\d{4}\s*Q[1-4]",                                                  # 2027 Q3
    r"(다음|이번|내|올|내년|올해)\s*(달|주|분기|해|년)",                 # 이번 주, 다음 분기
    r"(내일|모레|글피|오늘\s*안)",                                       # 내일
    r"(by|until|by\s+the\s+end\s+of|until\s+the\s+end\s+of)\s+\d{4}",  # by 2027
    r"\d+\s*(개월|일|주|년)\s*(안|이내|후|까지)",                        # 6개월 안에
    r"\d+\s*(month|months|day|days|week|weeks|year|years)\s+(later|after|from\s+now)",
    r"\d{4}[-/.]\d{1,2}",                                              # 2027-12 (월 단위)
    r"마감",                                                            # 마감일
    r"기한",                                                            # 기한
]

# 동사·결과 명사 화이트리스트 — Specific 판정용. 한국어/영어 광범위 커버.
_SPECIFIC_VERB_HINTS = [
    # 출판·집필
    "출간", "출판", "발간", "발행", "집필", "저술", "기고", "기록", "작성",
    # 학습·성취·완수
    "완성", "완수", "완주", "달성", "성취", "수료", "이수", "졸업", "입학", "진학",
    "수강", "취득", "획득", "합격", "통과", "인증", "자격", "면허",
    # 비즈니스
    "확보", "유치", "체결", "계약", "매각", "인수", "합병", "투자", "모금",
    "런칭", "출시", "발매", "런처", "오픈", "개점", "폐점", "확장",
    "구축", "조성", "운영", "관리", "마감", "마무리", "종료",
    # 코칭·교육
    "강연", "강의", "교육", "멘토링", "코칭", "지도", "양성", "양육", "훈련",
    "모집", "선발", "채용", "채택", "참석", "발표", "전달", "공유",
    # 운동·신체
    "완주", "달리기", "기록 단축", "감량", "증량", "복귀", "회복",
    # 일반 결과
    "개발", "제작", "생산", "납품", "배포", "배송", "공개", "공시",
    # 영어
    "publish", "complete", "finish", "deliver", "achieve", "launch", "build",
    "write", "develop", "obtain", "secure", "run", "host", "earn", "win",
    "graduate", "certify", "license", "release", "ship", "raise", "close",
    "mentor", "coach", "teach", "train", "recruit", "hire",
]


# 한국어 동사 어미 / 명사화 어미 패턴 — Specific 보조 판정
_KOREAN_VERB_ENDINGS = re.compile(
    r"(하기|되기|기$|하다$|되다$|하라$|한다$|된다$|함$|됨$|화$)"
)


@dataclass
class AxisResult:
    axis: str
    passed: bool
    reason: str
    suggestion: str = ""


@dataclass
class SmartReport:
    goal_text: str
    axes: List[AxisResult]
    passed_all: bool

    def as_dict(self) -> dict:
        return {
            "goal_text": self.goal_text,
            "passed_all": self.passed_all,
            "axes": [vars(a) for a in self.axes],
        }


def _has_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _check_specific(text: str) -> AxisResult:
    has_verb = any(v in text for v in _SPECIFIC_VERB_HINTS)
    has_ending = bool(_KOREAN_VERB_ENDINGS.search(text))
    if (has_verb or has_ending) and len(text.strip()) >= 8:
        return AxisResult("Specific", True, "동사·대상이 식별됨")
    return AxisResult(
        "Specific", False, "동사·대상이 모호함",
        "예: '단행본 1권 출간', '강연 10회 개최' 식으로 동사+대상을 명시"
    )


def _check_measurable(text: str) -> AxisResult:
    if _has_any(text, _MEASURABLE_PATTERNS):
        return AxisResult("Measurable", True, "수치·단위가 포함됨")
    return AxisResult(
        "Measurable", False, "측정 가능한 수치·단위가 없음",
        "예: '___권', '___회', '___명', '___% 향상' 식 단위 추가"
    )


def _check_achievable(text: str, resources: Optional[str]) -> AxisResult:
    if resources and len(resources.strip()) >= 5:
        return AxisResult("Achievable", True, "자원·역량 근거 제출됨")
    return AxisResult(
        "Achievable", False, "자원·시간·역량 점검이 누락됨",
        "확보 자원·소요 시간·필요 역량 한 줄 명시"
    )


def _check_relevant(text: str, vision: Optional[str]) -> AxisResult:
    if vision and len(vision.strip()) >= 5:
        return AxisResult("Relevant", True, "비전 원본과 연결됨")
    return AxisResult(
        "Relevant", False, "비전 핵심과의 연결이 명시되지 않음",
        "이 목표가 영감 원본의 어느 부분을 구체화하는지 한 줄 명시"
    )


def _check_time_bound(text: str) -> AxisResult:
    if _has_any(text, _TIME_BOUND_PATTERNS):
        return AxisResult("Time-bound", True, "기한 표현이 포함됨")
    return AxisResult(
        "Time-bound", False, "명확한 기한이 없음",
        "예: '2027-12-31까지', '2027 Q3까지', '6개월 안에' 명시"
    )


def validate_smart(
    goal_text: str,
    resources_note: Optional[str] = None,
    vision_link: Optional[str] = None,
) -> SmartReport:
    """SMART 5축 결정론 검증.

    Args:
        goal_text: 검증 대상 목표 문장.
        resources_note: 자원·시간·역량 근거 한 줄.
        vision_link: 비전 원본과의 연결 한 줄.
    """
    axes = [
        _check_specific(goal_text),
        _check_measurable(goal_text),
        _check_achievable(goal_text, resources_note),
        _check_relevant(goal_text, vision_link),
        _check_time_bound(goal_text),
    ]
    return SmartReport(
        goal_text=goal_text,
        axes=axes,
        passed_all=all(a.passed for a in axes),
    )


def render_table(report: SmartReport) -> str:
    lines = ["| 축 | 통과 | 근거 | 보완 제안 |", "|---|------|------|-----------|"]
    for a in report.axes:
        mark = "✓" if a.passed else "✗"
        lines.append(f"| {a.axis} | {mark} | {a.reason} | {a.suggestion} |")
    return "\n".join(lines)


if __name__ == "__main__":
    import json
    sample = "2027-12-31까지 단행본 1권 출간"
    r = validate_smart(sample, resources_note="현 원고 6장 완성·주 10시간", vision_link="AGI 영성·미래학 통합 지혜 전수")
    print(json.dumps(r.as_dict(), ensure_ascii=False, indent=2))
    print()
    print(render_table(r))
