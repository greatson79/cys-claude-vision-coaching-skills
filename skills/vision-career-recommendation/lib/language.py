"""Deterministic input-language detection.

Strategy: Compare Hangul vs Latin character counts in raw user input.
- Hangul ratio >= 0.30 → 'ko'
- Else if explicit Korean tokens present → 'ko'
- Else → 'en'
Also recognises explicit override directives (last wins): '한국어로', 'in english',
'respond in english', '영어로'.
"""
from __future__ import annotations

import re

HANGUL_RE = re.compile(r"[가-힯ᄀ-ᇿ㄰-㆏]")
LATIN_RE = re.compile(r"[A-Za-z]")
DIRECTIVE_KO_RE = re.compile(r"(한국어로|국문으로|한글로|한국어 응답)", re.IGNORECASE)
DIRECTIVE_EN_RE = re.compile(r"(in english|respond in english|english reply|영어로)", re.IGNORECASE)


def detect_language(text: str) -> str:
    if not text:
        return "ko"

    # Last explicit directive wins
    ko_match = list(DIRECTIVE_KO_RE.finditer(text))
    en_match = list(DIRECTIVE_EN_RE.finditer(text))
    if ko_match and en_match:
        last_ko = ko_match[-1].start()
        last_en = en_match[-1].start()
        return "ko" if last_ko > last_en else "en"
    if ko_match:
        return "ko"
    if en_match:
        return "en"

    h = len(HANGUL_RE.findall(text))
    l = len(LATIN_RE.findall(text))
    total = h + l
    if total == 0:
        return "ko"
    if h / total >= 0.30:
        return "ko"
    return "en"
