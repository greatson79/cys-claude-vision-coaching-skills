#!/usr/bin/env python3
"""
CYS 비전 역량 진단 결정론 엔진
================================
LLM이 자연어로 추론하면 할루시네이션 위험이 있는 모든 단계를
결정론적 파이썬 함수로 환원한다.

호출 방식:
  python3 cys_engine.py <command> --input <json>

명령:
  validate_score          단일 점수 0~100 범위 검증
  validate_scores         다중 점수 일괄 검증
  classify_band           영역 E 통합 점수 → 강점/보통/발전영역
  classify_bands_batch    여러 영역 E 점수 일괄 분류
  enneagram_wing          에니어그램 9유형 점수 → 주·날개 결정
  mi_rank                 다중지능 9 점수 → 순위
  skill_balance_rank      4 Skill Balance 5 점수 → 순위
  aggregate_mean          세부 원점수 리스트 → 평균 (소수점 1자리)
  area_e_integrate        영역 E 통합 비전 코드 점수 산출
  bar_chart               점수 dict → 박사님 책 양식 막대 그래프
  integrate_subskills     6 하위 스킬 결과 → CYS 매핑
  full_diagnose           전체 진단 통합 처리 (입력 dict → 최종 보고서 데이터)

표준 출력: JSON
종료 코드: 0 성공, 1 입력 검증 실패, 2 내부 오류
"""

import argparse
import json
import sys
from typing import Dict, List, Tuple, Any

# ────────────────────────────────────────────────────────────────────
# 상수 정의 (박사님 책 명세 그대로)
# ────────────────────────────────────────────────────────────────────

# 영역 E 통합 점수 기준 (절대 원칙 #8)
STRENGTH_THRESHOLD = 75      # 75점 이상 = 강점
DEVELOPMENT_CEILING = 50     # 50점 미만 = 발전영역
# 50~74점 = 보통

# 박사님 본인 (A type) 진단 데이터 - 박사님 책 그대로
DR_CHOI_A_TYPE = {
    "area_a": {
        "외향력": 25, "내향력": 60, "현실 파악력": 63,
        "미래 통찰력": 85, "성취력": 48, "융통력": 40
    },
    "multiple_intelligence": {
        "논리수학지능": 90, "언어지능": 65, "공간지능": 42.5,
        "음악지능": 25, "신체운동지능": 42.5, "인간친화지능": 22.5,
        "자기성찰지능": 72.5, "자연친화지능": 25, "실존지능": None
    },
    "enneagram": {
        "1": 53, "2": 30, "3": 30, "4": 10, "5": 78,
        "6": 20, "7": 43, "8": 28, "9": 28
    },
    "skill_balance": {
        "생각": 77, "언어": 63, "감성": 30, "몸": 40, "영성": 92
    },
    "area_e": {
        "비전 구상력": 79, "비전 외향력": 25, "비전 내향력": 60,
        "비전 자기계발력": 64, "비전 계획력": 75, "비전 전략력": 73,
        "비전 추진력": 36, "비전 네트워킹력": 40
    },
    "core_values": [
        "지식·지혜 추구", "신·종교생활", "존중·존경",
        "성과·탁월함·전문가·명성", "성실·책임·최선을 다함",
        "창의·새로움·혁신·자율성"
    ],
    "vision_direction": "지적 연구",
    "vision_value_orientation": ["지식·지혜 추구", "정신적 가치", "진리 수호"],
    "leadership_style": "영성형"
}

# 다중지능 9 항목 (Gardner 1983 + 1999 잠정 추가)
MI_CANONICAL = [
    "논리수학지능", "언어지능", "공간지능", "음악지능",
    "신체운동지능", "인간친화지능", "자기성찰지능",
    "자연친화지능", "실존지능"
]

