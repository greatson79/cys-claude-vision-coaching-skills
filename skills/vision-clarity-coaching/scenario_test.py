"""10개 새 시나리오로 결정론 모듈을 종합 검증.

이전 검증과 전혀 다른 프롬프트로 구성. 사용자 첫 발화, 메타데이터,
진단 결과 보유 여부를 다양화한다.

각 시나리오는:
  1) 결정론 함수가 사양과 일치한 결정을 내리는가
  2) 응답 초안에 단정형·금지 이모지가 없는가
  3) Step 5 산출 문장이 5요소 구조를 통과하는가
"""

from __future__ import annotations

import json
import sys

import clarity_lib as L


SCENARIOS = [
    {
        "id": 1,
        "title": "30대 디자이너 — 진단 없음 막연 비전",
        "user": "27세 디자이너입니다. 회사 그만두고 뭘 해야 할지 모르겠어요",
        "meta": {},
        "diagnoses": [],
        "age": 27,
        "expected_type": "A",
        "expected_step4_kind": "five_year",
        "expected_honorific": "선생님",
    },
    {
        "id": 2,
        "title": "박사님 본인 — 모든 진단 + 압축 요청",
        "user": "단행본·강의·사역 통합 비전을 압축 모드로 빠르게 정리하고 싶습니다",
        "meta": {"is_doctor": True},
        "diagnoses": ["mbti", "enneagram", "values", "strong", "multipleintel"],
        "age": 56,
        "expected_type": "C",
        "expected_step4_kind": "eighty",
        "expected_honorific": "박사님",
    },
    {
        "id": 3,
        "title": "25세 청년 + INFJ 단일 진단",
        "user": "MBTI INFJ 결과 있어요. 비전 한 문장 찾고 싶어요",
        "meta": {"name": "지수"},
        "diagnoses": ["mbti"],
        "age": 25,
        "expected_type": "B",
        "expected_step4_kind": "five_year",
        "expected_honorific": "지수님",
    },
    {
        "id": 4,
        "title": "두 진로 중 선택 — 범위 밖",
        "user": "두 가지 진로 중에 뭘 결정해야 할까요?",
        "meta": {},
        "diagnoses": [],
        "age": 33,
        "expected_type": "E",
        "expected_scope_out": "goal-reframing",
        "expected_honorific": "선생님",
    },
    {
        "id": 5,
        "title": "현재 점검 — 범위 밖",
        "user": "지금까지 비전 진척 점검을 받고 싶습니다",
        "meta": {"title": "전도사"},
        "diagnoses": [],
        "age": 41,
        "expected_type": "E",
        "expected_scope_out": "progress-review",
        "expected_honorific": "전도사님",
    },
    {
        "id": 6,
        "title": "52세 목사 — 에니어그램 4번",
        "user": "에니어그램 4번 결과 있어요. 인생 후반 비전을 다시 잡고 싶습니다",
        "meta": {"title": "목사"},
        "diagnoses": ["enneagram"],
        "age": 52,
        "enneagram_num": 4,
        "expected_type": "B",
        "expected_step4_kind": "eighty",
        "expected_honorific": "목사님",
    },
    {
        "id": 7,
        "title": "19세 학생 — 직업 추천 요청",
        "user": "저한테 맞는 직업이 좋을까요? 추천해 주세요",
        "meta": {},
        "diagnoses": [],
        "age": 19,
        "expected_type": "E",
        "expected_scope_out": "career-recommendation",
        "expected_honorific": "선생님",
    },
    {
        "id": 8,
        "title": "35세 — 즉답 요청",
        "user": "내 비전 한 문장 바로 말해줘",
        "meta": {"name": "민호"},
        "diagnoses": [],
        "age": 35,
        "expected_type": "D",
        "expected_step4_kind": "five_year",
        "expected_honorific": "민호님",
    },
    {
        "id": 9,
        "title": "67세 — 다음 세대 전수",
        "user": "67세 은퇴 직전입니다. 자녀와 다음 세대에게 무엇을 남길지 막막합니다",
        "meta": {"title": "장로"},
        "diagnoses": [],
        "age": 67,
        "expected_type": "A",
        "expected_step4_kind": "eighty",
        "expected_honorific": "장로님",
    },
    {
        "id": 10,
        "title": "고3 입시생 — 진로 막막",
        "user": "고3인데 진로가 막막해요. 어디로 가야 할지 모르겠어요",
        "meta": {},
        "diagnoses": [],
        "age": 18,
        "expected_type": "A",
        "expected_step4_kind": "five_year",
        "expected_honorific": "선생님",
    },
]


