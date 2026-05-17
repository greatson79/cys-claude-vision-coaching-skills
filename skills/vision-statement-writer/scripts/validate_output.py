#!/usr/bin/env python3
"""vision-statement-writer 결정론적 출력 검증.

사용자가 작성한 12필드 답변 JSON에 대해 다음을 결정론적으로 검사:
  1. 12개 필수 필드 모두 존재 여부
  2. 각 필드 최소·최대 글자 길이
  3. F11 Purposes 항목 수 (권장 5, 최소 1, 최대 7)
  4. F12 작성 일자 한국어 날짜 형식 (예: 2026년 5월 17일, 연도는 2000~2099)
  5. 빈칸 placeholder 잔류 (예: _____ 또는 "(빈칸)" 패턴)
  6. 박사님 책 결문 "부름을 받았습니다!" 변경/누락 금지 — 별도 옵션
  7. 절대 원칙(11번) 실존 인물 위반 — 본 검증은 사용자 입력 기반이므로 LLM에 책임.
     단, "박사님"·"최윤식" 같은 실존 인물명이 F1 이외 필드에 등장하면 경고.

CLI:
    python3 scripts/validate_output.py --answers answers.json
    python3 scripts/validate_output.py --answers answers.json --strict

종료 코드:
    0 — 전 항목 PASS
    1 — 1건 이상 FAIL
    2 — 입력 파싱 오류
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

PLACEHOLDER_PATTERNS = [
    re.compile(r"_{3,}"),  # 3개 이상 연속 언더스코어
    re.compile(r"\(\s*빈칸\s*\)"),
    re.compile(r"\(\s*blank\s*\)", re.IGNORECASE),
    re.compile(r"TODO", re.IGNORECASE),
    re.compile(r"PLACEHOLDER", re.IGNORECASE),
]

REAL_PERSON_FLAGS = ["최윤식", "최현식"]

DATE_RE = re.compile(r"^\s*(20\d{2})\s*년\s*(\d{1,2})\s*월\s*(\d{1,2})\s*일\s*$")


def load_fields() -> list:
    return json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))[
        "vision_statement_form"
    ]["fields"]


def check_required(field: dict, answers: dict, errors: list, warnings: list) -> None:
    fid = field["id"]
    val = answers.get(fid)
    if val is None or (isinstance(val, str) and val.strip() == ""):
        errors.append(f"[FAIL] {fid} 누락 — 필드 '{field['label_ko']}'가 비어 있다.")
        return
    if field["type"] == "list":
        if isinstance(val, str):
            warnings.append(
                f"[WARN] {fid} 타입은 list여야 하나 문자열로 입력됨. "
                "검증을 단일 항목으로 간주."
            )
            items = [val]
        else:
            items = val
        mn = field.get("min_items", 1)
        mx = field.get("max_items", 99)
        rc = field.get("recommended_items")
        if len(items) < mn:
            errors.append(
                f"[FAIL] {fid} 항목 수 {len(items)} < 최소 {mn} — Purposes 항목이 부족하다."
            )
        if len(items) > mx:
            errors.append(
                f"[FAIL] {fid} 항목 수 {len(items)} > 최대 {mx} — Purposes 항목이 너무 많다."
            )
        if rc and len(items) != rc:
            warnings.append(
                f"[WARN] {fid} 권장 항목 수 {rc}개 — 현재 {len(items)}개. "
                "박사님 양식은 5가지 단계화를 권장한다."
            )
        for i, it in enumerate(items, 1):
            if not isinstance(it, str) or not it.strip():
                errors.append(f"[FAIL] {fid}[{i}] 항목이 비어 있다.")
        return
    if not isinstance(val, str):
        errors.append(f"[FAIL] {fid} 타입은 string이어야 한다. (현재 {type(val).__name__})")
        return
    mn = field.get("min_chars")
    mx = field.get("max_chars")
    if mn is not None and len(val.strip()) < mn:
        errors.append(
            f"[FAIL] {fid} 글자 수 {len(val.strip())} < 최소 {mn} — "
            f"'{field['label_ko']}' 응답이 너무 짧다."
        )
    if mx is not None and len(val.strip()) > mx:
        errors.append(
            f"[FAIL] {fid} 글자 수 {len(val.strip())} > 최대 {mx} — "
            f"'{field['label_ko']}' 응답이 너무 길다."
        )


def check_placeholder(field: dict, answers: dict, errors: list) -> None:
    fid = field["id"]
    val = answers.get(fid)
    if val is None:
        return
    # F12 날짜는 placeholder 잔류 별도 검증.
    if fid == "F12_date":
        return
    if isinstance(val, str):
        for pat in PLACEHOLDER_PATTERNS:
            if pat.search(val):
                errors.append(
                    f"[FAIL] {fid} 빈칸 placeholder({pat.pattern}) 잔류 — "
                    "사용자 답변을 채워야 한다."
                )
                break
    elif isinstance(val, list):
        for i, it in enumerate(val, 1):
            if isinstance(it, str):
                for pat in PLACEHOLDER_PATTERNS:
                    if pat.search(it):
                        errors.append(
                            f"[FAIL] {fid}[{i}] placeholder({pat.pattern}) 잔류."
                        )
                        break


def check_date(field: dict, answers: dict, errors: list) -> None:
    val = answers.get(field["id"])
    if not isinstance(val, str):
        return
    m = DATE_RE.match(val)
    if not m:
        errors.append(
            f"[FAIL] {field['id']} 날짜 형식이 'YYYY년 M월 D일' 한국어 형식이 아니다. "
            f"(입력: '{val}')"
        )
        return
    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))
    if not (2000 <= year <= 2099):
        errors.append(f"[FAIL] {field['id']} 연도 {year} — 2000~2099 범위 밖.")
    if not (1 <= month <= 12):
        errors.append(f"[FAIL] {field['id']} 월 {month} — 1~12 범위 밖.")
    if not (1 <= day <= 31):
        errors.append(f"[FAIL] {field['id']} 일 {day} — 1~31 범위 밖.")


def check_real_person(field: dict, answers: dict, warnings: list) -> None:
    fid = field["id"]
    if fid == "F1_name":
        return  # 이름 필드는 자기 본인이므로 제외
    val = answers.get(fid)
    if not isinstance(val, str):
        return
    for name in REAL_PERSON_FLAGS:
        if name in val:
            warnings.append(
                f"[WARN] {fid}에 실존 인물명 '{name}'이 등장 — "
                "절대 원칙 11(실존 인물 식별 정보 금지) 점검 필요."
            )


def validate(answers: dict, strict: bool = False) -> tuple[int, list, list]:
    fields = load_fields()
    errors: list[str] = []
    warnings: list[str] = []
    for f in fields:
        check_required(f, answers, errors, warnings)
        check_placeholder(f, answers, errors)
        if f["id"] == "F12_date":
            check_date(f, answers, errors)
        check_real_person(f, answers, warnings)
    if strict and warnings:
        # strict 모드에선 경고도 실패 처리.
        errors.extend(f"[STRICT] {w}" for w in warnings)
    return (1 if errors else 0), errors, warnings


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--answers", required=True, help="답변 JSON 경로")
    p.add_argument("--strict", action="store_true", help="경고도 실패로 처리")
    args = p.parse_args()
    try:
        answers = json.loads(Path(args.answers).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: 입력 파싱 실패 — {e}", file=sys.stderr)
        return 2
    code, errors, warnings = validate(answers, strict=args.strict)
    if errors:
        print("=== 검증 실패 ===")
        for e in errors:
            print(e)
    if warnings:
        print("=== 경고 ===")
        for w in warnings:
            print(w)
    if not errors and not warnings:
        print("=== 전 항목 PASS ===")
    elif not errors:
        print("=== 전 항목 PASS (경고만 발생) ===")
    return code


if __name__ == "__main__":
    sys.exit(main())
