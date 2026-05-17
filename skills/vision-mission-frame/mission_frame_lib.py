"""vision-mission-frame — 결정론적 헬퍼 라이브러리.

LLM이 자연어 추론으로 결정하면 할루시네이션·드리프트 위험이 있는 단계를
결정론으로 환원한 함수들. SKILL.md에서 명시적으로 호출하도록 지정한다.

기준 사양 1차: 같은 디렉터리의 SKILL.md (모든 인용문·표·도식의 정본).
기준 사양 2차: 최윤식 박사 『미래준비학교』(2016) 비전 프레임 도식 원문.

학계 표준 1:1 대조:
- (R) Reinforcing Feedback Loop 표기 — Peter Senge, The Fifth Discipline (1990)·
  Jay Forrester MIT System Dynamics Group 시스템 사고 표준 다이어그램 표기.
- 4가지 미래(Plausible/Possible/Wildcard/Normative) — Joseph Voros (2003),
  "A generic foresight process framework," Foresight 5(3): 10-21 — "Three P's
  and a W" 분류와 1:1 대응.

호출 예 (CLI):
    python3 mission_frame_lib.py honorific --doctor true
    python3 mission_frame_lib.py classify_input --text "한 축만 봐줘"
    python3 mission_frame_lib.py detect_religion --text "기도하면서 영감을"
    python3 mission_frame_lib.py list_quotes
    python3 mission_frame_lib.py verify_quote --text "비전 프레임이란..."
    python3 mission_frame_lib.py map_definition --phrase "시대적"
    python3 mission_frame_lib.py three_realm --self true --others false --moral true
    python3 mission_frame_lib.py diagnose_loop --spiritual strong --rational weak
    python3 mission_frame_lib.py validate_report --file report.md
    python3 mission_frame_lib.py detect_drift --text "..."
    python3 mission_frame_lib.py recommend_skills --weak_axis rational
    python3 mission_frame_lib.py emoji_check --text "..."
    python3 mission_frame_lib.py format_report_skeleton --honorific 박사님
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# 0. 공통 상수
# ---------------------------------------------------------------------------

HONORIFIC_DEFAULT = "선생님"

AXES = ("spiritual", "rational")

# 입력 유형 → 실행 단계 매핑 (SKILL.md "입력 처리 — 4유형" 표 1:1 대응)
INPUT_TYPE_STAGES: dict[str, list[int]] = {
    "A": [1, 2, 3, 4, 5, 6],        # 풀 점검
    "B-spiritual": [1, 2, 3, 6],    # 영적 직관력 축만
    "B-rational": [1, 4, 6],        # 이성적 판단력 축만
    "C": [1, 5],                    # (R) 강화 피드백 루프 진단만
    "D": [2, 4, 5, 6],              # 박사님 본인 (1단계 생략)
}


# ---------------------------------------------------------------------------
# 1. 호칭 결정 (SKILL.md 도입부·D유형 분기 1:1 대응)
# ---------------------------------------------------------------------------

def select_honorific(meta: dict | None) -> str:
    """호칭을 결정한다. SKILL.md D유형 분기에 따라 박사님 본인이면 "박사님".

    meta 키 (모두 선택):
      - is_doctor: bool      → 최윤식 박사 본인 (True면 "박사님")
      - title: str            → 명시 직함 ("목사", "전도사", "교수" 등)
      - name: str             → 이름 (직함 없을 때 "○○님")

    반환: 단일 호칭 문자열. 빈 입력은 기본값 "선생님".
    """
    if not isinstance(meta, dict):
        return HONORIFIC_DEFAULT
    if meta.get("is_doctor") is True:
        return "박사님"
    title = (meta.get("title") or "").strip()
    if title:
        return title if title.endswith("님") else f"{title}님"
    name = (meta.get("name") or "").strip()
    if name:
        return f"{name}님"
    return HONORIFIC_DEFAULT


# ---------------------------------------------------------------------------
# 2. 입력 유형 분류 A/B-spiritual/B-rational/C/D
# ---------------------------------------------------------------------------

# SKILL.md "입력 처리 — 4유형" 표 토큰
TYPE_D_TOKENS = (
    "박사님 본인", "최윤식 박사 본인", "본인 비전", "내가 박사",
    "is_doctor", "박사님이 직접",
)
TYPE_C_TOKENS = (
    "강화 피드백", "피드백 루프", "(r) loop", "r 루프", "루프 진단",
    "두 축이 서로 강화", "축이 흔들", "약한 축", "두 축 균형",
)
TYPE_B_SPIRITUAL_TOKENS = (
    "영적 직관력만", "영감만", "정신적 가치만", "영적 직관 축",
    "축 1만", "1축만", "spiritual intuition만",
)
TYPE_B_RATIONAL_TOKENS = (
    "이성적 판단력만", "정보만", "예측 구성만", "미래 변화 통찰만",
    "축 2만", "2축만", "intellectual judgment만", "judgement만",
)
TYPE_B_GENERIC_TOKENS = (
    "한 축만", "한 축", "한쪽 축만", "한 축 점검", "축 한 개",
)


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", (text or "").strip().lower())


def classify_input_type(text: str) -> str:
    """사용자 입력으로 A/B-spiritual/B-rational/C/D 유형을 결정한다.

    우선순위 (위에서 아래로 첫 매칭이 채택):
      D (박사님 본인) > C (루프 진단만) > B-spiritual > B-rational > B (한 축, 미명세) > A
    """
    norm = _normalize(text)
    if not norm:
        return "A"

    for tok in TYPE_D_TOKENS:
        if tok in norm:
            return "D"
    for tok in TYPE_C_TOKENS:
        if tok in norm:
            return "C"
    for tok in TYPE_B_SPIRITUAL_TOKENS:
        if tok in norm:
            return "B-spiritual"
    for tok in TYPE_B_RATIONAL_TOKENS:
        if tok in norm:
            return "B-rational"
    for tok in TYPE_B_GENERIC_TOKENS:
        if tok in norm:
            # 한 축이라고만 했고 어느 축인지 명시 안 됨 → 영적 직관력을 기본으로 처리
            # (이는 결정론 정책이지 추측 아님 — 사용자에게 재확인 권유)
            return "B-spiritual"

    return "A"


def stages_for_type(input_type: str) -> list[int]:
    """입력 유형이 거쳐야 할 단계 번호 리스트."""
    return INPUT_TYPE_STAGES.get(input_type, INPUT_TYPE_STAGES["A"])


# ---------------------------------------------------------------------------
# 3. 종교/비종교 컨텍스트 판별 (정신적 가치 기준 결정)
# ---------------------------------------------------------------------------

RELIGIOUS_TOKENS = (
    "기도", "예배", "성경", "교회", "목사", "전도사", "장로", "권사", "집사",
    "신앙", "주님", "하나님", "예수", "그리스도", "성령", "신학", "성도",
    "교파", "교인", "선교", "찬송", "qt", "큐티", "묵상", "신앙인",
    "기독교", "불교", "이슬람", "유대교", "힌두교", "종교", "수도", "수행",
    "경전", "코란", "꾸란", "토라", "탈무드", "다라니", "법문",
)


def detect_religion_context(text: str, explicit: str | None = None) -> str:
    """반환: "religious" | "secular" | "unknown".

    explicit이 "religious"/"secular"로 명시되면 그 값 우선.
    """
    if explicit in ("religious", "secular"):
        return explicit
    norm = _normalize(text)
    if not norm:
        return "unknown"
    for tok in RELIGIOUS_TOKENS:
        if tok in norm:
            return "religious"
    return "unknown"


def divine_value_criterion(religion_ctx: str) -> str:
    """SKILL.md "종교 여부별 적용" 1:1 매핑."""
    if religion_ctx == "religious":
        return "경전·신앙 기준"
    if religion_ctx == "secular":
        return "윤리·도덕·양심 기준"
    return "윤리·도덕·양심 기준 (종교 여부 미명시 → 비종교인 기준 기본 적용)"


# ---------------------------------------------------------------------------
# 4. 박사님 책 허용 인용문 사전 (할루시네이션 차단)
# ---------------------------------------------------------------------------
#
# SKILL.md에 명시된 인용문만 박사님 책 출처로 제시 가능. 다른 문구를 박사님 책
# 인용으로 제시하면 할루시네이션 — 절대 원칙 6 위반.
# 아래 목록은 SKILL.md 본문에서 *직접 발췌* 한 인용문이다.

AUTHORIZED_QUOTES: tuple[str, ...] = (
    # SKILL.md 12행, 92행, 243행 — 비전 프레임 정의
    "비전 프레임이란 '가치 있는 + 시대적 + 소명'이 어떻게 성장하는지를 "
    "설명하기 위해 필자가 만든 단어이다.",
    # SKILL.md 29행 — (R) Loop 비유
    "마이크로 들어간 소리가 더 커져서 스피커로 나오는 것 같은 증가형 강화 피드백",
    # SKILL.md 36행 — 영감 정의
    "외부로부터 주어지는 영감",
    # SKILL.md 42행 — 비종교인 영감
    "자기 외부에서 내부로 들어오는 영감·감동 혹은 통찰",
    # SKILL.md 45행 — 정신적 가치 정의
    "영감을 객관적으로 검증하는 안전장치",
    # SKILL.md 52행 — 정신적 가치 척도
    "비전의 건강도를 재는 척도",
    # SKILL.md 59행 — 정보 정의
    "과거와 현재에 대한 자기 이해 정보",
    # SKILL.md 65행 — 정보 출처 강조
    "이런 정보는 영감을 통해서가 아니라 이성적 판단력을 사용해서 찾는 자기 이해 정보이다.",
    # SKILL.md 68행 — 예측 구성 정의
    "미래를 예측하기 위한 자신만의 틀",
    # SKILL.md 85행 — 항목 살펴보기
    "각각의 항목에 대해서 자세하게 살펴보자.",
    # SKILL.md 148행 — (R) 의미
    "강화 피드백 Reinforcing Feedback Loop",
)


def _normalize_quote(s: str) -> str:
    """인용 비교용 정규화 — 공백/구두점 차이 흡수."""
    s = unicodedata.normalize("NFKC", s or "")
    # 따옴표·괄호 제거
    s = re.sub(r"[\"'`*_~()「」『』<>《》〈〉]", "", s)
    # 공백 압축
    s = re.sub(r"\s+", " ", s).strip()
    return s


_AUTHORIZED_NORMALIZED = tuple(_normalize_quote(q) for q in AUTHORIZED_QUOTES)


def list_authorized_quotes() -> list[str]:
    return list(AUTHORIZED_QUOTES)


def verify_quote(text: str) -> dict[str, Any]:
    """주어진 텍스트가 박사님 책 인용문(허용 목록)과 일치하는지 검증.

    반환: {
      "match": bool,
      "matched_index": int | None,
      "matched_quote": str | None,
      "reason": str
    }
    """
    norm = _normalize_quote(text)
    if not norm:
        return {
            "match": False,
            "matched_index": None,
            "matched_quote": None,
            "reason": "빈 입력",
        }
    for i, q in enumerate(_AUTHORIZED_NORMALIZED):
        if q in norm or norm in q:
            return {
                "match": True,
                "matched_index": i,
                "matched_quote": AUTHORIZED_QUOTES[i],
                "reason": "허용 목록 일치",
            }
    return {
        "match": False,
        "matched_index": None,
        "matched_quote": None,
        "reason": "박사님 책 인용 허용 목록에 없음 — 출력 금지",
    }


# ---------------------------------------------------------------------------
# 5. 비전 정의 매핑 (가치 있는/시대적/소명)
# ---------------------------------------------------------------------------

VISION_DEFINITION_MAP: dict[str, dict[str, str]] = {
    "가치 있는": {
        "axis": "영적 직관력 (Spiritual Intuition)",
        "components": "영감(Divine Inspiration) + 정신적 가치(Divine Value)",
    },
    "시대적": {
        "axis": "이성적 판단력 — 예측 구성 (Forecasting Framework)",
        "components": "미래예측 구성",
    },
    "소명": {
        "axis": "이성적 판단력 — 정보 (Information)",
        "components": "과거·현재 정보 (자기 내적 + 자기 외적)",
    },
}


def map_vision_definition_phrase(phrase: str) -> dict[str, str]:
    """비전 정의 3구문 중 하나를 비전 프레임 요소로 매핑.

    SKILL.md "비전 정의와의 직결" 표 1:1 대응. LLM이 매핑을 변형하지 못하도록.
    """
    key = (phrase or "").strip().strip('"\'').strip()
    if key not in VISION_DEFINITION_MAP:
        return {
            "error": f"'{phrase}' 는 비전 정의 3구문(가치 있는/시대적/소명)이 아님",
            "valid_keys": ", ".join(VISION_DEFINITION_MAP.keys()),
        }
    return {"phrase": key, **VISION_DEFINITION_MAP[key]}


# ---------------------------------------------------------------------------
# 6. 비전 영역 3겹 점검 (SKILL.md 3단계)
# ---------------------------------------------------------------------------

def classify_three_realm_check(
    self_joy: bool, others_value: bool, moral_value: bool
) -> dict[str, Any]:
    """SKILL.md 3단계 "비전 영역 3겹 점검" 결과 분류.

    인자:
      - self_joy:     박사님/사용자 자신 진정한 기쁨? (True/False)
      - others_value: 가족·이웃·세상에게 기쁨·가치? (True/False)
      - moral_value:  정신적·도덕적 가치? (True/False)

    반환: 분류·진단·재정의 안내가 포함된 dict.
    """
    flags = (bool(self_joy), bool(others_value), bool(moral_value))
    count = sum(flags)

    # 결과 분류 — SKILL.md 다이어그램 1:1
    if count == 3:
        return {
            "status": "PASS",
            "label": "3영역 교집합 — 진정한 비전 영역",
            "symbol": ("○", "○", "○"),
            "diagnosis": "세 영역 모두 동시 만족 — 건강한 비전 영역",
            "redefinition_prompt": None,
        }
    if count == 0:
        return {
            "status": "FAIL",
            "label": "세 영역 모두 미충족",
            "symbol": ("✗", "✗", "✗"),
            "diagnosis": "비전이 형성되어 있지 않음 — 비전 스케치 단계부터 재출발 필요",
            "redefinition_prompt": "현재 추구하는 일이 어느 한 영역에도 기쁨·가치를 만들지 못합니다. "
            "vision-clarity-coaching 또는 vision-five-stages 1단계(비전 스케치)로 돌아가 핵심을 재발견하세요.",
        }

    # 한두 영역만 만족 — SKILL.md 위험 표지
    if flags == (True, False, False):
        return {
            "status": "WARN",
            "label": "개인 욕망 (나만 기쁨)",
            "symbol": ("○", "✗", "✗"),
            "diagnosis": "한 영역만 극대화 시 자기중심·이기적 비전",
            "redefinition_prompt": "이 열망이 타인에게도 의미 있으려면 어떤 방향으로 확장할 수 있을까요?",
        }
    if flags == (False, True, False):
        return {
            "status": "WARN",
            "label": "자기희생·세상일",
            "symbol": ("✗", "○", "✗"),
            "diagnosis": "자기 진정한 기쁨 없는 헌신은 지속 불가 — 번아웃 위험",
            "redefinition_prompt": "이 헌신이 당신 자신에게도 진정한 기쁨인가요? 번아웃 없이 지속 가능한가요?",
        }
    if flags == (False, False, True):
        return {
            "status": "WARN",
            "label": "왜곡된 사명·질",
            "symbol": ("✗", "✗", "○"),
            "diagnosis": "높은 도덕적 기준만 내세워 나·가족 비참하게 만드는 균형 잃은 비전",
            "redefinition_prompt": "이 사명이 삶 속에서 어떻게 구체적으로 실현될 수 있을까요?",
        }
    if flags == (True, True, False):
        return {
            "status": "WARN",
            "label": "정신적 가치 누락 — 도덕 검증 안전장치 결여",
            "symbol": ("○", "○", "✗"),
            "diagnosis": "나·세상에는 기쁨이지만 정신적·도덕적 가치 검증이 결여됨 — 비전 안전장치 부재",
            "redefinition_prompt": "이 비전이 신앙·윤리·양심의 기준으로 점검될 때도 정당한가요?",
        }
    if flags == (True, False, True):
        return {
            "status": "WARN",
            "label": "이웃·세상 부재",
            "symbol": ("○", "✗", "○"),
            "diagnosis": "자기 만족과 정신적 가치는 있으나 이웃·세상 기여 없음 — 자족적 영성",
            "redefinition_prompt": "이 가치가 가족·이웃·세상에 어떤 기쁨·가치를 만드나요?",
        }
    if flags == (False, True, True):
        return {
            "status": "WARN",
            "label": "자기 부재 — 박사님(자신) 진정한 기쁨 누락",
            "symbol": ("✗", "○", "○"),
            "diagnosis": "세상 기여와 정신적 가치는 있으나 본인의 진정한 기쁨 누락 — 자기희생적 사명",
            "redefinition_prompt": "이 비전이 당신 자신에게도 진정한 기쁨과 의미를 주나요?",
        }

    # 모든 케이스가 위에서 처리되지만 안전망
    return {
        "status": "UNKNOWN",
        "label": "분류 불가",
        "symbol": ("?", "?", "?"),
        "diagnosis": "입력값 검증 실패",
        "redefinition_prompt": None,
    }


# ---------------------------------------------------------------------------
# 7. 강화 피드백 루프 진단 (SKILL.md 5단계)
# ---------------------------------------------------------------------------

STRENGTH_VALUES = ("strong", "balanced", "weak")

# SKILL.md "축별 약화 증상" + "약한 축 강화 방향" 1:1 대응 표
AXIS_WEAKNESS_TABLE: dict[str, dict[str, str]] = {
    "spiritual": {
        "axis_name": "영적 직관력 (Spiritual Intuition)",
        "weakness_symptoms": (
            "비전이 '해야 하는 일' 목록으로 전락, 의미·사명감 흐려짐, "
            "열정 감소, 번아웃 가속"
        ),
        "strengthening_path": (
            "기도·명상·독서 루틴 재정비 → 경전·윤리 서적으로 정신적 가치 재점검 → "
            "'왜 이 비전이어야 하는가?'를 정기적으로 자문"
        ),
        "linked_components": "영감(Divine Inspiration) + 정신적 가치(Divine Value)",
    },
    "rational": {
        "axis_name": "이성적 판단력 (Intellectual Judgment) / 미래 변화 통찰",
        "weakness_symptoms": (
            "영감·열정은 있으나 구체적 경로 막막, 미래 변화에 무방비, "
            "실행 계획 부재, 비전이 막연한 꿈에 머물"
        ),
        "strengthening_path": (
            "자기 내적 정보 정밀 수집(vision-readiness·mbti·enneagram·CYS 검사 활용) → "
            "미래지도 작성(vision-futures-timeline-map) → "
            "비전 영역 미래 트렌드 정기 스캔"
        ),
        "linked_components": "정보(Information) + 예측 구성(Forecasting Framework)",
    },
}


def diagnose_loop(spiritual: str, rational: str) -> dict[str, Any]:
    """5단계 강화 피드백 루프 진단.

    spiritual / rational ∈ {"strong", "balanced", "weak"}.

    반환: 강한 축·약한 축·약화 증상·강화 방향이 포함된 dict.
    """
    if spiritual not in STRENGTH_VALUES or rational not in STRENGTH_VALUES:
        return {
            "error": f"각 축의 값은 {STRENGTH_VALUES} 중 하나여야 함",
            "given": {"spiritual": spiritual, "rational": rational},
        }

    rank = {"weak": 0, "balanced": 1, "strong": 2}
    s_rank, r_rank = rank[spiritual], rank[rational]

    # 강한 축·약한 축 결정
    if s_rank == r_rank:
        strong_axis = "균형"
        weak_axis = "없음" if s_rank >= 1 else "양쪽 모두 약함"
    elif s_rank > r_rank:
        strong_axis = "영적 직관력 (Spiritual Intuition)"
        weak_axis = "rational"
    else:
        strong_axis = "이성적 판단력 (Intellectual Judgment)"
        weak_axis = "spiritual"

    result: dict[str, Any] = {
        "spiritual_strength": spiritual,
        "rational_strength": rational,
        "strong_axis": strong_axis,
        "weak_axis_key": weak_axis,
        "loop_status": _loop_status(s_rank, r_rank),
    }

    # 약화 증상 / 강화 방향 — SKILL.md 표 1:1
    if weak_axis in AXIS_WEAKNESS_TABLE:
        info = AXIS_WEAKNESS_TABLE[weak_axis]
        result["weakness_symptoms"] = info["weakness_symptoms"]
        result["strengthening_path"] = info["strengthening_path"]
        result["weak_axis_full_name"] = info["axis_name"]
    elif weak_axis == "양쪽 모두 약함":
        result["weakness_symptoms"] = (
            AXIS_WEAKNESS_TABLE["spiritual"]["weakness_symptoms"] + " / "
            + AXIS_WEAKNESS_TABLE["rational"]["weakness_symptoms"]
        )
        result["strengthening_path"] = (
            "양 축 모두 약화 — 영적 직관력부터 회복 권장: "
            + AXIS_WEAKNESS_TABLE["spiritual"]["strengthening_path"]
            + " // 동시에 "
            + AXIS_WEAKNESS_TABLE["rational"]["strengthening_path"]
        )
    else:
        result["weakness_symptoms"] = "약화 증상 없음 — 두 축 균형 (R)+ 작동 중"
        result["strengthening_path"] = "현 균형 유지 + 두 축 상호 강화 흐름 점검"

    return result


def _loop_status(s_rank: int, r_rank: int) -> str:
    """(R) 강화 피드백 루프 상태 분류."""
    if s_rank == 0 and r_rank == 0:
        return "루프 정지 — 두 축 모두 약화 (비전 위기)"
    if s_rank == 0 or r_rank == 0:
        return "루프 불균형 — 한쪽 축 약화 (비전 흔들림)"
    if s_rank == 2 and r_rank == 2:
        return "루프 강화 — 두 축 강함 (+ Reinforcing 활발)"
    return "루프 가동 중 — 두 축 작동 (강화 여지 있음)"


# ---------------------------------------------------------------------------
# 8. 박사님 정의 변형 검출 (할루시네이션 차단)
# ---------------------------------------------------------------------------
#
# LLM이 박사님 책 정의를 풀어쓰기·요약·임의 변형할 때 자동 감지.

CORE_TERMS: tuple[tuple[str, str, str], ...] = (
    # (정본 표현, 변형 의심 키워드 패턴, 위반 설명)
    ("영적 직관력", "직관력|영적 직관|spiritual intuit", "축 1 명칭"),
    ("이성적 판단력", "이성적|판단력|intellectual judg", "축 2 명칭"),
    ("미래 변화 통찰", "미래 통찰|변화 통찰|judgement", "축 2 결과 명칭"),
    ("영감", "divine inspirat|inspiration", "축 1 ①"),
    ("정신적 가치", "divine value|가치 안전장치", "축 1 ②"),
    ("정보", "information", "축 2 ③"),
    ("예측 구성", "forecasting framework|미래예측 구성|forecast frame", "축 2 ④"),
    ("강화 피드백 루프", "reinforcing feedback|(r) loop|루프", "(R) 핵심 메커니즘"),
)

FORBIDDEN_REWRITES: tuple[str, ...] = (
    # 박사님 정의를 임의 변형한 표현 — 출력 금지
    "정신적 직관력",  # 영적 직관력의 변형
    "감정적 판단력",  # 이성적 판단력의 변형
    "정보 통찰",       # 미래 변화 통찰의 변형
    "정보적 직관",
    "영적 판단력",
    "약화 피드백",     # (R) 강화 피드백의 반대 변형
    "약화 루프",
    "감소 피드백 루프",
    "비전 = 가치 있는 시대적 소명",  # 정의문은 인용으로만 — 등호 변형 금지
)


def detect_doctrinal_drift(text: str) -> dict[str, Any]:
    """LLM 출력 텍스트에 박사님 정의 변형(할루시네이션)이 있는지 검출.

    반환:
      {"clean": bool, "violations": [{"term": str, "reason": str}, ...]}
    """
    norm = (text or "")
    violations: list[dict[str, str]] = []
    for forbidden in FORBIDDEN_REWRITES:
        if forbidden in norm:
            violations.append({
                "term": forbidden,
                "reason": "박사님 책 정의 변형 — 출력 금지 (절대 원칙 1·6 위반)",
            })

    # 비전 정의 형식 검증: "비전 = ..." 으로 시작하면 인용 부호 필수
    if re.search(r"비전\s*=\s*[가-힣]", norm) and "*가치 있는 시대적 소명*" not in norm:
        violations.append({
            "term": "비전 = ...",
            "reason": "비전 정의는 박사님 원문 인용으로만 표기 — '가치 있는 시대적 소명' 형식 준수",
        })

    return {"clean": len(violations) == 0, "violations": violations}


# ---------------------------------------------------------------------------
# 9. 연계 스킬 추천 (사용자 상태에 따라)
# ---------------------------------------------------------------------------

LINKED_SKILLS: dict[str, list[dict[str, str]]] = {
    "spiritual": [
        {
            "skill": "vision-clarity-coaching",
            "reason": "영적 직관력 약화 시 비전 핵심 한 문장 재발견에 도움",
        },
        {
            "skill": "vision-three-realm-balance",
            "reason": "정신적 가치 검증·3겹 균형 재점검",
        },
    ],
    "rational": [
        {
            "skill": "vision-cys-competence-visioncoding",
            "reason": "자기 내적 정보(역량·관심·재능) 정밀 수집",
        },
        {
            "skill": "vision-mbti-visioncoding",
            "reason": "성격 기반 자기 이해 정보 수집",
        },
        {
            "skill": "vision-enneagram-visioncoding",
            "reason": "기질 기반 자기 이해 정보 수집",
        },
        {
            "skill": "vision-readiness-visioncoding",
            "reason": "비전 준비도(자기 이해 정보) 점검",
        },
        {
            "skill": "vision-futures-timeline-map",
            "reason": "예측 구성(Forecasting Framework)을 미래지도로 구체화",
        },
        {
            "skill": "vision-four-futures",
            "reason": "4가지 미래 가능성으로 예측 구성 정교화",
        },
        {
            "skill": "vision-future-needs-prediction",
            "reason": "미래 필요 예측을 예측 구성에 입력",
        },
    ],
    "post_frame": [
        {
            "skill": "vision-statement-writer",
            "reason": "프레임 점검 결과를 비전 선언문으로 정식화",
        },
        {
            "skill": "vision-five-stages",
            "reason": "박사님 미래준비학교 5단계의 디자인(2단계)에서 본 스킬 연결",
        },
    ],
}


def recommend_linked_skills(weak_axis: str | None = None, mode: str = "diagnostic") -> list[dict[str, str]]:
    """약한 축 또는 모드에 따라 연계 스킬을 결정론적으로 추천.

    weak_axis ∈ {"spiritual", "rational", None}.
    mode ∈ {"diagnostic", "post_frame", "both"}.
    """
    recs: list[dict[str, str]] = []
    if weak_axis in ("spiritual", "rational"):
        recs.extend(LINKED_SKILLS[weak_axis])
    elif weak_axis is None:
        recs.extend(LINKED_SKILLS["spiritual"])
        recs.extend(LINKED_SKILLS["rational"])
    if mode in ("post_frame", "both"):
        recs.extend(LINKED_SKILLS["post_frame"])
    # 중복 제거 (skill 키 기준)
    seen: set[str] = set()
    deduped: list[dict[str, str]] = []
    for r in recs:
        if r["skill"] in seen:
            continue
        seen.add(r["skill"])
        deduped.append(r)
    return deduped


# ---------------------------------------------------------------------------
# 10. 출력 양식 검증 (6단계 보고서)
# ---------------------------------------------------------------------------

REPORT_REQUIRED_SECTIONS: tuple[str, ...] = (
    "비전 프레임 점검 보고서",
    "영적 직관력",
    "영감",
    "정신적 가치",
    "비전 영역 3겹 교집합",
    "이성적 판단력",
    "자기 내적 정보",
    "자기 외적 정보",
    "예측 구성",
    "(R) 강화 피드백 루프",
    "강한 축",
    "약한 축",
    "정교화된 비전 한 문장",
    "가치 있는",
    "시대적",
    "소명",
)


def validate_report_structure(report_text: str, partial: bool = False) -> dict[str, Any]:
    """6단계 보고서가 SKILL.md 양식을 따르는지 검증.

    partial=True 면 부분 점검 모드(유형 B/C)에서 일부 섹션 누락 허용.
    """
    if not report_text:
        return {"valid": False, "missing": list(REPORT_REQUIRED_SECTIONS), "reason": "빈 보고서"}

    missing: list[str] = []
    for sec in REPORT_REQUIRED_SECTIONS:
        if sec not in report_text:
            missing.append(sec)

    if partial:
        # 부분 모드: 헤더·비전 한 문장만 필수
        critical = ("비전 프레임 점검 보고서", "정교화된 비전 한 문장")
        crit_missing = [s for s in critical if s in missing]
        return {
            "valid": len(crit_missing) == 0,
            "missing": missing,
            "critical_missing": crit_missing,
            "mode": "partial",
        }

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "mode": "full",
    }


# ---------------------------------------------------------------------------
# 11. 이모지 절제 검사 (SKILL.md 톤·스타일)
# ---------------------------------------------------------------------------

# SKILL.md "이모지 절제 — 핵심 도식에만"
# 허용 표지: 도식의 화살표·체크 표지
ALLOWED_DIAGRAM_CHARS = set("↑↓→←↗↘↖↙○△✗")


def emoji_check(text: str, max_emojis: int = 0) -> dict[str, Any]:
    """이모지 사용을 검사 (도식 외 사용 금지).

    max_emojis: 도식 외 이모지 허용 한도 (기본 0).
    """
    if not text:
        return {"clean": True, "count": 0, "found": []}

    found: list[str] = []
    for ch in text:
        cp = ord(ch)
        # Unicode 이모지 범위 (기본)
        if (
            0x1F300 <= cp <= 0x1FAFF or
            0x2600 <= cp <= 0x27BF or
            0x1F000 <= cp <= 0x1F2FF
        ):
            if ch not in ALLOWED_DIAGRAM_CHARS:
                found.append(ch)
    return {
        "clean": len(found) <= max_emojis,
        "count": len(found),
        "found": found,
        "policy": "도식 외 이모지 0개 (SKILL.md 톤·스타일)",
    }


# ---------------------------------------------------------------------------
# 12. 보고서 골격 생성 (결정론)
# ---------------------------------------------------------------------------

def format_report_skeleton(
    honorific: str = "박사님",
    input_type: str = "A",
) -> str:
    """SKILL.md 6단계 보고서 골격을 결정론으로 생성."""
    if input_type == "C":
        return _skeleton_loop_only(honorific)
    if input_type.startswith("B"):
        return _skeleton_partial(honorific, input_type)
    return _skeleton_full(honorific)


def _skeleton_full(honorific: str) -> str:
    return f"""# {honorific} 비전 프레임 점검 보고서

