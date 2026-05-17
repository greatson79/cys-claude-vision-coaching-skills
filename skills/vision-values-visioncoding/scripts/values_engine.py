"""values_engine.py — vision-values-visioncoding 결정론 엔진.

SKILL.md가 자연어 LLM 추론으로 처리하면 할루시네이션 위험이 있는 단계들을
결정론 파이썬 함수로 환원한다.  LLM은 본 모듈의 출력을 그대로 인용·표시해야
하며, 매핑·교집합·3선 도출·진단 채점·카탈로그 검증을 자연어로 다시
재구성하지 않는다.

본 모듈이 책임지는 결정론 영역
────────────────────────────────
1. MBTI 16유형 → 가치 7개 조회  (mbti_values.json)
2. 에니어그램 9유형 → 가치 7개 + 추구 세상 조회  (enneagram_values.json)
3. 에니어그램 윙 결합 (가중치 0.5x, 인접 유형만 허용)
4. 다중지능 상위 N개 → 가치 합집합 조회  (mi_values.json)
5. 모드 C 간이 진단 17문항 채점
   - 에니어그램: 1차/윙 후보 추출
   - 다중지능: 상위 3개 결정 (동률 시 알파벳 순)
6. 세 프레임워크 교집합 분석 (3개·2개·1개 등장 분류)
7. 핵심 가치 3선 폴백 규칙(Step 1~5) 결정론 적용
8. 모드 E(박사님 기독교 가치 강조) — Section A 가중치 1.5x
9. 카탈로그 외 가치 존재 검증 (모든 매핑 단어가 catalog에 존재해야 함)
10. 출처 메타데이터 반환

CLI 사용 예
────────────
    python3 values_engine.py validate            # 데이터 무결성 검사
    python3 values_engine.py profile --mbti INFJ --enneagram 1 --mi Linguistic,Intrapersonal,Interpersonal
    python3 values_engine.py screen --enneagram-rank 1,4 --mi-scores 5,3,2,4,2,4,5,3
    python3 values_engine.py catalog              # 카탈로그 단어 전체 출력
    python3 values_engine.py mbti INFJ            # MBTI 가치 조회
    python3 values_engine.py enneagram 1 --wing 9 # 에니어그램+윙 조회
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import Iterable

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


# ──────────────────────────────────────────────────────────────────────────────
# 1. 데이터 로딩
# ──────────────────────────────────────────────────────────────────────────────


def _load(name: str) -> dict:
    path = os.path.normpath(os.path.join(DATA_DIR, name))
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


CATALOG = _load("value_catalog.json")
MBTI = _load("mbti_values.json")
ENNEA = _load("enneagram_values.json")
MI = _load("mi_values.json")
SCREEN = _load("screening_questions.json")
SOURCES = _load("sources.json")

VALID_VALUES: set[str] = set(CATALOG["values"].keys())
VALID_MBTI: set[str] = set(MBTI["types"].keys())
VALID_ENN: set[str] = set(ENNEA["types"].keys())
VALID_MI: set[str] = set(MI["intelligences"].keys())
MI_ALIASES: dict[str, str] = dict(MI["aliases"])

# 박사님 강의·집필 빈도 우선 가치 (폴백 Step 5b)
DOC_FREQ_PRIORITY = ("Wisdom", "Vision", "Stewardship")


# ──────────────────────────────────────────────────────────────────────────────
# 2. 카탈로그 검증
# ──────────────────────────────────────────────────────────────────────────────


def _assert_in_catalog(values: Iterable[str], origin: str) -> None:
    bad = [v for v in values if v not in VALID_VALUES]
    if bad:
        raise ValueError(
            f"[catalog-violation] {origin} contains values not in value_catalog.json: {bad}"
        )


def validate_data() -> dict:
    """모든 데이터의 카탈로그 무결성 + 구조 무결성 검증."""
    errors: list[str] = []

    # MBTI
    expected_mbti = {"INTJ","INTP","ENTJ","ENTP","INFJ","INFP","ENFJ","ENFP",
                     "ISTJ","ISFJ","ESTJ","ESFJ","ISTP","ISFP","ESTP","ESFP"}
    if set(MBTI["types"].keys()) != expected_mbti:
        errors.append(f"MBTI types incomplete: missing={expected_mbti - set(MBTI['types'].keys())}")
    for t, payload in MBTI["types"].items():
        vals = payload["values"]
        if not 5 <= len(vals) <= 7:
            errors.append(f"MBTI {t}: values count {len(vals)} not in 5~7")
        if len(set(vals)) != len(vals):
            errors.append(f"MBTI {t}: duplicate values {vals}")
        try:
            _assert_in_catalog(vals, f"MBTI[{t}]")
        except ValueError as e:
            errors.append(str(e))

    # Enneagram
    for k in [str(i) for i in range(1, 10)]:
        if k not in ENNEA["types"]:
            errors.append(f"Enneagram missing type {k}")
            continue
        payload = ENNEA["types"][k]
        vals = payload["values"]
        if not 5 <= len(vals) <= 7:
            errors.append(f"Enneagram {k}: values count {len(vals)} not in 5~7")
        try:
            _assert_in_catalog(vals, f"Enneagram[{k}]")
        except ValueError as e:
            errors.append(str(e))
        wings = payload.get("wings", [])
        if len(wings) != 2:
            errors.append(f"Enneagram {k}: wings must be 2 adjacent types, got {wings}")
        expected_wings = [(int(k) - 2) % 9 + 1, int(k) % 9 + 1]
        if sorted(wings) != sorted(expected_wings):
            errors.append(f"Enneagram {k}: wings {wings} not adjacent {expected_wings}")

    # MI
    expected_mi = {"Linguistic","Logical-Mathematical","Spatial","Musical",
                   "Bodily-Kinesthetic","Interpersonal","Intrapersonal",
                   "Naturalist","Existential"}
    if set(MI["intelligences"].keys()) != expected_mi:
        errors.append(f"MI intelligences mismatch: {set(MI['intelligences'].keys())} vs {expected_mi}")
    for name, payload in MI["intelligences"].items():
        try:
            _assert_in_catalog(payload["values"], f"MI[{name}]")
        except ValueError as e:
            errors.append(str(e))

    # Screening
    enn_items = SCREEN["enneagram"]["items"]
    if len(enn_items) != 9:
        errors.append(f"Screening enneagram items = {len(enn_items)} (expected 9)")
    types_seen = sorted(item["type"] for item in enn_items)
    if types_seen != list(range(1, 10)):
        errors.append(f"Screening enneagram types {types_seen} != 1..9")
    mi_items = SCREEN["multiple_intelligences"]["items"]
    if len(mi_items) != 8:
        errors.append(f"Screening MI items = {len(mi_items)} (expected 8)")

    return {"ok": not errors, "errors": errors,
            "catalog_count": len(VALID_VALUES),
            "mbti_count": len(MBTI["types"]),
            "enneagram_count": len(ENNEA["types"]),
            "mi_count": len([k for k in MI["intelligences"]])}


# ──────────────────────────────────────────────────────────────────────────────
# 3. 매핑 조회 (할루시네이션 차단 — 매번 동일 결과)
# ──────────────────────────────────────────────────────────────────────────────


def mbti_values(mbti: str) -> list[str]:
    mbti = mbti.upper().strip()
    if mbti not in VALID_MBTI:
        raise ValueError(f"Invalid MBTI '{mbti}'. Valid: {sorted(VALID_MBTI)}")
    return list(MBTI["types"][mbti]["values"])


def enneagram_values(type_num: int | str) -> list[str]:
    k = str(int(type_num))
    if k not in VALID_ENN:
        raise ValueError(f"Invalid Enneagram type '{type_num}'. Valid: 1..9")
    return list(ENNEA["types"][k]["values"])


def enneagram_world(type_num: int | str) -> str:
    k = str(int(type_num))
    return ENNEA["types"][k]["world"]


def enneagram_label(type_num: int | str) -> tuple[str, str]:
    k = str(int(type_num))
    p = ENNEA["types"][k]
    return p["label_en"], p["label_ko"]


def enneagram_allowed_wings(type_num: int | str) -> list[int]:
    k = str(int(type_num))
    return list(ENNEA["types"][k]["wings"])


def resolve_mi_name(name: str) -> str:
    name = name.strip()
    if name in VALID_MI:
        return name
    if name in MI_ALIASES:
        return MI_ALIASES[name]
    raise ValueError(f"Unknown intelligence '{name}'. Valid: {sorted(VALID_MI)}")


def mi_values(intelligences: Iterable[str]) -> list[str]:
    """상위 N개 지능의 가치 합집합. 입력 순서 보존, 중복 제거."""
    seen: list[str] = []
    for raw in intelligences:
        canon = resolve_mi_name(raw)
        for v in MI["intelligences"][canon]["values"]:
            if v not in seen:
                seen.append(v)
    return seen


# ──────────────────────────────────────────────────────────────────────────────
# 4. 윙 결합 (가중치 0.5)
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class WeightedValue:
    value: str
    weight: float
    sources: list[str] = field(default_factory=list)


def enneagram_with_wing(base_type: int | str, wing: int | None) -> list[WeightedValue]:
    """기본 유형 1.0x, 인접 윙 0.5x. 윙은 인접 유형만 허용."""
    base_k = str(int(base_type))
    base_values = enneagram_values(base_k)
    out: dict[str, WeightedValue] = {}
    for v in base_values:
        out[v] = WeightedValue(value=v, weight=1.0, sources=[f"Enneagram-{base_k}"])
    if wing is None:
        return list(out.values())
    allowed = enneagram_allowed_wings(base_k)
    if int(wing) not in allowed:
        raise ValueError(
            f"Wing {wing} not adjacent to type {base_k}. Allowed: {allowed}"
        )
    for v in enneagram_values(int(wing)):
        if v in out:
            out[v].weight += 0.5
            out[v].sources.append(f"Enneagram-{wing}w")
        else:
            out[v] = WeightedValue(value=v, weight=0.5, sources=[f"Enneagram-{wing}w"])
    return list(out.values())


# ──────────────────────────────────────────────────────────────────────────────
# 5. 모드 C 간이 진단 채점
# ──────────────────────────────────────────────────────────────────────────────


def score_enneagram_screening(picks: list[int]) -> dict:
    """입력: 가장 공감 1개(필수) + 두 번째 공감 1개(옵션).
       반환: {primary, wing_candidate, wing_valid_for_primary}.

       wing_candidate가 primary의 인접 유형이 아니면 wing_valid_for_primary=False.
    """
    if not picks:
        raise ValueError("At least one pick required")
    primary = int(picks[0])
    if primary not in range(1, 10):
        raise ValueError(f"Primary must be 1..9, got {primary}")
    wing_candidate = int(picks[1]) if len(picks) > 1 else None
    wing_valid = False
    if wing_candidate is not None:
        if wing_candidate not in range(1, 10):
            raise ValueError(f"Wing candidate must be 1..9, got {wing_candidate}")
        allowed = enneagram_allowed_wings(primary)
        wing_valid = wing_candidate in allowed
    return {"primary": primary,
            "wing_candidate": wing_candidate,
            "wing_valid_for_primary": wing_valid,
            "allowed_wings": enneagram_allowed_wings(primary)}


def score_mi_screening(scores: list[int]) -> dict:
    """8개 점수(1~5)를 입력 받아 상위 3개 지능 결정. 동률 시 카탈로그 순서(JSON 키 순)."""
    items = SCREEN["multiple_intelligences"]["items"]
    if len(scores) != 8:
        raise ValueError(f"Need exactly 8 scores, got {len(scores)}")
    scale = SCREEN["multiple_intelligences"]["scale"]
    for s in scores:
        if not scale["min"] <= int(s) <= scale["max"]:
            raise ValueError(f"Score {s} out of {scale['min']}~{scale['max']}")
    indexed = [(items[i]["intelligence"], int(scores[i]), i) for i in range(8)]
    # 정렬: 점수 내림차순 → 입력 순서 오름차순 (동률 시 카탈로그 순)
    indexed.sort(key=lambda t: (-t[1], t[2]))
    top3 = [t[0] for t in indexed[:3]]
    return {"top3": top3,
            "all_scored": [{"intelligence": n, "score": s} for n, s, _ in indexed]}


# ──────────────────────────────────────────────────────────────────────────────
# 6. 교집합 분석 + 핵심 가치 3선 폴백 규칙
# ──────────────────────────────────────────────────────────────────────────────


@dataclass
class IntersectionResult:
    triple: list[str]       # 3개 프레임워크 모두 등장
    double: list[str]       # 2개 프레임워크 등장
    single_by_fw: dict[str, list[str]]  # 1개 등장 — 프레임워크별
    frequency: dict[str, int]           # 가치별 등장 회수


def analyze_intersection(mbti_vals: list[str] | None,
                         enn_vals: list[str] | None,
                         mi_vals: list[str] | None) -> IntersectionResult:
    """세 프레임워크 가치 집합을 받아 등장 회수별 분류."""
    sets = {}
    if mbti_vals is not None:
        sets["mbti"] = set(mbti_vals)
    if enn_vals is not None:
        sets["enneagram"] = set(enn_vals)
    if mi_vals is not None:
        sets["mi"] = set(mi_vals)
    if not sets:
        raise ValueError("At least one framework must be provided")
    all_values = set().union(*sets.values())
    freq: dict[str, int] = {}
    for v in all_values:
        freq[v] = sum(1 for s in sets.values() if v in s)
    triple = sorted(v for v, c in freq.items() if c == 3)
    double = sorted(v for v, c in freq.items() if c == 2)
    single_by_fw: dict[str, list[str]] = {}
    for name, s in sets.items():
        # 이 프레임워크에만 등장
        only_here = sorted(v for v in s if freq[v] == 1)
        single_by_fw[name] = only_here
    return IntersectionResult(triple=triple, double=double,
                              single_by_fw=single_by_fw, frequency=freq)


def _is_section_A(value: str) -> bool:
    return CATALOG["values"].get(value, {}).get("section") == "A"


def _tiebreak_key(value: str, mode_e: bool) -> tuple:
    """동률 처리: (a) 모드E면 A 분류 우선 → (b) 박사님 빈도 우선 → (c) 알파벳."""
    sec_a_priority = 0 if mode_e and _is_section_A(value) else 1
    try:
        doc_priority = DOC_FREQ_PRIORITY.index(value)
    except ValueError:
        doc_priority = len(DOC_FREQ_PRIORITY)
    return (sec_a_priority, doc_priority, value)


def derive_core_three(mbti_vals: list[str] | None,
                      enn_vals: list[str] | None,
                      mi_vals: list[str] | None,
                      mode_e: bool = False,
                      wing_extras: list[str] | None = None) -> dict:
    """SKILL.md '#### 핵심 가치 3선 도출 — 폴백 규칙' Step 1~5 결정론 구현.

    Step 1 — 3개 교집합 우선 (최대 3개)
    Step 2 — 부족 시 2개 교집합 보충 (동률 시 모드E면 A 분류 우선)
    Step 3 — 각 프레임워크 최소 1개 반영 보증
    Step 4 — 일부 입력 모드(B)에서는 가능한 범위로 도출 + 안내
    Step 5 — 동률 처리: (a) A 분류 → (b) 박사님 빈도 → (c) 알파벳
    """
    inter = analyze_intersection(mbti_vals, enn_vals, mi_vals)
    fw_sets: dict[str, set[str]] = {}
    if mbti_vals is not None: fw_sets["mbti"] = set(mbti_vals)
    if enn_vals is not None: fw_sets["enneagram"] = set(enn_vals)
    if mi_vals is not None: fw_sets["mi"] = set(mi_vals)

    missing_frameworks = [n for n in ("mbti", "enneagram", "mi") if n not in fw_sets]

    chosen: list[str] = []
    rationale: list[str] = []

    # Step 1
    triple_sorted = sorted(inter.triple, key=lambda v: _tiebreak_key(v, mode_e))
    for v in triple_sorted:
        if len(chosen) >= 3: break
        chosen.append(v)
        rationale.append(f"Step1: {v} — 3개 교집합")

    # Step 2 — 부족 시 2개 교집합 보충
    if len(chosen) < 3:
        double_sorted = sorted(inter.double, key=lambda v: _tiebreak_key(v, mode_e))
        for v in double_sorted:
            if len(chosen) >= 3: break
            if v not in chosen:
                chosen.append(v)
                rationale.append(f"Step2: {v} — 2개 교집합")

    # Step 3 — 각 프레임워크 최소 1개 반영 보증
    if len(fw_sets) >= 2:  # 최소 2개 프레임워크 있을 때만 보증 적용
        for fw_name, fw_set in fw_sets.items():
            if not any(c in fw_set for c in chosen):
                # 이 프레임워크의 가치 중 카탈로그 우선순위 따라 1개 강제
                candidates = sorted(fw_set, key=lambda v: _tiebreak_key(v, mode_e))
                for cand in candidates:
                    if cand not in chosen:
                        if len(chosen) < 3:
                            chosen.append(cand)
                            rationale.append(
                                f"Step3: {cand} — {fw_name} 프레임워크 대변 보증")
                        else:
                            # 3개 꽉 찬 상태에서 특정 프레임워크 비대변 발생 시
                            # 가장 약한 슬롯(2개 교집합 또는 마지막)을 대체
                            replace_idx = None
                            for i in range(len(chosen) - 1, -1, -1):
                                if inter.frequency.get(chosen[i], 1) < 3:
                                    replace_idx = i; break
                            if replace_idx is not None:
                                old = chosen[replace_idx]
                                chosen[replace_idx] = cand
                                rationale.append(
                                    f"Step3-replace: {old} → {cand} ({fw_name} 보증)")
                        break

    # Step 4 — 윙 보조 (3개 미만이면 윙 가치로 보충)
    if wing_extras and len(chosen) < 3:
        for v in sorted(wing_extras, key=lambda v: _tiebreak_key(v, mode_e)):
            if len(chosen) >= 3: break
            if v not in chosen:
                chosen.append(v)
                rationale.append(f"Step4: {v} — 윙 가치 보조(가중치 0.5)")

    # Step 4b — 모드 B(일부 입력) 폴백: 단일/이중 프레임워크 입력 시
    # 입력된 프레임워크 1순위(=리스트 앞쪽) 가치 중 카탈로그 우선순위로 보충.
    if len(chosen) < 3 and fw_sets:
        # 입력된 프레임워크 가치의 합집합 — 단, 입력 순서를 보존
        union_ordered: list[str] = []
        for fw_name, raw_list in (("mbti", mbti_vals), ("enneagram", enn_vals), ("mi", mi_vals)):
            if not raw_list: continue
            for v in raw_list:
                if v not in union_ordered:
                    union_ordered.append(v)
        # 1순위(목록 앞)를 약하게 우선하되 모드E·A섹션·박사님 빈도도 반영
        def _b_key(v: str):
            base = _tiebreak_key(v, mode_e)
            return (union_ordered.index(v),) + base
        for v in sorted(union_ordered, key=_b_key):
            if len(chosen) >= 3: break
            if v not in chosen:
                chosen.append(v)
                rationale.append(f"Step4b: {v} — 일부 입력 폴백(입력 순서·우선순위)")

    # 3개 여전히 안 채워지면 그대로 반환 (입력 자체가 3개 미만일 때)
    return {
        "core_three": chosen,
        "rationale": rationale,
        "intersection": {
            "triple": inter.triple,
            "double": inter.double,
            "single_by_fw": inter.single_by_fw,
            "frequency": inter.frequency,
        },
        "missing_frameworks": missing_frameworks,
        "mode_e_active": mode_e,
        "advisory": ("일부 프레임워크 누락 — 추가 입력 시 더 정밀한 가치 좌표 가능"
                     if missing_frameworks else None),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 7. 통합 프로파일 생성 (모드 A/B/D 진입점)
# ──────────────────────────────────────────────────────────────────────────────


def build_profile(mbti: str | None = None,
                  enneagram: int | None = None,
                  wing: int | None = None,
                  mi: list[str] | None = None,
                  mode_e: bool = False) -> dict:
    """완전한 가치 프로파일 산출. SKILL.md 처리 흐름 3-4-5단계 결정론 환원."""
    mbti_vals = mbti_values(mbti) if mbti else None
    enn_vals = enneagram_values(enneagram) if enneagram else None
    mi_vals = mi_values(mi) if mi else None

    # 윙 처리
    wing_extras: list[str] = []
    wing_info = None
    if enneagram and wing is not None:
        weighted = enneagram_with_wing(enneagram, wing)
        base_set = set(enneagram_values(enneagram))
        wing_extras = [w.value for w in weighted
                       if w.value not in base_set and w.weight == 0.5]
        wing_info = {
            "base_type": int(enneagram),
            "wing": int(wing),
            "allowed_wings": enneagram_allowed_wings(enneagram),
            "wing_only_values": wing_extras,
            "wing_weight": 0.5,
        }

    result = derive_core_three(mbti_vals, enn_vals, mi_vals,
                               mode_e=mode_e, wing_extras=wing_extras)
    return {
        "input": {
            "mbti": mbti, "enneagram": enneagram, "wing": wing,
            "mi": mi, "mode_e": mode_e,
        },
        "framework_values": {
            "mbti": {"type": mbti, "values": mbti_vals} if mbti_vals else None,
            "enneagram": ({"type": enneagram, "world": enneagram_world(enneagram),
                           "label": enneagram_label(enneagram), "values": enn_vals,
                           "wing": wing_info}
                          if enn_vals else None),
            "mi": {"intelligences": [resolve_mi_name(x) for x in mi] if mi else None,
                   "values_union": mi_vals} if mi_vals else None,
        },
        "intersection": result["intersection"],
        "core_three": result["core_three"],
        "rationale": result["rationale"],
        "missing_frameworks": result["missing_frameworks"],
        "mode_e_active": result["mode_e_active"],
        "advisory": result["advisory"],
        "determinism_note":
            "본 결과는 values_engine.py 결정론 산출이다. LLM은 이 출력을 그대로 인용하며, "
            "매핑·교집합·3선을 자연어로 재추론하지 않는다.",
        "sources_for_external_claims": {
            "enneagram_names": SOURCES["enneagram"]["riso_hudson_nine_types"]["source"],
            "multiple_intelligences": SOURCES["multiple_intelligences"]["gardner_8_plus_1"]["source"],
            "mbti": SOURCES["mbti"]["myers_briggs"]["source"],
            "biblical_values": SOURCES["biblical"]["2_peter_1_5_7"]["source"],
        },
    }


# ──────────────────────────────────────────────────────────────────────────────
# 8. CLI
# ──────────────────────────────────────────────────────────────────────────────


def _csv(s: str) -> list[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def _ints(s: str) -> list[int]:
    return [int(x) for x in _csv(s)]


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="vision-values-visioncoding 결정론 엔진")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="데이터 무결성 검사")
    sub.add_parser("catalog",  help="카탈로그 단어 전체 출력")

    p_mbti = sub.add_parser("mbti", help="MBTI 유형 가치 조회")
    p_mbti.add_argument("type")

    p_enn = sub.add_parser("enneagram", help="에니어그램 유형 가치 조회 (+윙 옵션)")
    p_enn.add_argument("type", type=int)
    p_enn.add_argument("--wing", type=int, default=None)

    p_mi = sub.add_parser("mi", help="다중지능 가치 합집합")
    p_mi.add_argument("intelligences", help="콤마 구분 (예: Linguistic,Intrapersonal)")

    p_prof = sub.add_parser("profile", help="통합 프로파일 산출")
    p_prof.add_argument("--mbti")
    p_prof.add_argument("--enneagram", type=int)
    p_prof.add_argument("--wing", type=int)
    p_prof.add_argument("--mi")
    p_prof.add_argument("--mode-e", action="store_true")

    p_screen = sub.add_parser("screen", help="모드 C 간이 진단 채점")
    p_screen.add_argument("--enneagram-rank", help="콤마 구분 1차,2차 (예: 1,4)")
    p_screen.add_argument("--mi-scores", help="콤마 구분 8개 점수 1~5")

    args = p.parse_args(argv)

    if args.cmd == "validate":
        out = validate_data()
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["ok"] else 1

    if args.cmd == "catalog":
        out = {"count": len(VALID_VALUES),
               "by_section": {sec: sorted([v for v, info in CATALOG["values"].items()
                                            if info["section"] == sec])
                              for sec in ("A","B","C","D","E","F")}}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "mbti":
        out = {"type": args.type.upper(), "values": mbti_values(args.type)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "enneagram":
        out = {
            "type": args.type,
            "label": enneagram_label(args.type),
            "world": enneagram_world(args.type),
            "values": enneagram_values(args.type),
            "allowed_wings": enneagram_allowed_wings(args.type),
        }
        if args.wing is not None:
            wv = enneagram_with_wing(args.type, args.wing)
            out["wing"] = args.wing
            out["weighted_values"] = [asdict(w) for w in wv]
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "mi":
        names = _csv(args.intelligences)
        out = {"input": names,
               "resolved": [resolve_mi_name(n) for n in names],
               "values_union": mi_values(names)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "profile":
        out = build_profile(
            mbti=args.mbti, enneagram=args.enneagram, wing=args.wing,
            mi=_csv(args.mi) if args.mi else None, mode_e=args.mode_e)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "screen":
        result: dict = {}
        if args.enneagram_rank:
            picks = _ints(args.enneagram_rank)
            result["enneagram"] = score_enneagram_screening(picks)
        if args.mi_scores:
            scores = _ints(args.mi_scores)
            result["mi"] = score_mi_screening(scores)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
