"""vision-strategy-coach 10개 검증 프롬프트 — 결정론 모듈 종합 검증.

이전 검증 사이클과 *전혀 다른* 시나리오 10개로 스킬 핵심 동작을 검증한다.
"테스트 통과를 위한 흉내" 코드 작성을 차단하기 위해 임의 사용자 시나리오를
사용하고, 각 시나리오에서 결정론 함수가 SKILL.md 사양과 1:1 대응하는지를
검사한다.

전 항목 PASS가 목표.
"""

from __future__ import annotations

import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import strategy_calc as sc  # noqa: E402


class Verification10Prompts(unittest.TestCase):
    """10개의 새로운 작업 명령 프롬프트로 vision-strategy-coach 검증."""

    # ── Prompt 1 ────────────────────────────────────────────────
    def test_prompt_01_returning_mother_pivot(self):
        """프롬프트 1: 육아 후 복직하는 30대 워킹맘이 'IT 개발자로 전환'
        비전을 제시. 비전만 입력. Mode=B 분류 + 첫 한 걸음 검증."""
        mode = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=False, has_mbti=False,
            has_values=False, has_strong=False, has_career=False,
            progress_check_only=False, is_baksanim=False,
        )
        self.assertEqual(mode["mode"], "B")

        first_step = "내일 아침 7시, 집 책상에서, Python 기초 강의 1강을 25분간 수강"
        self.assertTrue(sc.validate_first_step(first_step).ok)

    # ── Prompt 2 ────────────────────────────────────────────────
    def test_prompt_02_senior_pastor_retirement_strategy(self):
        """프롬프트 2: 67세 은퇴 목사가 '디아스포라 교회 메토링 1000명'
        LTG를 5년 후 목표로 설정. SMART S·M·T 통과해야 함."""
        ltg = "2031년까지 디아스포라 교회 후배 목회자 100명에게 멘토링 시간을 제공한다"
        r = sc.validate_smart_goal(ltg)
        self.assertTrue(r.ok, r.reasons)

    # ── Prompt 3 ────────────────────────────────────────────────
    def test_prompt_03_college_student_career_pivot(self):
        """프롬프트 3: 대학 4학년이 진단만 가지고 비전 정립 요청. Mode=C."""
        mode = sc.classify_input_mode(
            has_vision_statement=False, has_readiness=True, has_mbti=True,
            has_values=True, has_strong=True, has_career=False,
            progress_check_only=False, is_baksanim=False,
        )
        self.assertEqual(mode["mode"], "C")

    # ── Prompt 4 ────────────────────────────────────────────────
    def test_prompt_04_business_owner_quarterly_progress_60pct(self):
        """프롬프트 4: 자영업자가 STG 진척률 58%로 분기 점검 의뢰.
        Pivot trigger가 'pivot_required'를 반환해야 함."""
        pivot = sc.check_pivot_trigger(58)
        self.assertEqual(pivot["status"], "pivot_required")
        self.assertEqual(pivot["action"], "STG 재설계")

    # ── Prompt 5 ────────────────────────────────────────────────
    def test_prompt_05_artist_undated_ltg_should_fail(self):
        """프롬프트 5: 신진 작가가 기한 없이 'OECD 미술관 전시'를 LTG로 제시.
        Time-bound 결여로 SMART 미통과 → 사용자에게 보강 요청 필요."""
        ltg = "OECD 미술관 전시를 5회 갖는다"  # 기한 없음
        r = sc.validate_smart_goal(ltg)
        self.assertFalse(r.ok)
        self.assertIn("time:no_deadline", r.reasons)

    # ── Prompt 6 ────────────────────────────────────────────────
    def test_prompt_06_korean_grandmother_quarterly_overload(self):
        """프롬프트 6: 70대 권사님이 분기당 5개 STG를 추진하려 함.
        validate_quarter_focus가 violation을 잡아야 함."""
        r = sc.validate_quarter_focus([5, 3, 3, 2])
        self.assertFalse(r.ok)
        self.assertIn("Q1:5>3", r.reasons)

    # ── Prompt 7 ────────────────────────────────────────────────
    def test_prompt_07_high_school_teacher_readiness_low_followthrough(self):
        """프롬프트 7: 고교 교사가 readiness 4점수 제출 — FollowThrough 30점.
        분기점검 대신 '주간 점검 더 짧고 자주' 분기로 가야 함."""
        r = sc.readiness_branch({
            "BigPicture": 80, "Reframing": 70, "Strategy": 65, "FollowThrough": 30
        })
        self.assertTrue(r["ok"])
        self.assertEqual(r["branch"]["FollowThrough"], "주간 점검을 더 짧고 자주")

    # ── Prompt 8 ────────────────────────────────────────────────
    def test_prompt_08_coach_must_not_invent_publisher(self):
        """프롬프트 8: 박사님 비전 코칭 산출문에서 사용자가 언급하지 않은
        출판사 'BCD북스'를 코치가 임의로 추가했을 때 차단되는지."""
        coach_doc = (
            "박사님의 LTG-1을 위해 BCD북스와 협력하시고, 김민수 박사의 추천을 받으세요. "
            "SMART(Doran 1981 *Management Review* 70(11):35-36) 방식으로 정리합니다."
        )
        user_doc = "박사님 비전. 단행본을 출판하고 싶다."
        r = sc.filter_unsourced_entities(coach_doc, user_doc)
        self.assertFalse(r["ok"])
        violation_tokens = {v["token"] for v in r["violations"]}
        self.assertIn("BCD북스", violation_tokens)
        self.assertIn("김민수 박사", violation_tokens)

    # ── Prompt 9 ────────────────────────────────────────────────
    def test_prompt_09_review_schedule_for_new_user(self):
        """프롬프트 9: 신규 사용자가 2027-01-15에 코칭 시작.
        다음 점검 4개 일정이 정확히 계산되는지."""
        s = sc.calculate_review_schedule("2027-01-15")
        # 2027-01-15는 금요일 (weekday=4)
        # 다음 일요일 = 2027-01-17
        self.assertEqual(s["weekly"], "2027-01-17")
        # 1월 마지막 금요일 = 2027-01-29
        self.assertEqual(s["monthly"], "2027-01-29")
        # Q1 끝 = 3월. 3월 마지막 금요일 = 2027-03-26, 그 주 월요일 = 2027-03-22
        self.assertEqual(s["quarterly"], "2027-03-22")
        # 12월 첫 월요일 = 2027-12-06
        self.assertEqual(s["annual"], "2027-12-06")

    # ── Prompt 10 ───────────────────────────────────────────────
    def test_prompt_10_q08_citation_must_be_verbatim(self):
        """프롬프트 10: 코치가 Step 4에서 Q08을 인용. 의역하면 안 되고
        정확한 원문이어야 함."""
        good = "vision-readiness Q08 — \"I am good at trimming a giant dream into a first step I can take tomorrow morning\""
        bad = "Q08은 '거대한 꿈을 내일의 작은 걸음으로 잘 줄인다'는 능력을 측정"

        self.assertTrue(sc.verify_q08_canonical(good).ok)
        self.assertFalse(sc.verify_q08_canonical(bad).ok)

        # SMART 인용 검증
        c = sc.lookup_citation("SMART")
        self.assertEqual(c["author"], "George T. Doran")
        self.assertEqual(c["year"], 1981)
        self.assertEqual(c["venue"], "Management Review")
        self.assertEqual(c["volume"], 70)
        self.assertEqual(c["issue"], 11)
        self.assertEqual(c["pages"], "35-36")