> 인용 (박사님 책): *"비전 프레임이란 '가치 있는 + 시대적 + 소명'이 어떻게 성장하는지를 설명하기 위해 필자가 만든 단어이다."*

## 영적 직관력 (Spiritual Intuition)
- 영감(Divine Inspiration): [통로 + 내용]
- 정신적 가치(Divine Value): [경전/윤리 검증 결과 + 안전장치]

## 비전 영역 3겹 교집합
- 자신({honorific}) 진정한 기쁨? ○/△/✗
- 가족·이웃·세상에 기쁨·가치? ○/△/✗
- 정신적·도덕적 가치? ○/△/✗
- 세 영역 교집합 비전 영역: [한 문장]

## 이성적 판단력 (Intellectual Judgment) / 미래 변화 통찰
- 자기 내적 정보: [관심·재능·성격·가치관]
- 자기 외적 정보: [사람·관계·환경·과거 경험]
- 예측 구성(미래지도): [핵심 미래 변화]

## (R) 강화 피드백 루프
- 강한 축: [영적 직관력 / 이성적 판단력 / 균형]
- 약한 축: [영적 직관력 / 이성적 판단력 / 없음]
- 약화 증상: ___
- 강화 방향: ___

## 정교화된 비전 한 문장
> "가치 있는(___) 시대적(___) 소명(___)"
"""


def _skeleton_partial(honorific: str, input_type: str) -> str:
    axis_label = "영적 직관력" if input_type == "B-spiritual" else "이성적 판단력"
    return f"""# {honorific} 비전 프레임 점검 보고서 ({axis_label} 축만)

