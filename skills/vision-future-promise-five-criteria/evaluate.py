#!/usr/bin/env python3
"""
vision-future-promise-five-criteria 결정론 환원 모듈

박사님 『미래준비학교』(2016) 미래 유망성 5기준 평가를 결정론적으로 처리한다.

이 스크립트는 SKILL.md 의사결정 트리 규칙에 따라:
- 5개 기준 점수(1~10)를 입력받아
- 범위 검증
- 종합 점수 계산
- 의사결정 트리 분기 판정
- 박사님 4개 공식 레이블 중 하나로 반환

LLM이 자연어로 점수를 합산하거나 분기 조건을 추론하지 못하도록 차단한다.

Usage:
    python3 evaluate.py --scores 8,7,6,9,7
    python3 evaluate.py --json '{"influence":8,"happiness":7,"wealth":6,"sustainability":9,"competitiveness":7}'
"""
import argparse
import json
import sys
from typing import Dict, List, Tuple


# 박사님 책 5기준 (이름·순서·번호 그대로)
CRITERIA = [
    ("influence", "① 가치 있는 영향력"),
    ("happiness", "② 행복성"),
    ("wealth", "③ 부 가능성"),
    ("sustainability", "④ 지속가능성"),
    ("competitiveness", "⑤ 경쟁력"),
]

# 박사님 책 공식 4개 의사결정 레이블 (임의 변형 금지)
LABEL_STRONG = "★ 강력 권장 비전 영역"
LABEL_CONSIDER = "○ 고려 가능"
LABEL_REVIEW = "△ 재검토 필요"
LABEL_AVOID = "✗ 회피"

OFFICIAL_LABELS = (LABEL_STRONG, LABEL_CONSIDER, LABEL_REVIEW, LABEL_AVOID)


def validate_scores(scores: Dict[str, float]) -> List[str]:
    """점수 입력 검증. 오류 리스트 반환(빈 리스트면 통과)."""
    errors: List[str] = []
    required_keys = [k for k, _ in CRITERIA]
    for key in required_keys:
        if key not in scores:
            errors.append(f"필수 기준 누락: {key}")
            continue
        val = scores[key]
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            errors.append(f"{key}: 숫자 아님 ({val!r})")
            continue
        if val < 1 or val > 10:
            errors.append(f"{key}: 범위 위반 (1~10 필요, 입력: {val})")
    extra = set(scores.keys()) - set(required_keys)
    if extra:
        errors.append(f"불필요 키: {sorted(extra)}")
    return errors


