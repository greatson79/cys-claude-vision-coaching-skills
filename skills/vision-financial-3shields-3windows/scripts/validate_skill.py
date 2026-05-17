#!/usr/bin/env python3
"""3방패+3창 스킬의 모델·출처 일관성 검증 CLI.

용도: SKILL.md 응답 생성 전·후 결정론적 검증.
LLM이 모델 번호·명칭·출처 정보를 재추론하지 못하도록 차단한다.

사용:
  python3 validate_skill.py spec
  python3 validate_skill.py shield 1
  python3 validate_skill.py window 2
  python3 validate_skill.py citation C2
  python3 validate_skill.py quote Q3
  python3 validate_skill.py list-shields
  python3 validate_skill.py list-windows
  python3 validate_skill.py list-citations
  python3 validate_skill.py list-quotes
  python3 validate_skill.py principles
  python3 validate_skill.py six-actions
  python3 validate_skill.py check-response  (stdin으로 응답 본문을 받아 핵심 매핑 점검)
"""
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SPEC_PATH = SCRIPT_DIR / "spec_3shields_3windows.json"
CITES_PATH = SCRIPT_DIR / "citations.json"


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def load_cites() -> dict:
    return json.loads(CITES_PATH.read_text(encoding="utf-8"))


def cmd_spec() -> int:
    spec = load_spec()
    print(json.dumps(spec, ensure_ascii=False, indent=2))
    return 0


def cmd_shield(num: str) -> int:
    spec = load_spec()
    try:
        n = int(num)
    except ValueError:
        print(f"ERROR: 방패 번호는 정수여야 합니다 (1·2·3). 입력: {num!r}", file=sys.stderr)
        return 2
    if n not in (1, 2, 3):
        print(f"ERROR: 방패 번호는 1·2·3만 허용됩니다. 입력: {n}", file=sys.stderr)
        return 2
    s = [x for x in spec["shields"] if x["number"] == n][0]
    print(json.dumps(s, ensure_ascii=False, indent=2))
    return 0


def cmd_window(num: str) -> int:
    spec = load_spec()
    try:
        n = int(num)
    except ValueError:
        print(f"ERROR: 창 번호는 정수여야 합니다 (1·2·3). 입력: {num!r}", file=sys.stderr)
        return 2
    if n not in (1, 2, 3):
        print(f"ERROR: 창 번호는 1·2·3만 허용됩니다. 입력: {n}", file=sys.stderr)
        return 2
    w = [x for x in spec["windows"] if x["number"] == n][0]
    print(json.dumps(w, ensure_ascii=False, indent=2))
    return 0


def cmd_citation(cid: str) -> int:
    cites = load_cites()
    if cid not in cites:
        valid = [k for k in cites if not k.startswith("_")]
        print(f"ERROR: citation id {cid!r}을(를) 찾지 못했습니다. 유효한 ID: {valid}", file=sys.stderr)
        return 3
    print(json.dumps(cites[cid], ensure_ascii=False, indent=2))
    return 0


def cmd_quote(qid: str) -> int:
    spec = load_spec()
    quotes = spec["verified_quotes"]
    match = [q for q in quotes if q["id"] == qid]
    if not match:
        valid = [q["id"] for q in quotes]
        print(f"ERROR: quote id {qid!r}을(를) 찾지 못했습니다. 유효한 ID: {valid}", file=sys.stderr)
        return 3
    print(json.dumps(match[0], ensure_ascii=False, indent=2))
    return 0


def cmd_list_shields() -> int:
    spec = load_spec()
    for s in spec["shields"]:
        print(f"방패 {s['number']}: {s['korean_name']} ({s['domain']})")
    return 0


def cmd_list_windows() -> int:
    spec = load_spec()
    for w in spec["windows"]:
        print(f"창 {w['number']}: {w['korean_name']}")
    return 0


def cmd_list_citations() -> int:
    cites = load_cites()
    for k, v in cites.items():
        if k.startswith("_"):
            continue
        print(f"{k}: {v['claim_supported']}")
    return 0


def cmd_list_quotes() -> int:
    spec = load_spec()
    for q in spec["verified_quotes"]:
        print(f"{q['id']}: {q['topic']}")
    return 0


def cmd_principles() -> int:
    spec = load_spec()
    for p in spec["absolute_principles"]:
        print(p)
    return 0


def cmd_six_actions() -> int:
    spec = load_spec()
    for a in spec["doctor_six_actions"]:
        print(a)
    return 0


