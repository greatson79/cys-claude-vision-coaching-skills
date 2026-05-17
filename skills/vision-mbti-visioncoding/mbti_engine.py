#!/usr/bin/env python3
"""
vision-mbti-visioncoding 결정론 엔진.

LLM이 자연어로 추론하면 할루시네이션 위험이 있는 단계들을 결정론적 파이썬 함수로 환원.

환원된 단계:
  1) 20문항 카탈로그 — fixed data (각 축 5문항)
  2) 이항(A/B) 응답 채점
  3) 5점 척도(1~5) 응답 채점
  4) 4축 점수 → 16유형 결정
  5) 중립 판정 (5점 총점 = 15)
  6) 경계 유형 판정 (선호 강도)
  7) 인지 기능 스택 매핑 (Dom-Aux-Tert-Inf, Myers 표준)
  8) Grip state 열등기능 매핑 (Quenk 표준)
  9) 인구 비율 (MBTI Manual 3rd ed. CPP National Sample 1996, N=3009)
  10) 유형 별명 (16personalities.com NERIS / Keirsey 1998 두 가지 출처 병기)
  11) 입력 검증 (4글자 유형, 응답 개수, 척도 범위)
  12) 1차 사실 조회 — 핵심 정의·축 의미

핵심 학계 출처 (verified) — 상세 메타데이터는 모듈 하단 REFERENCES 참조.

라이선스 주의:
  - "16personalities.com" 별명(Architect, Logician 등)은 NERIS Analytics Ltd.의 상표 라벨이며
    Myers의 공식 명칭이 아님. 사용자 친숙도 때문에 1차 라벨로 사용하되,
    Keirsey 명명·인지기능 약어를 학계 출처와 함께 병기한다.
"""

from __future__ import annotations

import json
import sys
from typing import Dict, List, Optional, Tuple


# ============================================================
# (A0) 학술 출처 메타데이터 — 결정론적 reference. LLM 자작 금지.
# ============================================================
# 각 항목은 *외부 학자가 검증 가능한* 서지 정보로 구성.
# DOI·ISBN은 100% 검증 불가능한 경우 생략하고 출판 정보만 기재.
# verbatim 인용은 *공개 abstract* 또는 *공식 카탈로그*에서 확인 가능한 문구만 사용.

REFERENCES = {
    "myers_1980_gifts_differing": {
        "key": "Myers 1980",
        "authors": "Isabel Briggs Myers (with Peter B. Myers)",
        "year": 1980,
        "title": "Gifts Differing: Understanding Personality Type",
        "publisher": "Consulting Psychologists Press (CPP)",
        "place": "Mountain View, CA",
        "notes": ("4축·16유형·Dominant/Auxiliary/Tertiary/Inferior 인지기능 스택의 표준 정립. "
                  "1995년 reprint은 Davies-Black Publishing에서 발행."),
        "used_for": ["cognitive_stack", "type_definitions", "interpersonal_dynamics"],
    },
    "mbti_manual_1998_3rd": {
        "key": "MBTI Manual 3rd ed.",
        "authors": "Isabel Briggs Myers, Mary H. McCaulley, Naomi L. Quenk, Allen L. Hammer",
        "year": 1998,
        "title": ("MBTI Manual: A Guide to the Development and Use of "
                  "the Myers-Briggs Type Indicator (3rd ed.)"),
        "publisher": "Consulting Psychologists Press (CPP)",
        "place": "Palo Alto, CA",
        "table_cited": "Table 7.6, Sample 1 (CPP National Sample 1996, N=3009)",
        "notes": ("16유형 인구 비율의 학계 표준 출처. "
                  "Sample 1은 1996년 CPP가 미국 일반 인구 대표 표본으로 수집한 N=3009 데이터."),
        "used_for": ["population_pct"],
    },
    "quenk_2002_grip": {
        "key": "Quenk 2002",
        "authors": "Naomi L. Quenk",
        "year": 2002,
        "title": ("Was That Really Me? How Everyday Stress "
                  "Brings Out Our Hidden Personality"),
        "publisher": "Davies-Black Publishing (CPP 계열)",
        "place": "Palo Alto, CA",
        "notes": ("열등기능(Inferior function) 분출 현상 'in the grip'의 표준 임상 묘사. "
                  "16유형 각각의 grip state 행동 패턴을 체계화."),
        "used_for": ["inferior_grip"],
    },
    "beebe_2017_8function": {
        "key": "Beebe 2017",
        "authors": "John Beebe",
        "year": 2017,
        "title": ("Energies and Patterns in Psychological Type: "
                  "The reservoir of consciousness"),
        "publisher": "Routledge",
        "series": "Routledge Mental Health Classic Editions",
        "notes": ("8-function 모델 (Dom/Aux/Tert/Inf + Opposing/Senex/Trickster/Demon) "
                  "분석심리학적 정교화."),
        "used_for": ["function_archetypes"],
    },
    "jung_1921_psychological_types": {
        "key": "Jung 1921",
        "authors": "Carl Gustav Jung",
        "original_year": 1921,
        "title_original_de": ("Psychologische Typen "
                              "(Gesammelte Werke Band 6, 1921, Rascher Verlag, Zürich)"),
        "english_translation": ("Psychological Types, trans. R. F. C. Hull "
                                "(revision of H. G. Baynes 1923 translation), "
                                "Bollingen Series XX Vol. 6, "
                                "Princeton University Press 1971"),
        "notes": ("외향/내향, 4기능(사고·감정·감각·직관)의 원형 — Briggs·Myers MBTI 모델의 토대."),
        "used_for": ["axis_definitions_EI_SN_TF", "individuation_concept"],
    },
    "keirsey_1998_pumii": {
        "key": "Keirsey 1998",
        "authors": "David Keirsey",
        "year": 1998,
        "title": "Please Understand Me II: Temperament, Character, Intelligence",
        "publisher": "Prometheus Nemesis Book Company",
        "place": "Del Mar, CA",
        "notes": ("4기질 분류(NF Idealist·NT Rational·SJ Guardian·SP Artisan) "
                  "+ 16유형 Keirsey 명명 (Mastermind, Fieldmarshal, Counselor 등)의 정본."),
        "used_for": ["keirsey_label", "keirsey_temperament"],
    },
    "pittenger_1993": {
        "key": "Pittenger 1993",
        "authors": "David J. Pittenger",
        "year": 1993,
        "title": "Measuring the MBTI ... And Coming Up Short",
        "journal": "Journal of Career Planning and Employment",
        "volume_issue_pages": "54(1), 48–52",
        "notes": ("MBTI 재검사 신뢰도 비판의 대표 문헌. "
                  "5주 후 재검사 시 응답자 약 50%에서 유형 변화 보고."),
        "used_for": ["retest_reliability_critique"],
    },
    "pittenger_2005": {
        "key": "Pittenger 2005",
        "authors": "David J. Pittenger",
        "year": 2005,
        "title": "Cautionary Comments Regarding the Myers-Briggs Type Indicator",
        "journal": "Consulting Psychology Journal: Practice and Research",
        "volume_issue_pages": "57(3), 210–221",
        "doi": "10.1037/1065-9293.57.3.210",
        "publisher": "American Psychological Association (APA)",
        "notes": ("MBTI의 심리측정학적 약점·4축 이분법 비판 종합. "
                  "Educational and Industrial Testing Service·APA 등의 공개 비판 종합."),
        "used_for": ["psychometric_critique", "dichotomy_critique"],
    },
    "neris_16personalities": {
        "key": "NERIS / 16personalities",
        "authors": "NERIS Analytics Ltd.",
        "year_first_published": 2013,
        "url": "https://www.16personalities.com",
        "notes": ("Architect·Logician·Commander·Debater·Advocate·Mediator·Protagonist·"
                  "Campaigner·Logistician·Defender·Executive·Consul·Virtuoso·Adventurer·"
                  "Entrepreneur·Entertainer 등 16유형 별명은 NERIS Analytics Ltd.의 "
                  "등록 상표 라벨. Myers의 공식 명칭이 아님. "
                  "또한 NERIS 모델은 5번째 축(A/T, Assertive/Turbulent)을 추가한 변형 모델로, "
                  "원래 MBTI 모델과 다름. 사용자 친숙도 이유로 1차 라벨로 사용하되 "
                  "Keirsey 명명을 병기."),
        "used_for": ["neris_label"],
    },
}


