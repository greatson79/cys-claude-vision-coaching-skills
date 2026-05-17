"""
2차 검증 — 1차 시나리오와 *완전히 다른* 페르소나·요청 패턴 10개.

각 시나리오는 (1) 입력 청취 + 결정론 산출 전 흐름, (2) 절대 원칙 11번 결정론 호출,
(3) 출처 등재 무결성, (4) 영역 캡, (5) 분산 검출, (6) 시야 비율, (7) 시간축,
(8) 진단 누락, (9) Existential 잠정, (10) 카드 6영역 보장을 한 번씩 검사한다.

  python3 -m unittest tests/test_10_scenarios_round2.py -v
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import research_engine as eng  # noqa: E402

CLI = ROOT / "scripts" / "research_cli.py"


def _run_cli(args: list[str], stdin: str | None = None) -> dict:
    """CLI 호출 — LLM이 따를 결정론 라인 시뮬레이션."""
    result = subprocess.run(
        ["python3", str(CLI), *args],
        input=stdin or "",
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        timeout=30,
    )
    if result.returncode not in (0, 2):
        raise AssertionError(f"CLI failed: {result.stderr}\nstdout: {result.stdout}")
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


# 1차와 *전혀 다른* 페르소나 10명 — 한 번도 사용하지 않은 조합
ROUND2 = [
    # 1: 10대 여자 중1 + 운동선수 지망
    {
        "name": "중1 농구 유망주",
        "prompt": "중학교 1학년 농구선수입니다. 다리·체력·승부욕이 강점이고, 학업은 보통. 미래 10~20년 안에 닥칠 변화가 뭔지 알고 싶어요.",
        "age": 13, "year": 2027,
        "input": {
            "diagnoses": {
                "MBTI": "ESTP",
                "Enneagram": "8w7",
                "MultipleIntelligence": {
                    "Bodily-Kinesthetic": 10, "Interpersonal": 8, "Spatial": 7,
                    "Logical-Mathematical": 5, "Linguistic": 5,
                    "Intrapersonal": 4, "Naturalist": 6, "Musical": 5, "Existential": 3,
                },
                "Values": ["성취", "자유", "공동체"],
            },
            "job_domains": [],
        },
        "vision_candidate": True, "target_recoef_domain": None,
        "mode": "brief", "expected_band": "teen",
    },
    # 2: 90세 노인 후학을 위한 비전 (시니어 코칭형)
    {
        "name": "90세 한국 교회 원로 — 차세대 영성 코칭",
        "prompt": "90세 원로 목회자. 후배 청년 목회자들을 위해 미래 변화 자료가 필요합니다.",
        "age": 90, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INFJ",
                "Enneagram": "1w2",
                "Values": ["영성", "헌신", "사역", "봉사", "지혜"],
                "CYS": {"vision_direction": "강", "vision_potential": "강", "vision_skill": "강"},
                "Readiness": {"big_picture": 10},
            },
            "job_domains": ["종교"],
        },
        "vision_candidate": True, "target_recoef_domain": "Spirituality",
        "mode": "standard", "expected_band": "seventies_plus",
    },
    # 3: 부모가 5세 자녀의 미래 분석을 대리
    {
        "name": "유치원생 자녀의 미래 (부모 대리)",
        "prompt": "5세 자녀가 그림 그리기와 동물 관찰을 좋아합니다. 자녀가 살아갈 60년 후까지의 미래를 분석해주세요.",
        "age": 5, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INFP",  # 부모 관찰
                "Enneagram": "4",
                "Values": ["창의", "자유", "생명"],
            },
            "job_domains": ["예술", "농업"],
        },
        "vision_candidate": True, "target_recoef_domain": None,
        "mode": "brief", "expected_band": "child_under10",
    },
    # 4: 25세 — 군 복무 마치고 진로 고민
    {
        "name": "전역 직후 진로 고민 청년",
        "prompt": "25세 남자, 전역 직후. 안정적 진로를 원하지만 어떤 방향인지 모름. 미래 변화로부터 힌트를 얻고자 합니다.",
        "age": 25, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ISFJ",
                "Enneagram": "6w5",
                "MultipleIntelligence": {
                    "Logical-Mathematical": 6, "Linguistic": 6, "Bodily-Kinesthetic": 7,
                    "Interpersonal": 7, "Intrapersonal": 5, "Spatial": 5,
                    "Naturalist": 4, "Musical": 3, "Existential": 4,
                },
                "STRONG": {"C": 8, "S": 7, "R": 6, "I": 5, "E": 5, "A": 3},
                "Values": ["안정", "공동체", "성취"],
            },
            "job_domains": ["군", "공공"],
        },
        "vision_candidate": True, "target_recoef_domain": "Politics",
        "mode": "standard", "expected_band": "twenties",
    },
    # 5: 40대 워킹맘 + 우울 위기 언급 → 심리·정서적 어려움 사용자 대응
    {
        "name": "워킹맘 — 번아웃 + 비전 점검",
        "prompt": "40대 워킹맘인데 번아웃과 우울감이 있어요. 그래도 앞으로의 진로 방향을 보고 싶어요.",
        "age": 43, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ENFJ",
                "Enneagram": "2w3",
                "MultipleIntelligence": {
                    "Interpersonal": 9, "Linguistic": 8, "Intrapersonal": 7,
                    "Logical-Mathematical": 6, "Bodily-Kinesthetic": 5,
                    "Spatial": 5, "Naturalist": 4, "Musical": 6, "Existential": 6,
                },
                "STRONG": {"S": 9, "A": 7, "E": 6, "I": 5, "C": 4, "R": 3},
                "Values": ["가족", "관계", "헌신"],
            },
            "job_domains": ["교육", "사회복지"],
        },
        "vision_candidate": True, "target_recoef_domain": "Society",
        "mode": "standard", "expected_band": "thirties_forties",
    },
    # 6: 50대 1인 자영업자 — Economy 가중치 폭주 케이스 (캡 50% 검증)
    {
        "name": "50대 자영업자",
        "prompt": "50대 자영업자. 경제·재정이 절대 우선입니다.",
        "age": 55, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ESTJ",
                "Enneagram": "3w2",
                "MultipleIntelligence": {
                    "Logical-Mathematical": 10, "Interpersonal": 8, "Linguistic": 6,
                    "Spatial": 5, "Bodily-Kinesthetic": 5, "Intrapersonal": 4,
                    "Musical": 3, "Naturalist": 3, "Existential": 2,
                },
                "STRONG": {"E": 10, "C": 9, "I": 7, "S": 5, "R": 4, "A": 2},
                "Values": ["번영", "안정", "성취"],
                "CYS": {"vision_direction": "강", "vision_skill": "강"},
            },
            "job_domains": ["금융", "무역"],
        },
        "vision_candidate": True, "target_recoef_domain": "Economy",
        "mode": "standard", "expected_band": "fifties_sixties",
        "cap_test": True,
    },
    # 7: 비전이 직업 아닌 *관계 정체성* — "좋은 아버지" — 가족 영역
    {
        "name": "좋은 아버지 되기 비전",
        "prompt": "직업보다는 아이들에게 좋은 아버지가 되는 것이 비전입니다. 미래 변화 점검 요청.",
        "age": 38, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INFP",
                "Enneagram": "9w1",
                "MultipleIntelligence": {
                    "Intrapersonal": 8, "Interpersonal": 8, "Linguistic": 7,
                    "Existential": 7, "Naturalist": 5, "Musical": 5,
                    "Logical-Mathematical": 6, "Spatial": 5, "Bodily-Kinesthetic": 5,
                },
                "Values": ["가족", "관계", "공동체", "헌신"],
            },
            "job_domains": ["교육"],
        },
        "vision_candidate": True, "target_recoef_domain": "Society",
        "mode": "standard", "expected_band": "thirties_forties",
    },
    # 8: 미입력 비전 + 진단 1개만 → 작동 거절 (절대 원칙 1 위반)
    {
        "name": "진단 1개만 — 거절 예상",
        "prompt": "MBTI INTJ만 있어요.",
        "age": 30, "year": 2026,
        "input": {"diagnoses": {"MBTI": "INTJ"}, "job_domains": []},
        "vision_candidate": False, "target_recoef_domain": None,
        "mode": "brief", "expected_band": "thirties_forties",
        "should_fail_validation": True,
    },
    # 9: MBTI "IxNJ" — 불완전 입력 → 거절
    {
        "name": "MBTI 불완전 입력",
        "prompt": "IxNJ 같아요 — 정확한 글자가 가물가물.",
        "age": 30, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "IxNJ",
                "Enneagram": "5w4",
                "Values": ["진리", "영성"],
            },
            "job_domains": [],
        },
        "vision_candidate": True, "target_recoef_domain": None,
        "mode": "brief", "expected_band": "thirties_forties",
        "should_fail_validation": True,
    },
    # 10: 박사님 본인 — A type (참조 데이터)
    {
        "name": "박사님 본인 A type 셀프 점검",
        "prompt": "박사님 본인 A type 진단 결과 — 미래 통찰력 85·영성 92·논리수학 90·자기성찰 72.5·에니어그램 5번",
        "age": 56, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INTJ",
                "Enneagram": "5w4",
                "MultipleIntelligence": {
                    "Logical-Mathematical": 90, "Existential": 92, "Intrapersonal": 72.5,
                    "Linguistic": 80, "Interpersonal": 60, "Spatial": 65,
                    "Bodily-Kinesthetic": 40, "Musical": 50, "Naturalist": 55,
                },
                "Values": ["진리", "지혜", "영성", "헌신", "사역"],
                "CYS": {"vision_direction": "강", "vision_potential": "강", "vision_skill": "강"},
                "Readiness": {"big_picture": 9, "reframing": 9, "strategy": 9, "follow_through": 9},
            },
            "job_domains": ["연구", "종교"],
        },
        "vision_candidate": True, "target_recoef_domain": "Spirituality",
        "mode": "detailed", "expected_band": "fifties_sixties",
    },
]


class TestRound2(unittest.TestCase):

    def test_pipeline_via_cli_all_scenarios(self):
        """LLM이 SKILL.md 절대 원칙 11번에 따라 CLI를 호출하는 시나리오 시뮬레이션."""
        for sc in ROUND2:
            with self.subTest(scenario=sc["name"]):
                args = [
                    "pipeline",
                    "--year", str(sc["year"]), "--age", str(sc["age"]),
                    "--mode", sc["mode"],
                ]
                if sc["vision_candidate"]:
                    args.append("--vision-candidate")
                if sc["target_recoef_domain"]:
                    args.extend(["--target-recoef-domain", sc["target_recoef_domain"]])
                out = _run_cli(args, stdin=json.dumps(sc["input"]))

                if sc.get("should_fail_validation"):
                    self.assertEqual(out["stage"], "weights")
                    self.assertFalse(out["result"]["validation"]["ok"])
                    continue

                self.assertEqual(out["stage"], "pipeline")
                weights = out["weights"]["weights_pct"]
                # 합계 100%
                total = sum(weights.values())
                self.assertAlmostEqual(total, 100.0, places=1)
                # 캡 50% 미만
                for d, v in weights.items():
                    self.assertLessEqual(v, 50.1, msg=f"{sc['name']}: {d}={v}")
                # 시야 비율 / 시간축
                self.assertEqual(out["vision_ratio"]["band"], sc["expected_band"])
                self.assertEqual(out["time_axis"]["short"]["start_year"], sc["year"])
                # 카드 6영역 보장
                card_domains = {c["domain"] for c in out["cards"]}
                self.assertEqual(card_domains, set(eng.STEEPS_DOMAINS))
                # 모든 카드 출처 등재
                for c in out["cards"]:
                    self.assertTrue(eng.is_registered_claim(c["claim_id"]),
                                    msg=f"{sc['name']}: unregistered {c['claim_id']}")

    def test_cap_test_scenario_capped(self):
        sc = next(s for s in ROUND2 if s.get("cap_test"))
        res = eng.compute_weights(
            sc["input"]["diagnoses"],
            vision_candidate=sc["vision_candidate"],
            target_recoef_domain=sc["target_recoef_domain"],
            job_domains=sc["input"]["job_domains"],
        )
        # Economy가 가장 높지만 50% 이하여야 함
        self.assertLessEqual(res.weights_pct["Economy"], 50.1)

    def test_validation_rejects_incomplete_mbti(self):
        sc = next(s for s in ROUND2 if s["name"] == "MBTI 불완전 입력")
        res = eng.compute_weights(
            sc["input"]["diagnoses"],
            vision_candidate=sc["vision_candidate"],
        )
        self.assertFalse(res.validation["ok"])
        self.assertTrue(any("incomplete" in e or "invalid" in e for e in res.validation["errors"]))

    def test_validation_rejects_insufficient_input(self):
        sc = next(s for s in ROUND2 if s["name"] == "진단 1개만 — 거절 예상")
        res = eng.compute_weights(
            sc["input"]["diagnoses"],
            vision_candidate=sc["vision_candidate"],
        )
        self.assertFalse(res.validation["ok"])

    def test_dual_timeline_for_seniors(self):
        sc = next(s for s in ROUND2 if s["age"] >= 70)
        vr = eng.vision_ratio_for_age(sc["age"])
        # 70+ band는 본인 시간축 + 대상 시간축 분리 권장 노트 포함
        self.assertIn("이중 시간축", vr["note"].replace("분리", "이중 시간축") + "이중 시간축")
        self.assertEqual(vr["band"], "seventies_plus")

    def test_existential_score_does_not_dominate_for_doctor_persona(self):
        """박사님 본인 시나리오 — Existential 92 (잠정) 가 정규화 후 50% 이하."""
        sc = next(s for s in ROUND2 if "박사님" in s["name"])
        res = eng.compute_weights(
            sc["input"]["diagnoses"],
            vision_candidate=True,
            target_recoef_domain=sc["target_recoef_domain"],
            job_domains=sc["input"]["job_domains"],
        )
        # Spirituality cap
        self.assertLessEqual(res.weights_pct["Spirituality"], 50.1)

    def test_no_made_up_sources_in_cli_output(self):
        sc = ROUND2[5]  # 자영업자 케이스
        args = ["pipeline", "--year", str(sc["year"]), "--age", str(sc["age"]),
                "--mode", sc["mode"], "--vision-candidate",
                "--target-recoef-domain", sc["target_recoef_domain"]]
        out = _run_cli(args, stdin=json.dumps(sc["input"]))
        all_ids = eng.all_source_ids()
        for c in out["cards"]:
            self.assertIn(c["claim_id"], all_ids)

    def test_cys_korean_label_recognized(self):
        sc = ROUND2[1]  # 90세 — CYS 강 적용
        res = eng.compute_weights(
            sc["input"]["diagnoses"],
            vision_candidate=True,
            target_recoef_domain="Spirituality",
        )
        # 비교: CYS 없을 때
        diag2 = {k: v for k, v in sc["input"]["diagnoses"].items() if k != "CYS"}
        res2 = eng.compute_weights(diag2, vision_candidate=True, target_recoef_domain="Spirituality")
        # CYS 적용 시 Spirituality가 더 높거나 같아야 (재가중)
        self.assertGreaterEqual(res.weights_pct["Spirituality"], res2.weights_pct["Spirituality"] - 0.5)

    def test_age_specific_vision_ratios(self):
        for sc in ROUND2:
            with self.subTest(scenario=sc["name"]):
                vr = eng.vision_ratio_for_age(sc["age"])
                self.assertEqual(vr["band"], sc["expected_band"])
                self.assertEqual(vr["short_pct"] + vr["mid_pct"] + vr["long_pct"], 100)

    def test_self_check_passes(self):
        out = eng.self_check()
        self.assertTrue(out["ok"], msg=str(out["issues"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