def evaluate(scores: Dict[str, float]) -> Dict:
    """
    박사님 책 의사결정 트리 결정론 적용.

    규칙(SKILL.md 3단계):
      1. 5기준 모두 7점+ → ★ 강력 권장 비전 영역
      2. 4기준 7점+, 1기준 5~6점 → ○ 고려 가능
      3. 1~2기준 4점 이하 → △ 재검토 필요
      4. ⑤(경쟁력) 100:1 + ①~④ 미충족 → ✗ 회피
         결정론 환원:
           - ⑤ 100:1 시그널: competitiveness ≤ 4
           - ①~④ 미충족: 박사님 책 Rule 1·2의 "충족" = 7점+이므로
             ①~④ 중 1개라도 7점 미만이면 미충족
           - 단, "①~④ 모두 7점+ + ⑤ ≤ 4" 경계 케이스(박사님 책
             100:1 영역 선택 조건 충족 케이스)는 Rule 4 미적용 →
             경계 케이스로 처리되어 △ 재검토 + 100:1 도전 보완 권유

    우선순위:
      Rule 4 (회피) > Rule 3 (재검토) > Rule 1 (강력 권장) > Rule 2 (고려 가능)
      더 보수적인 판정이 우선한다.
      매칭 없으면 → 경계선 케이스 안내(공식 레이블 중 가장 가까운 것 + 보완 권유)
    """
    errors = validate_scores(scores)
    if errors:
        return {
            "ok": False,
            "errors": errors,
            "label": None,
            "scores": scores,
        }

    # 5기준 점수 추출 (순서 보존)
    pairs = [(label, scores[key]) for key, label in CRITERIA]
    values = [v for _, v in pairs]
    influence, happiness, wealth, sustainability, competitiveness = values

    sum_score = sum(values)
    avg_score = sum_score / len(values)

    # 결정론적 분기 변수
    count_seven_plus = sum(1 for v in values if v >= 7)
    count_five_to_six = sum(1 for v in values if 5 <= v < 7)
    count_four_or_less = sum(1 for v in values if v <= 4)

    # 보수성 우선 (회피→재검토→강권→고려)
    # Rule 4: 경쟁력 ≤ 4점(100:1 시그널) + ①~④ 중 1개 이상이 7점 미만(미충족)
    # 박사님 책 Rule 1·2에서 "충족" = 7점+이므로 Rule 4 "미충족"도 7점 미만으로 환원
    others = [influence, happiness, wealth, sustainability]
    others_less_than_seven = sum(1 for v in others if v < 7)
    others_all_seven_plus = all(v >= 7 for v in others)

    if competitiveness <= 4 and others_less_than_seven >= 1:
        label = LABEL_AVOID
        reason = (
            f"⑤ 경쟁력 {competitiveness}점(≤4, 100:1 시그널)에서 "
            f"①~④ 중 {others_less_than_seven}개가 7점 미만(미충족). "
            f"박사님 책 100:1 영역 전제(①~④ 모두 7점+ 충족) 미달."
        )
        rule_id = 4
    elif competitiveness <= 4 and others_all_seven_plus:
        # 박사님 책 "100:1 영역 선택 조건" 충족 케이스
        # (⑤ ≤ 4 + ①~④ 모두 7점+)
        # 박사님 책 4규칙에 정확 매칭 없음. ⑤도 ≤ 4점이므로 Rule 3(1~2개 ≤4)
        # 매칭 — △ 재검토 + 100:1 도전 안내
        label = LABEL_REVIEW
        reason = (
            f"⑤ 경쟁력 {competitiveness}점(≤4, 100:1 시그널)이지만 "
            f"①~④ 모두 7점+ 충족. 박사님 책 '100:1 영역 선택 조건'에 부합하는 "
            f"도전형 케이스. ⑤ 경쟁력 향상 전략(전문성·차별화·니치 발굴)을 "
            f"함께 고려하시면 ★ 강력 권장 구간 진입 가능."
        )
        rule_id = "3-100to1-challenge"
    elif count_four_or_less >= 1 and count_four_or_less <= 2:
        label = LABEL_REVIEW
        reason = f"기준 중 {count_four_or_less}개가 4점 이하 (재검토 필요)."
        rule_id = 3
    elif count_seven_plus == 5:
        label = LABEL_STRONG
        reason = "5기준 모두 7점 이상."
        rule_id = 1
    elif count_seven_plus == 4 and count_five_to_six == 1:
        label = LABEL_CONSIDER
        reason = "4기준 7점 이상, 1기준 5~6점."
        rule_id = 2
    else:
        # 경계선 케이스: 공식 4규칙 어디에도 정확히 매칭되지 않는 케이스
        # 박사님 책 정신: 5점은 "평균" 점수. "특별히 유망한 영역" 가려야 하므로
        # 7점+이 부족한 케이스는 △ 재검토가 박사님 정신에 더 부합한다.
        # SKILL.md 3단계 "주의" 규정: 공식 4개 레이블 외 표현 금지 +
        # "경계선 케이스는 가장 가까운 레이블 + 보완 권유"
        # 박사님 책 정신: Rule 1(5개 ≥7)·Rule 2(4개 ≥7, 1개 5~6) 이외는
        # "특별히 유망"한 영역으로 보기 어려움. SKILL.md 3단계 주의에 따라
        # 가장 가까운 공식 레이블 + 보완 권유 형식으로 안내한다.
        if count_four_or_less >= 3:
            label = LABEL_REVIEW
            reason = (
                f"기준 중 {count_four_or_less}개가 4점 이하. "
                f"Rule 3 확장 적용. 다수 기준 보완 필요."
            )
            rule_id = "3-extended"
        else:
            # 7점+ ≤ 3개 OR (7점+ 4개 + 1개가 5점 미만이지만 4점 이하 아닌 케이스는 불가능)
            # 즉 7점+이 4개 미만이거나, ≤4점이 1~2개 있으면서 위 Rule 3에 안 걸린 경우
            # 박사님 책 기준 ★/○ 미달 → △ 재검토
            label = LABEL_REVIEW
            gap_to_consider = max(0, 4 - count_seven_plus)
            gap_to_strong = max(0, 5 - count_seven_plus)
            reason = (
                f"공식 Rule 1·2 정확 매칭 없음. 7점+ {count_seven_plus}개, "
                f"5~6점 {count_five_to_six}개, ≤4점 {count_four_or_less}개. "
                f"7점+ 기준이 4개 미만이라 ★/○ 구간 미달. "
                f"가장 가까운 레이블로 △ 재검토 필요로 배정 — "
                f"기준 {gap_to_consider}개를 7점+로 끌어올리시면 ○ 고려 가능, "
                f"{gap_to_strong}개를 끌어올리시면 ★ 강력 권장 진입 가능합니다."
            )
            rule_id = "boundary-review"

    return {
        "ok": True,
        "errors": [],
        "scores": scores,
        "scores_ordered": pairs,
        "sum_score": sum_score,
        "avg_score": round(avg_score, 2),
        "count_seven_plus": count_seven_plus,
        "count_five_to_six": count_five_to_six,
        "count_four_or_less": count_four_or_less,
        "label": label,
        "reason": reason,
        "rule_id": rule_id,
        "official_labels": list(OFFICIAL_LABELS),
    }