def get_references_for(keys):
    """주어진 reference key 목록의 메타데이터를 반환."""
    return {k: REFERENCES[k] for k in keys if k in REFERENCES}


# ============================================================
# (A) 16유형 정의 — 라벨·인구비율·인지기능 스택·grip state
# ============================================================

# 16유형 별명·기능 데이터.
# 각 항목: {
#   "neris": 16personalities.com NERIS 라벨 (인기 라벨),
#   "neris_ko": 한국어 번역,
#   "keirsey": Keirsey (Please Understand Me II, 1998) 라벨,
#   "keirsey_temperament": Keirsey 4기질 (NF/NT/SJ/SP) 그룹명,
#   "stack": (Dominant, Auxiliary, Tertiary, Inferior) — Myers Gifts Differing (1980),
#   "inferior_grip": Quenk (Was That Really Me, 2002) 묘사,
#   "population_pct": Myers et al. MBTI Manual 3rd ed. (1998) Table 7.6 Sample 1
# }

TYPE_DATA: Dict[str, Dict] = {
    # 분석가 그룹 (NT)
    "INTJ": {
        "neris": "Architect",
        "neris_ko": "건축가",
        "keirsey": "Mastermind",
        "keirsey_temperament": "NT (Rational)",
        "stack": ("Ni", "Te", "Fi", "Se"),
        "inferior_grip": "Se grip — 스트레스 시 감각적 과식·충동적 행동·외부 세부 사항에 집착 (Quenk 2002)",
        "population_pct": 2.1,
        "group": "분석가 NT",
    },
    "INTP": {
        "neris": "Logician",
        "neris_ko": "논리술사",
        "keirsey": "Architect",
        "keirsey_temperament": "NT (Rational)",
        "stack": ("Ti", "Ne", "Si", "Fe"),
        "inferior_grip": "Fe grip — 스트레스 시 비논리적 감정 폭발·관계 집착·타인 의존 급증 (Quenk 2002)",
        "population_pct": 3.3,
        "group": "분석가 NT",
    },
    "ENTJ": {
        "neris": "Commander",
        "neris_ko": "통솔자",
        "keirsey": "Fieldmarshal",
        "keirsey_temperament": "NT (Rational)",
        "stack": ("Te", "Ni", "Se", "Fi"),
        "inferior_grip": "Fi grip — 스트레스 시 폭발적 분노·억눌린 감정 분출·자기 의심 (Quenk 2002)",
        "population_pct": 1.8,
        "group": "분석가 NT",
    },
    "ENTP": {
        "neris": "Debater",
        "neris_ko": "변론가",
        "keirsey": "Inventor",
        "keirsey_temperament": "NT (Rational)",
        "stack": ("Ne", "Ti", "Fe", "Si"),
        "inferior_grip": "Si grip — 스트레스 시 과거 집착·건강 염려·경직된 루틴 집착 (Quenk 2002)",
        "population_pct": 3.2,
        "group": "분석가 NT",
    },
    # 외교관 그룹 (NF)
    "INFJ": {
        "neris": "Advocate",
        "neris_ko": "옹호자",
        "keirsey": "Counselor",
        "keirsey_temperament": "NF (Idealist)",
        "stack": ("Ni", "Fe", "Ti", "Se"),
        "inferior_grip": "Se grip — 스트레스 시 폭식·강박적 외부 행동·신체 감각 과민 (Quenk 2002)",
        "population_pct": 1.5,
        "group": "외교관 NF",
    },
    "INFP": {
        "neris": "Mediator",
        "neris_ko": "중재자",
        "keirsey": "Healer",
        "keirsey_temperament": "NF (Idealist)",
        "stack": ("Fi", "Ne", "Si", "Te"),
        "inferior_grip": "Te grip — 스트레스 시 비판적 공격·통제 시도·논리적 단정 (Quenk 2002)",
        "population_pct": 4.4,
        "group": "외교관 NF",
    },
    "ENFJ": {
        "neris": "Protagonist",
        "neris_ko": "선도자",
        "keirsey": "Teacher",
        "keirsey_temperament": "NF (Idealist)",
        "stack": ("Fe", "Ni", "Se", "Ti"),
        "inferior_grip": "Ti grip — 스트레스 시 냉혹한 내적 비판·논리적 공격·정서적 고립 (Quenk 2002)",
        "population_pct": 2.5,
        "group": "외교관 NF",
    },
    "ENFP": {
        "neris": "Campaigner",
        "neris_ko": "활동가",
        "keirsey": "Champion",
        "keirsey_temperament": "NF (Idealist)",
        "stack": ("Ne", "Fi", "Te", "Si"),
        "inferior_grip": "Si grip — 스트레스 시 과거 집착·건강 염려·세부 사항 집착 (Quenk 2002)",
        "population_pct": 8.1,
        "group": "외교관 NF",
    },
    # 관리자 그룹 (SJ)
    "ISTJ": {
        "neris": "Logistician",
        "neris_ko": "청렴결백 논리주의자",
        "keirsey": "Inspector",
        "keirsey_temperament": "SJ (Guardian)",
        "stack": ("Si", "Te", "Fi", "Ne"),
        "inferior_grip": "Ne grip — 스트레스 시 비관적 가능성 집착·미래 재앙 상상·공격성 (Quenk 2002)",
        "population_pct": 11.6,
        "group": "관리자 SJ",
    },
    "ISFJ": {
        "neris": "Defender",
        "neris_ko": "수호자",
        "keirsey": "Protector",
        "keirsey_temperament": "SJ (Guardian)",
        "stack": ("Si", "Fe", "Ti", "Ne"),
        "inferior_grip": "Ne grip — 스트레스 시 부정적 가능성 집착·과민·미래 두려움 (Quenk 2002)",
        "population_pct": 13.8,
        "group": "관리자 SJ",
    },
    "ESTJ": {
        "neris": "Executive",
        "neris_ko": "경영자",
        "keirsey": "Supervisor",
        "keirsey_temperament": "SJ (Guardian)",
        "stack": ("Te", "Si", "Ne", "Fi"),
        "inferior_grip": "Fi grip — 스트레스 시 감정 폭발·자기 의심·억눌린 가치 분출 (Quenk 2002)",
        "population_pct": 8.7,
        "group": "관리자 SJ",
    },
    "ESFJ": {
        "neris": "Consul",
        "neris_ko": "집정관",
        "keirsey": "Provider",
        "keirsey_temperament": "SJ (Guardian)",
        "stack": ("Fe", "Si", "Ne", "Ti"),
        "inferior_grip": "Ti grip — 스트레스 시 논리적 공격·냉정한 비판·고립 (Quenk 2002)",
        "population_pct": 12.3,
        "group": "관리자 SJ",
    },
    # 탐험가 그룹 (SP)
    "ISTP": {
        "neris": "Virtuoso",
        "neris_ko": "만능재주꾼",
        "keirsey": "Crafter",
        "keirsey_temperament": "SP (Artisan)",
        "stack": ("Ti", "Se", "Ni", "Fe"),
        "inferior_grip": "Fe grip — 스트레스 시 감정 폭발·관계 집착·과민 (Quenk 2002)",
        "population_pct": 5.4,
        "group": "탐험가 SP",
    },
    "ISFP": {
        "neris": "Adventurer",
        "neris_ko": "모험가",
        "keirsey": "Composer",
        "keirsey_temperament": "SP (Artisan)",
        "stack": ("Fi", "Se", "Ni", "Te"),
        "inferior_grip": "Te grip — 스트레스 시 비판적 분석·통제 시도·단정적 판단 (Quenk 2002)",
        "population_pct": 8.8,
        "group": "탐험가 SP",
    },
    "ESTP": {
        "neris": "Entrepreneur",
        "neris_ko": "사업가",
        "keirsey": "Promoter",
        "keirsey_temperament": "SP (Artisan)",
        "stack": ("Se", "Ti", "Fe", "Ni"),
        "inferior_grip": "Ni grip — 스트레스 시 강박적 미래 분석·고립·부정적 비전 집착 (Quenk 2002)",
        "population_pct": 4.3,
        "group": "탐험가 SP",
    },
    "ESFP": {
        "neris": "Entertainer",
        "neris_ko": "연예인",
        "keirsey": "Performer",
        "keirsey_temperament": "SP (Artisan)",
        "stack": ("Se", "Fi", "Te", "Ni"),
        "inferior_grip": "Ni grip — 스트레스 시 어두운 미래 상상·고립·압도감 (Quenk 2002)",
        "population_pct": 8.5,
        "group": "탐험가 SP",
    },
}

