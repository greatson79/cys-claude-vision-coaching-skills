#!/usr/bin/env python3
"""ROUND A — 10개 새로운 검증 프롬프트.

각 프롬프트는 사용자가 본 스킬을 호출하는 다양한 발화를 모사한다.
스킬이 결정론 스크립트를 통해 정확히 동작하는지 시나리오별로 검증한다.

실행:
    python3 tests/round_a_prompts.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
TMP = Path("/tmp/vsw_round_a")
TMP.mkdir(parents=True, exist_ok=True)


def run(*args: str, expect_exit: int = 0) -> tuple[int, str, str]:
    r = subprocess.run(
        ["python3", *args],
        capture_output=True,
        text=True,
    )
    if r.returncode != expect_exit:
        return r.returncode, r.stdout, r.stderr
    return r.returncode, r.stdout, r.stderr


def write_answers(name: str, answers: dict) -> Path:
    p = TMP / f"{name}.json"
    p.write_text(json.dumps(answers, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


# 10개 새로운 사용자 시나리오 — ROUND A
SCENARIOS = [
    {
        "id": "A01",
        "prompt": "사용자: 비전 선언문 작성해줘. 도서관 사서로 일하는 30대 워킹맘이고, "
        "디지털 전환 시대에 책 읽기 문화를 살리는 사람이 되고 싶어.",
        "answers": {
            "F1_name": "박서연",
            "F2_plausible": "AI 추천 알고리즘이 대중 독서를 지배하며 깊은 독서 시간이 줄고, 공공도서관 디지털화가 가속되는 사회",
            "F3_possible": "오프라인 동네 책방·작은 도서관이 의도적 슬로 미디어 거점으로 부활하는 흐름",
            "F4_unexpected": "AI 큐레이션 피로감이 폭증하여 '인간 사서'가 다시 신뢰 받는 시대가 도래",
            "F5_problem": "디지털 전환 시대 깊은 독서 부재와 공동체 단절",
            "F6_interest": "독서 문화·도서관·청소년 교육",
            "F7_talent": "상위 3개 지능(Linguistic·Interpersonal·Intrapersonal) + 디지털 기록 관리 기술",
            "F8_personality": "INFJ 옹호자형 + 에니어그램 4번(개인주의자) 5번 날개",
            "F9_work": "공공도서관 사서·청소년 독서 모임 운영자·도서관 교육 프로그램 기획",
            "F10_value": "지혜·공동체·아름다움이 살아있는",
            "F11_purposes": [
                "동네 청소년 월간 독서 모임 운영",
                "도서관 디지털 큐레이션 워크숍 기획",
                "지역 시니어 독서 회복 프로그램 개설",
                "도서관 SNS·블로그로 책 추천 콘텐츠 발행",
                "사서 후배 멘토링 1:1 코칭",
            ],
            "F12_date": "2026년 5월 17일",
        },
        "expect_validate_exit": 0,
    },
    {
        "id": "A02",
        "prompt": "사용자: 그냥 빈 양식만 출력해줘. 내가 혼자 손글씨로 쓸 거야.",
        "render_mode": "C",
        "expect_keywords": ["부름을 받았습니다", "기본미래", "Purposes 목적들"],
    },
    {
        "id": "A03",
        "prompt": "사용자: 시연 예시 한 번 보여줘. 어떻게 작성되는지 보고 따라 쓸게.",
        "render_mode": "D",
        "expect_keywords": [
            "가상 시연",
            "Vision Statement",
            "부름을 받았습니다",
            "Existential",
        ],
    },
    {
        "id": "A04",
        "prompt": "사용자: 12개 질문 다 보여줘. 노트에 적어가며 답해볼게.",
        "render_mode": "A",
        "expect_keywords": [
            "Q1",
            "F1_name",
            "Q12",
            "F12_date",
            "vision-multipleintel-visioncoding",
        ],
    },
    {
        "id": "A05",
        "prompt": "사용자: 농촌 마을 부흥 비전을 가진 50대 농부예요. 비전 선언문 만들어주세요.",
        "answers": {
            "F1_name": "김덕수",
            "F2_plausible": "한국 농촌 고령화·소멸 위기가 심화되고 농업 인구 5% 이하로 감소하는 미래",
            "F3_possible": "스마트팜·6차 산업·청년 귀촌 흐름으로 일부 거점 마을이 재생되는 가능성",
            "F4_unexpected": "기후 위기로 도시민 대규모 농촌 회귀가 발생해 토지 가치가 재편될 가능성",
            "F5_problem": "농촌 공동체 와해와 식량 안보 위협",
            "F6_interest": "농업·지역 공동체·생태",
            "F7_talent": "상위 3개 지능(Naturalist·Bodily-Kinesthetic·Interpersonal) + 스마트팜 ICT 기술",
            "F8_personality": "ISFJ 수호자형 + 에니어그램 6번(충성가) 5번 날개",
            "F9_work": "유기농 협동조합 운영·청년 귀농 멘토·마을 학교 강사",
            "F10_value": "공동체·생태·정의가 회복되는",
            "F11_purposes": [
                "유기농 협동조합 200가구 결성",
                "청년 귀농 멘토링 30명 양성",
                "마을 식량 안보 자급 시스템 구축",
                "지역 학교 생태 교육 정규 과목 신설",
                "농촌-도시 직거래 플랫폼 운영",
            ],
            "F12_date": "2026년 5월 17일",
        },
        "expect_validate_exit": 0,
    },
    {
        "id": "A06",
        "prompt": "사용자: 일자 형식 어떻게 적어야 하는지 까먹어서 검증부터 돌려봤어. 잘못 적어봤어.",
        "answers": {
            "F1_name": "홍길동",
            "F2_plausible": "AI 시대 사회 변화에 대한 적응이 필요한 상황입니다.",
            "F3_possible": "사회적 연대가 강화되는 새로운 흐름의 가능성도 존재합니다.",
            "F4_unexpected": "전례 없는 글로벌 위기가 사회 전반을 재편할 가능성.",
            "F5_problem": "고립·분절·정신적 빈곤을 해결하기 위해",
            "F6_interest": "교육·연대",
            "F7_talent": "Linguistic·Interpersonal·Intrapersonal + 디지털 협업 도구",
            "F8_personality": "ENFJ + 에니어그램 2번 1번 날개",
            "F9_work": "교육 디자이너·NPO 운영",
            "F10_value": "정의·아름다움",
            "F11_purposes": [
                "교사 워크숍 50회",
                "청년 멘토링 100명",
                "온라인 학습 플랫폼 개설",
                "지역 NPO 5곳 협력",
                "교육 정책 정기 보고서 5건",
            ],
            "F12_date": "5/17/2026",
        },
        "expect_validate_exit": 1,
        "expect_fail_message": "날짜 형식",
    },
    {
        "id": "A07",
        "prompt": "사용자: Purposes 한 개만 적었어. 검증해줘.",
        "answers": {
            "F1_name": "이수영",
            "F2_plausible": "재택근무 보편화와 도심 공동화가 동시에 진행되는 사회 변화",
            "F3_possible": "지역 거점 도시의 다시 살아나는 흐름이 나타날 가능성",
            "F4_unexpected": "메타버스 일터가 폭발해 물리적 사무실 자체가 사라질 가능성",
            "F5_problem": "원격·재택 노동자의 소속감 결핍·정신건강 위기",
            "F6_interest": "조직 문화·정신건강·원격 협업",
            "F7_talent": "Interpersonal·Intrapersonal·Linguistic + 협업 도구 기술발달",
            "F8_personality": "ENFP 활동가형 + 에니어그램 7번(열정가) 6번 날개",
            "F9_work": "조직 문화 코치·HR 컨설턴트·웰빙 프로그램 기획자",
            "F10_value": "공동체·기쁨·자율이 회복되는",
            "F11_purposes": ["HR 컨설팅 한 건"],
            "F12_date": "2026년 5월 17일",
        },
        "expect_validate_exit": 0,
        "expect_warn_message": "권장 항목 수 5",
    },
    {
        "id": "A08",
        "prompt": "사용자: 책 출처랑 ISBN 확인하고 싶어.",
        "lookup_cmd": ["book"],
        "expect_keywords": ["9788993322972", "최윤식의 미래준비학교", "지식노마드"],
    },
    {
        "id": "A09",
        "prompt": "사용자: 5대 공리로 검증해줘.",
        "lookup_cmd": ["excluded-tools"],
        "expect_keywords": ["5대 공리", "사유", "할루시네이션 방지"],
    },
    {
        "id": "A10",
        "prompt": "사용자: 다중지능 9가지 정확한 영문명 알려줘. Spiritual인지 Existential인지 헷갈려.",
        "lookup_cmd": ["multiple-intelligences"],
        "expect_keywords": ["Existential", "영성지능", "Gardner", "Spiritual"],
    },
]


def evaluate_scenario(sc: dict, fails: list) -> None:
    sid = sc["id"]
    if "answers" in sc:
        path = write_answers(sid, sc["answers"])
        # 우선 양식 렌더 — 결정론 작동
        rc, out, err = run(
            str(SCRIPTS / "render_template.py"),
            "--mode",
            "B",
            "--answers",
            str(path),
        )
        if rc != 0:
            fails.append(f"{sid} render B 실패: {err}")
        # 검증
        rc, out, err = run(
            str(SCRIPTS / "validate_output.py"),
            "--answers",
            str(path),
        )
        if rc != sc.get("expect_validate_exit", 0):
            fails.append(
                f"{sid} validate exit={rc}, expect={sc.get('expect_validate_exit')}\n"
                f"   stdout={out[:400]}"
            )
        if sc.get("expect_fail_message") and sc["expect_fail_message"] not in out:
            fails.append(
                f"{sid} validate 출력에 '{sc['expect_fail_message']}' 누락"
            )
        if sc.get("expect_warn_message") and sc["expect_warn_message"] not in out:
            fails.append(
                f"{sid} validate 출력에 '{sc['expect_warn_message']}' 경고 누락"
            )
        return
    if "render_mode" in sc:
        rc, out, err = run(
            str(SCRIPTS / "render_template.py"),
            "--mode",
            sc["render_mode"],
        )
        if rc != 0:
            fails.append(f"{sid} render {sc['render_mode']} 실패: {err}")
            return
        for kw in sc.get("expect_keywords", []):
            if kw not in out:
                fails.append(f"{sid} render 출력에 '{kw}' 누락")
        return
    if "lookup_cmd" in sc:
        rc, out, err = run(
            str(SCRIPTS / "lookup.py"),
            *sc["lookup_cmd"],
        )
        if rc != 0:
            fails.append(f"{sid} lookup 실패: {err}")
            return
        for kw in sc.get("expect_keywords", []):
            if kw not in out:
                fails.append(f"{sid} lookup 출력에 '{kw}' 누락")
        return
    fails.append(f"{sid}: 시나리오 핸들러 누락")


def main() -> int:
    fails: list[str] = []
    for sc in SCENARIOS:
        before = len(fails)
        evaluate_scenario(sc, fails)
        after = len(fails)
        mark = "PASS" if after == before else "FAIL"
        print(f"{mark} {sc['id']} — {sc['prompt'][:70]}…")
        if after > before:
            for f in fails[before:after]:
                print(f"   {f}")
    print()
    print(f"=== ROUND A: {len(SCENARIOS) - len(fails)}/{len(SCENARIOS)} 통과 ===")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
