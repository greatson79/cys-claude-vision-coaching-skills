"""Deterministic rationale_key ↔ user profile matching.

Each job carries `rationale_keys` (e.g. ["ai", "ethics", "policy", "philosophy"]).
This module maps those keys to the user's MBTI/Enneagram/RIASEC/MI/values/interests
using a fixed lookup table — NEVER LLM free-form generation.
"""
from __future__ import annotations

from typing import Dict, List, Optional


MBTI_RATIONALE_KEYS: Dict[str, List[str]] = {
    "I": ["intrapersonal", "research", "writing"],
    "E": ["interpersonal", "performance", "leadership"],
    "S": ["bodily", "craft", "service"],
    "N": ["ai", "foresight", "narrative", "innovation"],
    "T": ["logic", "engineering", "analysis", "law"],
    "F": ["service", "care", "art", "interpersonal", "spirituality"],
    "J": ["policy", "strategy", "governance"],
    "P": ["creativity", "design", "art"],
}

ENNEAGRAM_RATIONALE_KEYS: Dict[str, List[str]] = {
    "1": ["ethics", "law", "policy", "justice"],
    "2": ["service", "care", "interpersonal"],
    "3": ["high_income", "achievement", "excellence"],
    "4": ["art", "narrative", "creativity"],
    "5": ["research", "data", "ai", "engineering"],
    "6": ["safety", "community", "governance"],
    "7": ["travel", "media", "creativity"],
    "8": ["leadership", "strategy", "power", "high_income"],
    "9": ["peace", "balance", "service"],
}

RIASEC_RATIONALE_KEYS: Dict[str, List[str]] = {
    "R": ["bodily", "craft", "engineering"],
    "I": ["research", "data", "ai"],
    "A": ["art", "creativity", "narrative"],
    "S": ["service", "interpersonal", "care"],
    "E": ["leadership", "strategy", "high_income"],
    "C": ["finance", "audit", "policy"],
}

MI_RATIONALE_KEYS: Dict[str, List[str]] = {
    "언어": ["language", "narrative", "writing"],
    "linguistic": ["language", "narrative", "writing"],
    "논리수학": ["logic", "data", "engineering", "analysis"],
    "logical-mathematical": ["logic", "data", "engineering"],
    "공간": ["visual", "design", "spatial"],
    "spatial": ["visual", "design", "spatial"],
    "신체운동": ["bodily", "craft", "performance"],
    "bodily-kinesthetic": ["bodily", "craft"],
    "음악": ["music", "art"],
    "musical": ["music", "art"],
    "대인관계": ["interpersonal", "service", "leadership"],
    "interpersonal": ["interpersonal", "service"],
    "자기성찰": ["intrapersonal", "spirituality", "writing"],
    "intrapersonal": ["intrapersonal", "spirituality"],
    "자연": ["naturalist", "environment"],
    "naturalist": ["naturalist", "environment"],
}


def find_matches(rationale_keys: List[str], profile_keys: List[str]) -> List[str]:
    rk_set = set(rationale_keys)
    pk_set = set(profile_keys)
    return sorted(rk_set & pk_set)


