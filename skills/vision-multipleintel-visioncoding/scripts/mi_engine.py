"""
Vision Multiple Intelligence (Howard Gardner) — Deterministic Engine

본 모듈은 vision-multipleintel-visioncoding 스킬의 모든 결정론적 단계를 처리한다.
LLM 자연어 추론으로 처리하면 할루시네이션이 발생할 수 있는 다음 단계를
파이썬으로 환원해 SKILL.md에서 호출하게 한다.

처리 단계 (모두 결정론):
  1) load_catalog()           — 27문항 카탈로그 로드
  2) stratified_select(seed)  — 9지능 × 각 2문항 = 18문항 층화 무작위 선발
  3) order_rounds(items)      — 라운드 단위(3문항) 동일 지능 중복 방지 배치
  4) validate_likert(value)   — 1~5 정수 검증
  5) score_round1(answers)    — 1차 18문항 점수 (지능별 2문항 합, 2~10)
  6) detect_top4_ties(scores) — 상위 4위 안 동점 검사
  7) score_full(answers)      — 27문항 점수 (지능별 3문항 합, 3~15)
  8) strength_label(score, total_items) — 점수 → 강도 라벨
  9) top_dominant(scores, k)  — 상위 K 우세 지능 (동점 시 공동 우세)

CLI:
  python3 mi_engine.py select --seed 42
  python3 mi_engine.py score --answers '{"Q01":4,"Q02":3,...}'
  python3 mi_engine.py label --score 13 --items 3
  python3 mi_engine.py top --scores '{"Linguistic":13,...}' --k 4

출처: SOURCES.md — Gardner Frames of Mind (1983) + Intelligence Reframed (1999)
"""

from __future__ import annotations
import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "mi_catalog.json")

INTELLIGENCES = [
    "Linguistic",
    "Logical-Mathematical",
    "Spatial",
    "Musical",
    "Bodily-Kinesthetic",
    "Interpersonal",
    "Intrapersonal",
    "Naturalist",
    "Existential",
]

# ───────────────────────── 카탈로그 ─────────────────────────

