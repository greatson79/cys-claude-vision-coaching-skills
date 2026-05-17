#!/usr/bin/env python3
"""
vision-enneagram-visioncoding 결정론 엔진.

LLM이 자연어로 추론하면 할루시네이션 위험이 있는 단계들을 결정론적 파이썬 함수로 환원.

환원된 단계:
  1) 27문항 카탈로그 — fixed data
  2) 층화 무작위 셔플 — seed 기반 재현 가능
  3) Likert 점수 합산 — 산수
  4) 18문항 1차 산출
  5) 동점 검사 (1위 동점 검출)
  6) 주 유형 argmax
  7) 윙 결정 (인접 매핑)
  8) 스트레스/성장 화살 매핑
  9) 센터 매핑
  10) 18개 윙 조합 텍스트 조회
  11) 종교 중립 분기 (사용자 신앙 명시 시 텍스트 갈래 결정)
  12) 입력 검증 (Likert 1~5 범위, 응답 개수 18/27)

출처 (학계 표준):
  - Don R. Riso & Russ Hudson, "Personality Types" (1996, Houghton Mifflin)
  - Don R. Riso & Russ Hudson, "The Wisdom of the Enneagram" (1999, Bantam)
  - The Enneagram Institute (Riso-Hudson 공식 사이트)
"""

from __future__ import annotations

import json
import random
import sys
from typing import Dict, List, Optional, Tuple


# ============================================================
# (A) 9유형 정의 (Riso-Hudson 모델 — Personality Types 1996 / Wisdom 1999)
# ============================================================

TYPE_NAMES = {
    1: ("The Reformer", "개혁가", "改革者", "⚖"),
    2: ("The Helper", "조력자", "助人者", "❤"),
    3: ("The Achiever", "성취가", "成就者", "🏆"),
    4: ("The Individualist", "예술가", "个人主义者", "🎨"),
    5: ("The Investigator", "탐구가", "调研者", "🔬"),
    6: ("The Loyalist", "충성가", "忠诚者", "🛡"),
    7: ("The Enthusiast", "열정가", "热情者", "✨"),
    8: ("The Challenger", "도전가", "挑战者", "⚡"),
    9: ("The Peacemaker", "평화주의자", "和平使者", "🕊"),
}

# Riso-Hudson Basic Desire (출처: enneagraminstitute.com 공식 type descriptions)
CORE_DESIRE = {
    1: "선하고 옳고 완벽하며 모든 것을 개선하는 것 (to be good, to have integrity)",
    2: "사랑받는다고 느끼는 것 (to feel loved)",
    3: "가치 있고 인정받는 것 (to feel valuable and worthwhile)",
    4: "자기 자신과 자기 의미를 발견하는 것 (to find themselves and their significance)",
    5: "유능하고 역량 있는 것 (to be capable and competent)",
    6: "안전·지지·확신 (to have security and support)",
    7: "만족·충만 (to be satisfied and content)",
    8: "자기 자신을 보호하고 자기 인생을 통제하는 것 (to protect themselves, to be in control)",
    9: "내면 안정·마음의 평화 (to have inner stability, peace of mind)",
}

# Riso-Hudson Basic Fear (출처: enneagraminstitute.com 공식)
CORE_FEAR = {
    1: "부패·결함·악·심판 받는 것 (of being corrupt/evil, defective)",
    2: "사랑받지 못하고 필요 없는 존재가 되는 것 (of being unwanted, unworthy of being loved)",
    3: "가치 없고 성공 없이 실패하는 것 (of being worthless, without value)",
    4: "정체성이 없고 평범한 존재가 되는 것 (of having no identity or personal significance)",
    5: "무능하고 무기력하고 도움 안 되는 것 (being useless, helpless, or incapable)",
    6: "지지·안내·안전을 잃는 것 (of being without support and guidance)",
    7: "결핍·고통·갇히는 것 (of being deprived and in pain)",
    8: "통제당하고 다치고 취약해지는 것 (of being harmed or controlled by others)",
    9: "상실·분리·갈등 (of loss and separation)",
}

