#!/usr/bin/env python3
"""vision-statement-writer 결정론적 양식 렌더러.

LLM이 박사님 비전 선언문 양식을 자유 재진술하지 않도록, 양식 골격
(빈칸 12개·문구·결문)을 본 스크립트가 결정론적으로 출력한다.
사용자 답변은 JSON으로 받아 빈칸을 채운다.

CLI 사용:
    python3 scripts/render_template.py --mode C
        : 빈 양식만 출력 (혼자 작성용)

    python3 scripts/render_template.py --mode A --questions
        : 12개 코칭 질문 결정론적 출력

    python3 scripts/render_template.py --mode B --answers answers.json
        : 사용자 답변 JSON으로 빈칸 채워 양식 출력

    python3 scripts/render_template.py --mode D
        : 시연 모드 — 가상 페르소나 예시 양식 출력

answers.json 스키마 (B 모드):
    {
      "F1_name": "홍길동",
      "F2_plausible": "...한 문단...",
      "F3_possible": "...",
      "F4_unexpected": "...",
      "F5_problem": "...",
      "F6_interest": "...",
      "F7_talent": "...",
      "F8_personality": "...",
      "F9_work": "...",
      "F10_value": "...",
      "F11_purposes": ["항목1", "항목2", ...],
      "F12_date": "2026년 5월 17일"
    }
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
BLANK_LINE = "_______________________________________________________________"


def load(name: str) -> dict:
    return json.loads((ASSETS / name).read_text(encoding="utf-8"))


def header_block() -> str:
    b = load("facts.json")["book"]
    return (
        f"> 출처: 『{b['title_ko']}』({b['year']}, {b['publisher']}, "
        f"ISBN {b['isbn13']}) — 저자 {' · '.join(b['authors'])}.\n"
        f"> 양식 주의: {b['form_template_caveat']}"
    )


def blank_form() -> str:
    """C 모드 — 빈 양식 (빈칸 12개 그대로)."""
    lines = [
        "● Vision Statement 비전선언문 ●",
        "",
        "Vision 임무",
        "",
        "나 _____________ 은/는",
        "",
        BLANK_LINE,
        BLANK_LINE,
        "________________________________ 한 기본미래(Plausible Future) 사회에 나타날",
        BLANK_LINE,
        BLANK_LINE,
        "________________________________ 한 또 다른 가능성의 미래(Possible Future) 사회에 나타날",
        BLANK_LINE,
        "________________________________ 한 뜻 밖의 미래(Unexpected Future) 사회에 나타날",
        BLANK_LINE,
        "________________________________ 문제, 욕구, 결핍을 해결하기 위해",
        "",
        "내가 타고난······",
        BLANK_LINE,
        "________________________________ 에 대한 관심과",
        BLANK_LINE,
        "________________________________ 한 재능(다중지능, 기술발달)과",
        BLANK_LINE,
        "________________________________ 행동성향, 성격들을 사용하는",
        BLANK_LINE,
        "________________________________ 직업 또는 일을 통해",
        BLANK_LINE,
        "________________________________ 한 가치가 실현되는 더 나은 사회를 만드는 일에",
        "부름을 받았습니다!",
        "",
        "",
        "Purposes 목적들",
        "",
        "이를 성취하기 위해서 다음과 같은 가치, 서비스, 제품, 봉사, 기타 활동인······",
        BLANK_LINE,
        "________________________________ 을 우선적으로 제공하겠습니다.",
        "",
        "",
        " 20 년 월 일",
    ]
    return "\n".join(lines)


def filled_form(answers: dict) -> str:
    """B 모드 — answers JSON으로 빈칸 채운 양식."""
    name = answers.get("F1_name", "_____")
    f2 = answers.get("F2_plausible", "_____")
    f3 = answers.get("F3_possible", "_____")
    f4 = answers.get("F4_unexpected", "_____")
    f5 = answers.get("F5_problem", "_____")
    f6 = answers.get("F6_interest", "_____")
    f7 = answers.get("F7_talent", "_____")
    f8 = answers.get("F8_personality", "_____")
    f9 = answers.get("F9_work", "_____")
    f10 = answers.get("F10_value", "_____")
    purposes = answers.get("F11_purposes", [])
    if isinstance(purposes, str):
        purposes_block = purposes
    else:
        purposes_block = "\n".join(f"{i+1}. {p}" for i, p in enumerate(purposes))
    date = answers.get("F12_date", "20 년 월 일")
    lines = [
        "● Vision Statement 비전선언문 ●",
        "",
        "Vision 임무",
        "",
        f"나 [{name}] 은/는",
        "",
        f"[기본미래(Plausible Future)] {f2}",
        "한 기본미래 사회에 나타날",
        "",
        f"[또 다른 가능성의 미래(Possible Future)] {f3}",
        "한 또 다른 가능성의 미래 사회에 나타날",
        "",
        f"[뜻밖의 미래(Unexpected Future)] {f4}",
        "한 뜻 밖의 미래 사회에 나타날",
        "",
        f"[문제·욕구·결핍] {f5}",
        "문제, 욕구, 결핍을 해결하기 위해",
        "",
        "내가 타고난······",
        f"[관심] {f6}",
        "에 대한 관심과",
        "",
        f"[재능] {f7}",
        "한 재능(다중지능, 기술발달)과",
        "",
        f"[행동성향·성격] {f8}",
        "행동성향, 성격들을 사용하는",
        "",
        f"[직업/일] {f9}",
        "직업 또는 일을 통해",
        "",
        f"[가치] {f10}",
        "한 가치가 실현되는 더 나은 사회를 만드는 일에",
        "부름을 받았습니다!",
        "",
        "",
        "Purposes 목적들",
        "",
        "이를 성취하기 위해서 다음과 같은 가치, 서비스, 제품, 봉사, 기타 활동인······",
        "",
        purposes_block,
        "",
        "을 우선적으로 제공하겠습니다.",
        "",
        "",
        f" {date}",
    ]
    return "\n".join(lines)


def questions_block() -> str:
    """A 모드 — 12개 코칭 질문 결정론적 출력."""
    fields = load("facts.json")["vision_statement_form"]["fields"]
    out = ["# Vision Statement 비전 선언문 — 1:1 코칭 질문 (12문항)", ""]
    out.append(header_block())
    out.append("")
    out.append("아래 12개 질문에 차례로 답해 주세요. 답을 모두 입력하시면 ")
    out.append("`scripts/render_template.py --mode B --answers <file>`로 양식이 완성됩니다.")
    out.append("")
    for f in fields:
        link = f" (참고 스킬: {f['linked_skill']})" if f.get("linked_skill") else ""
        out.append(f"### Q{f['order']} [{f['id']}] — {f['label_ko']}{link}")
        out.append(f"양식 문구: `{f['form_phrase']}`")
        out.append(f"질문: {f['question']}")
        constraints = []
        if f.get("min_chars") is not None:
            constraints.append(f"최소 {f['min_chars']}자")
        if f.get("max_chars") is not None:
            constraints.append(f"최대 {f['max_chars']}자")
        if f.get("min_items") is not None:
            constraints.append(f"최소 {f['min_items']}항목")
        if f.get("recommended_items") is not None:
            constraints.append(f"권장 {f['recommended_items']}항목")
        if f.get("max_items") is not None:
            constraints.append(f"최대 {f['max_items']}항목")
        if constraints:
            out.append(f"제약: {', '.join(constraints)}")
        out.append("")
    return "\n".join(out)


def demo_persona() -> dict:
    """D 모드 — 가상 페르소나 답변 (시연용)."""
    return {
        "F1_name": "[가상 페르소나] 홍길동",
        "F2_plausible": (
            "AGI가 본격 침투해 화이트칼라 자동화가 가속되고 "
            "한국 인구절벽이 심화되며, 의미·영성 시장이 첫 부흥기를 맞을"
        ),
        "F3_possible": (
            "AGI 충격이 역설적으로 청년의 의미 추구를 자극해 "
            "새로운 영성 공동체와 인문 르네상스가 시작될"
        ),
        "F4_unexpected": (
            "디지털 영성·AI 영적 동반자가 기성 종교를 대체하고 "
            "영적 분별이 핵심 사회 역량이 되는"
        ),
        "F5_problem": "AGI 시대의 의미 위기·영적 분별 부재·미래 대비 무지",
        "F6_interest": "미래학과 영성·기독교 신학·다음 세대 양육",
        "F7_talent": (
            "상위 3개 지능(Logical-Mathematical·Intrapersonal·Linguistic) + "
            "미래학 기술발달"
        ),
        "F8_personality": "INTJ 통찰형 + 에니어그램 5번(탐구가) 6번 날개",
        "F9_work": "미래학 단행본 저술·강연·신학교 강의·교회 담임 사역",
        "F10_value": "진리·지혜·정신적 가치가 살아있는",
        "F11_purposes": [
            "AGI 시대 미래학 단행본 5권 출간",
            "한국 청년 미래교육 강연 100회·글로벌 컨퍼런스 10회",
            "차세대 미래학자·영성 후학 20명 양성",
            "통합 지혜 디지털 아카이브 구축",
            "교회 청년부·신학교 비전 코칭 1년 커리큘럼 운영",
        ],
        "F12_date": "2026년 5월 17일",
    }


def render_demo() -> str:
    mi = load("facts.json")["multiple_intelligences_canonical"]
    lines = [
        "# 🎭 시연 모드 (D) — 가상 페르소나",
        "",
        "⚠ **아래는 가상 시연이며, 실존 인물의 비전 선언문이 아닙니다.**",
        "다중지능 표기는 vision-multipleintel-visioncoding 9지능 분류에 따른 가상의 상위 3개",
        "예시이며, 실제 점수는 해당 스킬의 진단을 거쳐야 합니다. 미래 사회 시나리오·",
        "통계 수치는 가상 예시이며, 실제 학술 근거를 갖춘 미래 예측이 아닙니다.",
        "",
        f"9지능 표준 분류 ({mi['source_skill']}): {', '.join(mi['categories'])}.",
        f"명명 주의: {mi['naming_caveat']}",
        "",
        header_block(),
        "",
        "---",
        "",
        filled_form(demo_persona()),
    ]
    return "\n".join(lines)


def render_for_mode(mode: str, answers_path: Path | None) -> str:
    if mode == "A":
        return questions_block()
    if mode == "B":
        if not answers_path:
            raise ValueError("--answers <file>이 B 모드에 필요합니다")
        answers = json.loads(answers_path.read_text(encoding="utf-8"))
        out = [
            "# Vision Statement 비전 선언문 (완성본)",
            "",
            header_block(),
            "",
            "---",
            "",
            filled_form(answers),
            "",
            "---",
            "",
            "## 검증 (다음 단계)",
            "",
            "다음 명령으로 결정론적 검증을 실행하세요:",
            "",
            "```",
            "python3 scripts/validate_output.py --answers <file>",
            "```",
            "",
            "검증 도구:",
            "  · V1 비전 영역 3겹 교집합 (vision-three-realm-balance)",
            "  · V2 진선미 검증 (vision-three-realm-balance)",
            "  · V3 6대 행동 강령 부합 (vision-five-stages)",
        ]
        return "\n".join(out)
    if mode == "C":
        return (
            "# Vision Statement 비전 선언문 — 빈 양식 (혼자 작성용)\n\n"
            + header_block()
            + "\n\n---\n\n"
            + blank_form()
        )
    if mode == "D":
        return render_demo()
    raise ValueError(f"unknown mode {mode}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="A", choices=["A", "B", "C", "D"])
    p.add_argument("--answers", default=None, help="B 모드 답변 JSON 경로")
    p.add_argument("--questions", action="store_true", help="A 모드 질문만 출력")
    args = p.parse_args()
    try:
        if args.mode == "A" or args.questions:
            print(render_for_mode("A", None))
        else:
            ap = Path(args.answers) if args.answers else None
            print(render_for_mode(args.mode, ap))
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