ALL_TYPES = sorted(TYPE_DATA.keys())  # 16개 ABC 정렬

# ============================================================
# (B) 4축 정의 (Jung 1921 / Myers 1980 표준)
# ============================================================

AXES = ["EI", "SN", "TF", "JP"]

AXIS_DEFINITION = {
    "EI": {
        "label_ko": "에너지 방향",
        "a_letter": "E",
        "b_letter": "I",
        "a_ko": "외향 (Extraversion)",
        "b_ko": "내향 (Introversion)",
        "a_desc": "외부 세계·사람·활동에서 에너지 충전",
        "b_desc": "내면 세계·성찰·소수와의 깊은 교류에서 에너지 충전",
        "source": "Jung 1921 §VI; Myers 1980 ch.1",
    },
    "SN": {
        "label_ko": "정보 수집",
        "a_letter": "S",
        "b_letter": "N",
        "a_ko": "감각 (Sensing)",
        "b_ko": "직관 (iNtuition)",
        "a_desc": "오감·구체·실제·현재·검증된 사실 우선",
        "b_desc": "패턴·연결·가능성·미래·아이디어 우선",
        "source": "Jung 1921 §VII–VIII; Myers 1980 ch.2",
    },
    "TF": {
        "label_ko": "의사결정",
        "a_letter": "T",
        "b_letter": "F",
        "a_ko": "사고 (Thinking)",
        "b_ko": "감정 (Feeling)",
        "a_desc": "논리·일관성·객관적 진실·시스템 우선",
        "b_desc": "가치·조화·사람·관계·맥락 우선",
        "source": "Jung 1921 §IX–X; Myers 1980 ch.3",
    },
    "JP": {
        "label_ko": "생활 양식 (외부세계 대처)",
        "a_letter": "J",
        "b_letter": "P",
        "a_ko": "판단 (Judging)",
        "b_ko": "인식 (Perceiving)",
        "a_desc": "계획·결정·완결·구조 선호",
        "b_desc": "유연·개방·즉흥·과정 선호",
        "source": "Myers 1980 ch.4 (Jung에서 명시되지 않은 Myers의 추가 축)",
    },
}

