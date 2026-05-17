"""변환 워크북 생성기 — 5단계 산출물을 단일 마크다운으로 결합.

LLM은 각 단계의 *내용*만 채우고, 워크북 스켈레톤·인용·날짜 표는
본 모듈이 결정론적으로 조립한다.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from . import date_engine, backcasting, smart_validator, okr_validator, citations


def build_workbook(
    today_iso: Optional[str],
    inspiration_quote: str,
    smart_report: smart_validator.SmartReport,
    backcasting_contents: Dict[str, str],
    okr_report: okr_validator.OkrReport,
    first_step: Dict[str, str],
    workbook_type: str = "A",
    extra_refs: Optional[List[str]] = None,
) -> str:
    """워크북 단일 마크다운 문서 생성."""
    tl = date_engine.build_timeline(today_iso)

    bc_check = backcasting.validate_backcasting(backcasting_contents)
    refs = list(citations.CORE_REFERENCES)
    if extra_refs:
        for r in extra_refs:
            if r not in refs:
                refs.append(r)

    out: List[str] = []
    out.append("# Vision Goal Reframing Workbook")
    out.append(f"**작성일**: {tl['today']['iso_date']} ({tl['today']['weekday_kr']}요일, {tl['today']['year']}년 {tl['today']['quarter']})")
    out.append(f"**입력 유형**: {workbook_type}")
    out.append("")
    out.append("## 1. 영감 원본 📖")
    out.append(f"> {inspiration_quote}")
    out.append("")
    out.append("*(Step 1 원칙: 사용자 영감 원본을 수정·압축·폄하 없이 그대로 인용)*")
    out.append("")
    out.append("## 2. SMART 검증 ⚖")
    out.append(f"검증 출처: {citations.cite('SMART_DORAN_1981')}")
    out.append("")
    out.append(smart_validator.render_table(smart_report))
    out.append("")
    out.append(f"**SMART 전체 통과 여부**: {'PASS' if smart_report.passed_all else 'FAIL — 보완 필요'}")
    out.append("")
    out.append("## 3. Backcasting 🔭")
    out.append(f"방법론 출처: {citations.cite('BACKCASTING_ROBINSON_1982')} ; {citations.cite('BACKCASTING_ROBINSON_1990')}")
    out.append("")
    out.append(backcasting.render_backcasting(tl, backcasting_contents))
    out.append("")
    if bc_check.errors:
        out.append("**Backcasting 검증 오류**:")
        for e in bc_check.errors:
            out.append(f"- {e}")
        out.append("")
    out.append("## 4. OKR (1년) 🎯")
    out.append(f"방법론 출처: {citations.cite('OKR_GROVE_1983')}")
    out.append(f"보급·채점 척도 출처: {citations.cite('OKR_DOERR_2018')} ; {citations.cite('OKR_GOOGLE_GRADING')}")
    out.append("")
    out.append(okr_validator.render_okr(okr_report))
    out.append("")
    out.append("**채점 척도 안내** (Google re:Work · Doerr 2018):")
    out.append("- 0.0~0.3 🔴 red — 계획·자원·실행 재검토")
    out.append("- 0.4~0.6 🟡 yellow — 진척 미흡, 보완")
    out.append("- 0.7~1.0 🟢 green — 이상적 (aspirational 평균 0.7 / committed 1.0)")
    out.append("")
    out.append("## 5. 첫 한 걸음 (T+1) 🚶")
    out.append(f"내일 아침 = {tl['tomorrow']['iso_date']} ({tl['tomorrow']['weekday_kr']}요일)")
    out.append("")
    for k in ["what", "when", "where", "how", "why"]:
        out.append(f"- **{k.capitalize()}**: {first_step.get(k, '—')}")
    out.append("")
    out.append("## 다음 단계")
    out.append("- 실행 지속력·습관 → vision-follow-through-habits")
    out.append("- 정기 점검·진척 추적 → vision-progress-review")
    out.append("")
    out.append(citations.references_block(refs))
    return "\n".join(out)