def cmd_check_response() -> int:
    """stdin으로 받은 응답 텍스트가 핵심 모델 명칭·번호 매핑을 위배하지 않는지 검사."""
    import re as _re
    text = sys.stdin.read()
    if not text.strip():
        print("ERROR: stdin이 비어 있습니다. 응답 본문을 파이프하세요.", file=sys.stderr)
        return 2
    spec = load_spec()
    findings = []

    SHIELD_KEYWORDS = {
        1: ["금융 관련 자산 리모델링", "보험", "연금", "빚"],
        2: ["투자 관련 자산 리모델링", "주식·부동산", "주식", "부동산"],
        3: ["소비 관련 자산 리모델링", "소비 패턴", "소비"],
    }
    WINDOW_KEYWORDS = {
        1: ["소득 효과", "지식 노동", "네트워크 노동", "1% 추가 소득"],
        2: ["좋은 투자 효과", "투자 효과", "7~10%", "복리 투자"],
        3: ["꿈 효과", "마음의 부자", "행복한 부자", "다른 사람을 부자로"],
    }

    def direct_binding(text, label_pattern, kw):
        """label(예: '방패 3') 뒤 직접 바인딩 문맥에서 keyword가 등장하는지 검사.

        ① 'label은/는/이/가/: KW' 패턴 — 같은 명제 안에 있어야 함
        ② 'KW(은/는/이/가) ... label' 역방향 (예: '소비 패턴은 방패 2')
        둘 다 KW와 label 사이 최대 25자 (조사·서술어만 허용).
        """
        kw_re = _re.escape(kw)
        forward = rf"{label_pattern}\s*(?:은|는|이|가|:|=|—|-)?\s*(?:[^\n.,;]{{0,15}}\s)?{kw_re}"
        backward = rf"{kw_re}\s*(?:은|는|이|가|—|-|:|=)?\s*(?:[^\n.,;]{{0,15}}\s)?{label_pattern}"
        return bool(_re.search(forward, text) or _re.search(backward, text))

    for correct_num, kws in SHIELD_KEYWORDS.items():
        for wrong_num in (1, 2, 3):
            if wrong_num == correct_num:
                continue
            label_pat = rf"방패\s*{wrong_num}"
            for kw in kws:
                if direct_binding(text, label_pat, kw):
                    findings.append(
                        f"VIOLATION: '{kw}'은(는) 방패 {correct_num}의 영역인데 본문이 '방패 {wrong_num}'에 직접 바인딩"
                    )

    for correct_num, kws in WINDOW_KEYWORDS.items():
        for wrong_num in (1, 2, 3):
            if wrong_num == correct_num:
                continue
            label_pat = rf"창\s*{wrong_num}"
            for kw in kws:
                if direct_binding(text, label_pat, kw):
                    findings.append(
                        f"VIOLATION: '{kw}'은(는) 창 {correct_num}의 영역인데 본문이 '창 {wrong_num}'에 직접 바인딩"
                    )

    # 2) 절대 원칙 7번 — 박사님 책 인용 명시 여부 (출처 키워드 점검)
    has_source_marker = any(
        kw in text for kw in ["박사님 책", "미래준비학교", "부의 정석", "(SKILL.md", "박사님 책 인용"]
    )
    if not has_source_marker and len(text) > 300:
        findings.append(
            "WARNING: 응답이 300자 이상이지만 박사님 책 출처 표기가 보이지 않습니다 (절대 원칙 7 위반 가능)"
        )

    if findings:
        for f in findings:
            print(f)
        return 1
    print("OK: 모델 매핑·출처 표기에 명시적 위반 없음.")
    return 0


COMMANDS = {
    "spec": (cmd_spec, 0),
    "shield": (cmd_shield, 1),
    "window": (cmd_window, 1),
    "citation": (cmd_citation, 1),
    "quote": (cmd_quote, 1),
    "list-shields": (cmd_list_shields, 0),
    "list-windows": (cmd_list_windows, 0),
    "list-citations": (cmd_list_citations, 0),
    "list-quotes": (cmd_list_quotes, 0),
    "principles": (cmd_principles, 0),
    "six-actions": (cmd_six_actions, 0),
    "check-response": (cmd_check_response, 0),
}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("사용법: validate_skill.py <command> [args...]", file=sys.stderr)
        print(f"  command 목록: {sorted(COMMANDS)}", file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd not in COMMANDS:
        print(f"ERROR: 알 수 없는 command: {cmd!r}", file=sys.stderr)
        print(f"  유효: {sorted(COMMANDS)}", file=sys.stderr)
        return 2
    fn, argc = COMMANDS[cmd]
    args = argv[2:]
    if len(args) != argc:
        print(f"ERROR: {cmd} 는 인자 {argc}개를 받습니다. 입력: {len(args)}개", file=sys.stderr)
        return 2
    return fn(*args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
