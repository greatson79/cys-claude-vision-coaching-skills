"""추가 약점 깊이 점검 — corner cases·edge cases·adversarial inputs.

검사 항목:
  A. 입력 텍스트 corner cases
     - 영어 입력
     - 매우 긴 입력 (10,000자)
     - 빈 입력
     - 공백만 입력
     - 특수문자·이모지 포함 입력
     - 따옴표·역슬래시 포함 입력 (shell escape 위험)
  B. 호칭 corner cases
     - 빈 메타
     - 직함 + 이름 동시 입력
     - 박사 + 다른 직함 동시
     - special char 직함
  C. 진단 키 corner cases
     - 대소문자 혼용
     - 별칭 매칭
     - 미지원 키
     - 빈 키
  D. Step 4 corner cases
     - 음수 나이
     - 매우 큰 나이 (200)
     - 0세
     - 39 vs 40 경계
  E. validate_sentence corner cases
     - 따옴표 안에 동사구 ("~하는 것")
     - 매우 긴 문장 (200자)
     - 종결부호 0개·1개·2개
     - 한자·이모지 포함
  F. detect_assertive corner cases
     - 단정형이지만 종결구가 의문문 ("ENFP니까 ~할까요?") → 검출 안 해야 함
     - 단정형 한국어 변형 ("이라서·이라면·이라고·이라고는·이기 때문에")
     - 부정문 ("ENFP라서 ~가 아니다") → 어떻게 처리?
  G. ReDoS 안전성
     - 매우 긴 한국어 문자열로 정규식 시간 측정
  H. JSON 출력 안정성
     - 한국어·이모지·따옴표 포함 시 json.dumps 라운드트립
"""

from __future__ import annotations

import json
import sys
import time
import unicodedata

import clarity_lib as L


_failures: list[str] = []


def check(name: str, condition: bool, info: str = "") -> None:
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}  info={info}")
        _failures.append(f"{name}: {info}")


# ============================================================================
# A. 입력 텍스트 corner cases
# ============================================================================

def test_input_corner() -> None:
    print("\n[A. 입력 텍스트 corner cases]")

    # A1. 영어 입력
    r = L.classify_input_type("I don't know what to do with my life")
    check("영어 입력 — 토큰 매치 없으므로 A", r["type"] == "A", r)

    # A2. 매우 긴 입력
    long_text = "비전이 모르겠어요. " * 1000  # 약 1.6만 자
    t0 = time.time()
    r = L.classify_input_type(long_text)
    elapsed = time.time() - t0
    check(
        f"매우 긴 입력 (1.6만 자) — 1초 이내 처리",
        elapsed < 1.0 and r["type"] == "A",
        f"elapsed={elapsed:.3f}s",
    )

    # A3. 빈 입력
    r = L.classify_input_type("")
    check("빈 입력 — A 기본", r["type"] == "A", r)

    # A4. 공백만 입력
    r = L.classify_input_type("   \n\n  \t  ")
    check("공백만 — A 기본", r["type"] == "A", r)

    # A5. 따옴표·역슬래시 포함
    r = L.classify_input_type('비전 "한 문장" \\으로')
    check("따옴표·역슬래시 포함 — 정상 처리", isinstance(r["type"], str), r)

    # A6. 이모지 포함 (사용자가 이모지 사용)
    r = L.classify_input_type("비전 모르겠어요 😢")
    check("이모지 포함 — 토큰 매치 없으므로 A", r["type"] == "A", r)

    # A7. 한국어 + 영어 혼용
    r = L.classify_input_type("MBTI ENTJ인데 my vision is unclear")
    check("한국어+영어 혼용", r["type"] == "A", r)


# ============================================================================
# B. 호칭 corner cases
# ============================================================================

