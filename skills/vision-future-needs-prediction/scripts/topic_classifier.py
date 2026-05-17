#!/usr/bin/env python3
"""
vision-future-needs-prediction — topic_classifier.py

결정론 환원 모듈 1: 주제 키워드 → 추가 집단·영역·고위험 프레이밍 자동 매핑.

LLM이 자연어 추론으로 "기본 집단에 무엇을 추가할지" 결정하는 단계를
결정론적 키워드 매칭으로 환원한다. 출력은 SKILL.md가 정의한 카탈로그를
1:1로 따른다. 키워드 표는 SKILL.md 본문의 카탈로그와 동기화되어야 한다.

사용:
    python3 topic_classifier.py "분석할 주제 한 문장"

출력: JSON
{
  "topic": "...",
  "matched_categories": [...],
  "required_groups_axis1": [...],
  "required_domains_axis3": [...],
  "framing_warnings": [...],
  "time_mode_b_required": bool,
  "time_mode_b_recommended": bool,
  "n_a_threshold_alert": false
}
"""

import json
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# 카탈로그 — SKILL.md "축 1 집단 조정 필수" 및 "축 3 영역 조정 필수" 와 동기화
# ---------------------------------------------------------------------------

TOPIC_CATEGORIES: dict[str, dict[str, Any]] = {
    "cbdc_finance": {
        "keywords": ["cbdc", "디지털화폐", "디지털 화폐", "중앙은행 디지털화폐", "암호화폐", "암호자산", "스테이블코인", "비트코인", "디파이", "defi", "핀테크"],
        "axis1_groups": ["금융기관", "비은행 계층", "암호화폐 투자자"],
        "axis3_domains": ["금융·통화"],
        "framing_warning": "핀테크·암호화폐 — 혁신 낙관론 회피, 금융안정성·투기·사기 위험 명시 의무 (선례: 테라/루나 폭락)",
    },
    "unification_nk": {
        "keywords": ["통일", "북한", "북-한", "탈북", "이산가족", "한반도 통합", "남북"],
        "axis1_groups": ["북한 주민", "탈북민", "이산가족"],
        "axis3_domains": ["안보·외교"],
        "framing_warning": "통일 — 통합 비용·체제 충돌·세대 갈등 균형 필수",
    },
    "ai_religion": {
        "keywords": ["ai 영성", "디지털 종교", "메타교회", "디지털 영성", "ai 목회"],
        "axis1_groups": ["종교기관", "영적 구도자", "세속화 집단"],
        "axis3_domains": ["종교·정신건강"],
        "framing_warning": "AI 영성·디지털 종교 — 전통 신앙 침식 vs 영적 접근성 확대 균형 필수",
    },
    "geopolitics": {
        "keywords": ["지정학", "미중", "공급망", "디커플링", "수출규제", "패권"],
        "axis1_groups": ["수출의존산업", "방위산업", "에너지 기업"],
        "axis3_domains": ["국제통상·기술안보·공급망정책"],
        "framing_warning": None,
    },
    "low_birth": {
        "keywords": ["출산율", "저출산", "출생아", "혼인", "인구절벽"],
        "axis1_groups": ["기혼 가구", "미혼 인구", "여성", "남성"],
        "axis3_domains": [],
        "framing_warning": None,
    },
    "education": {
        "keywords": ["교육", "사교육", "입시", "수능", "대학", "교사", "학원"],
        "axis1_groups": ["입시 의존 학생", "비입시 학생", "교사", "사교육 종사자", "대학"],
        "axis3_domains": ["교육정책·직업훈련·사교육 시장"],
        "framing_warning": None,
    },
    "housing": {
        "keywords": ["부동산", "주거", "전세", "임차", "주택", "월세", "재건축"],
        "axis1_groups": ["자산 보유자", "무주택 청년", "전세 의존 임차인", "다중채무 임대인"],
        "axis3_domains": ["부동산정책·금융안정·도시계획"],
        "framing_warning": "부동산 가격 하락 — 청년 기회 낙관 회피, 금융권 부실·소비 위축 명시 의무",
    },
    "single_household": {
        "keywords": ["1인 가구", "1인가구", "독신", "혼자 사는", "가족 구조", "가족구조"],
        "axis1_groups": ["청년 1인 가구(자발)", "고령 1인 가구(상실·고독)", "이혼자", "돌봄 공백 노출자"],
        "axis3_domains": ["사회복지정책·노후보장·공동주거"],
        "framing_warning": None,
    },
    "aging": {
        "keywords": ["고령화", "노인", "노년", "65세", "은퇴", "실버"],
        "axis1_groups": ["활동 고령자", "의존 고령자", "요양 서비스 종사자", "연금 생활자"],
        "axis3_domains": ["연금·노인 돌봄·의료인력 수급"],
        "framing_warning": "고령화·노인 복지 — 비용 부담 비관 회피, 활동적 노년·시니어 경제 기회 균형 필수",
    },
    "energy_transition": {
        "keywords": ["에너지 전환", "신재생", "재생에너지", "탄소중립", "수소", "탈탄소", "rps", "rec"],
        "axis1_groups": ["화석연료 산업 노동자", "신재생에너지 기업", "에너지 취약계층(저소득·난방비)"],
        "axis3_domains": ["에너지정책·산업전환·노동 재배치"],
        "framing_warning": "수소·신재생에너지 전환 — 탄소중립 낙관 회피, 그린워싱·기술 불확실성·전환 비용 명시 의무",
    },
    "semiconductor_tech": {
        "keywords": ["반도체", "팹리스", "파운드리", "tsmc", "asml", "euv", "기술 패권"],
        "axis1_groups": ["반도체 대기업", "장비·소재 중소기업", "엔지니어 인력"],
        "axis3_domains": ["국제통상·기술안보·공급망정책"],
        "framing_warning": None,
    },
    "agi_automation": {
        "keywords": ["agi", "초인공지능", "자동화", "범용 인공지능", "agi 도래"],
        "axis1_groups": ["사무직 화이트칼라", "전문직(법·의·회계)", "블루칼라 일부", "프롬프트·튜닝 전문가"],
        "axis3_domains": ["법제도·AI 거버넌스"],
        "framing_warning": None,
    },
    "platform_gig": {
        "keywords": ["플랫폼", "긱 이코노미", "긱이코노미", "배달", "라이더", "쿠팡", "우버"],
        "axis1_groups": ["플랫폼 노동자", "전통 자영업", "플랫폼 기업"],
        "axis3_domains": ["노동법·사회보험"],
        "framing_warning": "플랫폼 독점·과점 — 독점 비판 과장 회피, 효율성·편의·고용 창출 균형 필수",
    },
    "climate": {
        "keywords": ["기후위기", "기후 위기", "기후변화", "온실가스", "이상기후"],
        "axis1_groups": ["연안 거주민", "농어업 종사자", "냉방취약 계층"],
        "axis3_domains": ["기후적응·재난관리"],
        "framing_warning": "기후위기 적응 — 비관·위기 과장 회피, 기술 적응 기회·새 산업 창출 균형 필수",
    },
    "esg": {
        "keywords": ["esg", "지속가능성", "지속 가능성", "sustainability"],
        "axis1_groups": ["대기업", "중소기업(부담)", "ESG 평가기관"],
        "axis3_domains": ["기업 거버넌스·공시"],
        "framing_warning": "ESG·지속가능성 — 긍정 프레이밍 회피, 중소기업 부담·산업 경쟁력 약화 명시 의무",
    },
    "remote_work": {
        "keywords": ["원격근무", "재택근무", "디지털 노마드", "워케이션", "하이브리드 근무"],
        "axis1_groups": ["고숙련 화이트칼라", "현장직", "관리자", "오피스 상권"],
        "axis3_domains": ["노동·도시구조"],
        "framing_warning": "원격근무·디지털 노마드 — 자유·균형 낙관 회피, 사회적 고독·계층 격차 명시 의무",
    },
    "digital_divide": {
        "keywords": ["디지털 리터러시", "디지털 격차", "정보격차"],
        "axis1_groups": ["디지털 고령층", "저소득층", "디지털 네이티브"],
        "axis3_domains": ["디지털 포용 정책"],
        "framing_warning": "디지털 리터러시 격차 — 소외 동정 비관 회피, 디지털 선택의 자율성·아날로그 가치 균형 필수",
    },
    "immigration": {
        "keywords": ["다문화", "이민", "외국인 노동자", "난민", "체류"],
        "axis1_groups": ["내국인 노동자", "이주민", "지역 사회", "기업"],
        "axis3_domains": ["이민정책·통합정책"],
        "framing_warning": "다문화·이민 증가 — 포용·다양성 낙관 회피, 사회 갈등·임금 경쟁·문화 충돌 현실 명시 의무",
    },
    "mental_health": {
        "keywords": ["정신건강", "우울", "번아웃", "자살", "정신질환"],
        "axis1_groups": ["청년", "고령 1인 가구", "워킹맘", "정신과 인프라"],
        "axis3_domains": ["정신건강 서비스 체계"],
        "framing_warning": "정신건강 위기 — 위기 비관론 과장 회피, 기술 해법(앱·AI)·제도 개선 기회 균형 필수",
    },
    "space_industry": {
        "keywords": ["우주산업", "민간 우주", "스페이스x", "스타링크", "위성 인터넷"],
        "axis1_groups": ["우주 스타트업", "전통 항공우주 대기업", "통신 사업자"],
        "axis3_domains": ["우주정책·궤도 거버넌스"],
        "framing_warning": "우주산업 민간화 — 미래 낙관론 회피, 기술 불확실성·비용·우주환경 위험 현실 명시 의무",
    },
    "ai_crime": {
        "keywords": ["딥페이크", "ai 범죄", "ai 사기", "보이스피싱 ai", "생성형 ai 범죄"],
        "axis1_groups": ["일반 시민", "기업(평판)", "사법기관"],
        "axis3_domains": ["사이버 범죄·디지털 포렌식"],
        "framing_warning": "AI 범죄·딥페이크 — 피해 감정론 비관 회피, 기술 감지·법제 대응 기회 균형 필수",
    },
    "k_culture": {
        "keywords": ["한류", "k-pop", "k-드라마", "k-콘텐츠", "k-culture"],
        "axis1_groups": ["대형 엔터", "독립 창작자", "K-팬덤", "전통 문화 종사자"],
        "axis3_domains": ["문화산업·창작자 권리"],
        "framing_warning": "한류·K-문화 확산 — 수출·경제 낙관 회피, 전통문화 침식·창작자 착취 구조 명시 의무",
    },
    "metropolitan_decline": {
        "keywords": ["지방소멸", "메가시티", "수도권 집중", "지방 인구"],
        "axis1_groups": ["수도권 거주자", "고령 지방주민(이탈 불가)", "청년 지방주민(이동 선택)"],
        "axis3_domains": ["지방재정·국토계획"],
        "framing_warning": None,
    },
}


