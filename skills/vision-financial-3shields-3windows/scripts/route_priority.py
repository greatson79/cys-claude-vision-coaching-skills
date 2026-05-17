#!/usr/bin/env python3
"""3방패·3창 시작 순서 결정론 라우터.

SKILL.md "방패 시작 순서"·"창 시작 순서" 분기 로직을 LLM 추론에서 분리.
입력: 사용자 상태 플래그 JSON (stdin 또는 --input)
출력: 권장 순서 + 근거 (JSON)

상태 플래그 키:
  has_high_interest_debt: bool   (고이자 부채 있음)
  has_excess_insurance: bool     (보험 과도)
  has_overweight_investments: bool (투자 자산 과다·부실)
  has_overspending_pattern: bool (과소비·지출 통제 불가·저축 0)
  vision_clarified: bool         (비전 선언문 명료화 완료)

박사님 원칙 (SKILL.md 130~142 라인):
  방패①: 빚/보험 즉각 현금흐름 개선
  방패②: 투자 자산 재평가 시급
  방패③: 과소비 패턴
  일반적 권장: ① → ② → ③
  창①: 항상 첫 시작점
  창②: 창①의 잉여 → 장기 투자
  창③: 재정 상태와 무관, 병행 가능
"""
import json
import sys
import argparse


def decide_shield_order(state: dict) -> dict:
    flags = {
        "has_high_interest_debt": bool(state.get("has_high_interest_debt", False)),
        "has_excess_insurance": bool(state.get("has_excess_insurance", False)),
        "has_overweight_investments": bool(state.get("has_overweight_investments", False)),
        "has_overspending_pattern": bool(state.get("has_overspending_pattern", False)),
    }
    reasons = []
    order = []

    if flags["has_high_interest_debt"] or flags["has_excess_insurance"]:
        order.append(1)
        reasons.append(
            "방패① 우선: 고이자 부채 또는 보험 과도 → 즉각 현금흐름 개선이 가장 큰 즉효"
        )
    if flags["has_overweight_investments"]:
        if 2 not in order:
            order.append(2)
        reasons.append(
            "방패② 추가: 투자 자산 과다/부실 → 장기 저성장 전제 재평가가 시급"
        )
    if flags["has_overspending_pattern"]:
        if 3 not in order:
            order.append(3)
        reasons.append(
            "방패③ 추가: 과소비 패턴 → 소비 리모델링으로 여력 확보 우선"
        )

    if not order:
        order = [1, 2, 3]
        reasons.append("특정 트리거 미감지 → 일반적 권장 순서: ①(기초 정비) → ②(자산 재편) → ③(소비 최적화)")
    else:
        for n in (1, 2, 3):
            if n not in order:
                order.append(n)

    return {"order": order, "reasons": reasons, "flags_used": flags}


def decide_window_order(state: dict) -> dict:
    flags = {
        "vision_clarified": bool(state.get("vision_clarified", False)),
    }
    order = [1, 2, 3]
    reasons = [
        "창① 먼저: 지식 노동·1% 추가 소득은 지금 당장 시작 가능하며 복리 시스템의 씨앗",
        "창② 연결: 창①에서 만들어진 잉여를 장기 투자 시스템으로 전환",
        "창③ 병행: '마음의 부자'는 재정 상태와 무관하게 지금 시작 가능, 창①·② 병행",
    ]
    if not flags["vision_clarified"]:
        reasons.append(
            "주의: 비전 선언문이 명료화되지 않았음 → vision-statement-writer를 먼저 권장. "
            "재정 분석은 진행하되 비전 명료 후 전략을 최종 조율할 것"
        )
    return {"order": order, "reasons": reasons, "flags_used": flags}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="3방패·3창 시작 순서 결정")
    parser.add_argument("--target", choices=["shield", "window", "both"], default="both",
                        help="순서를 산출할 대상")
    parser.add_argument("--input", help="JSON 파일 경로 (기본: stdin)")
    args = parser.parse_args(argv[1:])

    if args.input:
        with open(args.input, encoding="utf-8") as f:
            state = json.load(f)
    else:
        raw = sys.stdin.read().strip()
        state = json.loads(raw) if raw else {}

    if not isinstance(state, dict):
        print("ERROR: 입력은 JSON 객체여야 합니다.", file=sys.stderr)
        return 2

    out = {}
    if args.target in ("shield", "both"):
        out["shield"] = decide_shield_order(state)
    if args.target in ("window", "both"):
        out["window"] = decide_window_order(state)

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