> 인용 (박사님 책): *"비전 프레임이란 '가치 있는 + 시대적 + 소명'이 어떻게 성장하는지를 설명하기 위해 필자가 만든 단어이다."*

## {axis_label}
- [축 구성요소별 진단]

## 정교화된 비전 한 문장
> "가치 있는(___) 시대적(___) 소명(___)"

## 추가 권고
- 다른 축은 별도 점검 권장 — 두 축이 (R) 강화 피드백 루프로 함께 작동할 때 비전이 정교해짐
"""


def _skeleton_loop_only(honorific: str) -> str:
    return f"""# {honorific} 비전 프레임 점검 보고서 ((R) 강화 피드백 루프 진단)

> 인용 (박사님 책): *"비전 프레임이란 '가치 있는 + 시대적 + 소명'이 어떻게 성장하는지를 설명하기 위해 필자가 만든 단어이다."*

## (R) 강화 피드백 루프 진단
- 강한 축: [영적 직관력 / 이성적 판단력 / 균형]
- 약한 축: [영적 직관력 / 이성적 판단력 / 없음]
- 약화 증상: ___
- 강화 방향: ___
- 박사님 비유: *"마이크로 들어간 소리가 더 커져서 스피커로 나오는 것 같은 증가형 강화 피드백"*

