#!/usr/bin/env python3
"""SMART 5역량 결정론적 엔진.

vision-smart-five-competence 스킬의 사실 조회·점수 계산·1만 시간 계산을
LLM 자연어 추론에서 분리한 결정론 모듈.

사용 예:
    python3 smart_engine.py facts --query competences
    python3 smart_engine.py facts --query deseco
    python3 smart_engine.py facts --query countries
    python3 smart_engine.py facts --query source --id ERICSSON_1993
    python3 smart_engine.py quote --key A_10000_HOURS
    python3 smart_engine.py assess --scores '{"S":3,"M":4,"A":6,"R":8,"T":5}'
    python3 smart_engine.py tenkhour --daily-hours 2 --current-hours 1200
    python3 smart_engine.py map --smart-keys SAT
    python3 smart_engine.py validate --scores '{"S":3,"M":4,"A":6,"R":8,"T":5}'
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "smart_facts.json"
VALID_SMART_KEYS = {"S", "M", "A", "R", "T"}
VALID_DESECO_CODES = {"TOOLS", "GROUPS", "AUTONOMY"}


def load_data() -> dict:
    """Load and return the smart_facts.json content."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"smart_facts.json not found at {DATA_PATH}. Skill data missing."
        )
    with DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


# ---------------- Validation -----------------

def validate_score(value: Any, key: str) -> int:
    """Validate a single score is integer 1~10."""
    if isinstance(value, bool):
        raise ValueError(f"Score for '{key}' must be integer, not bool")
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(
                f"Score for '{key}' must be integer 1~10 (got {value})"
            )
        value = int(value)
    if not isinstance(value, int):
        raise ValueError(
            f"Score for '{key}' must be integer 1~10 (got {type(value).__name__})"
        )
    if value < 1 or value > 10:
        raise ValueError(
            f"Score for '{key}' must be in range 1~10 (got {value})"
        )
    return value


def validate_scores(scores: dict) -> dict:
    """Validate a complete 5-key score dict."""
    if not isinstance(scores, dict):
        raise ValueError(f"scores must be dict, got {type(scores).__name__}")
    missing = VALID_SMART_KEYS - set(scores)
    extra = set(scores) - VALID_SMART_KEYS
    if missing:
        raise ValueError(
            f"Missing SMART keys: {sorted(missing)}. Required: S,M,A,R,T"
        )
    if extra:
        raise ValueError(
            f"Invalid SMART keys: {sorted(extra)}. Only S,M,A,R,T allowed"
        )
    return {k: validate_score(v, k) for k, v in scores.items()}


# ---------------- Fact lookup -----------------

def get_competences(data: dict) -> list[dict]:
    return sorted(data["competences"], key=lambda c: c["order"])


def get_competence(data: dict, key: str) -> dict:
    key = key.upper()
    if key not in VALID_SMART_KEYS:
        raise ValueError(f"Invalid SMART key: {key}. Use one of {sorted(VALID_SMART_KEYS)}")
    for c in data["competences"]:
        if c["key"] == key:
            return c
    raise KeyError(f"Competence {key} not found in data")


def get_deseco(data: dict) -> dict:
    return data["deseco"]


def get_countries(data: dict) -> list[str]:
    return data["deseco"]["participating_countries"]


def get_source(data: dict, source_id: str) -> dict:
    for s in data["academic_sources"]:
        if s["id"] == source_id:
            return s
    valid_ids = [s["id"] for s in data["academic_sources"]]
    raise KeyError(
        f"Academic source '{source_id}' not found. Valid IDs: {valid_ids}"
    )


def get_quote(data: dict, key: str) -> str:
    quotes = data["book_quotes_verbatim"]
    if key not in quotes:
        valid = sorted(quotes.keys())
        raise KeyError(
            f"Quote key '{key}' not found. Valid keys: {valid}"
        )
    return quotes[key]


def get_training(data: dict, smart_key: str) -> dict:
    smart_key = smart_key.upper()
    if smart_key not in VALID_SMART_KEYS:
        raise ValueError(f"Invalid SMART key: {smart_key}")
    return data["training_methods"][smart_key]


# ---------------- SMART <-> DeSeCo mapping -----------------

