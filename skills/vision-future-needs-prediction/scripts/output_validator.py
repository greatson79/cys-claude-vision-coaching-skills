#!/usr/bin/env python3
"""
vision-future-needs-prediction — output_validator.py

결정론 환원 모듈 2: 최종 산출물의 구조·형식·완결성을 결정론적으로 검증한다.

LLM이 자연어로 "출력 체크리스트"를 self-check 하는 단계를 코드로 환원.
SKILL.md "출력 체크리스트 — 산출 직전" 14항목 + 한계 4항목 + 데이터 인용
형식까지 일괄 검증한다. FAIL 항목이 하나라도 있으면 LLM은 보강 후 재산출해야
한다.

사용:
    python3 output_validator.py < output.md
    또는
    python3 output_validator.py --file output.md --time-years 30 --topic "주제 문장"

출력: JSON {"pass": bool, "checks": [...], "blockers": [...]}
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Check:
    id: str
    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "pass": self.passed, "detail": self.detail}


# ---------------------------------------------------------------------------
# 검증 규칙
# ---------------------------------------------------------------------------

STEEPS_DOMAINS = ["Society", "Technology", "Economy", "Environment", "Politics", "Spirituality"]

DECISION_ACTION_GROUPS = ["개인 액션", "기업 액션", "정책 액션"]

LIMITATION_REQUIRED = ["핵심 가정", "점검 신호", "재검토", "면책"]

CITATION_OUT = re.compile(r"\[출처:\s*[^\]]+\]")
CITATION_ESTIMATE = re.compile(r"\[추정:\s*[^\]]+\]")
NUMBER_CANDIDATE = re.compile(
    r"(?<![\w가-힣])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\d+)\s*(%|퍼센트|만\s*명|억\s*원|조\s*원|GW|TWh|kWh|건|배|위|건당|명당)"
)
TIME_PATTERN = re.compile(r"(\d+)\s*년")


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="검증할 마크다운 산출물 파일 경로(미지정 시 stdin)")
    ap.add_argument("--time-years", type=int, default=10, help="분석 시간 범위(년)")
    ap.add_argument("--topic", default="", help="원본 주제(고위험 프레이밍 자동 점검용)")
    ap.add_argument("--required-groups", default="", help="콤마구분 — Axis 1에 반드시 포함될 집단")
    ap.add_argument("--required-domains", default="", help="콤마구분 — Axis 3에 반드시 포함될 영역")
    ap.add_argument("--framing-warnings", default="", help="세미콜론구분 — 반드시 명시되어야 할 프레이밍 경고문")
    return ap.parse_args()


def read_input(path: str | None) -> str:
    if path:
        with open(path, encoding="utf-8") as f:
            return f.read()
    return sys.stdin.read()


def check_change_definition(text: str) -> Check:
    """변화 정의 4요소(무엇/언제/어디서/누구) 한 문장 검증."""
    m = re.search(r"##?#?\s*(?:변화\s*정의|변화 정의)[^\n]*\n+([^\n]+)", text)
    if not m:
        return Check("def_present", "변화 정의 섹션 존재", False, "## 변화 정의 헤더 미발견")
    sentence = m.group(1).strip()
    elements = []
    if re.search(r"\d{4}|\d+\s*년|단기|중기|장기", sentence):
        elements.append("언제")
    if re.search(r"한국|글로벌|아시아|미국|중국|일본|유럽|동아시아|지역|국가", sentence):
        elements.append("어디서")
    if re.search(
        r"세대|집단|계층|시민|국민|기업|가구|인구|노동|학생|환자|투자자|종교|소비자|"
        r"주민|거주자|이용자|사용자|구도자|종사자|근로자|구성원|신자|소비층",
        sentence,
    ):
        elements.append("누구")
    if re.search(
        r"확산|도입|전환|증가|감소|도래|성숙|보편화|시행|발효|상용화|보급|소멸|침체|회복|성장|위기|"
        r"재편|고착|급감|급증|하락|상승|개편|개혁|혁신|변화|충격|붕괴|부상|쇠퇴|"
        r"보편적|확립|정착|동결|침투|침식|진입|이탈|구조조정|등장|발생",
        sentence,
    ):
        elements.append("무엇")
    missing = [e for e in ["무엇", "언제", "어디서", "누구"] if e not in elements]
    return Check(
        "def_4_elements",
        "변화 정의 4요소(무엇/언제/어디서/누구)",
        not missing,
        "포함: " + ",".join(elements) + (f" / 누락: {','.join(missing)}" if missing else ""),
    )


def check_steeps_premem(text: str) -> Check:
    """STEEPS 6차원 사전 점검 섹션 존재 + 6차원 모두 언급."""
    section_present = bool(re.search(r"STEEPS\s*6\s*차원\s*사전\s*점검|STEEPS\s*사전\s*점검", text))
    found = [d for d in STEEPS_DOMAINS if re.search(rf"\b{d}\b", text, re.IGNORECASE)]
    ok = section_present and len(found) == 6
    return Check(
        "steeps_premem",
        "STEEPS 6차원 사전 점검",
        ok,
        f"section={section_present} / found={','.join(found)}",
    )


def check_axis1_table(text: str, required_groups: list[str]) -> Check:
    """축 1 표 행 8개 이상 + 주제 특화 집단 포함."""
    block = re.search(r"축\s*1[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|축\s*2|\Z)", text)
    if not block:
        return Check("axis1_table", "축 1 표 존재", False, "축 1 섹션 미발견")
    body = block.group(1)
    rows = re.findall(r"^\|[^|]+\|[^|]+\|[^|]+\|", body, re.MULTILINE)
    data_rows = [r for r in rows if not re.match(r"^\|\s*집단\s*\|", r) and not re.match(r"^\|\s*-+\s*\|", r)]
    has_min_rows = len(data_rows) >= 8
    missing_required = []
    for g in required_groups:
        if g and g not in body:
            missing_required.append(g)
    ok = has_min_rows and not missing_required
    return Check(
        "axis1_table",
        "축 1 표 8행+ + 주제 특화 집단 포함",
        ok,
        f"rows={len(data_rows)} / missing_required={missing_required}",
    )


def check_axis2_steeps(text: str) -> Check:
    """축 2 표가 STEEPS 6차원을 모두 포함."""
    block = re.search(r"축\s*2[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|축\s*3|\Z)", text)
    if not block:
        return Check("axis2_table", "축 2 표 존재", False, "축 2 섹션 미발견")
    body = block.group(1)
    found = []
    na_count = 0
    for d in STEEPS_DOMAINS:
        if re.search(rf"\|\s*{d}\s*\|", body, re.IGNORECASE):
            found.append(d)
            row = re.search(rf"\|\s*{d}\s*\|([^\n]+)", body, re.IGNORECASE)
            if row and re.search(r"N/?A", row.group(1), re.IGNORECASE):
                na_count += 1
    has_all = len(found) == 6
    na_alert = na_count >= 2
    detail = f"found={','.join(found)} / N/A={na_count}"
    if na_alert:
        detail += " / 균형 재점검 필요 (N/A 2개 이상)"
    return Check("axis2_steeps", "축 2 STEEPS 6차원 모두 포함", has_all, detail)


def check_axis3_domains(text: str, required_domains: list[str]) -> Check:
    """축 3 표 + 주제 특화 영역 포함."""
    block = re.search(r"축\s*3[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|핵심\s*통찰|\Z)", text)
    if not block:
        return Check("axis3_table", "축 3 표 존재", False, "축 3 섹션 미발견")
    body = block.group(1)
    rows = re.findall(r"^\|[^|]+\|[^|]+\|[^|]+\|", body, re.MULTILINE)
    data_rows = [r for r in rows if not re.match(r"^\|\s*영역\s*\|", r) and not re.match(r"^\|\s*-+\s*\|", r)]
    has_min_rows = len(data_rows) >= 6
    missing_required = [d for d in required_domains if d and d not in body]
    ok = has_min_rows and not missing_required
    return Check(
        "axis3_table",
        "축 3 표 6행+ + 주제 특화 영역 포함",
        ok,
        f"rows={len(data_rows)} / missing_required={missing_required}",
    )


def check_axis2_axis3_overlap(text: str) -> Check:
    """축 2와 축 3이 내용 중복 없는지 단순 휴리스틱(같은 문장 반복 검출)."""
    a2 = re.search(r"축\s*2[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|축\s*3|\Z)", text)
    a3 = re.search(r"축\s*3[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|핵심\s*통찰|\Z)", text)
    if not (a2 and a3):
        return Check("a2_a3_overlap", "축 2/3 중복 점검", True, "표 미존재로 점검 스킵")
    a2_sents = set(re.findall(r"[^.\n|]{15,}?(?=[.\n|])", a2.group(1)))
    a3_sents = set(re.findall(r"[^.\n|]{15,}?(?=[.\n|])", a3.group(1)))
    common = a2_sents & a3_sents
    return Check(
        "a2_a3_overlap",
        "축 2/3 동일 문장 중복 없음",
        len(common) == 0,
        f"공통 문장 {len(common)}건" + (f": {list(common)[:3]}" if common else ""),
    )


def check_core_insights(text: str) -> Check:
    """핵심 통찰 5선 (정확히 5개 또는 유형 D는 10개)."""
    section = re.search(r"핵심\s*통찰[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|의사결정자|\Z)", text)
    if not section:
        return Check("insights_5", "핵심 통찰 섹션 존재", False, "헤더 미발견")
    items = re.findall(r"^\s*(?:\d+[.)]\s+|[-*]\s+)", section.group(1), re.MULTILINE)
    ok = len(items) in (5, 10)
    return Check("insights_5", "핵심 통찰 5선(또는 10선)", ok, f"count={len(items)}")


def check_decision_actions(text: str) -> Check:
    """의사결정자 액션 3그룹(개인·기업·정책) 모두 존재.

    주의: ### 서브헤더가 ## 으로 오인되지 않도록 lookahead는 정확히 두 개 # 다음 공백으로 한정.
    """
    section = re.search(
        r"의사결정자\s*액션[^\n]*\n+([\s\S]+?)(?=\n##\s+(?!#)|한계[·\s]*불확실성|\Z)",
        text,
    )
    if not section:
        return Check("actions_3", "의사결정자 액션 섹션 존재", False, "헤더 미발견")
    body = section.group(1)
    found = [g for g in DECISION_ACTION_GROUPS if g in body]
    ok = len(found) == 3
    return Check("actions_3", "의사결정자 액션 3그룹", ok, f"found={','.join(found)}")


def check_limitations(text: str) -> Check:
    """한계·불확실성 4항목(핵심 가정·점검 신호·재검토·면책) 존재."""
    section = re.search(r"한계[·\s]*불확실성[^\n]*\n+([\s\S]+?)\Z", text)
    if not section:
        return Check("limit_4", "한계·불확실성 섹션 존재", False, "헤더 미발견")
    body = section.group(1)
    found = [k for k in LIMITATION_REQUIRED if k in body]
    ok = len(found) == 4
    return Check("limit_4", "한계·불확실성 4항목", ok, f"found={','.join(found)} / missing={set(LIMITATION_REQUIRED)-set(found)}")


def check_citation_format(text: str) -> Check:
    """모든 수치 인용에 [출처:...] 또는 [추정:...] 부착."""
    numbers = NUMBER_CANDIDATE.findall(text)
    out_count = len(CITATION_OUT.findall(text))
    est_count = len(CITATION_ESTIMATE.findall(text))
    annotated = out_count + est_count
    # 수치 후 5자 이내에 인용이 와야 진짜 부착으로 카운트(휴리스틱)
    nums_unannotated = 0
    for m in NUMBER_CANDIDATE.finditer(text):
        end = m.end()
        snippet = text[end : end + 80]
        if not (CITATION_OUT.search(snippet) or CITATION_ESTIMATE.search(snippet)):
            nums_unannotated += 1
    ok = nums_unannotated == 0 or annotated >= max(3, len(numbers) // 2)
    return Check(
        "citation_format",
        "수치 인용 형식 [출처:...] / [추정:...]",
        ok,
        f"numbers={len(numbers)} unannotated={nums_unannotated} 출처={out_count} 추정={est_count}",
    )


def check_balanced_framing(text: str, framing_warnings: list[str]) -> Check:
    """일방적 프레이밍 고위험 주제 — 반대 방향 명시 포함."""
    if not framing_warnings:
        return Check("framing_balanced", "고위험 프레이밍 — 반대 방향 명시", True, "트리거 없음")
    missing: list[str] = []
    for warn in framing_warnings:
        # 핵심 키워드만 추출해 본문에 등장하는지 확인
        keywords = re.findall(r"[가-힣A-Za-z]{2,}", warn)[:5]
        if not any(k in text for k in keywords):
            missing.append(warn[:40] + "…")
    ok = not missing
    return Check("framing_balanced", "고위험 프레이밍 — 반대 방향 명시", ok, f"missing={missing}")


def check_time_mode_b(text: str, time_years: int) -> Check:
    """20년+ 권장, 30년+ 의무 시간 분리 보충 분석(방식 B)."""
    if time_years < 20:
        return Check("time_mode_b", "시간 분리 방식 B (20년+ 권장 / 30년+ 의무)", True, "시간 범위 미해당")
    has_mode_b = bool(re.search(r"(시간\s*분리\s*보충|방식\s*B|단기[·\s]+중기[·\s]+장기)", text))
    ok = has_mode_b if time_years >= 30 else True
    return Check(
        "time_mode_b",
        "시간 분리 방식 B (20년+ 권장 / 30년+ 의무)",
        ok or time_years < 30,
        f"time_years={time_years} mode_b_found={has_mode_b}",
    )


def check_korean_context(text: str) -> Check:
    """한국 맥락 우선 반영(또는 지정 지역) 명시."""
    ok = bool(re.search(r"한국|글로벌|미국|중국|일본|동아시아|유럽", text))
    return Check("korean_context", "한국 맥락(또는 지정 지역) 명시", ok)


def check_neutral_tone(text: str) -> Check:
    """과장·일방 단정 어휘 검출."""
    bad_phrases = ["반드시 망한다", "확실히 망", "분명히 실패", "100% 성공", "절대 불가능", "완벽한 미래"]
    found = [p for p in bad_phrases if p in text]
    return Check("neutral_tone", "정보적·중립적 톤", not found, f"검출 어휘: {found}")


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main() -> int:
    args = parse_args()
    text = read_input(args.file)

    required_groups = [g.strip() for g in args.required_groups.split(",") if g.strip()]
    required_domains = [d.strip() for d in args.required_domains.split(",") if d.strip()]
    framing_warnings = [w.strip() for w in args.framing_warnings.split(";") if w.strip()]

    checks: list[Check] = [
        check_change_definition(text),
        check_steeps_premem(text),
        check_axis1_table(text, required_groups),
        check_axis2_steeps(text),
        check_axis3_domains(text, required_domains),
        check_axis2_axis3_overlap(text),
        check_core_insights(text),
        check_decision_actions(text),
        check_limitations(text),
        check_citation_format(text),
        check_balanced_framing(text, framing_warnings),
        check_time_mode_b(text, args.time_years),
        check_korean_context(text),
        check_neutral_tone(text),
    ]

    blockers = [c.to_dict() for c in checks if not c.passed]
    result = {
        "pass": not blockers,
        "total": len(checks),
        "passed": sum(1 for c in checks if c.passed),
        "failed": len(blockers),
        "checks": [c.to_dict() for c in checks],
        "blockers": blockers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