# ============================================================
# (C) 20문항 카탈로그 (각 축 5문항) — SKILL.md와 1:1 동기화
# ============================================================
# Q01–Q05: EI / Q06–Q10: SN / Q11–Q15: TF / Q16–Q20: JP
# 각 문항: (축, A 선택지 텍스트, B 선택지 텍스트)
# A 선택지가 축의 a_letter(E/S/T/J) 쪽, B가 b_letter(I/N/F/P) 쪽으로 *반드시* 일관

QUESTIONS: Dict[str, Tuple[str, str, str]] = {
    "Q01": ("EI", "새로운 사람들과 대화하면 에너지가 충전된다.",
            "새로운 사람들과 대화하면 에너지가 소진되어 혼자만의 시간이 필요하다."),
    "Q02": ("EI", "휴식·재충전을 위해 친구들과 만나는 것을 선호한다.",
            "휴식·재충전을 위해 혼자 시간을 보내는 것을 선호한다."),
    "Q03": ("EI", "큰 모임에서 여러 사람과 짧고 폭넓게 어울리는 편이다.",
            "큰 모임에서 한두 명과 깊고 길게 대화하는 편이다."),
    "Q04": ("EI", "생각을 정리할 때 말하면서 또는 대화하면서 정리된다.",
            "생각을 정리할 때 침묵 속에서 혼자 정리한다."),
    "Q05": ("EI", "새 환경·낯선 자리에 가면 즉시 다가가 사람들과 어울린다.",
            "새 환경·낯선 자리에 가면 한발 물러서 먼저 관찰한다."),
    "Q06": ("SN", "정보를 받을 때 구체적·실제적·검증된 내용을 선호한다.",
            "정보를 받을 때 연결·가능성·아이디어를 선호한다."),
    "Q07": ("SN", "책·콘텐츠를 고를 때 실용·사실·역사에 끌린다.",
            "책·콘텐츠를 고를 때 상상·미래·은유·이론에 끌린다."),
    "Q08": ("SN", "사람을 평가할 때 그가 실제로 한 행동과 결과를 본다.",
            "사람을 평가할 때 그의 잠재력·동기·내면을 본다."),
    "Q09": ("SN", "문제 해결 시 검증된 방법·과거 성공 사례를 적용한다.",
            "문제 해결 시 새로운 접근·아직 시도되지 않은 방법에 끌린다."),
    "Q10": ("SN", "과거를 회상할 때 일어난 사건·구체적 장면이 먼저 떠오른다.",
            "과거를 회상할 때 그때의 느낌·의미·해석이 먼저 떠오른다."),
    "Q11": ("TF", "결정을 내릴 때 논리·일관성·객관적 옳음이 가장 중요하다.",
            "결정을 내릴 때 사람·조화·맥락의 가치가 가장 중요하다."),
    "Q12": ("TF", "비판을 받을 때 내용 자체에 집중한다 (관계는 별개).",
            "비판을 받을 때 관계가 흔들렸는지가 먼저 신경 쓰인다."),
    "Q13": ("TF", "갈등 상황에서 옳고 그름의 판단이 먼저 정리되어야 한다고 본다.",
            "갈등 상황에서 모두의 감정과 입장 이해가 먼저 정리되어야 한다고 본다."),
    "Q14": ("TF", "영화·드라마를 평가할 때 줄거리·논리·구성을 본다.",
            "영화·드라마를 평가할 때 등장인물의 감정·관계를 본다."),
    "Q15": ("TF", "힘들어하는 친구에게 문제를 분석하고 해결책을 제시하는 편이다.",
            "힘들어하는 친구에게 공감하고 경청·정서적 지지를 먼저 하는 편이다."),
    "Q16": ("JP", "여행은 미리 계획된 일정대로 가는 것이 좋다.",
            "여행은 그때그때 즉흥적으로 가는 것이 좋다."),
    "Q17": ("JP", "마감이 있는 일을 일찍 끝내는 편이다.",
            "마감이 있는 일을 마지막 순간에 몰아서 하는 편이다."),
    "Q18": ("JP", "책상·작업 공간이 정돈되어 있어야 마음이 편하다.",
            "책상·작업 공간이 작업 중심으로 어수선해도 신경 쓰지 않는다."),
    "Q19": ("JP", "결정을 빨리 내려 닫고 다음으로 넘어가는 것을 선호한다.",
            "결정을 가능한 한 오래 열어두고 정보를 더 모으는 것을 선호한다."),
    "Q20": ("JP", "일주일을 미리 짠 일정대로 보내는 것이 효율적이다.",
            "일주일을 그때그때 정하면서 보내는 것이 효율적이다."),
}

# 축별 문항 ID 그룹 (사전 사후 일관성 검증용)
AXIS_QIDS: Dict[str, List[str]] = {
    "EI": [f"Q{n:02d}" for n in range(1, 6)],
    "SN": [f"Q{n:02d}" for n in range(6, 11)],
    "TF": [f"Q{n:02d}" for n in range(11, 16)],
    "JP": [f"Q{n:02d}" for n in range(16, 21)],
}


# ============================================================
# (D) 입력 검증
# ============================================================

def is_valid_type(t: str) -> bool:
    """16유형 화이트리스트 검증."""
    return isinstance(t, str) and t.upper() in TYPE_DATA


