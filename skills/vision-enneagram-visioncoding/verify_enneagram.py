#!/usr/bin/env python3
"""
vision-enneagram-visioncoding 종단 검증 스크립트.

10개 신규 검증 프롬프트로 결정론 파이프라인 전체를 자동 시험.
이전 검증 라운드와 *완전히 다른* 프롬프트 시나리오를 사용한다.

각 테스트는:
- 입력 시나리오 (응답 패턴 or 유형 직접 지정)
- 기대 결과 (주 유형, 윙, 화살, 센터 등)
- assert로 PASS/FAIL 판정
"""

from __future__ import annotations

import json
import sys
import subprocess

from enneagram_engine import (
    BLOCK_A,
    BLOCK_B,
    CORE_DESIRE,
    CORE_FEAR,
    STRESS_ARROW,
    GROWTH_ARROW,
    WING_NEIGHBORS,
    CENTER,
    TYPE_NAMES,
    WORLD_SOUGHT_KO,
    WORLD_SOUGHT_EN,
    WORLD_SOUGHT_ZH,
    QUESTIONS_KO,
    QUESTIONS_EN,
    QUESTIONS_ZH,
    stratified_shuffle,
    build_result,
    score_types,
    decide_primary,
    decide_wing,
    validate_answers,
    detect_language,
    detect_religion_neutral,
    parse_score_input,
    decide_from_scores,
)
from enneagram_lookup import (
    BEHAVIOR_PATTERN,
    HEALTHY_STATE,
    UNHEALTHY_STATE,
    WING_COMBO,
    BIBLE_BACKGROUND,
    SECULAR_BACKGROUND,
    GROWTH_PATH,
    CAUTION_KO,
    dump_type,
)


PASS = 0
FAIL = 0
REPORT = []


def assert_eq(name, got, expected):
    global PASS, FAIL
    if got == expected:
        PASS += 1
        REPORT.append(f"  PASS — {name}")
        return True
    FAIL += 1
    REPORT.append(f"  FAIL — {name}: got={got!r} expected={expected!r}")
    return False


