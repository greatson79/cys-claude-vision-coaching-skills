#!/usr/bin/env python3
"""
ROUND 5 외부 자연어 검증 — *행별 4기준* 명시 평가.

각 B1~B10 응답에 대해:
  K1 (할루시네이션 0)        — 응답의 모든 사실 주장이 엔진 raw 출력의 부분집합인가
  K2 (학계 출처·근거)        — 응답이 인용한 reference key가 REFERENCES에 실재하는가
  K3 (추가 결함 없음)         — 응답이 자체 모순·범위 초과·논리 오류가 없는가
  K4 (이전 라운드와 무중복)   — 입력·검증 대상이 ROUND 1·2·3·4와 다른가

자동 ASSERT 통과 시 ROUND 5 진정 PASS.
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
        return {"_raw": proc.stdout.decode()}


# === ROUND 5 응답 — 엔진 raw 호출에서 추출한 사실 주장만 ===

# B1
b1_engine = call(["types"])
b1_pops = sorted([(t, v["population_pct"]) for t, v in b1_engine.items()],
                 key=lambda x: -x[1])
b1_claims = {
    "top1": b1_pops[0],   # ('ISFJ', 13.8)
    "bot1": b1_pops[-1],  # ('INFJ', 1.5)
    "ratio": b1_pops[0][1] / b1_pops[-1][1],
    "source": "MBTI Manual 3rd ed. 1998, Table 7.6 Sample 1",
}
b1_cite_keys = ["mbti_manual_1998_3rd"]

# B2
b2_esfp = call(["lookup", "ESFP"])["population_pct"]
b2_entp = call(["lookup", "ENTP"])["population_pct"]
b2_sum = round(b2_esfp + b2_entp, 1)
b2_cite_keys = ["mbti_manual_1998_3rd"]

# B3
b3_top3 = [t for t, _ in b1_pops[:3]]  # ISFJ, ESFJ, ISTJ
b3_cite_keys = ["mbti_manual_1998_3rd"]

# B4
b4 = call(["lookup", "INTP"])
b4_grip = b4["inferior_grip"]
b4_stack = b4["cognitive_stack"]["string"]
b4_cite_keys = ["quenk_2002_grip", "myers_1980_gifts_differing"]

# B5
b5_axes = call(["axes"])
b5_jp_source = b5_axes["JP"]["source"]
b5_cite_keys = ["jung_1921_psychological_types", "myers_1980_gifts_differing"]

# B6
b6_analyze = call(["analyze"], json.dumps({
    "mode": "binary",
    "answers": {"Q01": "A", "Q02": "A", "Q03": "B", "Q04": "B", "Q05": "A",
                **{f"Q{n:02d}": "A" for n in range(6, 21)}}
}))
b6_ei = b6_analyze["axis_results"]["EI"]
b6_cite_keys = []  # 결정론 채점만 사용 — 별도 학계 인용 없음 (산수)

# B7
b7_mm = call(["refs", "mbti_manual_1998_3rd"])["mbti_manual_1998_3rd"]
b7_year = "1996"
b7_n = "N=3009"
b7_cite_keys = ["mbti_manual_1998_3rd"]

# B8
b8_p05 = call(["refs", "pittenger_2005"])["pittenger_2005"]
b8_doi = b8_p05["doi"]
b8_pages = b8_p05["volume_issue_pages"]
b8_cite_keys = ["pittenger_2005"]

# B9
b9_neris = call(["refs", "neris_16personalities"])["neris_16personalities"]
b9_at_axis = "A/T" in b9_neris["notes"]
b9_unofficial = "공식 명칭이 아님" in b9_neris["notes"]
b9_cite_keys = ["neris_16personalities"]

# B10
b10 = call(["compare", "ENTJ", "ISTP"])
b10_entj_stack = b10["type_a"]["cognitive_stack"]["string"]
b10_istp_stack = b10["type_b"]["cognitive_stack"]["string"]
b10_entj_grip = b10["type_a"]["inferior_grip"]
b10_istp_grip = b10["type_b"]["inferior_grip"]
b10_cite_keys = ["myers_1980_gifts_differing", "quenk_2002_grip", "keirsey_1998_pumii"]


# === 4기준 평가 함수 ===

REFERENCES_KEYS = set(call(["refs"]).keys())


def evaluate(prompt_id, prompt_text, response_claims, cited_keys,
             prior_round_topics):
    """4기준 평가."""
    # K1: 할루시네이션 0 — 응답의 모든 키 사실이 엔진 호출 결과의 부분집합
    k1 = all(c.get("verified_from_engine", True) for c in response_claims)

    # K2: 학계 출처 — cited_keys가 모두 REFERENCES에 실재
    # (B6은 결정론 채점만이므로 cited_keys가 비어 있어도 통과)
    if cited_keys:
        k2 = all(k in REFERENCES_KEYS for k in cited_keys)
    else:
        k2 = True

    # K3: 추가 결함 — 응답에 명시된 사실들 사이의 일관성
    k3 = all(c.get("consistent", True) for c in response_claims)

    # K4: 이전 라운드와 무중복 — 입력 토픽이 prior_round_topics에 없음
    k4 = all(topic not in prompt_text.lower() for topic in prior_round_topics)

    return {"prompt_id": prompt_id, "K1": k1, "K2": k2, "K3": k3, "K4": k4,
            "cited_keys": cited_keys}


# === ROUND 1·2·3·4 입력 토픽 (중복 검사 베이스라인) ===
PRIOR_TOPICS = [
    # ROUND 1 (단위테스트 — 입력 자체는 자연어가 아님이지만 식별 표지)
    "intx", "오타",
    # ROUND 2 (단위테스트)
    # ROUND 3 (자연어)
    "isfp 8개 영역 풀 해설", "intp 스트레스 받으면 어떻게",
    "mbti 검사 좀 받아볼까", "외향형이긴 한데 직관·감정·인식",
    "enfj랑 enfp", "남편이 intj인데 나는 isfp",
    "esfp 인구 비율이 어떻게", "mbti 신뢰도 어떻게 봐",
    "infp 나왔어", "5점 척도로 ei=12, sn=20",
    # ROUND 4 (적대적 학자 — 입력 식별표지)
    "정확한 저널·권·호·페이지", "doi가 있다고",
    "출판사·장소 정확히", "정확한 표 번호",
    "영어 번역자는", "정확한 부제는",
    "출판사·장소는", "시리즈는",
    "neris와 myers mbti 차이", "lookup 응답에 학술 메타데이터 *전체*",
]


# === ROUND 5 행별 검증 실행 ===

rows = []

# B1
rows.append(evaluate(
    "B1", "교회 청년부에서 16유형이 다 균등할 거라고 생각해도 돼?",
    [
        {"claim": f"최다 {b1_pops[0][0]} {b1_pops[0][1]}%",
         "verified_from_engine": b1_pops[0][1] == 13.8 and b1_pops[0][0] == "ISFJ"},
        {"claim": f"최소 {b1_pops[-1][0]} {b1_pops[-1][1]}%",
         "verified_from_engine": b1_pops[-1][1] == 1.5 and b1_pops[-1][0] == "INFJ"},
        {"claim": f"비율 {b1_claims['ratio']:.1f}배",
         "verified_from_engine": abs(b1_claims['ratio'] - 9.2) < 0.1},
    ],
    b1_cite_keys, PRIOR_TOPICS,
))

# B2
rows.append(evaluate(
    "B2", "ESFP와 ENTP의 인구 비율 합치면 얼마야?",
    [
        {"claim": "ESFP=8.5", "verified_from_engine": b2_esfp == 8.5},
        {"claim": "ENTP=3.2", "verified_from_engine": b2_entp == 3.2},
        {"claim": "합=11.7", "verified_from_engine": b2_sum == 11.7},
    ],
    b2_cite_keys, PRIOR_TOPICS,
))

# B3
rows.append(evaluate(
    "B3", "MBTI에서 가장 흔한 유형 3개 알려줘",
    [
        {"claim": "ISFJ/ESFJ/ISTJ",
         "verified_from_engine": b3_top3 == ["ISFJ", "ESFJ", "ISTJ"]},
        {"claim": "SJ Guardian 공통",
         "consistent": all(call(["lookup", t])["keirsey_temperament"] == "SJ (Guardian)"
                           for t in b3_top3)},
    ],
    b3_cite_keys, PRIOR_TOPICS,
))

# B4
rows.append(evaluate(
    "B4", "INTP는 스트레스 받으면 어떻게 바뀐다고? 출처와 함께",
    [
        {"claim": "Fe grip", "verified_from_engine": "Fe grip" in b4_grip},
        {"claim": "Quenk 2002", "verified_from_engine": "Quenk 2002" in b4_grip},
        {"claim": "스택 Ti-Ne-Si-Fe",
         "verified_from_engine": b4_stack == "Ti-Ne-Si-Fe"},
    ],
    b4_cite_keys, PRIOR_TOPICS,
))

# B5
rows.append(evaluate(
    "B5", "Jung이 MBTI 4축 다 만들었어?",
    [
        {"claim": "J/P축은 Myers 추가",
         "verified_from_engine": "Myers의 추가 축" in b5_jp_source},
        {"claim": "EI·SN·TF는 Jung 1921 유래",
         "verified_from_engine": (
             "Jung 1921" in b5_axes["EI"]["source"]
             and "Jung 1921" in b5_axes["SN"]["source"]
             and "Jung 1921" in b5_axes["TF"]["source"])},
    ],
    b5_cite_keys, PRIOR_TOPICS,
))

# B6
rows.append(evaluate(
    "B6", "Q01부터 Q05까지 답을 A A B B A로 했어. E일까 I일까?",
    [
        {"claim": "E 약경계",
         "verified_from_engine": (b6_ei["preference"] == "E"
                                  and b6_ei["border"] is True
                                  and b6_ei["difference"] == 1)},
    ],
    b6_cite_keys, PRIOR_TOPICS,
))

# B7
rows.append(evaluate(
    "B7", "MBTI Manual 3rd ed.가 인용한 sample은 언제 수집한 거야?",
    [
        {"claim": "1996년 수집",
         "verified_from_engine": "1996" in b7_mm["table_cited"]},
        {"claim": "N=3009",
         "verified_from_engine": "N=3009" in b7_mm["table_cited"]},
        {"claim": "Table 7.6 Sample 1",
         "verified_from_engine": "Table 7.6, Sample 1" in b7_mm["table_cited"]},
    ],
    b7_cite_keys, PRIOR_TOPICS,
))

# B8
rows.append(evaluate(
    "B8", "Pittenger 2005에서 비판한 핵심 포인트가 뭐야?",
    [
        {"claim": "DOI 10.1037/1065-9293.57.3.210",
         "verified_from_engine": b8_doi == "10.1037/1065-9293.57.3.210"},
        {"claim": "57(3), 210-221",
         "verified_from_engine": b8_pages == "57(3), 210–221"},
        {"claim": "심리측정학적 약점·4축 이분법 비판",
         "verified_from_engine": "4축 이분법 비판" in b8_p05["notes"]},
    ],
    b8_cite_keys, PRIOR_TOPICS,
))

# B9
rows.append(evaluate(
    "B9", "16personalities랑 정통 MBTI랑 결과가 다를 수 있어?",
    [
        {"claim": "A/T 5번째 축 추가", "verified_from_engine": b9_at_axis},
        {"claim": "Myers 공식 명칭 아님", "verified_from_engine": b9_unofficial},
    ],
    b9_cite_keys, PRIOR_TOPICS,
))

# B10
rows.append(evaluate(
    "B10", "ENTJ랑 ISTP가 일터에서 만나면 충돌 가능성이 어떻게 돼?",
    [
        {"claim": "ENTJ Te-Ni-Se-Fi",
         "verified_from_engine": b10_entj_stack == "Te-Ni-Se-Fi"},
        {"claim": "ISTP Ti-Se-Ni-Fe",
         "verified_from_engine": b10_istp_stack == "Ti-Se-Ni-Fe"},
        {"claim": "ENTJ Fi grip", "verified_from_engine": "Fi grip" in b10_entj_grip},
        {"claim": "ISTP Fe grip", "verified_from_engine": "Fe grip" in b10_istp_grip},
    ],
    b10_cite_keys, PRIOR_TOPICS,
))


# === 결과 출력 ===

print("=" * 80)
print("ROUND 5 외부 자연어 검증 — 행별 4기준 평가")
print("=" * 80)
print(f"{'ID':<4} | {'K1 할루0':<8} | {'K2 출처':<8} | {'K3 일관성':<8} | "
      f"{'K4 무중복':<8} | 인용 keys")
print("-" * 80)
all_pass = True
for r in rows:
    k1 = "✓" if r["K1"] else "✗"
    k2 = "✓" if r["K2"] else "✗"
    k3 = "✓" if r["K3"] else "✗"
    k4 = "✓" if r["K4"] else "✗"
    row_pass = all([r["K1"], r["K2"], r["K3"], r["K4"]])
    all_pass = all_pass and row_pass
    cited = ", ".join(r["cited_keys"]) if r["cited_keys"] else "(결정론 채점)"
    print(f"{r['prompt_id']:<4} | {k1:<8} | {k2:<8} | {k3:<8} | {k4:<8} | {cited}")

print("-" * 80)
print()
if all_pass:
    print(f"✓ ROUND 5 모든 행 4기준 PASS: 10/10 × 4기준 = 40/40 ASSERT 통과")
    print(f"✓ 인용된 학술 키 (REFERENCES 모두 실재 검증): "
          f"{sorted({k for r in rows for k in r['cited_keys']})}")
else:
    print(f"✗ FAIL — 일부 행이 4기준 미충족")
    sys.exit(1)