def format_report(result: Dict) -> str:
    """평가 결과를 사람이 읽기 좋은 텍스트로 변환."""
    if not result["ok"]:
        lines = ["[입력 오류]"]
        for e in result["errors"]:
            lines.append(f"  - {e}")
        return "\n".join(lines)
    lines = []
    lines.append("=" * 50)
    lines.append("미래 유망성 5기준 평가 (결정론 산출)")
    lines.append("=" * 50)
    for label, val in result["scores_ordered"]:
        lines.append(f"  {label}: {val}점")
    lines.append("-" * 50)
    lines.append(f"  합계: {result['sum_score']}점 (50점 만점)")
    lines.append(f"  평균: {result['avg_score']}점")
    lines.append(f"  7점+ 기준 개수: {result['count_seven_plus']}")
    lines.append(f"  5~6점 기준 개수: {result['count_five_to_six']}")
    lines.append(f"  ≤4점 기준 개수: {result['count_four_or_less']}")
    lines.append("-" * 50)
    lines.append(f"  판정: {result['label']}")
    lines.append(f"  근거: {result['reason']}")
    lines.append(f"  적용 규칙: Rule {result['rule_id']}")
    lines.append("=" * 50)
    return "\n".join(lines)


def parse_scores_arg(arg: str) -> Dict[str, float]:
    """쉼표 5개 점수를 키 순서대로 매핑."""
    parts = [p.strip() for p in arg.split(",")]
    if len(parts) != 5:
        raise ValueError(f"--scores 는 5개 점수가 쉼표로 구분되어야 함 (입력 개수: {len(parts)})")
    result = {}
    for (key, _), p in zip(CRITERIA, parts):
        try:
            result[key] = float(p)
        except ValueError:
            raise ValueError(f"점수 '{p}' 는 숫자가 아님")
    return result


