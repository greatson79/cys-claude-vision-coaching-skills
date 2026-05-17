#!/usr/bin/env python3
"""Final verification: 10 live user prompts.
For each P1~P10:
  1. Verify plan structure (4 types × 5 slots, no dups, no fail-verdicts)
  2. Verify every slot id exists in master catalog (no LLM hallucination room)
  3. Verify language detection matches user input
  4. Verify scenario-specific assertions
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.catalog import TYPE_KEYS, jobs_in_type, load_catalog  # noqa: E402
from lib.dedup import assert_no_duplicates  # noqa: E402


CATALOG_IDS = set()
for t in TYPE_KEYS:
    for j in jobs_in_type(t):
        CATALOG_IDS.add(j["id"])


def verify_plan(plan_path, expected):
    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    plan = data["plan"]
    meta = data["meta"]
    problems = []

    # Hard universal checks
    for t in TYPE_KEYS:
        if len(plan[t]["slots"]) != 5:
            problems.append(f"{t} has {len(plan[t]['slots'])} slots")
        for j in plan[t]["slots"]:
            if j.get("_verdict") == "fail":
                problems.append(f"fail-verdict slot leaked: {t}/{j['id']}")
            # Catalog-id check (placeholders allowed but flagged)
            if not j.get("_is_placeholder"):
                if j["id"] not in CATALOG_IDS:
                    problems.append(f"NON-CATALOG job id appears: {t}/{j['id']} (hallucination)")
    dup = assert_no_duplicates(plan)
    if dup:
        problems.append(f"dup: {dup}")

    # expected language
    if expected.get("language") and meta["language"] != expected["language"]:
        problems.append(f"lang={meta['language']} expected {expected['language']}")
    if expected.get("age_category") and meta["age_category"]["id"] != expected["age_category"]:
        problems.append(f"age_cat={meta['age_category']['id']} expected {expected['age_category']}")
    if expected.get("education_normalized") and meta["education_normalized"] != expected["education_normalized"]:
        problems.append(f"edu={meta['education_normalized']} expected {expected['education_normalized']}")

    # Scenario-specific
    forbidden = expected.get("forbidden_ids", set())
    found = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
    for fid in forbidden:
        if fid in found:
            problems.append(f"forbidden id appears: {fid}")
    must_have_faith = expected.get("must_have_faith_in_retirement", False)
    if must_have_faith:
        has = any(j.get("requires_faith_disclosure") for j in plan["retirement"]["slots"])
        if not has:
            problems.append("faith_disclosed=true but no faith job in retirement")
    must_not_have_faith = expected.get("must_not_have_faith_in_retirement", False)
    if must_not_have_faith:
        has = any(j.get("requires_faith_disclosure") for j in plan["retirement"]["slots"])
        if has:
            problems.append("faith_disclosed=false but faith job appears in retirement")

    return problems


EXPECTED = {
    "p1": {"language": "ko", "age_category": "early_career", "education_normalized": "bachelor",
           "must_not_have_faith_in_retirement": True},
    "p2": {"language": "ko", "age_category": "senior_career", "education_normalized": "doctorate",
           "must_not_have_faith_in_retirement": True},
    "p3": {"language": "ko", "age_category": "young_adult", "education_normalized": "high",
           "forbidden_ids": {"physician", "lawyer_big_firm", "professor_medical", "tax_attorney", "specialist_surgeon"}},
    "p4": {"language": "ko", "age_category": "pre_retirement", "education_normalized": "bachelor",
           "must_not_have_faith_in_retirement": True},
    "p5": {"language": "ko", "age_category": "early_career", "education_normalized": "doctorate"},
    "p6": {"language": "ko", "age_category": "senior_career", "education_normalized": "bachelor",
           "must_not_have_faith_in_retirement": True,
           "forbidden_ids": {"physician", "lawyer_big_firm", "professor_medical"}},
    "p7": {"language": "ko", "age_category": "young_adult", "education_normalized": "bachelor",
           "forbidden_ids": {"physician", "lawyer_big_firm", "professor_medical", "tax_attorney", "specialist_surgeon"}},
    "p8": {"language": "ko", "age_category": "mid_career", "education_normalized": "high",
           "forbidden_ids": {"physician", "lawyer_big_firm", "professor_medical", "tax_attorney", "dentist", "pharmacist", "oriental_medicine"}},
    "p9": {"language": "ko", "age_category": "pre_retirement", "education_normalized": "doctorate",
           "must_have_faith_in_retirement": True},
    "p10": {"language": "ko", "age_category": "early_career", "education_normalized": "doctorate"},
}


def main():
    results = []
    for i in range(1, 11):
        key = f"p{i}"
        path = f"/tmp/vcr_live_test/{key}_plan.json"
        problems = verify_plan(path, EXPECTED[key])
        results.append((key, problems))
    passed = sum(1 for _, p in results if not p)
    for key, problems in results:
        status = "✅ PASS" if not problems else "❌ FAIL"
        print(f"{status} {key}")
        for p in problems:
            print(f"   - {p}")
    print()
    print(f"== Live prompts: {passed}/{len(results)} PASS ==")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
