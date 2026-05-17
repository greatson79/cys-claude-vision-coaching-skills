#!/usr/bin/env python3
"""
vision-four-futures — 결정론적 사실 조회.

이 스크립트는 LLM 자연어 추론이 환각을 일으킬 수 있는 모든 사실 조회를
파이썬 함수로 결정론 환원한다. SKILL.md는 사실을 직접 진술하지 않고
반드시 이 스크립트를 호출하여 답을 가져온다.

CLI 사용 (모든 명령은 결정론적·항상 동일 결과):
    python3 scripts/lookup.py book                       # 책 메타데이터
    python3 scripts/lookup.py futures                    # 4가지 미래 라벨
    python3 scripts/lookup.py future F1                  # 특정 미래 정의
    python3 scripts/lookup.py elements                   # 기본미래 4요소
    python3 scripts/lookup.py wildcard-subtypes          # 뜻밖의 미래 2종
    python3 scripts/lookup.py wildcard-questions         # 박사님 책 4개 예시 질문
    python3 scripts/lookup.py vision-count               # 비전 3~4개 권장
    python3 scripts/lookup.py vision-mapping             # 비전 후보 매핑
    python3 scripts/lookup.py intersection               # 미래 분기점 정의
    python3 scripts/lookup.py principles                 # 8대 절대 원칙
    python3 scripts/lookup.py input-modes                # A/B/C/D 입력 유형
    python3 scripts/lookup.py quote Q1                   # 인용문 단일 조회
    python3 scripts/lookup.py quotes                     # 전체 인용 목록
    python3 scripts/lookup.py source S1                  # 외부 학술 출처
    python3 scripts/lookup.py sources                    # 학술 출처 목록
    python3 scripts/lookup.py probability F1             # 확률 표기 가이드
    python3 scripts/lookup.py json                       # 전체 fact JSON (raw)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ASSETS = Path(__file__).resolve().parent.parent / "assets"


def load_facts() -> dict:
    return json.loads((ASSETS / "facts.json").read_text(encoding="utf-8"))


def load_citations() -> dict:
    return json.loads((ASSETS / "citations.json").read_text(encoding="utf-8"))


def load_sources() -> dict:
    return json.loads((ASSETS / "external_sources.json").read_text(encoding="utf-8"))


def find_future(facts: dict, fid: str) -> dict:
    fid_norm = fid.upper()
    for f in facts["futures"]:
        if f["id"] == fid_norm:
            return f
    raise KeyError(f"Unknown future id: {fid}. Valid: F1, F2, F3, F4")


def find_quote(citations: dict, qid: str) -> dict:
    qid_norm = qid.upper()
    for q in citations["citations"]:
        if q["id"] == qid_norm:
            return q
    raise KeyError(f"Unknown quote id: {qid}. Valid: Q1..Q12")


def find_source(sources: dict, sid: str) -> dict:
    sid_norm = sid.upper()
    for s in sources["sources"]:
        if s["id"] == sid_norm:
            return s
    raise KeyError(f"Unknown source id: {sid}. Valid: S1..S6")


def cmd_book() -> str:
    f = load_facts()["book"]
    lines = [
        f"제목: {f['title_ko']}",
        f"부제: {f['title_subtitle_ko']}",
        f"저자: {' · '.join(f['authors'])}",
        f"출판사: {f['publisher']}",
        f"출판년: {f['year']}",
        f"쪽수: {f['pages']}",
        f"ISBN-13: {f['isbn13']}",
        f"실존 검증: {'완료' if f['existence_verified'] else '미완료'}",
        f"검증 출처: {', '.join(f['existence_sources'])}",
        f"온라인 전문 공개: {'예' if f['online_full_text_available'] else '아니오'}",
        f"인용 검증 한계: {f['quote_verification_caveat']}",
    ]
    return "\n".join(lines)


def cmd_futures() -> str:
    facts = load_facts()
    lines = ["[박사님 4가지 미래 — 결정론적 사실]\n"]
    for f in facts["futures"]:
        lines.append(f"{f['id']}: {f['korean_label']} = {f['english_label']}")
        if f.get("synonyms_english"):
            lines.append(f"    영어 동의어: {', '.join(f['synonyms_english'])}")
    return "\n".join(lines)


def cmd_future(fid: str) -> str:
    facts = load_facts()
    f = find_future(facts, fid)
    lines = [
        f"[{f['id']}] {f['korean_label']} ({f['english_label']})",
        f"영어 동의어: {', '.join(f.get('synonyms_english', []))}",
        f"책 정의(요지): {f['probability_band_book_verbatim']}",
        f"확률 수치 책 명시 여부: {'명시' if f['probability_quant_in_book'] else '미명시'}",
        f"확률 해석 가이드: {f['probability_quant_interpretation']}",
    ]
    if "elements" in f:
        lines.append("4요소:")
        for el in f["elements"]:
            lines.append(f"  {el['order']}. {el['korean']} — {el['note']}")
        lines.append(f"요소 포함 이유(책 명시 여부): {'명시' if f.get('rationale_in_book') else '미명시'}")
        if not f.get("rationale_in_book"):
            lines.append(f"  → 응답 템플릿: {f['rationale_response_template']}")
    if "purpose" in f:
        lines.append("용도:")
        for p in f["purpose"]:
            lines.append(f"  · {p}")
    if "subtypes" in f:
        lines.append(f"하위 {f['subtypes_count']}종:")
        for s in f["subtypes"]:
            v = "" if s["english_label_in_book_verified"] else " ⚠ 원서 표기 미검증"
            lines.append(f"  {s['order']}. {s['korean']} (스킬 표기: {s['english_label_in_skill']}){v}")
            lines.append(f"     책 예시: {s.get('example_from_book') or s.get('example_from_book_2016')}")
            lines.append(f"     주의: {s['example_caveat']}")
        lines.append(f"핵심 원칙: {f['key_principle']}")
        lines.append("박사님 책 예시 질문 4가지:")
        for q in f["key_questions_from_book"]:
            lines.append(f"  - {q}")
        lines.append(f"두 명칭 병용 근거: {f.get('dual_naming_evidence')}")
    if "diagram_position" in f:
        lines.append(f"다이어그램 위치: {f['diagram_position']}")
        lines.append(f"비전 연계: {f['vision_linkage']}")
    return "\n".join(lines)


def cmd_elements() -> str:
    f = find_future(load_facts(), "F1")
    out = [f"기본미래 4요소 — 박사님 책 정의 (총 {f['elements_count']}개):"]
    for el in f["elements"]:
        out.append(f"  {el['order']}. {el['korean']} — {el['note']}")
    out.append("")
    out.append(f"요소별 '왜 이 요소인가'에 대한 책 명시: "
               f"{'있음' if f.get('rationale_in_book') else '없음'}")
    out.append(f"→ '왜' 질문 표준 응답: {f['rationale_response_template']}")
    return "\n".join(out)


def cmd_wildcard_subtypes() -> str:
    f = find_future(load_facts(), "F3")
    out = ["뜻밖의 미래 하위 2종 — 박사님 책 정의:"]
    for s in f["subtypes"]:
        out.append("")
        out.append(f"  {s['order']}. {s['korean']}")
        out.append(f"     스킬 영어 표기: {s['english_label_in_skill']}")
        out.append(f"     원서 영어 표기 검증: "
                   f"{'예' if s['english_label_in_book_verified'] else '미확인'}"
                   f" — {s['english_label_verification_note']}")
        out.append(f"     박사님 책 예시: "
                   f"{s.get('example_from_book') or s.get('example_from_book_2016')}")
        out.append(f"     주의: {s['example_caveat']}")
    out.append("")
    out.append(f"핵심 원칙: {f['key_principle']}")
    return "\n".join(out)


def cmd_wildcard_questions() -> str:
    f = find_future(load_facts(), "F3")
    out = ["박사님 책 뜻밖의 미래 예시 질문 (책 직접 인용):"]
    for q in f["key_questions_from_book"]:
        out.append(f"  - {q}")
    return "\n".join(out)


def cmd_vision_count() -> str:
    f = load_facts()["vision_count_recommended"]
    out = [
        f"박사님 권장 비전 개수: {f['value']}",
        f"책 명시 여부: {'예' if f['in_book'] else '아니오'}",
        "이유:",
    ]
    for r in f["reasons"]:
        out.append(f"  · {r}")
    out.append(f"실행 방식: {f['deployment']}")
    return "\n".join(out)


def cmd_vision_mapping() -> str:
    facts = load_facts()
    out = ["비전 후보 → 4가지 미래 매핑 (박사님 책 다이어그램):"]
    by_id = {f["id"]: f for f in facts["futures"]}
    for m in facts["vision_candidate_mapping"]:
        future = by_id[m["matches_future"]]
        out.append(
            f"  · {m['source']} → {m['target_label']} "
            f"= {future['korean_label']} ({future['english_label']})"
        )
    return "\n".join(out)


def cmd_intersection() -> str:
    fi = load_facts()["futures_intersection"]
    return (
        f"미래 분기점 ({fi['english_label_in_skill']}) — "
        f"원서 영어 표기 검증: "
        f"{'예' if fi['english_label_in_book_verified'] else '미확인'}\n"
        f"정의: {fi['definition']}\n"
        f"분기점 이전: {fi['strategy_split']['before']}\n"
        f"분기점 이후: {fi['strategy_split']['after']}"
    )


def cmd_principles() -> str:
    out = ["박사님 책 충실 — 8대 절대 원칙:"]
    for i, p in enumerate(load_facts()["absolute_principles"], 1):
        out.append(f"  {i}. {p}")
    return "\n".join(out)


def cmd_input_modes() -> str:
    out = ["입력 처리 4유형 (사용자 요청 분기):"]
    for m in load_facts()["input_modes"]:
        out.append(f"  {m['code']}: {m['name']} — {m['description']}")
    return "\n".join(out)


def cmd_quote(qid: str) -> str:
    q = find_quote(load_citations(), qid)
    out = [
        f"[{q['id']}] {q['context']}",
        f"  본문: > \"{q['text_ko']}\"",
        f"  출처: {q['source_book']}",
        f"  Provenance: {q['provenance_status']}",
    ]
    if q.get("provenance_note"):
        out.append(f"  Provenance 주석: {q['provenance_note']}")
    if q.get("external_alignment"):
        out.append(f"  외부 학술 정렬: {q['external_alignment']}")
    return "\n".join(out)


def cmd_quotes() -> str:
    out = ["박사님 책 인용 12개 (Provenance 표기 포함):"]
    for q in load_citations()["citations"]:
        out.append(f"  {q['id']} — {q['context']} [{q['provenance_status']}]")
    out.append("")
    out.append("주의: 모든 인용의 provenance가 'unverifiable_online'인 이유는 "
               "책 전문이 온라인에 공개되지 않기 때문이다. 인용 출력 시 "
               "사용자에게 '실물 원서 직접 확인 권장'을 안내한다.")
    return "\n".join(out)


def cmd_source(sid: str) -> str:
    s = find_source(load_sources(), sid)
    out = [
        f"[{s['id']}] {s.get('author') or s.get('publisher')}, "
        f"{s.get('year') or ''}",
        f"  제목: {s['title']}",
    ]
    if s.get("venue"):
        out.append(f"  Venue: {s['venue']}")
    if s.get("publisher"):
        out.append(f"  출판: {s['publisher']}")
    if s.get("contribution_to_four_futures"):
        out.append(f"  4가지 미래에 대한 기여: {s['contribution_to_four_futures']}")
    if s.get("predecessor_definition"):
        out.append(f"  선행 정의: {s['predecessor_definition']}")
    out.append(f"  검증일: {s.get('verification_date', 'N/A')}")
    if s.get("evidence_url"):
        out.append(f"  Evidence: {s['evidence_url']}")
    if s.get("evidence_urls"):
        out.append("  Evidence URLs:")
        for u in s["evidence_urls"]:
            out.append(f"    - {u}")
    return "\n".join(out)


def cmd_sources() -> str:
    out = ["외부 학술 출처 (검증 완료):"]
    for s in load_sources()["sources"]:
        head = s.get("author") or s.get("publisher")
        year = s.get("year") or ""
        out.append(f"  {s['id']}: {head} ({year}) — {s['title']}")
    return "\n".join(out)


def cmd_probability(fid: str) -> str:
    """확률 표기 가이드 — 단정 금지·해석치 표기."""
    f = find_future(load_facts(), fid)
    out = [
        f"[{f['id']}] {f['korean_label']} 확률 표기 가이드",
        f"  책 본문 요지: {f['probability_band_book_verbatim']}",
        f"  책에 수치 명시 여부: "
        f"{'명시' if f['probability_quant_in_book'] else '미명시'}",
        f"  해석/통용치: {f['probability_quant_interpretation']}",
        "",
        "  ⛔ 출력 시 금지 패턴 — '박사님 책은 70~80%로 명시한다' 같은 단정.",
        "  ✅ 출력 시 허용 패턴 — '책 본문에는 수치가 명시되지 않으며, "
        "스킬 외부 해석으로 51% 이상(대개 70~80%)이 통용됩니다 (해석치).'",
    ]
    return "\n".join(out)


def cmd_json() -> str:
    return json.dumps({
        "facts": load_facts(),
        "citations": load_citations(),
        "external_sources": load_sources(),
    }, ensure_ascii=False, indent=2)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    arg = argv[2] if len(argv) > 2 else None
    try:
        if cmd == "book":
            print(cmd_book())
        elif cmd == "futures":
            print(cmd_futures())
        elif cmd == "future":
            print(cmd_future(arg or "F1"))
        elif cmd == "elements":
            print(cmd_elements())
        elif cmd == "wildcard-subtypes":
            print(cmd_wildcard_subtypes())
        elif cmd == "wildcard-questions":
            print(cmd_wildcard_questions())
        elif cmd == "vision-count":
            print(cmd_vision_count())
        elif cmd == "vision-mapping":
            print(cmd_vision_mapping())
        elif cmd == "intersection":
            print(cmd_intersection())
        elif cmd == "principles":
            print(cmd_principles())
        elif cmd == "input-modes":
            print(cmd_input_modes())
        elif cmd == "quote":
            print(cmd_quote(arg or "Q1"))
        elif cmd == "quotes":
            print(cmd_quotes())
        elif cmd == "source":
            print(cmd_source(arg or "S1"))
        elif cmd == "sources":
            print(cmd_sources())
        elif cmd == "probability":
            print(cmd_probability(arg or "F1"))
        elif cmd == "json":
            print(cmd_json())
        else:
            print(f"ERROR: unknown command '{cmd}'", file=sys.stderr)
            print(__doc__)
            return 2
        return 0
    except (KeyError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
