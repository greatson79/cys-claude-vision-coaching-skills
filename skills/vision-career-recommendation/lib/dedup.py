"""Cross-type duplicate detection & reassignment.

SKILL.md priority: future > high_pay > happy_fun > retirement.
If the same job.id appears in multiple Type slot lists, retain it only in
the highest-priority type. Lower-priority slots are flagged for replacement.
"""
from __future__ import annotations

from typing import Dict, List, Set

from .catalog import DEDUP_PRIORITY, jobs_in_type
from .filter_jobs import select_top5


def resolve_duplicates(
    plan: Dict[str, Dict],
    age,
    education,
    include_faith_jobs: bool,
) -> Dict[str, Dict]:
    """Plan is dict: type_key -> {"slots": [job, ...], "warning": ...}.
    Returns mutated plan where each job.id appears in exactly one type.

    Placeholder slots (`_is_placeholder=True`) are NOT considered duplicates
    and are replaced with real jobs whenever possible during the refill pass.
    """
    seen: Set[str] = set()
    keep_by_type: Dict[str, List] = {}
    duplicated_ids: Set[str] = set()

    for tkey in DEDUP_PRIORITY:
        entry = plan.get(tkey)
        if not entry:
            continue
        kept = []
        for j in entry["slots"]:
            if j.get("_is_placeholder"):
                # Skip placeholders in the dedup pass; refill pass will try to replace them.
                continue
            if j["id"] in seen:
                duplicated_ids.add(j["id"])
                continue
            seen.add(j["id"])
            kept.append(j)
        keep_by_type[tkey] = kept

    # Re-fill any type that now has fewer than 5 slots
    from .filter_jobs import classify_fit, _make_unfilled_slot
    from .catalog import normalize_education
    edu_norm = normalize_education(education) if education else None

    for tkey in DEDUP_PRIORITY:
        slots = keep_by_type.get(tkey, [])
        if len(slots) >= 5:
            keep_by_type[tkey] = slots[:5]
            continue
        full_pool = jobs_in_type(tkey)

        def refill_sort_key(j):
            # When user discloses faith AND filling Type 3, surface faith-tagged jobs first.
            faith_boost = 0 if (
                tkey == "retirement"
                and include_faith_jobs
                and j.get("requires_faith_disclosure")
            ) else 1
            return faith_boost

        candidate_pool = sorted(full_pool, key=refill_sort_key)
        for j in candidate_pool:
            if j["id"] in seen:
                continue
            if j.get("requires_faith_disclosure") and not include_faith_jobs:
                continue
            verdict, reason = classify_fit(j, age, edu_norm)
            if verdict == "fail":
                continue
            new_j = dict(j)
            new_j["_verdict"] = verdict
            new_j["_verdict_reason"] = reason
            slots.append(new_j)
            seen.add(j["id"])
            if len(slots) >= 5:
                break

        if len(slots) < 5:
            shortfall = 5 - len(slots)
            for _ in range(shortfall):
                slots.append(
                    _make_unfilled_slot(
                        index=len(slots) + 1,
                        type_key=tkey,
                        reason=(
                            f"나이 {age}·학력 {education} 조건에 직접 부합하는 {tkey} "
                            "카테고리 직업이 카탈로그 내에 부족합니다. "
                            "보완 경로(추가 교육·자격·경력)로 진입 가능한 미래 옵션으로 안내."
                        ),
                    )
                )
        keep_by_type[tkey] = slots[:5]

    # Rebuild plan
    for tkey in DEDUP_PRIORITY:
        plan[tkey]["slots"] = keep_by_type.get(tkey, [])
        warning = plan[tkey].get("warning")
        if duplicated_ids and tkey not in (DEDUP_PRIORITY[0],):
            extra = f"중복 직업 제거 후 재선정 적용: {sorted(duplicated_ids)}"
            plan[tkey]["warning"] = (warning + " | " + extra) if warning else extra
    return plan


def assert_no_duplicates(plan: Dict[str, Dict]) -> List[str]:
    """Return list of duplicate-id problems (empty if clean)."""
    seen: Dict[str, str] = {}
    problems: List[str] = []
    for tkey, entry in plan.items():
        for j in entry["slots"]:
            jid = j["id"]
            if jid in seen and seen[jid] != tkey:
                problems.append(f"{jid} appears in both {seen[jid]} and {tkey}")
            seen[jid] = tkey
    return problems