# 다중지능 별칭 매핑 (Gardner 영문 원어 + 한글 약칭 + 하위 스킬 호환)
# 정규형은 한글 9개 (논리수학지능·언어지능·공간지능·음악지능·신체운동지능·
# 인간친화지능·자기성찰지능·자연친화지능·실존지능)
MI_ALIAS = {
    # 영문 Gardner 원어 (1983/1999)
    "Linguistic": "언어지능",
    "Linguistic Intelligence": "언어지능",
    "Logical-Mathematical": "논리수학지능",
    "Logical-Mathematical Intelligence": "논리수학지능",
    "Logical Mathematical": "논리수학지능",
    "Spatial": "공간지능",
    "Spatial Intelligence": "공간지능",
    "Visual-Spatial": "공간지능",
    "Musical": "음악지능",
    "Musical Intelligence": "음악지능",
    "Bodily-Kinesthetic": "신체운동지능",
    "Bodily Kinesthetic": "신체운동지능",
    "Bodily-Kinesthetic Intelligence": "신체운동지능",
    "Kinesthetic": "신체운동지능",
    "Interpersonal": "인간친화지능",
    "Interpersonal Intelligence": "인간친화지능",
    "Intrapersonal": "자기성찰지능",
    "Intrapersonal Intelligence": "자기성찰지능",
    "Naturalist": "자연친화지능",
    "Naturalistic": "자연친화지능",
    "Naturalist Intelligence": "자연친화지능",
    "Existential": "실존지능",
    "Existential Intelligence": "실존지능",
    "Existentialist": "실존지능",
    "Spiritual": "실존지능",
    # 한글 약칭·대안 명칭
    "언어": "언어지능",
    "논리수학": "논리수학지능",
    "수리": "논리수학지능",
    "공간": "공간지능",
    "시공간지능": "공간지능",
    "음악": "음악지능",
    "신체운동": "신체운동지능",
    "신체": "신체운동지능",
    "운동지능": "신체운동지능",
    "대인관계지능": "인간친화지능",
    "대인관계": "인간친화지능",
    "대인": "인간친화지능",
    "자기성찰": "자기성찰지능",
    "내성지능": "자기성찰지능",
    "자연친화": "자연친화지능",
    "자연": "자연친화지능",
    "실존": "실존지능",
    "영성지능": "실존지능",
    "영성": "실존지능",
}

# 4 Skill Balance 5영역
SB_CANONICAL = ["생각", "언어", "감성", "몸", "영성"]

# 4 Skill Balance 별칭 매핑 (영문 + 한글 변형)
SB_ALIAS = {
    # 영문
    "Thinking": "생각", "Thought": "생각", "Thought Skill": "생각",
    "Cognitive": "생각", "Cognition": "생각",
    "Language": "언어", "Linguistic": "언어", "Verbal": "언어",
    "Emotion": "감성", "Emotional": "감성", "Feeling": "감성",
    "Body": "몸", "Bodily": "몸", "Physical": "몸", "Kinesthetic": "몸",
    "Spirit": "영성", "Spiritual": "영성", "Spirituality": "영성",
    # 한글 변형
    "사고": "생각", "사고력": "생각", "지성": "생각",
    "언어력": "언어",
    "감성지능": "감성", "정서": "감성", "감정": "감성",
    "신체": "몸", "육체": "몸",
    "영적": "영성", "영성지능": "영성",
}

# 에니어그램 9유형
ENN_TYPES = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]

# 에니어그램 인접 유형 매핑 (날개 후보)
ENN_NEIGHBORS = {
    "1": ("9", "2"), "2": ("1", "3"), "3": ("2", "4"),
    "4": ("3", "5"), "5": ("4", "6"), "6": ("5", "7"),
    "7": ("6", "8"), "8": ("7", "9"), "9": ("8", "1")
}

# 에니어그램 유형명 (Riso-Hudson 표준)
ENN_NAMES = {
    "1": "개혁가(Reformer)", "2": "조력자(Helper)",
    "3": "성취자(Achiever)", "4": "개인주의자(Individualist)",
    "5": "탐구가(Investigator)", "6": "충성가(Loyalist)",
    "7": "열정가(Enthusiast)", "8": "도전자(Challenger)",
    "9": "평화주의자(Peacemaker)"
}

# 영역 E 8항목 (10 비전 코드 중 점수형 7항목 + 외향력 1항목으로 구성)
AREA_E_KEYS = [
    "비전 구상력", "비전 외향력", "비전 내향력", "비전 자기계발력",
    "비전 계획력", "비전 전략력", "비전 추진력", "비전 네트워킹력"
]


# ────────────────────────────────────────────────────────────────────
# 입력 검증
# ────────────────────────────────────────────────────────────────────

def validate_score(score: Any, label: str = "score") -> float:
    """단일 점수 0~100 범위 검증. 미기재 = None 허용."""
    if score is None:
        return None
    try:
        v = float(score)
    except (TypeError, ValueError):
        raise ValueError(f"{label}: 숫자가 아님 ({score!r})")
    if v < 0 or v > 100:
        raise ValueError(f"{label}: 0~100 범위 밖 ({v})")
    return v


def validate_scores(scores: Dict[str, Any]) -> Dict[str, float]:
    """다중 점수 일괄 검증."""
    if not isinstance(scores, dict):
        raise ValueError("scores: dict 타입이어야 함")
    return {k: validate_score(v, k) for k, v in scores.items()}


