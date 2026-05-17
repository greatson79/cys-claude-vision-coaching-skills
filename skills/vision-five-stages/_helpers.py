"""vision-five-stages 결정론 환원 헬퍼.

LLM 자연어 추론에 맡기면 할루시네이션 위험이 있는 영역을
순수 함수로 환원한다. SKILL.md의 워크플로우는 본 모듈을
호출하도록 강제된다(자연어로 다시 추론하지 않는다).

대상 작업:
- 입력 유형 분류 (A·B·C·D·E)
- 사용자 현재 단계 진단 (Stage 1~5)
- 1년 커리큘럼 주차 표 룩업
- 5단계 정식 명칭 검증 / 별칭 정규화
- 6대 행동 강령 키워드 매핑
- 미래 유망성 5기준 점수 합산·등급화
- SMART 5역량 토큰 검증
- 비전 훈련 8대 영역 토큰 검증
- 비전 재인식 시점 판정 (재실시 트리거)
- 사양 원문 인용 인덱스 (책 페이지·다이어그램)

설계 원칙:
- 모든 함수는 결정론(deterministic). 동일 입력 → 동일 출력.
- 외부 I/O 없음. 모든 데이터는 모듈 상수로 고정.
- "어림짐작" 매칭은 토큰 단위 정확 일치 + 정규화된 부분 문자열 매칭.
- 한국어·영어·로마자 표기를 모두 흡수.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple


# ============================================================
# 0. 데이터 상수 — 사양 원문 인용 (출처 명시)
# ============================================================
#
# 출처: 최윤식, 『미래준비학교』 (서울: 생명의 말씀사, 2016).
# 본 모듈의 표·명칭은 위 단행본의 표제 그대로다. 임의 가공·재명명 금지.
#
# 학계 주류 문헌 1:1 대조 (결정론 환원 불가능 항목용):
# - SMART 원칙: Doran, G. T. (1981). "There's a S.M.A.R.T. way to
#   write management's goals and objectives." Management Review,
#   70(11): 35-36.
# - 4 Futures (Plausible / Possible / Wildcard / Preferred):
#   Voros, J. (2003). "A generic foresight process framework."
#   Foresight, 5(3): 10-21.  +  Bezold, C. (2009). "Aspirational
#   Futures." Journal of Futures Studies, 13(4): 81-90.
# - Vision Network (비전 재생산): 비교 문헌 — Collins & Porras
#   (1996). "Building Your Company's Vision." Harvard Business
#   Review, 74(5): 65-77.

SPEC_SOURCE = (
    "최윤식, 『미래준비학교』 (서울: 생명의 말씀사, 2016)"
)

# 5단계 정식 명칭 표 (변형 금지 — 절대 원칙 1)
STAGE_NAMES: Dict[int, Dict[str, str]] = {
    1: {
        "ko": "비전 스케치",
        "sub": "자기 인식",
        "ko_full": "비전 스케치 (자기 인식)",
        "en": "Vision Sketch (Self-Awareness)",
        "purpose": "비전의 밑그림을 그려보는 단계 — 완벽이 아닌 대략 간추린 모양에 만족",
    },
    2: {
        "ko": "비전 디자인",
        "sub": "비전 발견",
        "ko_full": "비전 디자인 (비전 발견)",
        "en": "Vision Design (Vision Discovery)",
        "purpose": "깊은 성찰과 탐구를 거치며 좋은 선택과 결정을 하기 위한 시간",
    },
    3: {
        "ko": "비전 훈련",
        "sub": "",
        "ko_full": "비전 훈련",
        "en": "Vision Training",
        "purpose": "가치·세상·나에 대한 심층 탐구 + 비전 디자인 정교화 + 비전 역량 개발",
    },
    4: {
        "ko": "비전 재인식",
        "sub": "",
        "ko_full": "비전 재인식",
        "en": "Vision Re-Recognition",
        "purpose": "가치 향상 토론·CYS 비전 역량 재검사로 비전 재발견",
    },
    5: {
        "ko": "비전 재생산",
        "sub": "최고 경지",
        "ko_full": "비전 재생산 (최고 경지)",
        "en": "Vision Reproduction (Highest Stage)",
        "purpose": "비전 네트워크 구축 + 다른 사람을 비전가로 세움",
    },
}

# 별칭·오기 정규화 사전 (사용자 입력 흡수용)
STAGE_ALIAS: Dict[str, int] = {
    # Stage 1
    "비전스케치": 1, "비전 스케치": 1, "스케치": 1,
    "자기인식": 1, "자기 인식": 1, "self awareness": 1, "self-awareness": 1,
    "1단계": 1, "stage 1": 1, "stage1": 1, "1": 1, "단계1": 1,
    # Stage 2
    "비전디자인": 2, "비전 디자인": 2, "디자인": 2,
    "비전발견": 2, "비전 발견": 2, "vision design": 2,
    "2단계": 2, "stage 2": 2, "stage2": 2, "2": 2, "단계2": 2,
    "2-1": 2, "2-2": 2, "2-3": 2, "2-4": 2, "2-5": 2, "2-6": 2,
    # Stage 3
    "비전훈련": 3, "비전 훈련": 3, "훈련": 3,
    "vision training": 3,
    "3단계": 3, "stage 3": 3, "stage3": 3, "3": 3, "단계3": 3,
    # Stage 4
    "비전재인식": 4, "비전 재인식": 4, "재인식": 4,
    "vision re-recognition": 4,
    "4단계": 4, "stage 4": 4, "stage4": 4, "4": 4, "단계4": 4,
    # Stage 5
    "비전재생산": 5, "비전 재생산": 5, "재생산": 5,
    "vision reproduction": 5,
    "5단계": 5, "stage 5": 5, "stage5": 5, "5": 5, "단계5": 5,
    "최고경지": 5, "최고 경지": 5,
}

# 1년 커리큘럼 표 (52주). 출처: 박사님 책 미래준비학교 본문 표.
CURRICULUM_TABLE: List[Dict[str, object]] = [
    {
        "label": "1단계",
        "weeks": 5,
        "topic": "비전 중요성 이해 + CYS 검사 + 비전 선언문 초안",
        "textbook": "미래준비학교",
        "maps_to_stage": 1,
    },
    {
        "label": "2-1단계",
        "weeks": 8,
        "topic": "비전 스케치 — CYS 검사 심층 + 부의 정석",
        "textbook": "기회의 대이동, 부의 정석",
        "maps_to_stage": 1,
    },
    {
        "label": "2-2단계",
        "weeks": 12,
        "topic": "미래 자극 — Futures Wheel + 사업 영역 선정",
        "textbook": "2030 대담한 미래 1·2 등",
        "maps_to_stage": 2,
    },
    {
        "label": "3-1단계",
        "weeks": 5,
        "topic": "비전 디자인 + 미래지도 완성",
        "textbook": "—",
        "maps_to_stage": 2,
    },
    {
        "label": "3-2단계",
        "weeks": 12,
        "topic": "비전 심층 탐구 — 창업 시뮬레이션",
        "textbook": "비판적 사고",
        "maps_to_stage": 2,
    },
    {
        "label": "4단계",
        "weeks": 8,
        "topic": "비전 훈련 — SMART Habit",
        "textbook": "생각이 미래다, 미래학자의 통찰법",
        "maps_to_stage": 3,
    },
    {
        "label": "5단계",
        "weeks": 2,
        "topic": "비전 네트워킹·재생산",
        "textbook": "—",
        "maps_to_stage": 5,
    },
]

# 6대 행동 강령 정식 명칭 (변형 금지)
SIX_PRINCIPLES: List[Dict[str, str]] = [
    {"ko": "서두르지 마라", "en": "Take a Time"},
    {"ko": "멀리 보라", "en": "Foresee Futures"},
    {"ko": "비전을 품어라", "en": "Make a Vision"},
    {"ko": "계획을 짜라", "en": "Make a Plan"},
    {"ko": "어떻게 일할지 훈련하고 생각하라", "en": "Train and Think about How To Work"},
    {"ko": "작은 일을 소중하게 하라", "en": "Be Faithful with a Few Things"},
]

# 6대 행동 강령 키워드 사전 (사용자 발화 → 강령 매칭)
SIX_PRINCIPLE_KEYWORDS: Dict[int, List[str]] = {
    0: ["서두르", "조급", "급하", "느긋", "time", "여유"],
    1: ["멀리", "장기", "미래", "foresee", "통찰", "예측"],
    2: ["품", "vision", "비전", "꿈"],
    3: ["계획", "plan", "전략 짜"],
    4: ["훈련", "train", "어떻게 일", "방법"],
    5: ["작은 일", "사소", "소중", "충실", "faithful"],
}

# SMART 5역량 (Sense·Method·Art·Relationship·Technology)
SMART_FIVE: Dict[str, Dict[str, str]] = {
    "S": {"name": "Sense", "ko": "사물·현상 감각·판단·통찰력"},
    "M": {"name": "Method", "ko": "통합적·분석적 사고 + 체계적 업무"},
    "A": {"name": "Art", "ko": "장인의 지식·기술 + 예술적 상상력"},
    "R": {"name": "Relationship", "ko": "집단지성·대인관계·인격"},
    "T": {"name": "Technology", "ko": "최신 기술·기술지능"},
}

# 비전 훈련 8대 영역
EIGHT_TRAINING_AREAS: List[str] = [
    "균형 잡힌 영성",
    "건강한 사고",
    "좋은 언어",
    "좋은 관계",
    "효과적 학습",
    "효율적 실행",
    "지혜로운 재정 전략",
    "건강한 신체",
]

# 미래 유망성 5기준 (Stage 1 스케치 흐름의 필터)
FIVE_CRITERIA: List[str] = [
    "영향력",
    "행복성",
    "부 가능성",
    "지속가능성",
    "경쟁력",
]

# 4가지 미래 가능성 (Stage 2-2)
FOUR_FUTURES: List[Dict[str, str]] = [
    {"ko": "기본 미래", "en": "Plausible Future"},
    {"ko": "가능한 미래들", "en": "Possible Futures"},
    {"ko": "뜻밖의 미래", "en": "Wildcard Future"},
    {"ko": "바람직한 미래", "en": "Normative/Preferred Future"},
]

# Stage 2 비전 디자인 6개 작업
STAGE2_TASKS: List[str] = [
    "2-1 비전 프레임 이해",
    "2-2 4가지 미래 가능성 학습",
    "2-3 미래지도 + 또 다른 미래",
    "2-4 타겟팅",
    "2-5 비전 선언문 작성",
    "2-6 재정 전략 모델",
]

# 비전 재생산 단계의 3가지 활동
STAGE5_ACTIVITIES: List[str] = [
    "비전 네트워크 구축",
    "다른 사람을 비전가로 세움",
    "비전 코치 양성 (비전코치 · 시니어코치 · 마스터코치 3단계)",
]

# 입력 유형 (A·B·C·D·E)
INPUT_TYPES: Dict[str, str] = {
    "A": "박사님 5단계 풀 진행",
    "B": "특정 단계만 깊이 코칭",
    "C": "단계 진단 (어디 있는지 파악)",
    "D": "박사님 본인 점검 (단행본·강의·사역 5단계 적용)",
    "E": "강의·청년부 도구 (1년 커리큘럼 적용)",
}

# 입력 유형 분류 키워드
INPUT_TYPE_KEYWORDS: Dict[str, List[str]] = {
    "A": [
        "처음부터", "5단계 전부", "전체 진행", "풀 코스", "전체적",
        "1단계부터", "처음 시작", "통째로", "처음 비전",
    ],
    "B": [
        "stage", "단계만", "1단계 깊이", "2단계 깊이", "3단계 깊이",
        "4단계 깊이", "5단계 깊이", "비전 스케치만", "비전 디자인만",
        "비전 훈련만", "비전 재인식만", "비전 재생산만",
        "smart 훈련", "8대 영역", "타겟팅", "비전 선언문",
        "재정 전략", "이 단계만", "이 부분만",
    ],
    "C": [
        "어디 있", "어느 단계", "지금 나", "내 위치", "진단",
        "어디쯤", "몇 단계", "어디까지 왔",
    ],
    "D": [
        "박사님 본인", "박사님 점검", "박사님 사역", "박사님 단행본",
        "박사님 강의", "내 사역", "내 단행본", "본인 점검",
        "자기 점검",
    ],
    "E": [
        "청년부", "셀모임", "강의 도구", "커리큘럼", "1년 과정",
        "52주", "주차", "학기", "신학교 강의", "교회 청년",
    ],
}


# ============================================================
# 유틸 — 텍스트 정규화
# ============================================================

def _normalize(text: str) -> str:
    """대소문자·공백·유니코드 정규화."""
    if not text:
        return ""
    s = unicodedata.normalize("NFC", text)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ============================================================
# 1. 입력 유형 분류기 (A/B/C/D/E)
# ============================================================

def classify_input_type(text: str) -> Dict[str, object]:
    """사용자 입력을 결정론으로 A~E 유형 분류.

    Returns:
        {
          "type": "A"|"B"|"C"|"D"|"E"|"UNKNOWN",
          "scores": {"A": int, ...},
          "matched_keywords": {"A": [...], ...},
          "description": str,
          "source": str
        }
    """
    if text is None:
        text = ""
    n = _normalize(text)
    scores: Dict[str, int] = {k: 0 for k in INPUT_TYPES}
    matched: Dict[str, List[str]] = {k: [] for k in INPUT_TYPES}

    if not n:
        return {
            "type": "UNKNOWN",
            "scores": scores,
            "matched_keywords": matched,
            "description": "빈 입력 — 사용자 요청이 비어 있습니다. 명확화 질문 필요",
            "source": "_helpers.classify_input_type — empty input",
        }

    for itype, kws in INPUT_TYPE_KEYWORDS.items():
        for kw in kws:
            if _normalize(kw) in n:
                scores[itype] += 1
                matched[itype].append(kw)

    max_score = max(scores.values())
    if max_score == 0:
        chosen = "UNKNOWN"
        desc = "키워드 매칭 실패 — 명확화 질문 필요"
    else:
        # 동점 시 우선순위: C > D > E > B > A
        # (진단·점검·커리큘럼 의도가 풀 진행보다 명시적)
        priority = ["C", "D", "E", "B", "A"]
        top = [t for t in priority if scores[t] == max_score]
        chosen = top[0]
        desc = INPUT_TYPES[chosen]

    return {
        "type": chosen,
        "scores": scores,
        "matched_keywords": matched,
        "description": desc,
        "source": "_helpers.classify_input_type — deterministic keyword map",
    }


# ============================================================
# 2. 단계 진단기 (Stage 1~5)
# ============================================================

# 단계 진단용 상태 토큰
STAGE_DIAGNOSIS_KEYWORDS: Dict[int, List[str]] = {
    1: [
        "처음", "비전 없", "막막", "관심사 모름", "역량 모름",
        "자기 이해 부족", "가치 모름", "스케치", "밑그림", "자존감",
        "cys 검사 안 함", "비전 시작",
    ],
    2: [
        "밑그림 있", "스케치 끝", "디자인", "비전 선언문", "타겟팅",
        "미래지도", "4가지 미래", "재정 전략", "선언문 작성",
        "비전 정교화", "프레임",
    ],
    3: [
        "디자인 끝", "선언문 완성", "훈련 필요", "smart 훈련",
        "8대 영역", "역량 개발", "실행력", "리더십 훈련",
        "비전 훈련 시작",
    ],
    4: [
        "훈련 일정 기간", "1년 지", "재인식", "재발견",
        "재검사", "가치 향상 토론", "비전 점검",
        "비전 코드 평가",
    ],
    5: [
        "훈련 완성", "비전 확장", "네트워크 구축", "비전가 양성",
        "재생산", "최고 경지", "비전 코치", "시니어 코치",
        "마스터 코치", "다른 사람 비전",
    ],
}


def diagnose_stage(state_text: str) -> Dict[str, object]:
    """사용자 상태 기술 → Stage 1~5 결정론 매핑.

    Returns:
        {
          "stage": int (1~5) | 0 (UNKNOWN),
          "stage_name": str,
          "scores": {1: int, ...},
          "matched_signals": {1: [...], ...},
          "source": str
        }
    """
    if state_text is None:
        state_text = ""
    n = _normalize(state_text)
    scores: Dict[int, int] = {s: 0 for s in STAGE_DIAGNOSIS_KEYWORDS}
    matched: Dict[int, List[str]] = {s: [] for s in STAGE_DIAGNOSIS_KEYWORDS}

    if not n:
        return {
            "stage": 0,
            "stage_name": "UNKNOWN — 빈 입력. 상태 기술 필요",
            "scores": scores,
            "matched_signals": matched,
            "source": "_helpers.diagnose_stage — empty input",
        }

    for stage, signals in STAGE_DIAGNOSIS_KEYWORDS.items():
        for sig in signals:
            if _normalize(sig) in n:
                scores[stage] += 1
                matched[stage].append(sig)

    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        return {
            "stage": 0,
            "stage_name": "UNKNOWN — 단계 진단을 위해 더 많은 정보 필요",
            "scores": scores,
            "matched_signals": matched,
            "ambiguous": False,
            "tied_stages": [],
            "source": "_helpers.diagnose_stage — deterministic signal map",
        }

    # 동점 시 *높은* 단계가 더 명시적 신호 (디자인 끝 + 훈련 필요 = Stage 3)
    tied = [s for s in scores if scores[s] == max_score]
    top = max(tied, default=0)
    ambiguous = len(tied) > 1

    return {
        "stage": top,
        "stage_name": STAGE_NAMES[top]["ko_full"],
        "scores": scores,
        "matched_signals": matched,
        "ambiguous": ambiguous,
        "tied_stages": tied,
        "ambiguity_note": (
            f"동점 신호 {tied} — 더 높은 단계({top})로 결정. "
            "사용자에게 명확화 질문 권장."
        ) if ambiguous else "",
        "source": "_helpers.diagnose_stage — deterministic signal map",
    }


# ============================================================
# 3. 1년 커리큘럼 주차 룩업
# ============================================================

def lookup_curriculum(label_or_stage: str | int) -> Dict[str, object]:
    """1년 커리큘럼 표 룩업 — 결정론.

    Args:
        label_or_stage: "1단계" / "2-1단계" / 1 / 2 / "5단계" 등

    Returns:
        정확 매칭 시 단일 행:
            {"found": True, "row": {...}, "rows": [{...}], ...}
        부모 레벨 매칭 시 (예: "2단계" → "2-1단계","2-2단계"):
            {"found": True, "row": None, "rows": [{...},{...}], ...}
        매칭 없을 시:
            {"found": False, "row": None, "rows": [], "error": ..., ...}
    """
    if label_or_stage is None:
        return {
            "found": False,
            "row": None,
            "rows": [],
            "error": "입력이 None — 라벨 또는 단계 정수가 필요합니다.",
            "source": "_helpers.lookup_curriculum — None input",
        }

    if isinstance(label_or_stage, int):
        key = f"{label_or_stage}단계"
    else:
        key = _normalize(label_or_stage)
        if not key:
            return {
                "found": False,
                "row": None,
                "rows": [],
                "error": "빈 입력 — 라벨 또는 단계 정수가 필요합니다.",
                "source": "_helpers.lookup_curriculum — empty input",
            }

    # 1순위: 라벨 정확 일치
    for row in CURRICULUM_TABLE:
        if _normalize(row["label"]) == key:
            return {
                "found": True,
                "row": row,
                "rows": [row],
                "error": None,
                "source": f"{SPEC_SOURCE} — 1년 커리큘럼 표",
            }

    # 2순위: 부모 레벨 접두 매칭 (예: "2단계" → "2-1단계", "2-2단계")
    # "N단계" 형태 입력만 부모 접두로 인정 (오용 방지)
    m = re.fullmatch(r"(\d+)단계", key)
    if m:
        prefix = f"{m.group(1)}-"
        matched_rows = [r for r in CURRICULUM_TABLE
                        if _normalize(r["label"]).startswith(prefix)]
        if matched_rows:
            total_weeks = sum(r["weeks"] for r in matched_rows)  # type: ignore
            return {
                "found": True,
                "row": None,
                "rows": matched_rows,
                "matched_as": "parent_prefix",
                "total_weeks_of_parent": total_weeks,
                "error": None,
                "source": f"{SPEC_SOURCE} — 1년 커리큘럼 표 (부모 단계 접두 매칭)",
            }

    return {
        "found": False,
        "row": None,
        "rows": [],
        "error": f"'{label_or_stage}'에 해당하는 커리큘럼 라벨 없음 — 가능 라벨: "
                 + ", ".join(r["label"] for r in CURRICULUM_TABLE),
        "source": "_helpers.lookup_curriculum",
    }


def total_curriculum_weeks() -> int:
    """52주 총합 검증."""
    return sum(row["weeks"] for row in CURRICULUM_TABLE)  # type: ignore


# ============================================================
# 4. 5단계 정식 명칭 검증·정규화
# ============================================================

def normalize_stage_name(text: str) -> Dict[str, object]:
    """입력 문자열을 5단계 표준 명칭으로 정규화.

    Returns:
        {
          "found": bool,
          "stage": int | 0,
          "official_name": str | None,
          "purpose": str | None,
          "source": str
        }
    """
    if text is None:
        n = ""
    else:
        n = _normalize(text)

    # 빈/과도하게 짧은 입력 거부 (false-positive 부분 매칭 차단)
    if not n or len(n) < 1:
        return {
            "found": False,
            "stage": 0,
            "official_name": None,
            "purpose": None,
            "source": "_helpers.normalize_stage_name — empty input rejected",
        }

    # 1순위: 정확 일치
    if n in STAGE_ALIAS:
        s = STAGE_ALIAS[n]
        return {
            "found": True,
            "stage": s,
            "official_name": STAGE_NAMES[s]["ko_full"],
            "purpose": STAGE_NAMES[s]["purpose"],
            "source": f"{SPEC_SOURCE} — 5단계 명칭표",
        }

    # 1.5순위: "N단계" / "stage N" / "단계N" 같은 숫자 패턴은 정확 일치만 허용
    # (예: "10단계"가 "1단계"에 부분 매칭되는 false-positive 차단)
    num_patterns = [
        r"(\d+)\s*단계",
        r"stage\s*(\d+)",
        r"단계\s*(\d+)",
    ]
    for pat in num_patterns:
        m = re.fullmatch(pat, n)
        if m:
            try:
                num = int(m.group(1))
            except ValueError:
                num = -1
            if 1 <= num <= 5:
                # 이미 STAGE_ALIAS에 있어야 하지만 방어적으로 처리
                return {
                    "found": True,
                    "stage": num,
                    "official_name": STAGE_NAMES[num]["ko_full"],
                    "purpose": STAGE_NAMES[num]["purpose"],
                    "source": f"{SPEC_SOURCE} — 5단계 명칭표 (숫자 정확 매칭)",
                }
            # 1~5 범위 밖이면 매칭 실패로 즉시 종료 (부분 매칭 진입 차단)
            return {
                "found": False,
                "stage": 0,
                "official_name": None,
                "purpose": None,
                "source": (
                    f"_helpers.normalize_stage_name — 숫자 {num} 는 5단계 범위 밖"
                ),
            }

    # 2순위: 부분 매칭 — 단 *숫자 alias는 제외*. 숫자 alias는 정확 일치만 인정.
    for alias, s in STAGE_ALIAS.items():
        # 순수 숫자 alias("1","2","3","4","5") 또는 N단계 alias는 위에서 처리.
        # 여기서는 텍스트 alias만 부분 매칭 대상.
        if re.fullmatch(r"\d+(단계)?", alias):
            continue
        if re.fullmatch(r"stage\s*\d+", alias):
            continue
        # 입력이 더 긴 경우 — n 안에 alias가 통째로 포함
        if len(n) >= 2 and alias in n and len(alias) >= 2:
            return {
                "found": True,
                "stage": s,
                "official_name": STAGE_NAMES[s]["ko_full"],
                "purpose": STAGE_NAMES[s]["purpose"],
                "source": f"{SPEC_SOURCE} — 5단계 명칭표 (부분 매칭)",
            }
        # 입력이 더 짧은 경우 — alias 안에 n이 포함되되 n이 alias의 절반 이상
        if len(n) >= 2 and n in alias and len(n) * 2 >= len(alias):
            return {
                "found": True,
                "stage": s,
                "official_name": STAGE_NAMES[s]["ko_full"],
                "purpose": STAGE_NAMES[s]["purpose"],
                "source": f"{SPEC_SOURCE} — 5단계 명칭표 (부분 매칭)",
            }
    return {
        "found": False,
        "stage": 0,
        "official_name": None,
        "purpose": None,
        "source": "_helpers.normalize_stage_name — no match",
    }


def validate_stage_order(seq: List[str]) -> Dict[str, object]:
    """입력된 단계 시퀀스가 1→2→3→4→5 순서와 일치하는지 검증.

    Returns:
        {"valid": bool, "expected": [...], "got": [...], "first_mismatch_idx": int | None}
    """
    expected = [STAGE_NAMES[i]["ko"] for i in range(1, 6)]
    got: List[str] = []
    for s in seq:
        r = normalize_stage_name(s)
        if r["found"]:
            got.append(STAGE_NAMES[r["stage"]]["ko"])  # type: ignore
        else:
            got.append(f"UNKNOWN({s})")

    first_mismatch = None
    for i, (e, g) in enumerate(zip(expected, got)):
        if e != g:
            first_mismatch = i
            break

    return {
        "valid": got == expected,
        "expected": expected,
        "got": got,
        "first_mismatch_idx": first_mismatch,
        "source": "_helpers.validate_stage_order",
    }


# ============================================================
# 5. 6대 행동 강령 매핑
# ============================================================

def match_six_principles(action_text: str) -> Dict[str, object]:
    """행동 발화 → 6대 행동 강령 매칭.

    Returns:
        {
          "matches": [{"idx": int, "ko": str, "en": str, "matched_keywords": [...]}],
          "source": str
        }
    """
    if action_text is None:
        action_text = ""
    n = _normalize(action_text)
    if not n:
        return {
            "matches": [],
            "source": f"{SPEC_SOURCE} — 박사님 6대 행동 강령 (빈 입력)",
        }
    matches: List[Dict[str, object]] = []
    for idx, kws in SIX_PRINCIPLE_KEYWORDS.items():
        mk = [kw for kw in kws if _normalize(kw) in n]
        if mk:
            matches.append({
                "idx": idx + 1,
                "ko": SIX_PRINCIPLES[idx]["ko"],
                "en": SIX_PRINCIPLES[idx]["en"],
                "matched_keywords": mk,
            })
    return {
        "matches": matches,
        "source": f"{SPEC_SOURCE} — 박사님 6대 행동 강령",
    }


def lookup_principle(idx_or_name: int | str) -> Dict[str, object]:
    """6대 행동 강령 단건 룩업.

    Args:
        idx_or_name: 1~6 인덱스 또는 한글/영문 명칭

    Returns:
        {"found": bool, "idx": int, "ko": str, "en": str, "source": str}
    """
    if isinstance(idx_or_name, int):
        if 1 <= idx_or_name <= 6:
            p = SIX_PRINCIPLES[idx_or_name - 1]
            return {"found": True, "idx": idx_or_name, "ko": p["ko"],
                    "en": p["en"], "source": f"{SPEC_SOURCE} — 6대 강령"}
        return {"found": False, "idx": 0, "ko": "", "en": "",
                "source": "out of range (1-6)"}

    if idx_or_name is None:
        return {"found": False, "idx": 0, "ko": "", "en": "",
                "source": "_helpers.lookup_principle — None input"}

    n = _normalize(idx_or_name)
    # 빈/과도하게 짧은 입력 거부 (false-positive 부분 매칭 차단)
    if not n or len(n) < 2:
        return {"found": False, "idx": 0, "ko": "", "en": "",
                "source": "_helpers.lookup_principle — empty/too-short input"}

    for i, p in enumerate(SIX_PRINCIPLES):
        ko_n = _normalize(p["ko"])
        en_n = _normalize(p["en"])
        # n 안에 강령이 통째로 포함되거나, 강령 안에 n이 통째로 포함되되
        # n 길이가 강령 길이의 절반 이상일 때만 매칭
        if ko_n in n or en_n in n:
            return {"found": True, "idx": i + 1, "ko": p["ko"],
                    "en": p["en"], "source": f"{SPEC_SOURCE} — 6대 강령"}
        if (n in ko_n and len(n) * 2 >= len(ko_n)) \
                or (n in en_n and len(n) * 2 >= len(en_n)):
            return {"found": True, "idx": i + 1, "ko": p["ko"],
                    "en": p["en"], "source": f"{SPEC_SOURCE} — 6대 강령"}
    return {"found": False, "idx": 0, "ko": "", "en": "",
            "source": "_helpers.lookup_principle — no match"}


# ============================================================
# 6. 미래 유망성 5기준 점수 합산·등급화
# ============================================================

def score_five_criteria(scores: Dict[str, int]) -> Dict[str, object]:
    """5기준(영향력·행복성·부 가능성·지속가능성·경쟁력) 점수 합산.

    각 기준 1-5점. 산출: 합계, 평균, 등급, 결여 기준 목록.

    Returns:
        {
          "valid": bool,
          "sum": int,
          "avg": float,
          "grade": str,  # "S"·"A"·"B"·"C"·"D"
          "missing": [...],
          "out_of_range": [...],
          "source": str
        }
    """
    missing = [c for c in FIVE_CRITERIA if c not in scores]
    out_of_range: List[str] = []
    s = 0
    for c in FIVE_CRITERIA:
        if c not in scores:
            continue
        v = scores[c]
        if not isinstance(v, int) or v < 1 or v > 5:
            out_of_range.append(f"{c}={v}")
            continue
        s += v

    if missing or out_of_range:
        return {
            "valid": False,
            "sum": 0,
            "avg": 0.0,
            "grade": "INVALID",
            "missing": missing,
            "out_of_range": out_of_range,
            "source": "_helpers.score_five_criteria",
        }

    avg = s / 5.0
    # 등급 기준 (결정론 임계값)
    if avg >= 4.5:
        grade = "S"
    elif avg >= 4.0:
        grade = "A"
    elif avg >= 3.0:
        grade = "B"
    elif avg >= 2.0:
        grade = "C"
    else:
        grade = "D"

    return {
        "valid": True,
        "sum": s,
        "avg": round(avg, 2),
        "grade": grade,
        "missing": [],
        "out_of_range": [],
        "source": f"{SPEC_SOURCE} — Stage 1 스케치 흐름 5기준",
    }


# ============================================================
# 7. SMART 5역량 토큰 검증
# ============================================================

def validate_smart_tokens(tokens: List[str]) -> Dict[str, object]:
    """SMART 토큰 시퀀스 검증."""
    expected = list(SMART_FIVE.keys())  # S M A R T
    got_letters = [t.strip().upper()[:1] for t in tokens]
    valid = got_letters == expected
    return {
        "valid": valid,
        "expected": expected,
        "got": got_letters,
        "source": f"{SPEC_SOURCE} — Stage 3 SMART 5역량",
    }


def get_smart_full(letter: str) -> Dict[str, object]:
    """SMART 단일 글자 → 전체 정의."""
    L = letter.strip().upper()[:1]
    if L in SMART_FIVE:
        d = SMART_FIVE[L]
        return {"found": True, "letter": L, "name": d["name"],
                "ko": d["ko"], "source": f"{SPEC_SOURCE} — SMART 5역량"}
    return {"found": False, "letter": L, "name": "", "ko": "",
            "source": "_helpers.get_smart_full — invalid letter"}


# ============================================================
# 8. 8대 훈련 영역 검증
# ============================================================

def validate_eight_areas(areas: List[str]) -> Dict[str, object]:
    """8대 훈련 영역 검증 — 명칭 일치성·중복 검사.

    None·비문자열 항목은 invalid_items로 분리 보고.
    """
    if areas is None:
        areas = []

    invalid_items: List[object] = []
    clean_areas: List[str] = []
    for a in areas:
        if a is None or not isinstance(a, str) or not a.strip():
            invalid_items.append(a)
        else:
            clean_areas.append(a)

    norm_input = [_normalize(a) for a in clean_areas]
    norm_expected = [_normalize(a) for a in EIGHT_TRAINING_AREAS]

    missing = [a for a in EIGHT_TRAINING_AREAS
               if _normalize(a) not in norm_input]
    extra = [a for a in clean_areas if _normalize(a) not in norm_expected]
    duplicates = [a for a in clean_areas
                  if norm_input.count(_normalize(a)) > 1]

    return {
        "valid": (
            len(missing) == 0
            and len(extra) == 0
            and len(duplicates) == 0
            and len(invalid_items) == 0
        ),
        "missing": missing,
        "extra": extra,
        "duplicates": list(set(duplicates)),
        "invalid_items": invalid_items,
        "expected_count": 8,
        "got_count": len(clean_areas),
        "source": f"{SPEC_SOURCE} — 비전 훈련 8대 영역",
    }


# ============================================================
# 9. 비전 재인식 시점 판정 (Stage 4 트리거)
# ============================================================

def should_trigger_reracognition(
    months_since_training_start: int,
    value_change: bool = False,
    env_change: bool = False,
    new_data_accumulated: bool = False,
) -> Dict[str, object]:
    """Stage 4 (비전 재인식) 트리거 판정.

    박사님 책 기준:
    - 비전 훈련 일정 기간 후 (1년 1회 권장)
    - 가치 변화·환경 변화 발생 시
    - 비전 디자인 단계 이후 새로운 자료 누적 시
    """
    # 입력 검증
    if not isinstance(months_since_training_start, int):
        return {
            "trigger": False,
            "reasons": [],
            "recommendation": "",
            "valid": False,
            "error": (
                f"months_since_training_start는 정수여야 합니다 "
                f"(받은 값: {months_since_training_start!r})"
            ),
            "source": "_helpers.should_trigger_reracognition — invalid input",
        }
    if months_since_training_start < 0:
        return {
            "trigger": False,
            "reasons": [],
            "recommendation": "",
            "valid": False,
            "error": (
                f"months_since_training_start는 0 이상이어야 합니다 "
                f"(받은 값: {months_since_training_start}). "
                "훈련 시작 전이라면 Stage 3을 먼저 진행하세요."
            ),
            "source": "_helpers.should_trigger_reracognition — negative input",
        }
    # 비현실적 큰 값에는 경고만 (계산은 진행)
    overflow_warning = (
        f"입력 month={months_since_training_start}이(가) 비정상적으로 큽니다."
        if months_since_training_start > 1200 else None
    )

    reasons: List[str] = []
    if months_since_training_start >= 12:
        reasons.append("훈련 시작 후 12개월 경과 — 1년 1회 정기 재인식 시점")
    if value_change:
        reasons.append("가치 변화 발생")
    if env_change:
        reasons.append("환경 변화 발생")
    if new_data_accumulated:
        reasons.append("새로운 자료 누적")

    if reasons:
        recommendation = (
            "재인식 단계(Stage 4) 진입 권장 — 가치 향상 토론·CYS 재검사·비전 정교화"
        )
    else:
        months_until = max(0, 12 - months_since_training_start)
        recommendation = (
            f"아직 정기 재인식 시점 아님 — 정기 시점까지 약 {months_until}개월 남음. "
            "그 사이 가치/환경 변화나 새 자료 누적이 발생하면 즉시 트리거."
        )

    result: Dict[str, object] = {
        "trigger": len(reasons) > 0,
        "reasons": reasons,
        "recommendation": recommendation,
        "valid": True,
        "input": {
            "months_since_training_start": months_since_training_start,
            "value_change": value_change,
            "env_change": env_change,
            "new_data_accumulated": new_data_accumulated,
        },
        "source": f"{SPEC_SOURCE} — Stage 4 재인식 시점",
    }
    if overflow_warning:
        result["warning"] = overflow_warning
    return result


# ============================================================
# 9b. 혼동 패턴 감지 (결정론 — SKILL.md 오류·예외처리 표 자동화)
# ============================================================

# Doran(1981) SMART 두문자 패턴
DORAN_SMART_TOKENS: List[str] = [
    "specific", "measurable", "assignable", "achievable",
    "realistic", "relevant", "time-related", "time-bound", "timely",
]

# vision-strategy-coach 일반 5단계 패턴
GENERAL_5STAGE_TOKENS: List[str] = [
    "비전 핵심", "비전핵심", "장기 목표", "단기 목표",
    "행동 계획", "측정 평가", "vision to action",
    "비전핵심 식별", "long-term goals", "short-term goals",
    "action plan",
]


def detect_doran_smart_confusion(text: str) -> Dict[str, object]:
    """Doran(1981) SMART 두문자 혼동 발화 감지.

    Returns:
        {
          "is_doran_pattern": bool,
          "matched_tokens": [...],
          "advisory": str,
          "source": str
        }
    """
    n = _normalize(text)
    matched = [t for t in DORAN_SMART_TOKENS if _normalize(t) in n]
    is_doran = len(matched) >= 2
    advisory = ""
    if is_doran:
        advisory = (
            "박사님 SMART(Sense·Method·Art·Relationship·Technology)와 "
            "Doran(1981) SMART(Specific·Measurable·Assignable·Realistic·Time-related)는 "
            "두문자만 같고 의미가 다릅니다. 본 스킬은 박사님 SMART를 다루며, "
            "Doran SMART는 vision-strategy-coach에서 다룹니다."
        )
    return {
        "is_doran_pattern": is_doran,
        "matched_tokens": matched,
        "advisory": advisory,
        "source": f"{SPEC_SOURCE} (박사님 SMART) vs Doran (1981) Management Review 70(11):35-36 (일반 SMART)",
    }


def detect_general_5stage_confusion(text: str) -> Dict[str, object]:
    """vision-strategy-coach 일반 5단계 발화 감지."""
    n = _normalize(text)
    matched = [t for t in GENERAL_5STAGE_TOKENS if _normalize(t) in n]
    is_general = len(matched) >= 1
    advisory = ""
    if is_general:
        advisory = (
            "그 5단계는 vision-strategy-coach의 일반 5단계(비전핵심→장기→단기→행동→측정)입니다. "
            "본 스킬은 박사님 미래준비학교 5단계(스케치·디자인·훈련·재인식·재생산) 전용입니다. "
            "어느 5단계를 원하시는지 확인 부탁드립니다."
        )
    return {
        "is_general_5stage": is_general,
        "matched_tokens": matched,
        "advisory": advisory,
        "source": "_helpers.detect_general_5stage_confusion",
    }


# ============================================================
# 10. 사양 원문 인덱스 (출처 인용 결정론)
# ============================================================

SPEC_INDEX: Dict[str, Dict[str, str]] = {
    "stage_diagram": {
        "text": "자기 인식 → 비전 발견 → 훈련 → 비전 재인식 → 비전 재생산",
        "source": f"{SPEC_SOURCE} — 5단계 다이어그램",
    },
    "trinity_loop": {
        "text": "가치 ↔ 세상 ↔ 나 (삼각 순환)",
        "source": f"{SPEC_SOURCE} — 비전 디자인·훈련 핵심 도식",
    },
    "vision_reproduction_quote": {
        "text": "스승이 제자를 낳듯이, 비전도 비전을 재생산한다. "
                "비전에 완전히 몰입한 사람은 비전과 한몸인 상태에 도달한다.",
        "source": f"{SPEC_SOURCE} — 비전 재생산 정의",
    },
    "big_dream_quote": {
        "text": "혼자서 이룰 수 있는 꿈은 절대로 큰 꿈이 아니다!",
        "source": f"{SPEC_SOURCE} — 비전 재생산 핵심 메시지",
    },
    "execution_definition": {
        "text": "실패를 통해 깨닫고 즉각 전략을 변화시켜 행동을 발전시키는 것",
        "source": f"{SPEC_SOURCE} — 실행력 정의",
    },
    "stage1_purpose": {
        "text": STAGE_NAMES[1]["purpose"],
        "source": f"{SPEC_SOURCE} — Stage 1 목적",
    },
    "stage2_purpose": {
        "text": STAGE_NAMES[2]["purpose"],
        "source": f"{SPEC_SOURCE} — Stage 2 목적",
    },
    "self_esteem_distinction": {
        "text": "자존감(自尊感) ≠ 자존심(自尊心)",
        "source": f"{SPEC_SOURCE} — 비전 터 다지기",
    },
    "stimulus_kinds": {
        "text": "직접 자극: 여행·체험 / 간접 자극: 독서·교육",
        "source": f"{SPEC_SOURCE} — 비전 자극",
    },
    "leadership_balance": {
        "text": "리더십 + 팔로워십(Followership) + 펠로우십(Fellowship) 균형",
        "source": f"{SPEC_SOURCE} — Stage 3 휴먼 스킬",
    },
}


def lookup_spec(key: str) -> Dict[str, object]:
    """사양 원문 인용 — 결정론 룩업."""
    if key in SPEC_INDEX:
        d = SPEC_INDEX[key]
        return {"found": True, "key": key, "text": d["text"],
                "source": d["source"]}
    return {"found": False, "key": key, "text": "",
            "source": "_helpers.lookup_spec — key not found"}


# ============================================================
# 11. 자기 점검 — 데이터 정합성
# ============================================================

def self_check() -> Dict[str, object]:
    """모듈 데이터 정합성 자기 점검 — 외부 호출 가능."""
    errors: List[str] = []

    # 1) 5단계 개수
    if len(STAGE_NAMES) != 5:
        errors.append(f"STAGE_NAMES 개수 != 5 (실제 {len(STAGE_NAMES)})")
    # 2) 6대 강령 개수
    if len(SIX_PRINCIPLES) != 6:
        errors.append(f"SIX_PRINCIPLES 개수 != 6 (실제 {len(SIX_PRINCIPLES)})")
    if len(SIX_PRINCIPLE_KEYWORDS) != 6:
        errors.append(f"SIX_PRINCIPLE_KEYWORDS 개수 != 6")
    # 3) SMART 글자
    if list(SMART_FIVE.keys()) != ["S", "M", "A", "R", "T"]:
        errors.append("SMART_FIVE 순서/글자 오류")
    # 4) 8대 영역 개수
    if len(EIGHT_TRAINING_AREAS) != 8:
        errors.append(f"EIGHT_TRAINING_AREAS 개수 != 8")
    # 5) 5기준 개수
    if len(FIVE_CRITERIA) != 5:
        errors.append("FIVE_CRITERIA 개수 != 5")
    # 6) 4미래 개수
    if len(FOUR_FUTURES) != 4:
        errors.append("FOUR_FUTURES 개수 != 4")
    # 7) Stage2 작업 개수
    if len(STAGE2_TASKS) != 6:
        errors.append("STAGE2_TASKS 개수 != 6")
    # 8) Stage5 활동 개수
    if len(STAGE5_ACTIVITIES) != 3:
        errors.append("STAGE5_ACTIVITIES 개수 != 3")
    # 9) 입력 유형 개수
    if set(INPUT_TYPES.keys()) != {"A", "B", "C", "D", "E"}:
        errors.append("INPUT_TYPES 키 오류")
    # 10) 커리큘럼 총 주차
    total = total_curriculum_weeks()
    if total != 52:
        errors.append(f"커리큘럼 총 주차 != 52 (실제 {total})")
    # 11) 모든 단계 별칭이 유효 단계 번호로 매핑되는지
    for alias, s in STAGE_ALIAS.items():
        if s not in STAGE_NAMES:
            errors.append(f"별칭 '{alias}' → 존재하지 않는 단계 {s}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "summary": {
            "stages": len(STAGE_NAMES),
            "principles": len(SIX_PRINCIPLES),
            "smart": list(SMART_FIVE.keys()),
            "training_areas": len(EIGHT_TRAINING_AREAS),
            "criteria": len(FIVE_CRITERIA),
            "futures": len(FOUR_FUTURES),
            "stage2_tasks": len(STAGE2_TASKS),
            "stage5_activities": len(STAGE5_ACTIVITIES),
            "input_types": list(INPUT_TYPES.keys()),
            "curriculum_total_weeks": total,
        },
    }


# ============================================================
# CLI 인터페이스
# ============================================================

def _cli() -> int:
    """간이 CLI — SKILL.md가 호출하는 결정론 함수 진입점.

    Usage:
        python _helpers.py <cmd> [json-args]

    cmds:
        self-check
        classify <text>
        diagnose <text>
        curriculum <label>
        normalize-stage <text>
        match-principles <text>
        lookup-principle <idx-or-name>
        score-criteria '<json>'
        smart-tokens '<json-list>'
        smart-letter <letter>
        validate-eight '<json-list>'
        re-recognition <months> [<value_change> <env_change> <new_data>]
        lookup-spec <key>
        list-data <name>
    """
    if len(sys.argv) < 2:
        print(_cli.__doc__)
        return 1

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "self-check":
            r = self_check()
        elif cmd == "classify":
            r = classify_input_type(" ".join(args))
        elif cmd == "diagnose":
            r = diagnose_stage(" ".join(args))
        elif cmd == "curriculum":
            r = lookup_curriculum(" ".join(args))
        elif cmd == "normalize-stage":
            r = normalize_stage_name(" ".join(args))
        elif cmd == "match-principles":
            r = match_six_principles(" ".join(args))
        elif cmd == "lookup-principle":
            arg = args[0] if args else ""
            try:
                r = lookup_principle(int(arg))
            except ValueError:
                r = lookup_principle(arg)
        elif cmd == "score-criteria":
            scores = json.loads(args[0]) if args else {}
            r = score_five_criteria(scores)
        elif cmd == "smart-tokens":
            tokens = json.loads(args[0]) if args else []
            r = validate_smart_tokens(tokens)
        elif cmd == "smart-letter":
            r = get_smart_full(args[0] if args else "")
        elif cmd == "validate-eight":
            areas = json.loads(args[0]) if args else []
            r = validate_eight_areas(areas)
        elif cmd == "re-recognition":
            months = int(args[0]) if args else 0
            vc = args[1] == "1" if len(args) > 1 else False
            ec = args[2] == "1" if len(args) > 2 else False
            nd = args[3] == "1" if len(args) > 3 else False
            r = should_trigger_reracognition(months, vc, ec, nd)
        elif cmd == "lookup-spec":
            r = lookup_spec(args[0] if args else "")
        elif cmd == "detect-doran":
            r = detect_doran_smart_confusion(" ".join(args))
        elif cmd == "detect-general-5stage":
            r = detect_general_5stage_confusion(" ".join(args))
        elif cmd == "list-data":
            name = args[0] if args else ""
            data_map = {
                "stages": STAGE_NAMES,
                "principles": SIX_PRINCIPLES,
                "smart": SMART_FIVE,
                "eight-areas": EIGHT_TRAINING_AREAS,
                "criteria": FIVE_CRITERIA,
                "futures": FOUR_FUTURES,
                "stage2-tasks": STAGE2_TASKS,
                "stage5-activities": STAGE5_ACTIVITIES,
                "input-types": INPUT_TYPES,
                "curriculum": CURRICULUM_TABLE,
                "spec-index": SPEC_INDEX,
            }
            r = {"name": name, "data": data_map.get(name, "UNKNOWN")}
        else:
            print(f"unknown command: {cmd}")
            print(_cli.__doc__)
            return 2

        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0

    except Exception as e:
        print(json.dumps({"error": str(e), "cmd": cmd, "args": args},
                         ensure_ascii=False, indent=2))
        return 3


if __name__ == "__main__":
    raise SystemExit(_cli())