def smart_to_deseco(data: dict, smart_keys: str | list[str]) -> list[dict]:
    """Map SMART keys to DeSeCo categories.

    SMART keys can be passed as 'SAT' string or ['S','A','T'] list.
    Returns the DeSeCo categories these keys map into.
    """
    if isinstance(smart_keys, str):
        keys = list(smart_keys.upper())
    else:
        keys = [k.upper() for k in smart_keys]
    invalid = set(keys) - VALID_SMART_KEYS
    if invalid:
        raise ValueError(f"Invalid SMART keys: {sorted(invalid)}")
    mapped = []
    for kc in data["deseco"]["key_competencies"]:
        if any(k in kc["mapped_smart_keys"] for k in keys):
            mapped.append(kc)
    return mapped


def deseco_to_smart(data: dict, deseco_code: str) -> list[str]:
    """Return SMART keys mapped to a DeSeCo category code."""
    deseco_code = deseco_code.upper()
    if deseco_code not in VALID_DESECO_CODES:
        raise ValueError(
            f"Invalid DeSeCo code: {deseco_code}. Use one of {sorted(VALID_DESECO_CODES)}"
        )
    for kc in data["deseco"]["key_competencies"]:
        if kc["code"] == deseco_code:
            return kc["mapped_smart_keys"]
    raise KeyError(f"DeSeCo code {deseco_code} not found")


# ---------------- Assessment -----------------

def assess(data: dict, scores: dict) -> dict:
    """Run the full 5-competence assessment.

    Returns:
        {
          'scores': {validated input},
          'average': float,
          'weakest': [list of keys at min],
          'strongest': [list of keys at max],
          'deseco_group_scores': {TOOLS, GROUPS, AUTONOMY},
          'deseco_group_averages': {TOOLS, GROUPS, AUTONOMY},
          'recommendations': [{key, action, priority}]
        }
    """
    validated = validate_scores(scores)
    values = list(validated.values())
    avg = round(sum(values) / len(values), 2)
    min_v = min(values)
    max_v = max(values)
    weakest = sorted([k for k, v in validated.items() if v == min_v])
    strongest = sorted([k for k, v in validated.items() if v == max_v])

    deseco_group_scores = {}
    deseco_group_averages = {}
    for kc in data["deseco"]["key_competencies"]:
        code = kc["code"]
        keys = kc["mapped_smart_keys"]
        members = [validated[k] for k in keys]
        deseco_group_scores[code] = sum(members)
        deseco_group_averages[code] = round(sum(members) / len(members), 2)

    recommendations = []
    for k in weakest:
        recommendations.append({
            "key": k,
            "priority": "HIGH (약점 — 3단계 깊이 코칭 권장)",
            "action": f"{k} 역량 박사님 책 verbatim 인용 + 구체 훈련법 + 1주/1개월/3개월 계획"
        })
    for k in strongest:
        if k not in weakest:  # avoid duplicating when all equal
            recommendations.append({
                "key": k,
                "priority": "STRENGTH (강점 — 4단계 장인화 코칭 권장)",
                "action": f"{k} 역량 1만 시간 계획 + 무료 세미나·글 기고 등 7가지 훈련"
            })

    return {
        "scores": validated,
        "average": avg,
        "weakest": weakest,
        "strongest": strongest,
        "deseco_group_scores": deseco_group_scores,
        "deseco_group_averages": deseco_group_averages,
        "recommendations": recommendations,
    }


# ---------------- 10,000-hour calculator -----------------

def ten_thousand_hours(daily_hours: float, current_hours: float = 0.0,
                       start_date: str | None = None) -> dict:
    """1만 시간까지 남은 시간/일/년 계산.

    Args:
        daily_hours: 하루에 투자할 의도적 연습 시간 (deliberate practice)
        current_hours: 이미 누적된 시간
        start_date: 시작 날짜 (YYYY-MM-DD). 미지정 시 오늘.
    """
    if not isinstance(daily_hours, (int, float)) or isinstance(daily_hours, bool):
        raise ValueError("daily_hours must be a positive number")
    if daily_hours <= 0:
        raise ValueError(f"daily_hours must be > 0 (got {daily_hours})")
    if daily_hours > 24:
        raise ValueError(f"daily_hours cannot exceed 24 (got {daily_hours})")
    if not isinstance(current_hours, (int, float)) or isinstance(current_hours, bool):
        raise ValueError("current_hours must be a non-negative number")
    if current_hours < 0:
        raise ValueError(f"current_hours must be >= 0 (got {current_hours})")

    target = 10000.0
    remaining = max(0.0, target - float(current_hours))
    if remaining == 0:
        result_days = 0
    else:
        result_days = int(remaining / daily_hours) + (
            1 if (remaining % daily_hours) > 0 else 0
        )

    if start_date is None:
        sd = date.today()
    else:
        try:
            y, m, d = (int(x) for x in start_date.split("-"))
            sd = date(y, m, d)
        except Exception as exc:
            raise ValueError(
                f"start_date must be YYYY-MM-DD (got {start_date!r})"
            ) from exc

    completion_date = sd + timedelta(days=result_days)
    years = round(result_days / 365.25, 2)

    return {
        "target_hours": int(target),
        "current_hours": float(current_hours),
        "remaining_hours": remaining,
        "daily_hours": float(daily_hours),
        "days_to_complete": result_days,
        "years_to_complete": years,
        "start_date": sd.isoformat(),
        "completion_date": completion_date.isoformat(),
        "academic_source": "Ericsson, K. A., Krampe, R. T., & Tesch-Römer, C. (1993). Psychological Review, 100(3), 363-406.",
        "caveat": "Ericsson 본인은 단순 시간 누적이 아닌 'deliberate practice'(의도적 연습)임을 강조. Macnamara et al. (2014) 메타분석은 영역 의존성을 지적.",
    }


