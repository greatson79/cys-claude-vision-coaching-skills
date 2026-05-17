#!/usr/bin/env python3
"""fact_check.py — 산출물 내용 정확성·할루시네이션 차단 검증.

결정론 환원 모듈 4: 산출물의 *내용 수준* 정확성을 결정론적으로 점검한다.

검증 항목:
1. **출처 화이트리스트 매칭** — 모든 [출처: ...] 인용이 source_whitelist.py에 등재된 신뢰 가능 기관과 매칭
2. **수치 인용 부착률** — % 또는 통계 수치 80% 이상이 [출처:] 또는 [추정:]로 라벨링
3. **추정 비율 상한** — 전체 인용 중 [추정] 비율이 80%를 넘지 않음 (학계 지지 부족 신호)
4. **단정·과장 어휘 차단** — "확실히·반드시·100%·절대" 등 단정 어휘 검출
5. **가공 기관명 검출** — "가상연구소·한국미래연구소" 등 의심 패턴

사용:
    python3 fact_check.py --file output.md
    또는
    cat output.md | python3 fact_check.py
"""

import argparse
import json
import os
import re
import sys
from typing import Any

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
from source_whitelist import audit as audit_sources  # noqa: E402

CITATION_OUT = re.compile(r"\[출처:\s*[^\]]+\]")
CITATION_ESTIMATE = re.compile(r"\[추정[:\]]")
PERCENT_NUMBER = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%")
LARGE_NUMBER = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+조|\d+억|\d+만\s*명)")

"""단정·과장 어휘 — word boundary + 명확한 단정 표현만 검출.

주의: 한국어 다의어("절대 감소·절대 다수" 등 *완전한*의 의미)와
substring 오탐("70%"가 "0%"에 매칭) 방지를 위해 정규식 기반 검출 사용.
"""
OVERCLAIM_PATTERNS = [
    re.compile(r"확실히\s*[가-힣]"),  # "확실히 망한다"
    re.compile(r"반드시\s*망|반드시\s*실패|반드시\s*성공"),
    re.compile(r"절대\s*불가능|절대로\s*[가-힣]|절대\s*안\s*[가-힣]"),
    re.compile(r"(?<!\d)100\s*%\s*성공|(?<!\d)100\s*%\s*실패"),
    re.compile(r"분명히\s*망|분명히\s*실패"),
    re.compile(r"완벽히\s*[가-힣]"),
    re.compile(r"전혀\s*없을\s*것"),
    re.compile(r"결코\s*일어나지"),
    re.compile(r"무조건\s*[가-힣]"),
]


def check_source_whitelist(text: str) -> dict[str, Any]:
    audit_result = audit_sources(text)
    return {
        "name": "출처 화이트리스트 매칭",
        "total": audit_result["total_citations"],
        "passed": audit_result["passed"],
        "failed": audit_result["failed"],
        "blockers": [r for r in audit_result["results"] if not r["pass"]],
        "pass": audit_result["failed"] == 0,
    }


def check_number_citation_rate(text: str) -> dict[str, Any]:
    """수치(%·억·만명)가 [출처:]/[추정:] 라벨로 80% 이상 부착되었는지.

    예외: 주제 자체에 포함된 % 표기(제목·변화 정의·핵심 가정의 키 비율)는
    *주제 진술 표기*로 간주하여 라벨 의무에서 제외 (예: "출산율 0.5"·"65세+ 30%").
    검출 범위: 표 셀(파이프 |로 둘러싸인 영역) 안의 수치만 라벨 의무 적용.
    """
    # 표 라인만 추출(| 로 시작하는 라인)
    table_lines = [ln for ln in text.splitlines() if ln.lstrip().startswith("|")]
    table_text = "\n".join(table_lines)
    nums = list(PERCENT_NUMBER.finditer(table_text)) + list(LARGE_NUMBER.finditer(table_text))
    if not nums:
        return {"name": "수치 라벨링 80%+ (표 안)", "total": 0, "labeled": 0, "rate": 1.0, "pass": True}
    labeled = 0
    for m in nums:
        snippet = table_text[m.end() : m.end() + 80]
        if CITATION_OUT.search(snippet) or CITATION_ESTIMATE.search(snippet):
            labeled += 1
    rate = labeled / len(nums)
    return {
        "name": "수치 라벨링 80%+ (표 안)",
        "total": len(nums),
        "labeled": labeled,
        "rate": round(rate, 3),
        "pass": rate >= 0.8,
    }


def check_estimate_ratio(text: str) -> dict[str, Any]:
    """전체 인용 중 [추정] 비율이 80% 이하인지 (학계 지지 부족 차단)."""
    out_count = len(CITATION_OUT.findall(text))
    est_count = len(CITATION_ESTIMATE.findall(text))
    total = out_count + est_count
    if total == 0:
        return {
            "name": "[추정] 비율 ≤ 80%",
            "출처": 0,
            "추정": 0,
            "추정비율": 0.0,
            "pass": True,
            "note": "인용 없음",
        }
    ratio = est_count / total
    return {
        "name": "[추정] 비율 ≤ 80%",
        "출처": out_count,
        "추정": est_count,
        "추정비율": round(ratio, 3),
        "pass": ratio <= 0.8,
    }


def check_overclaim(text: str) -> dict[str, Any]:
    found = []
    for pat in OVERCLAIM_PATTERNS:
        for m in pat.finditer(text):
            found.append(m.group(0))
    return {
        "name": "단정·과장 어휘 0건",
        "검출": found,
        "pass": not found,
    }


def check_fabricated_institutions(text: str) -> dict[str, Any]:
    from source_whitelist import SUSPICIOUS_PATTERN

    found = SUSPICIOUS_PATTERN.findall(text)
    return {
        "name": "가공 기관명 패턴 0건",
        "검출": found,
        "pass": not found,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    args = ap.parse_args()
    text = sys.stdin.read() if not args.file else open(args.file, encoding="utf-8").read()

    checks = [
        check_source_whitelist(text),
        check_number_citation_rate(text),
        check_estimate_ratio(text),
        check_overclaim(text),
        check_fabricated_institutions(text),
    ]
    blockers = [c for c in checks if not c["pass"]]
    result = {
        "pass": not blockers,
        "total": len(checks),
        "passed": sum(1 for c in checks if c["pass"]),
        "failed": len(blockers),
        "checks": checks,
        "blockers": blockers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