def test_honorific_corner() -> None:
    print("\n[B. 호칭 corner cases]")

    # B1. 빈 메타
    check("빈 dict", L.select_honorific({}) == "선생님")

    # B2. 직함 + 이름 동시 — 직함 우선
    r = L.select_honorific({"title": "목사", "name": "철수"})
    check("직함 + 이름 — 직함 우선 (목사님)", r == "목사님", r)

    # B3. 박사 + 다른 직함 — 박사 우선
    r = L.select_honorific({"is_doctor": True, "title": "교수", "name": "윤식"})
    check("박사 + 교수 + 이름 — 박사님", r == "박사님", r)

    # B4. None 입력
    r = L.select_honorific(None)
    check("None 입력 — 기본", r == "선생님", r)

    # B5. 비-dict 입력
    r = L.select_honorific("박사")
    check("string 입력 — 기본", r == "선생님", r)

    # B6. 빈 직함·빈 이름
    r = L.select_honorific({"title": "", "name": ""})
    check("빈 직함·빈 이름 — 기본", r == "선생님", r)

    # B7. 공백 직함
    r = L.select_honorific({"title": "   "})
    check("공백 직함 — 기본", r == "선생님", r)

    # B8. 직함에 "님" 이미 포함
    r = L.select_honorific({"title": "사모님"})
    check("사모님 — 그대로", r == "사모님", r)


# ============================================================================
# C. 진단 키 corner cases
# ============================================================================

def test_diagnosis_corner() -> None:
    print("\n[C. 진단 키 corner cases]")

    # C1. 대소문자
    r = L.map_diagnosis_to_step("MBTI")
    check("대문자 MBTI", r["valid"] and r["step"] == 2, r)

    # C2. 별칭
    r = L.map_diagnosis_to_step("에니어그램")
    check("한국어 별칭 에니어그램", r["valid"] and r["step"] == 1, r)

    # C3. 미지원 키
    r = L.map_diagnosis_to_step("DISC")
    check("DISC — 미지원", not r["valid"], r)

    # C4. 빈 키
    r = L.map_diagnosis_to_step("")
    check("빈 키 — 미지원", not r["valid"], r)

    # C5. None
    r = L.map_diagnosis_to_step(None)
    check("None — 미지원", not r["valid"], r)

    # C6. render_diagnosis_question — 미지원 ValueError
    try:
        L.render_diagnosis_question("DISC")
        check("미지원 키 ValueError", False)
    except ValueError:
        check("미지원 키 ValueError", True)


# ============================================================================
# D. Step 4 corner cases
# ============================================================================

def test_step4_corner() -> None:
    print("\n[D. Step 4 corner cases]")

    # D1. 음수 나이
    r = L.select_step4_question(-5)
    check("음수 나이 — 5년 후", r["chosen"] == "five_year", r)

    # D2. 매우 큰 나이
    r = L.select_step4_question(200)
    check("나이 200 — 80세 임종", r["chosen"] == "eighty", r)

    # D3. 0세
    r = L.select_step4_question(0)
    check("0세 — 5년 후", r["chosen"] == "five_year", r)

    # D4. 경계
    check("39세 — 5년", L.select_step4_question(39)["chosen"] == "five_year")
    check("40세 — 80세", L.select_step4_question(40)["chosen"] == "eighty")
    check("41세 — 80세", L.select_step4_question(41)["chosen"] == "eighty")

    # D5. 정수 아닌 입력
    r = L.select_step4_question("55")
    check("문자열 '55' — 5년 (정수 아님)", r["chosen"] == "five_year", r)
    r = L.select_step4_question(55.5)
    check("실수 55.5 — 5년 (int 아님)", r["chosen"] == "five_year", r)


# ============================================================================
# E. validate_sentence corner cases
# ============================================================================