def _self_test() -> int:
    """모든 회귀 케이스에 대한 self-test. 실패 시 비-0 종료코드."""
    cases: List[Tuple[Dict[str, float], str, object]] = [
        # (scores, expected_label, expected_rule_id)
        ({"influence": 9, "happiness": 9, "wealth": 9, "sustainability": 9, "competitiveness": 9}, LABEL_STRONG, 1),
        ({"influence": 7, "happiness": 7, "wealth": 7, "sustainability": 7, "competitiveness": 7}, LABEL_STRONG, 1),
        ({"influence": 8, "happiness": 7, "wealth": 6, "sustainability": 9, "competitiveness": 7}, LABEL_CONSIDER, 2),
        ({"influence": 7, "happiness": 7, "wealth": 7, "sustainability": 7, "competitiveness": 5}, LABEL_CONSIDER, 2),
        # Rule 3: 1~2개 ≤4점, 단 Rule 4 미적용 케이스
        ({"influence": 3, "happiness": 8, "wealth": 7, "sustainability": 9, "competitiveness": 7}, LABEL_REVIEW, 3),
        ({"influence": 4, "happiness": 4, "wealth": 7, "sustainability": 9, "competitiveness": 7}, LABEL_REVIEW, 3),
        # Rule 4: ⑤≤4 + ①~④ 1개 이상 7점 미만
        ({"influence": 3, "happiness": 8, "wealth": 7, "sustainability": 9, "competitiveness": 3}, LABEL_AVOID, 4),
        ({"influence": 8, "happiness": 8, "wealth": 8, "sustainability": 5, "competitiveness": 3}, LABEL_AVOID, 4),
        # Rule 3-100to1-challenge: ⑤≤4 + ①~④ 모두 7점+
        ({"influence": 8, "happiness": 8, "wealth": 8, "sustainability": 8, "competitiveness": 3}, LABEL_REVIEW, "3-100to1-challenge"),
        ({"influence": 7, "happiness": 7, "wealth": 7, "sustainability": 7, "competitiveness": 4}, LABEL_REVIEW, "3-100to1-challenge"),
        # boundary-review: 4규칙 미매칭
        ({"influence": 5, "happiness": 5, "wealth": 5, "sustainability": 5, "competitiveness": 5}, LABEL_REVIEW, "boundary-review"),
        ({"influence": 7, "happiness": 7, "wealth": 7, "sustainability": 5, "competitiveness": 5}, LABEL_REVIEW, "boundary-review"),
        ({"influence": 6, "happiness": 6, "wealth": 6, "sustainability": 6, "competitiveness": 6}, LABEL_REVIEW, "boundary-review"),
        # boundary-review 3-extended
        ({"influence": 3, "happiness": 3, "wealth": 3, "sustainability": 7, "competitiveness": 7}, LABEL_REVIEW, "3-extended"),
        # 점수 범위 위반
        ({"influence": 11, "happiness": 7, "wealth": 7, "sustainability": 7, "competitiveness": 7}, None, None),
        ({"influence": 0, "happiness": 7, "wealth": 7, "sustainability": 7, "competitiveness": 7}, None, None),
        # 필수 키 누락
        ({"influence": 7, "happiness": 7, "wealth": 7, "sustainability": 7}, None, None),
    ]
    failures = []
    for i, (scores, expected_label, expected_rule) in enumerate(cases, 1):
        result = evaluate(scores)
        if expected_label is None:
            # 입력 오류 기대
            if result["ok"]:
                failures.append(f"Case {i}: 입력 오류 기대했으나 통과 — {scores}")
        else:
            if not result["ok"]:
                failures.append(f"Case {i}: 통과 기대했으나 입력 오류 — {scores} / {result['errors']}")
            elif result["label"] != expected_label:
                failures.append(f"Case {i}: label 불일치 — 기대 {expected_label} 실제 {result['label']} / {scores}")
            elif result["rule_id"] != expected_rule:
                failures.append(f"Case {i}: rule_id 불일치 — 기대 {expected_rule} 실제 {result['rule_id']} / {scores}")
    if failures:
        print("[SELF-TEST 실패]")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"[SELF-TEST 통과] {len(cases)}개 케이스 모두 통과")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="미래 유망성 5기준 결정론 평가",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scores",
        help="5개 점수를 쉼표로 (순서: 영향력,행복성,부,지속가능성,경쟁력) 예: 8,7,6,9,7",
    )
    group.add_argument(
        "--json",
        help='JSON 객체. 키: influence, happiness, wealth, sustainability, competitiveness',
    )
    group.add_argument(
        "--self-test",
        action="store_true",
        help="자체 회귀 테스트 실행",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="text",
        help="출력 형식",
    )
    args = parser.parse_args()

    if args.self_test:
        sys.exit(_self_test())

    try:
        if args.scores:
            scores = parse_scores_arg(args.scores)
        else:
            scores = json.loads(args.json)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"[입력 오류] {e}", file=sys.stderr)
        sys.exit(2)

    result = evaluate(scores)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_report(result))

    sys.exit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
