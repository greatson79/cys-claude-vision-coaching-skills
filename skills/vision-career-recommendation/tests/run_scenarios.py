#!/usr/bin/env python3
"""Run 10 acceptance scenarios — assert PASS for all deterministic constraints."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.catalog import TYPE_KEYS, jobs_in_type  # noqa: E402
from lib.dedup import assert_no_duplicates  # noqa: E402
from lib.language import detect_language  # noqa: E402
from lib.pipeline import UserProfile, build_plan  # noqa: E402


SCENARIO_FILE = os.path.join(HERE, "scenarios.json")


def find_job(jid: str):
    for t in TYPE_KEYS:
        for j in jobs_in_type(t):
            if j["id"] == jid:
                return (t, j)
    return (None, None)


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

    # G1: 4 types each have exactly 5 slots
    for t in TYPE_KEYS:
        if len(plan[t]["slots"]) != 5:
            problems.append(f"{t} has {len(plan[t]['slots'])} slots, expected 5")

    # G2: no duplicates
    dup = assert_no_duplicates(plan)
    if dup:
        problems.append(f"Duplicates: {dup}")

    # G3: scenario-specific assertions
    if sid == "s01_youth_high_school_dropout":
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        for forbidden in ("physician", "lawyer_big_firm", "professor_medical", "tax_attorney", "specialist_surgeon"):
            if forbidden in ids:
                problems.append(f"forbidden {forbidden} present for 17yo middle-school")
        for j in plan["high_pay"]["slots"]:
            if j["_verdict"] == "fail":
                problems.append(f"high_pay slot kept fail: {j['id']}")

    if sid == "s02_translator_career_pivot":
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        # 42yo master should not get youth-entry, should not duplicate
        for j in plan["future"]["slots"] + plan["high_pay"]["slots"]:
            if j["_verdict"] == "fail":
                problems.append(f"fail-verdict slot kept: {j['id']}")

    if sid == "s03_english_input":
        if meta["language"] != "en":
            problems.append(f"language detected={meta['language']}, expected en")

    if sid == "s04_elderly_82_retiree":
        # synbio_researcher max_age=65 → must NOT appear
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        for forbidden in ("synbio_researcher", "ev_battery_engineer", "smr_engineer", "ib_pe", "vc_partner", "airline_pilot"):
            if forbidden in ids:
                problems.append(f"forbidden {forbidden} present for 82yo")
        # faith jobs must be allowed
        has_faith = any(j.get("requires_faith_disclosure") for j in plan["retirement"]["slots"])
        if not has_faith:
            problems.append("faith_disclosed=true but no faith retirement job appeared")

    if sid == "s05_phd_wants_cafe":
        # all jobs should pass at education level (no education-fail)
        for t in TYPE_KEYS:
            for j in plan[t]["slots"]:
                if j["_verdict"] == "fail" and "학력" in j["_verdict_reason"]:
                    problems.append(f"PhD blocked from {j['id']} due to education")

    if sid == "s06_age_unknown":
        # All slots verdict should be 'unknown' when age & edu both missing
        for t in TYPE_KEYS:
            for j in plan[t]["slots"]:
                if j["_verdict"] not in ("unknown", "pass", "borderline"):
                    problems.append(f"unknown profile gave non-allowed verdict: {j['id']}={j['_verdict']}")

    if sid == "s07_high_pay_high_school":
        ids = {j["id"] for t in TYPE_KEYS for j in plan[t]["slots"]}
        for forbidden in ("physician", "lawyer_big_firm", "professor_medical", "tax_attorney", "specialist_surgeon"):
            if forbidden in ids:
                problems.append(f"forbidden {forbidden} appears for high-school user")

    if sid == "s08_synonym_education":
        if meta["education_normalized"] != "master":
            problems.append(f"education '대학원' normalized to {meta['education_normalized']}, expected master")

    if sid == "s09_secular_no_faith":
        # no faith jobs should appear in retirement slots
        for j in plan["retirement"]["slots"]:
            if j.get("requires_faith_disclosure"):
                problems.append(f"faith job {j['id']} present though faith_disclosed=false")

    if sid == "s10_min_age_borderline":
        # 23yo wants futurist (min_age 32) — should not appear in slot or appear as borderline if at all
        for t in TYPE_KEYS:
            for j in plan[t]["slots"]:
                if j["id"] == "futurist_consultant" and j["_verdict"] == "pass":
                    problems.append("futurist_consultant min_age=32 but 23yo got pass verdict")

    return {"id": sid, "description": desc, "ok": not problems, "problems": problems, "meta": meta}


def main():
    with open(SCENARIO_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for scn in data["scenarios"]:
        results.append(check_scenario(scn))

    passed = sum(1 for r in results if r["ok"])
    total = len(results)

    for r in results:
        status = "✅ PASS" if r["ok"] else "❌ FAIL"
        print(f"{status} {r['id']}: {r['description']}")
        for p in r["problems"]:
            print(f"   - {p}")

    print()
    print(f"== {passed}/{total} scenarios PASS ==")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
