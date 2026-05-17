#!/usr/bin/env python3
"""
vision-eight-training-areas — 결정론적 검증기 (Deterministic Validator)

목적: 8대 영역 명칭·순서·SMART 매핑·6대 행동 강령·8주 커리큘럼·입력 유형 분류·
      박사님 책 verbatim 인용 검증을 LLM 자연어 추론 없이 결정론적으로 수행.

사용:
    python3 validator.py self-test                  # 내부 일관성 자가 진단
    python3 validator.py area <번호>                # 영역 1~8 조회
    python3 validator.py week <주차>                # 8주 커리큘럼 1~8 조회
    python3 validator.py smart-map <역량>           # SMART 역량 → 8대 영역 매핑
    python3 validator.py classify "<사용자 요청>"   # 입력 유형 A/B/C/D 분류
    python3 validator.py codes                      # 6대 행동 강령 명칭 조회
    python3 validator.py verify-area-name <이름>    # 영역명 정확성 검사
    python3 validator.py list-all                   # 8대 영역 일괄 출력

설계 원칙: 사실 조회·번호 매핑·범위 검사·존재 검증은 LLM이 추론하지 못하게
하드코딩된 ground truth dict로 결정론 처리. SKILL.md가 이 함수를 호출하도록 명시.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional


# ============================================================================
# Ground Truth — 박사님 『미래준비학교』(2016) 기반 결정론 데이터
# ============================================================================

# 8대 영역 — 박사님 책 + vision-five-stages SKILL 교차 검증
# 출처: vision-five-stages/SKILL.md line 117-124 (8개 명칭·순서 그대로)
EIGHT_AREAS: list[dict] = [
    {
        "number": 1,
        "name": "균형 잡힌 영성",
        "core": "영적 직관력 + 정신적 가치 + 자아성찰",
        "source": "박사님 책 비전 훈련 8대 영역 ① — vision-five-stages 교차 확인",
        "verbatim_in_curriculum_quote": True,  # "균형적 영성 습관"으로 인용에 포함
        "linked_skill": "vision-mission-frame",
    },
    {
        "number": 2,
        "name": "건강한 사고",
        "core": "통찰력·창의적 문제 해결",
        "source": "박사님 책 비전 훈련 8대 영역 ② — 커리큘럼 인용 verbatim",
        "verbatim_in_curriculum_quote": True,
        "linked_skill": "vision-smart-five-competence (Sense + Method)",
    },
    {
        "number": 3,
        "name": "좋은 언어",
        "core": "논리적 말하기·글쓰기·가르침",
        "source": "박사님 책 비전 훈련 8대 영역 ③ — 커리큘럼 인용 verbatim",
        "verbatim_in_curriculum_quote": True,
        "linked_skill": "vision-smart-five-competence (Art)",
    },
    {
        "number": 4,
        "name": "좋은 관계",
        "core": "리더십·팔로워십·펠로우십·커뮤니케이션",
        "source": "박사님 책 비전 훈련 8대 영역 ④ — 커리큘럼 인용 verbatim",
        "verbatim_in_curriculum_quote": True,
        "linked_skill": "vision-smart-five-competence (Relationship)",
    },
    {
        "number": 5,
        "name": "효과적 학습",
        "core": "지식 업데이트·필터링·시뮬레이션",
        "source": "박사님 책 비전 훈련 8대 영역 ⑤ — 커리큘럼 인용 verbatim",
        "verbatim_in_curriculum_quote": True,
        "linked_skill": "vision-smart-five-competence (Sense 훈련 3)",
    },
    {
        "number": 6,
        "name": "효율적 실행",
        "core": "실패에서 학습 + 즉각 전략 변화 + 행동 발전",
        "source": "박사님 책 비전 훈련 8대 영역 ⑥ — 커리큘럼 인용 verbatim",
        "verbatim_in_curriculum_quote": True,
        "linked_skill": "vision-smart-five-competence (Method 업무)",
    },
    {
        "number": 7,
        "name": "지혜로운 재정 전략",
        "core": "3방패 + 3창 모델",
        "source": "박사님 책 비전 훈련 8대 영역 ⑦ — 커리큘럼 인용에 '지혜로운 재정 습관'",
        "verbatim_in_curriculum_quote": True,
        "linked_skill": "vision-financial-3shields-3windows",
    },
    {
        "number": 8,
        "name": "건강한 신체",
        "core": "100세 시대 신체 자본 관리",
        "source": (
            "박사님 책 8대 영역 ⑧ — vision-five-stages SKILL line 124 교차 확인. "
            "1년 커리큘럼 4단계 verbatim 인용에는 7개만 나열되나, "
            "박사님 책의 별도 8대 영역 분류표에 ⑧로 명시됨"
        ),
        "verbatim_in_curriculum_quote": False,  # 커리큘럼 인용에는 명시 안 됨
        "linked_skill": None,
    },
]

# SMART ↔ 8대 영역 매핑 (박사님 본인 분석 기반 SKILL 매핑표)
SMART_TO_AREAS: dict[str, list[int]] = {
    "Sense": [2, 5],      # 건강한 사고 + 효과적 학습
    "Method-thinking": [2],   # 건강한 사고 (인문학·역사·철학)
    "Method-work": [6],       # 효율적 실행 (일·정보 줄이기·아웃소싱)
    "Art": [3],               # 좋은 언어 (글쓰기·가르침 장인화)
    "Relationship": [4],      # 좋은 관계
    "Technology": [2],        # 건강한 사고 (도구 활용 측면)
    "SMART-independent": [1, 7, 8],  # 영성, 재정, 신체
}

# 6대 행동 강령 — 박사님 책 + vision-five-stages SKILL 교차 검증 (line 161-168)
SIX_CODES: list[dict] = [
    {"number": 1, "ko": "서두르지 마라",                         "en": "Take a Time"},
    {"number": 2, "ko": "멀리 보라",                             "en": "Foresee Futures"},
    {"number": 3, "ko": "비전을 품어라",                         "en": "Make a Vision"},
    {"number": 4, "ko": "계획을 짜라",                           "en": "Make a Plan"},
    {"number": 5, "ko": "어떻게 일할지 훈련하고 생각하라",        "en": "Train and Think about How To Work"},
    {"number": 6, "ko": "작은 일을 소중하게 하라",                "en": "Be Faithful with a Few Things"},
]

# 8주 커리큘럼 (1주 = 1영역)
WEEK_TO_AREA: dict[int, int] = {i + 1: i + 1 for i in range(8)}

# 입력 유형 분류 키워드 (정규식 OR 패턴)
INPUT_TYPE_RULES: list[dict] = [
    {
        "type": "D",
        "description": "커리큘럼·강의·청년부·셀모임 8주 구조 요청",
        "patterns": [
            r"커리큘럼", r"강의\s*자료", r"청년부", r"8\s*주", r"셀모임",
            r"여덟\s*주", r"강의안", r"교안",
        ],
    },
    {
        "type": "A",
        "description": "8대 영역 전체 점검·8개 점수·종합 훈련 계획",
        "patterns": [
            r"8\s*대\s*영역\s*전체", r"전체\s*점검", r"여덟\s*영역\s*전체",
            r"8\s*개\s*점수", r"8\s*개\s*영역.*점수", r"여덟\s*영역.*점수",
            r"훈련\s*계획\s*세워", r"전\s*영역", r"종합\s*훈련", r"통합\s*점검",
            r"영성.*사고.*언어.*관계",  # 다수 영역명 동시 등장
        ],
    },
    {
        "type": "C",
        "description": "박사님 본인 점검·자기 진단",
        "patterns": [
            r"박사님\s*본인", r"자기\s*진단", r"내\s*상태\s*진단",
            r"제\s*자가\s*진단", r"개인\s*점검",
        ],
    },
    {
        "type": "B",
        "description": "특정 1~2개 영역 약점 코칭",
        "patterns": [
            r"이\s*영역\s*약", r"코칭해\s*줘", r"이\s*영역\s*만", r"영역\s*하나",
            r"약점\s*영역", r"한\s*영역", r"이\s*부분\s*만",
        ],
    },
]

# 박사님 책 verbatim 핵심 인용 (불변)
VERBATIM_QUOTES: dict[str, str] = {
    "criterion": (
        "비전 훈련을 평가하는 기준은 무엇일까? 비전 훈련의 최종 결과물은 무엇일까? "
        "바로 기술의 향상과 습관의 형성이다. "
        "미래준비학교에서 실시하는 비전 훈련을 8대 영역으로 분류하여 실시한다."
    ),
    "curriculum_week4": (
        "비전 훈련 : 미래인재 조건 훈련. SMART Habit, 미래인재의 조건들 훈련: "
        "좋은 언어 습관, 좋은 관계 습관(리더십, 책임, 커뮤니케이션 훈련), "
        "건강한 사고 습관(통찰력, 창의적 문제 해결 능력 훈련), 균형적 영성 습관, "
        "효과적 학습 습관, 효율적 실행 습관, 지혜로운 재정 습관"
    ),
    "execution_definition": (
        "실행력이란 '실패를 통해 깨닫고, 즉각 전략을 변화시켜 행동을 발전시키는 것'"
        "이라고 필자는 정의한다."
    ),
    "comprehensive": (
        "8대 영역은 완전히 새로운 것이 아니라 일상에서 접하는 것들이다. "
        "이 중 몇 가지는 독자들도 이미 중요하다고 생각하고 있을 것이다. "
        "훈련을 받기도 했을 것이다. 그러나 이런 것들을 종합적으로 "
        "체계적이고 균형 있게 훈련하는 것이 중요하다."
    ),
    "leadership_followership_fellowship": (
        "리더십 훈련만이 아니라 팔로워십(Followership)과 펠로우십(Fellowship) "
        "훈련이 균형을 이루어야 한다."
    ),
}


# ============================================================================
# 결정론 함수 — LLM 자연어 추론 차단
# ============================================================================

@dataclass
class ValidationResult:
    ok: bool
    detail: str
    data: Optional[dict] = None


def get_area(number: int) -> ValidationResult:
    """영역 번호로 영역 정보 조회. 1~8 범위 외 입력은 자동 FAIL."""
    if not isinstance(number, int) or number < 1 or number > 8:
        return ValidationResult(
            ok=False,
            detail=f"FAIL — 영역 번호는 1~8만 허용. 입력: {number!r}",
        )
    area = EIGHT_AREAS[number - 1]
    return ValidationResult(ok=True, detail=f"영역 {number} 조회 성공", data=area)


def verify_area_name(name: str) -> ValidationResult:
    """영역명 일치 검증. 정확히 일치하지 않으면 가장 유사한 후보 제시."""
    name_norm = name.strip()
    for area in EIGHT_AREAS:
        if area["name"] == name_norm:
            return ValidationResult(
                ok=True,
                detail=f"PASS — 영역 {area['number']} '{area['name']}' 정확 일치",
                data=area,
            )
    # 부분 일치 후보 탐색
    candidates = []
    for area in EIGHT_AREAS:
        a_tokens = set(area["name"].split())
        in_tokens = set(name_norm.split())
        if a_tokens & in_tokens:
            candidates.append(area["name"])
    return ValidationResult(
        ok=False,
        detail=(
            f"FAIL — '{name_norm}'은 정확한 영역명 아님. "
            f"정확한 8개 영역명: {[a['name'] for a in EIGHT_AREAS]}. "
            f"부분 일치 후보: {candidates or '없음'}"
        ),
    )


def get_week(week: int) -> ValidationResult:
    """8주 커리큘럼 주차 → 영역 매핑. 1~8 범위 외 입력은 자동 FAIL."""
    if not isinstance(week, int) or week < 1 or week > 8:
        return ValidationResult(
            ok=False,
            detail=f"FAIL — 주차는 1~8만 허용. 입력: {week!r}",
        )
    area_num = WEEK_TO_AREA[week]
    area = EIGHT_AREAS[area_num - 1]
    return ValidationResult(
        ok=True,
        detail=f"{week}주차 → 영역 {area_num} '{area['name']}'",
        data={"week": week, "area_number": area_num, "area_name": area["name"], "area": area},
    )


def smart_to_areas(competence: str) -> ValidationResult:
    """SMART 역량명 → 연계 8대 영역 번호·이름 매핑."""
    key = competence.strip()
    aliases = {
        "S": "Sense", "Sense": "Sense", "sense": "Sense", "센스": "Sense", "감각": "Sense",
        "M": "Method-thinking", "Method": "Method-thinking",
        "Method-thinking": "Method-thinking", "Method-사고": "Method-thinking",
        "Method-work": "Method-work", "Method-업무": "Method-work",
        "A": "Art", "Art": "Art", "art": "Art", "예술": "Art",
        "R": "Relationship", "Relationship": "Relationship", "관계": "Relationship",
        "T": "Technology", "Technology": "Technology", "기술": "Technology",
        "독립": "SMART-independent", "SMART-independent": "SMART-independent",
    }
    if key not in aliases:
        return ValidationResult(
            ok=False,
            detail=(
                f"FAIL — 알 수 없는 SMART 키: {key!r}. "
                f"허용: {sorted(set(aliases.values()))}"
            ),
        )
    canonical = aliases[key]
    area_nums = SMART_TO_AREAS[canonical]
    areas = [EIGHT_AREAS[n - 1] for n in area_nums]
    return ValidationResult(
        ok=True,
        detail=f"{canonical} → 영역 {area_nums}",
        data={
            "smart": canonical,
            "area_numbers": area_nums,
            "area_names": [a["name"] for a in areas],
        },
    )


def classify_input(user_request: str) -> ValidationResult:
    """사용자 요청 → 입력 유형 A/B/C/D 분류 (D > A > C > B 우선순위 폭포)."""
    text = user_request.strip()
    if not text:
        return ValidationResult(ok=False, detail="FAIL — 빈 입력")
    for rule in INPUT_TYPE_RULES:
        for pat in rule["patterns"]:
            if re.search(pat, text):
                return ValidationResult(
                    ok=True,
                    detail=f"유형 {rule['type']} — '{pat}' 매칭",
                    data={"type": rule["type"], "description": rule["description"], "matched": pat},
                )
    # 매칭 없으면 기본 B (특정 영역 코칭) 가정 — 사용자 명시 추가 입력 권장
    return ValidationResult(
        ok=False,
        detail=(
            "FAIL — 키워드 매칭 실패. SKILL은 사용자에게 명시적 유형 선택을 요구해야 함. "
            "유형 A(전체 점검)·B(특정 영역)·C(자기 진단)·D(커리큘럼) 중 어느 것인지 질문."
        ),
    )


def get_codes() -> ValidationResult:
    """6대 행동 강령 일괄 조회."""
    return ValidationResult(ok=True, detail="6대 행동 강령", data={"codes": SIX_CODES})


def list_all_areas() -> ValidationResult:
    """8대 영역 일괄 출력 (LLM이 순서·이름을 재생성하지 않도록)."""
    return ValidationResult(
        ok=True,
        detail="8대 영역 (불변)",
        data={"areas": EIGHT_AREAS, "count": len(EIGHT_AREAS)},
    )


def get_verbatim(key: str) -> ValidationResult:
    """박사님 책 verbatim 인용 조회. LLM이 임의 변형하지 못하도록."""
    if key not in VERBATIM_QUOTES:
        return ValidationResult(
            ok=False,
            detail=f"FAIL — 알 수 없는 인용 키: {key!r}. 허용: {sorted(VERBATIM_QUOTES.keys())}",
        )
    return ValidationResult(
        ok=True,
        detail=f"verbatim 인용 — {key}",
        data={"key": key, "quote": VERBATIM_QUOTES[key]},
    )


def self_test() -> ValidationResult:
    """내부 일관성 자가 진단 — SKILL.md 배포 전 필수 통과."""
    failures = []

    # 1. 영역 8개·번호 1~8 연속
    if len(EIGHT_AREAS) != 8:
        failures.append(f"영역 수 불일치: {len(EIGHT_AREAS)} ≠ 8")
    for i, area in enumerate(EIGHT_AREAS):
        if area["number"] != i + 1:
            failures.append(f"영역 번호 불연속: 인덱스 {i} → number {area['number']}")

    # 2. SMART 매핑 영역 번호가 1~8 범위
    for smart, nums in SMART_TO_AREAS.items():
        for n in nums:
            if n < 1 or n > 8:
                failures.append(f"SMART '{smart}' 매핑 범위 이탈: {n}")

    # 3. 8주 커리큘럼 1~8 모두 존재
    for w in range(1, 9):
        if w not in WEEK_TO_AREA:
            failures.append(f"주차 누락: {w}")

    # 4. 6대 행동 강령 6개 + 번호 연속
    if len(SIX_CODES) != 6:
        failures.append(f"6대 행동 강령 수 불일치: {len(SIX_CODES)} ≠ 6")
    for i, c in enumerate(SIX_CODES):
        if c["number"] != i + 1:
            failures.append(f"강령 번호 불연속: 인덱스 {i} → {c['number']}")

    # 5. verbatim 키 모두 비어있지 않음
    for k, v in VERBATIM_QUOTES.items():
        if not v.strip():
            failures.append(f"verbatim 비어있음: {k}")

    # 6. 입력 유형 4개 (A·B·C·D 모두)
    types_present = {r["type"] for r in INPUT_TYPE_RULES}
    if types_present != {"A", "B", "C", "D"}:
        failures.append(f"입력 유형 누락: {types_present}")

    if failures:
        return ValidationResult(
            ok=False,
            detail="FAIL — self-test 결함 발견",
            data={"failures": failures},
        )
    return ValidationResult(
        ok=True,
        detail="PASS — self-test 전 항목 통과 (8영역·SMART 매핑·8주·6강령·verbatim·4유형)",
        data={"checks": 6},
    )


# ============================================================================
# CLI
# ============================================================================

def _emit(result: ValidationResult) -> int:
    payload = {"ok": result.ok, "detail": result.detail}
    if result.data is not None:
        payload["data"] = result.data
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    cmd = argv[1]

    if cmd == "self-test":
        return _emit(self_test())
    if cmd == "list-all":
        return _emit(list_all_areas())
    if cmd == "codes":
        return _emit(get_codes())
    if cmd == "area" and len(argv) >= 3:
        try:
            return _emit(get_area(int(argv[2])))
        except ValueError:
            return _emit(ValidationResult(ok=False, detail=f"FAIL — 정수 아님: {argv[2]!r}"))
    if cmd == "week" and len(argv) >= 3:
        try:
            return _emit(get_week(int(argv[2])))
        except ValueError:
            return _emit(ValidationResult(ok=False, detail=f"FAIL — 정수 아님: {argv[2]!r}"))
    if cmd == "smart-map" and len(argv) >= 3:
        return _emit(smart_to_areas(argv[2]))
    if cmd == "classify" and len(argv) >= 3:
        return _emit(classify_input(argv[2]))
    if cmd == "verify-area-name" and len(argv) >= 3:
        return _emit(verify_area_name(argv[2]))
    if cmd == "verbatim" and len(argv) >= 3:
        return _emit(get_verbatim(argv[2]))

    print(f"FAIL — 알 수 없는 명령: {cmd}\n\n{__doc__}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