# 가상 시나리오별 Step 5 산출 문장 (코치가 산출했다고 가정)
DRAFT_SENTENCES = {
    1: "사용자 중심 경험을 디자인하는 작업으로 한국 작은 가게들의 일상을 따뜻하게 바꾸는 것",
    2: "AGI 시대에 영성과 미래학을 잇는 통합 지혜를 한국 다음 세대에게 책과 강의로 전수하는 것",
    3: "내면의 통찰력을 살려 청소년 마음 회복을 돕는 글쓰기 사역을 이어가는 것",
    6: "예술적 감수성으로 교회 공동체에 새로운 예배 형식을 일으키는 것",
    8: "기술과 사람을 잇는 다리가 되어 중소기업의 디지털 전환을 돕는 것",
    9: "한국 교회 다음 세대에게 신앙의 유산을 일상의 본보기로 전수하는 것",
    10: "내가 좋아하는 영역을 끝까지 파고드는 학문의 길로 나아가는 것",
}


# 단정형 검출용 — 코치가 절대 송출하면 안 되는 표현 예시
ASSERTIVE_NEGATIVES = [
    "INFJ니까 청소년 사역이 잘 맞습니다",
    "에니어그램 4번이라서 예술 분야로 가야 한다",
    "MBTI 결과가 INTJ니까 전략 컨설팅 비전이 맞다",
    "8유형은 반드시 리더십 비전을 가져야 한다",
]


# 정상 (단정형 아닌) 응답 예시
NORMAL_RESPONSES = [
    "MBTI 결과가 '나답다'고 느껴진 부분이 있으셨나요?",
    "에니어그램 4번 결과를 보셨을 때 가장 공감되었던 부분은 어디일까요?",
    "STRONG 검사 결과에서 가장 마음에 닿았던 영역이 있으셨나요?",
]


