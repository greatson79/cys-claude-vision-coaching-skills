#!/usr/bin/env python3
"""vision-three-realm-balance 결정론 CLI.

LLM은 *반드시* 이 스크립트를 호출하여 진단/분류/특수 케이스/인용 검증을 받는다.
LLM 자연어 추론으로 8개 패턴을 다시 결정하지 못하게 한다.

사용 예시:
    # 진단만:
    python3 scripts/diagnose.py --triple "O,O,X"

    # 분류 + 진단:
    python3 scripts/diagnose.py --text "박사님 본인 비전" --triple "O,O,O"

    # 분류만 (특수 케이스 + 입력 유형 + 호칭):
    python3 scripts/diagnose.py --text "10년 후 의사가 되고 싶다"

    # 인용 검증:
    python3 scripts/diagnose.py --verify-quote role_opening --candidate "..."

    # 인용 렌더링:
    python3 scripts/diagnose.py --render-quote closing

    # JSON 출력:
    python3 scripts/diagnose.py --text "..." --triple "O,X,X" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from lib import realm_balance as rb  # noqa: E402


def _parse_triple(raw: str) -> tuple[str, str, str]:
    parts = [p.strip() for p in raw.split(",")]
    return rb.normalize_triple(parts)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="vision-three-realm-balance 결정론 분석기"
    )
    parser.add_argument("--text", default="", help="사용자 입력 텍스트")
    parser.add_argument("--triple", default="", help='3영역 마크 "①,②,③" (예: "O,O,X")')
    parser.add_argument("--user-signal", default="", help="호칭 분기용 별도 신호 (없으면 --text 사용)")
    parser.add_argument("--verify-quote", default="", help="박사님 인용 검증 키")
    parser.add_argument("--candidate", default="", help="--verify-quote와 함께 검증할 후보 텍스트")
    parser.add_argument("--render-quote", default="", help="박사님 인용 렌더링 키")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    # 모드 1: 인용 검증
    if args.verify_quote:
        ok = rb.verify_quote(args.verify_quote, args.candidate)
        if args.json:
            print(json.dumps({"verify": ok, "key": args.verify_quote}, ensure_ascii=False))
        else:
            print("PASS" if ok else "FAIL — 박사님 원문과 불일치, 출력 금지")
        return 0 if ok else 1

    # 모드 2: 인용 렌더링
    if args.render_quote:
        try:
            print(rb.render_quote(args.render_quote))
            return 0
        except KeyError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2

    # 모드 3: 분류 + (선택적) 진단
    triple = _parse_triple(args.triple) if args.triple else None
    result = rb.analyze(
        args.text,
        triple=triple,
        user_signal=args.user_signal or None,
    )

    if args.json:
        payload = {
            "input_type": result.input_type,
            "address": result.address,
            "special_cases": [asdict(c) for c in result.special_cases],
            "diagnosis": asdict(result.diagnosis) if result.diagnosis else None,
            "notes": result.notes,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"[입력 유형] {result.input_type}")
    print(f"[호칭]      {result.address}")
    if result.special_cases:
        print("[특수 케이스]")
        for c in result.special_cases:
            print(f"  - {c.name}: {c.handler} — {c.note}")
    if result.diagnosis:
        d = result.diagnosis
        print(f"[진단]      {d.display_marks()}  →  {d.name}  (위험도: {d.risk})")
        print(f"[처방]      {d.remedy}")
        print(f"[다음 단계] {d.next_step}")
    if result.notes:
        print("[코치 노트]")
        for n in result.notes:
            print(f"  - {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