# 추구 세상 (원본 지침 한국어, SKILL.md와 1:1 동기화)
WORLD_SOUGHT_KO = {
    1: "윤리·법·질서·가치가 살아 있는 세상",
    2: "봉사·아웃리치·사랑으로 따뜻해지는 세상",
    3: "다양한 성취와 성공으로 탁월해지는 세상",
    4: "자유로운 자기표현·예술이 격려되는 아름다운 세상",
    5: "흥미로운 지적 탐구로 진화하는 창의적 세상",
    6: "다양한 공동체가 안정적으로 함께 사는 세상",
    7: "새로움과 혁신이 활발하고 흥미·재미 가득한 세상",
    8: "질서와 권력이 있는 강한 세상",
    9: "절제와 균형의 평화로운 세상",
}

# 비한국어 사용자용 영문 병기 (SKILL.md "원문 + 번역" 규약)
WORLD_SOUGHT_EN = {
    1: "A world where ethics, law, order, and value are alive",
    2: "A world made warm through service, outreach, and love",
    3: "A world made excellent through diverse achievements and success",
    4: "A beautiful world where free self-expression and art are encouraged",
    5: "A creative world that evolves through fascinating intellectual inquiry",
    6: "A world where diverse communities live together stably",
    7: "A world full of novelty, innovation, interest, and joy",
    8: "A strong world with order and power",
    9: "A peaceful world of moderation and balance",
}

WORLD_SOUGHT_ZH = {
    1: "伦理·法律·秩序·价值充满的世界",
    2: "通过服侍·外展·爱而温暖的世界",
    3: "通过多样的成就和成功而卓越的世界",
    4: "鼓励自由自我表达·艺术的美丽世界",
    5: "通过有趣的知识探索而进化的创意世界",
    6: "多样社区稳定共存的世界",
    7: "充满新奇·创新·乐趣的世界",
    8: "有秩序和权力的强大世界",
    9: "节制与平衡的和平世界",
}


# ============================================================
# (B) 27문항 카탈로그 (각 유형 3문항, 블록 A 2 + 블록 B 1)
# ============================================================
# SKILL.md 카탈로그와 1:1 동기화 — 변경 금지

QUESTIONS_KO = {
    "Q01": (1, "옳고 그름이 분명하지 않은 상황에서 강한 불편함을 느끼며, 옳은 방향으로 바로잡고 싶은 충동이 자주 든다."),
    "Q02": (1, "내가 부패하거나 잘못된 사람이 되는 것을 가장 두려워한다."),
    "Q03": (1, "일을 할 때 완벽하지 않으면 만족스럽지 않다."),
    "Q04": (2, "다른 사람이 나를 사랑하지 않거나 필요로 하지 않을까 가장 두려워한다."),
    "Q05": (2, "내 욕구보다 다른 사람의 욕구를 먼저 살피게 된다."),
    "Q06": (2, "누군가에게 도움이 되었다는 느낌에서 가장 큰 만족을 얻는다."),
    "Q07": (3, "성공·성취가 없으면 내 가치가 없다고 느낀다."),
    "Q08": (3, "내가 가치 없고 실패한 사람이 되는 것을 가장 두려워한다."),
    "Q09": (3, "사람들 앞에서 유능하고 멋진 모습을 보여주는 것이 매우 중요하다."),
    "Q10": (4, "나는 남들과 본질적으로 다른 사람이라고 느낀다."),
    "Q11": (4, "내가 정체성이 없고 평범한 사람이 되는 것을 가장 두려워한다."),
    "Q12": (4, "깊은 감정·미적 경험에서 살아있음을 가장 강하게 느낀다."),
    "Q13": (5, "사람들과의 만남보다 혼자 깊이 탐구하는 시간이 더 만족스럽다."),
    "Q14": (5, "내가 무능하고 도움이 안 되는 사람이 되는 것을 가장 두려워한다."),
    "Q15": (5, "어떤 주제든 충분히 이해하고 알아야 행동할 수 있다."),
    "Q16": (6, "새로운 상황에서 위험·위협을 먼저 살피게 된다."),
    "Q17": (6, "내가 지지·안전·확신을 잃는 것을 가장 두려워한다."),
    "Q18": (6, "신뢰할 수 있는 공동체·시스템을 매우 중요하게 여긴다."),
    "Q19": (7, "한 가지에 머물러 있으면 답답하고 새로운 경험을 찾아 나서게 된다."),
    "Q20": (7, "내가 고통·결핍·갇힘에 사로잡히는 것을 가장 두려워한다."),
    "Q21": (7, "항상 재미·즐거움·새 가능성에 끌린다."),
    "Q22": (8, "누가 나를 통제하거나 약하게 만드는 것을 참을 수 없다."),
    "Q23": (8, "내가 통제당하거나 다치거나 약해지는 것을 가장 두려워한다."),
    "Q24": (8, "약자를 보호하기 위해 내 힘을 쓰는 것에 자부심을 느낀다."),
    "Q25": (9, "갈등 상황에서 내 입장을 강하게 주장하기보다 조화를 맞추려 한다."),
    "Q26": (9, "내가 상실·분리·갈등에 휘말리는 것을 가장 두려워한다."),
    "Q27": (9, "내적 평화·균형이 가장 큰 가치다."),
}

