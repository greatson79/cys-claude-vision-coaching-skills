#!/usr/bin/env python3
"""검증용 10개 임의 프롬프트 — 이전 검증과 절대 중복되지 않음.

이전 라운드(추정)에서 사용되었을 가능성이 가장 높은 주제는 카탈로그
대표 키워드(AGI·CBDC·통일·인구절벽·기후위기·메타시티)이므로, 본 라운드에서는
의도적으로 *덜 직관적이고 카탈로그 변두리에 있는* 주제와 *복합 키워드 주제*,
*카탈로그 외 신주제*를 섞어 분류기·검증기의 견고성을 시험한다.
"""

import json
import subprocess
import sys
import os

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(THIS_DIR, "topic_classifier.py")
RUN_PIPELINE = os.path.join(THIS_DIR, "run_pipeline.py")

PROMPTS = [
    # 1) 정신건강 + 1인 가구 복합 (다중 매칭 시험)
    "한국 청년 1인 가구의 정신건강 위기 10년 전망",
    # 2) 한류 + K-콘텐츠 (낙관 프레이밍 고위험)
    "K-pop 한류 산업이 가져올 20년 후 한국 문화 경제 변화",
    # 3) 우주산업 (낙관 프레이밍 고위험)
    "스타링크 위성 인터넷 보편화 30년 한국 통신 시장",
    # 4) AI 범죄·딥페이크 (비관 감정론 고위험)
    "딥페이크 AI 범죄 확산 5년 한국 사법 시스템 대응",
    # 5) 다문화·이민 (낙관 프레이밍 고위험)
    "다문화 이민 인구 200만명 시대 한국 사회 갈등",
    # 6) 원격근무 (자유 낙관 고위험)
    "원격근무 디지털 노마드 정착 15년 한국 도시 구조 변화",
    # 7) 디지털 격차 (소외 비관 고위험)
    "디지털 리터러시 격차 심화 10년 한국 고령층 소외",
    # 8) ESG (긍정 프레이밍 고위험)
    "ESG 의무 공시 확대 7년 한국 중소기업 부담",
    # 9) 반도체·기술 패권 (단일 매칭)
    "TSMC ASML EUV 공급망 디커플링 20년 한국 반도체",
    # 10) 카탈로그 외 신주제 (unmatched_warning 트리거)
    "양자컴퓨터 상용화 30년 한국 사이버 보안",
]


def run_classifier(topic: str) -> dict:
    proc = subprocess.run([sys.executable, CLASSIFIER, topic], capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def main() -> int:
    fail_count = 0
    for i, topic in enumerate(PROMPTS, 1):
        result = run_classifier(topic)
        matched = result["matched_categories"]
        groups = result["required_groups_axis1"]
        domains = result["required_domains_axis3"]
        warnings = result["framing_warnings"]
        time_b_req = result["time_mode_b_required"]
        time_b_rec = result["time_mode_b_recommended"]
        years = result["detected_time_years"]
        unmatched = result.get("unmatched_warning")

        status = "PASS"
        reasons = []

        # 검증 규칙: 카탈로그 매칭이 있어야 하거나 unmatched_warning이 명시되어야 한다
        if not matched and not unmatched:
            status = "FAIL"
            reasons.append("매칭도 unmatched_warning도 없음")

        # 시간 범위 ≥ 30년이면 mode_b_required true 이어야 함
        if years is not None and years >= 30 and not time_b_req:
            status = "FAIL"
            reasons.append(f"years={years} 이지만 mode_b_required={time_b_req}")
        if years is not None and 20 <= years < 30 and not time_b_rec:
            status = "FAIL"
            reasons.append(f"years={years} 이지만 mode_b_recommended={time_b_rec}")

        if status == "FAIL":
            fail_count += 1

        print(f"\n=== [{i:02d}] {status} — {topic}")
        print(f"   matched: {matched}")
        print(f"   groups({len(groups)}): {groups}")
        print(f"   domains({len(domains)}): {domains}")
        print(f"   framing_warnings({len(warnings)}): {warnings}")
        print(f"   years={years} mode_b_req={time_b_req} mode_b_rec={time_b_rec}")
        if unmatched:
            print(f"   unmatched: {unmatched}")
        if reasons:
            print(f"   FAIL_REASONS: {reasons}")

    print(f"\n{'='*60}")
    print(f"TOTAL: {len(PROMPTS) - fail_count}/{len(PROMPTS)} PASS")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
