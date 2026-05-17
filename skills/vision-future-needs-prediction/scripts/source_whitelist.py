#!/usr/bin/env python3
"""source_whitelist.py — 한국 공식 통계 기관·국제기구·학계 1차 자료 화이트리스트.

산출물의 모든 [출처: 기관명, 연도] 인용은 이 화이트리스트와 1:1 매칭되어야 한다.
화이트리스트에 없는 출처 = 자동 FAIL (할루시네이션·가공 기관명 차단).

화이트리스트는 다음 4계층:
A. 한국 정부·공식 통계 기관 (공신력 1차)
B. 한국 공공 연구원·공단 (공신력 1차)
C. 국제기구·국제 학계 표준 (공신력 1차)
D. 본 스킬 SKILL.md "외부 출처·1차 자료" 표 기재 학계 표준 문헌

화이트리스트 갱신 원칙:
- 새 출처 추가는 *공신력 검증* 후에만 허용
- 학계 일반 기관(대학 명·교수 이름 단독)은 *제목·연도·출판지* 모두 명시 시에만 허용
"""

import re
from typing import Iterable

# ---------------------------------------------------------------------------
# A. 한국 정부 부처·공식 통계 기관
# ---------------------------------------------------------------------------
KOREA_GOVERNMENT = {
    "통계청", "한국은행", "기획재정부", "기재부",
    "보건복지부", "복지부", "고용노동부", "고용부", "노동부",
    "농림축산식품부", "농림부", "교육부", "환경부",
    "국토교통부", "국토부", "행정안전부", "행안부",
    "여성가족부", "여가부", "통일부", "산업통상자원부", "산업부",
    "금융위원회", "금융위", "공정거래위원회", "공정위",
    "방송통신위원회", "방통위", "과학기술정보통신부", "과기정통부",
    "외교부", "법무부", "국방부", "문화체육관광부", "문체부",
    "해양수산부", "중소벤처기업부", "중기부",
    "감사원", "국세청", "관세청", "병무청",
    "기상청", "질병관리청", "질병청", "산림청", "농촌진흥청",
}

# ---------------------------------------------------------------------------
# B. 한국 공공 연구원·공단·공공기관
# ---------------------------------------------------------------------------
KOREA_PUBLIC_INSTITUTES = {
    "한국개발연구원", "KDI",
    "한국노동연구원", "노동연구원",
    "보건사회연구원", "보사연",
    "농촌경제연구원",
    "산업연구원",
    "통일연구원",
    "국민연금연구원",
    "한국금융연구원", "금융연구원",
    "정보통신정책연구원", "KISDI",
    "국토연구원",
    "한국개발연구원 KDI",
    "한국교육개발원", "KEDI",
    "한국직업능력연구원",
    "한국조세재정연구원",
    "에너지경제연구원",
    "한국행정연구원",
    "국방연구원", "KIDA",
    "외교안보연구원",
    "대외경제정책연구원", "KIEP",
    "한국환경연구원",
    "한국형사·법무정책연구원", "형사정책연구원",
    "국민건강보험공단", "건강보험공단",
    "국민연금공단",
    "주택금융공사",
    "주택도시보증공사", "HUG",
    "안전보건공단",
    "한국토지주택공사", "LH",
    "한국전력공사", "한전",
    "한국가스공사",
    "근로복지공단",
    "한국갤럽", "갤럽",
    "한국정보화진흥원", "NIA",
    "서울시", "서울특별시", "경기도", "부산시", "대구시", "인천시",
    "광주시", "대전시", "울산시", "세종시", "제주도",
    "대한의사협회", "의협", "대한간호협회", "간협",
    "대한변호사협회", "변협", "대한치과의사협회",
    "대한신경정신의학회", "정신건강의학회", "신경정신의학회",
    "대한내과학회", "대한외과학회", "대한가정의학회",
    "한국심리학회", "한국사회학회", "한국정치학회", "한국경제학회",
    "한국경영학회", "한국교육학회",
}

