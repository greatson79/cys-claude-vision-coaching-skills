"""Deterministic loader for the master job catalog."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, List, Optional

CATALOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "job_catalog.json",
)

TYPE_KEYS = ["future", "happy_fun", "retirement", "high_pay"]
TYPE_LABEL_KO = {
    "future": "Type 1 — Future Jobs (미래 직업)",
    "happy_fun": "Type 2 — Happy & Fun Jobs (행복·재미)",
    "retirement": "Type 3 — Retirement Volunteering (은퇴 후 사회·종교 자원봉사)",
    "high_pay": "Type 4 — High-Pay Current (현재 고소득 직업)",
}
TYPE_EMOJI = {"future": "🚀", "happy_fun": "😊", "retirement": "⛪", "high_pay": "💰"}
DEDUP_PRIORITY = ["future", "high_pay", "happy_fun", "retirement"]


@lru_cache(maxsize=1)
def load_catalog() -> Dict:
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def education_rank(level: str) -> int:
    catalog = load_catalog()
    if level not in catalog["education_levels"]:
        raise ValueError(f"Unknown education level: {level}")
    return catalog["education_levels"][level]


def normalize_education(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    key = str(raw).strip().lower()
    catalog = load_catalog()
    syn = catalog["education_synonyms"]
    if key in catalog["education_levels"]:
        return key
    if key in syn:
        return syn[key]
    for k, v in syn.items():
        if k.lower() == key:
            return v
    return None


def get_age_category(age: int) -> Optional[Dict]:
    catalog = load_catalog()
    for cat in catalog["age_categories"]:
        if cat["min"] <= age <= cat["max"]:
            return cat
    return None


def jobs_in_type(type_key: str) -> List[Dict]:
    if type_key not in TYPE_KEYS:
        raise ValueError(f"Unknown type: {type_key}")
    catalog = load_catalog()
    return list(catalog["jobs"].get(type_key, []))


def all_jobs() -> List[Dict]:
    out = []
    for t in TYPE_KEYS:
        for j in jobs_in_type(t):
            j2 = dict(j)
            j2["_type"] = t
            out.append(j2)
    return out
