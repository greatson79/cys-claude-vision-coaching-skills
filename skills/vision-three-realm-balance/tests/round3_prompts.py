"""라운드 3 검증 — 라운드 1·2와 *완전히 다른* 신규 10개 프롬프트.

특수 케이스 4종(외부 강요·그룹 비전·내세 비전·정량화)과 잔여 진단 패턴을 분포.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import realm_balance as rb  # noqa: E402


PROMPTS = [
    {
        "id": "R1",
        "text": "최윤식 박사 본인이 비전을 잃어버린 상태에서 점검하고 싶다. 미래학자·담임목사·아빠·남편 모든 역할에서 기쁨도 의미도 없다.",
        "triple": ("X", "X", "X"),
        "expect_type": "C",
        "expect_address": "박사님",
        "expect_diag_name": "비전 아님",
        "expect_special_substrings": [],
    },
    {
        "id": "R2",
        "text": "저는 베이커리 사장으로 동네 사람들에게 좋은 빵을 주며 본인도 빵 굽는 시간이 즐겁지만 인생 의미는 모르겠습니다.",
        "triple": ("O", "O", "X"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "정신적 가치 결여",
        "expect_special_substrings": [],
    },
    {
        "id": "R3",
        "text": "저는 그림 그리기를 평생 추구하며 영적으로도 만족하지만 가족·이웃과는 단절돼 혼자 작업실에 있는 시간이 대부분입니다.",
        "triple": ("O", "X", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "가족·세상 단절",
        "expect_special_substrings": [],
    },
    {
        "id": "R4",
        "text": "저는 부모가 시켜서 의대에 왔고 가족·환자에게 도움 되고 의사 윤리도 따르지만 본인은 매일이 죽고 싶을 만큼 괴롭습니다.",
        "triple": ("X", "O", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "자기 기쁨 부재",
        "expect_special_substrings": ["externally_imposed"],
    },
    {
        "id": "R5",
        "text": "부부 공동 비전으로 함께 다문화 가정을 돕는 사역을 하고 싶습니다. 어떻게 점검합니까?",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["group_vision"],
    },
    {
        "id": "R6",
        "text": "제 비전은 천국에서 영원히 하나님 영광을 찬양하는 것입니다.",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["eschatological"],
    },
    {
        "id": "R7",
        "text": "이 비전을 점수화 해서 100점 만점에 몇 점인지 알려주세요.",
        "triple": ("O", "O", "X"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "정신적 가치 결여",
        "expect_special_substrings": ["quantification"],
    },
    {
        "id": "R8",
        "text": "결과만 짧게 요약해서 알려주세요.",
        "triple": ("X", "O", "X"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "자기희생·세상일",
        "expect_special_substrings": ["quick_mode"],
    },
    {
        "id": "R9",
        "text": "회사에서는 매출 1조 달성이 비전이고 가정에서는 좋은 아빠가 되는 게 비전입니다.",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["role_split"],
    },
    {
        "id": "R10",
        "text": "최윤식 박사 본인이 미래학자 역할에서만 보면 어떨지 점검 — 학문적 영감은 있고 사회 기여도 있는데 본인 즐거움은 줄어들었다.",
        "triple": ("X", "O", "O"),
        "expect_type": "C",
        "expect_address": "박사님",
        "expect_diag_name": "자기 기쁨 부재",
        "expect_special_substrings": ["role_split"],
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
    print("\n전 항목 PASS — 라운드 3 통과")
