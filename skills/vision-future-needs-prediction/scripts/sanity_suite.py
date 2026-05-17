#!/usr/bin/env python3
"""sanity_suite.py — 분류기·검증기 통합 sanity 시험.

(1) 10개 임의 분류 시험 → 모두 PASS
(2) perfect output → validator 14/14 PASS
(3) 빈 input → validator FAIL
(4) 30년 주제에 방식 B 누락 산출물 → validator FAIL (방식 B + 주제 특화 집단)

모든 시험이 의도된 결과를 내면 exit 0.
"""

import json
import os
import subprocess
import sys
import tempfile

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER = os.path.join(THIS_DIR, "topic_classifier.py")
VALIDATOR = os.path.join(THIS_DIR, "output_validator.py")
PIPELINE = os.path.join(THIS_DIR, "run_pipeline.py")
TEST_10 = os.path.join(THIS_DIR, "test_10prompts.py")


PERFECT_OUTPUT_PATH = os.path.join(tempfile.gettempdir(), "vfnp_sanity_perfect.md")
EMPTY_OUTPUT_PATH = os.path.join(tempfile.gettempdir(), "vfnp_sanity_empty.md")


PERFECT_OUTPUT = r"""# 한국 청년 1인 가구 정신건강 위기 10년 전망

## 변화 정의
2025~2035년 사이 한국에서 청년 1인 가구 비중이 30% 이상으로 확산되고 정신건강 위기 증가가 동시 진행되며, 청년·고령 1인 가구·돌봄 공백 인구에 광범위 영향을 미친다.

## STEEPS 6차원 사전 점검
- Society: 가족 구조 해체·고독 증가
- Technology: 정신건강 앱 보급
- Economy: 1인 소비 시장 확대
- Environment: 도시 밀집 영향
- Politics: 복지 정책 부담 증가
- Spirituality: 의미 추구 욕구 강화

## 축 1 — Opportunities vs Challenges
| 집단 | 기회 | 도전 |
|---|---|---|
| 청년 | 자유로운 라이프 [출처: 통계청, 2024] | 고독·우울 30% 증가 [출처: 보건복지부, 2024] |
| 중장년 | 1인 라이프 컨설팅 시장 [추정: 시장 성장] | 자녀 부재 노후 불안 [출처: KDI, 2024] |
| 노년 | 시니어 코하우징 수요 [추정: 수요 증가] | 사회적 고립 위험 50% [출처: 통계청, 2024] |
| 대기업 | 1인 가구 타겟 제품 [추정: 매출 기여] | 가족 시장 축소 [출처: 산업연구원, 2024] |
| 중소기업 | 틈새 서비스 [추정: 기회] | 인력 수급 [출처: 중기부, 2024] |
| 자영업 | 1인 외식 시장 [출처: 농림부, 2024] | 가족 단위 매출 감소 [추정] |
| 수도권 | 소형 주거 수요 [출처: 국토부, 2024] | 도시 외로움 [출처: 서울시, 2024] |
| 지방 | 청년 정착 인센티브 [출처: 행안부, 2024] | 청년 유출 가속 [출처: 통계청, 2024] |
| 청년 1인 가구(자발) | 자율적 삶 설계 [추정] | 정서적 지지 부족 [출처: 보건복지부, 2024] |
| 고령 1인 가구(상실·고독) | 돌봄 서비스 접근 [출처: 복지부, 2024] | 만성 고독사 위험 [출처: 통계청, 2024] |
| 이혼자 | 새 출발 자유도 [추정] | 사회적 낙인 [출처: 여성가족부, 2024] |
| 돌봄 공백 노출자 | 공공 돌봄 확대 [출처: 복지부, 2024] | 위기 대응 지연 [추정] |
| 청년(정신건강) | 디지털 정신건강 서비스 [출처: 복지부, 2024] | 진단 미수용 [출처: 정신건강의학회, 2024] |
| 워킹맘 | 재택·플렉시블 워크 확대 [출처: 고용노동부, 2024] | 일·돌봄·자기관리 다중 부담 [출처: 여가부, 2024] |
| 정신과 인프라 | 수요 폭증 사업 기회 [추정] | 의사 부족 50% [출처: 의협, 2024] |

## 축 2 — Needs Filled vs Deprivations Created
| 차원 | 필요 충족 (✓) | 결핍 창출 (⚠) |
|---|---|---|
| Society | 자율성 욕구 충족 | 소속감 결핍 심화 |
| Technology | 정신건강 앱 접근성 | 디지털 대체 의존 |
| Economy | 1인 시장 성장 | 가족경제 위축 |
| Environment | 소형 주거 친환경화 | 도시 밀집 스트레스 |
| Politics | 1인 정책 강화 | 가족 정책 약화 |
| Spirituality | 의미 추구 자율 | 공동체 영성 약화 |

## 축 3 — Problems Solved vs New Problems
| 영역 | 해결 (✓) | 신규 문제 (⚠) |
|---|---|---|
| 노동 | 유연 근무 확대 | 1인 워라밸 압박 |
| 교육 | 평생교육 수요 | 가족 교육 약화 |
| 의료 | 디지털 진료 보편화 | 진단 사각지대 |
| 주거 | 소형 주거 공급 | 임대료 양극화 |
| 환경 | 1인 친환경 소비 | 1회용품 증가 |
| 가족 | 결혼 압박 완화 | 출산율 추가 하락 |
| 사회복지정책·노후보장·공동주거 | 1인 노후 보장 강화 | 재정 부담 가중 |
| 정신건강 서비스 체계 | AI 상담 보편화 | 인간 상담 부족 |

## 핵심 통찰 5선
1. 청년 1인 가구 정신건강 위기는 *수도권 집중* 현상으로 평균 통계가 지방의 안정을 가린다.
2. 정신건강 앱은 *접근성을 늘리지만 진단 후 치료 갭*을 키운다.
3. 1인 가구 정책 강화가 *역설적으로 가족 정책 예산을 잠식*해 출산율 추가 하락을 부른다.
4. 정신과 의사 50% 부족으로 *디지털 서비스 의존*이 강제될 것이다.
5. 비대칭: 자발적 청년 1인 가구는 자유 향유, 강제적 고령 1인 가구는 고립사 위험에 노출된다. 정신건강 위기 비관론 회피, 기술 해법·제도 개선 기회 균형 필수.

## 의사결정자 액션
### 개인 액션
- 모니터링 지표: 통계청 1인 가구 비중, 자살률
- 선제 행동: 디지털 정신건강 앱 정기 사용
- 헷지: 오프라인 공동체 1개 유지

### 기업 액션
- 신규 시장 기회: 1인 가구 타겟 정신건강 구독 서비스
- 위험 관리: 가족 단위 제품 의존도 점검
- 인재 확보: 디지털 정신건강 전문가

### 정책 액션
- 정부 우선순위: 1인 가구 정신건강 안전망
- 입법·예산 권고: 정신과 의사 정원 확대 + 공공 상담 인프라
- 사회 안전망: 고령 1인 가구 위기 대응 24시간 시스템

## 한계·불확실성
1. 핵심 가정: 청년 1인 가구 비중이 2035년 30% 이상으로 증가하는 전제. 빗나가면 분석 전반 흔들림.
2. 점검 신호: 통계청 인구주택총조사 5년 주기, 보건복지부 정신건강 실태조사 3년 주기, 자살률 분기 통계.
3. 재검토 권장: 2~3년 후 또는 정신건강 대형 사건 발생 시 즉시 재검토.
4. 면책: 본 분석은 시뮬레이션이며 실제 의사결정은 본인 판단과 전문가 자문을 결합한다.
"""


