"""
10개 다양 시나리오 검증 — 이전 검증과 전혀 다른 사용자 페르소나.

각 시나리오는 SKILL.md '입력 처리 4유형'(A·B·C·D·E·F·G), 절대 원칙 1~10,
처리 흐름 0~5단계, 결정론 환원 강제 단계를 한 케이스 이상씩 다룬다.

  python3 -m unittest tests/test_10_scenarios.py -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lib import research_engine as eng  # noqa: E402


SCENARIOS = [
    # 1: 청소년 (16세) — 단기 20·중기 45·장기 35, 진단 4종
    {
        "name": "고1 학생 — 신학+AI 융합 비전",
        "age": 16,
        "year": 2027,
        "diagnoses": {
            "MBTI": "INFP",
            "Enneagram": "4w5",
            "MultipleIntelligence": {
                "Linguistic": 9, "Existential": 9, "Intrapersonal": 8,
                "Logical-Mathematical": 7, "Musical": 6, "Interpersonal": 5,
                "Spatial": 4, "Bodily-Kinesthetic": 3, "Naturalist": 5,
            },
            "Values": ["진리", "영성", "창의", "헌신", "공동체"],
        },
        "vision_candidate": True,
        "job_domains": ["종교", "기술"],
        "target_recoef_domain": None,
        "mode": "standard",
        "expected_top_band": "teen",
    },
    # 2: 70대 시니어 코칭형 비전 — 이중 시간축, 단기 60·장기 10
    {
        "name": "은퇴 후 청소년 멘토",
        "age": 72,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ENFJ",
            "Enneagram": "2w1",
            "MultipleIntelligence": {
                "Interpersonal": 10, "Linguistic": 8, "Intrapersonal": 9,
                "Existential": 8, "Musical": 5, "Bodily-Kinesthetic": 4,
                "Logical-Mathematical": 6, "Spatial": 4, "Naturalist": 5,
            },
            "Values": ["봉사", "헌신", "사역", "관계", "공동체"],
            "CYS": {"vision_direction": "강", "vision_potential": "중"},
        },
        "vision_candidate": True,
        "job_domains": ["사회복지", "교육"],
        "target_recoef_domain": "Society",
        "mode": "brief",
        "expected_top_band": "seventies_plus",
    },
    # 3: 20대 청년 — 환경+경제 융합 (E E 영역)
    {
        "name": "기후 스타트업 창업 준비 청년",
        "age": 27,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ENTJ",
            "Enneagram": "8w7",
            "MultipleIntelligence": {
                "Logical-Mathematical": 9, "Naturalist": 9, "Interpersonal": 8,
                "Linguistic": 7, "Spatial": 6, "Intrapersonal": 6,
                "Bodily-Kinesthetic": 5, "Musical": 4, "Existential": 6,
            },
            "STRONG": {"E": 9, "R": 7, "I": 8, "S": 5, "C": 4, "A": 3},
            "Values": ["지구", "생명", "번영", "정의"],
            "Readiness": {"big_picture": 9, "strategy": 8},
        },
        "vision_candidate": True,
        "job_domains": ["농업", "무역"],
        "target_recoef_domain": "Environment",
        "mode": "detailed",
        "expected_top_band": "twenties",
    },
    # 4: 의료 도메인 + 부정 시나리오 우선 (wildcards 포함)
    {
        "name": "팬데믹 후 의료 시스템 우려 의사",
        "age": 42,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ISTJ",
            "Enneagram": "6w5",
            "MultipleIntelligence": {
                "Logical-Mathematical": 9, "Intrapersonal": 7, "Bodily-Kinesthetic": 8,
                "Linguistic": 6, "Interpersonal": 7, "Spatial": 6,
                "Musical": 3, "Naturalist": 5, "Existential": 4,
            },
            "STRONG": {"I": 9, "S": 7, "R": 6, "C": 5, "A": 3, "E": 4},
        },
        "vision_candidate": True,
        "job_domains": ["의료"],
        "target_recoef_domain": "Technology",
        "mode": "standard",
        "include_wildcards": True,
        "expected_top_band": "thirties_forties",
    },
    # 5: 어린이 (8세) — 부모/보호자 대리, child_under10 band
    {
        "name": "초등 2학년 자녀의 미래 (부모 대리)",
        "age": 8,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ENFP",  # 부모가 관찰 입력
            "Enneagram": "7",
            "Values": ["창의", "자유", "공동체"],
        },
        "vision_candidate": True,
        "job_domains": ["교육", "예술"],
        "target_recoef_domain": None,
        "mode": "brief",
        "expected_top_band": "child_under10",
    },
    # 6: 진단 갈등 — 영역 분산 (비전 다중 후보 판정)
    {
        "name": "MBTI·MI·가치가 서로 다른 방향",
        "age": 35,
        "year": 2026,
        "diagnoses": {
            "MBTI": "INTP",
            "Enneagram": "5w4",
            "MultipleIntelligence": {
                "Logical-Mathematical": 9, "Naturalist": 9, "Existential": 9,
                "Spatial": 8, "Linguistic": 8, "Interpersonal": 8,
                "Bodily-Kinesthetic": 8, "Musical": 8, "Intrapersonal": 8,
            },
            "STRONG": {"R": 7, "I": 7, "A": 7, "S": 7, "E": 7, "C": 7},
            "Values": ["정의", "영성", "안정", "가족", "지구", "진리"],
        },
        "vision_candidate": True,
        "job_domains": [],
        "target_recoef_domain": None,
        "mode": "standard",
        "expected_top_band": "thirties_forties",
        "should_be_split": True,
    },
    # 7: 입력 누락 다수 — 진단 4개 누락 → warn_insufficient_differentiation
    {
        "name": "MBTI·에니어그램만 입력한 사용자",
        "age": 52,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ESFJ",
            "Enneagram": "9w1",
            "Values": ["관계", "안정", "공동체"],
        },
        "vision_candidate": True,
        "job_domains": ["코칭"],
        "target_recoef_domain": None,
        "mode": "standard",
        "expected_top_band": "fifties_sixties",
        "expect_missing_warn": True,
    },
    # 8: 법조인 — Politics 우세
    {
        "name": "정의 추구 변호사",
        "age": 38,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ENTJ",
            "Enneagram": "1w2",
            "MultipleIntelligence": {
                "Linguistic": 9, "Logical-Mathematical": 9, "Interpersonal": 8,
                "Intrapersonal": 7, "Musical": 4, "Spatial": 5,
                "Bodily-Kinesthetic": 4, "Naturalist": 3, "Existential": 6,
            },
            "STRONG": {"E": 8, "I": 8, "S": 7, "A": 5, "R": 3, "C": 6},
            "Values": ["정의", "공정", "평등"],
        },
        "vision_candidate": True,
        "job_domains": ["법조"],
        "target_recoef_domain": "Politics",
        "mode": "standard",
        "expected_top_band": "thirties_forties",
    },
    # 9: 금융 도메인 + 가족 단위(부모 + 자녀 시간축 분리는 별도 호출)
    {
        "name": "결혼 신혼 — 재정 코치 청취",
        "age": 31,
        "year": 2026,
        "diagnoses": {
            "MBTI": "ISTJ",
            "Enneagram": "3w2",
            "MultipleIntelligence": {
                "Logical-Mathematical": 9, "Interpersonal": 7, "Linguistic": 7,
                "Intrapersonal": 6, "Naturalist": 4, "Existential": 5,
                "Spatial": 6, "Musical": 4, "Bodily-Kinesthetic": 5,
            },
            "STRONG": {"C": 9, "E": 8, "I": 7, "S": 6, "A": 3, "R": 4},
            "Values": ["안정", "번영", "가족", "성취"],
        },
        "vision_candidate": True,
        "job_domains": ["금융"],
        "target_recoef_domain": "Economy",
        "mode": "standard",
        "expected_top_band": "thirties_forties",
    },
    # 10: 해외 거주 한국인 + 학문 융합 (심리+신경과학) + Existential 잠정
    {
        "name": "재미 한국인 — 심리+신경과학 융합 학자",
        "age": 45,
        "year": 2026,
        "diagnoses": {
            "MBTI": "INFJ",
            "Enneagram": "5w4",
            "MultipleIntelligence": {
                "Intrapersonal": 10, "Existential": 9, "Linguistic": 8,
                "Logical-Mathematical": 9, "Interpersonal": 7,
                "Spatial": 5, "Musical": 6, "Bodily-Kinesthetic": 4, "Naturalist": 5,
            },
            "STRONG": {"I": 9, "S": 7, "A": 6, "E": 4, "R": 3, "C": 5},
            "Values": ["진리", "지혜", "학문", "영성"],
            "CYS": {"vision_direction": "강", "vision_potential": "강", "vision_skill": "강"},
            "Readiness": {"big_picture": 9, "reframing": 9, "strategy": 7, "follow_through": 8},
        },
        "vision_candidate": True,
        "job_domains": ["연구", "의료"],
        "target_recoef_domain": "Spirituality",
        "mode": "detailed",
        "expected_top_band": "thirties_forties",
    },
]


class TestTenScenarios(unittest.TestCase):
    def _run_pipeline(self, sc: dict):
        res = eng.compute_weights(
            sc["diagnoses"],
            vision_candidate=sc.get("vision_candidate", True),
            target_recoef_domain=sc.get("target_recoef_domain"),
            job_domains=sc.get("job_domains"),
        )
        return res

    def test_all_scenarios_compute(self):
        for sc in SCENARIOS:
            with self.subTest(scenario=sc["name"]):
                res = self._run_pipeline(sc)
                # 합계 100% ± 0.1
                total = sum(res.weights_pct.values())
                self.assertAlmostEqual(total, 100.0, places=1,
                                       msg=f"{sc['name']}: total {total}")
                # 6영역 모두 키 존재
                self.assertEqual(set(res.weights_pct.keys()), set(eng.STEEPS_DOMAINS))
                # 영역 캡 50% 이하
                for d, v in res.weights_pct.items():
                    self.assertLessEqual(v, 50.1, msg=f"{sc['name']}: {d} = {v}")

    def test_age_band_correct(self):
        for sc in SCENARIOS:
            with self.subTest(scenario=sc["name"]):
                vr = eng.vision_ratio_for_age(sc["age"])
                self.assertEqual(vr["band"], sc["expected_top_band"])

    def test_time_axis_correct(self):
        for sc in SCENARIOS:
            with self.subTest(scenario=sc["name"]):
                ax = eng.absolute_time_axis(sc["year"])
                self.assertEqual(ax["short"]["start_year"], sc["year"])
                self.assertEqual(ax["mid"]["end_year"], sc["year"] + 15)
                self.assertEqual(ax["long"]["end_year"], sc["year"] + 30)

    def test_cards_built_with_registered_sources(self):
        for sc in SCENARIOS:
            with self.subTest(scenario=sc["name"]):
                res = self._run_pipeline(sc)
                cards = eng.build_change_cards(
                    res.weights_pct,
                    include_wildcards=sc.get("include_wildcards", False),
                )
                cards = eng.select_top_cards(cards, mode=sc["mode"])
                cards = eng.ensure_six_domain_min_one(cards)
                domains = {c.domain for c in cards}
                self.assertEqual(domains, set(eng.STEEPS_DOMAINS),
                                 msg=f"{sc['name']}: missing domains {set(eng.STEEPS_DOMAINS) - domains}")
                # 모든 카드는 등재 출처에서만 — claim_id가 sources.json에 있어야 함
                for c in cards:
                    self.assertTrue(eng.is_registered_claim(c.claim_id),
                                    msg=f"{sc['name']}: unregistered claim '{c.claim_id}'")

    def test_split_detection_works(self):
        sc = next(s for s in SCENARIOS if s.get("should_be_split"))
        res = self._run_pipeline(sc)
        self.assertTrue(res.vision_split["is_split"],
                        msg=f"split expected for {sc['name']} got stdev={res.vision_split['stdev_pct']} diff={res.vision_split['top_two_diff_pct']}")

    def test_missing_warning_works(self):
        sc = next(s for s in SCENARIOS if s.get("expect_missing_warn"))
        res = self._run_pipeline(sc)
        self.assertTrue(res.missing_notice["warn_insufficient_differentiation"],
                        msg=f"missing warn expected for {sc['name']}")

    def test_deterministic_across_runs(self):
        # 동일 입력 → 동일 산출
        for sc in SCENARIOS:
            with self.subTest(scenario=sc["name"]):
                a = self._run_pipeline(sc).weights_pct
                b = self._run_pipeline(sc).weights_pct
                self.assertEqual(a, b)

    def test_response_patterns_present_for_mbti_enneagram(self):
        for sc in SCENARIOS:
            with self.subTest(scenario=sc["name"]):
                res = self._run_pipeline(sc)
                if "MBTI" in sc["diagnoses"]:
                    self.assertIsNotNone(res.response_patterns["MBTI"])
                if "Enneagram" in sc["diagnoses"]:
                    self.assertIsNotNone(res.response_patterns["Enneagram"])

    def test_no_hallucination_in_sources(self):
        # 등록 ID 외의 모든 임의 ID는 None 반환
        fake_ids = [
            "made_up_claim_x", "fake_2050_oracle", "magic_number_99",
            "future_revival", "ai_god_arrival",
        ]
        for fid in fake_ids:
            for d in eng.STEEPS_DOMAINS:
                for h in ("short", "mid", "long"):
                    self.assertIsNone(eng.get_source(d, h, fid))

    def test_existential_provisional_in_full_scenarios(self):
        # Existential을 가진 시나리오들 — 잠정 0.5 vs full 1.0 차이
        for sc in SCENARIOS:
            if not sc["diagnoses"].get("MultipleIntelligence"):
                continue
            if "Existential" not in sc["diagnoses"]["MultipleIntelligence"]:
                continue
            with self.subTest(scenario=sc["name"]):
                mi = sc["diagnoses"]["MultipleIntelligence"]
                prov = eng.map_multiple_intelligence(mi)
                full = eng.map_multiple_intelligence(mi, existential_full_weight=True)
                # full 모드의 Spirituality 점수가 prov 모드 이상
                self.assertGreaterEqual(full["Spirituality"], prov["Spirituality"])

    def test_six_domain_min_one_enforced(self):
        # 한 시나리오에서 영역 가중치 0인 도메인도 카드 1개 보장
        sc = SCENARIOS[0]
        res = self._run_pipeline(sc)
        cards = eng.build_change_cards(res.weights_pct)
        cards = eng.select_top_cards(cards, mode=sc["mode"])
        cards = eng.ensure_six_domain_min_one(cards)
        for d in eng.STEEPS_DOMAINS:
            self.assertTrue(any(c.domain == d for c in cards),
                            msg=f"{sc['name']}: domain {d} has no card")


if __name__ == "__main__":
    unittest.main(verbosity=2)
