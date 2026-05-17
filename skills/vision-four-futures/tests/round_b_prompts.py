#!/usr/bin/env python3
"""
10개 검증 프롬프트 — Round B (이전 검증과 전혀 다른 10개).

각 프롬프트가 스킬 작업 흐름을 따라 *정확한* 결과를 산출하는지 확인한다.
PASS 기준:
  · 결정론 호출만으로 답이 만들어진다 (자연어 환각 0)
  · 산출이 facts/citations/external_sources의 기록과 1:1 일치
  · 모드 A/B/C/D 출력은 validate_output.py PASS

실행:
    python3 tests/round_b_prompts.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
SCRIPTS = ROOT / "scripts"
ASSETS = ROOT / "assets"

FAILURES: list[str] = []


def run(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, cwd=str(ROOT), input=stdin)


def expect(cond: bool, msg: str) -> None:
    if cond:
        print(f"  ok: {msg}")
    else:
        print(f"  FAIL: {msg}")
        FAILURES.append(msg)


# ---------------- 프롬프트 정의 ----------------

PROMPTS = [
    # 프롬프트 1 — 책 부제와 쪽수가 어떻게 되는가? (메타데이터 결정론)
    {
        "id": "P1",
        "task": "박사님 책 부제와 쪽수가 어떻게 되는가",
        "type": "metadata_lookup",
    },
    # 프롬프트 2 — 가능 미래들의 확률 수치를 정확히 알려 달라 (확률 단정 거절)
    {
        "id": "P2",
        "task": "가능 미래들의 확률이 박사님 책에 정확히 몇 %로 명시되어 있는가",
        "type": "probability_refusal",
    },
    # 프롬프트 3 — Henchey 1978 학술 정렬 (외부 출처)
    {
        "id": "P3",
        "task": "Henchey 1978이 분류한 4가지가 박사님 F1~F4와 어떻게 대응하는가",
        "type": "external_source_alignment",
    },
    # 프롬프트 4 — '비약적 진보'의 영어가 원서에 명시되어 있는가
    {
        "id": "P4",
        "task": "'비약적 진보'의 영어 'Quantum Progress'가 원서에 그대로 표기되어 있는가",
        "type": "english_label_verification",
    },
    # 프롬프트 5 — F5에 대해 알려 달라 (오류 처리)
    {
        "id": "P5",
        "task": "F5는 어떤 미래인가",
        "type": "error_handling",
    },
    # 프롬프트 6 — 모드 D 풀 (박사님 AGI 시대 4가지 미래 골격)
    {
        "id": "P6",
        "task": "박사님 미래학자 본업 — AGI 시대 4가지 미래 골격",
        "type": "mode_d_render",
    },
    # 프롬프트 7 — 모드 B F3 단독 심층
    {
        "id": "P7",
        "task": "뜻밖의 미래만 단독 심층 — 한국 통일 wildcard 4개 펼치기",
        "type": "mode_b_render",
    },
    # 프롬프트 8 — Petersen 1997 인용으로 wildcard 학술 근거 보여 달라
    {
        "id": "P8",
        "task": "Petersen 1997 'Out of the Blue'에서 wildcard 정의 학술 근거",
        "type": "external_source_lookup",
    },
    # 프롬프트 9 — 비전 후보 매핑 4개를 그대로 보여 달라
    {
        "id": "P9",
        "task": "비전 후보 매핑 4개 (재능·미래유망성·가치·나머지)가 어느 미래에 매핑되는가",
        "type": "vision_mapping_lookup",
    },
    # 프롬프트 10 — 박사님 책에 70~80%로 명시되어 있나? 단정 답해 달라 (확률 단정 거절)
    {
        "id": "P10",
        "task": "박사님 책이 기본미래 확률을 70~80%로 명시했는가, 단정 답해 달라",
        "type": "probability_strict_refusal",
    },
]


# ---------------- 프롬프트 실행 ----------------

def t_p1_book_metadata() -> None:
    print("\n[P1] 박사님 책 부제와 쪽수")
    r = run([PY, str(SCRIPTS / "lookup.py"), "book"])
    expect(r.returncode == 0, "lookup book 종료 코드 0")
    expect("흔들림 없는 인생을 계획하는 5단계 비전 방법론" in r.stdout, "부제 정확")
    expect("272" in r.stdout, "쪽수 272 정확")
    expect("9788993322972" in r.stdout, "ISBN 정확")
    expect("최윤식" in r.stdout and "최현식" in r.stdout, "공저자 2인")


def t_p2_probability_refusal() -> None:
    print("\n[P2] 가능 미래들 확률 단정 거절")
    r = run([PY, str(SCRIPTS / "lookup.py"), "probability", "F2"])
    expect(r.returncode == 0, "probability F2 종료 코드 0")
    expect("미명시" in r.stdout, "책에 수치 미명시 명시")
    expect("단정" in r.stdout and ("금지" in r.stdout or "허용" in r.stdout), "단정 금지 가이드")


def t_p3_henchey_alignment() -> None:
    print("\n[P3] Henchey 1978 학술 정렬")
    r = run([PY, str(SCRIPTS / "lookup.py"), "source", "S1"])
    expect(r.returncode == 0, "source S1 종료 코드 0")
    expect("Henchey" in r.stdout, "Henchey 명시")
    expect("1978" in r.stdout, "연도 1978")
    expect("possible" in r.stdout and "plausible" in r.stdout, "Henchey 4분류 포함")
    # mapping 확인
    s1 = next(s for s in json.loads(
        (ASSETS / "external_sources.json").read_text(encoding="utf-8")
    )["sources"] if s["id"] == "S1")
    m = s1["mapping_to_choi_yoonsik"]
    expect(any("F2" in k for k in m), "possible→F2 매핑")
    expect(any("F1" in k for k in m), "plausible→F1 매핑")
    expect(any("F4" in k for k in m), "preferable→F4 매핑")


def t_p4_english_label_verification() -> None:
    print("\n[P4] '비약적 진보' 영문 표기 검증")
    r = run([PY, str(SCRIPTS / "lookup.py"), "wildcard-subtypes"])
    expect("미확인" in r.stdout, "Quantum Progress 원서 표기 미확인 명시")
    expect("실물 확인이 필요" in r.stdout, "실물 확인 필요 안내")


def t_p5_error_handling() -> None:
    print("\n[P5] F5 오류 처리")
    r = run([PY, str(SCRIPTS / "lookup.py"), "future", "F5"])
    expect(r.returncode != 0, "F5 비정상 종료")
    expect("Unknown future id" in r.stderr or "Unknown future id" in r.stdout,
           "오류 메시지 안내")
    expect("F1, F2, F3, F4" in r.stderr or "F1, F2, F3, F4" in r.stdout,
           "유효 ID 안내")


def t_p6_mode_d_render() -> None:
    print("\n[P6] 모드 D 풀 골격 + 검증")
    r1 = run([PY, str(SCRIPTS / "render_skeleton.py"), "--mode", "D"])
    expect(r1.returncode == 0, "render D 종료 코드 0")
    expect("AGI 시대" in r1.stdout, "AGI 시대 머리말")
    expect("F1" in r1.stdout and "F4" in r1.stdout, "4개 미래 모두 등장")
    # 검증 통과
    r2 = run([PY, str(SCRIPTS / "validate_output.py"), "-", "--mode", "D"], stdin=r1.stdout)
    expect(r2.returncode == 0, f"모드 D validate PASS\n--- stdout ---\n{r2.stdout}")
    expect("OVERALL: PASS" in r2.stdout, "검증 OVERALL PASS")


def t_p7_mode_b_render() -> None:
    print("\n[P7] 모드 B F3 단독 + 검증")
    r1 = run([PY, str(SCRIPTS / "render_skeleton.py"), "--mode", "B", "--focus", "F3"])
    expect(r1.returncode == 0, "render B F3 종료 코드 0")
    expect("뜻밖의 미래" in r1.stdout, "F3 라벨")
    expect("비약적 진보" in r1.stdout and "붕괴" in r1.stdout, "2종 모두 등장")
    expect("시기 예측" in r1.stdout, "시기 예측 핵심 원칙 포함")
    r2 = run([PY, str(SCRIPTS / "validate_output.py"), "-",
              "--mode", "B", "--focus", "F3"], stdin=r1.stdout)
    expect(r2.returncode == 0, f"모드 B F3 validate PASS\n--- stdout ---\n{r2.stdout}")


def t_p8_petersen_lookup() -> None:
    print("\n[P8] Petersen 1997 외부 학술 출처")
    r = run([PY, str(SCRIPTS / "lookup.py"), "source", "S5"])
    expect(r.returncode == 0, "source S5 종료 코드 0")
    expect("Petersen" in r.stdout and "Out of the Blue" in r.stdout, "저자·책 명")
    expect("low probability" in r.stdout.lower() or "high impact" in r.stdout.lower(),
           "wildcard 정의 구문")
    expect("1992" in r.stdout, "Copenhagen Institute 1992 선행 정의 명시")


def t_p9_vision_mapping() -> None:
    print("\n[P9] 비전 후보 매핑 4개")
    r = run([PY, str(SCRIPTS / "lookup.py"), "vision-mapping"])
    expect(r.returncode == 0, "vision-mapping 종료 코드 0")
    expect("재능·역량 직접 연결" in r.stdout and "기본 비전" in r.stdout, "재능→기본")
    expect("미래 유망성이 좋은 것" in r.stdout, "미래유망성")
    expect("가치에 부합하는 것" in r.stdout, "가치 부합")
    expect("나머지" in r.stdout, "나머지")
    # 4매핑 모두 F1~F4 등장
    for fid in ["기본미래", "가능 미래들", "뜻밖의 미래", "바람직한 미래"]:
        expect(fid in r.stdout, f"매핑에 {fid} 포함")


def t_p10_strict_probability_refusal() -> None:
    print("\n[P10] '70~80%' 단정 답 거절")
    r = run([PY, str(SCRIPTS / "lookup.py"), "probability", "F1"])
    expect("미명시" in r.stdout, "수치 미명시 안내")
    expect("해석치" in r.stdout, "해석치 표기 안내")
    # 단정 텍스트 생성 시 validate가 잡는지
    bad_assertion = (
        "박사님은 기본미래 (Plausible Future)를 70~80%로 단정 표기한다.\n"
        "## F2 가능 미래들\n대안.\n## F3 뜻밖의 미래\n비약적 진보. 붕괴.\n## F4 바람직한 미래\n원하는 미래.\n"
    )
    r2 = run([PY, str(SCRIPTS / "validate_output.py"), "-", "--mode", "A"],
             stdin="## F1 기본미래\n" + bad_assertion)
    expect(r2.returncode == 1, "단정 표기는 validate FAIL")
    expect("R4" in r2.stdout, "R4 위반 명시")


def main() -> int:
    tests = [
        t_p1_book_metadata,
        t_p2_probability_refusal,
        t_p3_henchey_alignment,
        t_p4_english_label_verification,
        t_p5_error_handling,
        t_p6_mode_d_render,
        t_p7_mode_b_render,
        t_p8_petersen_lookup,
        t_p9_vision_mapping,
        t_p10_strict_probability_refusal,
    ]
    for t in tests:
        t()
    print()
    if FAILURES:
        print(f"=== Round B {len(FAILURES)} 실패 ===")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("=== Round B 10개 프롬프트 100% PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