def validate_type(t: str) -> str:
    """4글자 유형 정규화. 실패 시 ValueError."""
    if not isinstance(t, str):
        raise ValueError(f"유형은 문자열이어야 함 (입력: {t!r})")
    norm = t.strip().upper()
    if norm not in TYPE_DATA:
        raise ValueError(f"유효한 16유형이 아님 (입력: {t!r}). "
                         f"가능: {', '.join(ALL_TYPES)}")
    return norm


def validate_binary_answers(answers: Dict[str, str]) -> List[str]:
    """
    이항(A/B) 응답 검증.
    반환: 오류 메시지 목록 (빈 리스트면 통과)
    """
    errors = []
    for qid in [f"Q{n:02d}" for n in range(1, 21)]:
        if qid not in answers:
            errors.append(f"누락된 응답: {qid}")
            continue
        v = answers[qid]
        if not isinstance(v, str) or v.upper() not in ("A", "B"):
            errors.append(f"{qid}: 이항 응답은 'A' 또는 'B'여야 함 (입력: {v!r})")
    return errors


def validate_scale_answers(answers: Dict[str, int]) -> List[str]:
    """
    5점 척도 응답 검증 (1~5 정수).
    """
    errors = []
    for qid in [f"Q{n:02d}" for n in range(1, 21)]:
        if qid not in answers:
            errors.append(f"누락된 응답: {qid}")
            continue
        v = answers[qid]
        if not isinstance(v, int) or v < 1 or v > 5:
            errors.append(f"{qid}: 5점 척도 응답은 1~5 정수여야 함 (입력: {v!r})")
    return errors


def validate_b1_counts(counts: Dict[str, Dict[str, int]]) -> List[str]:
    """
    형식 B-1 검증: 축별 (a, b) 카운트 합이 5인지.
    counts 예: {"EI": {"E": 4, "I": 1}, ...}
    """
    errors = []
    for axis in AXES:
        if axis not in counts:
            errors.append(f"누락된 축: {axis}")
            continue
        d = AXIS_DEFINITION[axis]
        a, b = d["a_letter"], d["b_letter"]
        c = counts[axis]
        if a not in c or b not in c:
            errors.append(f"{axis}: '{a}'와 '{b}' 키가 모두 필요 (입력: {c})")
            continue
        if c[a] + c[b] != 5:
            errors.append(f"{axis}: {a}={c[a]} + {b}={c[b]} = {c[a]+c[b]} (5여야 함)")
        if any(not isinstance(v, int) or v < 0 for v in (c[a], c[b])):
            errors.append(f"{axis}: 카운트는 0 이상의 정수여야 함 (입력: {c})")
    return errors


def validate_b2_totals(totals: Dict[str, int]) -> List[str]:
    """
    형식 B-2 검증: 축별 5점 척도 총점이 5~25 범위인지.
    totals 예: {"EI": 7, "SN": 18, "TF": 8, "JP": 22}
    """
    errors = []
    for axis in AXES:
        if axis not in totals:
            errors.append(f"누락된 축: {axis}")
            continue
        v = totals[axis]
        if not isinstance(v, int) or v < 5 or v > 25:
            errors.append(f"{axis}: 5점 척도 5문항 총점은 5~25 범위여야 함 (입력: {v})")
    return errors


# ============================================================
# (E) 채점 함수
# ============================================================

def score_axis_binary(axis: str, answers: Dict[str, str]) -> Dict:
    """
    이항 응답을 축 단위로 채점.
    반환: {
        "axis": "EI", "a_count": int, "b_count": int,
        "preference": "E"|"I"|None(=경계),
        "difference": int (절댓값),
        "strength": "강한"|"보통"|"약한"
    }
    """
    qids = AXIS_QIDS[axis]
    a_letter = AXIS_DEFINITION[axis]["a_letter"]
    b_letter = AXIS_DEFINITION[axis]["b_letter"]
    a_count = sum(1 for q in qids if answers[q].upper() == "A")
    b_count = sum(1 for q in qids if answers[q].upper() == "B")
    diff = abs(a_count - b_count)
    # 이항 5문항 → 가능한 diff: 1, 3, 5
    if diff == 5:
        strength = "강한"
    elif diff == 3:
        strength = "보통"
    elif diff == 1:
        strength = "약한 (경계)"
    else:
        strength = "이론상 불가능"  # 5문항 이항에서 diff=0/2/4 불가능
    if a_count > b_count:
        pref = a_letter
    elif b_count > a_count:
        pref = b_letter
    else:
        pref = None  # 5문항 이항은 동점 불가능, 방어용
    return {
        "axis": axis,
        "a_letter": a_letter,
        "b_letter": b_letter,
        "a_count": a_count,
        "b_count": b_count,
        "preference": pref,
        "difference": diff,
        "strength": strength,
        "border": (diff == 1),
        "mode": "binary",
    }


def score_axis_scale(axis: str, answers: Dict[str, int]) -> Dict:
    """
    5점 척도(1~5) 응답을 축 단위로 채점.
    축 5문항 총점 = 5~25.
    SKILL.md 명세: 5~14 → A 쪽 / 15 → 중립 / 16~25 → B 쪽.
    선호 강도: 차이 = |총점 − 15| (0~10).
    """
    qids = AXIS_QIDS[axis]
    total = sum(answers[q] for q in qids)
    return _score_axis_scale_from_total(axis, total)


def _score_axis_scale_from_total(axis: str, total: int) -> Dict:
    a_letter = AXIS_DEFINITION[axis]["a_letter"]
    b_letter = AXIS_DEFINITION[axis]["b_letter"]
    diff = abs(total - 15)
    if total < 15:
        pref = a_letter
    elif total > 15:
        pref = b_letter
    else:
        pref = None  # 중립
    if pref is None:
        strength = "중립 (재검토 필요)"
    elif diff >= 7:
        strength = "강한"
    elif diff >= 4:
        strength = "보통"
    elif diff >= 1:
        strength = "약한 (경계)"
    else:
        strength = "이론상 불가능"
    return {
        "axis": axis,
        "a_letter": a_letter,
        "b_letter": b_letter,
        "total": total,
        "preference": pref,
        "difference": diff,
        "strength": strength,
        "border": (pref is not None and diff <= 3),
        "neutral": (pref is None),
        "mode": "scale",
    }


