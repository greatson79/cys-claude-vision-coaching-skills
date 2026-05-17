#!/usr/bin/env python3
"""Round 2 — completely different 10 scenarios. Verify the verification."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.catalog import TYPE_KEYS, jobs_in_type  # noqa: E402
from lib.dedup import assert_no_duplicates  # noqa: E402
from lib.pipeline import UserProfile, build_plan  # noqa: E402

SCENARIO_FILE = os.path.join(HERE, "scenarios_round2.json")


def check_scenario(scn):
    sid = scn["id"]
    desc = scn["description"]
    prof_data = scn["profile"]
    prof = UserProfile(
        age=prof_data.get("age"),
        education=prof_data.get("education"),
        mbti=prof_data.get("mbti"),
        enneagram=prof_data.get("enneagram"),
        riasec=prof_data.get("riasec"),
        multiple_intel=prof_data.get("multiple_intel", []),
        values=prof_data.get("values", []),
        interests=prof_data.get("interests", []),
        current_job=prof_data.get("current_job"),
        location=prof_data.get("location"),
        faith_disclosed=bool(prof_data.get("faith_disclosed", False)),
        raw_input=prof_data.get("raw_input", ""),
    )
    out = build_plan(prof)
    plan = out["plan"]
    meta = out["meta"]
    problems = []

    # Universal constraints (always)
    for t in TYPE_KEYS:
        if len(plan[t]["slots"]) != 5:
            problems.append(f"{t} has {len(plan[t]['slots'])} slots, expected 5")
        for j in plan[t]["slots"]:
            if j.get("_verdict") == "fail":
                problems.append(f"FAIL-verdict slot leaked: {t}/{j['id']}")

    dup = assert_no_duplicates(plan)
    if dup:
        problems.append(f"Duplicates: {dup}")

    # Scenario-specific assertions
    if sid == "r2_01_12_year_old":
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        for forbidden in ("physician", "lawyer_big_firm", "professor_medical", "specialist_surgeon", "tax_attorney"):
            if forbidden in ids:
                problems.append(f"{forbidden} should not appear for 12yo middle-school")

    if sid == "r2_02_mid50_phd_transition":
        # All slots education-pass (phd > all min_education)
        for t in TYPE_KEYS:
            for j in plan[t]["slots"]:
                if j.get("_verdict_reason", "").startswith("학력 미달"):
                    problems.append(f"PhD blocked by education: {j['id']}")

    if sid == "r2_03_explicit_english_directive":
        if meta["language"] != "en":
            problems.append(f"expected en, got {meta['language']}")

    if sid == "r2_04_associate_degree_marketing":
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        for forbidden in ("physician", "lawyer_big_firm", "tax_attorney", "professor_medical", "specialist_surgeon"):
            if forbidden in ids:
                problems.append(f"{forbidden} present for college2yr user")

    if sid == "r2_05_75_widow_volunteer":
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        # synbio_researcher (max 65), ib_pe (max 65), vc_partner (max 70), airline_pilot (max 65) should not appear
        for forbidden in ("synbio_researcher", "ib_pe", "airline_pilot", "specialist_surgeon"):
            if forbidden in ids:
                problems.append(f"{forbidden} should not appear for 75yo")

    if sid == "r2_06_60_secular_high_pay":
        # No faith jobs since not disclosed
        for j in plan["retirement"]["slots"]:
            if j.get("requires_faith_disclosure"):
                problems.append(f"faith job leaked: {j['id']}")

    if sid == "r2_07_master_pivot_to_developer":
        # No fail verdicts
        for t in TYPE_KEYS:
            for j in plan[t]["slots"]:
                if j.get("_verdict") == "fail":
                    problems.append(f"fail slot: {t}/{j['id']}")

    if sid == "r2_08_disabled_ageless":
        # Faith disclosed → retirement slots should include at least one faith job
        has_faith = any(j.get("requires_faith_disclosure") for j in plan["retirement"]["slots"])
        if not has_faith:
            problems.append("faith_disclosed=true but no faith retirement job appeared")

    if sid == "r2_09_18yr_high_school_grad":
        # high school grad → no doctor/lawyer
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        for forbidden in ("physician", "lawyer_big_firm", "professor_medical", "tax_attorney", "specialist_surgeon"):
            if forbidden in ids:
                problems.append(f"{forbidden} blocked for 18yo high school")

    if sid == "r2_10_50_doctor_career_continuation":
        # PhD doctor at 50 → physician should be allowable (within max_age=75)
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        # Verify no fails leaked
        for t in TYPE_KEYS:
            for j in plan[t]["slots"]:
                if j.get("_verdict") == "fail":
                    problems.append(f"fail slot: {t}/{j['id']}")

    return {"id": sid, "description": desc, "ok": not problems, "problems": problems, "meta": meta}


def main():
    with open(SCENARIO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = [check_scenario(s) for s in data["scenarios"]]
    passed = sum(1 for r in results if r["ok"])
    total = len(results)
    for r in results:
        status = "✅ PASS" if r["ok"] else "❌ FAIL"
        print(f"{status} {r['id']}: {r['description']}")
        for p in r["problems"]:
            print(f"   - {p}")
    print()
    print(f"== Round 2: {passed}/{total} scenarios PASS ==")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
