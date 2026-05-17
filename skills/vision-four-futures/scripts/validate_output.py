#!/usr/bin/env python3
"""
vision-four-futures — 출력 검증기.

LLM이 4가지 미래 시나리오를 작성한 뒤, 그 결과가 박사님 책 골격을
만족하는지 결정론적으로 검증한다. SKILL.md는 4단계 완료 직후 이 스크립트로
출력을 통과시킨다.

검증 규칙 (모두 결정론):
  R1) F1·F2·F3·F4 네 라벨이 모두 본문에 등장한다 (한국어 또는 영어 어느 쪽이든 OK).
  R2) F1 섹션에 4요소 키워드(트렌드·계획·심층원동력·대중[이미지])가 모두 등장한다.
  R3) F3 섹션에 두 하위 종류 키워드(비약적 진보·붕괴)가 모두 등장한다.
  R4) 본문에서 확률 수치(70%, 80%, 51% 등)를 단정적으로 사용하지 않는다.
       — 허용: 수치가 등장하되 '해석치'·'책에 명시되지 않음'·'추정'·'추산'·'유추' 같은
         담보 표현이 인접 (±200자)에 함께 등장.
  R5) Type B(한 미래만 깊이)가 아닌 경우 F1·F2·F3·F4 섹션 헤더가 모두 존재해야 한다.

CLI:
    python3 scripts/validate_output.py <output.md> [--mode A|B|C|D] [--focus F3]
    cat output.md | python3 scripts/validate_output.py - [--mode A]

종료 코드:
    0 — 전 항목 PASS
    1 — 하나 이상 FAIL
    2 — 사용법 오류
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ASSETS = Path(__file__).resolve().parent.parent / "assets"

PROBABILITY_PATTERN = re.compile(
    r"(\d{1,3})\s*%|(\d{1,3})\s*~\s*(\d{1,3})\s*%"
)

PROBABILITY_CLAIM_TRIGGERS = [
    "확률", "가능성", "발생 확률", "발생할 확률",
]

FUTURE_LABEL_TRIGGERS = [
    "기본미래", "Plausible Future", "Plausible World",
    "가능 미래", "Possible Future", "Possible World",
    "뜻밖의 미래", "Wildcard Future", "Wildcard World", "Unexpected Future",
    "바람직한 미래", "Normative Future", "Preferred Future",
]

HEDGE_TERMS = [
    "해석치", "해석", "통용", "추정", "추산", "유추",
    "명시되지 않", "명시 안", "직접 명시", "확인 필요",
    "원서 직접", "외부 해석", "박사님 책 예시", "예시 질문",
    "정확하게 맞출", "정확히 맞출",
]


def load_facts() -> dict:
    return json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))


def has_label(text: str, future: dict) -> bool:
    labels = [future["korean_label"], future["english_label"]]
    labels.extend(future.get("synonyms_english", []))
    return any(lbl in text for lbl in labels)


def check_r1_all_labels(text: str, futures: list[dict]) -> dict:
    missing = [f["id"] for f in futures if not has_label(text, f)]
    return {
        "id": "R1",
        "name": "4가지 미래 라벨 모두 등장",
        "pass": not missing,
        "missing": missing,
    }


def find_section(text: str, future: dict) -> str | None:
    """주어진 미래 라벨로 시작하는 섹션(다음 미래 라벨 전까지)을 추출."""
    labels = [future["korean_label"], future["english_label"]] + future.get(
        "synonyms_english", []
    )
    label_pat = "|".join(re.escape(l) for l in labels)
    m = re.search(rf"(^|[\n#])([^\n]*({label_pat})[^\n]*)\n", text)
    if not m:
        return None
    start = m.end()
    # 다음 future label까지 자르기
    facts = load_facts()
    other_labels = []
    for fo in facts["futures"]:
        if fo["id"] != future["id"]:
            other_labels.append(fo["korean_label"])
            other_labels.append(fo["english_label"])
            other_labels.extend(fo.get("synonyms_english", []))
    end = len(text)
    for ol in other_labels:
        idx = text.find(ol, start)
        if idx != -1 and idx < end:
            end = idx
    return text[start:end]


def check_r2_elements(text: str, facts: dict) -> dict:
    f1 = next(f for f in facts["futures"] if f["id"] == "F1")
    section = find_section(text, f1) or text
    required = ["트렌드", "계획", "심층원동력"]
    optional_image = ["대중", "이미지"]  # both OK
    missing = [r for r in required if r not in section]
    if not any(o in section for o in optional_image):
        missing.append("대중 이미지(키워드 '대중' 또는 '이미지')")
    return {
        "id": "R2",
        "name": "기본미래 4요소 키워드 등장",
        "pass": not missing,
        "missing": missing,
    }


def check_r3_wildcard_subtypes(text: str, facts: dict) -> dict:
    f3 = next(f for f in facts["futures"] if f["id"] == "F3")
    section = find_section(text, f3) or text
    required = ["비약적 진보", "붕괴"]
    missing = [r for r in required if r not in section]
    return {
        "id": "R3",
        "name": "뜻밖의 미래 2종(비약적 진보·붕괴) 키워드 등장",
        "pass": not missing,
        "missing": missing,
    }


def check_r4_probability_hedge(text: str) -> dict:
    """확률 수치 단정 검출 — 단, '확률/가능성' 트리거 또는 미래 라벨이
    근처(±80자)에 있을 때만 단정 위반으로 본다. 책 예시 질문·일반 통계
    수치는 미적용. 위반 시 ±200자 hedge 확보 여부 확인."""
    matches = list(PROBABILITY_PATTERN.finditer(text))
    failures = []
    for m in matches:
        # 근접 80자 안에 확률 트리거 또는 미래 라벨이 있어야 단정으로 간주
        near_start = max(0, m.start() - 80)
        near_end = min(len(text), m.end() + 80)
        near = text[near_start:near_end]
        is_probability_claim = (
            any(t in near for t in PROBABILITY_CLAIM_TRIGGERS)
            and any(l in near for l in FUTURE_LABEL_TRIGGERS)
        )
        if not is_probability_claim:
            continue
        # 단정이라면 ±200자 안에 hedge 표기 필요
        wide_start = max(0, m.start() - 200)
        wide_end = min(len(text), m.end() + 200)
        wide = text[wide_start:wide_end]
        if not any(h in wide for h in HEDGE_TERMS):
            failures.append({
                "value": m.group(0),
                "context": wide.replace("\n", " ").strip(),
            })
    return {
        "id": "R4",
        "name": "확률 수치 단정 사용 금지 (확률·미래라벨 근접 시 해석치 표기 동반)",
        "pass": not failures,
        "violations": failures,
    }


def check_r5_section_headers(text: str, facts: dict, mode: str, focus: str | None) -> dict:
    if mode == "B" and focus:
        focus_id = focus.upper()
        future = next((f for f in facts["futures"] if f["id"] == focus_id), None)
        if not future:
            return {
                "id": "R5",
                "name": "포커스 미래 섹션 존재",
                "pass": False,
                "missing": [f"Unknown focus id: {focus}"],
            }
        ok = has_label(text, future)
        return {
            "id": "R5",
            "name": f"포커스 미래({focus_id}) 섹션 존재",
            "pass": ok,
            "missing": [] if ok else [focus_id],
        }
    # Other modes — all four headers required
    missing = [f["id"] for f in facts["futures"] if not has_label(text, f)]
    return {
        "id": "R5",
        "name": "4개 섹션 헤더 모두 존재",
        "pass": not missing,
        "missing": missing,
    }


def validate(text: str, mode: str = "A", focus: str | None = None) -> dict:
    facts = load_facts()
    results = []
    if mode != "B":
        results.append(check_r1_all_labels(text, facts["futures"]))
        results.append(check_r2_elements(text, facts))
        results.append(check_r3_wildcard_subtypes(text, facts))
    else:
        # 포커스가 F1·F3가 아니면 해당 룰은 건너뜀
        if focus and focus.upper() == "F1":
            results.append(check_r2_elements(text, facts))
        if focus and focus.upper() == "F3":
            results.append(check_r3_wildcard_subtypes(text, facts))
    results.append(check_r4_probability_hedge(text))
    results.append(check_r5_section_headers(text, facts, mode, focus))
    overall = all(r["pass"] for r in results)
    return {"pass": overall, "results": results, "mode": mode, "focus": focus}


def format_report(report: dict) -> str:
    lines = [f"[validate_output] mode={report['mode']} focus={report['focus']}"]
    lines.append(f"OVERALL: {'PASS' if report['pass'] else 'FAIL'}")
    lines.append("")
    for r in report["results"]:
        status = "PASS" if r["pass"] else "FAIL"
        lines.append(f"  [{status}] {r['id']} — {r['name']}")
        if not r["pass"]:
            if "missing" in r and r["missing"]:
                lines.append(f"         missing: {r['missing']}")
            if "violations" in r and r["violations"]:
                for v in r["violations"]:
                    lines.append(f"         violation: {v['value']}")
                    lines.append(f"           context: ...{v['context']}...")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", help="검증할 출력 파일 경로 또는 '-' (stdin)")
    p.add_argument("--mode", default="A", choices=["A", "B", "C", "D"])
    p.add_argument("--focus", default=None)
    p.add_argument("--json", action="store_true", help="JSON 출력")
    args = p.parse_args()

    if args.path == "-":
        text = sys.stdin.read()
    else:
        text = Path(args.path).read_text(encoding="utf-8")

    report = validate(text, mode=args.mode, focus=args.focus)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
