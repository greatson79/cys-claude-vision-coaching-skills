"""vision-goal-reframing 통합 CLI 진입점.

SKILL.md가 호출하는 단일 명령. 표준입력으로 JSON 페이로드를 받아
SMART·Backcasting·OKR 검증·날짜 시간선·인용 lock·워크북 조립까지
한 번에 결정론으로 처리한다.

페이로드 예시:
{
  "today_iso": "2026-05-17",
  "user_text": "AGI 영성·미래학 통합 비전을 목표로 만들어줘",
  "vision_clarity_output": false,
  "has_ltg_stg": false,
  "inspiration_quote": "AGI 시대에 영성과 미래학을 잇는 통합 지혜를 다음 세대에 전수",
  "smart_goal": "2027-12-31까지 단행본 1권 출간",
  "smart_resources": "현 원고 6장 완성·주 10시간 확보",
  "smart_vision_link": "AGI 영성·미래학 통합 지혜 전수의 1차 결실",
  "backcasting": {
    "five_years": "단행본 5권 + 글로벌 강연 50회",
    "one_year": "첫 단행본 출간 + 강연 10회",
    "next_quarter": "골격 완성 + 출판사 미팅 3건",
    "one_week": "1~3장 골격 보강 + 출판사 5곳 조사",
    "tomorrow": "골격 현재 버전 30분 검토 + 보강 영역 3개 식별"
  },
  "okr": {
    "objective": "...",
    "key_results": ["...", "..."],
    "okr_type": "aspirational"
  },
  "first_step": {
    "what": "골격 현재 버전 30분 검토",
    "when": "06:30~07:00",
    "where": "서재 책상",
    "how": "노션 골격 파일 + 종이 인쇄",
    "why": "1주 후 1~3장 보강의 우선순위 식별"
  }
}
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict

# Allow being executed as `python3 lib/run.py` directly (without package import).
if __package__ in (None, ""):
    import os as _os
    _pkg_dir = _os.path.dirname(_os.path.abspath(__file__))
    _root = _os.path.dirname(_pkg_dir)
    if _root not in sys.path:
        sys.path.insert(0, _root)
    from lib import date_engine, smart_validator, okr_validator, backcasting, citations, workbook, input_router  # type: ignore
else:
    from . import date_engine, smart_validator, okr_validator, backcasting, citations, workbook, input_router


def run(payload: Dict[str, Any]) -> Dict[str, Any]:
    today_iso = payload.get("today_iso")
    timeline = date_engine.build_timeline(today_iso)

    decision = input_router.route(
        user_text=payload.get("user_text", ""),
        vision_clarity_output=bool(payload.get("vision_clarity_output", False)),
        has_ltg_stg=bool(payload.get("has_ltg_stg", False)),
    )

    result: Dict[str, Any] = {
        "timeline": timeline,
        "route": vars(decision),
        "errors": [],
    }

    # SMART
    if "smart_goal" in payload:
        sr = smart_validator.validate_smart(
            goal_text=payload["smart_goal"],
            resources_note=payload.get("smart_resources"),
            vision_link=payload.get("smart_vision_link"),
        )
        result["smart"] = sr.as_dict()
        if not sr.passed_all:
            result["errors"].append("SMART 5축 중 일부 미통과 — 보완 필요")

    # Backcasting
    if "backcasting" in payload:
        bc = backcasting.validate_backcasting(payload["backcasting"])
        result["backcasting"] = bc.as_dict()
        if not bc.passed:
            result["errors"].append("Backcasting 5시점 중 누락/부실 발견")

    # OKR
    if "okr" in payload:
        ok = payload["okr"]
        ores = okr_validator.validate_okr(
            objective=ok.get("objective", ""),
            key_results=ok.get("key_results", []),
            okr_type=ok.get("okr_type", "aspirational"),
        )
        result["okr"] = ores.as_dict()
        if not ores.passed:
            result["errors"].append("OKR 구조 검증 실패 — 보완 필요")

    # Workbook 조립 (필수 필드 모두 있을 때만)
    can_build = all(k in payload for k in ["inspiration_quote", "smart_goal", "backcasting", "okr", "first_step"])
    if can_build:
        sr = smart_validator.validate_smart(
            payload["smart_goal"],
            payload.get("smart_resources"),
            payload.get("smart_vision_link"),
        )
        ok = payload["okr"]
        ores = okr_validator.validate_okr(
            ok.get("objective", ""),
            ok.get("key_results", []),
            ok.get("okr_type", "aspirational"),
        )
        result["workbook_markdown"] = workbook.build_workbook(
            today_iso=today_iso,
            inspiration_quote=payload["inspiration_quote"],
            smart_report=sr,
            backcasting_contents=payload["backcasting"],
            okr_report=ores,
            first_step=payload["first_step"],
            workbook_type=decision.input_type,
        )
    else:
        result["workbook_markdown"] = None
        result["errors"].append("워크북 조립 불가 — 필수 필드 누락: inspiration_quote/smart_goal/backcasting/okr/first_step 중 일부")

    return result


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] != "-":
        with open(sys.argv[1], "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        payload = json.load(sys.stdin)
    out = run(payload)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