def derive_profile_keys(profile: Dict) -> Dict[str, List[str]]:
    """Return per-source profile_keys dict (MBTI/Enneagram/RIASEC/MI/values/interests)."""
    out: Dict[str, List[str]] = {}

    mbti = profile.get("mbti")
    if mbti:
        keys: List[str] = []
        for letter in mbti.upper():
            keys.extend(MBTI_RATIONALE_KEYS.get(letter, []))
        out["mbti"] = sorted(set(keys))

    enn = profile.get("enneagram")
    if enn:
        enn_str = str(enn).strip().replace("Type", "").replace("type", "").strip()
        out["enneagram"] = ENNEAGRAM_RATIONALE_KEYS.get(enn_str, [])

    riasec = profile.get("riasec")
    if riasec:
        keys = []
        for letter in riasec.upper():
            keys.extend(RIASEC_RATIONALE_KEYS.get(letter, []))
        out["riasec"] = sorted(set(keys))

    mi = profile.get("multiple_intel", [])
    if mi:
        keys = []
        for m in mi:
            keys.extend(MI_RATIONALE_KEYS.get(m, []))
            keys.extend(MI_RATIONALE_KEYS.get(m.lower(), []))
        out["multiple_intel"] = sorted(set(keys))

    # Values & interests are free text — match by simple lowercase substring containment
    # against a fixed value→key mini-table.
    VALUES_KEYS = {
        "balance": ["peace", "balance"],
        "peace": ["peace", "balance"],
        "service": ["service", "care"],
        "wisdom": ["research", "intrapersonal"],
        "justice": ["law", "ethics", "policy", "justice"],
        "faith": ["spirituality", "religion"],
        "love": ["service", "care", "interpersonal"],
        "excellence": ["achievement", "excellence", "high_income"],
        "creativity": ["creativity", "art"],
        "community": ["community", "service"],
        "innovation": ["innovation", "ai", "engineering"],
        "narrative": ["narrative", "language"],
        "healing": ["care", "health"],
        "freedom": ["creativity", "travel"],
        "achievement": ["achievement", "excellence"],
        "joy": ["creativity", "performance"],
        "power": ["leadership", "strategy"],
    }
    vkeys: List[str] = []
    for v in profile.get("values", []):
        vkeys.extend(VALUES_KEYS.get(v.lower(), []))
    out["values"] = sorted(set(vkeys))

    INTERESTS_KEYS = {
        "ai": ["ai", "data", "engineering"],
        "교육": ["education", "service"],
        "글쓰기": ["language", "writing", "narrative"],
        "작가": ["language", "writing", "narrative"],
        "음악": ["music", "art"],
        "사진": ["visual", "art"],
        "여행": ["travel", "narrative"],
        "환경": ["environment", "naturalist"],
        "기후": ["climate", "environment"],
        "디자인": ["design", "visual", "art"],
        "사업": ["leadership", "strategy", "small_business"],
        "고소득": ["high_income"],
        "봉사": ["service", "care", "community"],
        "ngo": ["service", "civic"],
        "사회 공헌": ["service", "civic", "community"],
        "워라밸": ["peace", "balance"],
        "안정": ["governance", "policy"],
        "전략": ["strategy", "leadership"],
        "미래학": ["foresight", "strategy", "research"],
        "프로그래밍": ["software", "engineering", "ai"],
        "소프트웨어": ["software", "engineering"],
        "컴퓨터공학": ["software", "engineering", "ai"],
        "정밀의료": ["health", "ai", "data"],
        "헬스케어": ["health", "ai"],
        "ai 헬스케어": ["health", "ai"],
        "ai 윤리": ["ai", "ethics", "policy"],
        "성경공부": ["spirituality", "religion"],
        "전도": ["spirituality", "religion", "service"],
        "조직 내 안정": ["governance", "policy"],
        "이야기": ["narrative", "language"],
        "공공": ["policy", "governance"],
    }
    ikeys: List[str] = []
    for it in profile.get("interests", []):
        ikeys.extend(INTERESTS_KEYS.get(it.lower(), []))
    out["interests"] = sorted(set(ikeys))

    return out


def build_rationale_sentence(job: Dict, profile_keys: Dict[str, List[str]], lang: str = "ko") -> str:
    """Produce a deterministic one-sentence rationale for this job.

    Combines: matched keys per source (MBTI/Enneagram/etc.) + job.rationale_keys.
    Never invents content beyond what is in profile_keys ∩ job.rationale_keys.
    """
    rk = job.get("rationale_keys", [])
    matched_sources: List[str] = []
    for src, pkeys in profile_keys.items():
        m = find_matches(rk, pkeys)
        if m:
            label = {
                "mbti": "MBTI",
                "enneagram": "에니어그램",
                "riasec": "STRONG/RIASEC",
                "multiple_intel": "다중지능",
                "values": "가치",
                "interests": "관심",
            }.get(src, src)
            matched_sources.append(f"{label}({', '.join(m)})")

    if not matched_sources:
        if lang == "en":
            return (
                f"Catalog rationale keys: {', '.join(rk)}. No direct user-profile overlap detected; "
                "suggested for breadth and exploratory consideration."
            )
        return (
            f"카탈로그 직무 키워드 [{', '.join(rk)}]에 대해 사용자 프로파일 직접 일치는 없으나, "
            "탐색·확장 후보로 제안."
        )

    if lang == "en":
        return f"Matches the user's {' / '.join(matched_sources)}; aligns with job rationale keys [{', '.join(rk)}]."
    return f"사용자 {' / '.join(matched_sources)}와(과) 직무 키워드 [{', '.join(rk)}] 정합."