# ---------------------------------------------------------------------------
# C. 국제기구·국제 표준
# ---------------------------------------------------------------------------
INTERNATIONAL = {
    "OECD", "IMF", "World Bank", "WB", "UN", "United Nations",
    "WHO", "IPCC", "BIS", "IEA", "FAO", "ILO", "UNICEF", "UNESCO",
    "WTO", "IAEA", "WEF", "World Economic Forum",
    "European Commission", "EC", "Eurostat",
}

# ---------------------------------------------------------------------------
# D. 학계 표준 문헌 (SKILL.md "외부 출처·1차 자료" 표 기재 + 미래학·통계 표준)
# ---------------------------------------------------------------------------
ACADEMIC_LITERATURE = {
    "Aguilar", "Maslow", "Bell", "Hines", "Bishop", "Hines & Bishop",
    "Inayatullah", "Voros", "Gordon", "Glenn", "Glenn & Gordon",
    "Fahey", "Narayanan", "Fahey & Narayanan", "Slaughter",
    "Brown", "Millennium Project", "RAND", "Shell",
    "Pew Research", "Gartner", "McKinsey", "BCG", "Deloitte",
    "한국기독교사회문제연구원", "한국기독교목회자협의회",
    "신학연구원", "한국신학회",
}

# ---------------------------------------------------------------------------
# 통합 화이트리스트
# ---------------------------------------------------------------------------
ALL_SOURCES: set[str] = (
    KOREA_GOVERNMENT | KOREA_PUBLIC_INSTITUTES | INTERNATIONAL | ACADEMIC_LITERATURE
)

# ---------------------------------------------------------------------------
# 정규식
# ---------------------------------------------------------------------------
CITATION_PATTERN = re.compile(r"\[출처:\s*([^\]]+?)\]")

# 가공 기관명 의심 패턴 (실재하지 않을 가능성 높은 단어 조합)
SUSPICIOUS_PATTERN = re.compile(
    r"한국[가-힣]*미래[가-힣]*연구소|"
    r"미래[가-힣]+학회(?!\s|$)|"
    r"가상[가-힣]+연구원|"
    r"미상의|"
    r"some\s*research|"
    r"a\s*study\s*shows"
)


def extract_citations(text: str) -> list[str]:
    """본문에서 [출처:...] 인용을 모두 추출."""
    return [m.group(1).strip() for m in CITATION_PATTERN.finditer(text)]


def normalize_source(citation: str) -> str:
    """인용에서 기관명만 추출(연도·보고서명 제외)."""
    # "통계청 인구추계, 2024" → "통계청"
    # "기관명 보고, 2024" → "기관명"
    # 콤마 전까지 잘라낸 뒤 공백 분리하여 첫 토큰·전체 토큰 조합 시도
    head = citation.split(",")[0].strip()
    head = re.sub(r"\s+\d{4}년?$", "", head).strip()
    return head


def is_whitelisted(citation: str) -> tuple[bool, str]:
    """인용이 화이트리스트에 매칭되는지 검사.

    Return: (PASS여부, 매칭된 화이트리스트 항목 또는 사유)
    """
    if SUSPICIOUS_PATTERN.search(citation):
        return False, "의심 패턴(가공 기관명 가능)"

    head = normalize_source(citation)
    # 정확 매칭
    if head in ALL_SOURCES:
        return True, head
    # 부분 매칭(앞쪽 토큰 포함)
    for src in ALL_SOURCES:
        if src in citation or src in head:
            return True, src
    return False, "화이트리스트 미매칭"


def audit(text: str) -> dict:
    """본문의 모든 인용을 감사."""
    citations = extract_citations(text)
    results = []
    pass_count = 0
    for c in citations:
        ok, matched = is_whitelisted(c)
        results.append({"citation": c, "pass": ok, "matched": matched})
        if ok:
            pass_count += 1
    return {
        "total_citations": len(citations),
        "passed": pass_count,
        "failed": len(citations) - pass_count,
        "results": results,
    }


if __name__ == "__main__":
    import json
    import sys

    text = sys.stdin.read() if len(sys.argv) < 2 else open(sys.argv[1], encoding="utf-8").read()
    print(json.dumps(audit(text), ensure_ascii=False, indent=2))