def score_axis_b1(axis: str, count: Dict[str, int]) -> Dict:
    """
    형식 B-1 (각 축 A·B 카운트만 입력) 채점.
    이항과 동일한 차이 계산.
    """
    a_letter = AXIS_DEFINITION[axis]["a_letter"]
    b_letter = AXIS_DEFINITION[axis]["b_letter"]
    a_count = count[a_letter]
    b_count = count[b_letter]
    diff = abs(a_count - b_count)
    if diff == 5:
        strength = "강한"
    elif diff == 3:
        strength = "보통"
    elif diff == 1:
        strength = "약한 (경계)"
    elif diff == 0:
        strength = "중립 (재검토 필요)"
    else:
        strength = "비정상"
    if a_count > b_count:
        pref = a_letter
    elif b_count > a_count:
        pref = b_letter
    else:
        pref = None
    return {
        "axis": axis,
        "a_letter": a_letter,
        "b_letter": b_letter,
        "a_count": a_count,
        "b_count": b_count,
        "preference": pref,
        "difference": diff,
        "strength": strength,
        "border": (pref is not None and diff == 1),
        "neutral": (pref is None),
        "mode": "b1",
    }


def score_axis_b2(axis: str, total: int) -> Dict:
    """형식 B-2 (각 축 총점만 입력) 채점."""
    res = _score_axis_scale_from_total(axis, total)
    res["mode"] = "b2"
    return res


# ============================================================
# (F) 16유형 조립·경계 처리
# ============================================================

def assemble_type(axis_results: Dict[str, Dict]) -> Dict:
    """
    4축 채점 결과 → 16유형 결정 + 경계 분석.
    axis_results: {"EI": {...}, "SN": {...}, "TF": {...}, "JP": {...}}
    """
    letters = []
    border_axes = []
    neutral_axes = []
    for axis in AXES:
        r = axis_results[axis]
        if r.get("neutral"):
            neutral_axes.append(axis)
            letters.append("?")  # 중립 표시
        else:
            letters.append(r["preference"])
            if r.get("border"):
                border_axes.append(axis)
    primary = "".join(letters)

    # 가능한 유형 후보 (중립 축 = 양쪽 모두 가능)
    candidates = generate_candidates(axis_results)

    result = {
        "primary_string": primary,
        "is_complete": all(r.get("preference") for r in axis_results.values()),
        "border_axes": border_axes,
        "neutral_axes": neutral_axes,
        "axis_results": axis_results,
        "candidate_types": candidates,
    }
    if result["is_complete"]:
        # 유형 화이트리스트 검증
        result["primary_type"] = validate_type(primary)
        result["primary_data"] = TYPE_DATA[result["primary_type"]]
        # 경계 유형 처리
        if len(border_axes) == 0:
            result["boundary_warning"] = None
        elif len(border_axes) == 1:
            result["boundary_warning"] = (
                f"{border_axes[0]}축이 경계 영역(약한 선호). "
                f"두 유형 모두 가능성으로 두고 비교를 권합니다."
            )
        else:
            result["boundary_warning"] = (
                f"{len(border_axes)}개 축({', '.join(border_axes)})이 경계 영역. "
                f"공식 MBTI 검사(Form M 등) 권장."
            )
    else:
        result["primary_type"] = None
        result["primary_data"] = None
        result["boundary_warning"] = (
            f"중립 축 {len(neutral_axes)}개({', '.join(neutral_axes)}) — "
            f"재검토 또는 두 유형 비교 제시 필요."
        )
    return result


def generate_candidates(axis_results: Dict[str, Dict]) -> List[str]:
    """
    중립 축에서 양쪽 후보를 모두 펼쳐 가능한 16유형 후보 목록 생성.
    경계 축은 1차 후보 + 대안 후보를 함께 제시.
    """
    options = []
    for axis in AXES:
        r = axis_results[axis]
        if r.get("neutral"):
            options.append([r["a_letter"], r["b_letter"]])
        else:
            opts = [r["preference"]]
            if r.get("border"):
                # 약한 선호 → 반대편도 후보로 포함
                other = r["b_letter"] if r["preference"] == r["a_letter"] else r["a_letter"]
                opts.append(other)
            options.append(opts)
    # cartesian product
    result = []

    def recurse(idx: int, current: List[str]):
        if idx == 4:
            t = "".join(current)
            if t in TYPE_DATA and t not in result:
                result.append(t)
            return
        for letter in options[idx]:
            recurse(idx + 1, current + [letter])

    recurse(0, [])
    return result


# ============================================================
# (G) 유형 조회 함수 (입력 유형 C / D용)
# ============================================================

def lookup_type(t: str) -> Dict:
    """단일 유형 풀 데이터 조회 (학술 출처 메타데이터 포함)."""
    norm = validate_type(t)
    data = TYPE_DATA[norm]
    stack = data["stack"]
    return {
        "type": norm,
        "neris_label_en": data["neris"],
        "neris_label_ko": data["neris_ko"],
        "keirsey_label_en": data["keirsey"],
        "keirsey_temperament": data["keirsey_temperament"],
        "cognitive_stack": {
            "dominant": stack[0],
            "auxiliary": stack[1],
            "tertiary": stack[2],
            "inferior": stack[3],
            "string": "-".join(stack),
        },
        "inferior_grip": data["inferior_grip"],
        "population_pct": data["population_pct"],
        "group": data["group"],
        "sources_short": {
            "stack": "Myers (Gifts Differing, 1980)",
            "grip": "Quenk (Was That Really Me, 2002)",
            "population": "Myers et al. (MBTI Manual 3rd ed. 1998, Table 7.6 Sample 1, N=3009 CPP National Sample)",
            "neris_label": "16personalities.com (NERIS Analytics Ltd.) — 비공식·등록 상표",
            "keirsey_label": "Keirsey (Please Understand Me II, 1998)",
        },
        "sources": get_references_for([
            "myers_1980_gifts_differing",
            "mbti_manual_1998_3rd",
            "quenk_2002_grip",
            "keirsey_1998_pumii",
            "neris_16personalities",
        ]),
        "critique_sources": get_references_for([
            "pittenger_1993", "pittenger_2005",
        ]),
    }


