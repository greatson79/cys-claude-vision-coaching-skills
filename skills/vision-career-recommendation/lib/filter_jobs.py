"""Deterministic age/education filter for candidate jobs.

Hard rules (mirror SKILL.md §나이·학력 우선 필터링 규칙):
- ✓ 적합 (pass): age in [min_age, max_age] AND user_education_rank >= min_education_rank
- △ 약간 미달 (borderline): age within ±5 of bound OR education exactly 1 rank below
- ✗ 미달 (fail): otherwise — excluded from final slot
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .catalog import education_rank, get_age_category, jobs_in_type, normalize_education

AGE_TOLERANCE = 5


def classify_fit(
    job: Dict,
    age: Optional[int],
    education: Optional[str],
) -> Tuple[str, str]:
    """Return (verdict, explanation) where verdict ∈ {pass, borderline, fail}."""

    if age is None and education is None:
        return ("unknown", "나이·학력 미확인 — 실제 적합도는 개인 상황에 따라 다름")

    min_edu = job.get("min_education")
    edu_gap = None
    if education is not None and min_edu is not None:
        user_rank = education_rank(education)
        req_rank = education_rank(min_edu)
        edu_gap = user_rank - req_rank
    age_status = "unknown"
    if age is not None:
        if job["min_age"] <= age <= job["max_age"]:
            age_status = "in_range"
        elif (
            (job["min_age"] - AGE_TOLERANCE) <= age < job["min_age"]
            or job["max_age"] < age <= (job["max_age"] + AGE_TOLERANCE)
        ):
            age_status = "borderline"
        else:
            age_status = "out"

    # strict_education = true: any negative edu_gap is FAIL (no borderline tolerance)
    is_strict = bool(job.get("strict_education"))

    # Pure FAIL: education clearly below
    if edu_gap is not None:
        if is_strict and edu_gap < 0:
            return ("fail", f"학력 미달 — 전문자격 직업({job.get('ko')})은 정확한 학력 필요 ({education} → {min_edu})")
        if edu_gap <= -2:
            return ("fail", f"학력 미달 ({education} → 필요 {min_edu})")
    # Out of age range with no borderline allowance
    if age_status == "out":
        return ("fail", f"나이 범위 초과 (권장 {job['min_age']}~{job['max_age']})")

    # Borderline conditions
    if edu_gap is not None and edu_gap == -1:
        return ("borderline", f"학력 1단계 부족 — 보완 경로 필요 ({education} → {min_edu})")
    if age_status == "borderline":
        return ("borderline", f"나이 권장 범위 ±{AGE_TOLERANCE}년 — 추가 검토 권장")

    # All clear
    return ("pass", "나이·학력 적합")


def filter_jobs_for_user(
    type_key: str,
    age: Optional[int],
    education: Optional[str],
    include_faith_jobs: bool = False,
) -> List[Dict]:
    """Return list of jobs with verdict tagged. Sorts pass > borderline > fail."""
    edu_norm = normalize_education(education) if education else None
    candidates = jobs_in_type(type_key)
    results = []
    for job in candidates:
        if job.get("requires_faith_disclosure") and not include_faith_jobs:
            continue
        verdict, reason = classify_fit(job, age, edu_norm)
        out = dict(job)
        out["_verdict"] = verdict
        out["_verdict_reason"] = reason
        results.append(out)
    order = {"pass": 0, "borderline": 1, "unknown": 2, "fail": 3}
    results.sort(key=lambda j: order[j["_verdict"]])
    return results


def _make_unfilled_slot(index: int, type_key: str, reason: str) -> Dict:
    """Placeholder slot used when no eligible job remains. SKILL.md rule:
    '5개 미만으로 출력하지 않는다' + '현재 직접 적합 직업 부족 — 이유: [구체 사유]'.
    Verdict='unfilled' so the LLM and validator can clearly mark this case.
    """
    return {
        "id": f"__unfilled_{type_key}_{index}__",
        "ko": "현재 직접 적합 직업 부족 (자료 기반)",
        "en": "No directly-fitting career in catalog (data-based)",
        "min_education": None,
        "min_age": None,
        "max_age": None,
        "rationale_keys": [],
        "_verdict": "unfilled",
        "_verdict_reason": reason,
        "_is_placeholder": True,
    }


def select_top5(
    type_key: str,
    age: Optional[int],
    education: Optional[str],
    include_faith_jobs: bool = False,
    preferred_ids: Optional[List[str]] = None,
) -> Dict:
    """Select 5 jobs for this type. Always returns 5 slots.

    HARD RULE (SKILL.md §나이·학력 우선 필터링):
    - verdict='fail' jobs are NEVER inserted into a slot.
    - When eligible count < 5, slots are padded with explicit placeholder objects
      (id='__unfilled_*__') rather than silently leaking fail-verdict jobs.

    Sort priority within eligible:
      1. preferred_ids (if any)
      2. faith-disclosed user → faith retirement jobs first (within retirement type)
      3. pass > borderline > unknown
    """
    filtered = filter_jobs_for_user(type_key, age, education, include_faith_jobs)
    eligible = [j for j in filtered if j["_verdict"] in ("pass", "borderline", "unknown")]

    pref_set = set(preferred_ids) if preferred_ids else set()
    verdict_rank = {"pass": 0, "borderline": 1, "unknown": 2}

    def sort_key(j):
        is_pref = 0 if j["id"] in pref_set else 1
        # When user discloses faith AND we're filling Type 3, surface faith-tagged jobs
        # ahead of generic volunteer roles (so users get the breadth they asked for).
        faith_boost = 0 if (
            type_key == "retirement"
            and include_faith_jobs
            and j.get("requires_faith_disclosure")
        ) else 1
        return (is_pref, faith_boost, verdict_rank[j["_verdict"]])

    eligible.sort(key=sort_key)

    # SKILL.md: faith_disclosed=True surfaces faith jobs but does NOT monopolize.
    # Reserve at least 2 of 5 retirement slots for non-faith secular volunteering
    # so users see breadth, not a faith-only lineup.
    if type_key == "retirement" and include_faith_jobs:
        faith_jobs = [j for j in eligible if j.get("requires_faith_disclosure")]
        secular_jobs = [j for j in eligible if not j.get("requires_faith_disclosure")]
        faith_quota = min(3, len(faith_jobs))
        secular_quota = 5 - faith_quota
        selected = faith_jobs[:faith_quota] + secular_jobs[:secular_quota]
    else:
        selected = eligible[:5]
    warning = None
    if len(selected) < 5:
        shortfall = 5 - len(selected)
        warning = (
            f"적합 직업 부족 ({len(selected)}/5) — 사용자 조건(나이={age}, 학력={education})에 "
            "맞는 카탈로그 직업이 부족합니다. 미달 슬롯은 placeholder로 표시."
        )
        for i in range(shortfall):
            selected.append(
                _make_unfilled_slot(
                    index=len(selected) + 1,
                    type_key=type_key,
                    reason=(
                        f"나이 {age}·학력 {education} 조건에 직접 부합하는 {type_key} "
                        "카테고리 직업이 카탈로그 내에 부족합니다. "
                        "보완 경로(추가 교육·자격증·경력)를 통해 진입 가능한 미래 옵션으로만 안내하세요."
                    ),
                )
            )
    return {
        "type": type_key,
        "slots": selected,
        "warning": warning,
    }