QUESTIONS_EN = {
    "Q01": (1, "In situations where right and wrong are unclear, I feel strong discomfort and urge to correct it."),
    "Q02": (1, "I most fear becoming corrupt or a wrong person."),
    "Q03": (1, "I am not satisfied unless my work is perfect."),
    "Q04": (2, "I most fear that others will not love me or need me."),
    "Q05": (2, "I tend to attend to others' needs before my own."),
    "Q06": (2, "I get the greatest satisfaction from being helpful to someone."),
    "Q07": (3, "Without success and achievement, I feel I have no value."),
    "Q08": (3, "I most fear being worthless and a failure."),
    "Q09": (3, "It is very important to look competent and impressive in front of people."),
    "Q10": (4, "I feel essentially different from others."),
    "Q11": (4, "I most fear becoming someone without identity or ordinary."),
    "Q12": (4, "I feel most alive through deep emotional and aesthetic experiences."),
    "Q13": (5, "I find time alone for deep inquiry more satisfying than meeting people."),
    "Q14": (5, "I most fear becoming incompetent and useless."),
    "Q15": (5, "I must understand any topic sufficiently before I can act."),
    "Q16": (6, "In new situations I first scan for dangers and threats."),
    "Q17": (6, "I most fear losing support, safety, or assurance."),
    "Q18": (6, "I greatly value trustworthy communities and systems."),
    "Q19": (7, "Staying with one thing feels stifling; I seek new experiences."),
    "Q20": (7, "I most fear being trapped in pain, deprivation, or confinement."),
    "Q21": (7, "I am always drawn to fun, joy, and new possibilities."),
    "Q22": (8, "I cannot tolerate anyone controlling me or making me weak."),
    "Q23": (8, "I most fear being controlled, hurt, or weakened."),
    "Q24": (8, "I take pride in using my strength to protect the weak."),
    "Q25": (9, "In conflict, I try to harmonize rather than strongly assert my position."),
    "Q26": (9, "I most fear being caught in loss, separation, or conflict."),
    "Q27": (9, "Inner peace and balance are my greatest value."),
}

QUESTIONS_ZH = {
    "Q01": (1, "在对错不明的情况下，我感到强烈的不适，常想把事情纠正到正确的方向。"),
    "Q02": (1, "我最害怕变成腐败或错误的人。"),
    "Q03": (1, "做事如果不完美我就不满足。"),
    "Q04": (2, "我最害怕别人不爱我或不需要我。"),
    "Q05": (2, "我倾向于先关注别人的需要而不是自己的。"),
    "Q06": (2, "从对某人有帮助的感觉中获得最大满足。"),
    "Q07": (3, "没有成功和成就，我觉得自己没有价值。"),
    "Q08": (3, "我最害怕成为没有价值和失败的人。"),
    "Q09": (3, "在人面前显得能干和出色对我非常重要。"),
    "Q10": (4, "我觉得自己本质上与众不同。"),
    "Q11": (4, "我最害怕成为没有身份、平凡的人。"),
    "Q12": (4, "在深刻的情感和审美体验中我最强烈地感到活着。"),
    "Q13": (5, "独自深入探究比与人见面更让我满足。"),
    "Q14": (5, "我最害怕成为无能和无用的人。"),
    "Q15": (5, "我必须充分理解任何课题才能行动。"),
    "Q16": (6, "在新情况下我会首先察看危险和威胁。"),
    "Q17": (6, "我最害怕失去支持、安全和信心。"),
    "Q18": (6, "我非常重视可信赖的群体和系统。"),
    "Q19": (7, "一直停留在一件事上让我憋闷，会寻找新体验。"),
    "Q20": (7, "我最害怕被痛苦、缺乏和受困所束缚。"),
    "Q21": (7, "我始终被乐趣、快乐和新的可能性所吸引。"),
    "Q22": (8, "我无法忍受任何人控制我或让我变弱。"),
    "Q23": (8, "我最害怕被控制、受伤或变弱。"),
    "Q24": (8, "用我的力量保护弱者让我感到自豪。"),
    "Q25": (9, "在冲突中我宁可调和而不强力主张自己。"),
    "Q26": (9, "我最害怕被卷入丧失、分离或冲突中。"),
    "Q27": (9, "内在的平和与均衡是我最大的价值。"),
}

