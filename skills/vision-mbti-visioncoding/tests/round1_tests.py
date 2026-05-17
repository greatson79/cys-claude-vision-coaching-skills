#!/usr/bin/env python3
"""
vision-mbti-visioncoding ROUND 1 검증 테스트 — 10개 새 프롬프트.

이전 검증과 *완전히 다른* 시나리오로 설계. 엣지·할루시네이션 위험 지점 집중.
각 테스트: 엔진 호출 시뮬레이션 + 기대 결과 ASSERT.

PASS 조건:
  1) 모든 테스트가 100% 일치 (예상 = 실제)
  2) 결정론 산출이 학계 출처와 1:1 대조
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(os.path.dirname(HERE), "mbti_engine.py")


def call(cmd_args, stdin_payload=None):
    proc = subprocess.run(
        ["python3", ENGINE] + cmd_args,
        input=stdin_payload.encode() if stdin_payload else None,
        capture_output=True,
        timeout=10,
    )
    out = proc.stdout.decode().strip()
    err = proc.stderr.decode().strip()
    if proc.returncode != 0 and not out:
        return {"_rc": proc.returncode, "_err": err}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"_raw": out, "_err": err}


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f"  -- {detail}" if not condition and detail else ""))
    return condition


def main():
    failures = []

    # TEST 1: 오타 4글자 거부 — "INTX"
    r = call(["lookup", "INTX"])
    if not check("T1 INTX 거부", "error" in r and "16유형" in r.get("error", "")):
        failures.append(("T1", r))

    # TEST 2: 5점 척도 응답 누락 — Q01만 입력
    r = call(["analyze"], json.dumps({"mode": "scale", "answers": {"Q01": 3}}))
    if not check("T2 누락 응답 거부",
                 r.get("status") == "error" and any("누락" in e for e in r.get("errors", []))):
        failures.append(("T2", r))

    # TEST 3: 5점 척도 전부 3 → 4축 중립 → 후보 16개
    answers = {f"Q{n:02d}": 3 for n in range(1, 21)}
    r = call(["analyze"], json.dumps({"mode": "scale", "answers": answers}))
    cond = (r.get("status") == "ok"
            and len(r.get("neutral_axes", [])) == 4
            and len(r.get("candidate_types", [])) == 16
            and r.get("primary_type") is None)
    if not check("T3 전부3 → 4축중립·후보16", cond):
        failures.append(("T3", r))

    # TEST 4: 단일 축 경계 — EI만 약한 선호, 나머지 강한
    # EI: 3A 2B (이항 → I 약한 선호? 아니, A=3 B=2 → A쪽 = E, diff=1)
    # 실제: A=3 → E. 경계.
    binary = {
        "Q01": "A", "Q02": "A", "Q03": "A", "Q04": "B", "Q05": "B",  # EI: A3,B2 → E 약경계
        "Q06": "B", "Q07": "B", "Q08": "B", "Q09": "B", "Q10": "B",  # SN: B5 → N 강
        "Q11": "B", "Q12": "B", "Q13": "B", "Q14": "B", "Q15": "B",  # TF: B5 → F 강
        "Q16": "A", "Q17": "A", "Q18": "A", "Q19": "A", "Q20": "A",  # JP: A5 → J 강
    }
    r = call(["analyze"], json.dumps({"mode": "binary", "answers": binary}))
    cond = (r.get("status") == "ok"
            and r.get("primary_type") == "ENFJ"
            and r.get("border_axes") == ["EI"]
            and set(r.get("candidate_types", [])) == {"ENFJ", "INFJ"})
    if not check("T4 단일 EI 경계 → ENFJ + INFJ 후보", cond,
                 f"primary={r.get('primary_type')} border={r.get('border_axes')} cands={r.get('candidate_types')}"):
        failures.append(("T4", r))

    # TEST 5: B-1 합 != 5 거부 (EI 합=4)
    r = call(["analyze"], json.dumps({
        "mode": "b1",
        "counts": {"EI": {"E": 4, "I": 0}, "SN": {"S": 2, "N": 3},
                   "TF": {"T": 5, "F": 0}, "JP": {"J": 3, "P": 2}}
    }))
    cond = r.get("status") == "error" and any("EI" in e and "5" in e for e in r.get("errors", []))
    if not check("T5 B-1 합!=5 거부", cond):
        failures.append(("T5", r))

    # TEST 6: B-2 범위 초과 거부 (EI=30)
    r = call(["analyze"], json.dumps({
        "mode": "b2",
        "totals": {"EI": 30, "SN": 18, "TF": 8, "JP": 22}
    }))
    cond = r.get("status") == "error" and any("EI" in e and "25" in e for e in r.get("errors", []))
    if not check("T6 B-2 범위 초과 거부", cond):
        failures.append(("T6", r))

    # TEST 7: 두 유형 비교 — ENFJ vs ESTP (대각 유형)
    r = call(["compare", "ENFJ", "ESTP"])
    enfj_stack = r.get("type_a", {}).get("cognitive_stack", {}).get("string")
    estp_stack = r.get("type_b", {}).get("cognitive_stack", {}).get("string")
    cond = (enfj_stack == "Fe-Ni-Se-Ti" and estp_stack == "Se-Ti-Fe-Ni")
    if not check("T7 ENFJ/ESTP compare 스택", cond,
                 f"ENFJ={enfj_stack} ESTP={estp_stack}"):
        failures.append(("T7", r))

    # TEST 8: 인구 비율 합 ≈ 100 (MBTI Manual 3rd ed.)
    r = call(["types"], None)
    total_pct = sum(d["population_pct"] for d in r.values())
    cond = abs(total_pct - 100) < 0.5
    if not check("T8 인구비율 합≈100", cond, f"sum={total_pct:.2f}"):
        failures.append(("T8", total_pct))

    # TEST 9: 별명 출처 표기 — NERIS vs Keirsey 둘 다 존재 (sources_short 단축형)
    r = call(["lookup", "INFJ"])
    cond = ("16personalities" in r.get("sources_short", {}).get("neris_label", "")
            and "Keirsey" in r.get("sources_short", {}).get("keirsey_label", "")
            and r.get("neris_label_en") == "Advocate"
            and r.get("keirsey_label_en") == "Counselor")
    if not check("T9 별명 출처 NERIS+Keirsey 병기", cond):
        failures.append(("T9", r))

    # TEST 10: 인지 기능 스택 — Myers 1980 표준 검증 (모든 16유형)
    standard_stacks = {
        "INTJ": "Ni-Te-Fi-Se", "INTP": "Ti-Ne-Si-Fe",
        "ENTJ": "Te-Ni-Se-Fi", "ENTP": "Ne-Ti-Fe-Si",
        "INFJ": "Ni-Fe-Ti-Se", "INFP": "Fi-Ne-Si-Te",
        "ENFJ": "Fe-Ni-Se-Ti", "ENFP": "Ne-Fi-Te-Si",
        "ISTJ": "Si-Te-Fi-Ne", "ISFJ": "Si-Fe-Ti-Ne",
        "ESTJ": "Te-Si-Ne-Fi", "ESFJ": "Fe-Si-Ne-Ti",
        "ISTP": "Ti-Se-Ni-Fe", "ISFP": "Fi-Se-Ni-Te",
        "ESTP": "Se-Ti-Fe-Ni", "ESFP": "Se-Fi-Te-Ni",
    }
    all_ok = True
    mismatches = []
    for t, expected in standard_stacks.items():
        actual = call(["lookup", t]).get("cognitive_stack", {}).get("string")
        if actual != expected:
            all_ok = False
            mismatches.append(f"{t}: 기대 {expected}, 실제 {actual}")
    if not check("T10 16유형 인지기능 스택 (Myers 1980 표준)", all_ok,
                 "; ".join(mismatches)):
        failures.append(("T10", mismatches))

    print()
    if failures:
        print(f"FAIL: {len(failures)}/10 (실패: {[f[0] for f in failures]})")
        sys.exit(1)
    print("ROUND 1 ALL PASS: 10/10")


if __name__ == "__main__":
    main()