def test_sentence_corner() -> None:
    print("\n[E. validate_sentence corner cases]")

    # E1. 정상 (~하는 것)
    r = L.validate_vision_sentence("한국 청년에게 미래 분별의 안목을 키우는 것")
    check("정상 — ~키우는 것", r["structure_ok"], r)

    # E2. 정상 (~나아가는 것)
    r = L.validate_vision_sentence("학문의 길로 나아가는 것")
    check("정상 — 나아가는 것", r["structure_ok"], r)

    # E3. 정상 (~기 명사형)
    r = L.validate_vision_sentence("이웃 사랑 실천하기를 통해 한국 사회를 회복하기")
    check("정상 — 회복하기", r["structure_ok"], r)

    # E4. 따옴표 포함
    r = L.validate_vision_sentence("\"믿음으로 살아가는 것\"")
    check("따옴표 포함", r["structure_ok"], r)

    # E5. 종결부호 2개
    r = L.validate_vision_sentence("일하는 것. 그리고 사는 것.")
    check("종결부호 2개 — 위반", not r["is_single_sentence"], r)

    # E6. 매우 짧음
    r = L.validate_vision_sentence("가는 것")
    check("매우 짧음 — 위반", not r["approx_length_ok"], r)

    # E7. 매우 김
    long_sent = "한국 청년에게 미래 분별의 안목을 " + "깊이 깊이 " * 20 + "키우는 것"
    r = L.validate_vision_sentence(long_sent)
    check("매우 김 — 위반", not r["approx_length_ok"], r)

    # E8. 동사구 없음
    r = L.validate_vision_sentence("한국 청년 미래 분별 안목 향상")
    check("동사구 없음 — 위반", not r["has_verb_phrase"], r)

    # E9. 한자·영문 혼용
    r = L.validate_vision_sentence("AGI 時代에 한국 다음 세대에게 智慧를 전수하는 것")
    check("한자·영문 혼용", r["structure_ok"], r)


# ============================================================================
# F. detect_assertive corner cases
# ============================================================================

def test_assertive_corner() -> None:
    print("\n[F. detect_assertive corner cases]")

    # F1. 단정형 변형 — 이기에·이므로
    hits = L.detect_assertive_phrases("ENTJ이기에 리더가 되어야 한다")
    check("이기에 변형 검출", len(hits) >= 1, hits)

    hits = L.detect_assertive_phrases("ENTJ이므로 리더십 비전이다")
    check("이므로 변형 검출", len(hits) >= 1, hits)

    # F2. 의문형 (단정 아님)
    hits = L.detect_assertive_phrases("ENFP니까 창작 비전일까요?")
    check("의문문 — 단정 아님", len(hits) == 0, hits)

    # F3. 가정문
    hits = L.detect_assertive_phrases("만약 ENFP면 창작이 어울릴 수 있겠지만")
    check("가정문 — 단정 아님 (어울릴 수 있겠지만)", len(hits) == 0, hits)

    # F4. 정상 응답 — 진단 단어만 있고 단정 없음
    hits = L.detect_assertive_phrases(
        "MBTI ENFP 결과 보셨을 때 어떻게 느끼셨나요? 에니어그램 4번은 어떠셨어요?"
    )
    check("질문 응답 — 무검출", len(hits) == 0, hits)

    # F5. 추측형
    hits = L.detect_assertive_phrases("ENFP라서 창작 비전일지도 모르겠어요")
    check("추측형 — 단정 아님", len(hits) == 0, hits)


# ============================================================================
# G. ReDoS 안전성
# ============================================================================

def test_redos_safety() -> None:
    print("\n[G. ReDoS 안전성]")

    # G1. 매우 긴 텍스트로 정규식 시간 측정
    big = "ENFP" + "니" * 5000 + "까 " + "아" * 5000 + "이다"
    t0 = time.time()
    hits = L.detect_assertive_phrases(big)
    elapsed = time.time() - t0
    check(
        f"5천자 텍스트 정규식 — 1초 이내 ({elapsed:.3f}s)",
        elapsed < 1.0,
        f"elapsed={elapsed}",
    )

    # G2. 입력 유형 분류 매우 긴 입력
    big_text = ("비전 한 문장 바로 말해줘 " * 1000)
    t0 = time.time()
    r = L.classify_input_type(big_text)
    elapsed = time.time() - t0
    check(
        f"긴 텍스트 입력 유형 분류 — 1초 이내 ({elapsed:.3f}s)",
        elapsed < 1.0,
        f"elapsed={elapsed}",
    )

    # G3. validate_sentence 매우 긴
    big_sent = ("이루는 것 " * 1000)
    t0 = time.time()
    r = L.validate_vision_sentence(big_sent)
    elapsed = time.time() - t0
    check(
        f"긴 문장 검증 — 1초 이내 ({elapsed:.3f}s)",
        elapsed < 1.0,
        f"elapsed={elapsed}",
    )