LANGUAGE_TO_QUESTIONS = {"ko": QUESTIONS_KO, "en": QUESTIONS_EN, "zh": QUESTIONS_ZH}

# 블록 A (각 유형 첫 두 문항) — SKILL.md §출제 방식 1단계 명시
BLOCK_A = ["Q01", "Q02", "Q04", "Q05", "Q07", "Q08", "Q10", "Q11", "Q13",
           "Q14", "Q16", "Q17", "Q19", "Q20", "Q22", "Q23", "Q25", "Q26"]
# 블록 B (각 유형 세 번째 문항)
BLOCK_B = ["Q03", "Q06", "Q09", "Q12", "Q15", "Q18", "Q21", "Q24", "Q27"]


# ============================================================
# (C) 동적 관계 매핑 (출처: Riso-Hudson, Personality Types 1996, Wisdom 1999)
# ============================================================

# Direction of Disintegration (Stress Arrow) — 표준
STRESS_ARROW = {1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6}

# Direction of Integration (Growth Arrow) — 표준
GROWTH_ARROW = {1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3}

# Wing 인접 매핑 (에니어그램 원형의 인접 두 유형)
WING_NEIGHBORS = {
    1: (9, 2),
    2: (1, 3),
    3: (2, 4),
    4: (3, 5),
    5: (4, 6),
    6: (5, 7),
    7: (6, 8),
    8: (7, 9),
    9: (8, 1),
}

# 센터 (Triadic groupings) — 표준 Riso-Hudson
CENTER = {
    1: ("본능 (Instinctive/Gut)", "Instinctive Triad", "本能中心"),
    8: ("본능 (Instinctive/Gut)", "Instinctive Triad", "本能中心"),
    9: ("본능 (Instinctive/Gut)", "Instinctive Triad", "本能中心"),
    2: ("감정 (Feeling/Heart)", "Feeling Triad", "情感中心"),
    3: ("감정 (Feeling/Heart)", "Feeling Triad", "情感中心"),
    4: ("감정 (Feeling/Heart)", "Feeling Triad", "情感中心"),
    5: ("사고 (Thinking/Head)", "Thinking Triad", "思考中心"),
    6: ("사고 (Thinking/Head)", "Thinking Triad", "思考中心"),
    7: ("사고 (Thinking/Head)", "Thinking Triad", "思考中心"),
}


# ============================================================
# (D) 셔플 / 점수 / 결정 함수
# ============================================================

def stratified_shuffle(seed: int) -> Tuple[List[str], List[str]]:
    """
    SKILL.md §출제 방식 1단계: 블록 A 18문항 · 블록 B 9문항 각각 무작위 셔플.
    동일 seed → 동일 순서 (재현 가능성).
    """
    rng_a = random.Random(seed)
    rng_b = random.Random(seed + 1)
    a = BLOCK_A[:]
    b = BLOCK_B[:]
    rng_a.shuffle(a)
    rng_b.shuffle(b)
    return a, b


def validate_answers(answers: Dict[str, int], required_qids: List[str]) -> List[str]:
    """
    Likert 1~5 범위 검증, 필수 문항 누락 검증.
    반환: 오류 메시지 목록 (빈 리스트면 통과)
    """
    errors = []
    for qid in required_qids:
        if qid not in answers:
            errors.append(f"누락된 응답: {qid}")
            continue
        v = answers[qid]
        if not isinstance(v, int) or v < 1 or v > 5:
            errors.append(f"{qid}: Likert 1~5 범위 초과 (입력: {v!r})")
    return errors


