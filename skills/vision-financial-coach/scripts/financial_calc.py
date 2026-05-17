#!/usr/bin/env python3
"""
vision-financial-coach 결정론적 계산 모듈

LLM 자연어 추론에서 분리된 결정론 함수들:
- snowball_simulation: 스노우볼 부채 청산 시뮬레이션 (월별 상환 추적)
- avalanche_simulation: 어밸런치 부채 청산 시뮬레이션
- tax_credit_calc: 연금저축/IRP 세액공제 환급액 계산
- emergency_fund_target: 응급자금 목표액 계산 (월 평균 지출 × 권장 개월수)
- budget_rule_50_30_20: 50/30/20 룰 분배 계산
- categorize_debts: 부채를 악성/중성/양성으로 자동 분류
- validate_budget_data: 입력 데이터 검증 (음수·합 검증)
- emergency_fund_recommended_months: 사용자 유형별 권장 응급자금 개월수 결정

CLI 사용:
  python3 financial_calc.py snowball '[{"name":"A","balance":1000,"rate":0.025,"min":20}]' 40
  python3 financial_calc.py avalanche '[{"name":"A","balance":1000,"rate":0.025,"min":20}]' 40
  python3 financial_calc.py tax 9000000 5500
  python3 financial_calc.py emergency 3000000 6
  python3 financial_calc.py budget 5000000
  python3 financial_calc.py classify '[{"name":"카드","rate":0.199}]'
"""
import json
import sys
from typing import List, Dict, Any, Tuple


# ============================================================
# 1. 입력 데이터 검증
# ============================================================

def validate_budget_data(income: float, expenses_by_category: Dict[str, float]) -> Dict[str, Any]:
    """
    수입·지출 데이터 검증.
    음수 거부, 카테고리 합 검증, 잔액 계산.
    """
    errors = []
    if income < 0:
        errors.append(f"수입은 음수가 될 수 없음: {income}")
    for cat, amt in expenses_by_category.items():
        if amt < 0:
            errors.append(f"지출 카테고리 '{cat}'가 음수: {amt}")
    total_expense = sum(expenses_by_category.values())
    balance = income - total_expense
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "income": income,
        "total_expense": total_expense,
        "balance": balance,
        "savings_rate": (balance / income) if income > 0 else 0.0,
    }