class Verification10Integration(unittest.TestCase):
    """10개 프롬프트를 1개 통합 시나리오로 묶어 5단계 모두 결정론 통과 검증."""

    def test_integrated_baksanim_full_strategy_doc(self):
        # 박사님 본인 사용 시나리오 (Mode=E)
        mode = sc.classify_input_mode(
            has_vision_statement=True, has_readiness=True, has_mbti=True,
            has_values=True, has_strong=True, has_career=True,
            progress_check_only=False, is_baksanim=True,
        )
        self.assertEqual(mode["mode"], "E")

        # readiness
        r = sc.readiness_branch({
            "BigPicture": 85, "Reframing": 72, "Strategy": 78, "FollowThrough": 68
        })
        self.assertTrue(r["ok"])

        # LTG 3개 (Mode E: 박사님 본인 진술 안에서)
        ltgs = [
            "2030년까지 미래학 단행본 4권을 출판한다",
            "2028년까지 디아스포라 후배 목회자 50명에게 멘토링 시간을 제공한다",
            "2029년까지 강의 100회를 진행한다",
        ]
        self.assertTrue(sc.validate_ltg_count(ltgs).ok)
        for g in ltgs:
            self.assertTrue(sc.validate_smart_goal(g).ok, (g, sc.validate_smart_goal(g).reasons))

        # STG 분해 — 각 LTG마다 4개씩
        stgs = [
            [
                "2026년 단행본 1권 초안 완성",
                "2026년 단행본 1권 출판",
                "2027년 단행본 2권 초안 60% 작성",
                "2027년 단행본 2권 출판",
            ],
            [
                "2026년 후배 목회자 10명에게 멘토링 시간 제공",
                "2026년 멘토링 커리큘럼 1차 작성",
                "2027년 후배 목회자 15명에게 멘토링 시간 제공",
                "2027년 멘토링 그룹 5개 운영",
            ],
            [
                "2026년 강의 20회 진행",
                "2027년 강의 25회 진행",
                "2026년 강의 슬라이드 30개 정비",
                "2027년 디지털 강의 플랫폼 1개 개설",
            ],
        ]
        self.assertTrue(sc.validate_stg_count(stgs).ok)
        self.assertTrue(sc.validate_quarter_focus([3, 3, 3, 2]).ok)

        # 첫 한 걸음
        first_step = "내일 아침 5시 30분, 서재에서, 단행본 1권 1장의 초고를 60분간 작성"
        self.assertTrue(sc.validate_first_step(first_step).ok)

        # Q08
        q08 = "I am good at trimming a giant dream into a first step I can take tomorrow morning"
        self.assertTrue(sc.verify_q08_canonical(q08).ok)

        # 점검 일정
        schedule = sc.calculate_review_schedule("2026-05-17", birthday="1968-08-15")
        for k in ("weekly", "monthly", "quarterly", "annual"):
            self.assertRegex(schedule[k], r"^\d{4}-\d{2}-\d{2}$")

        # 산출문 시뮬레이션 — 사용자 진술 외 인명·기관 없음, 학술 인용만.
        # user_input에는 비전 진술 + 분기 STG에서 사용자가 합의한 연도(2026·2027) +
        # 점검 일정의 연도가 모두 포함되어야 한다.
        user_input = (
            " ".join(ltgs)
            + " " + " ".join(s for group in stgs for s in group)
            + " 박사님 비전 미래학 단행본 멘토링 강의 디지털 플랫폼 디아스포라 후배 목회자 "
            + schedule["weekly"] + " " + schedule["monthly"]
        )
        coach_doc = (
            "박사님의 비전을 SMART(Doran 1981 Management Review)과 "
            "PDCA(Shewhart 1939, Deming 1950s) 사이클로 정리합니다. "
            f"LTG1: {ltgs[0]}. LTG2: {ltgs[1]}. LTG3: {ltgs[2]}. "
            f"첫 한 걸음: {first_step}. "
            "다음 점검 일정: 주간 " + schedule["weekly"] + ", 월간 " + schedule["monthly"] + "."
        )
        filt = sc.filter_unsourced_entities(coach_doc, user_input)
        self.assertTrue(filt["ok"], filt["violations"])

        # 호칭 일관성
        h = sc.validate_honorific_consistency(coach_doc, declared="박사님")
        self.assertTrue(h.ok, h.reasons)

        # Pivot 시나리오 (분기 진척률 50%)
        pivot = sc.check_pivot_trigger(50)
        self.assertEqual(pivot["status"], "pivot_required")


if __name__ == "__main__":
    unittest.main(verbosity=2)