def score_types(answers: Dict[str, int], qid_pool: List[str]) -> Dict[int, int]:
    """
    qid_pool 내 응답들의 유형별 합계를 산출.
    18문항 1차 산출 시 → qid_pool = BLOCK_A (각 유형 2문항)
    27문항 완성 산출 시 → qid_pool = BLOCK_A + BLOCK_B (각 유형 3문항)
    """
    scores = {t: 0 for t in range(1, 10)}
    for qid in qid_pool:
        if qid not in answers:
            continue
        type_id, _ = QUESTIONS_KO[qid]
        scores[type_id] += answers[qid]
    return scores


def detect_top_tie(scores: Dict[int, int]) -> Tuple[int, List[int]]:
    """
    1위 점수와 1위 동점 유형 목록 반환.
    """
    max_score = max(scores.values())
    tied = sorted([t for t, s in scores.items() if s == max_score])
    return max_score, tied


def decide_primary(scores: Dict[int, int]) -> Tuple[int, bool, List[int]]:
    """
    주 유형 결정.
    반환: (주 유형, 동점 여부, 동점 유형 목록)
    """
    _, tied = detect_top_tie(scores)
    return tied[0], len(tied) > 1, tied


def decide_wing(primary: int, scores: Dict[int, int]) -> Tuple[Optional[int], bool, Tuple[int, int]]:
    """
    윙 결정.
    SKILL.md §6단계 윙: 주 유형의 인접 두 유형 중 점수 높은 쪽.
    반환: (윙 유형 또는 None, 동점 여부, 인접 두 유형 튜플)
    """
    left, right = WING_NEIGHBORS[primary]
    ls, rs = scores[left], scores[right]
    if ls > rs:
        return left, False, (left, right)
    if rs > ls:
        return right, False, (left, right)
    return None, True, (left, right)


def build_result(
    answers: Dict[str, int],
    use_full_27: bool = False,
) -> Dict:
    """
    풀 결과 dict 산출 (LLM이 그대로 인용할 수 있는 결정론적 데이터).
    use_full_27=False → 18문항 1차 산출
    use_full_27=True  → 27문항 완성 산출
    """
    qid_pool = BLOCK_A + BLOCK_B if use_full_27 else BLOCK_A
    errors = validate_answers(answers, qid_pool)
    if errors:
        return {"status": "error", "errors": errors}

    scores = score_types(answers, qid_pool)
    primary, primary_tie, tied = decide_primary(scores)

    if primary_tie and not use_full_27:
        return {
            "status": "needs_tiebreaker",
            "scores_18": scores,
            "tied_types": tied,
            "additional_qids": BLOCK_B,  # 추가 출제 필요 9문항
        }

    wing, wing_tie, wing_neighbors = decide_wing(primary, scores)

    result = {
        "status": "complete",
        "scores": scores,
        "qid_count": len(qid_pool),
        "primary": primary,
        "primary_tie": primary_tie,
        "tied_types": tied,
        "wing": wing,
        "wing_tie": wing_tie,
        "wing_neighbors": list(wing_neighbors),
        "stress_arrow_to": STRESS_ARROW[primary],
        "growth_arrow_to": GROWTH_ARROW[primary],
        "center_ko": CENTER[primary][0],
        "center_en": CENTER[primary][1],
        "center_zh": CENTER[primary][2],
        "type_name_en": TYPE_NAMES[primary][0],
        "type_name_ko": TYPE_NAMES[primary][1],
        "type_name_zh": TYPE_NAMES[primary][2],
        "emoji": TYPE_NAMES[primary][3],
        "core_desire": CORE_DESIRE[primary],
        "core_fear": CORE_FEAR[primary],
        "world_sought_ko": WORLD_SOUGHT_KO[primary],
        "world_sought_en": WORLD_SOUGHT_EN[primary],
        "world_sought_zh": WORLD_SOUGHT_ZH[primary],
    }

    if wing is not None:
        result["wing_combination"] = f"{primary}w{wing}"
    else:
        result["wing_combination"] = f"{primary}w?(동점 — 사용자 자기 체감 선택 필요)"
        result["wing_options"] = [f"{primary}w{wing_neighbors[0]}", f"{primary}w{wing_neighbors[1]}"]

    return result


