"""Deterministic final-output checklist validator.

Validates every item from SKILL.md '출력 체크리스트' programmatically.
Run on the final markdown the LLM produced (or on the structured plan).
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple


REQUIRED_TYPE_HEADERS = [
    ("Type 1", r"##\s*Type\s*1\b"),
    ("Type 2", r"##\s*Type\s*2\b"),
    ("Type 3", r"##\s*Type\s*3\b"),
    ("Type 4", r"##\s*Type\s*4\b"),
]


def char_count_excluding_markdown(text: str) -> int:
    """Approximate visible character count by stripping markdown noise."""
    stripped = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    stripped = re.sub(r"[#>*_\-`\[\]()]", "", stripped)
    stripped = re.sub(r"\s+", " ", stripped)
    return len(stripped.strip())


def validate_plan_structure(plan: Dict) -> List[str]:
    """Check the structured plan dict (before formatting) is 20-slot/no-dup/etc."""
    problems = []
    expected = ["future", "happy_fun", "retirement", "high_pay"]
    for t in expected:
        entry = plan.get(t)
        if not entry:
            problems.append(f"Missing type entry: {t}")
            continue
        slots = entry.get("slots", [])
        if len(slots) != 5:
            problems.append(f"Type {t} has {len(slots)} slots, expected 5")
    # Cross-type dup check
    seen = {}
    for t in expected:
        for j in plan.get(t, {}).get("slots", []):
            if j["id"] in seen and seen[j["id"]] != t:
                problems.append(f"Duplicate job id {j['id']} in {seen[j['id']]} and {t}")
            seen[j["id"]] = t
    return problems


def validate_markdown(
    markdown: str,
    min_chars: int = 1000,
    require_disclaimers: bool = True,
    expected_language: str = "ko",
) -> Tuple[bool, List[str]]:
    """Return (ok, list of problems)."""
    problems = []

    # 1. four type headers
    for name, pat in REQUIRED_TYPE_HEADERS:
        if not re.search(pat, markdown):
            problems.append(f"Missing header: {name}")

    # 2. min length
    visible = char_count_excluding_markdown(markdown)
    if visible < min_chars:
        problems.append(f"Output too short: {visible} < {min_chars} chars")

    # 3. work type section
    if not re.search(r"직무\s*형태|Work\s*Type", markdown, re.IGNORECASE):
        problems.append("Missing 직무 형태 (Work Type) section")

    # 4. work type section must appear AFTER all 4 Type sections
    work_match = re.search(r"##\s*.*직무\s*형태|##\s*Work\s*Type", markdown, re.IGNORECASE)
    if work_match:
        last_type_pos = 0
        for _, pat in REQUIRED_TYPE_HEADERS:
            m = list(re.finditer(pat, markdown))
            if m:
                last_type_pos = max(last_type_pos, m[-1].end())
        if work_match.start() < last_type_pos:
            problems.append("직무 형태 섹션이 Type 1~4 뒤가 아닌 앞 또는 중간에 위치")

    # 5. limitations disclaimer
    if require_disclaimers:
        if not re.search(r"한계|Limit|시뮬레이션|simulation", markdown, re.IGNORECASE):
            problems.append("Missing 한계·주의 disclaimer")

    # 6. follow-up skill announcement
    if not re.search(r"vision-clarity-coaching|vision-\*|다음 단계|next\s*step", markdown, re.IGNORECASE):
        problems.append("Missing follow-up vision-* skill guidance")

    # 7. each Type must contain 5 numbered items
    # Split markdown into Type sections by header
    headers = [(name, m.start()) for name, pat in REQUIRED_TYPE_HEADERS for m in [re.search(pat, markdown)] if m]
    headers_sorted = sorted(headers, key=lambda t: t[1])
    for i, (name, start) in enumerate(headers_sorted):
        end = headers_sorted[i + 1][1] if i + 1 < len(headers_sorted) else len(markdown)
        section = markdown[start:end]
        # Count "### 1." style or "### 1) " or "**1." patterns
        nums = re.findall(r"###\s*([1-9])\b|^\s*([1-9])\.\s", section, re.MULTILINE)
        flat = [n[0] or n[1] for n in nums]
        unique_first_five = {n for n in flat if n in {"1", "2", "3", "4", "5"}}
        if len(unique_first_five) < 5:
            problems.append(f"{name} section appears to lack 5 numbered items (found {sorted(unique_first_five)})")

    # 8. language match
    from .language import detect_language
    detected = detect_language(markdown)
    if detected != expected_language:
        problems.append(f"Output language detected={detected}, expected={expected_language}")

    return (len(problems) == 0, problems)
