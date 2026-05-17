"""End-to-end deterministic pipeline.

Inputs (UserProfile) → Filtered candidates → 20-slot plan → Dedup → Validation.

LLM only consumes the structured plan to write rationales + 1000+ char coaching.
"""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from .catalog import TYPE_KEYS, normalize_education, get_age_category
from .dedup import assert_no_duplicates, resolve_duplicates
from .filter_jobs import select_top5
from .language import detect_language


@dataclass
class UserProfile:
    age: Optional[int] = None
    education: Optional[str] = None  # raw or normalized
    mbti: Optional[str] = None
    enneagram: Optional[str] = None
    riasec: Optional[str] = None
    multiple_intel: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    current_job: Optional[str] = None
    location: Optional[str] = None
    faith_disclosed: bool = False
    raw_input: str = ""


def build_plan(profile: UserProfile) -> Dict:
    edu_norm = normalize_education(profile.education) if profile.education else None
    age_cat = get_age_category(profile.age) if profile.age is not None else None

    plan = {}
    for t in TYPE_KEYS:
        plan[t] = select_top5(
            type_key=t,
            age=profile.age,
            education=edu_norm,
            include_faith_jobs=profile.faith_disclosed,
        )

    plan = resolve_duplicates(
        plan,
        age=profile.age,
        education=edu_norm,
        include_faith_jobs=profile.faith_disclosed,
    )

    dup_issues = assert_no_duplicates(plan)
    meta = {
        "language": detect_language(profile.raw_input or ""),
        "age_category": age_cat,
        "education_normalized": edu_norm,
        "faith_disclosed": profile.faith_disclosed,
        "dup_issues_after_resolve": dup_issues,
        "input_categories": _summarize_input(profile),
    }
    return {"plan": plan, "meta": meta}


def _summarize_input(profile: UserProfile) -> Dict:
    return {
        "mbti": profile.mbti,
        "enneagram": profile.enneagram,
        "riasec": profile.riasec,
        "multiple_intel": profile.multiple_intel,
        "values": profile.values,
        "interests": profile.interests,
        "current_job": profile.current_job,
        "location": profile.location,
    }


def cli_main(argv: List[str]) -> int:
    """CLI entry: read JSON profile from stdin or first arg, print plan as JSON."""
    if len(argv) > 1 and argv[1] not in {"-", "--stdin"}:
        with open(argv[1], "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    prof = UserProfile(
        age=data.get("age"),
        education=data.get("education"),
        mbti=data.get("mbti"),
        enneagram=data.get("enneagram"),
        riasec=data.get("riasec"),
        multiple_intel=data.get("multiple_intel", []),
        values=data.get("values", []),
        interests=data.get("interests", []),
        current_job=data.get("current_job"),
        location=data.get("location"),
        faith_disclosed=bool(data.get("faith_disclosed", False)),
        raw_input=data.get("raw_input", ""),
    )
    result = build_plan(prof)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(cli_main(sys.argv))