def compare_types(t1: str, t2: str) -> Dict:
    """두 유형 비교 (입력 유형 D)."""
    a = lookup_type(t1)
    b = lookup_type(t2)
    return {"type_a": a, "type_b": b}


# ============================================================
# (H) 통합 분석 (입력 유형 A·B 용)
# ============================================================

def analyze_binary(answers: Dict[str, str]) -> Dict:
    errors = validate_binary_answers(answers)
    if errors:
        return {"status": "error", "errors": errors}
    axis_results = {axis: score_axis_binary(axis, answers) for axis in AXES}
    return {"status": "ok", **assemble_type(axis_results)}


def analyze_scale(answers: Dict[str, int]) -> Dict:
    errors = validate_scale_answers(answers)
    if errors:
        return {"status": "error", "errors": errors}
    axis_results = {axis: score_axis_scale(axis, answers) for axis in AXES}
    return {"status": "ok", **assemble_type(axis_results)}


def analyze_b1(counts: Dict[str, Dict[str, int]]) -> Dict:
    errors = validate_b1_counts(counts)
    if errors:
        return {"status": "error", "errors": errors}
    axis_results = {axis: score_axis_b1(axis, counts[axis]) for axis in AXES}
    return {"status": "ok", **assemble_type(axis_results)}


def analyze_b2(totals: Dict[str, int]) -> Dict:
    errors = validate_b2_totals(totals)
    if errors:
        return {"status": "error", "errors": errors}
    axis_results = {axis: score_axis_b2(axis, totals[axis]) for axis in AXES}
    return {"status": "ok", **assemble_type(axis_results)}


# ============================================================
# (I) CLI 진입점
# ============================================================

def cmd_questions(args):
    """20문항 카탈로그 출력. 옵션: --axis EI|SN|TF|JP."""
    axis = None
    if args and args[0].startswith("--axis"):
        axis = args[0].split("=", 1)[1] if "=" in args[0] else args[1]
    out = []
    for qid, (ax, a, b) in QUESTIONS.items():
        if axis and ax != axis:
            continue
        out.append({"qid": qid, "axis": ax, "A": a, "B": b})
    print(json.dumps({"questions": out, "count": len(out)}, ensure_ascii=False, indent=2))


def cmd_axes(_args):
    """4축 정의 출력."""
    print(json.dumps(AXIS_DEFINITION, ensure_ascii=False, indent=2))


def cmd_types(_args):
    """16유형 전체 데이터 출력."""
    print(json.dumps({t: TYPE_DATA[t] for t in ALL_TYPES}, ensure_ascii=False, indent=2))


def cmd_lookup(args):
    if not args:
        print(json.dumps({"error": "유형 인자 필요 (예: INTJ)"}, ensure_ascii=False))
        sys.exit(1)
    try:
        print(json.dumps(lookup_type(args[0]), ensure_ascii=False, indent=2))
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


def cmd_compare(args):
    if len(args) < 2:
        print(json.dumps({"error": "두 유형 인자 필요 (예: INTJ INFJ)"}, ensure_ascii=False))
        sys.exit(1)
    try:
        print(json.dumps(compare_types(args[0], args[1]), ensure_ascii=False, indent=2))
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(1)


