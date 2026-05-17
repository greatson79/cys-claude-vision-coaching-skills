#!/usr/bin/env python3
"""ROUND B — ROUND A와 완전히 다른 10개 검증 프롬프트.

ROUND A 프롬프트와 의도적으로 겹치지 않도록 사용자 시나리오·확인 항목·
음성 어조·실패 케이스의 종류를 다르게 구성한다. 학습 회피·우회 시도를
배제한다.

실행:
    python3 tests/round_b_prompts.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TMP = Path("/tmp/vsw_round_b")
TMP.mkdir(parents=True, exist_ok=True)


def run(*args: str) -> tuple[int, str, str]:
    r = subprocess.run(
        ["python3", *args],
        capture_output=True,
        text=True,
    )
    return r.returncode, r.stdout, r.stderr


def write_answers(name: str, answers: dict) -> Path:
    p = TMP / f"{name}.json"
    p.write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


SCENARIOS = [
    {
        "id": "B01",
        "prompt": "사용자: 박사님 본인 비전 선언문 한번 만들어줘 — 이름은 '최윤식'으로.",
        "answers": {
            "F1_name": "박사님 본인",  # 그래도 실존 이름은 F1에 직접 적게 허용
            "F2_plausible": "AGI 침투와 한국 인구절벽으로 미래학·의미 시장이 첫 부흥기를 맞을 사회 변화",
            "F3_possible": "청년층의 의미 갈증으로 영성 공동체와 인문 르네상스가 살아나는 가능성",
            "F4_unexpected": "AI 영적 동반자가 기성 종교를 대체해 영적 분별이 핵심 사회 역량이 되는 가능성",
            "F5_problem": "AGI 시대 의미 위기와 미래 대비 무지를 해결하기 위해",
            "F6_interest": "미래학·기독교 신학·다음 세대 양육",
            "F7_talent": "Logical-Mathematical·Intrapersonal·Linguistic + 미래학 기술발달",
            "F8_personality": "INTJ + 에니어그램 5번 6번 날개 — 박사님 본인 데이터",
            "F9_work": "최윤식 박사 미래학자 본업·신학교 강의·교회 사역 (참고 사례)",
            "F10_value": "진리·지혜·정신적 가치가 살아있는",
            "F11_purposes": [
                "AGI 시대 미래학 단행본 5권",
                "한국 청년 강연 100회",
                "차세대 미래학자 양성",
                "통합 지혜 디지털 아카이브",
                "교회 청년부 비전 코칭 커리큘럼",
            ],
            "F12_date": "2026년 5월 17일",
        },
        "expect_validate_exit": 0,
        "expect_warn_message": "최윤식",  # F8,F9 본문에 실존 이름 포함 → WARN
    },
    {
        "id": "B02",
        "prompt": "사용자: F1부터 F12까지 필드 ID와 한글 라벨 매핑표 보여줘.",
        "lookup_cmd": ["fields"],
        "expect_keywords": [
            "F1_name", "F2_plausible", "F6_interest",
            "F11_purposes", "F12_date", "12",
        ],
    },
    {
        "id": "B03",
        "prompt": "사용자: 단일 필드 F7_talent 어떻게 답해야 하는지 자세히 알려줘.",
        "lookup_cmd": ["field", "F7_talent"],
        "expect_keywords": [
            "다중지능", "vision-multipleintel-visioncoding", "기술발달",
        ],
    },
    {
        "id": "B04",
        "prompt": "사용자: V2 검증 도구 — 진선미 검증 기준 다시 보여줘.",
        "lookup_cmd": ["tool", "V2"],
        "expect_keywords": ["진리(眞)", "올바름(善)", "아름다움(美)"],
    },
    {
        "id": "B05",
        "prompt": "사용자: Q1 인용 본문 한 번 결정론적으로 가져와봐.",
        "lookup_cmd": ["quote", "Q1"],
        "expect_keywords": [
            "통합 비전 선언문", "비전 디자인",
            "최윤식의 미래준비학교",
        ],
    },
    {
        "id": "B06",
        "prompt": "사용자: Voros 2003 Cone of Plausibility 출처 정보 가져와줘.",
        "lookup_cmd": ["source", "FS1"],
        "expect_keywords": ["Voros", "2003", "Foresight"],
    },
    {
        "id": "B07",
        "prompt": "사용자: 비전 선언문 다 채웠는데 Q11에 7개 적었어 — 너무 많은가?",
        "answers": {
            "F1_name": "정한나",
            "F2_plausible": "기후 위기 가속화로 지역 식량 시스템이 위협받고 도시 가족 농업이 부상하는 사회",
            "F3_possible": "탄소 중립 제도화로 지역 협력조합이 핵심 행위자가 되는 흐름",
            "F4_unexpected": "초대형 자연재해가 도시-농촌 식량망을 재편할 가능성",
            "F5_problem": "도시 가족의 식량 불안과 지역 단절",
            "F6_interest": "도시 농업·기후 정의·식량 주권",
            "F7_talent": "Naturalist·Intrapersonal·Linguistic + 도시 가드닝 기술",
            "F8_personality": "INFP 중재자형 + 에니어그램 4번(개인주의자) 5번 날개",
            "F9_work": "도시 농업 코디네이터·기후 교육 활동가·시민 식량 협동조합 매니저",
            "F10_value": "정의·생태·공동체가 살아있는",
            "F11_purposes": [
                "동네 옥상 정원 10곳 조성",
                "초등학교 식량 교육 정규 수업",
                "지역 협동조합 한 곳 창립",
                "기후 시민 워크숍 30회",
                "지자체 정책 제안서 5건",
                "친환경 식자재 직거래 시장 운영",
                "청년 농부 멘토링 5명",
            ],
            "F12_date": "2026년 5월 17일",
        },
        "expect_validate_exit": 0,
        "expect_warn_message": "권장 항목 수 5",
    },
    {
        "id": "B08",
        "prompt": "사용자: Q11이 비어 있어도 양식 출력은 되는지 보고 싶어.",
        "answers": {
            "F1_name": "이도현",
            "F2_plausible": "디지털 전환 가속화로 중소기업 70% 이상이 ERP/AI 활용을 강요받는 사회 변화",
            "F3_possible": "중소기업 디지털 전환을 돕는 외주 컨설팅 산업이 폭발적으로 성장하는 가능성",
            "F4_unexpected": "범국가적 사이버 침해 사건으로 디지털 신뢰가 일시 붕괴할 가능성",
            "F5_problem": "중소기업의 디지털 격차와 IT 인력 부재",
            "F6_interest": "기업 ERP·디지털 전환·중소기업 컨설팅",
            "F7_talent": "Logical-Mathematical·Linguistic·Interpersonal + 클라우드/SaaS 기술",
            "F8_personality": "ESTJ 경영자형 + 에니어그램 3번(성취가) 2번 날개",
            "F9_work": "중소기업 ERP 컨설턴트·디지털 전환 강사·도메인 SaaS 창업가",
            "F10_value": "효율·정직·공동체가 살아있는",
            "F11_purposes": [],
            "F12_date": "2026년 5월 17일",
        },
        "expect_validate_exit": 1,
        "expect_fail_message": "Purposes 항목이 부족",
    },
    {
        "id": "B09",
        "prompt": "사용자: 비전 선언문 양식의 결문 '부름을 받았습니다!' 결정론 렌더에서 정말 항상 나오나? 검증.",
        "render_mode": "C",
        "expect_keywords": ["부름을 받았습니다!"],
    },
    {
        "id": "B10",
        "prompt": "사용자: render --mode B로 답변 채워서 본문에 1번~5번 Purposes가 순서대로 들어가는지 보고 싶어.",
        "answers": {
            "F1_name": "최민지",
            "F2_plausible": "비대면 정신건강 서비스가 대중화되어 1차 케어가 디지털로 이동하는 사회",
            "F3_possible": "오프라인 회복 공동체가 도시 외곽 거점으로 부활하는 가능성",
            "F4_unexpected": "팬데믹급 정신건강 위기로 국가가 무료 상담을 의무화할 가능성",
            "F5_problem": "청년 우울·고립·정체성 위기",
            "F6_interest": "청년 정신건강·공동체·신앙",
            "F7_talent": "Interpersonal·Intrapersonal·Linguistic + 디지털 상담 도구",
            "F8_personality": "INFJ 옹호자형 + 에니어그램 2번(돕는이) 3번 날개",
            "F9_work": "청년 상담사·공동체 멘토·디지털 상담 플랫폼 기획자",
            "F10_value": "사랑·진리·공동체가 살아있는",
            "F11_purposes": [
                "청년 셀프케어 워크북 출간",
                "지역 회복 공동체 5곳 운영",
                "디지털 상담 플랫폼 시범 운영",
                "교회 청년부 정신건강 세미나 30회",
                "1:1 멘토링 50명",
            ],
            "F12_date": "2026년 5월 17일",
        },
        "render_after": True,
        "expect_validate_exit": 0,
        "expect_render_keywords": [
            "1. 청년 셀프케어 워크북 출간",
            "5. 1:1 멘토링 50명",
            "부름을 받았습니다",
        ],
    },
]


def evaluate(sc: dict, fails: list) -> None:
    sid = sc["id"]
    if "lookup_cmd" in sc:
        rc, out, err = run(str(SCRIPTS / "lookup.py"), *sc["lookup_cmd"])
        if rc != 0:
            fails.append(f"{sid} lookup 실패: {err}")
            return
        for kw in sc.get("expect_keywords", []):
            if kw not in out:
                fails.append(f"{sid} lookup 출력에 '{kw}' 누락")
        return
    if "render_mode" in sc and "answers" not in sc:
        rc, out, err = run(
            str(SCRIPTS / "render_template.py"),
            "--mode",
            sc["render_mode"],
        )
        if rc != 0:
            fails.append(f"{sid} render 실패: {err}")
            return
        for kw in sc.get("expect_keywords", []):
            if kw not in out:
                fails.append(f"{sid} render 출력에 '{kw}' 누락")
        return
    if "answers" in sc:
        path = write_answers(sid, sc["answers"])
        rc, out, err = run(
            str(SCRIPTS / "validate_output.py"),
            "--answers",
            str(path),
        )
        if rc != sc.get("expect_validate_exit", 0):
            fails.append(
                f"{sid} validate exit={rc}, expect={sc.get('expect_validate_exit')}"
                f"\n   stdout={out[:400]}"
            )
        if sc.get("expect_fail_message") and sc["expect_fail_message"] not in out:
            fails.append(
                f"{sid} validate 출력에 '{sc['expect_fail_message']}' 누락"
            )
        if sc.get("expect_warn_message") and sc["expect_warn_message"] not in out:
            fails.append(
                f"{sid} validate 출력에 '{sc['expect_warn_message']}' 경고 누락"
            )
        if sc.get("render_after"):
            rc2, out2, err2 = run(
                str(SCRIPTS / "render_template.py"),
                "--mode",
                "B",
                "--answers",
                str(path),
            )
            if rc2 != 0:
                fails.append(f"{sid} render B 실패: {err2}")
                return
            for kw in sc.get("expect_render_keywords", []):
                if kw not in out2:
                    fails.append(f"{sid} render 출력에 '{kw}' 누락")
        return
    fails.append(f"{sid}: 시나리오 핸들러 누락")


def main() -> int:
    fails: list[str] = []
    for sc in SCENARIOS:
        before = len(fails)
        evaluate(sc, fails)
        after = len(fails)
        mark = "PASS" if after == before else "FAIL"
        print(f"{mark} {sc['id']} — {sc['prompt'][:70]}…")
        if after > before:
            for f in fails[before:after]:
                print(f"   {f}")
    print()
    print(f"=== ROUND B: {len(SCENARIOS) - len(fails)}/{len(SCENARIOS)} 통과 ===")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
