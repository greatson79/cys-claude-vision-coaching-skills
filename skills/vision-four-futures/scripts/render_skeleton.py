#!/usr/bin/env python3
"""
vision-four-futures — 출력 골격 렌더러.

LLM이 4가지 미래 시나리오를 작성하기 전에, 본 스크립트로 결정론적인
출력 골격을 먼저 받아 그 안을 사용자 콘텐츠로 채운다. 박사님 정의·인용·
4요소·2종 wildcard 라벨 등은 모두 facts.json에서 기계적으로 가져오므로
LLM이 라벨·정의·인용을 자유 재진술하지 않도록 차단한다.

CLI:
    python3 scripts/render_skeleton.py --mode A
    python3 scripts/render_skeleton.py --mode B --focus F3
    python3 scripts/render_skeleton.py --mode C
    python3 scripts/render_skeleton.py --mode D

모드:
    A — 4가지 미래 풀 작성 (기본)
    B — 한 미래만 깊이 (--focus F1|F2|F3|F4 필수)
    C — 기존 미래지도에 4분류 매핑
    D — 박사님 본인 AGI 시대 4가지 미래
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ASSETS = Path(__file__).resolve().parent.parent / "assets"


def load(name: str) -> dict:
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def book_header(facts: dict) -> str:
    b = facts["book"]
    return (
        f"> 출처: 『{b['title_ko']}』({b['year']}, {b['publisher']}, "
        f"ISBN {b['isbn13']}) — 저자 {' · '.join(b['authors'])}.\n"
        f"> 인용 검증: 책 전문이 온라인에 공개되지 않아 본 스킬 인용은 "
        f"실물 원서를 직접 참조한 발췌로 가정한다. 사용자에게 인용을 "
        f"전달할 때는 실물 원서 확인을 권장한다."
    )


def render_future_card(f: dict, citations: dict) -> str:
    """단일 미래의 결정론적 골격 — 라벨·정의·요소·예시·확률 가이드."""
    lines = []
    lines.append(f"## {f['id']} — {f['korean_label']} ({f['english_label']})")
    if f.get("synonyms_english"):
        lines.append(f"_영어 동의어: {', '.join(f['synonyms_english'])}_")
    lines.append("")
    lines.append("**박사님 책 정의 (요지):**")
    lines.append(f"> {f['probability_band_book_verbatim']}")
    lines.append("")
    lines.append(
        f"**확률 표기 가이드:** 책 수치 명시 여부는 "
        f"{'**명시**' if f['probability_quant_in_book'] else '**미명시**'}. "
        f"{f['probability_quant_interpretation']}"
    )
    if "elements" in f:
        lines.append("")
        lines.append("**4요소 (박사님 책 정의 그대로):**")
        for el in f["elements"]:
            lines.append(f"  {el['order']}. **{el['korean']}** — {el['note']}")
        if not f.get("rationale_in_book"):
            lines.append("")
            lines.append(f"_왜 이 4요소인가의 책 명시 없음 — {f['rationale_response_template']}_")
    if "purpose" in f:
        lines.append("")
        lines.append("**용도:**")
        for p in f["purpose"]:
            lines.append(f"  · {p}")
    if "subtypes" in f:
        lines.append("")
        lines.append(f"**하위 {f['subtypes_count']}종 (박사님 책 정의 그대로):**")
        for s in f["subtypes"]:
            tag = "" if s["english_label_in_book_verified"] else " _⚠ 스킬 표기, 원서 영어 표기 미검증_"
            lines.append(
                f"  {s['order']}. **{s['korean']}** (스킬 표기: "
                f"_{s['english_label_in_skill']}_){tag}"
            )
            lines.append(
                f"     박사님 책 예시: "
                f"{s.get('example_from_book') or s.get('example_from_book_2016')}"
            )
            lines.append(f"     주의: {s['example_caveat']}")
        lines.append("")
        lines.append(f"**핵심 원칙:** {f['key_principle']}")
        lines.append("")
        lines.append("**박사님 책 예시 질문 4가지:**")
        for q in f["key_questions_from_book"]:
            lines.append(f"  - {q}")
    if "diagram_position" in f:
        lines.append("")
        lines.append(f"**다이어그램 위치:** {f['diagram_position']}")
        lines.append(f"**비전 연계:** {f['vision_linkage']}")
    lines.append("")
    lines.append(f"### [{f['id']}] 사용자 비전 영역 시나리오")
    if f["id"] == "F1":
        lines.append("_LLM이 채울 영역 — 4요소(트렌드·계획·심층원동력·대중 이미지)를 모두 포함한 한 문단._")
    elif f["id"] == "F2":
        lines.append("_LLM이 채울 영역 — 2~3개 시나리오 (기본미래 변형·확장)._")
    elif f["id"] == "F3":
        lines.append("_LLM이 채울 영역 — 비약적 진보 1~2개 + 붕괴 1~2개. 시기 예측 X, 영향력 O._")
    elif f["id"] == "F4":
        lines.append("_LLM이 채울 영역 — 사용자가 *원하는* 비전 미래 한 문단._")
    lines.append("")
    return "\n".join(lines)


def render_full(facts: dict, citations: dict) -> str:
    lines = []
    lines.append("# 4가지 미래 가능성 — 사용자 비전 영역 적용")
    lines.append("")
    lines.append(book_header(facts))
    lines.append("")
    lines.append("---")
    lines.append("")
    for f in facts["futures"]:
        lines.append(render_future_card(f, citations))
        lines.append("---")
        lines.append("")
    # 비전 후보 매핑
    lines.append("## 비전 가능성 영역 3~4개 도출")
    lines.append("")
    vc = facts["vision_count_recommended"]
    lines.append(f"박사님 권장 — **{vc['value']} 비전 동시 추구**.")
    for r in vc["reasons"]:
        lines.append(f"  · {r}")
    lines.append("")
    lines.append("**비전 후보 매핑 (박사님 책 다이어그램):**")
    by_id = {f["id"]: f for f in facts["futures"]}
    for m in facts["vision_candidate_mapping"]:
        future = by_id[m["matches_future"]]
        lines.append(
            f"  · {m['source']} → **{m['target_label']}** "
            f"({future['korean_label']} · {future['english_label']})"
        )
    lines.append("")
    lines.append("### 사용자 비전 후보 3~4개")
    lines.append("_LLM이 채울 영역 — 위 매핑을 따라 사용자 콘텐츠로 3~4개 비전 도출._")
    lines.append("")
    lines.append("---")
    lines.append("")
    # 미래 분기점
    fi = facts["futures_intersection"]
    lines.append(f"## 미래 분기점 ({fi['english_label_in_skill']})")
    lines.append("")
    lines.append(f"**정의:** {fi['definition']}")
    lines.append(f"  · 분기점 **이전**: {fi['strategy_split']['before']}")
    lines.append(f"  · 분기점 **이후**: {fi['strategy_split']['after']}")
    lines.append("")
    lines.append("### 사용자 분기점 분석")
    lines.append("_LLM이 채울 영역 — (1) 시간축 배치, (2) F1→F2 전환 촉발 외부 변수, "
                 "(3) F3 전조 신호, (4) 공통 전략 3~5개, (5) 미래별 차별 전략 1~2개씩._")
    lines.append("")
    lines.append("---")
    lines.append("")
    # 8대 원칙
    lines.append("## 박사님 책 충실 — 8대 절대 원칙")
    for i, p in enumerate(facts["absolute_principles"], 1):
        lines.append(f"  {i}. {p}")
    lines.append("")
    # 마무리 인용
    q10 = next(q for q in citations["citations"] if q["id"] == "Q10")
    lines.append("---")
    lines.append("")
    lines.append("## 마무리 인용")
    lines.append(f"> *\"{q10['text_ko']}\"*")
    lines.append(f"> — {q10['source_book']} ({q10['provenance_status']})")
    return "\n".join(lines)


def render_focus(facts: dict, citations: dict, focus_id: str) -> str:
    f = next((x for x in facts["futures"] if x["id"] == focus_id.upper()), None)
    if not f:
        return f"ERROR: unknown focus id {focus_id}"
    lines = []
    lines.append(f"# {f['korean_label']} ({f['english_label']}) — 심층 탐색")
    lines.append("")
    lines.append(book_header(facts))
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(render_future_card(f, citations))
    lines.append("---")
    lines.append("")
    lines.append("## 박사님 책 충실 — 8대 절대 원칙")
    for i, p in enumerate(facts["absolute_principles"], 1):
        lines.append(f"  {i}. {p}")
    return "\n".join(lines)


def render_mode_c(facts: dict, citations: dict) -> str:
    """모드 C — 사용자 기존 시나리오에 4가지 분류를 매핑하기 위한 골격."""
    lines = []
    lines.append("# 기존 미래지도 → 4가지 분류 매핑")
    lines.append("")
    lines.append(book_header(facts))
    lines.append("")
    lines.append("## 1) 사용자 기존 시나리오 입력 (LLM 정리)")
    lines.append("_LLM이 채울 영역 — 사용자 시나리오를 N개 묶음으로 정리._")
    lines.append("")
    lines.append("## 2) 각 시나리오 → 4가지 미래 매핑")
    lines.append("표 형식:")
    lines.append("")
    lines.append("| 시나리오 | 분류 | 근거 |")
    lines.append("|---|---|---|")
    lines.append("| (사용자 시나리오 1) | F? | (분류 근거 — 박사님 정의 인용) |")
    lines.append("| ... | ... | ... |")
    lines.append("")
    lines.append("## 3) 4가지 미래 라벨 정의 (결정론적)")
    for f in facts["futures"]:
        lines.append(
            f"- **{f['id']} {f['korean_label']} ({f['english_label']})**: "
            f"{f['probability_band_book_verbatim']}"
        )
    lines.append("")
    lines.append("## 4) 누락된 미래 보강 제안")
    lines.append("_LLM이 채울 영역 — 사용자 시나리오에서 비어 있는 미래 유형 보강._")
    return "\n".join(lines)


def render_mode_d(facts: dict, citations: dict) -> str:
    """모드 D — 박사님 본인 AGI 시대 4가지 미래."""
    txt = render_full(facts, citations)
    intro = (
        "# 박사님 미래학자 본업 — AGI 시대 4가지 미래\n\n"
        "_본 모드는 박사님의 미래학자 본업 입력에 맞춰 AGI 시대 한국·세계의 "
        "4가지 미래 가능성을 박사님 책 프레임워크로 펼친다. 4단계 작성은 박사님의 "
        "실시간 통찰을 LLM이 받아 채운다 — 골격(라벨·정의·요소)은 결정론적이다._\n\n"
        "---\n\n"
    )
    return intro + txt


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="A", choices=["A", "B", "C", "D"])
    p.add_argument("--focus", default=None)
    args = p.parse_args()

    facts = load("facts.json")
    citations = load("citations.json")

    if args.mode == "A":
        print(render_full(facts, citations))
    elif args.mode == "B":
        if not args.focus:
            print("ERROR: --focus required for mode B (F1|F2|F3|F4)", file=sys.stderr)
            return 2
        print(render_focus(facts, citations, args.focus))
    elif args.mode == "C":
        print(render_mode_c(facts, citations))
    elif args.mode == "D":
        print(render_mode_d(facts, citations))
    return 0


if __name__ == "__main__":
    sys.exit(main())
