"""clarity_lib.py 단위 테스트 — 결정론 동작 점검."""

from __future__ import annotations

import sys
import traceback

import clarity_lib as L


_failures: list[str] = []


def check(name: str, condition: bool, info: str = "") -> None:
    if condition:
        print(f"  PASS  {name}")
    else:
        msg = f"  FAIL  {name}  {info}"
        print(msg)
        _failures.append(msg)


def test_honorific() -> None:
    print("[honorific]")
    check("default 빈 입력", L.select_honorific({}) == "선생님")
    check("박사 본인", L.select_honorific({"is_doctor": True}) == "박사님")
    check(
        "목사 직함",
        L.select_honorific({"title": "목사"}) == "목사님",
    )
    check(
        "직함 + 님 이미 포함",
        L.select_honorific({"title": "전도사님"}) == "전도사님",
    )
    check(
        "이름만",
        L.select_honorific({"name": "민수"}) == "민수님",
    )
    check(
        "박사 우선 (다른 키와 충돌)",
        L.select_honorific({"is_doctor": True, "title": "교수"}) == "박사님",
    )


def test_input_type() -> None:
    print("[input_type]")
    # A: 진단 없음, 일반 막연 요청
    r = L.classify_input_type("비전이 모르겠어요")
    check("A — 진단 없음·일반", r["type"] == "A", r)
    # B: 진단 보유
    r = L.classify_input_type("비전 한 문장 만들고 싶어요", ["mbti", "enneagram"])
    check("B — 진단 보유", r["type"] == "B", r)
    # C: 압축 토큰
    r = L.classify_input_type(
        "진단 다 했어요. 압축 모드로 빠르게 가요", ["mbti", "enneagram", "values"]
    )
    check("C — 압축 토큰", r["type"] == "C", r)
    # D: 즉답 토큰
    r = L.classify_input_type("내 비전 한 문장 바로 말해줘")
    check("D — 즉답 토큰", r["type"] == "D", r)
    # E: 범위 밖 (선택지 비교)
    r = L.classify_input_type("두 선택지 중에 뭘 결정해야 할까요?")
    check("E — 범위 밖 goal-reframing", r["type"] == "E" and r["scope_out"] == "goal-reframing", r)
    # E: 직업 추천
    r = L.classify_input_type("어떤 직업이 좋을까요?")
    check("E — 직업 추천", r["type"] == "E" and r["scope_out"] == "career-recommendation", r)
    # E: 진척 점검
    r = L.classify_input_type("현재 점검을 받고 싶어요")
    check("E — 진척 점검", r["type"] == "E" and r["scope_out"] == "progress-review", r)
    # E: 진로 결정
    r = L.classify_input_type("두 가지 진로 중에 뭘 선택해야 할까요?")
    check("E — 두 가지 진로 중", r["type"] == "E" and r["scope_out"] == "goal-reframing", r)
    # E: 직업이 좋을까
    r = L.classify_input_type("저한테 맞는 직업이 좋을까요?")
    check("E — 직업이 좋을까", r["type"] == "E" and r["scope_out"] == "career-recommendation", r)


def test_step4() -> None:
    print("[step4]")
    r = L.select_step4_question(55, "박사님")
    check("나이 55 → 80세 임종", r["chosen"] == "eighty" and "80세" in r["primary_question"], r)
    r = L.select_step4_question(27, "선생님")
    check("나이 27 → 5년 후", r["chosen"] == "five_year" and "5년 후" in r["primary_question"], r)
    r = L.select_step4_question(None)
    check("나이 None → 기본 5년 후", r["chosen"] == "five_year", r)
    r = L.select_step4_question(40)
    check("경계 40 → 80세", r["chosen"] == "eighty", r)
    r = L.select_step4_question(39)
    check("경계 39 → 5년 후", r["chosen"] == "five_year", r)


def test_diag_step() -> None:
    print("[diag_step]")
    check("values → 1", L.map_diagnosis_to_step("values")["step"] == 1)
    check("enneagram → 1", L.map_diagnosis_to_step("enneagram")["step"] == 1)
    check("mbti → 2", L.map_diagnosis_to_step("mbti")["step"] == 2)
    check("strong → 2", L.map_diagnosis_to_step("strong")["step"] == 2)
    check("multipleintel → 2", L.map_diagnosis_to_step("multipleintel")["step"] == 2)
    check("readiness → 4", L.map_diagnosis_to_step("readiness")["step"] == 4)
    check(
        "cys-competence → 1~4",
        L.map_diagnosis_to_step("cys-competence")["step"] == [1, 2, 3, 4],
    )
    check(
        "별칭 vision-mbti → mbti",
        L.map_diagnosis_to_step("vision-mbti")["key"] == "mbti",
    )
    check(
        "미지원 키 → valid False",
        L.map_diagnosis_to_step("xyz")["valid"] is False,
    )


