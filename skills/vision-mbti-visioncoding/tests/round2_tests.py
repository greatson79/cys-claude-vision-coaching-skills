#!/usr/bin/env python3
"""
vision-mbti-visioncoding ROUND 2 검증 테스트 — 10개 *완전히 새로운* 사용자 시나리오.

ROUND 1과 *겹치지 않는* 자연어 명령 시나리오. 실제 사용자 입력 형태로 검증.
각 시나리오에서 엔진이 산출해야 할 결과를 명세하고 ASSERT.
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
        capture_output=True, timeout=10,
    )
    try:
        return json.loads(proc.stdout.decode().strip())
    except json.JSONDecodeError:
        return {"_raw": proc.stdout.decode(), "_err": proc.stderr.decode()}


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f"  -- {detail}" if not condition and detail else ""))
    return condition


def main():
    failures = []

    # 시나리오 S1 — 사용자: "Q01~Q20: A B A B A A B A B A B A B A B A B A B A 결과 알려줘"
    # 이항 채점 시뮬레이션
    pattern_s1 = ["A","B","A","B","A","A","B","A","B","A","B","A","B","A","B","A","B","A","B","A"]
    answers = {f"Q{i+1:02d}": pattern_s1[i] for i in range(20)}
    r = call(["analyze"], json.dumps({"mode": "binary", "answers": answers}))
    # EI: ABABA = A3 B2 → E
    # SN: ABABA = A3 B2 → S
    # TF: BABAB = A2 B3 → F
    # JP: ABABA = A3 B2 → J
    # → ESFJ
    cond = r.get("status") == "ok" and r.get("primary_type") == "ESFJ"
    if not check("S1 이항 패턴 ABABA계열 → ESFJ", cond,
                 f"primary={r.get('primary_type')}"):
        failures.append(("S1", r))

    # 시나리오 S2 — 사용자: "ESFJ의 grip state 자세히 설명해줘"
    r = call(["lookup", "ESFJ"])
    cond = (r.get("type") == "ESFJ"
            and "Ti" in r.get("inferior_grip", "")
            and "Quenk 2002" in r.get("inferior_grip", ""))
    if not check("S2 ESFJ grip = Ti grip (Quenk)", cond,
                 f"grip={r.get('inferior_grip')}"):
        failures.append(("S2", r))

    # 시나리오 S3 — 사용자: "이미 ESTP인 거 알아. 인지 기능 스택만 알려줘"
    r = call(["lookup", "ESTP"])
    stack = r.get("cognitive_stack", {})
    cond = (stack.get("dominant") == "Se"
            and stack.get("auxiliary") == "Ti"
            and stack.get("inferior") == "Ni")
    if not check("S3 ESTP 스택 = Se-Ti-Fe-Ni", cond, f"stack={stack}"):
        failures.append(("S3", r))

    # 시나리오 S4 — 사용자: "공백 들어간 'intj ' 받아줄 수 있어?"
    r = call(["lookup", "intj"])  # 소문자도
    cond = r.get("type") == "INTJ"
    if not check("S4 소문자 'intj' 정규화 → INTJ", cond, f"type={r.get('type')}"):
        failures.append(("S4", r))

    # 시나리오 S5 — 사용자: "ENFP랑 INTJ 비교해줘 — duality 짝이라고 하던데"
    r = call(["compare", "ENFP", "INTJ"])
    enfp = r.get("type_a", {})
    intj = r.get("type_b", {})
    cond = (enfp.get("type") == "ENFP" and intj.get("type") == "INTJ"
            and enfp.get("cognitive_stack", {}).get("string") == "Ne-Fi-Te-Si"
            and intj.get("cognitive_stack", {}).get("string") == "Ni-Te-Fi-Se")
    if not check("S5 ENFP/INTJ compare 스택", cond):
        failures.append(("S5", r))

    # 시나리오 S6 — 사용자가 답 안 한 채로: "Q01-Q19까지 답했는데 Q20 누락"
    answers_missing = {f"Q{i:02d}": "A" for i in range(1, 20)}
    r = call(["analyze"], json.dumps({"mode": "binary", "answers": answers_missing}))
    cond = (r.get("status") == "error"
            and any("Q20" in e and "누락" in e for e in r.get("errors", [])))
    if not check("S6 Q20 누락 오류 명시", cond, f"errors={r.get('errors')}"):
        failures.append(("S6", r))

    # 시나리오 S7 — 사용자: "INFJ가 인구의 몇 %인지 출처 포함해서"
    r = call(["lookup", "INFJ"])
    cond = (r.get("population_pct") == 1.5
            and "MBTI Manual" in r.get("sources_short", {}).get("population", "")
            and "mbti_manual_1998_3rd" in r.get("sources", {}))
    if not check("S7 INFJ 인구 1.5% + MBTI Manual 출처(단축+풀)", cond,
                 f"pct={r.get('population_pct')} short={r.get('sources_short', {}).get('population')}"):
        failures.append(("S7", r))

    # 시나리오 S8 — 사용자: "ENTJ의 Keirsey 명칭은?"
    r = call(["lookup", "ENTJ"])
    cond = (r.get("keirsey_label_en") == "Fieldmarshal"
            and r.get("keirsey_temperament") == "NT (Rational)")
    if not check("S8 ENTJ Keirsey = Fieldmarshal / NT", cond,
                 f"k={r.get('keirsey_label_en')} t={r.get('keirsey_temperament')}"):
        failures.append(("S8", r))

    # 시나리오 S9 — 사용자: "2축 동시 경계: EI 약 + TF 약, 나머지 강한 → 후보 4유형 줘"
    # EI: A=3 B=2 (약), TF: A=3 B=2 (약), SN: A=5 (강), JP: A=5 (강)
    binary9 = {
        "Q01": "A", "Q02": "A", "Q03": "A", "Q04": "B", "Q05": "B",
        "Q06": "A", "Q07": "A", "Q08": "A", "Q09": "A", "Q10": "A",
        "Q11": "A", "Q12": "A", "Q13": "A", "Q14": "B", "Q15": "B",
        "Q16": "A", "Q17": "A", "Q18": "A", "Q19": "A", "Q20": "A",
    }
    r = call(["analyze"], json.dumps({"mode": "binary", "answers": binary9}))
    cond = (r.get("status") == "ok"
            and r.get("primary_type") == "ESTJ"
            and set(r.get("border_axes", [])) == {"EI", "TF"}
            and set(r.get("candidate_types", [])) == {"ESTJ", "ISTJ", "ESFJ", "ISFJ"})
    if not check("S9 EI+TF 2축 경계 → 4후보", cond,
                 f"primary={r.get('primary_type')} borders={r.get('border_axes')} cands={r.get('candidate_types')}"):
        failures.append(("S9", r))

    # 시나리오 S10 — 사용자: "5점 척도로 EI=8, SN=22, TF=11, JP=20 → 결과랑 강도"
    r = call(["analyze"], json.dumps({
        "mode": "b2",
        "totals": {"EI": 8, "SN": 22, "TF": 11, "JP": 20}
    }))
    # EI: 8 < 15 → E, diff=7 → 강한
    # SN: 22 > 15 → N, diff=7 → 강한
    # TF: 11 < 15 → T, diff=4 → 보통
    # JP: 20 > 15 → P, diff=5 → 보통
    # → ENTP
    axis = r.get("axis_results", {})
    cond = (r.get("primary_type") == "ENTP"
            and axis.get("EI", {}).get("strength") == "강한"
            and axis.get("SN", {}).get("strength") == "강한"
            and axis.get("TF", {}).get("strength") == "보통"
            and axis.get("JP", {}).get("strength") == "보통"
            and r.get("border_axes") == [])
    if not check("S10 B-2 강·강·보·보 → ENTP", cond,
                 f"primary={r.get('primary_type')} strengths={[axis.get(a,{}).get('strength') for a in ['EI','SN','TF','JP']]}"):
        failures.append(("S10", r))

    print()
    if failures:
        print(f"FAIL: {len(failures)}/10 (실패: {[f[0] for f in failures]})")
        sys.exit(1)
    print("ROUND 2 ALL PASS: 10/10")


if __name__ == "__main__":
    main()
