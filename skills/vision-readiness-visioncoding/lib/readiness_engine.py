"""
vision-readiness-visioncoding 결정론 엔진.

LLM 자연어 추론에서 분리해 결정론적으로 처리하는 작업:
  1. 점수 입력 파싱 (5종 형식: 공식/콤마/한국어 자연어/줄바꿈/혼합)
  2. 범위 검증 (0~10 정수, 음수·11+ 자동 거부)
  3. 누락 검증 (20개 모두 존재 여부)
  4. 능력별 평균 산출 (5문항 / 5)
  5. Composite 산출 (4능력 평균)
  6. 레벨 매핑 (정수부 기반)
  7. ASCII 막대 그래프 생성 (1/8 partial block 매핑)
  8. Mermaid xychart 생성
  9. 강점·성장 영역 분류 (7+ / 6-)
 10. 처방 스킬 매핑
 11. 한 줄 요약(재진단 비교용) 생성
 12. 변화 추적 (재진단 시 이전 점수와 델타 계산)

순수 함수. 외부 I/O 없음. import 후 단위 테스트 가능.
"""

from __future__ import annotations

import re
import json
import sys
from dataclasses import dataclass, asdict
from datetime import date
from typing import Optional


# ===== 상수 (SKILL.md의 절대 원칙·체계와 1:1 대응) =====

SKILL_NAMES_EN = [
    "Big Picture",
    "Reframing Goals",
    "Creating Strategies",
    "Following Through",
]

SKILL_NAMES_KO = [
    "큰 그림 보기",
    "영감을 현실적 목표로 재구성",
    "목표 달성 전략 수립",
    "계획 실행 지속력",
]

# 각 능력당 5문항씩, 능력 1: Q01-Q05, 능력 2: Q06-Q10, ...
QUESTIONS_PER_SKILL = 5
NUM_SKILLS = 4
NUM_QUESTIONS = QUESTIONS_PER_SKILL * NUM_SKILLS  # 20

# 0~10 척도 레벨 라벨 (SKILL.md 0~10 척도 가이드 표와 동일)
LEVEL_LABELS = {
    10: ("World Class", "이 능력에서 세계 최고 수준. 대부분의 사람이 도달 못 하는 영역"),
    9: ("Exceptional", "매우 드문 탁월함. 100명 중 1명 수준"),
    8: ("Strong", "분명한 강점. 또래 상위 10%"),
    7: ("Above Average", "평균보다 확실히 위"),
    6: ("Solid", "평균. 안정적이고 신뢰할 만함"),
    5: ("Average", "정확히 평균. 어떤 날은 잘하고 어떤 날은 흔들림"),
    4: ("Developing", "평균보다 약간 낮음. 의식적 노력 필요"),
    3: ("Poor", "약점 영역. 자주 어려움을 겪음"),
    2: ("Weak", "분명한 약점. 이 능력 없이는 진척이 어려움"),
    1: ("Very Weak", "거의 작동하지 않음. 의도적 훈련 시급"),
    0: ("Not Yet", "아직 시작 전. 인식만 있고 실천 경험 없음"),
}

# 1/8 partial block 매핑 (SKILL.md 표 그대로)
# 키: (lo, hi] 범위 — partial value (0.0~1.0)에 대응하는 유니코드 블록.
# 0.000~0.062 = 빈 칸 ░, 0.938~1.000 = 가득 █, 나머지는 8분의 1 단위.
PARTIAL_BLOCK_TABLE = [
    (0.0625, "░"),   # 0.000~0.062
    (0.1875, "▏"),   # 0.063~0.187 (1/8)
    (0.3125, "▎"),   # 0.188~0.312 (2/8)
    (0.4375, "▍"),   # 0.313~0.437 (3/8)
    (0.5625, "▌"),   # 0.438~0.562 (4/8)
    (0.6875, "▋"),   # 0.563~0.687 (5/8)
    (0.8125, "▊"),   # 0.688~0.812 (6/8)
    (0.9375, "▉"),   # 0.813~0.937 (7/8)
    (1.0001, "█"),   # 0.938~1.000 (8/8)
]

FULL_BLOCK = "█"
EMPTY_BLOCK = "░"