# ============================================================================
# H. JSON 라운드트립 안정성
# ============================================================================

def test_json_safety() -> None:
    print("\n[H. JSON 라운드트립]")

    # H1. 한국어·이모지·따옴표 포함된 응답
    payload = {
        "honorific": "박사님",
        "opening": L.render_opening_template(),
        "step4_q": L.select_step4_question(55, "박사님")["primary_question"],
        "diag_q": L.render_diagnosis_question("enneagram", "박사님", 9),
        "emoji_in_text": "🪞 ⚡ 🎬 ⏳ ✨",
        "vision": '"통합 지혜"를 전수하는 것',
    }
    serialized = json.dumps(payload, ensure_ascii=False)
    parsed = json.loads(serialized)
    check("JSON 라운드트립 일치", parsed == payload)

    # H2. 응답 내부 따옴표
    body = L.render_step5_check("박사님", '책 "AGI 시대"를 쓰는 것')
    serialized = json.dumps({"body": body}, ensure_ascii=False)
    parsed = json.loads(serialized)
    check("따옴표 안의 따옴표 JSON 안정", parsed["body"] == body)


# ============================================================================
# I. CLI subprocess 안정성 (shell injection 위험 점검)
# ============================================================================

def test_cli_injection() -> None:
    print("\n[I. CLI subprocess 안전성]")

    # subprocess.run + 리스트 인자는 shell escape 불필요
    # 본 스킬의 SKILL.md도 subprocess + list 호출 권장
    # 사용자 입력에 shell metacharacter 포함되어도 안전
    import subprocess
    from pathlib import Path

    here = Path(__file__).resolve().parent
    py = sys.executable
    cli = str(here / "clarity_lib.py")

    # I1. 따옴표 포함 입력
    proc = subprocess.run(
        [py, cli, "input_type", "--text", '비전 "막연" 해요', "--diagnoses", ""],
        capture_output=True, text=True, check=True,
    )
    r = json.loads(proc.stdout)
    check("따옴표 포함 CLI — 정상 처리", r["type"] == "A", r)

    # I2. shell metacharacter 포함 입력
    proc = subprocess.run(
        [py, cli, "input_type", "--text", "비전; rm -rf /tmp/foo `; echo x", "--diagnoses", ""],
        capture_output=True, text=True, check=True,
    )
    r = json.loads(proc.stdout)
    check("shell metachar CLI — 정상 처리 (escape 불필요)", r["type"] == "A", r)


# ============================================================================
# J. Step 5 확인 반영 — 따옴표 처리
# ============================================================================

def test_step5_quote() -> None:
    print("\n[J. Step 5 따옴표 처리]")

    sent = '"AGI 시대의 통합 지혜"를 전수하는 것'
    r = L.render_step5_check("박사님", sent)
    check("따옴표 포함 문장 — step5_check 정상", "전수하는 것" in r and "박사님" in r, r)


def main() -> int:
    print("=" * 70)
    print("추가 약점 깊이 점검 (corner cases·adversarial inputs)")
    print("=" * 70)
    test_input_corner()
    test_honorific_corner()
    test_diagnosis_corner()
    test_step4_corner()
    test_sentence_corner()
    test_assertive_corner()
    test_redos_safety()
    test_json_safety()
    test_cli_injection()
    test_step5_quote()

    print("\n" + "=" * 70)
    if _failures:
        print(f"실패 {len(_failures)}건:")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print(f"== 약점 점검 전 항목 PASS ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
