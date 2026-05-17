#!/usr/bin/env python3
"""Validate LLM-produced markdown against SKILL.md checklist."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from lib.output_validator import validate_markdown  # noqa: E402


def main(argv):
    if len(argv) < 2:
        print("Usage: validate_output.py <markdown_file> [--lang ko|en] [--min CHARS]", file=sys.stderr)
        return 2
    path = argv[1]
    lang = "ko"
    min_chars = 1000
    i = 2
    while i < len(argv):
        if argv[i] == "--lang" and i + 1 < len(argv):
            lang = argv[i + 1]
            i += 2
        elif argv[i] == "--min" and i + 1 < len(argv):
            min_chars = int(argv[i + 1])
            i += 2
        else:
            i += 1
    with open(path, "r", encoding="utf-8") as f:
        md = f.read()
    ok, problems = validate_markdown(md, min_chars=min_chars, expected_language=lang)
    result = {"ok": ok, "problems": problems}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