# 처방 스킬 매핑 (SKILL.md 약점 → 1순위 처방 스킬 표)
PRESCRIPTION_MAP = {
    "Big Picture": [
        "vision-future-needs-prediction",
        "vision-futures-timeline-map",
    ],
    "Reframing Goals": [
        "vision-goal-reframing",
        "vision-statement-writer",
    ],
    "Creating Strategies": [
        "vision-strategy-coach",
        "vision-eight-training-areas",
    ],
    "Following Through": [
        "vision-follow-through-habits",
        "vision-progress-review",
    ],
}


# ===== 예외 =====


class ReadinessError(ValueError):
    """결정론 검증 실패. SKILL.md '응답 검증' 절을 강제하는 단일 예외."""


# ===== 1. 파싱 =====


_RE_Q_PREFIX = re.compile(
    r"[QqＱ]\s*0*(\d{1,2})\s*[:=\s\)\.]\s*(-?\d{1,3})"
)
_RE_KOREAN_LABEL = re.compile(
    r"(?:문항|번호|문제)\s*0*(\d{1,2})\s*[:=\s\)\.]\s*(-?\d{1,3})"
)
_RE_KOREAN_NUM_BUN_PT = re.compile(
    r"(?<![\dQqＱ])0*(\d{1,2})\s*번\s*[은는의에이가도]?\s*(-?\d{1,3})\s*점"
)
_RE_NUM_COLON = re.compile(
    r"(?<![\dQqＱ])0*(\d{1,2})\s*[:=]\s*(-?\d{1,3})"
)


def _add_explicit(result: dict, qn: int, sc: int) -> None:
    if qn in result and result[qn] != sc:
        raise ReadinessError(
            f"Q{qn:02d}에 서로 다른 점수가 두 번 이상 입력되었습니다: "
            f"{result[qn]} vs {sc}"
        )
    result[qn] = sc


def parse_scores(raw: str) -> dict[int, int]:
    """
    사용자 입력 raw 문자열을 {질문번호: 점수} dict로 변환.

    지원 형식:
      A. 공식: "Q01: 7\nQ02: 8\n..."  또는 "Q1: 7\nQ2: 8\n..."  또는 "1: 7\n..."
      B. 콤마 분리: "7, 8, 6, 9, ..." (정확히 20개)
      C. 한국어 자연어: "1번 8점, 2번 7점, ..."
      D. 줄바꿈 분리: "8\n7\n9\n..." (정확히 20줄)
      E. 혼합: 명시적 (번호:점수) 매핑이 5개 이상이면 explicit 모드,
         그 외 단순 숫자 20개 시퀀스로 fallback.

    범위 검증·누락 검증은 별도 함수가 담당 (parse는 매핑만 책임).
    """
    if not isinstance(raw, str) or not raw.strip():
        raise ReadinessError("입력이 비어 있습니다.")

    text = raw.strip()

    explicit: dict[int, int] = {}

    # 1) Q-prefix 패턴 (Q01: 7, Q1: 7, Q01=7, Q01 7)
    for m in _RE_Q_PREFIX.finditer(text):
        qn, sc = int(m.group(1)), int(m.group(2))
        if 1 <= qn <= 99:
            _add_explicit(explicit, qn, sc)

    # 2) 한국어 라벨 (문항01: 7 등)
    for m in _RE_KOREAN_LABEL.finditer(text):
        qn, sc = int(m.group(1)), int(m.group(2))
        if 1 <= qn <= 99:
            _add_explicit(explicit, qn, sc)

    # 3) 한국어 자연어 (1번 7점)
    for m in _RE_KOREAN_NUM_BUN_PT.finditer(text):
        qn, sc = int(m.group(1)), int(m.group(2))
        if 1 <= qn <= 99:
            _add_explicit(explicit, qn, sc)

    # 4) 단순 콜론 매핑 — Q-prefix 매칭에 이미 들어간 위치는 제외
    # Q-prefix 이미 잡은 (qn, sc) 페어를 그대로 통과하므로 충돌 검사가 자연스럽게 동작
    for m in _RE_NUM_COLON.finditer(text):
        qn, sc = int(m.group(1)), int(m.group(2))
        if 1 <= qn <= 99:
            _add_explicit(explicit, qn, sc)

    if len(explicit) >= 5:
        return explicit

    # Fallback — 명시 매핑이 없거나 부족하면 단순 숫자 시퀀스로 시도
    nums = re.findall(r"-?\d+", text)
    if len(nums) == NUM_QUESTIONS:
        return {i + 1: int(n) for i, n in enumerate(nums)}

    if len(nums) == 0:
        raise ReadinessError("입력에서 숫자를 하나도 찾지 못했습니다.")

    raise ReadinessError(
        f"입력 형식이 모호합니다. 숫자 {len(nums)}개가 추출됐지만 "
        f"20개 시퀀스도 아니고 명시적 (번호:점수) 매핑도 부족합니다. "
        f"'Q01: 7, Q02: 8, ...' 또는 콤마 분리 20개 형식으로 다시 입력해 주세요."
    )


