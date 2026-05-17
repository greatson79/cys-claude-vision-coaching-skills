"""10개 신규 검증 시나리오 — 이전 검증과 *완전히 다른* 도메인·경계 케이스."""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))

from lib import run, citations, date_engine  # noqa: E402


def _full_payload(**overrides):
    """채워진 기본 payload — 테스트별로 일부만 override."""
    base = {
        "today_iso": "2026-05-17",
        "user_text": "",
        "inspiration_quote": "기본 영감",
        "smart_goal": "2027-12-31까지 책 1권 출간",
        "smart_resources": "주 10시간 확보",
        "smart_vision_link": "비전 1차 결실",
        "backcasting": {
            "five_years": "5년 후 목표 placeholder",
            "one_year": "1년 후 목표 placeholder",
            "next_quarter": "분기 목표 placeholder",
            "one_week": "주간 마일스톤 placeholder",
            "tomorrow": "내일 30분 행동 placeholder",
        },
        "okr": {
            "objective": "1년 안에 첫 책 출간",
            "key_results": [
                "Q1 6장 초고 완성",
                "Q2 12장 초고 완성",
                "Q3 출판사 계약 체결",
            ],
            "okr_type": "aspirational",
        },
        "first_step": {
            "what": "검토", "when": "06:30",
            "where": "서재", "how": "노션", "why": "보강 식별",
        },
    }
    for k, v in overrides.items():
        base[k] = v
    return base