# ---------------------------------------------------------------------------
# 시간 범위 → 방식 B 의무·권장 자동 판정 (SKILL.md "분석 도구 — Self-Route" 절)
# ---------------------------------------------------------------------------

TIME_PATTERNS = [
    (re.compile(r"(\d+)\s*년"), "years"),
    (re.compile(r"(\d+)\s*년\s*후"), "years"),
    (re.compile(r"즉각|진행\s*중|현재"), "now"),
]


def detect_time_range_years(topic: str) -> int | None:
    """주제 문자열에서 최대 시간 범위(년)을 추출. 없으면 None."""
    max_years: int | None = None
    for pat, kind in TIME_PATTERNS:
        for m in pat.finditer(topic):
            if kind == "now":
                if max_years is None:
                    max_years = 0
            else:
                try:
                    yr = int(m.group(1))
                    if max_years is None or yr > max_years:
                        max_years = yr
                except (ValueError, IndexError):
                    continue
    return max_years


# ---------------------------------------------------------------------------
# 메인 분류기
# ---------------------------------------------------------------------------


def classify_topic(topic: str) -> dict[str, Any]:
    topic_lower = topic.lower()

    matched: list[str] = []
    required_groups: list[str] = []
    required_domains: list[str] = []
    framing_warnings: list[str] = []

    for cat_id, cat in TOPIC_CATEGORIES.items():
        for kw in cat["keywords"]:
            if kw.lower() in topic_lower:
                matched.append(cat_id)
                for g in cat["axis1_groups"]:
                    if g not in required_groups:
                        required_groups.append(g)
                for d in cat["axis3_domains"]:
                    if d not in required_domains:
                        required_domains.append(d)
                if cat["framing_warning"] and cat["framing_warning"] not in framing_warnings:
                    framing_warnings.append(cat["framing_warning"])
                break

    yrs = detect_time_range_years(topic)
    mode_b_required = yrs is not None and yrs >= 30
    mode_b_recommended = yrs is not None and yrs >= 20

    return {
        "topic": topic,
        "matched_categories": matched,
        "required_groups_axis1": required_groups,
        "required_domains_axis3": required_domains,
        "framing_warnings": framing_warnings,
        "detected_time_years": yrs,
        "time_mode_b_required": mode_b_required,
        "time_mode_b_recommended": mode_b_recommended and not mode_b_required,
        "unmatched_warning": "주제 키워드가 카탈로그와 매칭되지 않음 — 분석가가 직접 집단·영역 추가 결정"
        if not matched
        else None,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: topic_classifier.py '주제 문장'", file=sys.stderr)
        return 1
    topic = " ".join(sys.argv[1:])
    result = classify_topic(topic)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