# ============================================================
# (E) 보조 결정론 함수 — 언어 감지·종교 중립 감지·점수 입력 파싱
# ============================================================

def detect_language(text: str) -> str:
    """
    텍스트의 문자 구성으로 ko/en/zh 자동 감지.
    한글 우선 → 한자 → 영어. LLM 자연어 추론보다 강한 결정성 보장.
    """
    if not text:
        return "ko"
    hangul = sum(1 for c in text if "가" <= c <= "힣")
    cjk = sum(1 for c in text if "一" <= c <= "鿿" and not ("가" <= c <= "힣"))
    latin = sum(1 for c in text if c.isascii() and c.isalpha())
    if hangul >= max(cjk, latin):
        return "ko"
    if cjk > latin:
        return "zh"
    return "en"


RELIGION_NEUTRAL_KEYS = [
    # 한국어
    "종교 없음", "종교없음", "비종교", "성경 빼", "성경빼", "성경 없이",
    "종교 빼", "종교빼", "무종교", "무신론",
    # English
    "no religion", "skip bible", "secular", "non-religious", "atheist",
    "without bible", "no scripture",
    # 中文
    "无宗教", "无神论", "跳过圣经",
]


def detect_religion_neutral(text: str) -> bool:
    """사용자 메시지에 종교 중립 키워드가 있는지 결정론적으로 검출."""
    if not text:
        return False
    lowered = text.lower()
    return any(k.lower() in lowered for k in RELIGION_NEUTRAL_KEYS)


def parse_score_input(text: str) -> Optional[Dict[int, int]]:
    """
    유형 B 입력 (점수만 입력) 결정론 파서.
    예: "Type 4=12, Type 1=10, Type 9=8, ..."
    예: "4=12 1=10 9=8"
    반환: {유형 번호: 점수} dict. 9유형 모두 있을 때만 유효.
    """
    import re
    if not text:
        return None
    pattern = re.compile(r"(?:type\s*)?([1-9])\s*[:=]\s*(\d+)", re.IGNORECASE)
    matches = pattern.findall(text)
    if len(matches) < 9:
        return None
    result = {}
    for t_str, s_str in matches:
        t = int(t_str)
        s = int(s_str)
        if t in result:
            continue  # 중복 무시 (첫 매치 우선)
        if s < 2 or s > 15:  # 점수 범위 (2~15: 2문항 합 또는 3문항 합)
            return None
        result[t] = s
    if set(result.keys()) != set(range(1, 10)):
        return None
    return result


def decide_from_scores(scores: Dict[int, int]) -> Dict:
    """
    이미 산출된 유형별 점수를 받아 주 유형·윙·관계 등 결정.
    유형 B 입력에 사용.
    """
    primary, primary_tie, tied = decide_primary(scores)
    wing, wing_tie, wing_neighbors = decide_wing(primary, scores)
    result = {
        "status": "complete",
        "scores": scores,
        "primary": primary,
        "primary_tie": primary_tie,
        "tied_types": tied,
        "wing": wing,
        "wing_tie": wing_tie,
        "wing_neighbors": list(wing_neighbors),
        "stress_arrow_to": STRESS_ARROW[primary],
        "growth_arrow_to": GROWTH_ARROW[primary],
        "center_ko": CENTER[primary][0],
        "center_en": CENTER[primary][1],
        "center_zh": CENTER[primary][2],
        "type_name_en": TYPE_NAMES[primary][0],
        "type_name_ko": TYPE_NAMES[primary][1],
        "type_name_zh": TYPE_NAMES[primary][2],
        "emoji": TYPE_NAMES[primary][3],
        "core_desire": CORE_DESIRE[primary],
        "core_fear": CORE_FEAR[primary],
        "world_sought_ko": WORLD_SOUGHT_KO[primary],
        "world_sought_en": WORLD_SOUGHT_EN[primary],
        "world_sought_zh": WORLD_SOUGHT_ZH[primary],
    }
    if wing is not None:
        result["wing_combination"] = f"{primary}w{wing}"
    else:
        result["wing_combination"] = f"{primary}w?(동점 — 사용자 자기 체감 선택 필요)"
        result["wing_options"] = [f"{primary}w{wing_neighbors[0]}", f"{primary}w{wing_neighbors[1]}"]
    return result


# ============================================================
# (F) CLI 진입점
# ============================================================

