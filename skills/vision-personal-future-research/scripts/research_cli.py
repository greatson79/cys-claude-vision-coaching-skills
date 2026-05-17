#!/usr/bin/env python3
"""vision-personal-future-research CLI — SKILL.md에서 결정론 단계 호출 진입점.

사용 패턴
---------
# 1) 가중치 계산 — 진단 JSON을 stdin으로 받음
python3 scripts/research_cli.py weights \\
  --vision-candidate --target-recoef-domain Technology < input.json

# 2) 시야 비율 — 연령 1개
python3 scripts/research_cli.py vision-ratio --age 47

# 3) 시간축 — 현재 연도 → Y/Y+5/Y+15/Y+30
python3 scripts/research_cli.py time-axis --year 2026

# 4) 출처 lookup
python3 scripts/research_cli.py source --domain Society --horizon short --id kr_tfr

# 5) 카드 빌드 (가중치 JSON 입력)
python3 scripts/research_cli.py cards --mode standard --include-wildcards < weights.json

# 6) 종합 점수
python3 scripts/research_cli.py score --weight 25 --horizon short --impact high

# 7) self-check
python3 scripts/research_cli.py self-check

# 8) 풀 파이프라인
python3 scripts/research_cli.py pipeline \\
  --vision-candidate --year 2026 --age 47 --mode standard \\
  --target-recoef-domain Technology < input.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

THIS = Path(__file__).resolve()
ROOT = THIS.parent.parent
sys.path.insert(0, str(ROOT))

from lib import research_engine as eng  # noqa: E402


def _read_json_stdin() -> dict:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def _emit(obj) -> None:
    if hasattr(obj, "__dataclass_fields__"):
        obj = asdict(obj)
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_weights(args: argparse.Namespace) -> int:
    payload = _read_json_stdin()
    diagnoses = payload.get("diagnoses", payload)
    res = eng.compute_weights(
        diagnoses,
        vision_candidate=args.vision_candidate,
        target_recoef_domain=args.target_recoef_domain,
        job_domains=payload.get("job_domains"),
        existential_full_weight=args.existential_full,
    )
    _emit(res)
    return 0 if res.validation["ok"] else 2


def cmd_vision_ratio(args: argparse.Namespace) -> int:
    _emit(eng.vision_ratio_for_age(args.age))
    return 0


def cmd_time_axis(args: argparse.Namespace) -> int:
    _emit(eng.absolute_time_axis(args.year))
    return 0


def cmd_source(args: argparse.Namespace) -> int:
    src = eng.get_source(args.domain, args.horizon, args.id)
    if src is None:
        print(json.dumps({"error": "claim_id not registered — auto FAIL per skill policy"}, ensure_ascii=False))
        return 3
    _emit(src)
    return 0


def cmd_list_sources(args: argparse.Namespace) -> int:
    _emit(eng.list_sources(args.domain, args.horizon))
    return 0


def cmd_cards(args: argparse.Namespace) -> int:
    payload = _read_json_stdin()
    weights = payload.get("weights_pct") or payload
    impacts = payload.get("personal_impact_by_id") or {}
    cards = eng.build_change_cards(
        weights,
        personal_impact_by_id=impacts,
        include_wildcards=args.include_wildcards,
    )
    cards = eng.select_top_cards(cards, mode=args.mode)
    cards = eng.ensure_six_domain_min_one(cards)
    _emit([asdict(c) for c in cards])
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    s = eng.composite_score(args.weight, args.horizon, args.impact)
    print(json.dumps({"composite_score": round(s, 4)}))
    return 0


def cmd_self_check(_args: argparse.Namespace) -> int:
    out = eng.self_check()
    _emit(out)
    return 0 if out["ok"] else 1


def cmd_missing_notice(args: argparse.Namespace) -> int:
    keys = [k.strip() for k in args.present.split(",") if k.strip()]
    _emit(eng.missing_diagnosis_notice(keys))
    return 0


def cmd_pipeline(args: argparse.Namespace) -> int:
    payload = _read_json_stdin()
    diagnoses = payload.get("diagnoses", payload)
    res = eng.compute_weights(
        diagnoses,
        vision_candidate=args.vision_candidate,
        target_recoef_domain=args.target_recoef_domain,
        job_domains=payload.get("job_domains"),
        existential_full_weight=args.existential_full,
    )
    if not res.validation["ok"]:
        _emit({"stage": "weights", "result": asdict(res)})
        return 2
    cards = eng.build_change_cards(
        res.weights_pct,
        personal_impact_by_id=payload.get("personal_impact_by_id") or {},
        include_wildcards=args.include_wildcards,
    )
    cards = eng.select_top_cards(cards, mode=args.mode)
    cards = eng.ensure_six_domain_min_one(cards)
    vision = eng.vision_ratio_for_age(args.age)
    axis = eng.absolute_time_axis(args.year)
    _emit({
        "stage": "pipeline",
        "weights": asdict(res),
        "vision_ratio": vision,
        "time_axis": axis,
        "cards": [asdict(c) for c in cards],
    })
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="research_cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    w = sub.add_parser("weights")
    w.add_argument("--vision-candidate", action="store_true")
    w.add_argument("--target-recoef-domain", default=None)
    w.add_argument("--existential-full", action="store_true")
    w.set_defaults(func=cmd_weights)

    vr = sub.add_parser("vision-ratio")
    vr.add_argument("--age", type=int, required=True)
    vr.set_defaults(func=cmd_vision_ratio)

    ta = sub.add_parser("time-axis")
    ta.add_argument("--year", type=int, required=True)
    ta.set_defaults(func=cmd_time_axis)

    so = sub.add_parser("source")
    so.add_argument("--domain", required=True)
    so.add_argument("--horizon", choices=["short", "mid", "long"], required=True)
    so.add_argument("--id", required=True)
    so.set_defaults(func=cmd_source)

    ls = sub.add_parser("list-sources")
    ls.add_argument("--domain", required=True)
    ls.add_argument("--horizon", choices=["short", "mid", "long"], required=True)
    ls.set_defaults(func=cmd_list_sources)

    ca = sub.add_parser("cards")
    ca.add_argument("--mode", choices=["brief", "standard", "detailed"], default="standard")
    ca.add_argument("--include-wildcards", action="store_true")
    ca.set_defaults(func=cmd_cards)

    sc = sub.add_parser("score")
    sc.add_argument("--weight", type=float, required=True)
    sc.add_argument("--horizon", choices=["short", "mid", "long"], required=True)
    sc.add_argument("--impact", choices=["high", "mid", "low"], required=True)
    sc.set_defaults(func=cmd_score)

    sch = sub.add_parser("self-check")
    sch.set_defaults(func=cmd_self_check)

    mn = sub.add_parser("missing-notice")
    mn.add_argument("--present", default="", help="comma-separated diagnosis keys present")
    mn.set_defaults(func=cmd_missing_notice)

    pi = sub.add_parser("pipeline")
    pi.add_argument("--vision-candidate", action="store_true")
    pi.add_argument("--target-recoef-domain", default=None)
    pi.add_argument("--existential-full", action="store_true")
    pi.add_argument("--year", type=int, required=True)
    pi.add_argument("--age", type=int, required=True)
    pi.add_argument("--mode", choices=["brief", "standard", "detailed"], default="standard")
    pi.add_argument("--include-wildcards", action="store_true")
    pi.set_defaults(func=cmd_pipeline)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
