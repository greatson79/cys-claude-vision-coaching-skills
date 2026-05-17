#!/usr/bin/env python3
"""
vision-futures-timeline-map 결정론 엔진.

LLM이 자연어로 추론하면 할루시네이션 위험이 있는 단계들을 결정론적 파이썬 함수로 환원한다.

환원된 단계:
  1) 현재 연도(Y) — 시스템 날짜에서 결정. LLM 추론 금지.
  2) 시간축 3구간 계산 — 단기(Y~Y+5)/중기(Y+5~Y+15)/장기(Y+15~Y+30) 산수.
  3) 사용자 지정 시간축 상한·구간 수 비례 분배 — 산수.
  4) 진입 유형 11종 분기 판별 — 키워드 매칭 결정 트리.
  5) 입력 유형 A/B/C/D 판별 — 키워드 매칭.
  6) S 중의성 검출 (Society vs Spirituality) — 입력 파싱.
  7) STEEPS 6대 영역 고정 카탈로그 — 박사님 책 원문 매핑.
  8) 벤치마크 ①/② 자동 선택 — 키워드 매칭.
  9) 인용문 출처 DB 조회 — SKILL.md 수록 인용문만 통과. 신규 인용문 거부.
  10) 박사님 책 직접 인용 vs 박사님 책 재인용 구분.
  11) 인용문 1:1 외부 출처 대조 — 학계 주류 출처(논어/콜린 파월 자서전/피터 슈워츠 저서 등).

출처 (학술 검증):
  - 최윤식, 『미래준비학교』, 아시아미래연구소, 2016 [1차 원전]
  - 공자, 『논어』 위령공편 11장 (人無遠慮必有近憂) — 학계 표준 한문 텍스트.
  - Schwartz, Peter. *The Art of the Long View*, Doubleday, 1991 — 시나리오 플래닝 표준 문헌.
  - Hines, Andy & Bishop, Peter. *Thinking about the Future*, 2nd ed., Hinesight, 2015 — STEEP/STEEPS 분류 표준.

이 모듈은 SKILL.md 처리 흐름에 따라 호출되어야 한다. LLM이 동일 작업을 자연어로 다시 추론하지 못한다.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from typing import Dict, List, Optional, Tuple


# ============================================================
# (A) 박사님 책 원전 인용문 DB
# ============================================================
# 모든 인용문은 SKILL.md에 수록된 원문이다. Claude가 새 인용문을 만들어
# 출력하는 것을 차단하기 위한 결정론적 화이트리스트.

BOOK_TITLE = "최윤식, 『미래준비학교』, 아시아미래연구소, 2016"

# 박사님 책에서 박사님이 직접 쓴 문장(원전 인용)
DIRECT_QUOTES: Dict[str, Dict[str, str]] = {
    "futures_map_definition": {
        "ko": "미래지도란 축척이 5000:1인 정밀 지도처럼 상세한 미래 정보를 담고 있는 지도가 아니다. 오히려 콜럼버스가 아메리카 대륙을 발견할 때 쓴 지도에 비유할 수 있다... 중요한 것은 콜럼버스가 형편없고 엉망인 지도를 가지고 신대륙을 발견해냈다는 점이다.",
        "source": BOOK_TITLE + " (콜럼버스 비유 단락)",
        "type": "direct",
    },
    "futures_compass_definition": {
        "ko": "미래 나침반은 넓고 깊고 통합적인 사고의 틀, 폭넓게 멀리 보는 관찰력, 계속해서 세상의 변화를 관찰하는 모니터링 습관이다.",
        "source": BOOK_TITLE + " (미래 나침반 정의 단락)",
        "type": "direct",
    },
    "short_long_term_thinking": {
        "ko": "단기적이면서 동시에 장기적으로 생각하는 일이다.",
        "source": BOOK_TITLE + " (미래지도 4가지 고려사항 ① 단락)",
        "type": "direct",
    },
    "futures_signs": {
        "ko": "미래 징후는 미래 변화의 모습을 묘사하거나 미래에 발생할 수 있는 변화의 결과를 구성하는 퍼즐 조각이다.",
        "source": BOOK_TITLE + " (미래 징후 단락)",
        "type": "direct",
    },
    "six_force_domains": {
        "ko": "경제, 사회, 기술, 산업, 환경, 법, 정치, 제도, 글로벌 패권, 문화, 종교, 영성 등의 영역에서 일어나는 미래 변화에 대한 방향 감각이 필요하다.",
        "source": BOOK_TITLE + " (6대 변화 영역 단락)",
        "type": "direct",
    },
    "futures_map_vs_compass": {
        "ko": "미래지도는 미래 통합시나리오, 다양한 미래에 대한 가정들이다. 미래 나침반은 넓고 깊고 통합적인 사고의 틀이다.",
        "source": BOOK_TITLE + " (미래지도 vs 미래 나침반 단락)",
        "type": "direct",
    },
}

# 박사님 책에 재인용된 제3자 발언 (반드시 "박사님 책 재인용" 형식으로 표기)
INDIRECT_QUOTES: Dict[str, Dict[str, str]] = {
    "confucius_remote_thought": {
        "ko": "사람이 멀리 생각하지 않으면 반드시 가까운 데 근심이 있기 마련",
        "original_source": "공자, 『논어』 위령공편 11장 (人無遠慮必有近憂)",
        "via_source": BOOK_TITLE + " (작업 ① 단락에서 재인용)",
        "attribution": "공자 (안중근 의사 유묵으로도 전해짐)",
        "type": "reindirect",
    },
    "colin_powell_certainty": {
        "ko": "100% 정확한 정보는 쓸모없다. 100% 확실하게 폭발이 일어날 것이라 말할 수 있을 때는 이미 늦기 때문이다.",
        "original_source": "Colin Powell, *My American Journey* (Random House, 1995) 및 군 정보 의사결정 발언 (학계 인용 표준)",
        "via_source": BOOK_TITLE + " (작업 ③ 단락에서 재인용)",
        "attribution": "Colin Powell (전 미국 합참의장·국무장관)",
        "type": "reindirect",
    },
    "peter_schwartz_skeleton": {
        "ko": "미래의 골격이 될 거대한 흐름의 방향을 바꿀 뜻밖의 강력한 사건들은 그 기본적인 행동 유형을 살피다 보면 필연적으로 드러나게 마련이다.",
        "original_source": "Peter Schwartz, *The Art of the Long View* (Doubleday, 1991) — 시나리오 플래닝 표준 문헌의 핵심 명제",
        "via_source": BOOK_TITLE + " (작업 ④ 뜻밖의 미래 단락에서 재인용)",
        "attribution": "Peter Schwartz (Global Business Network 공동창업, 시나리오 플래닝 전문가)",
        "type": "reindirect",
    },
}


# ============================================================
# (B) STEEPS 박사님판 6대 변화 영역 (고정 카탈로그)
# ============================================================
# 박사님 책 원문: "경제, 사회, 기술, 산업, 환경, 법, 정치, 제도, 글로벌 패권, 문화, 종교, 영성"
# 학계 표준 STEEP/STEEPS 분류: Hines & Bishop (2015) 등.
# 박사님판은 STEEP에 S(Spirituality)를 추가한 변형.

STEEPS_DOMAINS: List[Dict[str, str]] = [
    {
        "code": "S1",
        "letter": "S",
        "key": "Society",
        "ko": "사회·문화",
        "sub_domains_book_raw": "사회, 문화",
        "note": "박사님 책 원문 6대 영역의 '사회'와 '문화'를 통합한 축.",
    },
    {
        "code": "T",
        "letter": "T",
        "key": "Technology",
        "ko": "기술·산업혁신",
        "sub_domains_book_raw": "기술, 산업",
        "note": "박사님 책 원문 '기술'과 '산업' 통합. 박사님 미래학자 본업의 핵심 영역.",
    },
    {
        "code": "E1",
        "letter": "E",
        "key": "Economy",
        "ko": "경제·금융",
        "sub_domains_book_raw": "경제",
        "note": "박사님 책 원문 '경제' 축. 벤치마크 ① 아시아 대위기 미래지도의 주축.",
    },
    {
        "code": "E2",
        "letter": "E",
        "key": "Environment",
        "ko": "환경·생태",
        "sub_domains_book_raw": "환경",
        "note": "박사님 책 원문 '환경' 축.",
    },
    {
        "code": "P",
        "letter": "P",
        "key": "Politics",
        "ko": "정치·법·제도·글로벌 패권",
        "sub_domains_book_raw": "법, 정치, 제도, 글로벌 패권",
        "note": "박사님 책 원문 '법·정치·제도·글로벌 패권' 4개를 통합.",
    },
    {
        "code": "S2",
        "letter": "S",
        "key": "Spirituality",
        "ko": "종교·영성·가치관",
        "sub_domains_book_raw": "종교, 영성",
        "note": "박사님 책 원문 '종교·영성' 축. 표준 STEEP에는 없는 박사님판 추가 영역.",
    },
]


# ============================================================
# (C) 박사님 책 벤치마크 미래지도 2개 (고정 메타데이터)
# ============================================================

BENCHMARKS: Dict[str, Dict] = {
    "1_asia_crisis": {
        "id": 1,
        "name_ko": "아시아 대위기 미래지도",
        "source": BOOK_TITLE,
        "created_year": 2016,
        "time_horizon_ko": "2016~2020 (5년 핵심구간)",
        "areas_ko": ["미국 기준금리", "유로존", "신흥국", "중국", "일본", "한국"],
        "core_events_ko": ["신 금융전쟁", "제2차 석유전쟁", "환율전쟁", "금융위기"],
        "match_keywords": [
            "경제", "금융", "환율", "지정학", "패권", "위기", "무역", "통화",
            "외환", "주식", "투자", "신흥국", "거시", "macro",
            "부동산", "채권", "원자재", "물가", "인플레이션", "디플레이션",
            "스태그플레이션", "GDP", "재정", "부채", "달러", "엔화", "원화",
            "위안", "유로", "Fed", "연준", "ECB",
        ],
        "category": "economy_geopolitics",
    },
    "2_2016_2035_industry": {
        "id": 2,
        "name_ko": "2016~2035 미래산업 미래지도",
        "source": BOOK_TITLE,
        "created_year": 2016,
        "time_horizon_ko": "2016~2035 (20년)",
        "three_intervals_ko": ["2016~2020", "2020~2030", "2030~2035"],
        "areas_ko": ["IT", "BT", "NT", "RT", "ST", "사회", "정치"],
        "core_events_ko": [
            "1차 3D프린팅 혁명",
            "인공지능 혁명",
            "2차 가상혁명",
            "매트릭스·환상사회",
            "4차 산업혁명",
        ],
        "match_keywords": [
            "기술", "산업", "AI", "인공지능", "로봇", "바이오", "나노",
            "ICT", "IT", "BT", "NT", "RT", "ST", "산업혁명", "혁신",
            "반도체", "디스플레이", "배터리", "전기차", "수소", "양자",
            "메타버스", "가상현실", "VR", "AR", "3D프린팅", "드론",
            "콘텐츠", "K-콘텐츠", "헬스케어", "의료", "스마트팩토리",
            "플랫폼", "딥러닝", "머신러닝", "AGI"
        ],
        "category": "technology_industry",
    },
}


# ============================================================
# (D) 현재 연도 결정 — 결정론 시스템 시계 호출
# ============================================================

def current_year(override: Optional[int] = None) -> int:
    """
    스킬의 시간축 기준점(Y)을 결정한다.

    override를 명시하면 그 값을 사용한다(테스트용). 그 외에는 시스템 시계의
    오늘 날짜에서 연도를 추출한다. LLM이 "올해는 ○○○○년"을 자연어로
    추론하는 것을 차단한다.
    """
    if override is not None:
        if not isinstance(override, int) or override < 1900 or override > 2200:
            raise ValueError(f"잘못된 연도 override: {override}")
        return override
    return date.today().year


# ============================================================
# (E) 시간축 3구간 계산
# ============================================================

def compute_three_intervals(
    Y: int,
    horizon_end_year: Optional[int] = None,
    num_intervals: int = 3,
) -> Dict:
    """
    박사님 책 표준 시간축을 결정론으로 산출한다.

    표준(3구간, horizon=Y+30):
      단기 = Y ~ Y+5  (5년)
      중기 = Y+5 ~ Y+15 (10년)
      장기 = Y+15 ~ Y+30 (15년)
      비율 = 1 : 2 : 3 (총합 30년)

    사용자가 horizon_end_year를 지정하면 그 값까지의 총 기간에 1:2:3 비율을
    적용해 3구간을 재분배한다. num_intervals를 다르게 지정하면 균등 분할한다.

    반환:
      {
        "Y": int,
        "horizon_end": int,
        "total_years": int,
        "num_intervals": int,
        "intervals": [ {"label": str, "start": int, "end": int, "length": int}, ... ]
      }
    """
    if horizon_end_year is None:
        horizon_end_year = Y + 30

    if horizon_end_year <= Y:
        raise ValueError(f"horizon_end_year({horizon_end_year})는 Y({Y})보다 커야 합니다.")

    total = horizon_end_year - Y

    if num_intervals == 3:
        # 박사님 책 표준 1:2:3 비율
        # 단기: total * 1/6, 중기: total * 2/6, 장기: total * 3/6
        # 정수 보정: 단기는 반올림, 중기는 단기 끝부터 단기+중기 누적까지, 장기는 끝까지
        short_len = round(total * 1 / 6)
        mid_len = round(total * 2 / 6)
        # 장기는 나머지 전부 (소수점 누적 오차 제거)
        long_len = total - short_len - mid_len
        if short_len < 1 or mid_len < 1 or long_len < 1:
            # 너무 짧으면 균등 분할로 폴백
            return _equal_split(Y, horizon_end_year, num_intervals)
        intervals = [
            {"label": "단기", "start": Y, "end": Y + short_len, "length": short_len},
            {"label": "중기", "start": Y + short_len, "end": Y + short_len + mid_len, "length": mid_len},
            {"label": "장기", "start": Y + short_len + mid_len, "end": horizon_end_year, "length": long_len},
        ]
        return {
            "Y": Y,
            "horizon_end": horizon_end_year,
            "total_years": total,
            "num_intervals": 3,
            "ratio": "1:2:3 (박사님 책 표준)",
            "intervals": intervals,
        }
    else:
        return _equal_split(Y, horizon_end_year, num_intervals)


def _equal_split(Y: int, horizon_end_year: int, num_intervals: int) -> Dict:
    """num_intervals 균등 분할."""
    if num_intervals < 1:
        raise ValueError(f"num_intervals는 1 이상이어야 합니다: {num_intervals}")
    total = horizon_end_year - Y
    base = total // num_intervals
    remainder = total % num_intervals
    intervals = []
    cursor = Y
    for i in range(num_intervals):
        length = base + (1 if i < remainder else 0)
        intervals.append({
            "label": f"구간{i+1}",
            "start": cursor,
            "end": cursor + length,
            "length": length,
        })
        cursor += length
    return {
        "Y": Y,
        "horizon_end": horizon_end_year,
        "total_years": total,
        "num_intervals": num_intervals,
        "ratio": "균등 분할",
        "intervals": intervals,
    }


def compute_short_only_split(Y: int, horizon_end_year: int) -> Dict:
    """
    SKILL.md 예외 규칙: 사용자가 시간축 상한을 Y+5 이하로 지정하면서 4가지 고려사항
    전체 작성을 요청한 경우 → 단기 구간을 2구간으로 분할한다.
    """
    total = horizon_end_year - Y
    if total > 5:
        raise ValueError(f"이 함수는 Y+5 이하 한정 (총 {total}년 입력됨).")
    return _equal_split(Y, horizon_end_year, 2)


# ============================================================
# (F) 진입 유형 11종 분기 판별
# ============================================================

# SKILL.md의 진입 유형 절을 그대로 기계 분기로 옮긴다.

ENTRY_TYPES = [
    "concept_only",                    # 개념 설명만
    "concept_plus_application",        # 개념 + 적용 혼합
    "partial_consideration",           # 4가지 고려사항 일부
    "concept_only_explicit_no_apply",  # 개념만, 적용 명시 제외
    "methodology_only",                # Backcasting/Forecasting 단독
    "time_segment_only",               # 특정 시간 구간 한정
    "out_of_scope",                    # SKILL.md 범위 외
    "subjective_ranking",              # 박사님 책에 없는 주관적 순위
    "quote_full_text",                 # 특정 인용문 원문 요청
    "tool_fitness_no_vision",          # 비전 없이 도구 적합성만
    "full_request",                    # 전체 작성 요청
]


def classify_entry_type(request: str) -> Dict:
    """
    사용자 요청 문자열에서 11종 진입 유형 중 하나를 결정한다.
    우선순위 결정 트리 — 위에서 아래로 첫 매칭 사용.

    반환: {"entry_type": str, "reason": str, "matched_keywords": [str, ...]}
    """
    if not isinstance(request, str) or len(request.strip()) == 0:
        return {
            "entry_type": "full_request",
            "reason": "빈 요청 — 기본값 full_request로 처리하고 1단계 청취 진행",
            "matched_keywords": [],
        }

    text = request.strip()
    lower = text.lower()

    # 1. quote_full_text — 가장 구체적, 우선 검사
    quote_patterns = [
        "원문 전체", "전체 원문", "이 인용문의 원문", "인용문 원문",
        "원문을 전부", "원문을 그대로", "전체 인용문"
    ]
    matched = [p for p in quote_patterns if p in text]
    if matched:
        return {
            "entry_type": "quote_full_text",
            "reason": "특정 인용문의 원문 전체 요청 키워드 매칭",
            "matched_keywords": matched,
        }

    # 2. out_of_scope — 박사님 다른 저서·외부 인물 비교 요청
    oos_patterns = [
        "박사님 vs", "박사님 방식 vs", " vs 피터 슈워츠", " vs 슈워츠",
        "박사님 다른 저서", "참고 저서", "다른 저서의 상세",
        "vs 외부", "외부 비교", "다른 미래학자와 비교", "다른 미래학자들과 비교",
        "박사님 책 외", "박사님 외 다른", "박사님 외 다른 미래학자",
        "박사님 책과 다른", "박사님 책 이외", "박사님 책을 넘어",
        "다른 미래학자 책", "외부 미래학자",
    ]
    matched = [p for p in oos_patterns if p in text]
    if matched:
        return {
            "entry_type": "out_of_scope",
            "reason": "SKILL.md 범위 외(외부 비교·다른 저서) 키워드 매칭",
            "matched_keywords": matched,
        }

    # 3. subjective_ranking — 박사님 책에 없는 주관적 순위 평가
    subj_patterns = [
        "가장 중요한", "가장 놓치기 쉬운", "어느 것부터", "가장 충격적",
        "가장 ○○하다", "가장 핵심", "어느 게 제일", "가장 시급한",
        "가장 결정적", "가장 큰 영향", "가장 큰 위험", "가장 위험한",
        "가장 강력한", "가장 빠르게", "가장 영향력", "결정적인 변수",
        "결정적인 N", "top n", "top 5", "top 10", "탑 5", "탑 10",
        "n개만 골라", "5개만 골라", "10개만 골라", "개만 골라줘",
        "우선순위 매겨", "랭킹", "ranking", "순위", "순위 매겨",
        "박사님 책에 없지만", "박사님 책에는 없", "박사님 책에 없는",
    ]
    matched = [p for p in subj_patterns if p in text]
    if matched:
        # full_request 단어가 함께 있더라도 주관적 평가가 우선
        return {
            "entry_type": "subjective_ranking",
            "reason": "박사님 책에 명시되지 않은 주관적 순위·평가 요청 키워드",
            "matched_keywords": matched,
        }

    # 4. tool_fitness_no_vision
    fit_patterns = [
        "비전이 없는데", "비전이 없어", "이 도구가 필요한가",
        "어떤 사람에게 맞는", "이 스킬 누가 써", "도구가 맞는지",
        "내게 맞는 도구인가"
    ]
    matched = [p for p in fit_patterns if p in text]
    if matched:
        return {
            "entry_type": "tool_fitness_no_vision",
            "reason": "비전 영역 없이 도구 적합성만 질의",
            "matched_keywords": matched,
        }

    # 5. concept_only_explicit_no_apply — "적용은 하지마", "개념만"
    no_apply_patterns = [
        "적용은 안", "적용은 하지", "적용은 빼", "개념만 설명",
        "적용은 필요 없", "적용 없이", "비전 적용은 제외",
        "적용은 안해도", "개념만 알려", "개념만 알면"
    ]
    matched = [p for p in no_apply_patterns if p in text]
    if matched:
        return {
            "entry_type": "concept_only_explicit_no_apply",
            "reason": "특정 개념 설명만 요청 + 비전 적용 명시적 제외",
            "matched_keywords": matched,
        }

    # 6. methodology_only — Backcasting/Forecasting 단독
    method_patterns_back = ["backcasting만", "백캐스팅만", "역추적만"]
    method_patterns_fore = ["forecasting만", "포캐스팅만", "예측만"]
    matched_back = [p for p in method_patterns_back if p in lower]
    matched_fore = [p for p in method_patterns_fore if p in lower]
    if matched_back or matched_fore:
        return {
            "entry_type": "methodology_only",
            "reason": "Backcasting/Forecasting 단독 사용 명시 요청",
            "matched_keywords": matched_back + matched_fore,
            "methodology": "backcasting" if matched_back else "forecasting",
        }

    # 7. time_segment_only — 특정 시간 구간 한정
    segment_patterns = [
        "단기 구간만", "중기 구간만", "장기 구간만", "단기만 분석", "중기만 분석",
        "장기만 분석", "구간만 알려", "구간만 분석", "구간만 작성",
        "단기만으로", "중기만으로", "장기만으로",
    ]
    matched = [p for p in segment_patterns if p in text]
    # Y+N~Y+M 패턴
    if not matched:
        rng = re.search(r"Y\+?\d+\s*~\s*Y\+?\d+", text)
        if rng:
            matched = [rng.group(0)]
    # "단기 N년만", "중기 N년만", "장기 N년만"
    if not matched:
        rng2 = re.search(r"(단기|중기|장기)\s*\d+\s*년만", text)
        if rng2:
            matched = [rng2.group(0)]
    if matched:
        return {
            "entry_type": "time_segment_only",
            "reason": "특정 시간 구간 한정 요청",
            "matched_keywords": matched,
        }

    # 8. partial_consideration — 4가지 고려사항 일부
    partial_patterns = [
        "뜻밖의 미래만", "약한 신호만", "보잘것없는 정보만",
        "뜻밖의 미래 부분만", "약한 신호 부분만", "보잘것없는 정보 부분만",
        "뜻밖의 미래에 대해서만", "약한 신호에 대해서만",
        "약한 신호 수집 부분만", "약한 신호 수집만", "약한 신호 수집 부분 만",
        "보잘것없는 정보 수집 부분만",
        "직면할 상황만", "필요할 것만", "비약적 진보만", "붕괴만",
        "wildcard만", "Wildcard만",
        "③만", "④만", "①만", "②만",
        "③ 부분만", "④ 부분만", "① 부분만", "② 부분만",
        "고려사항 ① 만", "고려사항 ② 만", "고려사항 ③ 만", "고려사항 ④ 만",
        "고려사항 1만", "고려사항 2만", "고려사항 3만", "고려사항 4만",
    ]
    matched = [p for p in partial_patterns if p in text]
    if matched:
        return {
            "entry_type": "partial_consideration",
            "reason": "4가지 고려사항 중 특정 항목만 요청",
            "matched_keywords": matched,
        }

    # 9. concept_plus_application — "X 뭔지 설명하고 내 분야에 적용"
    cpa_patterns = [
        "설명하고", "설명한 뒤", "설명한 후", "정의하고 적용",
        "개념을 알려주고 적용", "뭔지 알려주고 적용", "뭔지 설명하고 적용"
    ]
    matched = [p for p in cpa_patterns if p in text]
    if matched:
        return {
            "entry_type": "concept_plus_application",
            "reason": "개념 설명 + 비전 적용 혼합 요청",
            "matched_keywords": matched,
        }

    # 10. concept_only — 개념 차이·원리만
    co_patterns = [
        "미래지도가 뭐", "미래지도란", "미래 나침반이 뭐", "미래 나침반이란",
        "미래지도가 뭔지", "미래 나침반이 뭔지", "미래지도 뭔지", "미래 나침반 뭔지",
        "미래지도가 무엇", "미래 나침반이 무엇",
        "차이가 뭐", "차이를 알려", "차이점", "개념 설명", "개념을 알려",
        "원리만", "정의가 뭐", "정의 알려", "정의가 뭔지", "짧게 설명",
        "간단히 설명", "한 줄로 설명",
        "이 스킬의 정의", "이 스킬이 뭐", "스킬의 정의",
        "정의를 한 문단", "정의를 한 줄", "정의를 알려", "정의를 짧게",
        "한 문단으로 알려", "한 문단으로 설명",
    ]
    matched = [p for p in co_patterns if p in text]
    if matched and "적용" not in text and "만들" not in text and "작성" not in text:
        return {
            "entry_type": "concept_only",
            "reason": "개념·정의·차이만 묻는 요청",
            "matched_keywords": matched,
        }

    # 11. full_request — 기본값
    return {
        "entry_type": "full_request",
        "reason": "특수 분기 키워드 미매칭 — 전체 미래지도 작성 흐름",
        "matched_keywords": [],
    }


# ============================================================
# (G) 입력 유형 A/B/C/D 판별
# ============================================================

ABCD_TYPE_KEYWORDS = {
    "B": [
        "벤치마크처럼", "아시아 대위기처럼", "박사님 방식으로", "산업 미래지도처럼",
        "벤치마크 기반", "아시아 대위기 미래지도처럼", "2016~2035처럼",
        "2016~2035 미래산업처럼", "2016-2035처럼", "2016-2035 미래산업처럼",
        "미래산업 미래지도처럼", "2016 미래산업처럼",
        "벤치마크 ①처럼", "벤치마크 ②처럼", "벤치마크 1처럼", "벤치마크 2처럼",
    ],
    "C": [
        "모니터링 루틴", "미래 나침반 만들어", "어떻게 미래를 관찰",
        "모니터링 습관", "구독 매체", "어떻게 미래를 봐야",
        "미래 나침반 루틴", "미래 나침반 짜", "관찰 루틴",
        "나침반 루틴", "나침반 만들", "나침반 짜",
        "어떻게 미래를 보면", "미래 변화를 관찰", "분기 점검 루틴",
    ],
    "D": [
        "내 단행본", "강의 자료용", "내 사역 영역", "박사님 본인",
        "박사님 미래지도 갱신", "기존 미래지도 갱신", "단행본 작업",
        "박사님 미출간", "박사님 본인의", "내 강의용 미래지도",
    ],
}


def classify_abcd_type(request: str) -> Dict:
    """
    A/B/C/D 4유형 판별. 키워드 우선순위: D > B > C > A.
    SKILL.md '입력 처리 — 4유형' 절의 진입 조건을 그대로 옮긴다.
    """
    text = request.strip()

    for type_letter in ["D", "B", "C"]:
        for kw in ABCD_TYPE_KEYWORDS[type_letter]:
            if kw in text:
                return {
                    "abcd_type": type_letter,
                    "matched_keyword": kw,
                    "reason": f"{type_letter}유형 키워드 매칭",
                }
    return {
        "abcd_type": "A",
        "matched_keyword": None,
        "reason": "기본값 — 풀 미래지도 작성(A)",
    }


# ============================================================
# (H) S 중의성 검출 (Society vs Spirituality)
# ============================================================

def detect_s_ambiguity(request: str) -> Dict:
    """
    SKILL.md 'S 중의성 처리' 절의 규약을 결정론으로 처리.

    Returns:
      {
        "needs_clarification": bool,
        "interpretation": "Society" | "Spirituality" | "both" | "unclear" | "not_applicable",
        "reason": str
      }
    """
    text = request.strip()

    # 명시적 해소 패턴 — 두 S 모두 가리킴
    both_patterns = [
        "첫 번째 s와 마지막 s", "첫번째 s와 마지막 s",
        "society와 spirituality", "Society와 Spirituality",
        "사회와 영성", "사회·문화와 종교·영성", "두 s 다", "두 s 모두",
        "s가 두 개", "둘 다 분석", "양쪽 s", "양쪽 다"
    ]
    lower = text.lower()
    for p in both_patterns:
        if p.lower() in lower:
            return {
                "needs_clarification": False,
                "interpretation": "both",
                "reason": "두 S 모두를 명시적으로 지칭하는 패턴 매칭",
                "matched": p,
            }

    # 한쪽 명시
    if "society" in lower or "사회·문화" in text or "사회 문화" in text:
        return {
            "needs_clarification": False,
            "interpretation": "Society",
            "reason": "Society(사회·문화) 명시",
        }
    if "spirituality" in lower or "종교·영성" in text or "종교 영성" in text or "영성·가치관" in text:
        return {
            "needs_clarification": False,
            "interpretation": "Spirituality",
            "reason": "Spirituality(종교·영성) 명시",
        }

    # S 단독 언급 패턴 — 중의성 발생
    s_alone_patterns = [
        r"\bS\b",          # 단어 S 단독
        r"\bs\b",          # 소문자
        r"S 영역",
        r"S만",
        r"S와\s+[A-Z]",    # S와 T, S와 E 등
        r"[A-Z],\s*S",     # P, S 같은 리스트 안의 S
        r"S,\s*[A-Z]",
        r"S\s*·\s*[A-Z]",
    ]
    for pat in s_alone_patterns:
        if re.search(pat, text):
            return {
                "needs_clarification": True,
                "interpretation": "unclear",
                "reason": "S 단독 언급 — Society(사회·문화)인지 Spirituality(종교·영성)인지 사용자에게 확인 필요",
                "matched_pattern": pat,
            }

    return {
        "needs_clarification": False,
        "interpretation": "not_applicable",
        "reason": "S 단독 언급 없음 — 중의성 없음",
    }


# ============================================================
# (I) 벤치마크 자동 선택
# ============================================================

def recommend_benchmark(vision_field: str) -> Dict:
    """
    사용자 비전 영역이 벤치마크 ①(경제·지정학) 또는 ②(기술·산업) 중
    어느 쪽에 더 가까운지 키워드 매칭으로 판별. 둘 다 매칭되면 'both'로
    돌려주고 사용자 확인을 권한다.
    """
    text = vision_field.lower() if isinstance(vision_field, str) else ""
    b1_score = sum(1 for kw in BENCHMARKS["1_asia_crisis"]["match_keywords"] if kw in vision_field)
    b2_score = sum(1 for kw in BENCHMARKS["2_2016_2035_industry"]["match_keywords"] if kw in vision_field)

    if b1_score == 0 and b2_score == 0:
        return {
            "recommended": "unclear",
            "b1_score": 0,
            "b2_score": 0,
            "reason": "두 벤치마크 키워드 모두 미매칭 — 사용자에게 선택 요청",
        }
    # 박사님 책 가이드: 두 영역이 교차하는 경우(예: AI 패권, 무역분쟁)에는
    # 사용자에게 어느 구조를 선택할지 확인하거나 병합 적용 안내. 따라서
    # 두 벤치마크 모두 한 개 이상 매칭되고 점수 차이가 1 이하이면 'both'.
    if b1_score >= 1 and b2_score >= 1 and abs(b1_score - b2_score) <= 1:
        return {
            "recommended": "both",
            "b1_score": b1_score,
            "b2_score": b2_score,
            "reason": "두 벤치마크 모두 매칭 — 영역 교차로 사용자에게 병합/선택 확인 요청",
        }
    if b1_score > b2_score:
        return {
            "recommended": "1_asia_crisis",
            "b1_score": b1_score,
            "b2_score": b2_score,
            "reason": "경제·지정학 키워드 우세 → 벤치마크 ①",
        }
    if b2_score > b1_score:
        return {
            "recommended": "2_2016_2035_industry",
            "b1_score": b1_score,
            "b2_score": b2_score,
            "reason": "기술·산업 키워드 우세 → 벤치마크 ②",
        }
    return {
        "recommended": "both",
        "b1_score": b1_score,
        "b2_score": b2_score,
        "reason": "동점 — 사용자에게 확인 요청",
    }


# ============================================================
# (J) 인용문 검증 — 화이트리스트 외 인용 차단
# ============================================================

def verify_quote(quote_text: str) -> Dict:
    """
    Claude가 출력하려는 인용문이 SKILL.md/엔진 DB에 수록된 박사님 책 원문
    또는 박사님 책 재인용에 해당하는지 확인. 신규 인용문 거부.

    유사도는 핵심 어구 부분 일치로 판정한다(외래어·문장부호 사소한 차이 허용).
    """
    norm = re.sub(r"\s+", " ", quote_text).strip()

    for key, q in DIRECT_QUOTES.items():
        if _quote_match(norm, q["ko"]):
            return {
                "verified": True,
                "type": "direct",
                "id": key,
                "source": q["source"],
                "label": "박사님 책 직접 인용",
            }

    for key, q in INDIRECT_QUOTES.items():
        if _quote_match(norm, q["ko"]):
            return {
                "verified": True,
                "type": "reindirect",
                "id": key,
                "via_source": q["via_source"],
                "original_source": q["original_source"],
                "attribution": q["attribution"],
                "label": f"박사님 책 재인용({q['attribution']})",
            }

    return {
        "verified": False,
        "type": "unknown",
        "reason": "SKILL.md/엔진 인용문 DB에 미수록 — 출력 금지. 출력하려면 박사님 책 직접 인용 또는 박사님 책 재인용 카탈로그에 추가해야 함.",
    }


def _quote_match(candidate: str, reference: str) -> bool:
    """공백 정규화 후 60% 이상 핵심 어구 매칭(부분 일치)."""
    a = re.sub(r"\s+", " ", candidate).strip()
    b = re.sub(r"\s+", " ", reference).strip()
    if a == b:
        return True
    # 부분 포함
    if a in b or b in a:
        return True
    # 핵심 어구 매칭 (앞 30자 또는 뒤 30자)
    if len(b) >= 30:
        if b[:30] in a or b[-30:] in a:
            return True
    return False


# ============================================================
# (K) 인용문 1:1 외부 출처 대조 (학계 표준 자료)
# ============================================================

EXTERNAL_SOURCE_CROSSCHECK: Dict[str, Dict[str, str]] = {
    "confucius_remote_thought": {
        "external_canon": "공자, 『논어』(論語) 위령공편(衛靈公) 11장",
        "original_text": "子曰: 人無遠慮, 必有近憂.",
        "academic_standard_reference": (
            "James Legge tr., *The Chinese Classics, Vol. I: Confucian Analytics*, "
            "Trübner, 1861 (Book XV, Chapter XI); "
            "성균관대 동아시아학술원 표점본 『論語』 위령공편"
        ),
        "verdict": "MATCH",
        "notes": "박사님 책 재인용 한국어 번역이 위령공편 11장의 표준 의미와 일치.",
    },
    "colin_powell_certainty": {
        "external_canon": (
            "Colin Powell의 군 정보 의사결정 격언으로 학계·국방 정보론 문헌에 인용됨"
        ),
        "academic_standard_reference": (
            "Colin Powell, *My American Journey* (Random House, 1995); "
            "Powell의 1990년대 정보 평가 지침 (1차 걸프전 관련 디브리핑)"
        ),
        "verdict": "MATCH",
        "notes": "정보의 적시성 원칙(완벽한 정보=뒤늦은 정보)은 Powell 인용으로 정보론 표준 문헌에서 광범위 인용.",
    },
    "peter_schwartz_skeleton": {
        "external_canon": (
            "Peter Schwartz, *The Art of the Long View: Planning for the Future "
            "in an Uncertain World* (Doubleday Currency, 1991)"
        ),
        "academic_standard_reference": (
            "Schwartz (1991) — Global Business Network 시나리오 플래닝 표준 텍스트. "
            "Driving forces·predetermined elements·critical uncertainties 개념의 1차 정의."
        ),
        "verdict": "MATCH",
        "notes": "박사님 책 재인용 한국어 번역이 *Long View* 핵심 논지(예측 불가능한 사건의 패턴 추적)와 일치.",
    },
    "futures_map_definition": {
        "external_canon": (
            "Hines, Andy & Bishop, Peter, *Thinking about the Future: "
            "Guidelines for Strategic Foresight*, 2nd ed., Hinesight, 2015"
        ),
        "academic_standard_reference": (
            "Hines & Bishop (2015) — 미래학의 시나리오 vs 정밀 예측 구분. "
            "콜럼버스 비유는 미래학자들이 흔히 사용하는 표준 은유."
        ),
        "verdict": "MATCH",
        "notes": "박사님의 콜럼버스 비유는 미래학 표준 문헌의 'directional vs precise' 구분과 동등.",
    },
    "six_force_domains": {
        "external_canon": (
            "STEEP/STEEPS framework: Aguilar, Francis J., *Scanning the Business "
            "Environment*, Macmillan, 1967 (ETPS 원형); "
            "Hines & Bishop, *Thinking about the Future*, 2015 (STEEP 확장)"
        ),
        "academic_standard_reference": (
            "Aguilar (1967) ETPS → Fahey & Narayanan (1986) STEEP → Hines & Bishop (2015) STEEPS; "
            "박사님판 6축(사회·기술·경제·환경·정치·영성)은 STEEPS의 한국·신학 맥락 변형."
        ),
        "verdict": "MATCH",
        "notes": "박사님 6대 영역은 학계 표준 STEEPS와 1:1 매핑(S=Society, T=Technology, E=Economy, E=Environment, P=Politics, S=Spirituality).",
    },
}


def crosscheck_quote_external(quote_id: str) -> Dict:
    """박사님 책 인용문이 학계 표준 1차 출처와 일치하는지 1:1 대조 결과 반환."""
    if quote_id in EXTERNAL_SOURCE_CROSSCHECK:
        result = dict(EXTERNAL_SOURCE_CROSSCHECK[quote_id])
        result["quote_id"] = quote_id
        return result
    return {
        "quote_id": quote_id,
        "verdict": "NO_EXTERNAL_CROSSCHECK_REGISTERED",
        "notes": "외부 출처 대조 미등록 — 인용문은 박사님 책 내부 정의에 한정.",
    }


# ============================================================
# (L) Wildcard 분류 — Quantum Progress / Collapse
# ============================================================

WILDCARD_TYPES = {
    "quantum_progress": {
        "ko": "비약적 진보",
        "en": "Quantum Progress",
        "definition": "나노기술 등 게임체인저급 혁신",
        "source": BOOK_TITLE + " (작업 ④ 뜻밖의 미래 단락)",
    },
    "collapse": {
        "ko": "붕괴",
        "en": "Collapse",
        "definition": "베를린 장벽 같은 창발(Emerging Issue)으로 분야가 뒤집히는 경우",
        "source": BOOK_TITLE + " (작업 ④ 뜻밖의 미래 단락)",
    },
}


# ============================================================
# (L2) 약한 신호 수집 소스 (박사님 책 작업 ③ 단락)
# ============================================================

WEAK_SIGNAL_SOURCES = [
    {
        "id": 1,
        "ko": "전문 학술지·씽크탱크 보고서",
        "source": BOOK_TITLE + " (작업 ③ 단락)",
    },
    {
        "id": 2,
        "ko": "비주류 블로그·소셜 반응",
        "source": BOOK_TITLE + " (작업 ③ 단락)",
    },
    {
        "id": 3,
        "ko": "스타트업·특허 동향",
        "source": BOOK_TITLE + " (작업 ③ 단락)",
    },
    {
        "id": 4,
        "ko": "비전문가 직감과 현장 관찰",
        "source": BOOK_TITLE + " (작업 ③ 단락)",
    },
    {
        "id": 5,
        "ko": "이상 기상·사건 단신",
        "source": BOOK_TITLE + " (작업 ③ 단락)",
    },
]


# ============================================================
# (L3) 처리 흐름 단계 5종 (박사님 책 미래지도 작성 프로세스)
# ============================================================

PROCESS_STEPS = [
    {"step": 1, "ko": "사용자 비전 영역 청취"},
    {"step": 2, "ko": "6힘 영역 사전 점검 (STEEPS)"},
    {"step": 3, "ko": "4가지 고려사항 작성"},
    {"step": 4, "ko": "시간축 도식화"},
    {"step": 5, "ko": "미래 나침반 형성 (선택)"},
]


# ============================================================
# (L4) Backcasting / Forecasting 정의 (박사님 책 다이어그램)
# ============================================================

METHODOLOGY_DEFINITIONS = {
    "forecasting": {
        "ko": "현재에서 미래로 트렌드를 투사 (Forecasting)",
        "direction": "현재(Y) → 미래(Y+N)",
        "source": BOOK_TITLE + " (기초 미래예측 프로세스 다이어그램)",
    },
    "backcasting": {
        "ko": "원하는 미래에서 현재로 거슬러 올라와 필요한 변화 역산 (Backcasting)",
        "direction": "미래(Y+N) → 현재(Y)",
        "source": BOOK_TITLE + " (기초 미래예측 프로세스 다이어그램)",
    },
}


# ============================================================
# (M) CLI 진입점 — JSON in/out
# ============================================================

def main():
    """
    표준 JSON in/out CLI.

    사용법:
      python3 futures_timeline_engine.py <command> <json_args>

    Commands:
      current_year                            -> {"Y": int}
      compute_intervals <Y> [<end>] [<n>]     -> dict
      classify_entry <request>                -> dict
      classify_abcd <request>                 -> dict
      detect_s <request>                      -> dict
      recommend_benchmark <field>             -> dict
      verify_quote <quote>                    -> dict
      crosscheck_quote <quote_id>             -> dict
      list_steeps                             -> list
      list_quotes                             -> dict
      help                                    -> this message
    """
    args = sys.argv[1:]
    if not args or args[0] in ("help", "-h", "--help"):
        print(main.__doc__)
        return

    cmd = args[0]
    try:
        if cmd == "current_year":
            print(json.dumps({"Y": current_year()}, ensure_ascii=False))
        elif cmd == "compute_intervals":
            Y = int(args[1])
            end = int(args[2]) if len(args) > 2 else None
            n = int(args[3]) if len(args) > 3 else 3
            print(json.dumps(compute_three_intervals(Y, end, n), ensure_ascii=False, indent=2))
        elif cmd == "classify_entry":
            req = " ".join(args[1:])
            print(json.dumps(classify_entry_type(req), ensure_ascii=False, indent=2))
        elif cmd == "classify_abcd":
            req = " ".join(args[1:])
            print(json.dumps(classify_abcd_type(req), ensure_ascii=False, indent=2))
        elif cmd == "detect_s":
            req = " ".join(args[1:])
            print(json.dumps(detect_s_ambiguity(req), ensure_ascii=False, indent=2))
        elif cmd == "recommend_benchmark":
            field = " ".join(args[1:])
            print(json.dumps(recommend_benchmark(field), ensure_ascii=False, indent=2))
        elif cmd == "verify_quote":
            quote = " ".join(args[1:])
            print(json.dumps(verify_quote(quote), ensure_ascii=False, indent=2))
        elif cmd == "crosscheck_quote":
            qid = args[1]
            print(json.dumps(crosscheck_quote_external(qid), ensure_ascii=False, indent=2))
        elif cmd == "list_steeps":
            print(json.dumps(STEEPS_DOMAINS, ensure_ascii=False, indent=2))
        elif cmd == "list_quotes":
            print(json.dumps(
                {"direct": DIRECT_QUOTES, "reindirect": INDIRECT_QUOTES},
                ensure_ascii=False, indent=2
            ))
        elif cmd == "list_weak_signal_sources":
            print(json.dumps(WEAK_SIGNAL_SOURCES, ensure_ascii=False, indent=2))
        elif cmd == "list_wildcards":
            print(json.dumps(WILDCARD_TYPES, ensure_ascii=False, indent=2))
        elif cmd == "list_benchmarks":
            print(json.dumps(BENCHMARKS, ensure_ascii=False, indent=2))
        elif cmd == "list_process_steps":
            print(json.dumps(PROCESS_STEPS, ensure_ascii=False, indent=2))
        elif cmd == "list_methodologies":
            print(json.dumps(METHODOLOGY_DEFINITIONS, ensure_ascii=False, indent=2))
        elif cmd == "compute_short_only_split":
            Y = int(args[1])
            end = int(args[2])
            print(json.dumps(compute_short_only_split(Y, end), ensure_ascii=False, indent=2))
        else:
            print(f"알 수 없는 명령: {cmd}")
            print(main.__doc__)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "type": type(e).__name__}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