class TestTenNewScenarios(unittest.TestCase):

    # 시나리오 1 — 마라톤 풀코스 완주 (Q3 기준일, 1년 후 가을)
    def test_01_marathon_finish(self):
        p = _full_payload(
            today_iso="2026-09-12",
            user_text="3시간대 마라톤 풀코스 완주를 목표로 만들고 싶어",
            inspiration_quote="40대 중반에 내 몸을 새로 쓰는 삶, 풀코스 sub-4 완주",
            smart_goal="2027-10-31까지 풀코스 마라톤 sub-4 (4시간 이내) 완주",
            smart_resources="현재 10km 55분 페이스 보유, 주 4회 30km 훈련 가능",
            smart_vision_link="40대 몸 재건의 1차 결실",
            backcasting={
                "five_years": "5년 안에 100km 울트라 완주 + 후학 러닝 코칭 5명",
                "one_year": "풀코스 sub-4 완주 (2027 가을 대회)",
                "next_quarter": "하프 코스 sub-2 안정화 + 풀코스 첫 도전",
                "one_week": "주 4회 페이스 훈련 + 일요일 LSD 25km",
                "tomorrow": "오전 6시 10km 페이스 5:30 페이스로",
            },
            okr={
                "objective": "2027 가을 풀코스 마라톤 sub-4 완주",
                "key_results": [
                    "2027 Q1까지 하프 sub-2 안정화 (3회 완주)",
                    "2027 Q2까지 30km 페이스 6:00 안정 운영",
                    "2027 Q3까지 풀코스 1회 완주 (페이스 자유)",
                    "2027 Q4 sub-4 풀코스 완주 + 회복 4주 프로토콜 완료",
                ],
                "okr_type": "aspirational",
            },
            first_step={
                "what": "10km 페이스 5:30 훈련",
                "when": "06:00~07:00",
                "where": "한강 잠원지구",
                "how": "Garmin 시계 + 페이스 알림",
                "why": "주간 마일스톤 첫 페이스 훈련 시작",
            },
        )
        out = run.run(p)
        self.assertEqual(out["errors"], [], msg=out["errors"])
        # 1년 후 2027-09-12, Q3
        self.assertEqual(out["timeline"]["one_year"]["iso_date"], "2027-09-12")
        self.assertEqual(out["timeline"]["one_year"]["quarter"], "Q3")
        # 다음 분기 = 2026 Q4
        self.assertEqual(out["timeline"]["next_quarter"]["quarter"], "Q4")
        self.assertEqual(out["timeline"]["next_quarter"]["start_iso"], "2026-10-01")

    # 시나리오 2 — 유형 D (첫 한 걸음 단독)
    def test_02_first_step_only(self):
        p = {
            "today_iso": "2026-05-17",
            "user_text": "내일 아침 첫 한 걸음만 잡아주세요. 영어 단어 외우기 시작",
        }
        out = run.run(p)
        self.assertEqual(out["route"]["input_type"], "D")
        self.assertEqual(out["route"]["steps_to_run"], ["Step 5"])
        # 워크북 미조립 정상 — 필수 필드 누락
        self.assertIsNone(out["workbook_markdown"])

    # 시나리오 3 — 유형 C (OKR만)
    def test_03_okr_only(self):
        p = _full_payload(
            user_text="이미 LTG/STG 정해놓았으니 OKR만 만들어줘 — 스타트업 시드 투자 유치",
            has_ltg_stg=True,
            inspiration_quote="딥테크 스타트업 시드 유치하여 글로벌 진출",
            smart_goal="2027-06-30까지 시드 투자 30억 원 유치",
            smart_resources="MVP 완성, 3개 LOI 확보, 공동창업자 2인",
            smart_vision_link="딥테크 글로벌 진출의 1차 자금 확보",
            backcasting={
                "five_years": "Series B 마감 + 글로벌 진출 3개국",
                "one_year": "시드 30억 + MAU 10만",
                "next_quarter": "VC 5곳 IR + LOI 2건 확보",
                "one_week": "IR 자료 v3 완성",
                "tomorrow": "IR 자료 슬라이드 1~5 검토",
            },
            okr={
                "objective": "2027 H1까지 시드 30억 원 유치",
                "key_results": [
                    "2027 Q1 VC 5곳 IR 발표 진행",
                    "2027 Q2 LOI 2건 확보 + Term Sheet 1건",
                    "2027 Q2 30억 원 클로징 완료",
                ],
                "okr_type": "committed",
            },
        )
        out = run.run(p)
        self.assertEqual(out["route"]["input_type"], "C")
        self.assertEqual(out["okr"]["okr_type"], "committed")
        self.assertEqual(out["errors"], [])

    # 시나리오 4 — Time-bound 누락 FAIL
    def test_04_time_bound_fail(self):
        p = _full_payload(
            smart_goal="언젠가 작가가 되어 책을 쓰겠다",  # 기한 없음
        )
        out = run.run(p)
        self.assertFalse(out["smart"]["passed_all"])
        self.assertFalse(out["smart"]["axes"][4]["passed"])  # Time-bound
        self.assertIn("SMART 5축 중 일부 미통과 — 보완 필요", out["errors"])

    # 시나리오 5 — Backcasting 시점 누락 FAIL
    def test_05_backcasting_missing_horizon(self):
        p = _full_payload(
            backcasting={
                "one_year": "X 완성",
                "next_quarter": "Y 완성",
                "one_week": "Z 보강",
                "tomorrow": "W 30분",
                # five_years 누락
            }
        )
        out = run.run(p)
        self.assertFalse(out["backcasting"]["passed"])
        self.assertIn("5년 후 (LTG)", out["backcasting"]["missing"])

    # 시나리오 6 — OKR KR 개수 2개 FAIL
    def test_06_okr_too_few_krs(self):
        p = _full_payload(
            okr={
                "objective": "1년 안에 책 출간",
                "key_results": ["Q1 6장", "Q2 12장"],
                "okr_type": "aspirational",
            }
        )
        out = run.run(p)
        self.assertFalse(out["okr"]["passed"])
        self.assertTrue(any("최소 3개" in e for e in out["okr"]["errors"]))

    # 시나리오 7 — 유형 B (vision-clarity 산출물) Q4 기준일
    def test_07_clarity_output_q4_basis(self):
        p = _full_payload(
            today_iso="2026-10-15",
            user_text="vision-clarity-coaching 결과를 가지고 왔습니다",
            vision_clarity_output=True,
            inspiration_quote="청년부 30명을 다음 세대 리더로 양성하는 사역",
            smart_goal="2027-08-31까지 청년 리더 후보 10명 1년 멘토링 완주",
            smart_resources="청년부 50명, 격주 토요일 4시간 확보",
            smart_vision_link="다음 세대 리더 양성의 1차 결실",
            backcasting={
                "five_years": "리더 30명 양성 + 다음 세대 청년부 자립 운영",
                "one_year": "리더 후보 10명 1년 멘토링 완주",
                "next_quarter": "리더 후보 10명 선발 + 커리큘럼 12회기 확정",
                "one_week": "선발 공지문 작성 + 1차 모집",
                "tomorrow": "선발 공지 초안 30분 검토",
            },
            okr={
                "objective": "2027 여름까지 청년 리더 후보 10명 멘토링 완주",
                "key_results": [
                    "2026 Q4 10명 선발 + 커리큘럼 확정",
                    "2027 Q1 6회기 진행 + 중간 평가",
                    "2027 Q2 12회기 진행 + 리더 과제 산출물",
                    "2027 Q3 리더 인증식 + 차기 기수 모집 개시",
                ],
                "okr_type": "aspirational",
            },
        )
        out = run.run(p)
        self.assertEqual(out["route"]["input_type"], "B")
        # 다음 분기 = 2027 Q1
        self.assertEqual(out["timeline"]["next_quarter"]["quarter"], "Q1")
        self.assertEqual(out["timeline"]["next_quarter"]["year"], 2027)
        self.assertEqual(out["errors"], [])

    # 시나리오 8 — 윤년 2/29 경계
    def test_08_leap_year_feb29(self):
        p = _full_payload(today_iso="2024-02-29")
        out = run.run(p)
        self.assertEqual(out["timeline"]["five_years"]["iso_date"], "2029-02-28")
        self.assertEqual(out["timeline"]["one_year"]["iso_date"], "2025-02-28")
        self.assertEqual(out["timeline"]["next_quarter"]["quarter"], "Q2")

    # 시나리오 9 — Q4 11월 → 다음 분기 wrap Q1
    def test_09_q4_to_q1_wrap(self):
        p = _full_payload(today_iso="2026-11-30")
        out = run.run(p)
        self.assertEqual(out["timeline"]["today"]["quarter"], "Q4")
        self.assertEqual(out["timeline"]["next_quarter"]["year"], 2027)
        self.assertEqual(out["timeline"]["next_quarter"]["quarter"], "Q1")
        self.assertEqual(out["timeline"]["next_quarter"]["start_iso"], "2027-01-01")
        self.assertEqual(out["timeline"]["next_quarter"]["end_iso"], "2027-03-31")

    # 시나리오 10 — 영어 SMART 입력 + 모든 인용 키 포함 검증
    def test_10_english_smart_and_full_workbook(self):
        p = _full_payload(
            user_text="Help me reframe my dream of writing a children's book series into a measurable plan",
            inspiration_quote="A 5-book children's series about kindness for grades 1-3",
            smart_goal="By 2027-12-31, publish 2 children's books (Book 1 + Book 2)",
            smart_resources="Outline ready, 3 editor contacts, 2 hours/day writing time",
            smart_vision_link="First milestone of the 5-book kindness series",
            backcasting={
                "five_years": "5-book series complete + school visits 50 times",
                "one_year": "Book 1 + Book 2 published",
                "next_quarter": "Book 1 manuscript final draft + 3 editor pitches",
                "one_week": "Chapter 1-3 polish + 5 editor list research",
                "tomorrow": "30 min review of chapter 1 manuscript",
            },
            okr={
                "objective": "Publish 2 children's books in 2027",
                "key_results": [
                    "Q1 2027: Book 1 final manuscript 100 pages",
                    "Q2 2027: Book 1 published with publisher contract",
                    "Q3 2027: Book 2 manuscript 60 pages complete",
                    "Q4 2027: Book 2 published + 5 school readings",
                ],
                "okr_type": "aspirational",
            },
        )
        out = run.run(p)
        self.assertEqual(out["errors"], [])
        # 코어 인용 6개 모두 등장
        for key in citations.CORE_REFERENCES:
            self.assertIn(key, out["workbook_markdown"], f"Missing citation key: {key}")
        # 채점 척도 명시
        self.assertIn("0.7", out["workbook_markdown"])
        self.assertIn("aspirational", out["workbook_markdown"])
        # 결정론 날짜 정확
        self.assertIn("2026-05-18", out["workbook_markdown"])  # 내일 = 월요일
        self.assertIn("2031-05-17", out["workbook_markdown"])  # 5년 후


if __name__ == "__main__":
    unittest.main(verbosity=2)