def run() -> int:
    failures: list[str] = []

    print("=" * 70)
    print("10개 시나리오 — 결정론 분기 종합 검증")
    print("=" * 70)

    for sc in SCENARIOS:
        print(f"\n[Scenario #{sc['id']}] {sc['title']}")
        print(f"  user> {sc['user']}")

        # 1. 호칭 결정
        honorific = L.select_honorific(sc["meta"])
        ok = honorific == sc["expected_honorific"]
        print(f"  honorific = {honorific} (expected {sc['expected_honorific']}) {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"#{sc['id']} 호칭 불일치")

        # 2. 입력 유형 분류
        hint = "compact" if sc["expected_type"] == "C" else ""
        r = L.classify_input_type(sc["user"], sc["diagnoses"], hint)
        ok = r["type"] == sc["expected_type"]
        print(f"  input_type = {r['type']} (expected {sc['expected_type']}) {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"#{sc['id']} 입력 유형 불일치 — got {r['type']}")

        # 3. 범위 밖 시나리오는 여기서 종료
        if sc["expected_type"] == "E":
            ok = r["scope_out"] == sc["expected_scope_out"]
            print(f"  scope_out = {r['scope_out']} (expected {sc['expected_scope_out']}) {'OK' if ok else 'FAIL'}")
            if not ok:
                failures.append(f"#{sc['id']} scope_out 불일치")
            continue

        # 4. Step 4 질문 선택
        r4 = L.select_step4_question(sc["age"], honorific)
        ok = r4["chosen"] == sc["expected_step4_kind"]
        print(f"  step4_kind = {r4['chosen']} (expected {sc['expected_step4_kind']}) {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"#{sc['id']} step4 분기 불일치")

        # 5. 진단별 통합 질문 생성 (진단 보유 시)
        for key in sc["diagnoses"]:
            try:
                type_num = sc.get("enneagram_num") if key == "enneagram" else None
                q = L.render_diagnosis_question(key, honorific, type_num)
                a_hits = L.detect_assertive_phrases(q)
                e_hits = L.validate_emoji_usage(q)
                ok = len(a_hits) == 0 and e_hits["is_clean"]
                print(f"  diag_q[{key}] clean = {ok} (assertive={len(a_hits)}, emoji_clean={e_hits['is_clean']})")
                if not ok:
                    failures.append(f"#{sc['id']} {key} 통합 질문 위반")
            except ValueError as exc:
                failures.append(f"#{sc['id']} {key} ValueError: {exc}")
                print(f"  diag_q[{key}] ERROR: {exc}")

        # 6. Step 5 산출 문장 검증
        if sc["id"] in DRAFT_SENTENCES:
            sent = DRAFT_SENTENCES[sc["id"]]
            vs = L.validate_vision_sentence(sent)
            ok = vs["structure_ok"]
            print(f"  step5 sentence structure_ok = {ok}, issues = {vs['issues']}")
            if not ok:
                failures.append(f"#{sc['id']} Step5 구조 위반 — {vs['issues']}")

    # 7. 단정형 음성/양성 일반 점검
    print("\n[단정형 검출 일반 점검]")
    for txt in ASSERTIVE_NEGATIVES:
        hits = L.detect_assertive_phrases(txt)
        ok = len(hits) >= 1
        print(f"  '{txt[:30]}...' → assertive hits = {len(hits)} {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"단정형 미검출 — {txt!r}")

    print("\n[정상 응답 음성 점검]")
    for txt in NORMAL_RESPONSES:
        hits = L.detect_assertive_phrases(txt)
        ok = len(hits) == 0
        print(f"  '{txt[:30]}...' → hits = {len(hits)} {'OK' if ok else 'FAIL'}")
        if not ok:
            failures.append(f"정상 응답 오탐 — {txt!r}")

    # 8. 세션 시작 문구 일관성
    print("\n[세션 시작 문구 일관성]")
    op1 = L.render_opening_template()
    op2 = L.render_opening_template()
    op3 = L.render_opening_template()
    ok = op1 == op2 == op3
    print(f"  3회 호출 동일 = {ok}")
    if not ok:
        failures.append("opening 비결정론")

    # 9. 호칭별 step4 호칭 치환 일관성
    print("\n[호칭 치환 일관성]")
    for h in ["박사님", "선생님", "목사님", "전도사님", "지수님"]:
        r = L.select_step4_question(55, h)
        ok = h in r["primary_question"] and h in r["supplementary"]
        print(f"  honorific='{h}' → 모두 치환 {ok}")
        if not ok:
            failures.append(f"호칭 치환 누락 — {h}")

    # 10. 미지원 진단 키 처리
    print("\n[미지원 진단 키 처리]")
    r = L.map_diagnosis_to_step("unknown-key")
    ok = r["valid"] is False
    print(f"  unknown key valid=False {ok}")
    if not ok:
        failures.append("미지원 진단 키 valid 처리 실패")

    print("\n" + "=" * 70)
    if failures:
        print(f"실패 {len(failures)}건:")
        for f in failures:
            print("  -", f)
        return 1
    print("== 10개 시나리오 + 부수 점검 전체 PASS ==")
    return 0


if __name__ == "__main__":
    sys.exit(run())