# ────────────────────────────────────────────────────────────────────
# 강점/보통/발전영역 분류 (영역 E 통합 점수 기준)
# ────────────────────────────────────────────────────────────────────

def classify_band(score: float) -> str:
    """영역 E 통합 점수 → band 결정.

    절대 원칙 #8: 강점 75점+, 보통 50~74점, 발전영역 50점 미만.
    세부 원점수로 강점 분류 금지 → 본 함수는 영역 E 통합 점수에만 사용.
    """
    v = validate_score(score, "band_score")
    if v is None:
        return "미기재"
    if v >= STRENGTH_THRESHOLD:
        return "강점"
    if v >= DEVELOPMENT_CEILING:
        return "보통"
    return "발전영역"


def classify_bands_batch(scores: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """영역 E 8항목 일괄 분류."""
    result = {}
    for key, val in scores.items():
        band = classify_band(val)
        result[key] = {"score": validate_score(val, key), "band": band}
    return result


# ────────────────────────────────────────────────────────────────────
# 에니어그램 주 유형·날개 결정
# ────────────────────────────────────────────────────────────────────

def enneagram_wing(scores: Dict[str, Any]) -> Dict[str, Any]:
    """에니어그램 9유형 점수 → 주 유형·날개 결정.

    규칙 (Riso-Hudson RHETI 표준):
    1. 가장 높은 점수가 주 유형
    2. 동점이면 더 낮은 번호 우선 (결정론적 tie-break)
    3. 주 유형의 두 인접 유형 점수 중 더 높은 쪽이 날개
    4. 인접 동점이면 더 낮은 번호 우선
    """
    if not isinstance(scores, dict):
        raise ValueError("enneagram scores: dict 필요")
    validated = {}
    for t in ENN_TYPES:
        if t not in scores:
            raise ValueError(f"enneagram: 유형 {t} 점수 누락")
        validated[t] = validate_score(scores[t], f"enn_{t}")
        if validated[t] is None:
            raise ValueError(f"enneagram: 유형 {t} 점수 None 불가")

    # 주 유형: 최고점, tie-break = 낮은 번호
    main = sorted(ENN_TYPES, key=lambda t: (-validated[t], int(t)))[0]
    # 날개: 인접 유형 중 최고점, tie-break = 낮은 번호
    left, right = ENN_NEIGHBORS[main]
    wing_candidates = sorted(
        [left, right],
        key=lambda t: (-validated[t], int(t))
    )
    wing = wing_candidates[0]
    return {
        "main": main,
        "main_name": ENN_NAMES[main],
        "main_score": validated[main],
        "wing": wing,
        "wing_name": ENN_NAMES[wing],
        "wing_score": validated[wing],
        "notation": f"{main}w{wing}",
        "all_scores": validated
    }


# ────────────────────────────────────────────────────────────────────
# 다중지능·4 Skill Balance 순위
# ────────────────────────────────────────────────────────────────────

def _normalize_mi_key(key: str) -> str:
    """다중지능 별칭을 정규 명칭으로 통일."""
    return MI_ALIAS.get(key, key)


def mi_rank(scores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """다중지능 9 점수 → 순위 (높은 점수 우선, tie-break = canonical 순서)."""
    if not isinstance(scores, dict):
        raise ValueError("mi scores: dict 필요")
    normalized = {}
    for k, v in scores.items():
        nk = _normalize_mi_key(k)
        normalized[nk] = validate_score(v, nk)
    # 누락 항목 = None 처리
    for k in MI_CANONICAL:
        if k not in normalized:
            normalized[k] = None
    ranking = []
    canonical_idx = {k: i for i, k in enumerate(MI_CANONICAL)}
    # None은 마지막으로
    sorted_keys = sorted(
        MI_CANONICAL,
        key=lambda k: (
            normalized[k] is None,
            -(normalized[k] if normalized[k] is not None else 0),
            canonical_idx[k]
        )
    )
    for rank, k in enumerate(sorted_keys, start=1):
        ranking.append({
            "rank": rank,
            "intelligence": k,
            "score": normalized[k]
        })
    return ranking


def _normalize_sb_key(key: str) -> str:
    """4 Skill Balance 별칭을 정규 명칭으로 통일."""
    return SB_ALIAS.get(key, key)


def skill_balance_rank(scores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """4 Skill Balance 5영역 점수 → 순위."""
    if not isinstance(scores, dict):
        raise ValueError("skill_balance: dict 필요")
    # 별칭 → 정규형 변환
    normalized_input = {_normalize_sb_key(k): v for k, v in scores.items()}
    validated = {}
    for k in SB_CANONICAL:
        if k not in normalized_input:
            raise ValueError(f"skill_balance: {k} 누락")
        validated[k] = validate_score(normalized_input[k], f"sb_{k}")
        if validated[k] is None:
            raise ValueError(f"skill_balance: {k} 점수 None 불가")
    canonical_idx = {k: i for i, k in enumerate(SB_CANONICAL)}
    sorted_keys = sorted(
        SB_CANONICAL,
        key=lambda k: (-validated[k], canonical_idx[k])
    )
    # 박사님 책 영역별 설명 (가장 재능 높은 영역 식별표)
    descriptions = {
        "생각": "논리적 사고·분석·평가·창조·전략·종합·탐구·연구·통찰",
        "언어": "가르치다·논리적 말하기·논리적 글쓰기",
        "감성": "동감·마음으로 받아주기",
        "몸": "손으로 작동",
        "영성": "자아성찰·영적 묵상·가치 사고·종교활동·삶과 죽음 이후 세계 사고"
    }
    return [
        {
            "rank": i + 1,
            "area": k,
            "score": validated[k],
            "description": descriptions[k]
        }
        for i, k in enumerate(sorted_keys)
    ]


# ────────────────────────────────────────────────────────────────────
# 세부 평균 (추진력·네트워킹력)
# ────────────────────────────────────────────────────────────────────

def aggregate_mean(items: List[Any], round_digits: int = 2) -> float:
    """세부 원점수 리스트 → 평균.

    박사님 책 예: 추진력 [30, 27.5, 40, 47.5] → 36.25 → 정수 표기 36
                  네트워킹력 [22.5, 42.5, 62.5, 30, 41.7] → 39.84 → 정수 표기 40
    정밀도는 소수 2자리까지 보존하며, 영역 E 통합 시 정수 근사 처리한다.
    """
    if not isinstance(items, list) or not items:
        raise ValueError("aggregate_mean: 비어있지 않은 list 필요")
    nums = []
    for i, v in enumerate(items):
        s = validate_score(v, f"item[{i}]")
        if s is None:
            raise ValueError(f"aggregate_mean: item[{i}] None 불가")
        nums.append(s)
    mean = sum(nums) / len(nums)
    return round(mean, round_digits)


# ────────────────────────────────────────────────────────────────────
# 영역 E 통합 비전 코드 점수 산출
# ────────────────────────────────────────────────────────────────────

# 영역 E 통합 산출 명세 (박사님 책 데이터 역산):
# - 비전 구상력: 세부 [85] → 통합 79 (계수 약 0.929)
# - 비전 계획력: 세부 [85] → 통합 75 (계수 약 0.882)
# - 비전 전략력: 세부 [77.5] → 통합 73 (계수 약 0.942)
# - 비전 추진력: 세부 [30,27.5,40,47.5] → 통합 36 (단순 평균 반올림)
# - 비전 네트워킹력: 세부 [22.5,42.5,62.5,30,41.7] → 통합 40 (단순 평균 반올림)
#
# 박사님 책 원문에 정확한 통합 공식이 명시되지 않음.
# 보수적 처리: 추진력·네트워킹력은 단순 평균(검증된 공식),
# 구상력·계획력·전략력·자기계발력·외향력·내향력은 세부 원점수 = 통합 점수로 처리.
# 단, 세부 원점수가 여러 개면 단순 평균을 적용한다.
# 사용자 알림: 박사님 책의 통합 점수는 박사님 본인 데이터 그대로 인용이며,
# 사용자 적용 시에는 검증 가능한 단순 평균 규칙만 사용한다.

def area_e_integrate(detailed: Dict[str, Any]) -> Dict[str, Any]:
    """영역 E 8항목 세부 점수 → 통합 비전 코드 점수.

    입력 형식:
      {
        "비전 구상력": [85] or 85,        # 단일값 또는 리스트
        "비전 외향력": 25,
        "비전 내향력": 60,
        "비전 자기계발력": [72.5, 65, 42.5],  # 자기성찰·언어이해·지각조직
        "비전 계획력": 85,
        "비전 전략력": 77.5,
        "비전 추진력": [30, 27.5, 40, 47.5],
        "비전 네트워킹력": [22.5, 42.5, 62.5, 30, 41.7]
      }
    """
    if not isinstance(detailed, dict):
        raise ValueError("area_e_integrate: dict 필요")
    result = {}
    for key in AREA_E_KEYS:
        if key not in detailed:
            raise ValueError(f"area_e_integrate: {key} 누락")
        v = detailed[key]
        if isinstance(v, list):
            integrated = aggregate_mean(v, round_digits=1)
        else:
            integrated = validate_score(v, key)
            if integrated is None:
                raise ValueError(f"area_e_integrate: {key} 점수 None 불가")
        # 정수에 가까우면 정수로 표기 (박사님 책 양식)
        if abs(integrated - round(integrated)) < 0.05:
            integrated = float(round(integrated))
        result[key] = {
            "integrated": integrated,
            "band": classify_band(integrated),
            "detail": v if isinstance(v, list) else [v]
        }
    return result


# ────────────────────────────────────────────────────────────────────
# 막대 그래프 시각화 (박사님 책 양식)
# ────────────────────────────────────────────────────────────────────

# 100점 = MAX_BARS 칸 가득 채움
MAX_BARS = 10  # 박사님 책 양식: 1칸 = 10점

# 부분 채움 문자 (▏▎▍▌▋▊▉█ - U+258F~U+2588)
PARTIAL = "▏▎▍▌▋▊▉"  # 1/8 ~ 7/8


def _bar_for_score(score: float, max_bars: int = MAX_BARS) -> str:
    """점수 → 결정론적 막대 문자열."""
    if score is None:
        return "(미기재)"
    s = max(0.0, min(100.0, float(score)))
    full_bar_units = s / 10.0  # 10점당 1칸
    full = int(full_bar_units)
    frac = full_bar_units - full
    bar = "█" * full
    if frac > 0:
        # frac를 8단계로 양자화
        eighth = int(round(frac * 8))
        if eighth == 8:
            bar += "█"
        elif eighth >= 1:
            bar += PARTIAL[eighth - 1]
    return bar


def bar_chart(scores: Dict[str, Any], star_threshold: float = 80.0,
              sort_by_score: bool = True) -> str:
    """점수 dict → 박사님 책 양식 막대 그래프 문자열.

    형식: "라벨 | █████ 점수 [★]"
    """
    if not isinstance(scores, dict):
        raise ValueError("bar_chart: dict 필요")
    if not scores:
        raise ValueError("bar_chart: 빈 dict 불가 (적어도 1개 항목 필요)")
    validated = {k: validate_score(v, k) for k, v in scores.items()}
    items = list(validated.items())
    if sort_by_score:
        items.sort(key=lambda x: -(x[1] if x[1] is not None else -1))
    max_label_len = max((len(k) for k, _ in items), default=8)
    lines = []
    for label, score in items:
        bar = _bar_for_score(score)
        star = " ★" if (score is not None and score >= star_threshold) else ""
        if score is None:
            score_str = "(미기재)"
        elif abs(score - round(score)) < 0.05:
            score_str = str(int(round(score)))
        else:
            score_str = f"{score:.1f}"
        lines.append(f"{label.ljust(max_label_len)} | {bar} {score_str}{star}")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# 6 하위 스킬 결과 → CYS 매핑
# ────────────────────────────────────────────────────────────────────

# 매핑 명세 (SKILL.md "다른 vision 진단 스킬과의 분담" 표 그대로):
#   vision-mbti-visioncoding         → 비전 잠재력 (성격)
#   vision-enneagram-visioncoding    → 비전 잠재력 (성격)
#   vision-strong-visioncoding       → 비전 기술력 (관심사 검사)
#   vision-multipleintel-visioncoding → 비전 잠재력 (재능)
#   vision-values-visioncoding       → 비전 가치 방향
#   vision-readiness-visioncoding    → 비전 자기계발력·전략력 일부

SUBSKILL_MAP = {
    "mbti": {"cys_code": "비전 잠재력", "subcategory": "성격"},
    "enneagram": {"cys_code": "비전 잠재력", "subcategory": "성격(에니어그램)"},
    "strong": {"cys_code": "비전 기술력", "subcategory": "관심사 검사"},
    "multipleintel": {"cys_code": "비전 잠재력", "subcategory": "재능(다중지능)"},
    "values": {"cys_code": "비전 가치 방향", "subcategory": "가치 성향"},
    "readiness": {"cys_code": "비전 자기계발력·전략력", "subcategory": "준비 역량"}
}


def integrate_subskills(subskill_results: Dict[str, Any]) -> Dict[str, Any]:
    """6 하위 스킬 결과 dict → CYS 10 비전 코드 통합 dict.

    입력:
      {
        "mbti": {"type": "INTJ", ...},
        "enneagram": {"main": "5", "wing": "6", "scores": {...}},
        "strong": {...},
        "multipleintel": {"scores": {...}},
        "values": {"top_values": [...]},
        "readiness": {...}
      }
    """
    if not isinstance(subskill_results, dict):
        raise ValueError("integrate_subskills: dict 필요")
    cys_codes = {
        "비전 방향성": {"source": "사용자 직접 분류 필요", "data": None},
        "비전 가치 방향": {"sources": [], "data": {}},
        "비전 잠재력": {"sources": [], "data": {}},
        "비전 기술력": {"sources": [], "data": {}},
        "비전 구상력": {"source": "본 스킬 자체 측정 필요", "data": None},
        "비전 자기계발력": {"sources": [], "data": {}},
        "비전 전략력": {"sources": [], "data": {}},
        "비전 추진력": {"source": "본 스킬 자체 측정 필요", "data": None},
        "비전 네트워킹력": {"source": "본 스킬 자체 측정 필요", "data": None},
        "비전 리더십 스타일": {"source": "에니어그램에서 추론", "data": None}
    }

    for sub_name, sub_data in subskill_results.items():
        if sub_name not in SUBSKILL_MAP:
            continue  # 알 수 없는 하위 스킬은 무시
        mapping = SUBSKILL_MAP[sub_name]
        cys_code = mapping["cys_code"]
        subcat = mapping["subcategory"]

        if cys_code == "비전 자기계발력·전략력":
            for target in ("비전 자기계발력", "비전 전략력"):
                cys_codes[target]["sources"].append(sub_name)
                cys_codes[target]["data"][subcat] = sub_data
        elif cys_code in cys_codes and "sources" in cys_codes[cys_code]:
            cys_codes[cys_code]["sources"].append(sub_name)
            cys_codes[cys_code]["data"][subcat] = sub_data

    # 에니어그램 → 리더십 스타일 자동 도출
    if "enneagram" in subskill_results:
        enn = subskill_results["enneagram"]
        main = enn.get("main") if isinstance(enn, dict) else None
        leadership_map = {
            "1": "원칙형(개혁가)", "2": "관계형(조력자)",
            "3": "성취형(성취자)", "4": "감성형(개인주의자)",
            "5": "지식형/영성형(탐구가)", "6": "충성형(충성가)",
            "7": "비전형(열정가)", "8": "추진형(도전자)",
            "9": "중재형(평화주의자)"
        }
        if main and str(main) in leadership_map:
            cys_codes["비전 리더십 스타일"]["data"] = leadership_map[str(main)]
            cys_codes["비전 리더십 스타일"]["source"] = "에니어그램 주 유형 매핑"

    return cys_codes


# ────────────────────────────────────────────────────────────────────
# 통합 진단 (full_diagnose)
# ────────────────────────────────────────────────────────────────────

def full_diagnose(payload: Dict[str, Any]) -> Dict[str, Any]:
    """사용자 입력 dict → 최종 진단 보고서 데이터.

    입력:
      {
        "user_label": "사용자 익명",
        "area_a": {...},
        "multiple_intelligence": {...},
        "enneagram": {...},
        "skill_balance": {...},
        "area_e_detail": {...},
        "core_values": [...],
        "vision_direction": "...",
        "vision_value_orientation": [...]
      }
    """
    if not isinstance(payload, dict):
        raise ValueError("full_diagnose: dict 필요")
    report = {"user_label": payload.get("user_label", "사용자")}

    # 영역 A
    if "area_a" in payload:
        report["area_a"] = validate_scores(payload["area_a"])

    # 영역 B 다중지능
    if "multiple_intelligence" in payload:
        report["multiple_intelligence"] = {
            "scores": validate_scores({
                _normalize_mi_key(k): v
                for k, v in payload["multiple_intelligence"].items()
            }),
            "ranking": mi_rank(payload["multiple_intelligence"])
        }

    # 영역 C 에니어그램
    if "enneagram" in payload:
        report["enneagram"] = enneagram_wing(payload["enneagram"])

    # 영역 D 4 Skill Balance
    if "skill_balance" in payload:
        report["skill_balance"] = {
            "scores": validate_scores(payload["skill_balance"]),
            "ranking": skill_balance_rank(payload["skill_balance"])
        }

    # 영역 E 비전 코드 8항목 통합
    if "area_e_detail" in payload:
        e_result = area_e_integrate(payload["area_e_detail"])
        report["area_e"] = e_result
        # band 분류 카운트
        bands = {"강점": [], "보통": [], "발전영역": []}
        for k, v in e_result.items():
            bands[v["band"]].append({"code": k, "score": v["integrated"]})
        report["area_e_summary"] = bands
        # 막대 그래프
        chart_input = {k: v["integrated"] for k, v in e_result.items()}
        report["area_e_chart"] = bar_chart(chart_input, star_threshold=75.0)

    # 영역 F 핵심 가치
    if "core_values" in payload:
        cv = payload["core_values"]
        if not isinstance(cv, list):
            raise ValueError("core_values: list 필요")
        report["core_values"] = cv[:10]  # 최대 10개 까지만

    # 비전 방향성·가치 방향·리더십 스타일
    if "vision_direction" in payload:
        report["vision_direction"] = str(payload["vision_direction"])
    if "vision_value_orientation" in payload:
        vo = payload["vision_value_orientation"]
        report["vision_value_orientation"] = vo if isinstance(vo, list) else [str(vo)]
    if "enneagram" in payload:
        # 리더십 스타일 = 에니어그램 주 유형 매핑
        main = report["enneagram"]["main"]
        leadership_map = {
            "1": "원칙형(개혁가)", "2": "관계형(조력자)",
            "3": "성취형(성취자)", "4": "감성형(개인주의자)",
            "5": "지식형/영성형(탐구가)", "6": "충성형(충성가)",
            "7": "비전형(열정가)", "8": "추진형(도전자)",
            "9": "중재형(평화주의자)"
        }
        report["leadership_style"] = leadership_map.get(main, "미분류")

    return report


# ────────────────────────────────────────────────────────────────────
# 진입점
# ────────────────────────────────────────────────────────────────────

def _emit(obj: Any, code: int = 0):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)


def _read_input(args) -> Any:
    if args.input == "-" or args.input is None:
        raw = sys.stdin.read()
    else:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                raw = f.read()
        except FileNotFoundError:
            raw = args.input  # 파일이 아니면 인라인 JSON 문자열로 해석
    raw = raw.strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"입력 JSON 파싱 실패: {e}")


def main():
    parser = argparse.ArgumentParser(description="CYS 비전 역량 진단 결정론 엔진")
    parser.add_argument("command", choices=[
        "validate_score", "validate_scores",
        "classify_band", "classify_bands_batch",
        "enneagram_wing", "mi_rank", "skill_balance_rank",
        "aggregate_mean", "area_e_integrate",
        "bar_chart", "integrate_subskills", "full_diagnose",
        "dr_choi_data", "self_test"
    ])
    parser.add_argument("--input", default="-",
                        help="JSON 파일 경로, '-' (stdin), 또는 인라인 JSON 문자열")
    args = parser.parse_args()

    try:
        if args.command == "dr_choi_data":
            _emit(DR_CHOI_A_TYPE)
        if args.command == "self_test":
            _emit(_self_test())

        data = _read_input(args)
        cmd = args.command

        if cmd == "validate_score":
            _emit({"validated": validate_score(data)})
        elif cmd == "validate_scores":
            _emit(validate_scores(data))
        elif cmd == "classify_band":
            score = data.get("score") if isinstance(data, dict) else data
            _emit({"score": validate_score(score), "band": classify_band(score)})
        elif cmd == "classify_bands_batch":
            _emit(classify_bands_batch(data))
        elif cmd == "enneagram_wing":
            _emit(enneagram_wing(data))
        elif cmd == "mi_rank":
            _emit(mi_rank(data))
        elif cmd == "skill_balance_rank":
            _emit(skill_balance_rank(data))
        elif cmd == "aggregate_mean":
            items = data.get("items") if isinstance(data, dict) else data
            _emit({"mean": aggregate_mean(items)})
        elif cmd == "area_e_integrate":
            _emit(area_e_integrate(data))
        elif cmd == "bar_chart":
            scores = data.get("scores") if isinstance(data, dict) else data
            star = data.get("star_threshold", 80.0) if isinstance(data, dict) else 80.0
            sort_by = data.get("sort_by_score", True) if isinstance(data, dict) else True
            _emit({"chart": bar_chart(scores, star_threshold=star, sort_by_score=sort_by)})
        elif cmd == "integrate_subskills":
            _emit(integrate_subskills(data))
        elif cmd == "full_diagnose":
            _emit(full_diagnose(data))
    except ValueError as e:
        _emit({"error": "INPUT_ERROR", "message": str(e)}, code=1)
    except Exception as e:
        _emit({"error": "INTERNAL_ERROR", "message": str(e), "type": type(e).__name__}, code=2)


def _self_test() -> Dict[str, Any]:
    """결정론 엔진 자가 검증 (박사님 A type 데이터로 회귀 테스트)."""
    results = {}

    # 1. 강점/보통/발전 분류
    assert classify_band(85) == "강점"
    assert classify_band(75) == "강점"
    assert classify_band(74.9) == "보통"
    assert classify_band(50) == "보통"
    assert classify_band(49.9) == "발전영역"
    assert classify_band(0) == "발전영역"
    results["band_classification"] = "PASS"

    # 2. 에니어그램 박사님 데이터 → 5w6
    enn = enneagram_wing(DR_CHOI_A_TYPE["enneagram"])
    assert enn["main"] == "5", f"expected 5, got {enn['main']}"
    assert enn["wing"] == "6", f"expected wing 6 (4=10 vs 6=20 → 6), got {enn['wing']}"
    assert enn["notation"] == "5w6"
    results["enneagram_wing"] = "PASS (5w6)"

    # 3. 추진력 평균: [30, 27.5, 40, 47.5] → 36.25 → 36
    m = aggregate_mean([30, 27.5, 40, 47.5])
    assert abs(m - 36.25) < 0.01, f"expected 36.25, got {m}"
    results["aggregate_mean_drive"] = f"PASS ({m})"

    # 4. 네트워킹력 평균: [22.5, 42.5, 62.5, 30, 41.7] → 39.84
    m2 = aggregate_mean([22.5, 42.5, 62.5, 30, 41.7])
    assert abs(m2 - 39.84) < 0.01, f"expected 39.84, got {m2}"
    results["aggregate_mean_network"] = f"PASS ({m2})"

    # 5. 영역 E 분류 (박사님 데이터)
    bands = classify_bands_batch(DR_CHOI_A_TYPE["area_e"])
    assert bands["비전 구상력"]["band"] == "강점"  # 79
    assert bands["비전 계획력"]["band"] == "강점"  # 75
    assert bands["비전 전략력"]["band"] == "보통"  # 73
    assert bands["비전 자기계발력"]["band"] == "보통"  # 64
    assert bands["비전 내향력"]["band"] == "보통"  # 60
    assert bands["비전 외향력"]["band"] == "발전영역"  # 25
    assert bands["비전 추진력"]["band"] == "발전영역"  # 36
    assert bands["비전 네트워킹력"]["band"] == "발전영역"  # 40
    results["area_e_classification"] = "PASS"

    # 6. 다중지능 순위 (박사님)
    rank = mi_rank(DR_CHOI_A_TYPE["multiple_intelligence"])
    assert rank[0]["intelligence"] == "논리수학지능", f"expected 논리수학, got {rank[0]['intelligence']}"
    assert rank[1]["intelligence"] == "자기성찰지능", f"expected 자기성찰, got {rank[1]['intelligence']}"
    assert rank[2]["intelligence"] == "언어지능"
    results["mi_rank"] = "PASS"

    # 7. 4 Skill Balance 순위 (박사님)
    sbrank = skill_balance_rank(DR_CHOI_A_TYPE["skill_balance"])
    assert sbrank[0]["area"] == "영성", f"expected 영성, got {sbrank[0]['area']}"
    assert sbrank[1]["area"] == "생각"
    assert sbrank[2]["area"] == "언어"
    assert sbrank[3]["area"] == "몸"
    assert sbrank[4]["area"] == "감성"
    results["skill_balance_rank"] = "PASS"

    # 8. 막대 그래프 결정론성
    chart = bar_chart({"A": 85, "B": 50}, star_threshold=75)
    assert "★" in chart and "85" in chart
    results["bar_chart"] = "PASS"

    # 9. 입력 검증
    try:
        validate_score(150)
        results["range_validation"] = "FAIL (should reject 150)"
    except ValueError:
        results["range_validation"] = "PASS"

    try:
        validate_score(-5)
        results["range_validation_neg"] = "FAIL"
    except ValueError:
        results["range_validation_neg"] = "PASS"

    # 10. 영역 E 전체 통합 (박사님 데이터 재현)
    detail = {
        "비전 구상력": 79,
        "비전 외향력": 25,
        "비전 내향력": 60,
        "비전 자기계발력": 64,
        "비전 계획력": 75,
        "비전 전략력": 73,
        "비전 추진력": [30, 27.5, 40, 47.5],
        "비전 네트워킹력": [22.5, 42.5, 62.5, 30, 41.7]
    }
    e_int = area_e_integrate(detail)
    assert abs(e_int["비전 추진력"]["integrated"] - 36.25) < 0.5
    assert abs(e_int["비전 네트워킹력"]["integrated"] - 39.84) < 0.5
    results["area_e_integrate_full"] = "PASS"

    results["overall"] = "ALL TESTS PASS"
    return results


if __name__ == "__main__":
    main()