## 정교화된 비전 한 문장
> "가치 있는(___) 시대적(___) 소명(___)"
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mission_frame_lib", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    # honorific
    p = sub.add_parser("honorific")
    p.add_argument("--doctor", default="false")
    p.add_argument("--title", default="")
    p.add_argument("--name", default="")

    # classify_input
    p = sub.add_parser("classify_input")
    p.add_argument("--text", required=True)

    # detect_religion
    p = sub.add_parser("detect_religion")
    p.add_argument("--text", default="")
    p.add_argument("--explicit", default="")

    # list_quotes
    sub.add_parser("list_quotes")

    # verify_quote
    p = sub.add_parser("verify_quote")
    p.add_argument("--text", required=True)

    # map_definition
    p = sub.add_parser("map_definition")
    p.add_argument("--phrase", required=True)

    # three_realm
    p = sub.add_parser("three_realm")
    p.add_argument("--self", default="false")
    p.add_argument("--others", default="false")
    p.add_argument("--moral", default="false")

    # diagnose_loop
    p = sub.add_parser("diagnose_loop")
    p.add_argument("--spiritual", required=True, choices=STRENGTH_VALUES)
    p.add_argument("--rational", required=True, choices=STRENGTH_VALUES)

    # validate_report
    p = sub.add_parser("validate_report")
    p.add_argument("--file", default="")
    p.add_argument("--text", default="")
    p.add_argument("--partial", default="false")

    # detect_drift
    p = sub.add_parser("detect_drift")
    p.add_argument("--text", required=True)

    # recommend_skills
    p = sub.add_parser("recommend_skills")
    p.add_argument("--weak_axis", default="")
    p.add_argument("--mode", default="diagnostic")

    # emoji_check
    p = sub.add_parser("emoji_check")
    p.add_argument("--text", required=True)
    p.add_argument("--max", type=int, default=0)

    # format_report_skeleton
    p = sub.add_parser("format_report_skeleton")
    p.add_argument("--honorific", default="박사님")
    p.add_argument("--input_type", default="A")

    # stages_for_type
    p = sub.add_parser("stages_for_type")
    p.add_argument("--type", required=True)

    args = parser.parse_args(argv)

    def _b(v: str) -> bool:
        return str(v).lower() in ("1", "true", "yes", "y", "t")

    if args.cmd == "honorific":
        meta = {
            "is_doctor": _b(args.doctor),
            "title": args.title,
            "name": args.name,
        }
        print(select_honorific(meta))
        return 0

    if args.cmd == "classify_input":
        result = classify_input_type(args.text)
        _print_json({"input_type": result, "stages": stages_for_type(result)})
        return 0

    if args.cmd == "detect_religion":
        ctx = detect_religion_context(args.text, args.explicit or None)
        _print_json({"religion_context": ctx, "criterion": divine_value_criterion(ctx)})
        return 0

    if args.cmd == "list_quotes":
        _print_json({"count": len(AUTHORIZED_QUOTES), "quotes": list_authorized_quotes()})
        return 0

    if args.cmd == "verify_quote":
        _print_json(verify_quote(args.text))
        return 0

    if args.cmd == "map_definition":
        _print_json(map_vision_definition_phrase(args.phrase))
        return 0

    if args.cmd == "three_realm":
        _print_json(classify_three_realm_check(_b(args.self), _b(args.others), _b(args.moral)))
        return 0

    if args.cmd == "diagnose_loop":
        _print_json(diagnose_loop(args.spiritual, args.rational))
        return 0

    if args.cmd == "validate_report":
        if args.file:
            text = Path(args.file).read_text(encoding="utf-8")
        else:
            text = args.text or ""
        _print_json(validate_report_structure(text, partial=_b(args.partial)))
        return 0

    if args.cmd == "detect_drift":
        _print_json(detect_doctrinal_drift(args.text))
        return 0

    if args.cmd == "recommend_skills":
        wa = args.weak_axis or None
        _print_json(recommend_linked_skills(wa, args.mode))
        return 0

    if args.cmd == "emoji_check":
        _print_json(emoji_check(args.text, args.max))
        return 0

    if args.cmd == "format_report_skeleton":
        print(format_report_skeleton(args.honorific, args.input_type))
        return 0

    if args.cmd == "stages_for_type":
        _print_json({"input_type": args.type, "stages": stages_for_type(args.type)})
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