def assert_true(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        REPORT.append(f"  PASS — {name}")
        return True
    FAIL += 1
    REPORT.append(f"  FAIL — {name} {detail}")
    return False


# ============================================================
# 검증 프롬프트 10개 — 이전 라운드와 완전 다름
# ============================================================

def t01_data_integrity():
    """프롬프트 1: '카탈로그 27문항·9유형 무결성 검증' — 데이터 자체의 일관성"""
    REPORT.append("\n[T01] 데이터 무결성: 27문항 × 9유형 일관성")
    # 각 유형 정확히 3문항인가
    counts = {t: 0 for t in range(1, 10)}
    for qid, (t, _) in QUESTIONS_KO.items():
        counts[t] += 1
    for t, c in counts.items():
        assert_eq(f"Type {t} has 3 questions", c, 3)
    # 블록 A는 정확히 18, 블록 B는 정확히 9
    assert_eq("BLOCK_A length", len(BLOCK_A), 18)
    assert_eq("BLOCK_B length", len(BLOCK_B), 9)
    # 블록 A 각 유형 2개, 블록 B 각 유형 1개
    a_counts = {t: 0 for t in range(1, 10)}
    for qid in BLOCK_A:
        a_counts[QUESTIONS_KO[qid][0]] += 1
    for t, c in a_counts.items():
        assert_eq(f"BLOCK_A Type {t} count", c, 2)
    b_counts = {t: 0 for t in range(1, 10)}
    for qid in BLOCK_B:
        b_counts[QUESTIONS_KO[qid][0]] += 1
    for t, c in b_counts.items():
        assert_eq(f"BLOCK_B Type {t} count", c, 1)
    # ko/en/zh 모두 같은 매핑
    for qid in QUESTIONS_KO:
        assert_eq(f"{qid} en type-match", QUESTIONS_EN[qid][0], QUESTIONS_KO[qid][0])
        assert_eq(f"{qid} zh type-match", QUESTIONS_ZH[qid][0], QUESTIONS_KO[qid][0])


def t02_shuffle_reproducibility():
    """프롬프트 2: '동일 시드는 동일 순서 / 다른 시드는 다른 순서'"""
    REPORT.append("\n[T02] 셔플 재현성: seed 결정성")
    a1, b1 = stratified_shuffle(7)
    a2, b2 = stratified_shuffle(7)
    a3, b3 = stratified_shuffle(8)
    assert_eq("same seed → same block A", a1, a2)
    assert_eq("same seed → same block B", b1, b2)
    assert_true("different seed → different order (likely)", a1 != a3 or b1 != b3,
                detail="seeds 7 vs 8 collided which is statistically improbable")
    # 셔플 후에도 길이·구성원 보존
    assert_eq("shuffle preserves BLOCK_A members", sorted(a1), sorted(BLOCK_A))
    assert_eq("shuffle preserves BLOCK_B members", sorted(b1), sorted(BLOCK_B))


def t03_type7_dominant_with_8_wing():
    """프롬프트 3: 'Type 7 우세 + 8 윙' 시나리오 — 열정가 7w8"""
    REPORT.append("\n[T03] Type 7 우세 + 8 윙: 7w8")
    answers = {}
    # T7 (Q19,Q20) 둘 다 5
    answers["Q19"] = 5; answers["Q20"] = 5
    # T8 인접 — Q22, Q23 모두 4 (8쪽 6점 → 4쪽보다 클 것)
    answers["Q22"] = 4; answers["Q23"] = 4
    # T6 인접 — Q16, Q17 모두 2
    answers["Q16"] = 2; answers["Q17"] = 2
    # 나머지는 모두 3
    rest_qs = ["Q01","Q02","Q04","Q05","Q07","Q08","Q10","Q11","Q13","Q14","Q25","Q26"]
    for q in rest_qs:
        answers[q] = 3
    r = build_result(answers, use_full_27=False)
    assert_eq("primary", r["primary"], 7)
    assert_eq("wing", r["wing"], 8)
    assert_eq("combination", r["wing_combination"], "7w8")
    assert_eq("stress arrow → 1", r["stress_arrow_to"], 1)
    assert_eq("growth arrow → 5", r["growth_arrow_to"], 5)
    assert_eq("center is Thinking", r["center_en"], "Thinking Triad")
    assert_eq("type name en", r["type_name_en"], "The Enthusiast")


def t04_type9_dominant_with_1_wing():
    """프롬프트 4: 'Type 9 우세 + 1 윙' — 평화주의자 9w1"""
    REPORT.append("\n[T04] Type 9 + 1 윙: 9w1")
    answers = {q: 2 for q in BLOCK_A}
    answers["Q25"] = 5; answers["Q26"] = 5  # T9
    answers["Q01"] = 4; answers["Q02"] = 4  # T1 (인접 1)
    answers["Q22"] = 3; answers["Q23"] = 3  # T8 (인접 2)
    r = build_result(answers, use_full_27=False)
    assert_eq("primary", r["primary"], 9)
    assert_eq("wing", r["wing"], 1)
    assert_eq("combination", r["wing_combination"], "9w1")
    assert_eq("stress arrow → 6", r["stress_arrow_to"], 6)
    assert_eq("growth arrow → 3", r["growth_arrow_to"], 3)
    assert_eq("center is Instinctive", r["center_en"], "Instinctive Triad")


def t05_tiebreaker_via_27():
    """프롬프트 5: 18문항에서 동점 → 27문항으로 해소"""
    REPORT.append("\n[T05] 동점 해소: 18에서 동점 → 27 추가")
    # T3와 T6 동점 시나리오
    answers18 = {q: 2 for q in BLOCK_A}
    answers18["Q07"] = 5; answers18["Q08"] = 5  # T3 합 10
    answers18["Q16"] = 5; answers18["Q17"] = 5  # T6 합 10
    r18 = build_result(answers18, use_full_27=False)
    assert_eq("18 status", r18["status"], "needs_tiebreaker")
    assert_eq("tied types", r18["tied_types"], [3, 6])
    # 27 풀: Q09(T3)=5, Q18(T6)=2 → T3 우세
    answers27 = dict(answers18)
    for q in BLOCK_B:
        answers27[q] = 2
    answers27["Q09"] = 5  # T3 추가 5
    answers27["Q18"] = 2  # T6 추가 2
    r27 = build_result(answers27, use_full_27=True)
    assert_eq("27 status", r27["status"], "complete")
    assert_eq("27 primary", r27["primary"], 3)


def t06_wing_tie_options():
    """프롬프트 6: 윙 동점 시 두 후보 옵션 제공"""
    REPORT.append("\n[T06] 윙 동점: 두 후보 제시")
    answers = {q: 2 for q in BLOCK_A}
    answers["Q22"] = 5; answers["Q23"] = 5  # T8 합 10
    answers["Q19"] = 4; answers["Q20"] = 4  # T7 (인접 1) 합 8
    answers["Q25"] = 4; answers["Q26"] = 4  # T9 (인접 2) 합 8
    r = build_result(answers, use_full_27=False)
    assert_eq("primary", r["primary"], 8)
    assert_true("wing_tie", r["wing_tie"], detail=f"got {r}")
    assert_eq("wing options", sorted(r["wing_options"]), sorted(["8w7", "8w9"]))


def t07_invalid_likert_rejected():
    """프롬프트 7: Likert 범위 외 입력 거절"""
    REPORT.append("\n[T07] 잘못된 Likert: 거절")
    answers = {q: 3 for q in BLOCK_A}
    answers["Q01"] = 7  # out of range
    answers["Q05"] = 0  # out of range
    r = build_result(answers, use_full_27=False)
    assert_eq("status error", r["status"], "error")
    assert_true("Q01 caught", any("Q01" in e for e in r["errors"]))
    assert_true("Q05 caught", any("Q05" in e for e in r["errors"]))


def t08_missing_answer_rejected():
    """프롬프트 8: 응답 누락 거절"""
    REPORT.append("\n[T08] 누락 응답: 거절")
    answers = {q: 3 for q in BLOCK_A}
    del answers["Q14"]
    r = build_result(answers, use_full_27=False)
    assert_eq("status error", r["status"], "error")
    assert_true("Q14 missing caught", any("Q14" in e for e in r["errors"]))


def t09_lookup_type5_secular():
    """프롬프트 9: Type 5 단독 룩업 (secular 모드)"""
    REPORT.append("\n[T09] 유형 단독 룩업: Type 5 / 5w4 / secular")
    out = dump_type(5, 4, mode="secular")
    assert_eq("primary", out["primary"], 5)
    assert_eq("wing", out["wing"], 4)
    assert_true("growth_path length 4", len(out["growth_path"]) == 4)
    assert_true("wing combo 5w4 text non-empty", len(out["wing_combination_text"]) > 10)
    assert_eq("background figures (secular)", out["background"]["figures"],
              SECULAR_BACKGROUND[5]["figures"])
    # 5w4 텍스트 일치 확인
    assert_eq("wing combo key", out["wing_combination_key"], "5w4")
    assert_eq("wing combo text exact", out["wing_combination_text"], WING_COMBO["5w4"])


def t10_full_arrow_and_center_matrix():
    """프롬프트 10: 9유형 전체의 화살·센터·인접·욕구·두려움 매트릭스 검증"""
    REPORT.append("\n[T10] 9유형 전체 매트릭스: 화살·센터·인접·욕구·두려움")
    # 표준 (Riso-Hudson 1996/1999)
    expected_stress = {1: 4, 2: 8, 3: 9, 4: 2, 5: 7, 6: 3, 7: 1, 8: 5, 9: 6}
    expected_growth = {1: 7, 2: 4, 3: 6, 4: 1, 5: 8, 6: 9, 7: 5, 8: 2, 9: 3}
    expected_neighbors = {1: (9, 2), 2: (1, 3), 3: (2, 4), 4: (3, 5),
                          5: (4, 6), 6: (5, 7), 7: (6, 8), 8: (7, 9), 9: (8, 1)}
    expected_center = {1: "Instinctive", 2: "Feeling", 3: "Feeling", 4: "Feeling",
                       5: "Thinking", 6: "Thinking", 7: "Thinking",
                       8: "Instinctive", 9: "Instinctive"}
    for t in range(1, 10):
        assert_eq(f"Type {t} stress", STRESS_ARROW[t], expected_stress[t])
        assert_eq(f"Type {t} growth", GROWTH_ARROW[t], expected_growth[t])
        assert_eq(f"Type {t} neighbors", WING_NEIGHBORS[t], expected_neighbors[t])
        # 센터 검증
        center_label = CENTER[t][0].split()[0]  # "본능", "감정", "사고"
        center_map = {"본능": "Instinctive", "감정": "Feeling", "사고": "Thinking"}
        assert_eq(f"Type {t} center", center_map[center_label], expected_center[t])
        # core desire/fear 비어있지 않음
        assert_true(f"Type {t} CORE_DESIRE non-empty", len(CORE_DESIRE[t]) > 10)
        assert_true(f"Type {t} CORE_FEAR non-empty", len(CORE_FEAR[t]) > 10)
        # world_sought 3개 언어 모두
        assert_true(f"Type {t} WORLD_KO non-empty", len(WORLD_SOUGHT_KO[t]) > 5)
        assert_true(f"Type {t} WORLD_EN non-empty", len(WORLD_SOUGHT_EN[t]) > 5)
        assert_true(f"Type {t} WORLD_ZH non-empty", len(WORLD_SOUGHT_ZH[t]) > 5)


def t11_language_detection():
    """프롬프트 11: 언어 자동 감지 결정론 함수"""
    REPORT.append("\n[T11] 언어 감지: ko/en/zh 결정성")
    assert_eq("Korean text → ko", detect_language("저는 에니어그램 검사를 하고 싶어요"), "ko")
    assert_eq("English text → en", detect_language("I want to take the Enneagram test"), "en")
    assert_eq("Chinese text → zh", detect_language("我想做九型人格测试"), "zh")
    assert_eq("Empty → ko default", detect_language(""), "ko")
    assert_eq("Mixed (mostly Korean) → ko",
              detect_language("Enneagram 테스트 하고 싶습니다"), "ko")


def t12_religion_neutral_detection():
    """프롬프트 12: 종교 중립 키워드 감지"""
    REPORT.append("\n[T12] 종교 중립 키워드 감지")
    assert_true("'종교 없음' 감지", detect_religion_neutral("저는 종교 없음으로 진행해주세요"))
    assert_true("'no religion' 감지", detect_religion_neutral("I have no religion, please skip"))
    assert_true("'skip bible' 감지", detect_religion_neutral("Please skip bible references"))
    assert_true("'secular' 감지", detect_religion_neutral("Use secular mode please"))
    assert_true("'무종교' 감지", detect_religion_neutral("무종교입니다"))
    assert_true("일반 입력은 통과", not detect_religion_neutral("저는 에니어그램 5번이에요"))
    assert_true("Empty 통과", not detect_religion_neutral(""))


def t13_score_input_parsing():
    """프롬프트 13: 유형 B 점수 입력 파싱"""
    REPORT.append("\n[T13] 유형 B 점수 파싱")
    # 정상 입력
    text = "Type 4=12, Type 1=10, Type 2=8, Type 3=6, Type 5=11, Type 6=9, Type 7=7, Type 8=5, Type 9=4"
    parsed = parse_score_input(text)
    assert_true("9 types parsed", parsed is not None and len(parsed) == 9)
    if parsed:
        assert_eq("Type 4 score", parsed[4], 12)
        assert_eq("Type 5 score", parsed[5], 11)
        # 그 점수를 decide_from_scores에 넣으면 Type 4 우세 + 5 윙(4의 인접 3,5 중 5가 더 큼)
        r = decide_from_scores(parsed)
        assert_eq("primary from scores", r["primary"], 4)
        assert_eq("wing from scores", r["wing"], 5)
        assert_eq("combination from scores", r["wing_combination"], "4w5")
    # 짧은 표기
    parsed2 = parse_score_input("1=10 2=8 3=6 4=12 5=11 6=9 7=7 8=5 9=4")
    assert_true("short form parsed", parsed2 is not None)
    # 부분 입력 (실패해야 함)
    parsed3 = parse_score_input("Type 4=12, Type 1=10")
    assert_true("partial input rejected", parsed3 is None)
    # 범위 초과 점수 (실패해야 함)
    parsed4 = parse_score_input("1=10 2=8 3=6 4=99 5=11 6=9 7=7 8=5 9=4")
    assert_true("out-of-range score rejected", parsed4 is None)


def t14_lookup_all_18_wing_combos():
    """프롬프트 14: 18개 윙 조합 텍스트 모두 존재 + 비어있지 않음"""
    REPORT.append("\n[T14] 18 윙 조합 텍스트 모두 존재")
    from enneagram_lookup import WING_COMBO
    expected = ["1w9", "1w2", "2w1", "2w3", "3w2", "3w4",
                "4w3", "4w5", "5w4", "5w6", "6w5", "6w7",
                "7w6", "7w8", "8w7", "8w9", "9w8", "9w1"]
    for combo in expected:
        assert_true(f"{combo} 존재", combo in WING_COMBO, detail=f"WING_COMBO keys: {list(WING_COMBO.keys())}")
        assert_true(f"{combo} 비어있지 않음", len(WING_COMBO.get(combo, "")) > 20)
    assert_eq("총 18개", len(WING_COMBO), 18)


def t15_round_trip_consistency():
    """프롬프트 15: 셔플 → 응답 → 점수 → 결과의 라운드트립 일관성"""
    REPORT.append("\n[T15] 라운드트립 일관성: 셔플과 무관하게 같은 결과")
    # 동일한 응답을 다른 seed의 셔플로 받아도 점수는 같아야 한다
    answers = {}
    for qid in BLOCK_A:
        t_id = QUESTIONS_KO[qid][0]
        answers[qid] = 5 if t_id == 6 else 2  # Type 6 우세
    r1 = build_result(answers, use_full_27=False)
    r2 = build_result(answers, use_full_27=False)  # 같은 응답, 같은 결과
    assert_eq("동일 응답은 동일 결과", r1, r2)
    assert_eq("primary=6", r1["primary"], 6)
    # 셔플 seed가 달라도 응답 dict는 qid 키이므로 셔플 무관
    a1, b1 = stratified_shuffle(99)
    a2, b2 = stratified_shuffle(100)
    assert_eq("셔플 seed 99 != 100 produces different orders (likely)",
              a1 != a2 or b1 != b2, True)


def run_all():
    tests = [t01_data_integrity, t02_shuffle_reproducibility, t03_type7_dominant_with_8_wing,
             t04_type9_dominant_with_1_wing, t05_tiebreaker_via_27, t06_wing_tie_options,
             t07_invalid_likert_rejected, t08_missing_answer_rejected, t09_lookup_type5_secular,
             t10_full_arrow_and_center_matrix,
             t11_language_detection, t12_religion_neutral_detection, t13_score_input_parsing,
             t14_lookup_all_18_wing_combos, t15_round_trip_consistency]
    for fn in tests:
        try:
            fn()
        except Exception as e:
            global FAIL
            FAIL += 1
            REPORT.append(f"  FAIL — {fn.__name__} exception: {e!r}")
    print("\n".join(REPORT))
    print(f"\n===== TOTAL: {PASS} PASS / {FAIL} FAIL =====")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all()
