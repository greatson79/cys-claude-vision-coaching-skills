"""라운드 1 검증 — 신규 10개 임의 프롬프트 결정론 라우팅 시뮬레이션.

각 프롬프트에 대해 결정론 모듈이 산출해야 하는 *기대값*을 명시하고
실제 산출이 일치하는지 자동 검증. 일치하지 않으면 결함을 출력한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import realm_balance as rb  # noqa: E402


PROMPTS = [
    {
        "id": "P1",
        "text": "박사님이 직접 본인 비전을 점검하고 싶다. 미래학자·담임목사·아빠·남편 4역할을 합쳐 한국 사회 변혁을 위한 미래 통찰력 공급이 비전이다.",
        "triple": ("O", "O", "O"),
        "expect_type": "C",
        "expect_address": "박사님",
        "expect_diag_name": "건강한 비전",
        "expect_special_substrings": [],
    },
    {
        "id": "P2",
        "text": "저는 IT 스타트업으로 큰 부를 쌓아 50대에 은퇴하는 게 비전입니다. 가족 시간은 못 챙겨도 어쩔 수 없어요.",
        "triple": ("O", "X", "X"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "개인 욕망",
        "expect_special_substrings": [],
    },
    {
        "id": "P3",
        "text": "100점 만점으로 환산해서 점수 좀 알려주세요.",
        "triple": None,
        "expect_type": "A",  # 키워드 없이 단독 정량화 요청
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["quantification"],
    },
    {
        "id": "P4",
        "text": "3겹 다이어그램이 뭔가요? 어떻게 작동하는 도구입니까?",
        "triple": None,
        "expect_type": "META",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "P5",
        "text": "절대로 다시는 가난한 삶을 살지 않겠다 — 이게 제 비전입니다.",
        "triple": ("M", "X", "X"),  # 부정형 — 명료화 전이지만 보수적 진단 = ✗✗✗
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "비전 아님",  # 부정형은 X로 환원 시 결국 XXX
        "expect_special_substrings": ["negative_vision"],
    },
    {
        "id": "P6",
        "text": "저는 비전이 없어요. 무엇을 비전으로 삼아야 할지 모르겠어요.",
        "triple": None,
        "expect_type": "EMPTY",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "P7",
        "text": "후보 A: 의사, 후보 B: 선교사, 후보 C: 작가 셋 중 어느 것이 가장 균형 잡힌 비전인가요?",
        "triple": None,
        "expect_type": "B",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "P8",
        "text": "ikigai 모델하고 박사님 3겹 다이어그램하고 어떻게 다른가요?",
        "triple": None,
        "expect_type": "META",  # '어떻게 ~' 메타 질문 + ikigai 외부 모델 특수 케이스
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["external_model"],
    },
    {
        "id": "P9",
        "text": "교회 청년부 30명 대상 1시간 30분 세미나 진행 흐름을 짜주세요.",
        "triple": None,
        "expect_type": "D",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "P10",
        "text": "자녀가 좋은 의사가 되어 가난한 사람들을 돕는 게 제 비전입니다.",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["other_oriented"],
    },
]


def run() -> tuple[int, int, list[str]]:
    passed = 0
    failed = 0
    failures: list[str] = []

    for p in PROMPTS:
        result = rb.analyze(p["text"], triple=p["triple"])
        errs: list[str] = []

        if result.input_type != p["expect_type"]:
            errs.append(f"input_type {result.input_type} != {p['expect_type']}")
        if result.address != p["expect_address"]:
            errs.append(f"address {result.address} != {p['expect_address']}")

        expected_diag = p["expect_diag_name"]
        actual_diag = result.diagnosis.name if result.diagnosis else None
        if expected_diag != actual_diag:
            errs.append(f"diag {actual_diag} != {expected_diag}")

        sc_names = {c.name for c in result.special_cases}
        for must in p["expect_special_substrings"]:
            if must not in sc_names:
                errs.append(f"special case missing: {must}; got {sc_names}")

        if errs:
            failed += 1
            failures.append(f"{p['id']}: " + " | ".join(errs))
        else:
            passed += 1

    return passed, failed, failures


if __name__ == "__main__":
    passed, failed, failures = run()
    print(f"PASSED: {passed} / {passed + failed}")
    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    print("\n전 항목 PASS — 라운드 1 통과")
