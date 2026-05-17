#!/usr/bin/env python3
"""
vision-future-needs-prediction — run_pipeline.py

결정론 환원 모듈 3: 사용자 입력을 받아 ① 주제 분류 → ② 분석 contract 생성 →
③ 산출물 자가검증까지를 한 번에 연결하는 진입점.

SKILL.md "처리 흐름"의 1~7단계 중 결정론 환원 가능한 부분(주제 분류·시간
범위 판정·고위험 프레이밍 감지·분석 contract 자동 생성·산출물 검증)을
파이썬으로 강제한다. LLM이 다시 자연어로 추론하지 못한다.

사용:
    # 1) 사전 contract 산출(분석 본문 작성 전)
    python3 run_pipeline.py contract --topic "주제 문장" [--years 10]

    # 2) 분석 본문 작성 후 검증
    python3 run_pipeline.py verify --topic "주제 문장" --file output.md [--years 10]
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(THIS_DIR, "topic_classifier.py")
VALIDATOR = os.path.join(THIS_DIR, "output_validator.py")


def run_classifier(topic: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, CLASSIFIER, topic],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def make_contract(topic: str, years: int) -> dict[str, Any]:
    cls = run_classifier(topic)
    if cls.get("detected_time_years") is not None:
        years = cls["detected_time_years"]
    contract = {
        "topic": topic,
        "time_years": years,
        "required_groups_axis1": cls["required_groups_axis1"],
        "required_domains_axis3": cls["required_domains_axis3"],
        "framing_warnings": cls["framing_warnings"],
        "time_mode_b_required": years >= 30,
        "time_mode_b_recommended": years >= 20 and years < 30,
        "unmatched_warning": cls.get("unmatched_warning"),
        "validator_args": {
            "time_years": years,
            "required_groups": ",".join(cls["required_groups_axis1"]),
            "required_domains": ",".join(cls["required_domains_axis3"]),
            "framing_warnings": ";".join(cls["framing_warnings"]),
        },
    }
    return contract


def verify_output(topic: str, years: int, file_path: str) -> dict[str, Any]:
    contract = make_contract(topic, years)
    args = contract["validator_args"]
    proc = subprocess.run(
        [
            sys.executable,
            VALIDATOR,
            "--file",
            file_path,
            "--time-years",
            str(args["time_years"]),
            "--topic",
            topic,
            "--required-groups",
            args["required_groups"],
            "--required-domains",
            args["required_domains"],
            "--framing-warnings",
            args["framing_warnings"],
        ],
        capture_output=True,
        text=True,
    )
    return {
        "contract": contract,
        "validation": json.loads(proc.stdout) if proc.stdout.strip() else {"pass": False, "error": proc.stderr},
        "exit_code": proc.returncode,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    c_contract = sub.add_parser("contract", help="사전 분석 contract 산출")
    c_contract.add_argument("--topic", required=True)
    c_contract.add_argument("--years", type=int, default=10)

    c_verify = sub.add_parser("verify", help="산출물 자가검증")
    c_verify.add_argument("--topic", required=True)
    c_verify.add_argument("--years", type=int, default=10)
    c_verify.add_argument("--file", required=True)

    args = ap.parse_args()

    if args.cmd == "contract":
        out = make_contract(args.topic, args.years)
    elif args.cmd == "verify":
        out = verify_output(args.topic, args.years, args.file)
    else:
        return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
