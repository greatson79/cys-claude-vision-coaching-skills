"""
STRONG / RIASEC 결정론 엔진

vision-strong-visioncoding 스킬의 모든 산술·매핑·검증 단계를 결정론으로 환원.
LLM이 자연어로 다시 추론하지 못하게 한다.

작업 단위:
  - validate_responses : 18문항 응답 검증
  - compute_scores     : 6영역 점수 산출
  - compute_percentages: 백분율 변환
  - compute_tricode    : 동점·정렬 규약 적용 트라이코드 산출
  - consistency_label  : Hexagon 인접성 평가
  - differentiation_label: max-min 차별성 평가
  - lookup_careers     : 36 트라이코드 DB + dyad fallback
  - bar_chart_ascii    : ASCII 막대 그래프
  - render_full_report : 전체 결과 문자열
  - detect_language    : 입력 문자열에서 ko/en/zh/ja 휴리스틱 감지

전 함수 LLM 의존도 0. 통일 검증된 단위 테스트는 tests/test_strong_engine.py.

학술 근거:
  - Holland, J. L. (1959, 1997). RIASEC 6유형·Hexagon 모델
  - Donnay et al. (2005). Strong Interest Inventory Manual (CPP)
  - Tracey & Rounds (1993). Holland Hexagon empirical structure
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────────────
# 상수: RIASEC 표준 순서·Hexagon 구조·문항 인덱스
# ──────────────────────────────────────────────────────────────────────

DOMAINS: tuple[str, ...] = ("R", "I", "A", "S", "E", "C")
"""Holland Code 표준 순서 (R-I-A-S-E-C). 영문 알파벳 순서가 아님."""

DOMAIN_INDEX: dict[str, int] = {d: i for i, d in enumerate(DOMAINS)}
"""정렬 비교용 표준 순서 인덱스 (R=0, I=1, A=2, S=3, E=4, C=5)."""

# Holland Hexagon 인접성 — 한 변(adjacent), 한 칸 건너(alternate), 정반대(opposite)
HEXAGON_ADJACENT: frozenset[frozenset[str]] = frozenset(
    {frozenset({a, b}) for a, b in [("R", "I"), ("I", "A"), ("A", "S"), ("S", "E"), ("E", "C"), ("C", "R")]}
)
HEXAGON_ALTERNATE: frozenset[frozenset[str]] = frozenset(
    {frozenset({a, b}) for a, b in [("R", "A"), ("I", "S"), ("A", "E"), ("S", "C"), ("E", "R"), ("C", "I")]}
)
HEXAGON_OPPOSITE: frozenset[frozenset[str]] = frozenset(
    {frozenset({a, b}) for a, b in [("R", "S"), ("I", "E"), ("A", "C")]}
)

# 문항 → 영역 매핑 (SKILL.md 라운드 1~6 정의 그대로)
QUESTION_DOMAIN: dict[int, str] = {
    1: "R", 2: "I", 3: "A",
    4: "S", 5: "E", 6: "C",
    7: "R", 8: "I", 9: "A",
    10: "S", 11: "E", 12: "C",
    13: "R", 14: "I", 15: "A",
    16: "S", 17: "E", 18: "C",
}

ROUND_QUESTIONS: dict[int, list[int]] = {
    1: [1, 2, 3], 2: [4, 5, 6],
    3: [7, 8, 9], 4: [10, 11, 12],
    5: [13, 14, 15], 6: [16, 17, 18],
}

SCALE_MIN, SCALE_MAX = 1, 5
DOMAIN_MIN_SCORE, DOMAIN_MAX_SCORE = 3, 15

# ──────────────────────────────────────────────────────────────────────
# 데이터 로드 (트라이코드 DB · 다국어 라벨)
# ──────────────────────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _load_json(name: str) -> dict[str, Any]:
    path = _DATA_DIR / name
    with path.open(encoding="utf-8") as f:
        return json.load(f)


_TRICODE_DB = _load_json("tricode_db.json")
_I18N = _load_json("i18n.json")

TRICODES: dict[str, list[str]] = _TRICODE_DB["tricodes"]
DYAD_SEEDS: dict[str, list[str]] = _TRICODE_DB["dyad_seeds"]


# ──────────────────────────────────────────────────────────────────────
# 응답 검증
# ──────────────────────────────────────────────────────────────────────


class ValidationError(ValueError):
    """입력 검증 실패."""


def validate_responses(responses: dict[int, int]) -> dict[int, int]:
    """18문항 응답을 검증한다.

    - 키는 1~18 정수, 모두 존재해야 함
    - 값은 1~5 정수
    위반 시 ValidationError(상세 메시지) 발생.

    반환: 검증 통과한 dict (입력 그대로, immutable copy)
    """
    if not isinstance(responses, dict):
        raise ValidationError(f"responses는 dict이어야 합니다. 현재 타입: {type(responses).__name__}")

    expected_keys = set(range(1, 19))
    actual_keys = set(responses.keys())

    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)

    errors: list[str] = []
    if missing:
        errors.append(f"누락 문항: {missing}")
    if extra:
        errors.append(f"범위 밖 문항 키: {extra} (1~18만 허용)")

    invalid_values: list[tuple[int, Any]] = []
    for q in sorted(actual_keys & expected_keys):
        v = responses[q]
        if isinstance(v, bool) or not isinstance(v, int) or v < SCALE_MIN or v > SCALE_MAX:
            invalid_values.append((q, v))
    if invalid_values:
        errors.append(
            "범위·타입 오류: "
            + ", ".join(f"Q{q:02d}={v!r}" for q, v in invalid_values)
            + f" (1~5 정수만 허용)"
        )

    if errors:
        raise ValidationError(" / ".join(errors))

    return {k: int(responses[k]) for k in sorted(expected_keys)}


# ──────────────────────────────────────────────────────────────────────
# 점수·백분율
# ──────────────────────────────────────────────────────────────────────


def compute_scores(responses: dict[int, int]) -> dict[str, int]:
    """6영역 점수 산출 (3~15)."""
    responses = validate_responses(responses)
    scores: dict[str, int] = {d: 0 for d in DOMAINS}
    for q, score in responses.items():
        scores[QUESTION_DOMAIN[q]] += score
    # 무결성 — 합산 결과 모두 3~15 범위
    for d, s in scores.items():
        if not (DOMAIN_MIN_SCORE <= s <= DOMAIN_MAX_SCORE):
            raise ValidationError(f"영역 {d} 점수 {s}가 범위 [{DOMAIN_MIN_SCORE}, {DOMAIN_MAX_SCORE}] 밖")
    return scores


def compute_percentages(scores: dict[str, int]) -> dict[str, float]:
    """(점수 - 3) / 12 × 100 → 0.0~100.0."""
    return {d: round((scores[d] - DOMAIN_MIN_SCORE) / (DOMAIN_MAX_SCORE - DOMAIN_MIN_SCORE) * 100, 1) for d in DOMAINS}


# ──────────────────────────────────────────────────────────────────────
# 트라이코드 산출 — 동점·Hexagon 인접·표준 순서
# ──────────────────────────────────────────────────────────────────────


def _tie_break_key(domain: str, fixed: list[str]) -> tuple[int, int]:
    """동점 시 정렬 키.

    1) 이미 결정된 상위 영역과 Hexagon 인접한 영역을 앞에 둠 (0=인접·이미결정과 1차로 가까움, 1=건너편, 2=대각, 3=고정된 영역 없음)
    2) 그래도 동률이면 RIASEC 표준 순서 (R→I→A→S→E→C)

    fixed: 이미 트라이코드에 들어간 영역 (예: 1위 결정 후 2위 동점 비교 시 [1위])
    """
    if not fixed:
        return (3, DOMAIN_INDEX[domain])
    # 가장 가까운(=점수 낮은) hexagon 거리만 본다
    best_distance = 2
    for f in fixed:
        pair = frozenset({domain, f})
        if pair in HEXAGON_ADJACENT:
            best_distance = min(best_distance, 0)
        elif pair in HEXAGON_ALTERNATE:
            best_distance = min(best_distance, 1)
        else:  # OPPOSITE
            best_distance = min(best_distance, 2)
    return (best_distance, DOMAIN_INDEX[domain])


def compute_tricode(scores: dict[str, int]) -> str:
    """상위 3영역 결정.

    절차 (각 단계 결정론):
    1) 1위: 점수 최댓값 → 동률 시 RIASEC 표준 순서
    2) 2위: 남은 5영역 중 최댓값 → 동률 시 1위와의 Hexagon 거리(가까운 우선) → RIASEC 표준 순서
    3) 3위: 남은 4영역 중 최댓값 → 동률 시 (1위·2위 중 가까운 거리) → RIASEC 표준 순서
    """
    if set(scores.keys()) != set(DOMAINS):
        raise ValidationError(f"scores 키가 RIASEC 6영역과 일치하지 않음: {sorted(scores.keys())}")

    remaining = list(DOMAINS)
    picked: list[str] = []
    for _ in range(3):
        max_score = max(scores[d] for d in remaining)
        candidates = [d for d in remaining if scores[d] == max_score]
        # tie-break: hexagon 인접(이미 picked와의 거리) → 표준 순서
        chosen = min(candidates, key=lambda d: _tie_break_key(d, picked))
        picked.append(chosen)
        remaining.remove(chosen)
    return "".join(picked)


def is_flat_profile(scores: dict[str, int], threshold: int = 3) -> bool:
    """차별성이 threshold 이하면 플랫 프로파일."""
    vals = [scores[d] for d in DOMAINS]
    return (max(vals) - min(vals)) <= threshold


# ──────────────────────────────────────────────────────────────────────
# Hexagon 일관성·차별성
# ──────────────────────────────────────────────────────────────────────


def _pair_class(a: str, b: str) -> str:
    """ADJACENT / ALTERNATE / OPPOSITE."""
    pair = frozenset({a, b})
    if pair in HEXAGON_ADJACENT:
        return "ADJACENT"
    if pair in HEXAGON_ALTERNATE:
        return "ALTERNATE"
    if pair in HEXAGON_OPPOSITE:
        return "OPPOSITE"
    raise ValidationError(f"동일 영역 비교 또는 미정의 쌍: {a}-{b}")


def consistency_label(tricode: str) -> dict[str, Any]:
    """트라이코드 3영역 쌍의 Hexagon 관계.

    학계 표준 (Holland 1997):
      - 1·2위 쌍이 ADJACENT → 일관성 높음
      - 1·2위 쌍이 ALTERNATE → 일관성 중간
      - 1·2위 쌍이 OPPOSITE → 일관성 낮음
    (3영역 모두 인접해야 'high'라는 비공식 변형도 있으나, Holland 원본은 *1·2위* 쌍을 본다)

    반환:
      {
        "primary_pair": "I-R", "primary_class": "ADJACENT",
        "secondary_pair_12_3": ["I-S", "R-S"], "secondary_classes": ["OPPOSITE", "OPPOSITE"],
        "level": "high" | "mid" | "low",
        "label_key": "high_consist" | "mid_consist" | "low_consist"
      }
    """
    if len(tricode) != 3 or any(c not in DOMAINS for c in tricode):
        raise ValidationError(f"트라이코드 형식 오류: {tricode!r}")
    a, b, c = tricode[0], tricode[1], tricode[2]
    primary_class = _pair_class(a, b)
    secondary_classes = [_pair_class(a, c), _pair_class(b, c)]
    if primary_class == "ADJACENT":
        level, key = "high", "high_consist"
    elif primary_class == "ALTERNATE":
        level, key = "mid", "mid_consist"
    else:
        level, key = "low", "low_consist"
    return {
        "primary_pair": f"{a}-{b}",
        "primary_class": primary_class,
        "secondary_pairs": [f"{a}-{c}", f"{b}-{c}"],
        "secondary_classes": secondary_classes,
        "level": level,
        "label_key": key,
    }


def differentiation_label(scores: dict[str, int]) -> dict[str, Any]:
    """max - min 기반 분화도.

    - ≥8: 고도 분화
    - 4~7: 중간 분화
    - ≤3: 저분화 (플랫)
    """
    vals = [scores[d] for d in DOMAINS]
    diff = max(vals) - min(vals)
    if diff >= 8:
        level, key = "high", "high_diff"
    elif diff >= 4:
        level, key = "mid", "mid_diff"
    else:
        level, key = "low", "low_diff"
    return {"diff": diff, "max": max(vals), "min": min(vals), "level": level, "label_key": key}


# ──────────────────────────────────────────────────────────────────────
# 직업군 매칭 (36 DB + dyad fallback + 정의 결합)
# ──────────────────────────────────────────────────────────────────────


def lookup_careers(tricode: str) -> dict[str, Any]:
    """트라이코드 → 직업군 매핑.

    절차:
    1) 36 DB 직접 매칭
    2) 1·2위 다이코드(dyad) 시드 매칭
    3) 둘 다 없으면 빈 리스트 + fallback_used 표기
    """
    if len(tricode) != 3 or any(c not in DOMAINS for c in tricode):
        raise ValidationError(f"트라이코드 형식 오류: {tricode!r}")

    if tricode in TRICODES:
        return {
            "tricode": tricode,
            "careers": list(TRICODES[tricode]),
            "source": "tricode_db",
            "fallback_used": False,
        }
    dyad = tricode[:2]
    if dyad in DYAD_SEEDS:
        return {
            "tricode": tricode,
            "careers": list(DYAD_SEEDS[dyad]),
            "source": f"dyad_seed:{dyad}",
            "fallback_used": True,
            "note": f"비표준 트라이코드 — 1·2위 다이코드({dyad}) 시드 적용",
        }
    return {
        "tricode": tricode,
        "careers": [],
        "source": "none",
        "fallback_used": True,
        "note": "사전 정의된 매칭 없음 — 1·2번째 영역 정의 결합으로 안내 필요",
    }


# ──────────────────────────────────────────────────────────────────────
# 막대 그래프 (ASCII)
# ──────────────────────────────────────────────────────────────────────


def bar_chart_ascii(scores: dict[str, int], lang: str = "ko") -> str:
    labels = _I18N["languages"].get(lang, _I18N["languages"]["en"])["domain_full"]
    label_score = _I18N["languages"].get(lang, _I18N["languages"]["en"])["labels"]["score"]
    max_label_len = max(len(labels[d]) for d in DOMAINS)
    bar_width = 15  # 3~15 → 0~12 폭을 그대로 사용 (점수-3)
    highest = max(scores[d] for d in DOMAINS)
    lines = [f"RIASEC Interest Profile (3 ~ 15 {label_score})", ""]
    for d in DOMAINS:
        s = scores[d]
        filled = s - DOMAIN_MIN_SCORE  # 0~12
        bar = "█" * filled + "░" * (bar_width - 3 - filled)
        star = " ★" if s == highest else ""
        lines.append(f"{labels[d]:<{max_label_len}} | {bar} {s:>2}{star}")
    lines.append("")
    lines.append("★ = Highest Domain")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────
# 언어 감지 (한·영·중·일 휴리스틱)
# ──────────────────────────────────────────────────────────────────────


def detect_language(text: str) -> str:
    """입력 문자열에서 ko/zh/ja/en 중 추정.

    휴리스틱 (결정론):
      - 한글 음절(0xAC00~0xD7A3) 존재 → 'ko'
      - 일본 히라가나(0x3040~0x309F) 또는 가타카나(0x30A0~0x30FF) 존재 → 'ja'
      - CJK 통합 한자(0x4E00~0x9FFF) 존재 + 한글·일본 가나 없음 → 'zh'
      - 그 외 → 'en'
    """
    has_hangul = any("가" <= ch <= "힣" for ch in text)
    has_kana = any(("぀" <= ch <= "ゟ") or ("゠" <= ch <= "ヿ") for ch in text)
    has_cjk = any("一" <= ch <= "鿿" for ch in text)
    if has_hangul:
        return "ko"
    if has_kana:
        return "ja"
    if has_cjk:
        return "zh"
    return "en"


# ──────────────────────────────────────────────────────────────────────
# 응답 파서 — "Q01: 4, Q02: 5" / 줄바꿈 / "1,2,3..." 등
# ──────────────────────────────────────────────────────────────────────

_RESPONSE_PATTERN = re.compile(r"[Qq]?\s*0*(\d{1,2})\s*[:=]\s*([1-5])")


def parse_responses(text: str) -> dict[int, int]:
    """자연어 응답 문자열 → {문항번호: 점수}.

    지원 형식:
      - "Q01: 4, Q02: 5, Q03: 3"
      - "1:4 2:5 3:3"
      - 줄바꿈으로 한 줄씩
      - 콤마·공백·세미콜론 구분
    번호 명시 없는 단순 리스트("4 5 3 ...")는 *지원하지 않음* — 매핑 안전성을 위해 명시 강제.
    """
    if not isinstance(text, str):
        raise ValidationError(f"text는 str이어야 합니다. 현재 타입: {type(text).__name__}")
    matches = _RESPONSE_PATTERN.findall(text)
    if not matches:
        raise ValidationError(
            "응답을 파싱하지 못했습니다. 형식 예: 'Q01: 4, Q02: 5, Q03: 3' 또는 '1: 4\\n2: 5\\n3: 3'"
        )
    result: dict[int, int] = {}
    for qstr, vstr in matches:
        q = int(qstr)
        v = int(vstr)
        if q in result and result[q] != v:
            raise ValidationError(f"Q{q:02d} 중복 응답 (값이 다름: {result[q]} vs {v})")
        result[q] = v
    return result


# ──────────────────────────────────────────────────────────────────────
# 전체 결과 렌더 — 한 함수 호출로 결정론 산출
# ──────────────────────────────────────────────────────────────────────


def analyze(responses: dict[int, int], lang: str = "ko") -> dict[str, Any]:
    """전체 결정론 분석 한 번에.

    반환 구조:
      {
        "lang": "ko",
        "scores": {R:..,I:..,A:..,S:..,E:..,C:..},
        "percentages": {...},
        "tricode": "IRS",
        "consistency": {...},
        "differentiation": {...},
        "flat": False,
        "careers": {tricode/careers/source/...},
        "bar_chart": "...",
        "warnings": [...]
      }
    """
    if lang not in _I18N["languages"]:
        lang = "en"
    validated = validate_responses(responses)
    scores = compute_scores(validated)
    percents = compute_percentages(scores)
    tricode = compute_tricode(scores)
    cons = consistency_label(tricode)
    diff = differentiation_label(scores)
    flat = is_flat_profile(scores)
    careers = lookup_careers(tricode)
    chart = bar_chart_ascii(scores, lang=lang)

    warnings: list[str] = []
    if flat:
        warnings.append(
            "흥미 프로파일이 평탄합니다 — 모든 영역에 *고른 관심* 또는 *흥미 미분화*가 양가 해석됩니다."
            if lang == "ko"
            else "Flat profile detected — could indicate balanced interests or undifferentiated exploration."
        )
    if careers["fallback_used"]:
        warnings.append(
            "비표준 트라이코드 — 사전 정의된 직업 매핑이 없어 fallback이 적용되었습니다."
            if lang == "ko"
            else "Non-standard tricode — career mapping uses fallback (dyad seed or domain combination)."
        )

    return {
        "lang": lang,
        "responses": validated,
        "scores": scores,
        "percentages": percents,
        "tricode": tricode,
        "consistency": cons,
        "differentiation": diff,
        "flat_profile": flat,
        "careers": careers,
        "bar_chart": chart,
        "warnings": warnings,
    }


# ──────────────────────────────────────────────────────────────────────
# CLI (선택) — 단일 호출 테스트용
# ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import sys

    p = argparse.ArgumentParser(description="STRONG / RIASEC 결정론 엔진")
    p.add_argument("--responses", type=str, help="응답 문자열 예: 'Q01:4,Q02:5,...'")
    p.add_argument("--scores", type=str, help="점수 직접 입력 예: 'R=12,I=14,A=8,S=10,E=7,C=6'")
    p.add_argument("--tricode", type=str, help="트라이코드 직접 입력 예: 'IRS'")
    p.add_argument("--lang", type=str, default="ko")
    args = p.parse_args()

    try:
        if args.responses:
            data = parse_responses(args.responses)
            out = analyze(data, lang=args.lang)
        elif args.scores:
            parsed: dict[str, int] = {}
            for part in re.split(r"[,\s]+", args.scores):
                if not part:
                    continue
                k, v = part.split("=")
                parsed[k.strip().upper()] = int(v)
            tricode = compute_tricode(parsed)
            out = {
                "scores": parsed,
                "tricode": tricode,
                "consistency": consistency_label(tricode),
                "differentiation": differentiation_label(parsed),
                "careers": lookup_careers(tricode),
                "bar_chart": bar_chart_ascii(parsed, lang=args.lang),
            }
        elif args.tricode:
            out = {
                "tricode": args.tricode.upper(),
                "consistency": consistency_label(args.tricode.upper()),
                "careers": lookup_careers(args.tricode.upper()),
            }
        else:
            p.print_help()
            sys.exit(1)
        print(json.dumps(out, ensure_ascii=False, indent=2))
    except ValidationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