def write_file(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_test_10() -> bool:
    proc = subprocess.run([sys.executable, TEST_10], capture_output=True, text=True)
    return proc.returncode == 0


def run_validator_perfect() -> tuple[bool, dict]:
    write_file(PERFECT_OUTPUT_PATH, PERFECT_OUTPUT)
    proc = subprocess.run(
        [
            sys.executable,
            PIPELINE,
            "verify",
            "--topic",
            "한국 청년 1인 가구 정신건강 위기 10년 전망",
            "--years",
            "10",
            "--file",
            PERFECT_OUTPUT_PATH,
        ],
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    return data["validation"]["pass"] and data["validation"]["passed"] == 14, data


def run_validator_empty() -> tuple[bool, dict]:
    write_file(EMPTY_OUTPUT_PATH, "그냥 한 줄 텍스트")
    proc = subprocess.run(
        [sys.executable, VALIDATOR, "--file", EMPTY_OUTPUT_PATH, "--time-years", "10"],
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    return (not data["pass"]) and data["failed"] >= 5, data


def run_fact_check_perfect() -> tuple[bool, dict]:
    """perfect output에 대해 fact_check 5/5 PASS."""
    proc = subprocess.run(
        [sys.executable, os.path.join(THIS_DIR, "fact_check.py"), "--file", PERFECT_OUTPUT_PATH],
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    return data["pass"], data


def run_fact_check_fabricated() -> tuple[bool, dict]:
    """가공 기관명 산출물에 대해 fact_check FAIL."""
    bad_path = os.path.join(tempfile.gettempdir(), "vfnp_sanity_fabricated.md")
    write_file(
        bad_path,
        "변화 [출처: 한국가상미래연구소, 2024]. 통계 [출처: 미래학회, 2024]. 100% 성공할 것이다.",
    )
    proc = subprocess.run(
        [sys.executable, os.path.join(THIS_DIR, "fact_check.py"), "--file", bad_path],
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    return (not data["pass"]) and data["failed"] >= 2, data


def run_validator_30y_no_modeb() -> tuple[bool, dict]:
    """30년 주제인데 산출물에 방식 B 없음 → time_mode_b FAIL."""
    proc = subprocess.run(
        [
            sys.executable,
            PIPELINE,
            "verify",
            "--topic",
            "스타링크 위성 인터넷 보편화 30년 한국 통신 시장",
            "--years",
            "30",
            "--file",
            PERFECT_OUTPUT_PATH,
        ],
        capture_output=True,
        text=True,
    )
    data = json.loads(proc.stdout)
    blockers_ids = {b["id"] for b in data["validation"]["blockers"]}
    expected_blockers = {"time_mode_b", "axis1_table", "axis3_table"}
    return expected_blockers.issubset(blockers_ids), data


def main() -> int:
    results: list[tuple[str, bool]] = []

    print("[1/6] 10개 임의 분류 시험 ...", end=" ")
    ok = run_test_10()
    results.append(("10개 임의 분류", ok))
    print("PASS" if ok else "FAIL")

    print("[2/6] perfect output 14/14 검증 ...", end=" ")
    ok, data = run_validator_perfect()
    results.append(("perfect output 14/14", ok))
    print("PASS" if ok else f"FAIL — {data['validation']['blockers']}")

    print("[3/6] 빈 input → FAIL ≥5 ...", end=" ")
    ok, data = run_validator_empty()
    results.append(("empty FAIL", ok))
    print("PASS" if ok else f"FAIL — pass={data['pass']} failed={data['failed']}")

    print("[4/6] 30년 주제 방식 B 누락 → 3개 FAIL ...", end=" ")
    ok, data = run_validator_30y_no_modeb()
    results.append(("30y mode-B FAIL", ok))
    print(
        "PASS"
        if ok
        else f"FAIL — blockers={[b['id'] for b in data['validation']['blockers']]}"
    )

    print("[5/6] perfect output fact-check 5/5 ...", end=" ")
    ok, data = run_fact_check_perfect()
    results.append(("perfect fact-check 5/5", ok))
    print("PASS" if ok else f"FAIL — {data.get('blockers')}")

    print("[6/6] 가공 기관명 산출물 → fact-check FAIL ...", end=" ")
    ok, data = run_fact_check_fabricated()
    results.append(("fabricated FAIL", ok))
    print("PASS" if ok else f"FAIL — passed={data['passed']}/{data['total']}")

    print("\n" + "=" * 60)
    all_pass = all(ok for _, ok in results)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(
        f"\nSANITY SUITE: {sum(1 for _, ok in results if ok)}/{len(results)} "
        f"— {'ALL GREEN' if all_pass else 'INVESTIGATE'}"
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
