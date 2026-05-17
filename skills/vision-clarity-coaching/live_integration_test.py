"""실 사용 흐름 통합 실행 테스트.

이전 검증(scenario_test.py·coach_response_audit.py)과 전혀 다른
10개 신규 프롬프트로 clarity_lib.py CLI를 subprocess로 실제 호출하여
각 단계의 출력을 캡처하고 4기준 감사한다.

이전 시나리오와의 차별:
  - 화자 직업·연령·맥락 모두 새로움
  - 발화 표현 다양화 (반말·존댓말·영문 일부 혼합)
  - 진단 보유 조합도 새로움 (readiness+values, multipleintel 단독 등)

검증 방식:
  - subprocess.run으로 clarity_lib.py CLI 호출
  - 표준 출력 JSON 파싱
  - 응답 조합 후 4기준 감사 (CLI 결과만으로 — 함수 직접 호출 불사용)

증거 기록: 각 단계의 CLI 명령·반환 JSON·감사 결과 모두 stdout으로.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
CLI = str(HERE / "clarity_lib.py")


def cli(*args: str) -> dict:
    """clarity_lib.py CLI 호출 — subprocess + JSON 파싱."""
    cmd = [PY, CLI, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


# 새 10개 시나리오 — 이전 두 라운드와 *완전히 다름*
NEW_SCENARIOS = [
    {
        "id": "L1",
        "title": "31세 카페 주인 — 진단 없음, 막연",
        "user": "31세 카페 주인입니다. 가게 운영은 안정됐는데 앞으로 뭘 더 해야 할지 모르겠습니다",
        "is_doctor": False,
        "title_str": "",
        "name": "",
        "diagnoses": "",
        "hint": "",
        "age": "31",
        "expect_type": "A",
        "expect_step4": "five_year",
        "expect_honorific": "선생님",
        "vision_sentence": (
            "한 동네의 일상에 머무는 공간을 정성껏 가꾸어 손님들에게 쉼을 건네는 것"
        ),
    },
    {
        "id": "L2",
        "title": "박사님 + values·readiness 진단 (일반 모드)",
        "user": "values 진단·readiness 진단 결과 있습니다. 강의 비전 한 문장으로 정리하고 싶어요",
        "is_doctor": True,
        "title_str": "",
        "name": "",
        "diagnoses": "values,readiness",
        "hint": "",
        "age": "56",
        "expect_type": "B",
        "expect_step4": "eighty",
        "expect_honorific": "박사님",
        "vision_sentence": (
            "변화의 시대를 사는 한국 리더들에게 미래를 분별하는 안목을 길러주는 강의를 펼치는 것"
        ),
    },
    {
        "id": "L3",
        "title": "28세 간호사 — ENTJ 단독",
        "user": "28세 간호사예요. MBTI ENTJ 나왔는데 더 큰 일을 하고 싶다는 마음만 들고 막연합니다",
        "is_doctor": False,
        "title_str": "",
        "name": "수민",
        "diagnoses": "mbti",
        "hint": "",
        "age": "28",
        "expect_type": "B",
        "expect_step4": "five_year",
        "expect_honorific": "수민님",
        "vision_sentence": (
            "환자 한 명의 회복에서 의료 시스템 개선으로 나아가는 길을 여는 것"
        ),
    },
    {
        "id": "L4",
        "title": "여러 직군 비교 요청 — 범위 밖",
        "user": "데이터 분석가랑 PM 직군 중 저한테 맞는 직업이 좋을까요?",
        "is_doctor": False,
        "title_str": "",
        "name": "",
        "diagnoses": "",
        "hint": "",
        "age": "29",
        "expect_type": "E",
        "expect_scope": "career-recommendation",
        "expect_honorific": "선생님",
    },
    {
        "id": "L5",
        "title": "45세 권사 — 진척 점검",
        "user": "45세 권사입니다. 작년에 세운 비전이 어디까지 왔나 점검을 받고 싶습니다",
        "is_doctor": False,
        "title_str": "권사",
        "name": "",
        "diagnoses": "",
        "hint": "",
        "age": "45",
        "expect_type": "E",
        "expect_scope": "progress-review",
        "expect_honorific": "권사님",
    },
    {
        "id": "L6",
        "title": "회사 결정 — 범위 밖 goal-reframing",
        "user": "A 회사 이직과 창업 두 가지 진로 중에 결정해야 할 시기입니다",
        "is_doctor": False,
        "title_str": "",
        "name": "",
        "diagnoses": "",
        "hint": "",
        "age": "34",
        "expect_type": "E",
        "expect_scope": "goal-reframing",
        "expect_honorific": "선생님",
    },
    {
        "id": "L7",
        "title": "박사님 + 다중지능·STRONG 압축 모드",
        "user": "다중지능·STRONG 결과 다 있어요. 압축으로 빠르게 가시죠",
        "is_doctor": True,
        "title_str": "",
        "name": "",
        "diagnoses": "multipleintel,strong",
        "hint": "compact",
        "age": "56",
        "expect_type": "C",
        "expect_step4": "eighty",
        "expect_honorific": "박사님",
        "vision_sentence": (
            "한국 교회와 사회에 미래 분별의 도구를 손에 쥐여 주는 일을 평생 이어가는 것"
        ),
    },
    {
        "id": "L8",
        "title": "22세 신학생 — 즉답",
        "user": "22살 신학생인데 내 비전 한 문장 바로 말해줘",
        "is_doctor": False,
        "title_str": "",
        "name": "준호",
        "diagnoses": "",
        "hint": "",
        "age": "22",
        "expect_type": "D",
        "expect_step4": "five_year",
        "expect_honorific": "준호님",
    },
    {
        "id": "L9",
        "title": "38세 워킹맘 — 진단 없음, 막연",
        "user": "38살 워킹맘이에요. 아이 키우면서 내 인생 방향을 모르겠어요",
        "is_doctor": False,
        "title_str": "",
        "name": "",
        "diagnoses": "",
        "hint": "",
        "age": "38",
        "expect_type": "A",
        "expect_step4": "five_year",
        "expect_honorific": "선생님",
        "vision_sentence": (
            "엄마이자 직장인으로서 다음 세대 여성들에게 가능한 균형의 길을 보여주는 것"
        ),
    },
    {
        "id": "L10",
        "title": "72세 — 노년 비전 재정립",
        "user": "72세입니다. 인생 마지막 장에서 무엇을 남길지 정리하고 싶습니다",
        "is_doctor": False,
        "title_str": "장로",
        "name": "",
        "diagnoses": "",
        "hint": "",
        "age": "72",
        "expect_type": "A",
        "expect_step4": "eighty",
        "expect_honorific": "장로님",
        "vision_sentence": (
            "한 평생 받은 은혜를 다음 세대 청년들의 일상에 흘려보내는 것"
        ),
    },
]


def run_scenario(sc: dict) -> dict:
    """한 시나리오 — CLI 호출 시퀀스 실 실행."""
    print(f"\n{'─' * 70}")
    print(f"[Scenario {sc['id']}] {sc['title']}")
    print(f"  user> {sc['user']}")

    issues: list[str] = []
    transcript: list[dict] = []

    # Step 1. 호칭 결정 — 실 CLI 호출
    cmd_args = [
        "honorific",
        "--doctor", "true" if sc["is_doctor"] else "false",
        "--title", sc["title_str"],
        "--name", sc["name"],
    ]
    r = cli(*cmd_args)
    honorific = r["honorific"]
    print(f"  $ clarity_lib.py {' '.join(cmd_args)}")
    print(f"    → honorific = {honorific!r}")
    transcript.append({"step": "honorific", "result": r})
    if honorific != sc["expect_honorific"]:
        issues.append(f"호칭 불일치 (got {honorific}, expected {sc['expect_honorific']})")

    # Step 2. 입력 유형 — 실 CLI 호출
    cmd_args = [
        "input_type",
        "--text", sc["user"],
        "--diagnoses", sc["diagnoses"],
        "--hint", sc["hint"],
    ]
    r = cli(*cmd_args)
    print(f"  $ clarity_lib.py input_type ...")
    print(f"    → type={r['type']}, scope_out={r['scope_out']}, reason={r['reason']}")
    transcript.append({"step": "input_type", "result": r})
    if r["type"] != sc["expect_type"]:
        issues.append(f"유형 불일치 (got {r['type']}, expected {sc['expect_type']})")
    if sc.get("expect_scope") and r["scope_out"] != sc["expect_scope"]:
        issues.append(f"scope_out 불일치 (got {r['scope_out']}, expected {sc['expect_scope']})")

    # Step 3. 세션 시작 문구 — 실 CLI 호출
    r = cli("opening")
    opening = r["opening"]
    print(f"  $ clarity_lib.py opening")
    print(f"    → (length={len(opening)}, prefix={opening[:50]!r}...)")
    transcript.append({"step": "opening", "result": r})

    # 응답 텍스트 누적
    response_pieces = [opening]

    # 범위 밖이면 여기서 종료 + 안내 텍스트
    if r := next((t for t in transcript if t["step"] == "input_type"), None):
        if r["result"]["type"] == "E":
            redirect = r["result"]["scope_out"]
            scope_msg = (
                f"{honorific}이 원하시는 것이 비전 자체를 새로 발굴하는 "
                f"것인가요, 아니면 vision-{redirect} 쪽이 더 적합할까요?"
            )
            response_pieces.append(scope_msg)
            print(f"    → scope_out redirect: vision-{redirect}")
            transcript.append({
                "step": "scope_out_redirect",
                "redirect": redirect,
                "text": scope_msg,
            })
            return _finalize(sc, response_pieces, transcript, issues)

    # Step 4. 진단별 통합 질문 — 보유 시 실 CLI 호출
    if sc["diagnoses"]:
        for key in sc["diagnoses"].split(","):
            key = key.strip()
            args = ["diag_step", "--key", key]
            r = cli(*args)
            print(f"  $ clarity_lib.py {' '.join(args)}")
            print(f"    → step={r['step']}, valid={r['valid']}")
            transcript.append({"step": f"diag_step[{key}]", "result": r})
            if not r["valid"]:
                issues.append(f"진단 키 {key} 미지원")
                continue

            type_num = "4" if (key == "enneagram" and sc.get("enneagram_num")) else ""
            args = ["diag_question", "--key", key, "--honorific", honorific, "--type_num", type_num]
            r = cli(*args)
            print(f"  $ clarity_lib.py diag_question --key {key} ...")
            print(f"    → {r['question'][:70]}...")
            transcript.append({"step": f"diag_question[{key}]", "result": r})
            response_pieces.append(r["question"])

    # Step 5. Step4 질문 — 실 CLI 호출
    args = ["step4", "--age", sc["age"], "--honorific", honorific]
    r = cli(*args)
    print(f"  $ clarity_lib.py {' '.join(args)}")
    print(f"    → chosen={r['chosen']}, q={r['primary_question'][:60]}...")
    transcript.append({"step": "step4", "result": r})
    if sc.get("expect_step4") and r["chosen"] != sc["expect_step4"]:
        issues.append(f"Step4 분기 불일치 (got {r['chosen']}, expected {sc['expect_step4']})")
    response_pieces.append(r["primary_question"])

    # Step 6. Step 5 — vision_sentence 검증 + 확인 반영 (가상 시점)
    if "vision_sentence" in sc:
        sent = sc["vision_sentence"]
        args = ["validate_sentence", "--sentence", sent]
        r = cli(*args)
        print(f"  $ clarity_lib.py validate_sentence ...")
        print(f"    → structure_ok={r['structure_ok']}, issues={r['issues']}")
        transcript.append({"step": "validate_sentence", "result": r})
        if not r["structure_ok"]:
            issues.append(f"Step5 구조 위반: {r['issues']}")

        args = ["step5_check", "--honorific", honorific, "--sentence", sent]
        r = cli(*args)
        print(f"  $ clarity_lib.py step5_check ...")
        print(f"    → {r['check'][:80]}...")
        transcript.append({"step": "step5_check", "result": r})
        response_pieces.append(r["check"])

    return _finalize(sc, response_pieces, transcript, issues)


def _finalize(sc: dict, pieces: list[str], transcript: list, issues: list) -> dict:
    """4기준 감사 — 응답 전문 합본을 CLI로 점검."""
    body = "\n\n".join(pieces)

    # detect_assertive — CLI 호출
    r = cli("detect_assertive", "--text", body)
    print(f"  $ clarity_lib.py detect_assertive (body 전문 검사)")
    print(f"    → assertive hits = {len(r['hits'])}")
    if r["hits"]:
        issues.append(f"C4 단정형 검출: {r['hits']}")

    # emoji_check — CLI 호출
    r = cli("emoji_check", "--text", body)
    print(f"  $ clarity_lib.py emoji_check (body 전문 검사)")
    print(f"    → is_clean = {r['is_clean']}, violations = {r['violations']}")
    if not r["is_clean"]:
        issues.append(f"C4 이모지 위반: {r['violations']}")

    ok = len(issues) == 0
    print(f"  >> 결과: {'PASS' if ok else 'FAIL'} ({len(pieces)} pieces, body {len(body)}자)")
    for it in issues:
        print(f"     ✗ {it}")

    return {
        "id": sc["id"],
        "ok": ok,
        "body": body,
        "pieces": pieces,
        "transcript": transcript,
        "issues": issues,
    }


def main() -> int:
    print("=" * 70)
    print("실 사용 흐름 통합 실행 테스트 (live integration)")
    print("=" * 70)
    print("이전 두 라운드와 *전혀 다른* 10개 신규 프롬프트로,")
    print("clarity_lib.py CLI를 subprocess로 실 호출 → JSON 파싱 → 합성 → 4기준 감사.")

    results = [run_scenario(sc) for sc in NEW_SCENARIOS]

    print("\n" + "=" * 70)
    print("최종 결과")
    print("=" * 70)
    n_pass = sum(1 for r in results if r["ok"])
    for r in results:
        flag = "PASS" if r["ok"] else "FAIL"
        print(f"  [{r['id']}] {flag}  body={len(r['body'])}자  issues={len(r['issues'])}")
    print(f"\nTotal: {n_pass}/{len(results)} PASS")

    if n_pass != len(results):
        return 1
    print("\n✓ 모든 10개 신규 시나리오 — 실 CLI 호출 기반 4기준 감사 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
