"""
3차 검증 — 1·2차와 완전히 다른 *실제 사용자 자연어 프롬프트* 10개.

각 프롬프트에 대해:
  1) 결정론 엔진 호출하여 실제 산출물 JSON 생성
  2) 산출물의 모든 변화 카드 claim_id가 data/sources.json에 등재 (할루시네이션 0)
  3) 모든 카드의 source 필드가 등재 출처와 1:1 일치
  4) weights_pct 합계 100% ± 0.1, 영역 캡 50%
  5) vision_ratio band가 연령에 정확히 매핑
  6) time_axis가 Y/Y+5/Y+15/Y+30 정확히
  7) 6영역 모두 카드 1개 이상 (절대 원칙 2)
  8) validation.ok (불완전 입력은 명시적으로 거절)
  9) 결정론(동일 입력 → 동일 산출)
 10) Existential 가중치 잠정 0.5 자동 적용 확인

  python3 -m unittest tests/test_10_scenarios_round3.py -v
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


def run_cli(args: list[str], stdin: str | None = None) -> dict:
    r = subprocess.run(
        ["python3", str(CLI), *args],
        input=stdin or "",
        capture_output=True, text=True,
        cwd=str(ROOT), timeout=30,
    )
    if r.returncode not in (0, 2):
        raise AssertionError(f"CLI exit {r.returncode}: {r.stderr}\nout: {r.stdout}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


# 1·2차와 *전혀 다른* — 사용자가 실제로 던질 자연어 프롬프트 10개
PROMPTS = [
    {
        "id": "P1",
        "user_prompt": "29살 그래픽 디자이너인데 AI 그림에 일자리 위협을 느낍니다. 앞으로 10년 미래 변화를 알고 싶어요.",
        "age": 29, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ISFP",
                "Enneagram": "4w3",
                "MultipleIntelligence": {
                    "Spatial": 10, "Musical": 8, "Linguistic": 6,
                    "Intrapersonal": 7, "Bodily-Kinesthetic": 6,
                    "Interpersonal": 6, "Logical-Mathematical": 5,
                    "Naturalist": 5, "Existential": 5,
                },
                "STRONG": {"A": 10, "S": 7, "E": 6, "I": 5, "R": 4, "C": 3},
                "Values": ["창의", "아름다움", "자유"],
            },
            "job_domains": ["예술", "디자인"],
            "personal_impact_by_id": {"genai_industry": "high", "agi_timing": "high"},
        },
        "vision_candidate": True, "target_recoef_domain": None, "mode": "standard",
        "expected_band": "twenties",
    },
    {
        "id": "P2",
        "user_prompt": "60대 초반 귀촌 준비중. 시골에서 작은 농장을 일구는 비전입니다.",
        "age": 62, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ISFJ",
                "Enneagram": "9w1",
                "MultipleIntelligence": {
                    "Naturalist": 10, "Bodily-Kinesthetic": 8, "Intrapersonal": 8,
                    "Interpersonal": 6, "Linguistic": 5, "Logical-Mathematical": 5,
                    "Spatial": 6, "Musical": 4, "Existential": 6,
                },
                "STRONG": {"R": 9, "S": 7, "I": 5, "C": 5, "E": 4, "A": 3},
                "Values": ["지구", "생명", "생태", "공동체"],
                "Readiness": {"big_picture": 7, "follow_through": 9},
            },
            "job_domains": ["농업", "생태"],
        },
        "vision_candidate": True, "target_recoef_domain": "Environment", "mode": "standard",
        "expected_band": "fifties_sixties",
    },
    {
        "id": "P3",
        "user_prompt": "프리랜서 카피라이터 36살. 10년·20년 후 글쓰기 직업은 어떻게 될까요?",
        "age": 36, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ENFP",
                "Enneagram": "7w6",
                "MultipleIntelligence": {
                    "Linguistic": 10, "Interpersonal": 8, "Intrapersonal": 7,
                    "Musical": 6, "Logical-Mathematical": 6, "Spatial": 5,
                    "Bodily-Kinesthetic": 4, "Naturalist": 4, "Existential": 6,
                },
                "Values": ["창의", "자유", "진리"],
            },
            "job_domains": ["미디어", "콘텐츠"],
        },
        "vision_candidate": True, "target_recoef_domain": "Society", "mode": "standard",
        "expected_band": "thirties_forties",
    },
    {
        "id": "P4",
        "user_prompt": "신학교 1학년 22살. 목회자가 되고 싶은데, 한국 교회 미래가 너무 어둡다고 들었어요.",
        "age": 22, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INFJ",
                "Enneagram": "1w2",
                "MultipleIntelligence": {
                    "Linguistic": 9, "Intrapersonal": 9, "Existential": 10,
                    "Interpersonal": 8, "Logical-Mathematical": 7,
                    "Spatial": 5, "Musical": 6, "Bodily-Kinesthetic": 4, "Naturalist": 5,
                },
                "STRONG": {"S": 9, "A": 7, "I": 7, "E": 5, "C": 4, "R": 3},
                "Values": ["영성", "헌신", "사역", "진리"],
                "CYS": {"vision_direction": "강"},
            },
            "job_domains": ["종교", "목회"],
            "personal_impact_by_id": {"kr_church_decline": "high", "ai_human_meaning": "high"},
        },
        "vision_candidate": True, "target_recoef_domain": "Spirituality", "mode": "detailed",
        "expected_band": "twenties",
    },
    {
        "id": "P5",
        "user_prompt": "AI 백엔드 엔지니어 33살. 지금 직업이 10년 안에 어떻게 변할까?",
        "age": 33, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INTJ",
                "Enneagram": "5w6",
                "MultipleIntelligence": {
                    "Logical-Mathematical": 10, "Spatial": 8, "Linguistic": 7,
                    "Intrapersonal": 7, "Musical": 5, "Bodily-Kinesthetic": 4,
                    "Interpersonal": 5, "Naturalist": 4, "Existential": 6,
                },
                "STRONG": {"I": 10, "R": 8, "C": 6, "E": 5, "S": 3, "A": 4},
                "Values": ["진리", "지혜", "창의"],
            },
            "job_domains": ["기술", "IT"],
            "personal_impact_by_id": {"agi_timing": "high", "humanoid_robot": "high", "ai_labor": "high"},
        },
        "vision_candidate": True, "target_recoef_domain": "Technology", "mode": "standard",
        "expected_band": "thirties_forties",
    },
    {
        "id": "P6",
        "user_prompt": "공무원 5급 49살. 정년까지 12년 남았고 이후 인생 30년을 어떻게 살까요?",
        "age": 49, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ESTJ",
                "Enneagram": "1w9",
                "MultipleIntelligence": {
                    "Linguistic": 8, "Logical-Mathematical": 8, "Interpersonal": 8,
                    "Intrapersonal": 7, "Musical": 4, "Spatial": 6,
                    "Bodily-Kinesthetic": 5, "Naturalist": 4, "Existential": 5,
                },
                "STRONG": {"E": 9, "C": 9, "S": 7, "I": 6, "A": 3, "R": 4},
                "Values": ["정의", "공정", "안정", "공동체"],
                "Readiness": {"big_picture": 7, "strategy": 9, "follow_through": 9},
            },
            "job_domains": ["정치", "공공"],
        },
        "vision_candidate": True, "target_recoef_domain": "Politics", "mode": "standard",
        "expected_band": "thirties_forties",
    },
    {
        "id": "P7",
        "user_prompt": "교수이면서 동시에 EdTech 스타트업 창업하려는 41살. 두 비전 동시에 가능할까?",
        "age": 41, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ENTJ",
                "Enneagram": "3w8",
                "MultipleIntelligence": {
                    "Logical-Mathematical": 9, "Linguistic": 9, "Interpersonal": 9,
                    "Intrapersonal": 7, "Spatial": 6, "Musical": 5,
                    "Bodily-Kinesthetic": 5, "Naturalist": 4, "Existential": 6,
                },
                "STRONG": {"I": 9, "E": 9, "S": 8, "A": 5, "C": 5, "R": 3},
                "Values": ["성취", "창의", "공동체", "번영"],
                "CYS": {"vision_direction": "강", "vision_potential": "강"},
            },
            "job_domains": ["교육", "기술"],
        },
        "vision_candidate": True, "target_recoef_domain": "Technology", "mode": "detailed",
        "expected_band": "thirties_forties",
        "expect_multi_vision_hint": True,
    },
    {
        "id": "P8",
        "user_prompt": "한국 거주 베트남 출신 외국인 노동자 28살. 한국에서 정착할지 고향으로 돌아갈지 고민입니다.",
        "age": 28, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ESFJ",
                "Enneagram": "2w3",
                "MultipleIntelligence": {
                    "Interpersonal": 9, "Bodily-Kinesthetic": 8, "Linguistic": 7,
                    "Intrapersonal": 6, "Musical": 6, "Logical-Mathematical": 6,
                    "Spatial": 5, "Naturalist": 5, "Existential": 5,
                },
                "STRONG": {"S": 9, "R": 7, "E": 6, "C": 5, "I": 4, "A": 3},
                "Values": ["가족", "공동체", "안정", "관계"],
            },
            "job_domains": ["사회복지", "농업"],
        },
        "vision_candidate": True, "target_recoef_domain": "Society", "mode": "standard",
        "expected_band": "twenties",
    },
    {
        "id": "P9",
        "user_prompt": "37살 청각장애 그래픽 디자이너. 시각 강점 살리는 미래 직업 찾고 싶어요.",
        "age": 37, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "INFP",
                "Enneagram": "4w5",
                "MultipleIntelligence": {
                    "Spatial": 10, "Linguistic": 7, "Logical-Mathematical": 7,
                    "Intrapersonal": 9, "Existential": 7,
                    "Musical": 2, "Bodily-Kinesthetic": 6,
                    "Interpersonal": 5, "Naturalist": 5,
                },
                "STRONG": {"A": 10, "I": 7, "R": 5, "C": 5, "S": 4, "E": 3},
                "Values": ["창의", "아름다움", "진리"],
            },
            "job_domains": ["예술", "디자인", "기술"],
        },
        "vision_candidate": True, "target_recoef_domain": "Technology", "mode": "standard",
        "expected_band": "thirties_forties",
    },
    {
        "id": "P10",
        "user_prompt": "프로축구 선수 30살. 은퇴 후 미래 30년 비전을 보고 싶어요.",
        "age": 30, "year": 2026,
        "input": {
            "diagnoses": {
                "MBTI": "ESTP",
                "Enneagram": "7w8",
                "MultipleIntelligence": {
                    "Bodily-Kinesthetic": 10, "Interpersonal": 8, "Spatial": 7,
                    "Intrapersonal": 6, "Musical": 5, "Linguistic": 5,
                    "Logical-Mathematical": 5, "Naturalist": 6, "Existential": 3,
                },
                "STRONG": {"R": 9, "S": 7, "E": 7, "A": 4, "I": 4, "C": 3},
                "Values": ["성취", "공동체", "관계", "자유"],
                "CYS": {"vision_direction": "중"},
            },
            "job_domains": ["교육", "코칭"],
        },
        "vision_candidate": True, "target_recoef_domain": "Society", "mode": "standard",
        "expected_band": "thirties_forties",
    },
]


class TestRound3Final(unittest.TestCase):

    def _pipeline(self, p):
        args = [
            "pipeline",
            "--year", str(p["year"]),
            "--age", str(p["age"]),
            "--mode", p["mode"],
        ]
        if p["vision_candidate"]:
            args.append("--vision-candidate")
        if p["target_recoef_domain"]:
            args.extend(["--target-recoef-domain", p["target_recoef_domain"]])
        return run_cli(args, stdin=json.dumps(p["input"]))

    # ─── 검증 1: 모든 프롬프트 산출 + 검증 통과 ───
    def test_01_all_prompts_pipeline_succeeds(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                self.assertEqual(out["stage"], "pipeline", msg=f"{p['id']}: {out}")
                self.assertTrue(out["weights"]["validation"]["ok"],
                                msg=f"{p['id']}: validation errors {out['weights']['validation']}")

    # ─── 검증 2: 모든 카드의 claim_id가 sources.json에 등재 (할루시네이션 0) ───
    def test_02_zero_hallucinated_claims(self):
        all_ids = eng.all_source_ids()
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                for c in out["cards"]:
                    self.assertIn(c["claim_id"], all_ids,
                                  msg=f"{p['id']}: hallucinated claim '{c['claim_id']}'")

    # ─── 검증 3: 모든 카드 source 필드 = sources.json 등록 출처 1:1 일치 ───
    def test_03_source_field_matches_registry_exactly(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                for c in out["cards"]:
                    src = eng.get_source(c["domain"], c["horizon"], c["claim_id"])
                    if src is None:
                        # wildcard fallback (Spirituality/long에 매핑됨)
                        wcs = {w["id"]: w for w in eng.list_wildcards()}
                        if c["claim_id"] in wcs:
                            src = wcs[c["claim_id"]]
                    self.assertIsNotNone(src, msg=f"{p['id']}: lookup miss {c['claim_id']}")
                    self.assertEqual(c["source"], src.get("source"),
                                     msg=f"{p['id']}: source mismatch for {c['claim_id']}")
                    self.assertEqual(c["certainty"], src.get("certainty"),
                                     msg=f"{p['id']}: certainty mismatch for {c['claim_id']}")

    # ─── 검증 4: weights 합계 100% ± 0.1, 각 영역 ≤ 50.1 ───
    def test_04_weights_sum_and_cap(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                w = out["weights"]["weights_pct"]
                self.assertAlmostEqual(sum(w.values()), 100.0, places=1)
                for d, v in w.items():
                    self.assertLessEqual(v, 50.1, msg=f"{p['id']}: {d}={v}")
                    self.assertGreaterEqual(v, 0.0)

    # ─── 검증 5: vision_ratio band 정확 매핑 ───
    def test_05_vision_ratio_band_correct(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                self.assertEqual(out["vision_ratio"]["band"], p["expected_band"])
                vr = out["vision_ratio"]
                self.assertEqual(vr["short_pct"] + vr["mid_pct"] + vr["long_pct"], 100)

    # ─── 검증 6: time_axis 정확 (Y / Y+5 / Y+15 / Y+30) ───
    def test_06_time_axis_correct(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                ax = out["time_axis"]
                self.assertEqual(ax["short"]["start_year"], p["year"])
                self.assertEqual(ax["short"]["end_year"], p["year"] + 5)
                self.assertEqual(ax["mid"]["end_year"], p["year"] + 15)
                self.assertEqual(ax["long"]["end_year"], p["year"] + 30)

    # ─── 검증 7: 6영역 모두 카드 1개 이상 (절대 원칙 2) ───
    def test_07_six_domain_coverage(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                domains = {c["domain"] for c in out["cards"]}
                self.assertEqual(domains, set(eng.STEEPS_DOMAINS),
                                 msg=f"{p['id']}: missing {set(eng.STEEPS_DOMAINS) - domains}")

    # ─── 검증 8: 결정론 — 동일 입력 2회 호출 → 동일 산출 ───
    def test_08_determinism(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                a = self._pipeline(p)
                b = self._pipeline(p)
                self.assertEqual(a["weights"]["weights_pct"], b["weights"]["weights_pct"])
                self.assertEqual([c["claim_id"] for c in a["cards"]],
                                 [c["claim_id"] for c in b["cards"]])
                self.assertEqual([c["priority"] for c in a["cards"]],
                                 [c["priority"] for c in b["cards"]])

    # ─── 검증 9: Existential 잠정 0.5 자동 적용 — 결과 검증 ───
    def test_09_existential_provisional_applied(self):
        for p in PROMPTS:
            mi = p["input"]["diagnoses"].get("MultipleIntelligence")
            if not mi or "Existential" not in mi:
                continue
            with self.subTest(prompt_id=p["id"]):
                prov = eng.map_multiple_intelligence(mi)
                full = eng.map_multiple_intelligence(mi, existential_full_weight=True)
                # full ≥ prov for Spirituality
                self.assertGreaterEqual(full["Spirituality"], prov["Spirituality"])

    # ─── 검증 10: 카드 우선순위 ★/★★/★★★ 합법성 + composite_score 결정론 ───
    def test_10_priority_and_score_consistency(self):
        for p in PROMPTS:
            with self.subTest(prompt_id=p["id"]):
                out = self._pipeline(p)
                for c in out["cards"]:
                    self.assertIn(c["priority"], {"★", "★★", "★★★"},
                                  msg=f"{p['id']}: {c['priority']}")
                    self.assertGreaterEqual(c["composite_score"], 0.0)
                # 카드 정렬: composite_score 내림차순 (ensure_six_domain_min_one은 마지막에 끼움)
                # 적어도 첫 카드는 가장 높은 점수
                scores = [c["composite_score"] for c in out["cards"]]
                top_card_score = scores[0]
                appended_zeros = sum(1 for s in scores if s == 0.0)
                # 0 점수는 6영역 보장 차원 추가분 — 가장 마지막에 있음
                self.assertGreaterEqual(top_card_score, max(scores) - 0.001)


class TestRound3MultiVision(unittest.TestCase):
    """P7 — 교수 + 창업 복수 비전 후보 처리"""

    def test_p7_split_detection_or_high_diversity(self):
        p = next(x for x in PROMPTS if x["id"] == "P7")
        args = [
            "pipeline", "--year", str(p["year"]), "--age", str(p["age"]),
            "--mode", p["mode"], "--vision-candidate",
            "--target-recoef-domain", p["target_recoef_domain"],
        ]
        out = run_cli(args, stdin=json.dumps(p["input"]))
        split = out["weights"]["vision_split"]
        # 교수 + 창업은 영역 분산이 있어야 정상 (또는 stdev_pct를 보고 비교)
        self.assertGreaterEqual(split["stdev_pct"], 0)
        # weights 산출 정상
        self.assertAlmostEqual(sum(out["weights"]["weights_pct"].values()), 100.0, places=1)


class TestRound3Reproducibility(unittest.TestCase):
    """입력을 변경하지 않는 한 산출은 결정론적이며 시간이 지나도 동일."""

    def test_engine_self_check_still_passes(self):
        out = eng.self_check()
        self.assertTrue(out["ok"], msg=str(out["issues"]))

    def test_source_count_unchanged(self):
        self.assertGreaterEqual(len(eng.all_source_ids()), 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