def validate_debt_data(debts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    부채 목록 데이터 검증.
    각 항목 필수 필드: name, balance, rate (소수, 0.199=19.9%), min (최소 상환액)
    """
    errors = []
    for i, d in enumerate(debts):
        for key in ["name", "balance", "rate", "min"]:
            if key not in d:
                errors.append(f"부채 #{i+1}: '{key}' 필드 누락")
        if "balance" in d and d["balance"] <= 0:
            errors.append(f"부채 #{i+1} ({d.get('name','?')}): 잔액이 0 이하: {d['balance']}")
        if "rate" in d and (d["rate"] < 0 or d["rate"] > 0.30):
            errors.append(f"부채 #{i+1} ({d.get('name','?')}): 이자율 범위 이상 (0~30% 한국 법정 상한): {d['rate']}")
        if "min" in d and d["min"] < 0:
            errors.append(f"부채 #{i+1} ({d.get('name','?')}): 최소 상환액 음수: {d['min']}")
    return {"valid": len(errors) == 0, "errors": errors}


# ============================================================
# 2. 부채 청산 시뮬레이션 (Snowball / Avalanche)
# ============================================================

def _simulate_debt_payoff(
    debts: List[Dict[str, Any]],
    extra_payment: float,
    order_key,
    max_months: int = 600,
) -> Dict[str, Any]:
    """
    부채 청산 시뮬레이션 공통 엔진.

    Args:
        debts: [{"name", "balance", "rate" (연이율 소수), "min" (월 최소 상환액)}]
        extra_payment: 모든 최소 상환을 한 후 남은 여유 자금 (월)
        order_key: 부채 정렬 기준 (Snowball=잔액 오름차순, Avalanche=이자율 내림차순)
        max_months: 안전장치

    Returns: {months, total_interest, payoff_order, schedule}
    """
    state = []
    for d in debts:
        state.append({
            "name": d["name"],
            "balance": float(d["balance"]),
            "rate": float(d["rate"]),
            "min": float(d["min"]),
            "paid_off_month": None,
            "total_interest": 0.0,
        })
    month = 0
    while month < max_months and any(s["balance"] > 0.01 for s in state):
        month += 1
        # 1. 모든 미상환 부채에 월간 이자 누적
        for s in state:
            if s["balance"] > 0.01:
                monthly_interest = s["balance"] * s["rate"] / 12.0
                s["balance"] += monthly_interest
                s["total_interest"] += monthly_interest
        # 2. 최소 상환액 지급 (각 부채에서 차감)
        for s in state:
            if s["balance"] > 0.01:
                payment = min(s["min"], s["balance"])
                s["balance"] -= payment
        # 3. 여유 자금을 우선순위 1위 미상환 부채에 집중 투입
        remaining_extra = extra_payment
        active = [s for s in state if s["balance"] > 0.01]
        active_sorted = sorted(active, key=order_key)
        for s in active_sorted:
            if remaining_extra <= 0:
                break
            apply = min(remaining_extra, s["balance"])
            s["balance"] -= apply
            remaining_extra -= apply
            # 한 부채에 집중 — 첫 부채에 다 쏟고 다음 부채로 넘어가지 않음
            # 단, 그 부채가 청산되어 잔여가 있으면 그 잔여를 다음 부채에
            # 첫 부채에 남은 잔액보다 extra가 크면 그 차액이 자동 다음 부채로
        # 4. 청산된 부채 마킹
        for s in state:
            if s["balance"] <= 0.01 and s["paid_off_month"] is None:
                s["paid_off_month"] = month

    total_interest = sum(s["total_interest"] for s in state)
    payoff_order = sorted(
        [(s["name"], s["paid_off_month"], round(s["total_interest"], 2)) for s in state],
        key=lambda x: (x[1] if x[1] is not None else 9999),
    )
    cleared = all(s["balance"] <= 0.01 for s in state)
    return {
        "months": month if cleared else None,
        "cleared": cleared,
        "total_interest": round(total_interest, 2),
        "payoff_order": payoff_order,
    }


def snowball_simulation(debts: List[Dict[str, Any]], extra_payment: float) -> Dict[str, Any]:
    """Dave Ramsey 스노우볼: 잔액이 작은 부채부터."""
    return _simulate_debt_payoff(
        debts, extra_payment, order_key=lambda s: s["balance"]
    )


def avalanche_simulation(debts: List[Dict[str, Any]], extra_payment: float) -> Dict[str, Any]:
    """어밸런치: 이자율이 높은 부채부터."""
    return _simulate_debt_payoff(
        debts, extra_payment, order_key=lambda s: -s["rate"]
    )


def compare_snowball_avalanche(debts: List[Dict[str, Any]], extra_payment: float) -> Dict[str, Any]:
    """두 방식 비교 결과."""
    s = snowball_simulation(debts, extra_payment)
    a = avalanche_simulation(debts, extra_payment)
    if not s["cleared"] or not a["cleared"]:
        return {"snowball": s, "avalanche": a, "comparison": "한쪽 또는 양쪽이 60년 내 청산 불가 — 여유 자금 부족"}
    interest_diff = s["total_interest"] - a["total_interest"]
    months_diff = s["months"] - a["months"]
    same_order = [p[0] for p in s["payoff_order"]] == [p[0] for p in a["payoff_order"]]
    return {
        "snowball": s,
        "avalanche": a,
        "interest_saving_by_avalanche": round(interest_diff, 2),
        "months_saving_by_avalanche": months_diff,
        "same_order": same_order,
        "comparison": (
            "두 방식의 청산 순서가 동일 — 결과 동일"
            if same_order
            else f"어밸런치가 이자 {interest_diff:,.0f}원 절약, {months_diff}개월 단축"
        ),
    }


# ============================================================
# 3. 연금저축/IRP 세액공제 환급액 계산
# ============================================================

def tax_credit_calc(
    contribution: float,
    annual_salary_manwon: float,
    is_self_employed: bool = False,
    is_self_employed_income_below_4500: bool = None,
) -> Dict[str, Any]:
    """
    연금저축·IRP 세액공제 환급액 계산.

    근거: 국세청 — 근로소득자 총급여 5,500만원 이하 16.5%, 초과 13.2%.
    자영업·종합소득 4,500만원 이하 16.5%, 초과 13.2%.
    합산 한도 900만원 (연금저축 600 + IRP 300 또는 IRP 단독 900).

    Args:
        contribution: 연간 납입액 (원)
        annual_salary_manwon: 근로자 총급여 (만원) 또는 자영업 종합소득 (만원)
        is_self_employed: 자영업 여부 (True이면 4,500만원 기준 적용)

    Returns: {capped_amount, rate, refund, exceeded}
    """
    LIMIT = 9_000_000  # 합산 900만원
    capped = min(contribution, LIMIT)
    exceeded = max(0, contribution - LIMIT)

    if is_self_employed:
        threshold_manwon = 4500
    else:
        threshold_manwon = 5500

    rate = 0.165 if annual_salary_manwon <= threshold_manwon else 0.132
    refund = round(capped * rate)
    return {
        "contribution_input": contribution,
        "capped_amount": capped,
        "exceeded": exceeded,
        "rate": rate,
        "refund": refund,
        "rate_label": f"{rate*100:.1f}% (지방소득세 포함)",
        "source": "국세청 — 근로소득자 5,500만원 / 자영업 4,500만원 기준",
    }


# ============================================================
# 4. 응급자금 목표 계산
# ============================================================

def emergency_fund_recommended_months(user_type: str) -> Dict[str, Any]:
    """
    사용자 유형별 응급자금 권장 개월수.

    근거:
    - Ramsey (Total Money Makeover 2003): 직장인 3~6개월
    - Orman (Young Fabulous & Broke 2005): 8개월 (청년 고부채 취약)
    - 자영업자 권장 12개월: 한국 자영업 평균 폐업까지 약 3년·계절 변동성·매출 변동성 고려
      → 보수적 권장. 단 본 권장은 보편적 학계 합의가 아니며 본 스킬의 한국 적응판 권고.
    """
    table = {
        "salaried": {"min": 3, "max": 6, "source": "Ramsey, Total Money Makeover (2003)"},
        "young_high_debt": {"min": 8, "max": 8, "source": "Orman, Young Fabulous & Broke (2005)"},
        "self_employed": {"min": 6, "max": 12, "source": "본 스킬 한국 적응판: Ramsey 3~6개월 보수적 확장 (소득 변동성·계절성 고려). 학계 단일 표준 없음 — 보편 표준 6개월부터 자영업 위험 수준 따라 최대 12개월"},
        "retiree": {"min": 12, "max": 24, "source": "Orman, The Ultimate Retirement Guide (2020) — 은퇴자 1~2년 권장"},
    }
    if user_type not in table:
        return {"error": f"알 수 없는 user_type: {user_type}. 가능값: salaried, young_high_debt, self_employed, retiree"}
    return {"user_type": user_type, **table[user_type]}


def emergency_fund_target(monthly_expense: float, user_type: str = "salaried") -> Dict[str, Any]:
    """
    응급자금 목표액 계산 = 월 평균 (필수) 지출 × 권장 개월수.

    Args:
        monthly_expense: 월 평균 필수 지출 (주거·식비·교통·보험·부채 최소 상환 합산, 원)
        user_type: salaried, young_high_debt, self_employed, retiree

    Returns: {target_min, target_max, months, source}
    """
    rec = emergency_fund_recommended_months(user_type)
    if "error" in rec:
        return rec
    return {
        "monthly_expense": monthly_expense,
        "user_type": user_type,
        "target_min": round(monthly_expense * rec["min"]),
        "target_max": round(monthly_expense * rec["max"]),
        "months_min": rec["min"],
        "months_max": rec["max"],
        "source": rec["source"],
        "note": "응급자금 기준은 '월 평균 필수 지출' (주거·식비·교통·보험·부채 최소 상환). 자유·여가는 제외.",
    }


# ============================================================
# 5. 50/30/20 룰 분배 계산
# ============================================================

def budget_rule_50_30_20(monthly_income: float, has_tithe: bool = False) -> Dict[str, Any]:
    """
    50/30/20 룰 분배 (Elizabeth Warren·Amelia Warren Tyagi, All Your Worth 2005).
    헌금/십일조 있으면 변형 안내 함께 반환.
    """
    base = {
        "necessities_50": round(monthly_income * 0.50),
        "wants_30": round(monthly_income * 0.30),
        "savings_debt_20": round(monthly_income * 0.20),
        "source": "Elizabeth Warren & Amelia Warren Tyagi, All Your Worth: The Ultimate Lifetime Money Plan (Free Press, 2005)",
    }
    if not has_tithe:
        return {"standard": base, "income": monthly_income}
    variant_40_25_20_15 = {
        "necessities_40": round(monthly_income * 0.40),
        "wants_25": round(monthly_income * 0.25),
        "savings_debt_20": round(monthly_income * 0.20),
        "tithe_15": round(monthly_income * 0.15),
    }
    variant_50_20_20_10 = {
        "necessities_50": round(monthly_income * 0.50),
        "wants_20": round(monthly_income * 0.20),
        "savings_debt_20": round(monthly_income * 0.20),
        "tithe_10": round(monthly_income * 0.10),
    }
    return {
        "income": monthly_income,
        "standard": base,
        "variant_with_tithe_balanced_40_25_20_15": variant_40_25_20_15,
        "variant_with_tithe_savings_first_50_20_20_10": variant_50_20_20_10,
        "note": "십일조(10%) 또는 헌금 별도 카테고리 분리한 본 스킬 변형. Warren 원본은 자유 카테고리 안에 기부 포함 가능 입장.",
    }


# ============================================================
# 6. 부채 유형 분류 (악성/중성/양성)
# ============================================================

def categorize_debts(debts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    이자율 기반 부채 분류.
    악성 (High-Interest): 연 10% 이상 — 카드·캐피탈·리볼빙·사채
    중성: 연 4% 이상 10% 미만 — 자동차·일반 신용대출
    양성: 연 4% 미만 — 학자금·주담대
    """
    result = []
    for d in debts:
        rate = float(d["rate"])
        if rate >= 0.10:
            tier = "악성 (High-Interest) — 최우선 청산"
        elif rate >= 0.04:
            tier = "중성 — 다음 청산"
        else:
            tier = "양성 — 마지막 청산 (학자금·주담대 등)"
        result.append({
            "name": d["name"],
            "balance": d["balance"],
            "rate": rate,
            "rate_pct": f"{rate*100:.2f}%",
            "tier": tier,
        })
    return result


# ============================================================
# 7. 청년도약계좌 → 청년미래적금 전환 안내 헬퍼
# ============================================================

def youth_account_info(birth_year: int = None, current_year: int = 2026) -> Dict[str, Any]:
    """
    청년도약계좌 신규 가입 가능 여부 및 후속 상품 안내.
    근거: 금융위원회 2025년 보도자료 — 청년도약계좌는 2025년 12월 31일 신규 가입 종료.
    2026년부터 후속 상품 청년미래적금이 운영됨.
    """
    info = {
        "yorim_account_new_signup_available": False,
        "yorim_signup_closed_date": "2025-12-31",
        "successor_product": "청년미래적금 (2026~)",
        "current_year": current_year,
        "source": "금융위원회 2025년 보도자료 — 청년도약계좌는 2025.12.31 신규 가입 종료, 청년미래적금으로 대체",
        "kept_benefit_for_existing": "기존 청년도약계좌 가입자는 만기까지 정부기여금 유지 (월 최대 33,000원, 2025년 1월부터 확대 기준)",
    }
    if birth_year is not None:
        age = current_year - birth_year
        info["age"] = age
        info["age_eligible_19_34"] = 19 <= age <= 34
    return info


# ============================================================
# 8. 부채 우선순위 정렬 (Baby Steps 매핑)
# ============================================================

def prioritize_baby_steps(
    has_emergency_fund_1month: bool,
    high_interest_debt_remaining: float,
    has_emergency_fund_3_6month: bool,
    retirement_savings_rate_pct: float,
    has_children_fund_started: bool,
    mortgage_remaining: float,
) -> Dict[str, Any]:
    """
    사용자 상황에서 Dave Ramsey 7 Baby Steps 중 현재 위치 결정.
    """
    if not has_emergency_fund_1month:
        current = 1
        action = "Baby Step 1: 시작 응급자금 (한국 기준 약 100~150만원 또는 월 필수 지출 1개월분 중 큰 값) 모으기"
    elif high_interest_debt_remaining > 0:
        current = 2
        action = f"Baby Step 2: 고이자 부채 {high_interest_debt_remaining:,.0f}원 청산 (스노우볼/어밸런치 선택)"
    elif not has_emergency_fund_3_6month:
        current = 3
        action = "Baby Step 3: 3~6개월 (Orman 8개월) 완전 응급자금 적립"
    elif retirement_savings_rate_pct < 15:
        current = 4
        action = f"Baby Step 4: 소득 15% 은퇴 투자 (현재 {retirement_savings_rate_pct}%) — 연금저축/IRP/ISA"
    elif not has_children_fund_started:
        current = 5
        action = "Baby Step 5: 자녀 자금 (대학·결혼) 적립 시작"
    elif mortgage_remaining > 0:
        current = 6
        action = f"Baby Step 6: 주담대 잔액 {mortgage_remaining:,.0f}원 조기 상환"
    else:
        current = 7
        action = "Baby Step 7: 부 축적 + 기부 (Give like no one else)"
    return {
        "current_step": current,
        "next_action": action,
        "source": "Dave Ramsey, The Total Money Makeover (2003), Chapter 11-17 — Baby Steps 1~7",
    }


# ============================================================
# CLI
# ============================================================

def _print_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]

    if cmd == "snowball":
        debts = json.loads(sys.argv[2])
        extra = float(sys.argv[3])
        _print_json(snowball_simulation(debts, extra))
    elif cmd == "avalanche":
        debts = json.loads(sys.argv[2])
        extra = float(sys.argv[3])
        _print_json(avalanche_simulation(debts, extra))
    elif cmd == "compare":
        debts = json.loads(sys.argv[2])
        extra = float(sys.argv[3])
        _print_json(compare_snowball_avalanche(debts, extra))
    elif cmd == "tax":
        contribution = float(sys.argv[2])
        salary_manwon = float(sys.argv[3])
        is_self = (len(sys.argv) > 4 and sys.argv[4] == "self")
        _print_json(tax_credit_calc(contribution, salary_manwon, is_self_employed=is_self))
    elif cmd == "emergency":
        monthly_expense = float(sys.argv[2])
        user_type = sys.argv[3] if len(sys.argv) > 3 else "salaried"
        _print_json(emergency_fund_target(monthly_expense, user_type))
    elif cmd == "budget":
        income = float(sys.argv[2])
        has_tithe = (len(sys.argv) > 3 and sys.argv[3] == "tithe")
        _print_json(budget_rule_50_30_20(income, has_tithe))
    elif cmd == "classify":
        debts = json.loads(sys.argv[2])
        _print_json(categorize_debts(debts))
    elif cmd == "youth":
        birth = int(sys.argv[2]) if len(sys.argv) > 2 else None
        _print_json(youth_account_info(birth))
    elif cmd == "babysteps":
        data = json.loads(sys.argv[2])
        _print_json(prioritize_baby_steps(**data))
    elif cmd == "validate":
        income = float(sys.argv[2])
        expenses = json.loads(sys.argv[3])
        _print_json(validate_budget_data(income, expenses))
    elif cmd == "validate_debt":
        debts = json.loads(sys.argv[2])
        _print_json(validate_debt_data(debts))
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
