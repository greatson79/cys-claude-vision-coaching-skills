"""라운드 4 — 라운드 1·2·3과 *완전히 다른* 신규 10개 엣지 시나리오.

특히 △ 환원·박사 코치 D 케이스 호칭 override·인용 정확성·복합 특수 케이스를 노린다.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib import realm_balance as rb  # noqa: E402


PROMPTS = [
    # S1: 박사님이 청년부 코칭 진행자로 가는 케이스 — D 흐름, 호칭 "당신" override
    {
        "id": "S1",
        "text": "최윤식 박사 본인이 청년부 50명 대상 1시간 워크숍 진행 흐름을 짜야 한다.",
        "triple": None,
        "expect_type": "D",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    # S2: △ 단일 → ✗ 환원 후 가족·세상 단절
    {
        "id": "S2",
        "text": "저는 동물 보호 NGO 운영이 비전인데 가족이 지지하는지 애매합니다.",
        "triple": ("O", "M", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "가족·세상 단절",  # M → X로 환원
        "expect_special_substrings": [],
    },
    # S3: △ 두 개 → ✗✗○ 왜곡된 사명·질
    {
        "id": "S3",
        "text": "저는 매일 묵상 1시간이 비전이고 그 외 영역은 잘 모르겠습니다.",
        "triple": ("M", "M", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "왜곡된 사명·질",
        "expect_special_substrings": [],
    },
    # S4: 박사님 본인 OOX — 4역할 통합인데 정신적 가치 결여
    {
        "id": "S4",
        "text": "박사님 본인이 4역할 통합 비전 점검을 원한다. 본인 기쁨·가족 가치는 충만한데 영적 의미는 흐릿하다.",
        "triple": ("O", "O", "X"),
        "expect_type": "C",
        "expect_address": "박사님",
        "expect_diag_name": "정신적 가치 결여",
        "expect_special_substrings": [],
    },
    # S5: 환경 영역 추가 제안 — domain_extension 특수 케이스
    {
        "id": "S5",
        "text": "기존 3영역에 환경·지구 영역을 추가하면 어떨까요?",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["domain_extension"],
    },
    # S6: ikigai + 정량화 동시 — META 격상 + quantification 특수 케이스
    {
        "id": "S6",
        "text": "ikigai 모델 4영역으로 환산하면 100점 만점에 몇 점인지 알려주세요.",
        "triple": None,
        "expect_type": "META",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["external_model", "quantification"],
    },
    # S7: 청년부에서 비전 없는 학생 — D보다 EMPTY가 우선 (EMPTY > META > D > C > B > A)
    {
        "id": "S7",
        "text": "저는 비전이 없어요. 청년부 모임에서 어떻게 시작해야 할까요?",
        "triple": None,
        "expect_type": "EMPTY",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": [],
    },
    # S8: 부정형 + 타인 비전 동시 (이중 특수 케이스)
    {
        "id": "S8",
        "text": "자녀가 절대 부모처럼 가난해지지 않도록 만드는 게 제 비전입니다.",
        "triple": None,
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": None,
        "expect_special_substrings": ["negative_vision", "other_oriented"],
    },
    # S9: 시간 순서 + 점검 동시
    {
        "id": "S9",
        "text": "10년 후 박사학위, 20년 후 교수, 30년 후 사회변혁가가 되겠습니다.",
        "triple": ("O", "O", "O"),
        "expect_type": "A",
        "expect_address": "당신",
        "expect_diag_name": "건강한 비전",
        "expect_special_substrings": ["time_phased"],
    },
    # S10: 박사님 본인 X·O·X — 자기희생·세상일 (4역할 중 가족·세상만 만족)
    {
        "id": "S10",
        "text": "최윤식 박사 본인이 모든 시간을 가족·교회·후학에 쓰고 본인 즐거움도 영적 의미도 잃었다고 한다.",
        "triple": ("X", "O", "X"),
        "expect_type": "C",
        "expect_address": "박사님",
        "expect_diag_name": "자기희생·세상일",
        "expect_special_substrings": [],
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
    print("\n전 항목 PASS — 라운드 4 통과")