# ===== 2. 범위 검증 =====


def validate_range(scores: dict[int, int]) -> None:
    """모든 점수가 0~10 정수인지 검사. 음수·11+ 발견 시 예외."""
    bad = []
    for qn, sc in scores.items():
        if not isinstance(sc, int):
            bad.append((qn, sc, "정수가 아님"))
        elif sc < 0 or sc > 10:
            bad.append((qn, sc, "0~10 범위 밖"))
    if bad:
        msg = "; ".join(f"Q{qn:02d}={sc} ({reason})" for qn, sc, reason in bad)
        raise ReadinessError(f"범위 위반 점수: {msg}")


# ===== 3. 누락 검증 =====


def validate_completeness(scores: dict[int, int]) -> None:
    """20문항 모두 입력되었는지. 누락 발견 시 어느 번호인지 명시."""
    expected = set(range(1, NUM_QUESTIONS + 1))
    actual = set(scores.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        parts = []
        if missing:
            parts.append("누락: " + ", ".join(f"Q{m:02d}" for m in missing))
        if extra:
            parts.append("범위 밖 번호: " + ", ".join(f"Q{e:02d}" for e in extra))
        raise ReadinessError("; ".join(parts))


def validate_all(scores: dict[int, int]) -> None:
    """범위 + 누락을 한 번에 검사. 외부에서 한 호출로 끝낼 수 있게."""
    validate_completeness(scores)
    validate_range(scores)


# ===== 4. 평균 산출 =====


@dataclass
class SkillScore:
    name_en: str
    name_ko: str
    score: float  # 소수점 첫째자리 반올림
    raw_sum: int
    raw_items: list[int]  # 5개 원점수
    skill_index: int  # 0..3


def _round1(x: float) -> float:
    """소수점 첫째자리 ROUND HALF UP. Python 기본 round는 banker's rounding."""
    return float(f"{x + 1e-9:.1f}") if x >= 0 else -float(f"{-x + 1e-9:.1f}")


def calculate_skill_scores(scores: dict[int, int]) -> list[SkillScore]:
    """4능력 점수를 산출. 각 능력 = 5문항 합 / 5, 소수점 1자리."""
    validate_all(scores)
    results = []
    for i in range(NUM_SKILLS):
        start_q = i * QUESTIONS_PER_SKILL + 1
        end_q = start_q + QUESTIONS_PER_SKILL  # exclusive
        items = [scores[q] for q in range(start_q, end_q)]
        total = sum(items)
        avg = _round1(total / QUESTIONS_PER_SKILL)
        results.append(SkillScore(
            name_en=SKILL_NAMES_EN[i],
            name_ko=SKILL_NAMES_KO[i],
            score=avg,
            raw_sum=total,
            raw_items=items,
            skill_index=i,
        ))
    return results


def calculate_composite(skill_scores: list[SkillScore]) -> float:
    """4능력 평균. 소수점 둘째자리까지(SKILL.md 예시: 6.65)."""
    if len(skill_scores) != NUM_SKILLS:
        raise ReadinessError(f"능력 점수가 {len(skill_scores)}개. {NUM_SKILLS}개 필요.")
    s = sum(sk.score for sk in skill_scores)
    return round(s / NUM_SKILLS + 1e-9, 2)


# ===== 5. 레벨 매핑 =====


def level_for(score: float) -> tuple[str, str]:
    """
    점수 → (레벨라벨, 설명). 정수부 기반 매핑.
    SKILL.md '레벨 매핑 규칙: 점수의 정수 부분을 기준으로 라벨 부여' 그대로.
    """
    if score < 0 or score > 10:
        raise ReadinessError(f"레벨 매핑 입력 범위 위반: {score}")
    int_part = int(score)  # 7.4 → 7, 8.0 → 8
    # 10.0의 경우만 예외 — 정수부 10
    if int_part > 10:
        int_part = 10
    return LEVEL_LABELS[int_part]


def next_level_hint(score: float) -> Optional[str]:
    """소수부 ≥ 0.5인 경우에만 '→ 다음 단계' 라벨을 부기. 그 외 None."""
    if score < 0 or score >= 10:
        return None
    int_part = int(score)
    frac = score - int_part
    if frac >= 0.5 - 1e-9:
        next_int = int_part + 1
        if next_int <= 10:
            return LEVEL_LABELS[next_int][0]
    return None


# ===== 6. 강점·성장 영역 분류 =====


def classify_strengths(skill_scores: list[SkillScore]) -> dict[str, list[SkillScore]]:
    """
    SKILL.md 출력 체크리스트 기준:
      - 강점 (Strengths): 7점 이상
      - 성장 영역 (Growth Areas): 6점 이하
    경계값 7.0은 강점에 포함(>= 7.0), 6.9는 성장 영역.
    """
    strengths = [s for s in skill_scores if s.score >= 7.0 - 1e-9]
    growth = [s for s in skill_scores if s.score < 7.0 - 1e-9]
    return {"strengths": strengths, "growth_areas": growth}


# ===== 7. 처방 스킬 매핑 =====


def prescriptions_for(skill_scores: list[SkillScore]) -> list[dict]:
    """
    성장 영역(6점 이하) 각 능력에 대해 1순위 처방 스킬을 매핑.
    가장 약한 능력부터 우선순위.
    """
    growth = sorted(
        [s for s in skill_scores if s.score < 7.0 - 1e-9],
        key=lambda s: s.score,
    )
    result = []
    for sk in growth:
        result.append({
            "skill_en": sk.name_en,
            "skill_ko": sk.name_ko,
            "score": sk.score,
            "level": level_for(sk.score)[0],
            "prescriptions": PRESCRIPTION_MAP[sk.name_en],
        })
    return result


# ===== 8. ASCII 막대 차트 =====


def partial_block_for(partial: float) -> str:
    """0.0~1.0 사이 partial 값을 가장 가까운 1/8 블록 문자로."""
    if partial < 0:
        partial = 0.0
    if partial > 1.0:
        partial = 1.0
    for upper, block in PARTIAL_BLOCK_TABLE:
        if partial < upper:
            return block
    return FULL_BLOCK


def render_ascii_bar(score: float, width: int = 10) -> str:
    """단일 막대(10칸 기본) — 점수 0~10을 채움 + partial + 빈칸으로."""
    if score < 0 or score > 10:
        raise ReadinessError(f"render_ascii_bar 범위 위반: {score}")
    full_count = int(score)  # 정수 칸
    partial = score - full_count
    bar = FULL_BLOCK * full_count
    # partial 블록 (정수칸 == 10이면 partial은 0이므로 생략)
    if full_count < width:
        pblock = partial_block_for(partial)
        # 빈칸 블록 ░은 partial=0 자리에도 들어가야 함
        if pblock == EMPTY_BLOCK:
            bar += EMPTY_BLOCK
        else:
            bar += pblock
        # 나머지 빈칸
        bar += EMPTY_BLOCK * (width - full_count - 1)
    return bar


def render_ascii_chart(skill_scores: list[SkillScore]) -> str:
    """SKILL.md 옵션 B 형식의 ASCII 차트 전체."""
    if len(skill_scores) != NUM_SKILLS:
        raise ReadinessError(f"render_ascii_chart 입력 {len(skill_scores)}개, {NUM_SKILLS} 필요")

    # 라벨 폭 정렬
    label_width = max(len(s.name_en) for s in skill_scores)

    lines = ["Vision Readiness Profile (0-10 Scale)", ""]
    for sk in skill_scores:
        bar = render_ascii_bar(sk.score)
        lines.append(f"{sk.name_en:<{label_width}} | {bar} {sk.score:.1f}")
    lines.extend([
        "",
        "X-Axis: Score (0 = Not Yet, 10 = World Class)",
        "Y-Axis: Four Core Vision Skills",
        "Legend: █ = filled (1.0) / ░ = empty (0.0) / ▎ etc. = partial 1/8 increments",
    ])
    return "\n".join(lines)


# ===== 9. Mermaid 차트 =====


def render_mermaid_chart(skill_scores: list[SkillScore]) -> str:
    """SKILL.md 옵션 A — Mermaid xychart-beta."""
    if len(skill_scores) != NUM_SKILLS:
        raise ReadinessError(f"render_mermaid_chart 입력 {len(skill_scores)}개")
    x_axis = ", ".join(f'"{s.name_en}"' for s in skill_scores)
    bar_data = ", ".join(f"{s.score:.1f}" for s in skill_scores)
    return (
        "```mermaid\n"
        "xychart-beta\n"
        '  title "Vision Readiness Profile"\n'
        f"  x-axis [{x_axis}]\n"
        '  y-axis "Score (0 = Not Yet, 10 = World Class)" 0 --> 10\n'
        f"  bar [{bar_data}]\n"
        "```"
    )


# ===== 10. 한 줄 요약 (재진단 비교용) =====


def one_line_summary(
    skill_scores: list[SkillScore],
    composite: float,
    when: Optional[date] = None,
) -> str:
    """SKILL.md 결과 저장 절의 한 줄 요약 형식."""
    when = when or date.today()
    bp, rg, cs, ft = skill_scores
    return (
        f"{when.isoformat()} | "
        f"BP {bp.score:.1f} / "
        f"RG {rg.score:.1f} / "
        f"CS {cs.score:.1f} / "
        f"FT {ft.score:.1f} / "
        f"Composite {composite:.2f}"
    )


# ===== 11. 변화 추적 =====


def compute_delta(
    current: list[SkillScore],
    previous: dict[str, float],
) -> dict[str, dict]:
    """
    재진단 모드 — 이전 점수(BP/RG/CS/FT 키 dict)와 비교해 능력별 델타.
    delta > 0 = 향상, < 0 = 하락.
    """
    key_map = {
        "Big Picture": "BP",
        "Reframing Goals": "RG",
        "Creating Strategies": "CS",
        "Following Through": "FT",
    }
    result = {}
    for sk in current:
        prev_key = key_map[sk.name_en]
        if prev_key in previous:
            prev_val = float(previous[prev_key])
            delta = _round1(sk.score - prev_val)
            result[sk.name_en] = {
                "previous": prev_val,
                "current": sk.score,
                "delta": delta,
                "direction": "↑" if delta > 0 else ("↓" if delta < 0 else "→"),
            }
    return result


# ===== 12. 요약 출력 (사용자가 짧게 요청 시) =====


def render_minimal_summary(skill_scores: list[SkillScore], composite: float) -> str:
    """SKILL.md '요약 출력' 체크리스트 최소 요소."""
    strongest = max(skill_scores, key=lambda s: s.score)
    weakest = min(skill_scores, key=lambda s: s.score)

    lines = [
        "**4능력 점수**: " + " / ".join(
            f"{sk.name_en[:2]} {sk.score:.1f}" for sk in skill_scores
        ),
        f"**가장 강한 능력**: {strongest.name_en} ({strongest.score:.1f})",
        f"**가장 약한 능력**: {weakest.name_en} ({weakest.score:.1f})",
        f"**1순위 처방 스킬**: {PRESCRIPTION_MAP[weakest.name_en][0]}",
        f"**Composite**: {composite:.2f}",
    ]
    return "\n".join(lines)


# ===== 4값 직접 입력 (집단 평균 시각화) =====


def skill_scores_from_means(
    bp: float, rg: float, cs: float, ft: float
) -> list[SkillScore]:
    """
    SKILL.md '집단 평균 처리 안내' 케이스 전용.

    원본 20문항이 없는 채로 4능력 평균만 주어진 경우(예: 청중 N명 평균,
    또는 다른 도구에서 산출된 4값), SkillScore 객체 4개를 만든다.
    raw_items·raw_sum은 가용하지 않으므로 빈 리스트와 0을 채운다 —
    이 케이스에서는 결과 해석에서 raw 항목별 분석을 *수행하지 않는다*.
    """
    inputs = [("Big Picture", bp), ("Reframing Goals", rg),
              ("Creating Strategies", cs), ("Following Through", ft)]
    out = []
    for i, (_name, val) in enumerate(inputs):
        if not isinstance(val, (int, float)):
            raise ReadinessError(f"능력 점수가 숫자가 아님: {_name}={val}")
        if val < 0 or val > 10:
            raise ReadinessError(f"능력 점수 범위 위반: {_name}={val} (0~10 필요)")
        out.append(SkillScore(
            name_en=SKILL_NAMES_EN[i],
            name_ko=SKILL_NAMES_KO[i],
            score=_round1(float(val)),
            raw_sum=0,
            raw_items=[],
            skill_index=i,
        ))
    return out


def process_means(
    bp: float, rg: float, cs: float, ft: float,
    audience_note: str = "본 출력은 집단 평균 시각화입니다. 개인 진단 결과가 아닙니다."
) -> dict:
    """
    4값 입력 → 그래프·해석 산출. 시나리오 7 등에서 사용.
    raw_items가 없으므로 prescriptions/level_summary 등 일부는 제한적 의미.
    """
    skills = skill_scores_from_means(bp, rg, cs, ft)
    composite = calculate_composite(skills)
    level_summary = []
    for sk in skills:
        label, desc = level_for(sk.score)
        nh = next_level_hint(sk.score)
        level_summary.append({
            "skill_en": sk.name_en,
            "score": sk.score,
            "level": label,
            "level_desc": desc,
            "next_hint": nh,
        })
    return {
        "input_mode": "means_only",
        "audience_note": audience_note,
        "skill_scores": skills,
        "composite": composite,
        "classify": classify_strengths(skills),
        "prescriptions": prescriptions_for(skills),
        "ascii_chart": render_ascii_chart(skills),
        "mermaid_chart": render_mermaid_chart(skills),
        "one_line": one_line_summary(skills, composite),
        "level_summary": level_summary,
        "minimal_summary": render_minimal_summary(skills, composite),
    }


# ===== 통합 파이프라인 =====


def process(raw_input: str) -> dict:
    """
    원시 입력 → 모든 결정론 산출물의 한 번에 처리.
    반환 dict 키:
      - skill_scores: list[SkillScore]
      - composite: float
      - classify: dict (strengths/growth_areas)
      - prescriptions: list
      - ascii_chart: str
      - mermaid_chart: str
      - one_line: str
      - level_summary: list[dict] (각 능력의 level + next_hint)
    """
    parsed = parse_scores(raw_input)
    validate_all(parsed)
    skills = calculate_skill_scores(parsed)
    composite = calculate_composite(skills)
    level_summary = []
    for sk in skills:
        label, desc = level_for(sk.score)
        nh = next_level_hint(sk.score)
        level_summary.append({
            "skill_en": sk.name_en,
            "score": sk.score,
            "level": label,
            "level_desc": desc,
            "next_hint": nh,
        })
    return {
        "raw_scores": parsed,
        "skill_scores": skills,
        "composite": composite,
        "classify": classify_strengths(skills),
        "prescriptions": prescriptions_for(skills),
        "ascii_chart": render_ascii_chart(skills),
        "mermaid_chart": render_mermaid_chart(skills),
        "one_line": one_line_summary(skills, composite),
        "level_summary": level_summary,
        "minimal_summary": render_minimal_summary(skills, composite),
    }


# ===== CLI =====


def _serialize(obj):
    """SkillScore 직렬화."""
    if isinstance(obj, SkillScore):
        return asdict(obj)
    if isinstance(obj, list):
        return [_serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def main():
    """
    CLI 사용:
      python readiness_engine.py "Q01: 7, Q02: 8, ..."
      또는 stdin에서 읽음 — 결정론 산출 JSON 출력.
    """
    if len(sys.argv) > 1:
        raw = " ".join(sys.argv[1:])
    else:
        raw = sys.stdin.read()
    try:
        out = process(raw)
        print(json.dumps(_serialize(out), ensure_ascii=False, indent=2, default=str))
    except ReadinessError as e:
        print(json.dumps({"error": str(e), "error_type": "ReadinessError"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