def load_catalog(path: str = DATA_PATH) -> Dict[str, Any]:
    """27문항 카탈로그를 로드한다. 무결성도 검증한다."""
    abs_path = os.path.abspath(path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"카탈로그 파일 없음: {abs_path}")
    with open(abs_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 무결성 검증
    items = data["items"]
    if len(items) != 27:
        raise ValueError(f"카탈로그는 27문항이어야 함, 현재 {len(items)}")
    qids = [it["qid"] for it in items]
    if len(set(qids)) != 27:
        raise ValueError("QID 중복 발견")
    intel_qids = data["intelligence_qids"]
    if set(intel_qids.keys()) != set(INTELLIGENCES):
        raise ValueError(f"intelligence_qids 키가 9지능과 불일치")
    for intel, qs in intel_qids.items():
        if len(qs) != 3:
            raise ValueError(f"{intel}에 3문항이 아님: {qs}")
    return data


def _items_by_intelligence(catalog: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """지능별로 문항 객체를 묶어 반환한다."""
    by_intel: Dict[str, List[Dict[str, Any]]] = {k: [] for k in INTELLIGENCES}
    qid_to_item = {it["qid"]: it for it in catalog["items"]}
    for intel, qs in catalog["intelligence_qids"].items():
        for q in qs:
            by_intel[intel].append(qid_to_item[q])
    return by_intel


# ───────────────────────── 층화 무작위 선발 ─────────────────────────

def stratified_select(seed: int, catalog: Optional[Dict[str, Any]] = None) -> Dict[str, List[str]]:
    """
    9지능 각각의 3문항 중 2문항을 시드 기반으로 결정론적으로 선발한다.
    반환:
      {
        "selected_18": [QID, ...] (총 18개, 9지능 × 2),
        "reserved_9":  [QID, ...] (총 9개, 9지능 × 1 — 동점 해소용)
      }
    수학적 보장: 각 지능에서 정확히 2문항이 selected_18에 포함된다.
    """
    if catalog is None:
        catalog = load_catalog()
    by_intel = _items_by_intelligence(catalog)

    rng = random.Random(seed)
    selected_18: List[str] = []
    reserved_9: List[str] = []

    for intel in INTELLIGENCES:
        qs = [it["qid"] for it in by_intel[intel]]
        if len(qs) != 3:
            raise ValueError(f"{intel}: 3문항이 아님 ({len(qs)})")
        # 결정론: 정렬한 후 RNG로 2개를 뽑는다.
        qs_sorted = sorted(qs)
        rng.shuffle(qs_sorted)
        selected_18.extend(qs_sorted[:2])
        reserved_9.append(qs_sorted[2])

    if len(selected_18) != 18 or len(reserved_9) != 9:
        raise AssertionError("층화 선발 결과 크기 오류")

    # 각 지능에서 정확히 2문항이 selected_18에 있는지 자기검증
    selected_set = set(selected_18)
    for intel, qs in catalog["intelligence_qids"].items():
        count = sum(1 for q in qs if q in selected_set)
        if count != 2:
            raise AssertionError(f"{intel}: selected에 {count}문항 (2여야 함)")

    return {"selected_18": selected_18, "reserved_9": reserved_9}


# ───────────────────────── 라운드 배치 (지능 중복 방지) ─────────────────────────

def order_rounds(selected_qids: List[str], seed: int, catalog: Optional[Dict[str, Any]] = None,
                 round_size: int = 3) -> List[List[str]]:
    """
    선발된 문항을 라운드 단위(기본 3문항)로 배치하되,
    같은 라운드에 동일 지능 2문항이 동시에 들어가지 않도록 결정론적으로 정렬한다.

    반환: [[Q?, Q?, Q?], [Q?, Q?, Q?], ...] (총 len/round_size 라운드)
    """
    if catalog is None:
        catalog = load_catalog()
    qid_to_intel = {it["qid"]: it["intel"] for it in catalog["items"]}
    n = len(selected_qids)
    if n % round_size != 0:
        raise ValueError(f"선발 문항 수 {n}이 라운드 크기 {round_size}로 나누어떨어지지 않음")
    n_rounds = n // round_size

    # 결정론 셔플 시드
    rng = random.Random(seed)
    pool = sorted(selected_qids)  # 정렬 후 셔플로 시드 의존
    rng.shuffle(pool)

    # 그리디: 매 자리마다 현재 라운드에 없는 지능 중 첫 후보를 선택.
    # 후보 부족 시 다음 라운드로 넘어가게 백트래킹.
    rounds: List[List[str]] = [[] for _ in range(n_rounds)]
    round_intels: List[set] = [set() for _ in range(n_rounds)]

    # 라운드를 채워간다: 각 자리에 대해 가능한 문항을 순차 시도.
    placed = [False] * len(pool)

    def backtrack(round_idx: int, slot_idx: int) -> bool:
        if round_idx == n_rounds:
            return True
        if slot_idx == round_size:
            return backtrack(round_idx + 1, 0)
        for i, qid in enumerate(pool):
            if placed[i]:
                continue
            intel = qid_to_intel[qid]
            if intel in round_intels[round_idx]:
                continue
            rounds[round_idx].append(qid)
            round_intels[round_idx].add(intel)
            placed[i] = True
            if backtrack(round_idx, slot_idx + 1):
                return True
            rounds[round_idx].pop()
            round_intels[round_idx].discard(intel)
            placed[i] = False
        return False

    if not backtrack(0, 0):
        raise RuntimeError("라운드 배치 실패 — 입력 구성에 모순이 있음")

    # 자기검증: 모든 라운드에서 지능 중복 없음
    for r_idx, r in enumerate(rounds):
        intels = [qid_to_intel[q] for q in r]
        if len(intels) != len(set(intels)):
            raise AssertionError(f"라운드 {r_idx+1}에 지능 중복: {intels}")
    return rounds


# ───────────────────────── Likert 검증 ─────────────────────────

def validate_likert(value: Any) -> int:
    """1~5 정수 검증. 부적합하면 ValueError."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Likert 값은 정수 1~5여야 함, 현재: {value!r}")
    if not (1 <= v <= 5):
        raise ValueError(f"Likert 값은 1~5 범위여야 함, 현재: {v}")
    return v


def parse_round_input(text: str, expected_count: int) -> List[int]:
    """
    한 라운드 응답 문자열을 파싱하여 1~5 정수 리스트로 반환한다.
    허용 구분자: 쉼표·공백·세미콜론. 부족·초과 시 ValueError.
    """
    if not text or not str(text).strip():
        raise ValueError("빈 입력")
    cleaned = str(text).replace(",", " ").replace(";", " ").replace("\t", " ")
    tokens = [t for t in cleaned.split() if t]
    if len(tokens) != expected_count:
        raise ValueError(f"이 라운드는 {expected_count}개 응답 필요, 입력 {len(tokens)}개")
    return [validate_likert(t) for t in tokens]


# ───────────────────────── 점수 산출 ─────────────────────────

def score_round1(answers: Dict[str, int], selected_18: List[str],
                 catalog: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    1차 18문항 응답을 받아 지능별 2문항 합(2~10)을 반환한다.
    answers: {QID: 1~5} 형식. 누락 시 ValueError.
    """
    if catalog is None:
        catalog = load_catalog()
    qid_to_intel = {it["qid"]: it["intel"] for it in catalog["items"]}

    missing = [q for q in selected_18 if q not in answers]
    if missing:
        raise ValueError(f"18문항 응답 누락: {missing}")

    for q in selected_18:
        validate_likert(answers[q])

    scores: Dict[str, int] = {k: 0 for k in INTELLIGENCES}
    counts: Dict[str, int] = {k: 0 for k in INTELLIGENCES}
    for q in selected_18:
        intel = qid_to_intel[q]
        scores[intel] += int(answers[q])
        counts[intel] += 1
    for intel, c in counts.items():
        if c != 2:
            raise AssertionError(f"{intel}: 응답 {c}건 (2여야 함)")
    return scores


def score_full(answers: Dict[str, int], catalog: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
    """
    27문항 전체 응답을 받아 지능별 3문항 합(3~15)을 반환한다.
    """
    if catalog is None:
        catalog = load_catalog()
    all_qids = [it["qid"] for it in catalog["items"]]
    missing = [q for q in all_qids if q not in answers]
    if missing:
        raise ValueError(f"27문항 응답 누락: {missing}")

    for q in all_qids:
        validate_likert(answers[q])

    qid_to_intel = {it["qid"]: it["intel"] for it in catalog["items"]}
    scores: Dict[str, int] = {k: 0 for k in INTELLIGENCES}
    counts: Dict[str, int] = {k: 0 for k in INTELLIGENCES}
    for q in all_qids:
        intel = qid_to_intel[q]
        scores[intel] += int(answers[q])
        counts[intel] += 1
    for intel, c in counts.items():
        if c != 3:
            raise AssertionError(f"{intel}: 응답 {c}건 (3여야 함)")
    return scores


# ───────────────────────── 동점 검사 ─────────────────────────

def detect_top4_ties(scores: Dict[str, int]) -> Dict[str, Any]:
    """
    상위 4위 안에 동점이 있는지 결정론적으로 검사한다.
    반환:
      {
        "has_tie": bool,
        "top4_strict": [(intel, score)...],  # 동점 여부 무시한 단순 정렬 상위 4
        "tied_at_boundary": [intel,...],     # 4위 경계에서 동점에 걸린 지능
        "expanded_top": [(intel, score)...]  # 동점 포함 확장 상위 (공동 우세 대상)
      }
    """
    if set(scores.keys()) != set(INTELLIGENCES):
        raise ValueError(f"scores 키가 9지능과 불일치: {sorted(scores.keys())}")
    # 점수 내림차순 → 동점 시 지능 알파벳 오름차순 (결정론 안정)
    sorted_pairs = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    top4_strict = sorted_pairs[:4]
    fourth_score = top4_strict[-1][1]

    # 4위 경계 동점: 5위 이하 중 4위 점수와 같은 항목들
    boundary_intels = [intel for intel, s in sorted_pairs[4:] if s == fourth_score]

    # 상위 1~3 안 내부 동점도 함께 검사 (사용자에게 고지 목적)
    internal_ties = False
    seen_scores: List[int] = []
    for _, s in top4_strict:
        if s in seen_scores:
            internal_ties = True
            break
        seen_scores.append(s)

    has_tie = bool(boundary_intels) or internal_ties

    expanded_top = list(top4_strict)
    for intel in boundary_intels:
        expanded_top.append((intel, fourth_score))

    return {
        "has_tie": has_tie,
        "top4_strict": top4_strict,
        "tied_at_boundary": boundary_intels,
        "expanded_top": expanded_top,
    }


# ───────────────────────── 강도 라벨 ─────────────────────────

# SKILL.md 기준표 — 변경 시 SKILL.md 표도 함께 갱신할 것
_LABELS_2Q = [
    (9, 10, "Outstanding"),
    (7, 8,  "Strong"),
    (5, 6,  "Above Average"),
    (4, 4,  "Solid"),
    (3, 3,  "Moderate"),
    (2, 2,  "Developing"),
]
_LABELS_3Q = [
    (14, 15, "Outstanding"),
    (12, 13, "Strong"),
    (10, 11, "Above Average"),
    (8,  9,  "Solid"),
    (6,  7,  "Moderate"),
    (3,  5,  "Developing"),
]


def strength_label(score: int, total_items: int) -> str:
    """
    점수와 합산 문항수(2 또는 3)에 따른 강도 라벨을 반환한다.
    """
    if total_items == 2:
        if not (2 <= score <= 10):
            raise ValueError(f"2문항 합 점수 범위는 2~10, 입력: {score}")
        table = _LABELS_2Q
    elif total_items == 3:
        if not (3 <= score <= 15):
            raise ValueError(f"3문항 합 점수 범위는 3~15, 입력: {score}")
        table = _LABELS_3Q
    else:
        raise ValueError(f"total_items는 2 또는 3, 입력: {total_items}")
    for lo, hi, label in table:
        if lo <= score <= hi:
            return label
    raise AssertionError(f"라벨 표 누락 구간: score={score}, items={total_items}")


# ───────────────────────── 상위 K 우세 식별 ─────────────────────────

def top_dominant(scores: Dict[str, int], k: int = 4) -> Dict[str, Any]:
    """
    결정론적으로 상위 K 우세 지능을 식별한다.
    K 경계에서 동점이 있으면 동점 지능 전체를 공동 우세(co-dominant)로 포함한다.
    """
    if set(scores.keys()) != set(INTELLIGENCES):
        raise ValueError(f"scores 키가 9지능과 불일치: {sorted(scores.keys())}")
    if k < 1 or k > 9:
        raise ValueError(f"k는 1~9 범위, 입력: {k}")
    sorted_pairs = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    cutoff_score = sorted_pairs[k - 1][1]
    co_dominant = [(intel, s) for intel, s in sorted_pairs if s >= cutoff_score]
    strict_top_k = sorted_pairs[:k]
    has_co = len(co_dominant) > k
    return {
        "strict_top_k": strict_top_k,
        "co_dominant": co_dominant,
        "has_co_dominant": has_co,
        "cutoff_score": cutoff_score,
    }


# ───────────────────────── 점수 범위 자동 판별 (Type B) ─────────────────────────

def infer_score_basis(scores: Dict[str, int]) -> str:
    """
    사용자가 점수만 제공했을 때 2문항(2~10) 기준인지 3문항(3~15) 기준인지 추정.
    한 점수라도 11 이상이면 3문항(3~15), 한 점수라도 1점이면 ambiguous (둘 다 가능하지 않음 — 1점은 부적합),
    최대값이 10 이하이면 ambiguous.
    """
    if not scores:
        raise ValueError("scores 비어 있음")
    vals = list(scores.values())
    for v in vals:
        if v < 2 or v > 15:
            raise ValueError(f"점수 범위 이탈: {v}")
    mx = max(vals)
    mn = min(vals)
    if mx >= 11:
        # 11~15는 3문항 기준에서만 가능
        return "3q"
    if mn < 2:
        # 1은 어느 기준에서도 합으로 불가능 — 이론적 fallthrough
        raise ValueError(f"점수 {mn}은 2문항(2~10) 또는 3문항(3~15) 합으로 발생 불가")
    return "ambiguous"  # 2~10 범위, 양쪽 기준 모두 유효 — 사용자에게 확인 필요


# ───────────────────────── CLI ─────────────────────────

def _cli_select(args: argparse.Namespace) -> None:
    catalog = load_catalog()
    result = stratified_select(args.seed, catalog)
    if args.order:
        rounds = order_rounds(result["selected_18"], args.seed, catalog)
        result["rounds"] = rounds
    if args.translate:
        lang = args.translate
        qid_to_item = {it["qid"]: it for it in catalog["items"]}
        translated = []
        for q in result["selected_18"]:
            it = qid_to_item[q]
            translated.append({"qid": q, "text": it.get(lang) or it["ko"]})
        result["translated"] = translated
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _cli_score(args: argparse.Namespace) -> None:
    catalog = load_catalog()
    answers = json.loads(args.answers)
    if args.full:
        scores = score_full(answers, catalog)
        items = 3
    else:
        if not args.selected:
            raise ValueError("--selected 또는 --full 필요")
        selected_18 = json.loads(args.selected)
        scores = score_round1(answers, selected_18, catalog)
        items = 2
    tie = detect_top4_ties(scores)
    top = top_dominant(scores, k=4)
    out = {
        "scores": scores,
        "items_per_intel": items,
        "labels": {intel: strength_label(s, items) for intel, s in scores.items()},
        "ties": tie,
        "top4": top,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def _cli_label(args: argparse.Namespace) -> None:
    print(strength_label(args.score, args.items))


def _cli_top(args: argparse.Namespace) -> None:
    scores = json.loads(args.scores)
    res = top_dominant(scores, k=args.k)
    print(json.dumps(res, ensure_ascii=False, indent=2))


def _cli_validate(args: argparse.Namespace) -> None:
    parsed = parse_round_input(args.input, args.count)
    print(json.dumps(parsed, ensure_ascii=False))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Multiple Intelligences deterministic engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_sel = sub.add_parser("select", help="층화 무작위 18문항 선발")
    p_sel.add_argument("--seed", type=int, required=True)
    p_sel.add_argument("--order", action="store_true", help="라운드 배치도 함께 출력")
    p_sel.add_argument("--translate", type=str, choices=["ko", "en", "zh"], help="문항 텍스트 번역 출력")
    p_sel.set_defaults(func=_cli_select)

    p_sc = sub.add_parser("score", help="응답 점수 산출 + 동점·강도·상위4")
    p_sc.add_argument("--answers", type=str, required=True, help='JSON: {"Q01":4,...}')
    p_sc.add_argument("--selected", type=str, help='1차 점수 — selected_18 JSON 배열')
    p_sc.add_argument("--full", action="store_true", help="27문항 전체 점수 모드")
    p_sc.set_defaults(func=_cli_score)

    p_lb = sub.add_parser("label", help="점수 → 강도 라벨")
    p_lb.add_argument("--score", type=int, required=True)
    p_lb.add_argument("--items", type=int, required=True, choices=[2, 3])
    p_lb.set_defaults(func=_cli_label)

    p_tp = sub.add_parser("top", help="상위 K 우세 식별")
    p_tp.add_argument("--scores", type=str, required=True, help='JSON: {"Linguistic":13,...}')
    p_tp.add_argument("--k", type=int, default=4)
    p_tp.set_defaults(func=_cli_top)

    p_v = sub.add_parser("validate", help="라운드 응답 문자열 파싱·검증")
    p_v.add_argument("--input", type=str, required=True)
    p_v.add_argument("--count", type=int, required=True)
    p_v.set_defaults(func=_cli_validate)

    args = parser.parse_args(argv)
    try:
        args.func(args)
    except ValueError as e:
        # 사용자/호출 LLM이 받을 친절한 오류 (트레이스백 없이 종료코드 2)
        print(json.dumps({"error": str(e), "kind": "ValueError"}, ensure_ascii=False), file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(json.dumps({"error": str(e), "kind": "FileNotFoundError"}, ensure_ascii=False), file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