def cmd_shuffle(args):
    seed = int(args[0]) if args else 42
    a, b = stratified_shuffle(seed)
    print(json.dumps({"seed": seed, "block_a_order": a, "block_b_order": b}, ensure_ascii=False, indent=2))


def cmd_questions(args):
    lang = args[0] if args else "ko"
    pool = LANGUAGE_TO_QUESTIONS.get(lang, QUESTIONS_KO)
    print(json.dumps({qid: {"type": t, "text": txt} for qid, (t, txt) in pool.items()},
                     ensure_ascii=False, indent=2))


def cmd_score(args):
    """
    표준 입력 JSON: {"answers": {"Q01": 4, ...}, "use_full_27": bool}
    """
    payload = json.loads(sys.stdin.read())
    answers = payload["answers"]
    use_full_27 = payload.get("use_full_27", False)
    result = build_result(answers, use_full_27=use_full_27)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_lookup(args):
    """
    유형 단독 조회 (입력 유형 B/C/D용): 유형 번호와 윙 → 결정론 데이터 일괄 제공.
    인자: <primary> [wing]
    """
    if not args:
        print(json.dumps({"error": "primary type 인자 필요 (1~9)"}, ensure_ascii=False))
        return
    primary = int(args[0])
    if primary < 1 or primary > 9:
        print(json.dumps({"error": f"유형 번호는 1~9이어야 함 (입력: {primary})"}, ensure_ascii=False))
        return
    wing = None
    if len(args) > 1 and args[1] not in ("?", "none"):
        wing = int(args[1])
        if wing not in WING_NEIGHBORS[primary]:
            print(json.dumps({
                "error": f"유형 {primary}의 인접 유형은 {WING_NEIGHBORS[primary]} 뿐 (입력 윙: {wing})"
            }, ensure_ascii=False))
            return
    out = {
        "primary": primary,
        "wing": wing,
        "wing_neighbors": list(WING_NEIGHBORS[primary]),
        "type_name_en": TYPE_NAMES[primary][0],
        "type_name_ko": TYPE_NAMES[primary][1],
        "type_name_zh": TYPE_NAMES[primary][2],
        "emoji": TYPE_NAMES[primary][3],
        "core_desire": CORE_DESIRE[primary],
        "core_fear": CORE_FEAR[primary],
        "world_sought_ko": WORLD_SOUGHT_KO[primary],
        "world_sought_en": WORLD_SOUGHT_EN[primary],
        "world_sought_zh": WORLD_SOUGHT_ZH[primary],
        "stress_arrow_to": STRESS_ARROW[primary],
        "growth_arrow_to": GROWTH_ARROW[primary],
        "center_ko": CENTER[primary][0],
        "center_en": CENTER[primary][1],
        "center_zh": CENTER[primary][2],
        "wing_combination": f"{primary}w{wing}" if wing else f"{primary}w?",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_detect(args):
    """
    텍스트에서 언어와 종교 중립 여부를 결정론적으로 감지.
    표준 입력으로 텍스트를 받음.
    """
    text = sys.stdin.read()
    out = {
        "language": detect_language(text),
        "religion_neutral": detect_religion_neutral(text),
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_parse_scores(args):
    """
    유형 B 입력 (점수만 입력) 파싱.
    표준 입력으로 텍스트를 받음. 파싱 성공 시 주 유형·윙 등 결정 결과 출력.
    """
    text = sys.stdin.read()
    scores = parse_score_input(text)
    if scores is None:
        print(json.dumps({
            "status": "parse_failed",
            "hint": "9유형 모두 'Type N=M' 또는 'N=M' 형식으로 입력 필요. 점수는 2~15 범위."
        }, ensure_ascii=False, indent=2))
        return
    result = decide_from_scores(scores)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        print("사용법: enneagram_engine.py <command> [args]")
        print("commands: shuffle [seed] | questions [ko|en|zh] | score (stdin JSON) | "
              "lookup <primary> [wing] | detect (stdin text) | parse_scores (stdin text)")
        sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    {
        "shuffle": cmd_shuffle,
        "questions": cmd_questions,
        "score": cmd_score,
        "lookup": cmd_lookup,
        "detect": cmd_detect,
        "parse_scores": cmd_parse_scores,
    }[cmd](args)


if __name__ == "__main__":
    main()