def cmd_analyze(args):
    """
    표준 입력 JSON:
      모드 binary: {"mode": "binary", "answers": {"Q01": "A", ...}}
      모드 scale:  {"mode": "scale",  "answers": {"Q01": 2, ...}}
      모드 b1:     {"mode": "b1", "counts": {"EI": {"E":4,"I":1}, ...}}
      모드 b2:     {"mode": "b2", "totals": {"EI": 7, "SN": 18, "TF": 8, "JP": 22}}
    """
    payload = json.loads(sys.stdin.read())
    mode = payload.get("mode")
    if mode == "binary":
        result = analyze_binary(payload["answers"])
    elif mode == "scale":
        result = analyze_scale(payload["answers"])
    elif mode == "b1":
        result = analyze_b1(payload["counts"])
    elif mode == "b2":
        result = analyze_b2(payload["totals"])
    else:
        result = {"status": "error", "errors": [f"unknown mode: {mode}"]}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_refs(args):
    """학술 출처 메타데이터 출력. 옵션: 특정 key."""
    if args:
        result = {k: REFERENCES[k] for k in args if k in REFERENCES}
        unknown = [k for k in args if k not in REFERENCES]
        if unknown:
            result["_unknown_keys"] = unknown
    else:
        result = REFERENCES
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_selftest(_args):
    """엔진 자기 테스트 — 회귀 방지용."""
    failures = []

    # 1) 모든 16유형 lookup 정상
    for t in ALL_TYPES:
        d = lookup_type(t)
        if d["type"] != t:
            failures.append(f"lookup {t}: 정규화 실패")
        if len(d["cognitive_stack"]["string"].split("-")) != 4:
            failures.append(f"lookup {t}: 스택 길이 != 4")

    # 2) 잘못된 유형 거부
    for bad in ["INTX", "1234", "INTJX", "", "intj", "  INTJ  "]:
        try:
            v = validate_type(bad)
            # 공백·소문자 정규화 케이스: INTJ로 정규화되면 통과
            if bad.strip().upper() != v:
                failures.append(f"validate_type({bad!r}): 잘못된 정규화 → {v}")
        except ValueError:
            if bad.strip().upper() in TYPE_DATA:
                failures.append(f"validate_type({bad!r}): 정상 유형을 거부")

    # 3) 이항 채점 — 모든 답 A → ESTJ
    answers_all_a = {f"Q{n:02d}": "A" for n in range(1, 21)}
    r = analyze_binary(answers_all_a)
    if r["status"] != "ok" or r["primary_type"] != "ESTJ":
        failures.append(f"all-A 이항: 기대 ESTJ, 결과 {r.get('primary_type')}")

    # 4) 이항 채점 — 모든 답 B → INFP
    answers_all_b = {f"Q{n:02d}": "B" for n in range(1, 21)}
    r = analyze_binary(answers_all_b)
    if r["status"] != "ok" or r["primary_type"] != "INFP":
        failures.append(f"all-B 이항: 기대 INFP, 결과 {r.get('primary_type')}")

    # 5) 5점 척도 — 모든 답 1 → ESTJ
    answers_all_1 = {f"Q{n:02d}": 1 for n in range(1, 21)}
    r = analyze_scale(answers_all_1)
    if r["status"] != "ok" or r["primary_type"] != "ESTJ":
        failures.append(f"all-1 5점: 기대 ESTJ, 결과 {r.get('primary_type')}")

    # 6) 5점 척도 — 모든 답 5 → INFP
    answers_all_5 = {f"Q{n:02d}": 5 for n in range(1, 21)}
    r = analyze_scale(answers_all_5)
    if r["status"] != "ok" or r["primary_type"] != "INFP":
        failures.append(f"all-5 5점: 기대 INFP, 결과 {r.get('primary_type')}")

    # 7) 5점 척도 — 모든 답 3 → 4축 모두 중립 → 후보 16개
    answers_all_3 = {f"Q{n:02d}": 3 for n in range(1, 21)}
    r = analyze_scale(answers_all_3)
    if r["status"] != "ok" or len(r["neutral_axes"]) != 4 or len(r["candidate_types"]) != 16:
        failures.append(
            f"all-3 5점 중립: 기대 neutral=4, candidates=16, "
            f"결과 neutral={len(r.get('neutral_axes', []))}, "
            f"candidates={len(r.get('candidate_types', []))}"
        )

    # 8) B-1 검증 — 합 != 5인 경우 거부
    bad_b1 = {"EI": {"E": 4, "I": 0}, "SN": {"S": 2, "N": 3},
              "TF": {"T": 5, "F": 0}, "JP": {"J": 3, "P": 2}}
    r = analyze_b1(bad_b1)
    if r["status"] != "error":
        failures.append("B-1 합 != 5 거부 실패")

    # 9) B-2 정상 — {EI:7, SN:18, TF:8, JP:22} → INTP (E총점7→E? 7<15→E. SN18>15→N. TF8<15→T. JP22>15→P → ENTP)
    # 사실 7<15→A쪽 = E. SN: 18>15 → B쪽 = N. TF: 8<15 → A쪽 = T. JP: 22>15 → B쪽 = P → ENTP
    r = analyze_b2({"EI": 7, "SN": 18, "TF": 8, "JP": 22})
    if r["status"] != "ok" or r["primary_type"] != "ENTP":
        failures.append(f"B-2 INTP 케이스: 기대 ENTP, 결과 {r.get('primary_type')}")

    # 10) 인지 기능 스택 — INTJ: Ni-Te-Fi-Se
    intj = lookup_type("INTJ")
    if intj["cognitive_stack"]["string"] != "Ni-Te-Fi-Se":
        failures.append(f"INTJ stack: 기대 Ni-Te-Fi-Se, 결과 {intj['cognitive_stack']['string']}")

    # 11) 인구 비율 — INFJ 최희소(1.5)
    pops = [(t, TYPE_DATA[t]["population_pct"]) for t in ALL_TYPES]
    rarest = min(pops, key=lambda x: x[1])
    if rarest[0] != "INFJ":
        failures.append(f"최희소 유형 INFJ 기대, 결과 {rarest}")

    # 12) 인구 비율 합 ≈ 100
    total = sum(TYPE_DATA[t]["population_pct"] for t in ALL_TYPES)
    if abs(total - 100) > 0.5:
        failures.append(f"인구 비율 합 ≈ 100 기대, 결과 {total:.2f}")

    # 13) REFERENCES 모든 key 존재 + 필수 필드
    required_keys = [
        "myers_1980_gifts_differing", "mbti_manual_1998_3rd", "quenk_2002_grip",
        "beebe_2017_8function", "jung_1921_psychological_types", "keirsey_1998_pumii",
        "pittenger_1993", "pittenger_2005", "neris_16personalities",
    ]
    for k in required_keys:
        if k not in REFERENCES:
            failures.append(f"REFERENCES 누락: {k}")
            continue
        ref = REFERENCES[k]
        if "key" not in ref or "notes" not in ref:
            failures.append(f"REFERENCES[{k}]: key·notes 필드 누락")

    # 14) Pittenger 2005 DOI 정확성
    if REFERENCES["pittenger_2005"].get("doi") != "10.1037/1065-9293.57.3.210":
        failures.append("Pittenger 2005 DOI 누락 또는 오류")

    # 15) lookup 응답에 sources·critique_sources 둘 다 포함
    d = lookup_type("INTJ")
    if "sources" not in d or "critique_sources" not in d:
        failures.append("lookup 응답: sources/critique_sources 필드 누락")
    if "myers_1980_gifts_differing" not in d.get("sources", {}):
        failures.append("lookup 응답 sources: Myers 1980 누락")
    if "pittenger_2005" not in d.get("critique_sources", {}):
        failures.append("lookup 응답 critique_sources: Pittenger 2005 누락")

    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures},
                         ensure_ascii=False, indent=2))
        sys.exit(1)
    print(json.dumps({"status": "PASS", "tests_run": 15}, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n사용법: mbti_engine.py <command> [args]")
        print("commands:")
        print("  questions [--axis=EI|SN|TF|JP]   20문항 카탈로그")
        print("  axes                              4축 정의")
        print("  types                             16유형 데이터")
        print("  lookup <TYPE>                     단일 유형 조회 (예: INTJ)")
        print("  compare <T1> <T2>                 두 유형 비교")
        print("  analyze  (stdin JSON)             통합 분석 (모드 binary/scale/b1/b2)")
        print("  selftest                          자기 회귀 테스트")
        sys.exit(1)
    cmd = sys.argv[1]
    args = sys.argv[2:]
    table = {
        "questions": cmd_questions,
        "axes": cmd_axes,
        "types": cmd_types,
        "lookup": cmd_lookup,
        "compare": cmd_compare,
        "analyze": cmd_analyze,
        "refs": cmd_refs,
        "selftest": cmd_selftest,
    }
    if cmd not in table:
        print(json.dumps({"error": f"unknown command: {cmd}"}, ensure_ascii=False))
        sys.exit(1)
    table[cmd](args)


if __name__ == "__main__":
    main()
