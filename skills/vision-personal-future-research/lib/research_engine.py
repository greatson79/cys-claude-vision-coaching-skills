"""
vision-personal-future-research 결정론 엔진.

SKILL.md가 자연어 LLM 추론으로 처리하던 다음 단계를 결정론 파이썬 함수로 환원:
- 입력 검증 (MBTI/Enneagram/MultipleIntelligence/STRONG 형식)
- 가중치 매핑 (다중지능·RIASEC·가치 → STEEPS)
- MBTI 대응 패턴 lookup
- 에니어그램 대응 패턴 lookup
- CYS 재가중 계수 (×1.5·×1.3)
- 영역별 상한 캡 50% + 잉여 비례 분배
- 합계 100% 정규화
- 시야 비율 (연령대별 lookup)
- 시간축 변환 (Y → Y+5/Y+15/Y+30 절대 연도)
- 시간 임박도 계수
- 종합 점수 압축
- 영역 표준편차 분산 판정
- 진단 누락 영향 안내
- 출처 lookup
- Existential 잠정 가중치 0.5 계수

본 모듈에 등재되지 않은 외부 사실 인용은 산출 금지 (출처 없는 판정 = 자동 FAIL).
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import pstdev
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

STEEPS_DOMAINS = [
    "Society",
    "Technology",
    "Economy",
    "Environment",
    "Politics",
    "Spirituality",
]


def _load(name: str) -> dict[str, Any]:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


MAPPINGS = _load("mappings.json")
AGE_VISIONS = _load("age_visions.json")
SOURCES = _load("sources.json")


# ─────────────────────────────────────────────────────────────────────────
# 입력 검증
# ─────────────────────────────────────────────────────────────────────────

VALID_MBTI = {
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ",
}
ENNEAGRAM_RE = re.compile(r"^([1-9])(?:w([1-9]))?$")
RIASEC_KEYS = {"R", "I", "A", "S", "E", "C"}
MULTIPLE_INT_KEYS = {
    "Logical-Mathematical", "Linguistic", "Spatial",
    "Bodily-Kinesthetic", "Musical",
    "Interpersonal", "Intrapersonal",
    "Naturalist", "Existential",
}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_mbti(mbti: str) -> ValidationResult:
    res = ValidationResult(ok=True)
    if not isinstance(mbti, str):
        return ValidationResult(ok=False, errors=["MBTI must be string"])
    m = mbti.strip().upper()
    if m not in VALID_MBTI:
        if "X" in m or "?" in m or len(m) != 4:
            res.ok = False
            res.errors.append(
                f"MBTI '{mbti}' is incomplete or invalid — must be one of 16 standard 4-letter types"
            )
        else:
            res.ok = False
            res.errors.append(f"MBTI '{mbti}' not in 16 standard types")
    return res


def validate_enneagram(s: str) -> ValidationResult:
    res = ValidationResult(ok=True)
    if not isinstance(s, str):
        return ValidationResult(ok=False, errors=["Enneagram must be string"])
    m = ENNEAGRAM_RE.match(s.strip())
    if not m:
        res.ok = False
        res.errors.append(
            f"Enneagram '{s}' invalid — expected 1-9 optionally with wing (e.g. '5w4')"
        )
        return res
    main, wing = m.group(1), m.group(2)
    if wing is not None:
        diff = abs(int(main) - int(wing)) % 9
        if diff not in (1, 8):
            res.warnings.append(
                f"Enneagram wing {wing} not adjacent to main {main} — conventional wings are adjacent"
            )
    return res


def validate_multiple_intelligence(scores: dict[str, float]) -> ValidationResult:
    res = ValidationResult(ok=True)
    if not isinstance(scores, dict):
        return ValidationResult(ok=False, errors=["MultipleIntelligence must be dict"])
    unknown = set(scores.keys()) - MULTIPLE_INT_KEYS
    if unknown:
        res.warnings.append(
            f"Unknown intelligence keys ignored: {sorted(unknown)}; expected subset of {sorted(MULTIPLE_INT_KEYS)}"
        )
    if not scores:
        res.ok = False
        res.errors.append("MultipleIntelligence empty")
        return res
    for k, v in scores.items():
        if not isinstance(v, (int, float)):
            res.ok = False
            res.errors.append(f"MI score for {k} not numeric: {v}")
    if len(scores) < 9 and len([k for k in scores if k in MULTIPLE_INT_KEYS]) < 9:
        res.warnings.append(
            f"MultipleIntelligence provided {len(scores)} scores (expected 9 incl. Existential)"
        )
    return res


def validate_strong(scores: dict[str, float]) -> ValidationResult:
    res = ValidationResult(ok=True)
    if not isinstance(scores, dict):
        return ValidationResult(ok=False, errors=["STRONG must be dict"])
    unknown = set(scores.keys()) - RIASEC_KEYS
    if unknown:
        res.warnings.append(f"Unknown RIASEC keys ignored: {sorted(unknown)}")
    for k, v in scores.items():
        if k in RIASEC_KEYS and not isinstance(v, (int, float)):
            res.ok = False
            res.errors.append(f"STRONG score for {k} not numeric: {v}")
    return res


def check_minimum_input(diagnoses: dict[str, Any], vision_candidate: bool) -> ValidationResult:
    """SKILL.md 절대 원칙 1: 진단 2개 이상 + 비전 영역 후보 또는 진단 3개 이상."""
    res = ValidationResult(ok=True)
    valid_keys = set(MAPPINGS["diagnosis_keys"])
    present = [k for k in diagnoses.keys() if k in valid_keys and diagnoses[k] is not None]
    n = len(present)
    rule = MAPPINGS["minimum_input_requirement"]
    rule_a = n >= rule["rule_a_min_diagnoses"] and vision_candidate
    rule_b = n >= rule["rule_b_min_diagnoses"]
    if not (rule_a or rule_b):
        res.ok = False
        res.errors.append(
            f"Minimum input not met — got {n} diagnoses, vision_candidate={vision_candidate}. "
            f"Need ≥{rule['rule_a_min_diagnoses']} + vision OR ≥{rule['rule_b_min_diagnoses']} diagnoses"
        )
    return res


# ─────────────────────────────────────────────────────────────────────────
# 가중치 매핑 (LLM 자연어 추론 → 결정론 lookup)
# ─────────────────────────────────────────────────────────────────────────

def _empty_domain_dict() -> dict[str, float]:
    return {d: 0.0 for d in STEEPS_DOMAINS}


def top_n_with_ties(scores: dict[str, float], n: int) -> list[tuple[str, float]]:
    """동순위는 모두 포함 — SKILL.md 동순위 처리 규약."""
    if not scores:
        return []
    sorted_items = sorted(scores.items(), key=lambda kv: -kv[1])
    if n >= len(sorted_items):
        return sorted_items
    cutoff_value = sorted_items[n - 1][1]
    return [(k, v) for k, v in sorted_items if v >= cutoff_value]


def map_multiple_intelligence(
    mi_scores: dict[str, float],
    *,
    existential_full_weight: bool = False,
) -> dict[str, float]:
    """다중지능 상위 → STEEPS 영역 점수."""
    domain = _empty_domain_dict()
    if not mi_scores:
        return domain
    adjusted: dict[str, float] = {}
    coef = MAPPINGS["existential_provisional_coefficient"]
    for k, v in mi_scores.items():
        if k not in MULTIPLE_INT_KEYS:
            continue
        if k == "Existential" and not existential_full_weight:
            adjusted[k] = float(v) * coef
        else:
            adjusted[k] = float(v)
    cap = MAPPINGS["weighting_algorithm"]["max_mapped_domains_per_diagnosis"]
    top = top_n_with_ties(adjusted, cap)
    mapping = MAPPINGS["multiple_intelligence_to_steeps"]
    for k, score in top:
        targets = mapping.get(k, [])
        if not targets:
            continue
        per = score / len(targets)
        for t in targets:
            domain[t] += per
    return domain


def map_riasec(strong_scores: dict[str, float]) -> dict[str, float]:
    domain = _empty_domain_dict()
    if not strong_scores:
        return domain
    filtered = {k: float(v) for k, v in strong_scores.items() if k in RIASEC_KEYS}
    cap = MAPPINGS["weighting_algorithm"]["max_mapped_domains_per_diagnosis"]
    top = top_n_with_ties(filtered, cap)
    mapping = MAPPINGS["riasec_to_steeps"]
    for k, score in top:
        targets = mapping.get(k, [])
        if not targets:
            continue
        per = score / len(targets)
        for t in targets:
            domain[t] += per
    return domain


def map_values(values: list[str]) -> dict[str, float]:
    """가치 단어 → STEEPS. 각 단어 1점, 매핑 도메인에 균등 분배."""
    domain = _empty_domain_dict()
    if not values:
        return domain
    mapping = MAPPINGS["value_keywords_to_steeps"]
    for raw in values:
        if not isinstance(raw, str):
            continue
        w = raw.strip()
        targets = mapping.get(w)
        if not targets:
            for key, tgt in mapping.items():
                if key.startswith("_"):
                    continue
                if key in w or w in key:
                    targets = tgt
                    break
        if not targets:
            continue
        per = 1.0 / len(targets)
        for t in targets:
            domain[t] += per
    return domain


def mbti_response_pattern(mbti: str | None) -> str | None:
    if not mbti:
        return None
    m = mbti.strip().upper()
    if m not in VALID_MBTI:
        return None
    key = m[1] + m[2]
    return MAPPINGS["mbti_response_pattern"].get(key)


def enneagram_response_pattern(s: str | None) -> str | None:
    if not s:
        return None
    m = ENNEAGRAM_RE.match(s.strip())
    if not m:
        return None
    return MAPPINGS["enneagram_response_pattern"].get(m.group(1))


def map_job_domain(domains: list[str]) -> dict[str, float]:
    """직업 도메인 → STEEPS 보조 매핑. primary 1.0, secondary 0.5."""
    domain = _empty_domain_dict()
    if not domains:
        return domain
    table = MAPPINGS["job_domain_to_steeps"]
    for d in domains:
        if not isinstance(d, str):
            continue
        entry = table.get(d.strip())
        if not entry:
            for k, v in table.items():
                if k.startswith("_"):
                    continue
                if k in d or d in k:
                    entry = v
                    break
        if not entry:
            continue
        for p in entry.get("primary", []):
            domain[p] += 1.0
        for s in entry.get("secondary", []):
            domain[s] += 0.5
    return domain


# ─────────────────────────────────────────────────────────────────────────
# CYS 재가중 + 합산 + 상한 캡 + 정규화
# ─────────────────────────────────────────────────────────────────────────

_CYS_STRONG_LABELS = {"강", "강함", "high", "strong", "상", "S"}


def _is_strong(label: str | None) -> bool:
    if label is None:
        return False
    return str(label).strip() in _CYS_STRONG_LABELS


def apply_cys_recoefficient(
    base: dict[str, float],
    cys_codes: dict[str, str] | None,
    target_domain: str | None,
) -> dict[str, float]:
    """CYS 비전 방향성/잠재력/기술력 강함 → 해당 영역 가중치 재가중."""
    out = dict(base)
    if not cys_codes:
        return out
    coefs = MAPPINGS["cys_recoefficient"]
    if not target_domain:
        return out
    if _is_strong(cys_codes.get("vision_direction")):
        out[target_domain] *= coefs["vision_direction_strong"]
    if _is_strong(cys_codes.get("vision_potential")):
        out[target_domain] *= coefs["vision_potential_strong"]
    if _is_strong(cys_codes.get("vision_skill")):
        out[target_domain] *= coefs["vision_skill_strong"]
    return out


def cap_and_normalize(
    raw: dict[str, float],
    *,
    cap_pct: float | None = None,
) -> dict[str, float]:
    """영역별 상한 캡 + 잉여 비례 분배 + 합계 100% 정규화 (SKILL.md 가중치 합산 알고리즘)."""
    algo = MAPPINGS["weighting_algorithm"]
    cap = float(cap_pct if cap_pct is not None else algo["domain_cap_pct"])
    redistribute_top_n = int(algo["redistribute_excess_to_top_n"])
    norm_target = float(algo["normalize_to_pct"])

    total = sum(raw.values())
    if total <= 0:
        # Empty input — uniform fallback
        n = len(STEEPS_DOMAINS)
        return {d: round(norm_target / n, 2) for d in STEEPS_DOMAINS}

    pct = {d: (raw[d] / total) * norm_target for d in STEEPS_DOMAINS}

    # 영역별 상한 캡 적용 + 잉여 비례 분배 (반복 수렴)
    for _ in range(10):
        excess = 0.0
        for d in STEEPS_DOMAINS:
            if pct[d] > cap:
                excess += pct[d] - cap
                pct[d] = cap
        if excess <= 1e-6:
            break
        # 캡 미만 영역 중 상위 N개에 비례 분배
        under = [(d, pct[d]) for d in STEEPS_DOMAINS if pct[d] < cap]
        under.sort(key=lambda kv: -kv[1])
        recipients = under[:redistribute_top_n] if under else []
        if not recipients:
            # 모두 cap 도달 — 균등 분배
            for d in STEEPS_DOMAINS:
                pct[d] += excess / len(STEEPS_DOMAINS)
            break
        sub_total = sum(v for _, v in recipients)
        if sub_total <= 0:
            # 비례 분배 불가 → 균등 분배
            equal_share = excess / len(recipients)
            for d, _ in recipients:
                pct[d] = min(cap, pct[d] + equal_share)
        else:
            for d, v in recipients:
                share = (v / sub_total) * excess
                pct[d] = min(cap, pct[d] + share)

    # 정규화 보정 (캡으로 인한 미세 합계 차이)
    actual = sum(pct.values())
    if actual > 0 and abs(actual - norm_target) > 0.01:
        scale = norm_target / actual
        pct = {d: pct[d] * scale for d in STEEPS_DOMAINS}

    return {d: round(pct[d], 2) for d in STEEPS_DOMAINS}


def detect_vision_split(weights_pct: dict[str, float]) -> dict[str, Any]:
    """영역 표준편차 < 10% 또는 상위 1·2 차이 < 5%p → 비전 다중 후보."""
    th = MAPPINGS["vision_split_thresholds"]
    values = list(weights_pct.values())
    if not values:
        return {"is_split": False}
    sd = pstdev(values)
    sorted_v = sorted(values, reverse=True)
    diff = sorted_v[0] - sorted_v[1] if len(sorted_v) >= 2 else 100.0
    is_split = sd < th["domain_stdev_pct_threshold"] or diff < th["top_two_diff_pct_threshold"]
    return {
        "is_split": is_split,
        "stdev_pct": round(sd, 2),
        "top_two_diff_pct": round(diff, 2),
        "threshold_stdev": th["domain_stdev_pct_threshold"],
        "threshold_top_two_diff": th["top_two_diff_pct_threshold"],
    }


# ─────────────────────────────────────────────────────────────────────────
# 시야 비율 (연령대) — 결정론 lookup
# ─────────────────────────────────────────────────────────────────────────

def vision_ratio_for_age(age: int) -> dict[str, Any]:
    if not isinstance(age, int) or age < 0 or age > 120:
        raise ValueError(f"age must be int in [0,120], got {age!r}")
    for band in AGE_VISIONS["vision_ratios_by_age_band"]:
        if band["age_min"] <= age <= band["age_max"]:
            return {
                "band": band["band"],
                "short_pct": band["short_pct"],
                "mid_pct": band["mid_pct"],
                "long_pct": band["long_pct"],
                "note": band["note"],
            }
    raise ValueError(f"No band for age {age}")


# ─────────────────────────────────────────────────────────────────────────
# 시간축 변환 (Y → Y+5/Y+15/Y+30)
# ─────────────────────────────────────────────────────────────────────────

def absolute_time_axis(current_year: int) -> dict[str, dict[str, int | str]]:
    if not isinstance(current_year, int) or current_year < 1900 or current_year > 2200:
        raise ValueError(f"current_year out of range: {current_year}")
    bands = AGE_VISIONS["time_horizon_bands"]
    return {
        "short": {
            "start_year": current_year + bands["short"]["years_from_now_min"],
            "end_year": current_year + bands["short"]["years_from_now_max"],
            "label": bands["short"]["label"],
        },
        "mid": {
            "start_year": current_year + bands["mid"]["years_from_now_min"],
            "end_year": current_year + bands["mid"]["years_from_now_max"],
            "label": bands["mid"]["label"],
        },
        "long": {
            "start_year": current_year + bands["long"]["years_from_now_min"],
            "end_year": current_year + bands["long"]["years_from_now_max"],
            "label": bands["long"]["label"],
        },
    }


# ─────────────────────────────────────────────────────────────────────────
# 종합 점수 압축 (영역 가중치 × 시간 임박도 × 개인 임팩트)
# ─────────────────────────────────────────────────────────────────────────

def composite_score(
    domain_weight_pct: float,
    time_horizon: str,
    personal_impact: str,
) -> float:
    timing = MAPPINGS["time_imminence_coefficient"]
    impact = MAPPINGS["personal_impact_coefficient"]
    if time_horizon not in timing:
        raise ValueError(f"time_horizon must be in {list(timing.keys())}, got {time_horizon!r}")
    if personal_impact not in impact:
        raise ValueError(f"personal_impact must be in {list(impact.keys())}, got {personal_impact!r}")
    return float(domain_weight_pct) * float(timing[time_horizon]) * float(impact[personal_impact])


def rank_priority(score: float, *, all_scores: list[float]) -> str:
    """★/★★/★★★ 배정 — 상대 분위 결정론."""
    if not all_scores:
        return "★"
    sorted_s = sorted(all_scores, reverse=True)
    n = len(sorted_s)
    p33 = sorted_s[max(0, n // 3 - 1)] if n >= 3 else sorted_s[0]
    p66 = sorted_s[max(0, 2 * n // 3 - 1)] if n >= 3 else sorted_s[-1]
    if score >= p33:
        return "★★★"
    if score >= p66:
        return "★★"
    return "★"


def card_count_for_mode(mode: str) -> tuple[int, int]:
    table = MAPPINGS["compression_card_count"]
    if mode not in table:
        raise ValueError(f"mode must be one of {list(table.keys())}, got {mode!r}")
    lo, hi = table[mode]
    return int(lo), int(hi)


# ─────────────────────────────────────────────────────────────────────────
# 진단 누락 영향 안내
# ─────────────────────────────────────────────────────────────────────────

def missing_diagnosis_notice(present_keys: list[str]) -> dict[str, Any]:
    valid = set(MAPPINGS["diagnosis_keys"])
    present_set = {k for k in present_keys if k in valid}
    missing = sorted(valid - present_set)
    impact_table = MAPPINGS["missing_diagnosis_impact"]
    impact = {k: impact_table[k] for k in missing}
    return {
        "present": sorted(present_set),
        "missing": missing,
        "missing_count": len(missing),
        "impact": impact,
        "warn_insufficient_differentiation": len(missing) >= 4,
    }


# ─────────────────────────────────────────────────────────────────────────
# 출처 lookup (등재된 항목만 사용 가능)
# ─────────────────────────────────────────────────────────────────────────

def get_source(domain: str, horizon: str, claim_id: str) -> dict[str, Any] | None:
    domain_l = domain.lower()
    if domain_l not in SOURCES:
        return None
    bucket = SOURCES[domain_l].get(horizon)
    if not bucket:
        return None
    for item in bucket:
        if item.get("id") == claim_id:
            return item
    return None


def list_sources(domain: str, horizon: str) -> list[dict[str, Any]]:
    domain_l = domain.lower()
    if domain_l not in SOURCES:
        return []
    return list(SOURCES[domain_l].get(horizon, []))


def list_wildcards() -> list[dict[str, Any]]:
    return list(SOURCES.get("wildcards", []))


def all_source_ids() -> set[str]:
    out: set[str] = set()
    for dom in STEEPS_DOMAINS:
        for h in ("short", "mid", "long"):
            for item in list_sources(dom, h):
                if "id" in item:
                    out.add(item["id"])
    for wc in list_wildcards():
        if "id" in wc:
            out.add(wc["id"])
    return out


def is_registered_claim(claim_id: str) -> bool:
    return claim_id in all_source_ids()


# ─────────────────────────────────────────────────────────────────────────
# 풀 파이프라인 — 진단 입력 → 6영역 가중치 산출
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class FullWeightResult:
    raw_domain_sum: dict[str, float]
    weights_pct: dict[str, float]
    vision_split: dict[str, Any]
    missing_notice: dict[str, Any]
    response_patterns: dict[str, str | None]
    validation: dict[str, Any]


def compute_weights(
    diagnoses: dict[str, Any],
    *,
    vision_candidate: bool = False,
    target_recoef_domain: str | None = None,
    job_domains: list[str] | None = None,
    existential_full_weight: bool = False,
) -> FullWeightResult:
    """진단 7종 → 6영역 가중치 결정론 파이프라인."""

    val_errors: list[str] = []
    val_warnings: list[str] = []

    min_check = check_minimum_input(diagnoses, vision_candidate)
    val_errors.extend(min_check.errors)
    val_warnings.extend(min_check.warnings)

    if "MBTI" in diagnoses and diagnoses["MBTI"]:
        v = validate_mbti(diagnoses["MBTI"])
        val_errors.extend(v.errors)
        val_warnings.extend(v.warnings)

    if "Enneagram" in diagnoses and diagnoses["Enneagram"]:
        v = validate_enneagram(diagnoses["Enneagram"])
        val_errors.extend(v.errors)
        val_warnings.extend(v.warnings)

    mi = diagnoses.get("MultipleIntelligence") or {}
    if mi:
        v = validate_multiple_intelligence(mi)
        val_errors.extend(v.errors)
        val_warnings.extend(v.warnings)

    strong = diagnoses.get("STRONG") or {}
    if strong:
        v = validate_strong(strong)
        val_errors.extend(v.errors)
        val_warnings.extend(v.warnings)

    raw = _empty_domain_dict()
    for k, v in map_multiple_intelligence(mi, existential_full_weight=existential_full_weight).items():
        raw[k] += v
    for k, v in map_riasec(strong).items():
        raw[k] += v
    values = diagnoses.get("Values") or []
    for k, v in map_values(values).items():
        raw[k] += v
    if job_domains:
        for k, v in map_job_domain(job_domains).items():
            raw[k] += v

    cys = diagnoses.get("CYS") or None
    raw_with_cys = apply_cys_recoefficient(raw, cys, target_recoef_domain)
    weights = cap_and_normalize(raw_with_cys)
    split = detect_vision_split(weights)
    missing = missing_diagnosis_notice(list(diagnoses.keys()))

    patterns = {
        "MBTI": mbti_response_pattern(diagnoses.get("MBTI")),
        "Enneagram": enneagram_response_pattern(diagnoses.get("Enneagram")),
    }

    return FullWeightResult(
        raw_domain_sum={k: round(v, 4) for k, v in raw_with_cys.items()},
        weights_pct=weights,
        vision_split=split,
        missing_notice=missing,
        response_patterns=patterns,
        validation={"errors": val_errors, "warnings": val_warnings, "ok": not val_errors},
    )


# ─────────────────────────────────────────────────────────────────────────
# 결정론 산출 빌더 — 매트릭스 + 카드 후보
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class ChangeCard:
    domain: str
    horizon: str
    claim_id: str
    title: str
    source: str
    certainty: str
    composite_score: float
    priority: str


def build_change_cards(
    weights_pct: dict[str, float],
    *,
    personal_impact_by_id: dict[str, str] | None = None,
    include_wildcards: bool = False,
) -> list[ChangeCard]:
    """등재된 출처 lookup만으로 변화 카드 후보 생성. 점수·우선순위 결정론."""
    raw_cards: list[ChangeCard] = []
    impacts = personal_impact_by_id or {}
    candidate_pairs: list[tuple[str, str, dict[str, Any]]] = []
    for dom in STEEPS_DOMAINS:
        for horizon in ("short", "mid", "long"):
            for item in list_sources(dom, horizon):
                if "id" not in item:
                    continue
                candidate_pairs.append((dom, horizon, item))
    if include_wildcards:
        for wc in list_wildcards():
            candidate_pairs.append(("Spirituality", "long", wc))

    scores_pool: list[float] = []
    scored: list[tuple[str, str, dict[str, Any], float]] = []
    for dom, horizon, item in candidate_pairs:
        dw = weights_pct.get(dom, 0.0)
        pi = impacts.get(item["id"], "mid")
        s = composite_score(dw, horizon, pi)
        scores_pool.append(s)
        scored.append((dom, horizon, item, s))

    for dom, horizon, item, s in scored:
        prio = rank_priority(s, all_scores=scores_pool)
        raw_cards.append(
            ChangeCard(
                domain=dom,
                horizon=horizon,
                claim_id=item["id"],
                title=item.get("claim", item.get("label", item["id"])),
                source=item.get("source", "출처 미등재"),
                certainty=item.get("certainty", "unknown"),
                composite_score=round(s, 4),
                priority=prio,
            )
        )

    raw_cards.sort(key=lambda c: -c.composite_score)
    return raw_cards


def select_top_cards(
    cards: list[ChangeCard],
    *,
    mode: str = "standard",
) -> list[ChangeCard]:
    lo, hi = card_count_for_mode(mode)
    return cards[:hi]


def ensure_six_domain_min_one(cards: list[ChangeCard]) -> list[ChangeCard]:
    """SKILL.md 절대 원칙 2: 6영역 모두 최소 1개 카드 보장 (경계 변화)."""
    have = {c.domain for c in cards}
    if have >= set(STEEPS_DOMAINS):
        return cards
    out = list(cards)
    for dom in STEEPS_DOMAINS:
        if dom in have:
            continue
        for h in ("short", "mid", "long"):
            items = list_sources(dom, h)
            if items:
                item = items[0]
                out.append(
                    ChangeCard(
                        domain=dom,
                        horizon=h,
                        claim_id=item["id"],
                        title=item.get("claim", item["id"]),
                        source=item.get("source", "출처 미등재"),
                        certainty=item.get("certainty", "unknown"),
                        composite_score=0.0,
                        priority="★",
                    )
                )
                break
    return out


# ─────────────────────────────────────────────────────────────────────────
# 자기 검증 (등재 출처 무결성 + 매핑 일관성)
# ─────────────────────────────────────────────────────────────────────────

def self_check() -> dict[str, Any]:
    issues: list[str] = []
    for dom, body in SOURCES.items():
        if dom in ("_meta", "wildcards"):
            continue
        if dom.capitalize() not in STEEPS_DOMAINS:
            issues.append(f"Unknown domain in sources.json: {dom}")
        for h in ("short", "mid", "long"):
            for item in body.get(h, []):
                for required in ("id", "claim", "source", "certainty"):
                    if required not in item:
                        issues.append(f"{dom}/{h}/{item.get('id', '?')} missing '{required}'")
    mi_map = MAPPINGS["multiple_intelligence_to_steeps"]
    for intel, targets in mi_map.items():
        if intel.startswith("_"):
            continue
        if intel not in MULTIPLE_INT_KEYS:
            issues.append(f"mappings.json MI {intel} not in MULTIPLE_INT_KEYS")
        for t in targets:
            if t not in STEEPS_DOMAINS:
                issues.append(f"MI {intel} maps to unknown domain {t}")
    for k in MAPPINGS["riasec_to_steeps"]:
        if k.startswith("_"):
            continue
        if k not in RIASEC_KEYS:
            issues.append(f"RIASEC key {k} unknown")
    return {"ok": not issues, "issues": issues, "source_count": len(all_source_ids())}


if __name__ == "__main__":
    import sys
    out = self_check()
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit(0 if out["ok"] else 1)
