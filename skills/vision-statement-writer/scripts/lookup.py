#!/usr/bin/env python3
"""vision-statement-writer 결정론적 사실 조회.

이 스크립트는 LLM 자연어 추론이 할루시네이션을 일으킬 수 있는 모든
사실 조회를 파이썬 함수로 결정론 환원한다. SKILL.md는 사실(책 메타,
12개 필드, 검증 도구, 교차 스킬 목록, 인용)을 직접 진술하지 않고
반드시 본 스크립트를 호출하여 답을 가져온다.

CLI 사용 (모든 명령은 결정론적·항상 동일 결과):
    python3 scripts/lookup.py book                       # 책 메타데이터
    python3 scripts/lookup.py author                     # 저자 신원
    python3 scripts/lookup.py fields                     # 12필드 목록(요약)
    python3 scripts/lookup.py field F1_name              # 단일 필드 상세
    python3 scripts/lookup.py questions                  # 12개 코칭 질문
    python3 scripts/lookup.py tools                      # 검증 도구 V1-V3
    python3 scripts/lookup.py tool V1                    # 검증 도구 단건
    python3 scripts/lookup.py excluded-tools             # 제외된 검증 도구(예: 5대 공리)
    python3 scripts/lookup.py preceding-skills           # 선행 권장 스킬 11개
    python3 scripts/lookup.py subsequent-skills          # 후속 스킬 5개
    python3 scripts/lookup.py input-modes                # A/B/C/D 모드
    python3 scripts/lookup.py multiple-intelligences     # 9 MI 분류
    python3 scripts/lookup.py principles                 # 12개 절대 원칙
    python3 scripts/lookup.py quote Q1                   # 단일 인용
    python3 scripts/lookup.py quotes                     # 전체 인용
    python3 scripts/lookup.py source MI1                 # 외부 출처 단건
    python3 scripts/lookup.py sources                    # 외부 출처 목록
    python3 scripts/lookup.py json                       # 전체 facts JSON raw
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def load(name: str) -> dict:
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def find_field(facts: dict, fid: str) -> dict:
    for f in facts["vision_statement_form"]["fields"]:
        if f["id"] == fid:
            return f
    raise KeyError(
        f"Unknown field id: {fid}. Valid: "
        f"{', '.join(x['id'] for x in facts['vision_statement_form']['fields'])}"
    )


def find_tool(facts: dict, tid: str) -> dict:
    for t in facts["validation_tools"]:
        if t["id"] == tid.upper():
            return t
    raise KeyError(
        f"Unknown tool id: {tid}. Valid: "
        f"{', '.join(t['id'] for t in facts['validation_tools'])}"
    )


def find_quote(citations: dict, qid: str) -> dict:
    for q in citations["citations"]:
        if q["id"] == qid.upper():
            return q
    raise KeyError(
        f"Unknown quote id: {qid}. Valid: "
        f"{', '.join(q['id'] for q in citations['citations'])}"
    )


def find_source(sources: dict, sid: str) -> dict:
    for s in sources["sources"]:
        if s["id"] == sid.upper():
            return s
    raise KeyError(
        f"Unknown source id: {sid}. Valid: "
        f"{', '.join(s['id'] for s in sources['sources'])}"
    )


def cmd_book() -> str:
    b = load("facts.json")["book"]
    lines = [
        f"제목: {b['title_ko']}",
        f"부제: {b['title_subtitle_ko']}",
        f"저자: {' · '.join(b['authors'])}",
        f"출판사: {b['publisher']}",
        f"출간년도: {b['year']}",
        f"쪽수: {b['pages']}",
        f"ISBN: {b['isbn13']}",
        f"실존 검증: {b['existence_verified']}",
        f"검증 출처: {', '.join(b['existence_sources'])}",
        f"온라인 전문 공개: {b['online_full_text_available']}",
        f"인용 대조 주의: {b['quote_verification_caveat']}",
        f"양식 주의: {b['form_template_caveat']}",
    ]
    return "\n".join(lines)


def cmd_author() -> str:
    a = load("facts.json")["author_credentials"]
    lines = [
        f"성함: {a['name']}",
        f"학위: {a['degree']}",
        f"소속: {a['affiliation']}",
        f"검증 출처: {', '.join(a['verification_sources'])}",
        f"주요 저서: {', '.join(a['major_works'])}",
    ]
    return "\n".join(lines)


def cmd_fields() -> str:
    fields = load("facts.json")["vision_statement_form"]["fields"]
    out = [f"양식 빈칸 항목 수: {len(fields)}", ""]
    for f in fields:
        label_en = f" ({f['label_en']})" if f.get("label_en") else ""
        out.append(f"{f['order']:2d}. {f['id']:<14} {f['label_ko']}{label_en}")
    return "\n".join(out)


def cmd_field(fid: str) -> str:
    f = find_field(load("facts.json"), fid)
    out = [
        f"ID: {f['id']}",
        f"순서: {f['order']}",
        f"한글 라벨: {f['label_ko']}",
    ]
    if f.get("label_en"):
        out.append(f"영문 라벨: {f['label_en']}")
    out.append(f"양식 문구: {f['form_phrase']}")
    out.append(f"필수: {f['required']}")
    out.append(f"타입: {f['type']}")
    if f.get("min_chars") is not None:
        out.append(f"최소 글자: {f['min_chars']}")
    if f.get("max_chars") is not None:
        out.append(f"최대 글자: {f['max_chars']}")
    if f.get("min_items") is not None:
        out.append(f"최소 항목: {f['min_items']}")
    if f.get("max_items") is not None:
        out.append(f"최대 항목: {f['max_items']}")
    if f.get("recommended_items") is not None:
        out.append(f"권장 항목 수: {f['recommended_items']}")
    if f.get("linked_skill"):
        out.append(f"연동 스킬: {f['linked_skill']}")
    out.append(f"질문: {f['question']}")
    if f.get("date_format_regex_extended"):
        out.append(f"날짜 정규식: {f['date_format_regex_extended']}")
    return "\n".join(out)


def cmd_questions() -> str:
    fields = load("facts.json")["vision_statement_form"]["fields"]
    out = []
    for f in fields:
        out.append(f"Q{f['order']} [{f['id']}]: {f['question']}")
    return "\n".join(out)


def cmd_tools() -> str:
    tools = load("facts.json")["validation_tools"]
    out = []
    for t in tools:
        out.append(f"[{t['id']}] {t['name_ko']} — 출처: {t['source_skill']}")
        for c in t["criteria"]:
            out.append(f"   · {c}")
        out.append(f"   합격 규칙: {t['pass_rule']}")
        out.append("")
    return "\n".join(out).rstrip()


def cmd_tool(tid: str) -> str:
    t = find_tool(load("facts.json"), tid)
    out = [
        f"ID: {t['id']}",
        f"이름: {t['name_ko']}",
        f"출처 스킬: {t['source_skill']}",
        "기준:",
    ]
    for c in t["criteria"]:
        out.append(f"   · {c}")
    out.append(f"합격 규칙: {t['pass_rule']}")
    return "\n".join(out)


def cmd_excluded_tools() -> str:
    excluded = load("facts.json").get("excluded_validation_tools_with_reason", [])
    if not excluded:
        return "(없음)"
    out = []
    for e in excluded:
        out.append(f"제외: {e['name']}")
        out.append(f"   사유: {e['exclusion_reason']}")
    return "\n".join(out)


def cmd_preceding() -> str:
    skills = load("facts.json")["preceding_skills"]
    out = [f"선행 권장 스킬 ({len(skills)}개):"]
    for s in skills:
        out.append(f"  {s['order']:2d}. {s['skill']} — {s['purpose']}")
    return "\n".join(out)


def cmd_subsequent() -> str:
    skills = load("facts.json")["subsequent_skills"]
    out = [f"후속 스킬 ({len(skills)}개):"]
    for s in skills:
        out.append(f"  · {s['skill']} — {s['purpose']}")
    return "\n".join(out)


def cmd_input_modes() -> str:
    modes = load("facts.json")["input_modes"]
    out = []
    for m in modes:
        default = " (기본)" if m["is_default"] else ""
        out.append(f"[{m['id']}] {m['korean']} ({m['english']}){default}")
        out.append(f"    {m['description']}")
    return "\n".join(out)


def cmd_mi() -> str:
    mi = load("facts.json")["multiple_intelligences_canonical"]
    out = [
        f"출처 스킬: {mi['source_skill']}",
        f"외부 출처 ID: {', '.join(mi['external_source_ids_in_external_sources_json'])}",
        f"분류 수: {mi['count_in_skill']}",
        "지능 분류:",
    ]
    for c in mi["categories"]:
        out.append(f"  · {c}")
    out.append(f"명명 주의: {mi['naming_caveat']}")
    return "\n".join(out)


def cmd_principles() -> str:
    ps = load("facts.json")["absolute_principles"]
    out = [f"절대 원칙 ({len(ps)}개):"]
    for i, p in enumerate(ps, 1):
        out.append(f"  {i:2d}. {p}")
    return "\n".join(out)


def cmd_quote(qid: str) -> str:
    q = find_quote(load("citations.json"), qid)
    out = [
        f"ID: {q['id']}",
        f"본문: {q['text_ko']}",
        f"출처: {q['source_book']}",
        f"검증 상태: {q['provenance_status']}",
        f"스킬 내 역할: {q['function_in_skill']}",
    ]
    if q.get("verified_by_sister_skill"):
        out.append(f"형제 스킬 검증: {q['verified_by_sister_skill']}")
    return "\n".join(out)


def cmd_quotes() -> str:
    c = load("citations.json")
    out = [f"전체 인용 ({len(c['citations'])}개):"]
    for q in c["citations"]:
        sib = (
            f" (검증: {q['verified_by_sister_skill']})"
            if q.get("verified_by_sister_skill")
            else ""
        )
        out.append(f"  [{q['id']}] {q['text_ko'][:60]}…{sib}")
    return "\n".join(out)


def cmd_source(sid: str) -> str:
    s = find_source(load("external_sources.json"), sid)
    out = [
        f"ID: {s['id']}",
        f"영역: {s['domain']}",
        f"저자: {s['author']}",
        f"연도: {s['year']}",
        f"제목: {s['title']}",
    ]
    if s.get("publisher"):
        out.append(f"출판: {s['publisher']}")
    if s.get("journal"):
        out.append(f"학술지: {s['journal']} {s.get('volume', '')}")
    if s.get("isbn13"):
        out.append(f"ISBN: {s['isbn13']}")
    out.append(f"주장: {s['claim']}")
    out.append(f"검증 상태: {s['verification_status']}")
    return "\n".join(out)


def cmd_sources() -> str:
    src = load("external_sources.json")["sources"]
    out = [f"외부 학술 출처 ({len(src)}개):"]
    for s in src:
        out.append(f"  [{s['id']}] {s['author']} ({s['year']}) — {s['title']}")
    return "\n".join(out)


def cmd_json() -> str:
    return json.dumps(
        {
            "facts": load("facts.json"),
            "citations": load("citations.json"),
            "external_sources": load("external_sources.json"),
        },
        ensure_ascii=False,
        indent=2,
    )


DISPATCH = {
    "book": cmd_book,
    "author": cmd_author,
    "fields": cmd_fields,
    "questions": cmd_questions,
    "tools": cmd_tools,
    "excluded-tools": cmd_excluded_tools,
    "preceding-skills": cmd_preceding,
    "subsequent-skills": cmd_subsequent,
    "input-modes": cmd_input_modes,
    "multiple-intelligences": cmd_mi,
    "principles": cmd_principles,
    "quotes": cmd_quotes,
    "sources": cmd_sources,
    "json": cmd_json,
}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        if cmd in DISPATCH:
            print(DISPATCH[cmd]())
        elif cmd == "field":
            if not arg:
                print("ERROR: field <ID> 필요", file=sys.stderr)
                return 2
            print(cmd_field(arg))
        elif cmd == "tool":
            if not arg:
                print("ERROR: tool <ID> 필요", file=sys.stderr)
                return 2
            print(cmd_tool(arg))
        elif cmd == "quote":
            if not arg:
                print("ERROR: quote <ID> 필요", file=sys.stderr)
                return 2
            print(cmd_quote(arg))
        elif cmd == "source":
            if not arg:
                print("ERROR: source <ID> 필요", file=sys.stderr)
                return 2
            print(cmd_source(arg))
        else:
            print(f"ERROR: unknown command {cmd}", file=sys.stderr)
            print(__doc__, file=sys.stderr)
            return 2
    except KeyError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
