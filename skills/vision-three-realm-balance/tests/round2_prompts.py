"""라운드 2 검증 — 라운드 1과 *완전히 다른* 신규 10개 프롬프트.

라운드 1 학습 흉내를 차단하기 위해 입력 유형 분포·특수 케이스 조합을
새로 짠다. 패턴 매트릭스 8개를 라운드 2가 모두 한 번 이상 다루도록 분배.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import realm_balance as rb  # noqa: E402


PROMPTS = [
    {
        "id": "Q1",
        "text": "저는 오케스트라 지휘자로 클래식 음악의 깊이를 회중에게 전하고 가족과도 매일 저녁을 보내며 음악적 영감을 추구합니다.",
        "triple": ("O", "O", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "건강한 비전",
        "expect_special_substrings": [],
    },
    {
        "id": "Q2",
        "text": "저는 군 장교가 되어 국가에 헌신하고 싶지만 가족·사회에 어떤 가치를 줄지 모르고 양심에도 자꾸 걸립니다.",
        "triple": ("O", "X", "X"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "개인 욕망",
        "expect_special_substrings": [],
    },
    {
        "id": "Q3",
        "text": "30년 동안 어머니 간병을 우선해서 살아왔습니다. 본인의 기쁨이나 영적 가치는 모르겠고 가족만 챙겼습니다.",
        "triple": ("X", "O", "X"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "자기희생·세상일",
        "expect_special_substrings": [],
    },
    {
        "id": "Q4",
        "text": "저는 매일 새벽 4시 기상해 성경 통독·금식하지만 가족은 지쳐있고 저 자신도 메마릅니다. 도덕적 기준만 높습니다.",
        "triple": ("X", "X", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "왜곡된 사명·질",
        "expect_special_substrings": [],
    },
    {
        "id": "Q5",
        "text": "비전이 뭐인지조차 모르겠어요. 어디서 시작해야 할까요.",
        "triple": None,
        "expect_type": "EMPTY",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "Q6",
        "text": "건강하지 않은 비전을 어떻게 알 수 있어요? 이 도구 활용법을 알려주세요.",
        "triple": None,
        "expect_type": "META",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "Q7",
        "text": "후보 1: 환경 활동가, 후보 2: 의료 봉사자, 후보 3: 교사 — 이 셋 중 어느 것이 가장 균형 잡혀 있나요?",
        "triple": None,
        "expect_type": "B",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "Q8",
        "text": "신학교 학생 50명 대상 2시간 워크숍을 진행하고 싶습니다.",
        "triple": None,
        "expect_type": "D",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    {
        "id": "Q9",
        "text": "박사님이 본인 비전으로 한국 교회의 미래 통찰력 공급을 점검하고 싶어한다. 그러나 가족에게 줄 시간이 없고 자기 즐거움도 줄어들고 있다.",
        "triple": ("X", "X", "O"),
        "expect_type": "C",
        "expect_address": "박사님",
        "expect_diag_name": "왜곡된 사명·질",
        "expect_special_substrings": [],
    },
    {
        "id": "Q10",
        "text": "10년 후 의사가 되고 20년 후 의료선교사가 되겠다는 단계별 비전입니다.",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["time_phased"],
    },
]


def run() -> tuple[int, int, list[str]]:
    passed = failed = 0
    failures: list[str] = []
    for p in PROMPTS:
        result = rb.analyze(p["text"], triple=p["triple"])
        errs: list[str] = []
        if result.input_type != p["expect_type"]:
            errs.append(f"input_type {result.input_type} != {p['expect_type']}")
        if result.address != p["expect_address"]:
            errs.append(f"address {result.address} != {p['expect_address']}")
        actual_diag = result.diagnosis.name if result.diagnosis else None
        if p["expect_diag_name"] != actual_diag:
            errs.append(f"diag {actual_diag} != {p['expect_diag_name']}")
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
    print("\n전 항목 PASS — 라운드 2 통과")