def test_diag_question() -> None:
    print("[diag_question]")
    q = L.render_diagnosis_question("enneagram", "박사님", 5)
    check(
        "enneagram 질문 — 단정형 없음·물음표 포함",
        "5번" in q and "?" in q and "이다" not in q,
        q,
    )
    q = L.render_diagnosis_question("mbti", "선생님")
    check("mbti 질문 — 물음표·체험 확인", "?" in q and "느껴진" in q, q)
    q = L.render_diagnosis_question("strong", "박사님")
    check("strong 질문 — 영역 표현", "영역" in q and "?" in q, q)
    q = L.render_diagnosis_question("readiness", "선생님")
    check("readiness 질문 — 약한 영역 화법", "약" in q and "?" in q, q)
    try:
        L.render_diagnosis_question("zzz")
        check("미지원 키 ValueError", False, "ValueError 미발생")
    except ValueError:
        check("미지원 키 ValueError", True)


def test_validate_sentence() -> None:
    print("[validate_sentence]")
    good = (
        "AGI 시대에 영성과 미래학을 잇는 통합 지혜를 한국 다음 세대에게 "
        "책과 강의로 전수하는 것"
    )
    r = L.validate_vision_sentence(good)
    check("good 문장 — structure_ok", r["structure_ok"] is True, r)
    # 두 문장 — 위반
    r = L.validate_vision_sentence("일을 하는 것이다. 사람을 살리는 것이다.")
    check("두 문장 — 위반", r["is_single_sentence"] is False, r)
    # 동사구 없음
    r = L.validate_vision_sentence("한국 청년 미래")
    check("동사구 없음 — 위반", r["has_verb_phrase"] is False, r)
    # 너무 짧음
    r = L.validate_vision_sentence("하는 것")
    check("너무 짧음 — 위반", r["approx_length_ok"] is False, r)


def test_detect_assertive() -> None:
    print("[detect_assertive]")
    hits = L.detect_assertive_phrases("ENFP니까 창작 비전이어야 한다")
    check("ENFP 단정 검출", len(hits) >= 1, hits)
    hits = L.detect_assertive_phrases("5번 유형이라서 봉사형 비전입니다")
    check("에니어그램 5번 단정 검출", len(hits) >= 1, hits)
    hits = L.detect_assertive_phrases(
        "8유형은 반드시 권력형 비전을 가져야 한다"
    )
    check("8유형 반드시 검출", len(hits) >= 1, hits)
    # 음성: 단정 아님
    hits = L.detect_assertive_phrases(
        "에니어그램 결과를 보셨을 때 어떻게 느끼셨나요?"
    )
    check("질문형 — 무검출", len(hits) == 0, hits)


def test_emoji_check() -> None:
    print("[emoji_check]")
    r = L.validate_emoji_usage("Step 1 🪞 Step 2 ⚡ Step 3 🎬")
    check("허용 이모지만 — clean", r["is_clean"], r)
    r = L.validate_emoji_usage("Step 1 🪞 잘 했어요 👏")
    check("미허용 이모지 검출", r["is_clean"] is False and "👏" in r["violations"], r)
    r = L.validate_emoji_usage("이모지 없음 텍스트")
    check("이모지 없음 — clean", r["is_clean"], r)


def test_opening() -> None:
    print("[opening]")
    txt = L.render_opening_template()
    check("opening 비어있지 않음", len(txt) > 50)
    check("opening MBTI 언급", "MBTI" in txt and "에니어그램" in txt)
    check("opening 진단 6종 모두", all(k in txt for k in ["MBTI", "에니어그램", "다중지능", "STRONG", "가치", "CYS"]))


def main() -> int:
    try:
        test_honorific()
        test_input_type()
        test_step4()
        test_diag_step()
        test_diag_question()
        test_validate_sentence()
        test_detect_assertive()
        test_emoji_check()
        test_opening()
    except Exception:
        traceback.print_exc()
        return 2

    print()
    if _failures:
        print(f"== 실패 {len(_failures)}건 ==")
        for f in _failures:
            print(f)
        return 1
    print("== 모든 단위 테스트 PASS ==")
    return 0


if __name__ == "__main__":
    sys.exit(main())
