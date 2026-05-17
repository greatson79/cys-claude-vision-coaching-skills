#!/usr/bin/env python3
"""12개월 재정 시뮬레이션 결정론 계산기.

SKILL.md 4단계 '자산 관리 통합 시뮬레이션' 표를 LLM이 계산하지 않도록 분리.
복리 계산, 1% 추가 소득 효과, 이자 절감 효과 등 모든 수치는 본 모듈로 산출.

입력: JSON (--input 또는 stdin)
{
  "monthly_income_expected": [12개 숫자],
  "monthly_income_actual":   [12개 숫자],
  "monthly_expense_expected":[12개 숫자],
  "monthly_expense_actual":  [12개 숫자],
  "starting_balance":        숫자 (기본 0)
}

또는 단축 모드:
{
  "base_monthly_income":  숫자,
  "base_monthly_expense":숫자,
  "starting_balance":     숫자
}
→ 12개월 동일값으로 채워서 시뮬레이션

출력: 월별 표 + 합계 + 연 복리 시뮬레이션 (7%·10% 기준)
"""
import json
import sys
import argparse
from typing import List


def expand_to_12(value, key: str) -> List[float]:
    if isinstance(value, (int, float)):
        return [float(value)] * 12
    if isinstance(value, list):
        if len(value) != 12:
            raise ValueError(f"{key}: 길이 12여야 합니다. 입력 길이={len(value)}")
        return [float(v) for v in value]
    raise ValueError(f"{key}: 숫자 또는 길이-12 리스트여야 합니다.")


def build_table(state: dict) -> dict:
    if "base_monthly_income" in state and "monthly_income_expected" not in state:
        bi = float(state["base_monthly_income"])
        be = float(state["base_monthly_expense"])
        income_exp = [bi] * 12
        income_act = [bi] * 12
        expense_exp = [be] * 12
        expense_act = [be] * 12
    else:
        income_exp = expand_to_12(state.get("monthly_income_expected", 0), "monthly_income_expected")
        income_act = expand_to_12(state.get("monthly_income_actual", income_exp), "monthly_income_actual")
        expense_exp = expand_to_12(state.get("monthly_expense_expected", 0), "monthly_expense_expected")
        expense_act = expand_to_12(state.get("monthly_expense_actual", expense_exp), "monthly_expense_actual")

    start_bal = float(state.get("starting_balance", 0))

    rows = []
    cum = start_bal
    months = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]
    for i in range(12):
        net = income_act[i] - expense_act[i]
        cum += net
        rows.append({
            "월": months[i],
            "수입_예상": income_exp[i],
            "수입_실제": income_act[i],
            "지출_예상": expense_exp[i],
            "지출_실제": expense_act[i],
            "월잔액": net,
            "누적잔액": cum,
        })

    sums = {
        "수입_예상": sum(income_exp),
        "수입_실제": sum(income_act),
        "지출_예상": sum(expense_exp),
        "지출_실제": sum(expense_act),
        "연간_잔액_변화": sum(income_act) - sum(expense_act),
        "기말_누적잔액": cum,
    }
    return {"rows": rows, "sums": sums, "starting_balance": start_bal}


def compound_projection(principal: float, years: int = 10) -> dict:
    out = {}
    for rate_label, r in [("7%", 0.07), ("10%", 0.10)]:
        series = []
        v = principal
        for y in range(1, years + 1):
            v *= (1 + r)
            series.append({"year": y, "value": round(v, 2)})
        out[f"연복리_{rate_label}_{years}년"] = series
    return out


def income_delta_1pct(base_monthly_income: float) -> dict:
    """창① 박사님 원칙: 월급 외 1% 추가 소득의 12개월·10년 누적 효과."""
    extra_monthly = base_monthly_income * 0.01
    yearly = extra_monthly * 12
    decade = yearly * 10
    decade_at_7pct = 0.0
    v = 0.0
    for _ in range(10):
        v = (v + yearly) * 1.07
    decade_at_7pct = v
    return {
        "기준_월수입": base_monthly_income,
        "1퍼센트_월_추가소득": round(extra_monthly, 2),
        "1년_누적": round(yearly, 2),
        "10년_단순누적": round(decade, 2),
        "10년_7%_복리_재투자": round(decade_at_7pct, 2),
    }


def interest_saving_1pct(debt_principal: float, original_rate: float) -> dict:
    """방패① 박사님 원칙: 부채 이자 1% 절감의 연·10년 효과."""
    annual_saving = debt_principal * 0.01
    decade_saving = annual_saving * 10
    return {
        "부채_원금": debt_principal,
        "원_금리": original_rate,
        "1퍼센트_금리_절감_연간_효과": round(annual_saving, 2),
        "10년_단순누적_절감": round(decade_saving, 2),
    }


def render_markdown_table(result: dict) -> str:
    lines = [
        "| 월 | 수입(예상) | 수입(실제) | 지출(예상) | 지출(실제) | 잔액(누적) |",
        "|----|-----------|-----------|-----------|-----------|-----------|",
    ]
    for r in result["rows"]:
        lines.append(
            f"| {r['월']} | {r['수입_예상']:.0f} | {r['수입_실제']:.0f} | "
            f"{r['지출_예상']:.0f} | {r['지출_실제']:.0f} | {r['누적잔액']:.0f} |"
        )
    s = result["sums"]
    lines.append(
        f"| **합계** | {s['수입_예상']:.0f} | {s['수입_실제']:.0f} | "
        f"{s['지출_예상']:.0f} | {s['지출_실제']:.0f} | {s['기말_누적잔액']:.0f} |"
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="12개월 재정 시뮬레이션 + 복리 투영")
    parser.add_argument("--input", help="JSON 파일 경로 (기본: stdin)")
    parser.add_argument("--markdown", action="store_true", help="마크다운 표만 출력")
    parser.add_argument("--mode", choices=["table", "compound", "income1pct", "interest1pct", "all"],
                        default="all", help="산출 항목 선택")
    parser.add_argument("--years", type=int, default=10, help="복리 투영 연수 (기본 10)")
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
    if args.mode in ("table", "all"):
        try:
            out["table"] = build_table(state)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
    if args.mode in ("compound", "all"):
        principal = float(state.get("starting_balance", 0))
        out["compound"] = compound_projection(principal, args.years)
    if args.mode in ("income1pct", "all") and "base_monthly_income" in state:
        out["income1pct"] = income_delta_1pct(float(state["base_monthly_income"]))
    if args.mode in ("interest1pct", "all") and "debt_principal" in state:
        out["interest1pct"] = interest_saving_1pct(
            float(state["debt_principal"]), float(state.get("original_rate", 0.0))
        )

    if args.markdown and "table" in out:
        print(render_markdown_table(out["table"]))
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