# ---------------- CLI -----------------

def _print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="SMART 5역량 결정론적 엔진"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_facts = sub.add_parser("facts", help="사실 조회")
    p_facts.add_argument(
        "--query",
        required=True,
        choices=[
            "competences", "competence", "deseco", "countries",
            "source", "all_sources", "training"
        ],
    )
    p_facts.add_argument("--key", help="competence key S/M/A/R/T 또는 training key")
    p_facts.add_argument("--id", help="academic source id")

    p_quote = sub.add_parser("quote", help="박사님 책 verbatim 인용")
    p_quote.add_argument("--key", required=True)

    p_assess = sub.add_parser("assess", help="5역량 자가 평가 채점")
    p_assess.add_argument("--scores", required=True,
                          help='JSON 예: {"S":3,"M":4,"A":6,"R":8,"T":5}')

    p_validate = sub.add_parser("validate", help="입력 점수 검증만")
    p_validate.add_argument("--scores", required=True)

    p_th = sub.add_parser("tenkhour", help="1만 시간 계산")
    p_th.add_argument("--daily-hours", type=float, required=True)
    p_th.add_argument("--current-hours", type=float, default=0.0)
    p_th.add_argument("--start-date", help="YYYY-MM-DD (default: today)")

    p_map = sub.add_parser("map", help="SMART <-> DeSeCo 매핑")
    p_map.add_argument("--smart-keys", help="예: SAT")
    p_map.add_argument("--deseco-code", help="TOOLS/GROUPS/AUTONOMY")

    args = parser.parse_args()
    data = load_data()

    try:
        if args.cmd == "facts":
            if args.query == "competences":
                _print(get_competences(data))
            elif args.query == "competence":
                if not args.key:
                    raise ValueError("--key required for competence")
                _print(get_competence(data, args.key))
            elif args.query == "deseco":
                _print(get_deseco(data))
            elif args.query == "countries":
                _print({
                    "count": data["deseco"]["participating_countries_count"],
                    "countries": get_countries(data),
                    "start_year": data["deseco"]["start_year"],
                    "end_year": data["deseco"]["end_year"],
                })
            elif args.query == "source":
                if not args.id:
                    raise ValueError("--id required for source")
                _print(get_source(data, args.id))
            elif args.query == "all_sources":
                _print([s["id"] for s in data["academic_sources"]])
            elif args.query == "training":
                if not args.key:
                    raise ValueError("--key required for training (S/M/A/R/T)")
                _print(get_training(data, args.key))

        elif args.cmd == "quote":
            _print({"key": args.key, "quote": get_quote(data, args.key)})

        elif args.cmd == "validate":
            scores = json.loads(args.scores)
            _print(validate_scores(scores))

        elif args.cmd == "assess":
            scores = json.loads(args.scores)
            _print(assess(data, scores))

        elif args.cmd == "tenkhour":
            _print(ten_thousand_hours(
                daily_hours=args.daily_hours,
                current_hours=args.current_hours,
                start_date=args.start_date,
            ))

        elif args.cmd == "map":
            if args.smart_keys and args.deseco_code:
                raise ValueError("Provide either --smart-keys OR --deseco-code, not both")
            if args.smart_keys:
                _print(smart_to_deseco(data, args.smart_keys))
            elif args.deseco_code:
                _print({
                    "deseco_code": args.deseco_code.upper(),
                    "smart_keys": deseco_to_smart(data, args.deseco_code),
                })
            else:
                raise ValueError("Provide --smart-keys or --deseco-code")
    except (ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except FileNotFoundError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
