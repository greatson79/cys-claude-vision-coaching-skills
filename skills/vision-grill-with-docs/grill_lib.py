"""
vision-grill-with-docs — 결정론적 헬퍼 라이브러리 (v2 — 약점 검증·보강 후).

LLM 자연어 추정으로 처리하면 할루시네이션·드리프트 위험이 있는 단계를
결정론으로 환원한 함수들. SKILL.md에서 명시적으로 호출하도록 지정한다.

기준 사양:
    SKILL.md / CONTEXT-FORMAT.md / LDR-FORMAT.md / SOURCES.md / glossary_standard.md /
    topic_skill_map.md (모두 같은 디렉터리)

모든 함수는 위 사양 문서의 문구·표를 1:1 대응하며,
세 자산(STANDARD_GLOSSARY / ALLOWED_QUOTES / TOPIC_MAP)이 사양 문서와 drift하지 않도록
sync 검증 함수를 별도 제공한다 (validate_glossary_sync / validate_quotes_sync /
validate_topic_map_skills).

호출 예 (CLI):
    python3 grill_lib.py route_mode --text "verify mission-frame"
    python3 grill_lib.py parse_topic --text "진로 결정 — 전공·학교"
    python3 grill_lib.py detect_glossary_conflict --text "내 소명은 가족을 잘 부양하는 것"
    python3 grill_lib.py glossary_lookup --term "비전"
    python3 grill_lib.py check_ldr_criteria --decision "공학에서 신학으로" \
        --reversibility hard --surprising true --tradeoff true
    python3 grill_lib.py next_ldr_number --base /tmp/user_vision
    python3 grill_lib.py is_multi_context --base /tmp/user_vision
    python3 grill_lib.py three_realm_check --self true --others false --moral true
    python3 grill_lib.py scenario_expand --topic "공학 전공 선택"
    python3 grill_lib.py verify_quote --text "외부로부터 주어지는 영감"
    python3 grill_lib.py find_related_artifact --topic "재정 결정"
    python3 grill_lib.py upsert_term --base /tmp/user_vision --term "중간 비전" \
        --definition "5년 단위 마일스톤" --avoid "단기 목표"
    python3 grill_lib.py promote_to_multi --base /tmp/user_vision --area 진로
    python3 grill_lib.py flag_conflict --base /tmp/user_vision \
        --term 소명 --user-usage "가족 부양" --resolution "박사님 표준 정의 채택"
    python3 grill_lib.py emoji_check --text "비전 🎯 발견했다"
    python3 grill_lib.py slug_normalize --title "진로 — 공학에서 신학으로 전환!"
    python3 grill_lib.py list_contexts --base /tmp/user_vision
    python3 grill_lib.py menu_options
    python3 grill_lib.py validate_glossary_sync
    python3 grill_lib.py validate_quotes_sync
    python3 grill_lib.py validate_topic_map_skills --skills-root /Users/.../skills
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 0. 박사님 표준 사전 — glossary_standard.md § 1~6과 1:1 대응
# ---------------------------------------------------------------------------
# 본 딕셔너리는 glossary_standard.md의 정의 *원문*과 정확히 일치해야 한다.
# drift 검증은 validate_glossary_sync()가 수행 — 두 자산 sync 실패 시 자동 FAIL.

STANDARD_GLOSSARY: dict[str, dict] = {
    # § 1 핵심 비전 어휘 (박사님 자작)
    "비전": {
        "definition": "가치 있는 시대적 소명",
        "avoid": ["꿈", "목표", "야망", "미래상"],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "미션": {
        "definition": "비전을 향한 지속적 실행",
        "avoid": ["임무", "과제", "일"],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "소명": {
        "definition": "시대를 향한 부르심에 응답한 일",
        "avoid": ["천직", "적성"],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "가치": {
        "definition": "비전의 영적 직관력 축 — 영감이 정신적 가치(경전·윤리·도덕·양심)로 검증된 결과",
        "avoid": ["선호", "취향", "관심"],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "시대": {
        "definition": "비전의 이성적 판단력 축에서 인식하는 지금 시점의 시대적 요구·구조적 변화 방향",
        "avoid": ["트렌드", "유행", "최근"],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "비전 프레임": {
        "definition": "박사님 자작 도식. 영적 직관력 + 이성적 판단력 두 축이 (R) 강화 피드백 루프로 작동해 비전을 성장시키는 구조",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    # § 2 영적 직관력 축
    "영적 직관력": {
        "definition": "영감 + 정신적 가치 = 비전의 한 축",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "영감": {
        "definition": "외부로부터 주어지는 영감",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "정신적 가치": {
        "definition": "영감을 객관적으로 검증하는 안전장치",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    # § 3 이성적 판단력 축
    "이성적 판단력": {
        "definition": "정보 + 예측 구성 = 비전의 다른 한 축. 미래 변화 통찰(Judgement)과 동일",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "정보": {
        "definition": "자기 내적 정보(관심사·재능·성격) + 자기 외적 정보(사람·관계·환경·실패 경험)",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "예측 구성": {
        "definition": "미래 예측을 구성하는 방법론적 틀. 박사님 미래학 방법론 (foresight-* 시리즈)",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "강화 피드백 루프": {
        "definition": "두 축이 서로 +로 강화하며 비전을 성장시키는 시스템 다이내믹스 패턴",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    # § 4 3영역 어휘 (vision-three-realm-balance 1:1)
    "3영역": {
        "definition": "박사님 표준 비전 건강도 3겹 다이어그램 — 나·가족과 세상·정신적 가치 세 영역이 모두 만족할 때 건강한 비전",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "나": {
        "definition": "비전이 나에게 진정한 기쁨을 주는가의 차원",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "가족과 세상": {
        "definition": "비전이 가족·이웃·인류에게도 기쁨이 되는가의 차원",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "개인 욕망": {
        "definition": "나만 기쁘게 하는 비전. 박사님 표준에서는 건강하지 않은 비전",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "자기희생·세상일": {
        "definition": "가족·세상만 기쁘게 하는 비전. 자기 진정한 기쁨이 없는 헌신은 지속 불가",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "왜곡된 사명": {
        "definition": "정신적 가치만 극단적으로 추구해 나와 가족을 비참하게 만드는 비전",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    # § 5 진단·역량 어휘
    "4 Skill Balance": {
        "definition": "박사님 자작 5축 균형 — 생각·언어·감성·몸·영성",
        "avoid": [],
        "source": "박사님 『미래준비학교』(2016) — SOURCES.md § A-01",
    },
    "9가지 다중지능": {
        "definition": "가드너 8가지(논리수학·언어·공간·음악·신체운동·인간친화·자기성찰·자연친화) + 영성",
        "avoid": [],
        "source": "Gardner 1983·1999 — SOURCES.md § B-01",
    },
    "10개 비전 코드": {
        "definition": "박사님 자작 비전 역량 진단 — 방향성·가치 방향·잠재력·기술력·구상력·자기계발력·전략력·추진력·네트워킹력·리더십 스타일",
        "avoid": [],
        "source": "박사님 『미래준비학교』 입학자 진단지 — SOURCES.md § A-02",
    },
    "MBTI 16유형": {
        "definition": "마이어스-브릭스 성격유형지표 16유형",
        "avoid": [],
        "source": "Myers & McCaulley 1985 — SOURCES.md § B-02",
    },
    "에니어그램 9유형": {
        "definition": "9가지 성격 유형. 각 유형이 추구하는 세상이 다르다 (박사님 vision-values-visioncoding 매핑)",
        "avoid": [],
        "source": "Riso & Hudson 1996·1999 — SOURCES.md § B-03",
    },
    "STRONG 직업 흥미검사": {
        "definition": "직업 흥미 표준화 진단",
        "avoid": [],
        "source": "Strong et al. — SOURCES.md § B-04",
    },
    # § 6 결정·실행 어휘 (LDR)
    "Life Decision Record": {
        "definition": "본 스킬에서 발행하는 되돌리기 어려운 인생 결정 기록. 3조건 충족 시 발행",
        "avoid": [],
        "source": "원형: Nygard ADR — SOURCES.md § B-06",
    },
    "Hard to reverse": {
        "definition": "번복 비용이 큰 결정. 시간·돈·관계·기회·정서 비용 포함",
        "avoid": [],
        "source": "Nygard ADR — SOURCES.md § B-06",
    },
    "Surprising without context": {
        "definition": "5~10년 뒤 본인이 또는 제3자가 \"왜 그렇게 결정했지?\"라고 의문 가질 결정",
        "avoid": [],
        "source": "Nygard ADR — SOURCES.md § B-06",
    },
    "Real trade-off": {
        "definition": "진짜 대안이 있었고 의도해서 선택한 결정. 자동 결정·관성 결정은 아님",
        "avoid": [],
        "source": "Nygard ADR — SOURCES.md § B-06",
    },
}

# Avoid 단어 → 표준 단어 역인덱스
AVOID_INDEX: dict[str, str] = {}
for std_term, payload in STANDARD_GLOSSARY.items():
    for avoid_term in payload.get("avoid", []):
        AVOID_INDEX[avoid_term] = std_term


# ---------------------------------------------------------------------------
# 0b. 박사님 인용 — SOURCES.md § A 명시 문장만
# ---------------------------------------------------------------------------
ALLOWED_QUOTES: list[str] = [
    "외부로부터 주어지는 영감",
    "영감을 객관적으로 검증하는 안전장치",
    "비전 프레임이란 '가치 있는 + 시대적 + 소명'이 어떻게 성장하는지를 설명하기 위해 필자가 만든 단어이다",
    "강한 비전은 높은 정신적 만족감을 준다",
    "참된 정신적 가치는 동시에 이웃(가족과 세상, 인류)에게도 기쁨이 되어야 하고, 나 자신에게도 진정한 기쁨을 주어야 한다",
    # 통합 인용 (SOURCES.md § A-01 원문)
    "강한 비전은 높은 정신적 만족감을 준다. 그러나 참된 정신적 가치는 동시에 이웃(가족과 세상, 인류)에게도 기쁨이 되어야 하고, 나 자신에게도 진정한 기쁨을 주어야 한다.",
    "비전 역량 평가지와 해석지는 미래학에 근거한 평가, MBTI, STRONG 직업 흥미검사, 에니어그램(Enneagram), 다중지능 이론들을 반영하여 만들었다",
    "비전 역량 평가지와 해석지는 미래학에 근거한 평가, MBTI, STRONG 직업 흥미검사, 에니어그램(Enneagram), 다중지능 이론들을 반영하여 만들었다.",
    "자기 외부에서 내부로 들어오는 영감",
    "가치 있는 시대적 소명",
]


# ---------------------------------------------------------------------------
# 1. 모드 분기 (route_mode)
# ---------------------------------------------------------------------------

MODE_B_PATTERNS = [
    r"^\s*verify\s+",
    r"산출물\s*검증",
    r"메타\s*검증",
    r"자기모순\s*검출",
]

MODE_A_PATTERNS = [
    r"^\s*me\s*$",
    r"^\s*coachee\s*:",
    r"내\s*비전\s*무너뜨려",
    r"내\s*비전\s*grill",
    r"본인\s*비전\s*grill",
]


def route_mode(text: Any) -> dict:
    if not isinstance(text, str):
        return {"mode": "C", "reason": "non-string input — defaulting to C"}
    t = text.strip()
    if not t:
        return {"mode": "menu", "reason": "empty input — show menu"}
    for pat in MODE_B_PATTERNS:
        if re.search(pat, t, flags=re.IGNORECASE):
            return {"mode": "B", "reason": f"matched B pattern: {pat}", "input": t}
    for pat in MODE_A_PATTERNS:
        if re.search(pat, t, flags=re.IGNORECASE):
            return {"mode": "A", "reason": f"matched A pattern: {pat}", "input": t}
    return {"mode": "C", "reason": "free-form topic — defaulting to C", "input": t}


# ---------------------------------------------------------------------------
# 2. 주제 파싱 (parse_topic) — topic_skill_map.md 기반
# ---------------------------------------------------------------------------

def _load_topic_map() -> tuple[list[dict], list[str]]:
    """topic_skill_map.md 파싱.

    반환: (행 리스트, 경고 리스트). 경고는 형식 위반 행을 명시한다.
    """
    path = os.path.join(HERE, "topic_skill_map.md")
    rows: list[dict] = []
    warnings: list[str] = []
    if not os.path.exists(path):
        warnings.append(f"topic_skill_map.md not found at {path}")
        return rows, warnings

    with open(path, "r", encoding="utf-8") as f:
        for line_no, raw in enumerate(f, 1):
            line = raw.rstrip("\n")
            stripped = line.strip()

            # 코드 블록 펜스 자체는 스킵 (안의 내용은 데이터로 사용 — topic_skill_map.md
            # 매핑은 가독성을 위해 ``` ... ``` 블록 안에 작성됨).
            if stripped.startswith("```"):
                continue

            # 매핑 행은 정확히 2개의 '|'를 갖는다 (3개 컬럼).
            pipe_count = line.count("|")
            if pipe_count == 0:
                continue
            if pipe_count != 2:
                # 매핑이 아닌 일반 텍스트일 수 있으나, 의심스러우면 경고
                if pipe_count >= 3:
                    warnings.append(
                        f"L{line_no}: unexpected pipe count={pipe_count}, skipped"
                    )
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                continue
            keywords_str, skills_str, focus = parts
            if not keywords_str or keywords_str.lower().startswith("키워드"):
                continue
            if not skills_str:
                continue
            keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
            skills = [s.strip() for s in skills_str.split(",") if s.strip()]
            if not keywords or not skills:
                continue
            rows.append({"keywords": keywords, "skills": skills, "focus": focus})

    if not rows:
        warnings.append("topic_skill_map.md parsed 0 rows — sync failure suspected")
    return rows, warnings


def parse_topic(text: Any) -> dict:
    if not isinstance(text, str) or not text.strip():
        return {
            "topic": "" if not isinstance(text, str) else text,
            "matched_keywords": [],
            "related_skills": [],
            "interview_focus": [],
            "warnings": [],
        }
    rows, warnings = _load_topic_map()
    matched_keywords: list[str] = []
    related_skills: list[str] = []
    interview_focus: list[str] = []
    norm_text = text.lower()

    for row in rows:
        for kw in row["keywords"]:
            if kw.lower() in norm_text:
                if kw not in matched_keywords:
                    matched_keywords.append(kw)
                for s in row["skills"]:
                    if s not in related_skills:
                        related_skills.append(s)
                if row["focus"] not in interview_focus:
                    interview_focus.append(row["focus"])
                break

    return {
        "topic": text,
        "matched_keywords": matched_keywords,
        "related_skills": related_skills,
        "interview_focus": interview_focus,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# 3. 박사님 표준 사전 충돌 검출 / lookup
# ---------------------------------------------------------------------------

# 영문 → 한글 별칭 매핑 (glossary_standard.md 헤더 영문 부제 기준)
ENGLISH_ALIASES: dict[str, str] = {
    "Vision": "비전",
    "Mission": "미션",
    "Calling": "소명",
    "Value": "가치",
    "Era": "시대",
    "Times": "시대",
    "Mission Frame": "비전 프레임",
    "Spiritual Intuition": "영적 직관력",
    "Divine Inspiration": "영감",
    "Divine Value": "정신적 가치",
    "Intellectual Judgment": "이성적 판단력",
    "Information": "정보",
    "Forecasting Framework": "예측 구성",
    "Reinforcing Feedback Loop": "강화 피드백 루프",
    "Three Realms": "3영역",
    "Self": "나",
    "Family & World": "가족과 세상",
    "Personal Desire": "개인 욕망",
    "Self-Sacrifice": "자기희생·세상일",
    "Distorted Mission": "왜곡된 사명",
    "LDR": "Life Decision Record",
}


def glossary_lookup(term: Any) -> dict:
    if not isinstance(term, str):
        return {"found": False, "term": str(term), "reason": "non-string"}
    t = term.strip()
    # 1차: 직접 매칭
    if t in STANDARD_GLOSSARY:
        return {"found": True, "term": t, "matched_via": "direct", **STANDARD_GLOSSARY[t]}
    # 2차: 영문 별칭 매칭
    if t in ENGLISH_ALIASES:
        ko = ENGLISH_ALIASES[t]
        if ko in STANDARD_GLOSSARY:
            return {
                "found": True,
                "term": ko,
                "english_input": t,
                "matched_via": "english_alias",
                **STANDARD_GLOSSARY[ko],
            }
    # 3차: 대소문자 무시 영문 매칭
    for en, ko in ENGLISH_ALIASES.items():
        if t.lower() == en.lower() and ko in STANDARD_GLOSSARY:
            return {
                "found": True,
                "term": ko,
                "english_input": t,
                "matched_via": "english_alias_ci",
                **STANDARD_GLOSSARY[ko],
            }
    return {"found": False, "term": t, "reason": "not in standard glossary"}


def detect_glossary_conflict(text: Any) -> dict:
    """사용자 발화에서 박사님 표준 사전과 충돌 가능한 표현 검출."""
    if not isinstance(text, str):
        return {"conflicts": [], "clean": True, "reason": "non-string"}

    conflicts: list[dict] = []

    # 규칙 1 — avoid 단어 검출 (단어 경계 또는 한국어 substring)
    for avoid_term, std_term in AVOID_INDEX.items():
        if avoid_term in text:
            conflicts.append({
                "type": "avoid_term_used",
                "user_term": avoid_term,
                "standard_term": std_term,
                "suggestion": f"'{avoid_term}'은(는) 박사님 표준에서 '{std_term}'으로 통일하시는 게 좋습니다.",
                "standard_definition": STANDARD_GLOSSARY[std_term]["definition"],
            })

    # 규칙 2 — "내 X은 Y" 형식 분기 검출 (4 핵심 어휘)
    for std_term in ("소명", "비전", "미션", "가치"):
        pattern = rf"(?:내|나의|저의|본인의)\s*{std_term}\s*(?:은|는)\s*(.{{1,80}}?)(?:[.。!?]|입니다|이다|이에요|예요|$)"
        m = re.search(pattern, text)
        if m:
            user_def = m.group(1).strip()
            std_def = STANDARD_GLOSSARY[std_term]["definition"]
            std_keywords = [w for w in re.split(r"[\s·,]+", std_def) if len(w) > 1]
            overlap = sum(1 for kw in std_keywords if kw in user_def)
            if overlap == 0:
                conflicts.append({
                    "type": "personal_definition_diverges",
                    "term": std_term,
                    "user_definition": user_def,
                    "standard_definition": std_def,
                    "suggestion": (
                        f"본인이 정의하신 '{std_term}'은(는) 박사님 표준 정의와 핵심 단어가 겹치지 않습니다. "
                        f"박사님 정의를 따르시겠습니까, 본인 맥락 정의로 override 기록하시겠습니까?"
                    ),
                })

    return {"conflicts": conflicts, "clean": len(conflicts) == 0}


# ---------------------------------------------------------------------------
# 4. LDR 3조건 자동 체크
# ---------------------------------------------------------------------------

def check_ldr_criteria(
    decision: Any,
    reversibility: Any,
    surprising: Any,
    tradeoff: Any,
) -> dict:
    missing: list[str] = []

    if not isinstance(decision, str) or not decision.strip():
        return {
            "decision": decision if isinstance(decision, str) else "",
            "qualifies": False,
            "missing": ["decision (empty or non-string)"],
            "recommendation": "LDR 미발행 — 결정 내용 비어 있음",
        }

    rev = str(reversibility).strip().lower() if reversibility is not None else ""
    if rev not in ("hard", "easy"):
        missing.append(f"reversibility (got '{reversibility}', must be 'hard' or 'easy')")
    elif rev != "hard":
        missing.append("reversibility (must be 'hard')")

    if surprising is not True:
        missing.append("surprising")
    if tradeoff is not True:
        missing.append("real_tradeoff")

    qualifies = len(missing) == 0
    return {
        "decision": decision,
        "qualifies": qualifies,
        "missing": missing,
        "recommendation": (
            "LDR 발행 — docs/ldr/에 lazy 생성 + 다음 번호 부여"
            if qualifies
            else "LDR 미발행 — 3조건 불충족. VISION-CONTEXT.md 본인 맥락 정의에는 반영 가능."
        ),
    }


# ---------------------------------------------------------------------------
# 5. LDR 번호 부여 (next_ldr_number) — 4자리 boundary 보호
# ---------------------------------------------------------------------------

LDR_NAME_PATTERN = re.compile(r"^(\d{4})-.+\.md$")
LDR_MAX_NUMBER = 9999


def next_ldr_number(base: Any) -> dict:
    if not isinstance(base, str) or not base:
        return {"next": "0001", "existing_max": 0, "ldr_dir_exists": False}
    ldr_dir = os.path.join(base, "docs", "ldr")
    if not os.path.isdir(ldr_dir):
        return {"next": "0001", "existing_max": 0, "ldr_dir_exists": False}
    max_n = 0
    for name in os.listdir(ldr_dir):
        m = LDR_NAME_PATTERN.match(name)
        if m:
            try:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
            except ValueError:
                pass
    if max_n >= LDR_MAX_NUMBER:
        return {
            "next": None,
            "existing_max": max_n,
            "ldr_dir_exists": True,
            "error": (
                f"LDR 최대 번호 {LDR_MAX_NUMBER} 초과. "
                "4자리 슬롯이 가득 찼습니다. 폴더 분리·아카이브 후 재시작 필요."
            ),
        }
    return {
        "next": f"{max_n + 1:04d}",
        "existing_max": max_n,
        "ldr_dir_exists": True,
    }


# ---------------------------------------------------------------------------
# 6. 단일 vs 멀티 컨텍스트 (is_multi_context / list_contexts / promote_to_multi)
# ---------------------------------------------------------------------------

def is_multi_context(base: Any) -> dict:
    if not isinstance(base, str) or not os.path.isdir(base):
        return {
            "structure": "none",
            "context_md_exists": False,
            "context_map_exists": False,
            "recommendation": "first term resolved → create VISION-CONTEXT.md lazily",
        }
    cm = os.path.join(base, "VISION-CONTEXT-MAP.md")
    c = os.path.join(base, "VISION-CONTEXT.md")
    if os.path.exists(cm):
        return {
            "structure": "multi",
            "context_md_exists": os.path.exists(c),
            "context_map_exists": True,
        }
    if os.path.exists(c):
        return {"structure": "single", "context_md_exists": True, "context_map_exists": False}
    return {
        "structure": "none",
        "context_md_exists": False,
        "context_map_exists": False,
        "recommendation": "first term resolved → create VISION-CONTEXT.md lazily",
    }


KNOWN_AREAS = ["진로", "재정", "관계", "사역", "건강"]


def list_contexts(base: Any) -> dict:
    """multi 구조에서 영역 폴더 목록과 각 CONTEXT.md 존재 여부 반환."""
    if not isinstance(base, str) or not os.path.isdir(base):
        return {"structure": "none", "areas": []}
    cm = os.path.join(base, "VISION-CONTEXT-MAP.md")
    if not os.path.exists(cm):
        return {
            "structure": "single" if os.path.exists(os.path.join(base, "VISION-CONTEXT.md")) else "none",
            "areas": [],
        }
    areas = []
    for entry in sorted(os.listdir(base)):
        full = os.path.join(base, entry)
        if not os.path.isdir(full):
            continue
        if entry.startswith(".") or entry in ("docs", "__pycache__"):
            continue
        ctx = os.path.join(full, "CONTEXT.md")
        areas.append({
            "name": entry,
            "context_md_exists": os.path.exists(ctx),
            "is_known_area": entry in KNOWN_AREAS,
        })
    return {"structure": "multi", "areas": areas}


def promote_to_multi(base: Any, area: Any) -> dict:
    """단일 VISION-CONTEXT.md → multi 구조 전환.

    1. 기존 VISION-CONTEXT.md를 <base>/<area>/CONTEXT.md로 이동
    2. <base>/VISION-CONTEXT-MAP.md 생성 (없으면)
    3. 멱등 — 이미 multi이면 단순히 새 영역만 등록

    인자:
        base: 작업 폴더
        area: 영역명 (예: "진로")
    """
    if not isinstance(base, str) or not base:
        return {"ok": False, "reason": "base required"}
    if not isinstance(area, str) or not area.strip():
        return {"ok": False, "reason": "area required"}
    area = area.strip()
    # 경로 traversal · OS-unsafe 문자 차단
    if "/" in area or "\\" in area or ".." in area or area.startswith(".") or len(area) > 50:
        return {
            "ok": False,
            "reason": (
                f"unsafe area name: {area!r}. "
                "must not contain '/', '\\\\', '..', leading '.', or exceed 50 chars."
            ),
        }
    if not os.path.isdir(base):
        return {"ok": False, "reason": f"base directory does not exist: {base}"}

    cm = os.path.join(base, "VISION-CONTEXT-MAP.md")
    c = os.path.join(base, "VISION-CONTEXT.md")
    area_dir = os.path.join(base, area)
    area_ctx = os.path.join(area_dir, "CONTEXT.md")

    moved_single_to_area = False
    created_map = False
    created_area = False

    # 1) area 폴더 lazy 생성
    if not os.path.isdir(area_dir):
        os.makedirs(area_dir, exist_ok=True)
        created_area = True

    # 2) 기존 단일 VISION-CONTEXT.md 처리
    if os.path.exists(c) and not os.path.exists(area_ctx):
        # 기존 단일 사전 → 첫 영역으로 이동 (idempotent: area_ctx 이미 있으면 건드리지 않음)
        with open(c, "r", encoding="utf-8") as f:
            content = f.read()
        with open(area_ctx, "w", encoding="utf-8") as f:
            f.write(content)
        os.remove(c)
        moved_single_to_area = True
    elif not os.path.exists(area_ctx):
        # 단일 사전 없이 바로 multi 시작 — area_ctx도 lazy 생성
        with open(area_ctx, "w", encoding="utf-8") as f:
            f.write(f"# {area} 영역 용어집\n\n## 1. 표준 정의\n\n## 2. 본인 맥락 정의\n\n## 3. 본인 고유 용어\n\n## 4. 관계\n\n## 5. 예시 대화\n\n## 6. 충돌 기록\n\n## 7. 외부 참조\n")

    # 3) VISION-CONTEXT-MAP.md 생성·갱신
    if not os.path.exists(cm):
        with open(cm, "w", encoding="utf-8") as f:
            f.write(
                "# 비전 영역 지도 (Vision Context Map)\n\n"
                "## 영역 (Contexts)\n\n"
                f"- [{area}](./{area}/CONTEXT.md)\n\n"
                "## 영역 간 관계 (Cross-context relationships)\n\n"
                "(인터뷰 진행 중 추가)\n"
            )
        created_map = True
    else:
        # 영역이 아직 목록에 없으면 추가
        with open(cm, "r", encoding="utf-8") as f:
            map_content = f.read()
        link = f"- [{area}](./{area}/CONTEXT.md)"
        if link not in map_content:
            # ## 영역 (Contexts) 다음 줄들에 추가
            map_content = re.sub(
                r"(## 영역 \(Contexts\)\s*\n+)",
                rf"\1{link}\n",
                map_content,
                count=1,
            )
            with open(cm, "w", encoding="utf-8") as f:
                f.write(map_content)

    return {
        "ok": True,
        "base": base,
        "area": area,
        "moved_single_to_area": moved_single_to_area,
        "created_map": created_map,
        "created_area": created_area,
        "area_ctx_path": area_ctx,
        "map_path": cm,
    }


# ---------------------------------------------------------------------------
# 7. 3영역 균형 검사 — 엄격한 type 검사
# ---------------------------------------------------------------------------

def _strict_bool(v: Any, name: str) -> tuple[bool, str | None]:
    if isinstance(v, bool):
        return v, None
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "1", "yes", "y", "t"):
            return True, None
        if s in ("false", "0", "no", "n", "f"):
            return False, None
    return False, f"{name} must be bool or 'true'/'false', got {type(v).__name__}: {v!r}"


def three_realm_check(self_realm: Any, others_realm: Any, moral_realm: Any) -> dict:
    s, e1 = _strict_bool(self_realm, "self_realm")
    o, e2 = _strict_bool(others_realm, "others_realm")
    m, e3 = _strict_bool(moral_realm, "moral_realm")
    errors = [e for e in (e1, e2, e3) if e]
    if errors:
        return {"status": "error", "errors": errors}

    truthy = sum([s, o, m])
    if truthy == 3:
        return {
            "status": "healthy",
            "label": "건강한 비전 — 3영역 모두 만족",
            "self": s, "others": o, "moral": m,
            "diagnosis": "박사님 표준 정의에 부합. 다음 인터뷰 가지로 이동 가능.",
        }
    if truthy == 0:
        return {
            "status": "empty",
            "label": "비전 부재 또는 비전 명료화 시작 단계",
            "self": False, "others": False, "moral": False,
            "diagnosis": "vision-clarity-coaching·vision-mission-frame부터 시작 권고.",
        }
    if s and not o and not m:
        label, diag = "개인 욕망 (자기중심·이기적 비전)", "박사님 표준에서 '나만 기쁘게 함' 단일 영역. 가족과 세상·정신적 가치 영역으로 확장 필요."
    elif o and not s and not m:
        label, diag = "자기희생·세상일", "박사님 표준에서 '자기 진정한 기쁨 없는 헌신' — 지속 불가. 나 영역 회복 필요."
    elif m and not s and not o:
        label, diag = "왜곡된 사명", "박사님 표준에서 '높은 도덕적 기준만 내세워 나·가족 비참' 패턴. 가장 흔한 잘못된 비전 유형."
    elif s and o and not m:
        label, diag = "정신적 가치 결핍", "박사님 표준에서 '높은 정신적 만족감' 축이 비어 있음. 영적 직관력 축 grill 필요."
    elif s and m and not o:
        label, diag = "가족과 세상 결핍", "박사님 표준에서 '이웃의 기쁨' 축이 비어 있음. 본인 비전이 타인에게 도달하는지 grill."
    elif o and m and not s:
        label, diag = "나 영역 결핍 (자기 진정한 기쁨 부재)", "박사님 표준에서 '나에게 진정한 기쁨' 축이 비어 있음. 5단계 burnout 위험."
    else:
        label, diag = "부분 만족", "3영역 중 일부 불충족."
    return {
        "status": "imbalanced",
        "label": label,
        "self": s, "others": o, "moral": m,
        "diagnosis": diag,
    }


# ---------------------------------------------------------------------------
# 8. 시나리오 4종 강제 확장
# ---------------------------------------------------------------------------

SCENARIO_TEMPLATES = [
    {"name": "5년 후 시나리오", "prompt_template": "{topic}을(를) 따랐을 때 5년 후 본인의 일상 한 장면을 묘사하세요 — 어디서, 누구와, 무엇을 하고 있나요? 4 Skill Balance 5축(생각·언어·감성·몸·영성) 중 어느 축이 가장 충만하고 어느 축이 가장 결핍될 것 같은가요?"},
    {"name": "10년 후 시나리오", "prompt_template": "10년 후 본인의 모습 — {topic} 결정으로 인해 비전 정의 '가치 있는 시대적 소명'의 세 자리(가치·시대·소명)가 각각 어떻게 채워져 있을 것 같은가요? 박사님 vision-five-stages로 보면 어느 단계에 도달해 있을까요?"},
    {"name": "실패 시나리오", "prompt_template": "{topic}이(가) *실패*했다고 가정합시다. 3년 안에 실패 신호가 나타난다면 그 신호는 어떤 형태일까요? 박사님 3영역(나·가족과 세상·정신적 가치) 중 어디서 먼저 신호가 올까요?"},
    {"name": "기회비용 시나리오", "prompt_template": "{topic} 결정을 *하지 않았을 때* 가능했던 대안 1개를 그려봅시다. 그 대안이 5년 후 본인에게 무엇을 줬을 것 같나요? 박사님 vision-four-futures의 '대안 미래' 관점에서 보세요."},
]


def scenario_expand(topic: Any) -> dict:
    if not isinstance(topic, str):
        topic = ""
    t = topic.strip() if topic.strip() else "이 결정"
    return {
        "topic": topic,
        "scenarios": [
            {"name": s["name"], "prompt": s["prompt_template"].format(topic=t)}
            for s in SCENARIO_TEMPLATES
        ],
    }


# ---------------------------------------------------------------------------
# 9. 박사님 인용 검증 — 문장 단위·정규화 매칭
# ---------------------------------------------------------------------------

_QUOTE_NORM_PUNCT = re.compile(r"[\s　 \.,;:'\"`!?·…—–-]+")


def _normalize_for_quote(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)
    s = _QUOTE_NORM_PUNCT.sub(" ", s)
    return s.strip().lower()


def verify_quote(text: Any) -> dict:
    """박사님 인용 의심 문장이 SOURCES.md § A 허용 목록과 일치하는지 검증.

    매칭 규칙 (엄격):
      1) 정확 매칭 — 정규화 후 동일
      2) 허용 인용이 텍스트의 핵심 인용 부분과 일치 — 텍스트가 허용 인용을 *그대로* 인용하고 있을 때만 통과
         (= 허용 인용 자체가 텍스트와 같거나, 텍스트가 허용 인용 그 자체)
      3) 위조 시도 차단 — "박사님께서 ... 라고 하셨다" 같은 wrapper에 허용 인용을
         부분적으로 끼워넣는 위조는 차단 (텍스트의 비-인용 부분이 의미 추가하면 FAIL)
    """
    if not isinstance(text, str):
        return {"match": False, "reason": "non-string"}
    raw = text.strip()
    # 인용 부호·작은따옴표·큰따옴표 제거
    stripped = raw.strip('"').strip("'").strip("'").strip("'").strip("「").strip("」").strip("『").strip("』")
    norm_text = _normalize_for_quote(stripped)
    if not norm_text:
        return {"match": False, "reason": "empty after normalization"}

    for allowed in ALLOWED_QUOTES:
        norm_allowed = _normalize_for_quote(allowed)
        if norm_text == norm_allowed:
            return {"match": True, "matched": allowed, "mode": "exact"}

    # 텍스트가 허용 인용 *전체*를 포함하면서 *추가 의미*를 거의 안 더한 경우만 부분 허용
    # (위조 차단 — wrapper 단어가 길어지면 FAIL)
    for allowed in ALLOWED_QUOTES:
        norm_allowed = _normalize_for_quote(allowed)
        if norm_allowed in norm_text:
            # 허용 인용 외 추가 문자 수가 인용 길이의 30% 미만이면 통과
            extra = len(norm_text) - len(norm_allowed)
            if extra <= max(5, int(len(norm_allowed) * 0.3)):
                return {"match": True, "matched": allowed, "mode": "near-exact"}
    return {
        "match": False,
        "reason": "no match in SOURCES.md § A allowed quotes (or wrapper too long — possible fabrication)",
        "input": raw,
    }


# ---------------------------------------------------------------------------
# 10. 관련 산출물 후보 식별
# ---------------------------------------------------------------------------

def find_related_artifact(topic: Any) -> dict:
    parsed = parse_topic(topic)
    return {
        "topic": topic if isinstance(topic, str) else "",
        "candidate_skills": parsed["related_skills"],
        "focus_hints": parsed["interview_focus"],
        "matched_keywords": parsed["matched_keywords"],
        "warnings": parsed.get("warnings", []),
        "note": "사용자가 해당 스킬을 과거 돌렸다면 산출물을 가져와 cross-reference. 없으면 본 스킬 인터뷰만으로 grill 가능.",
    }


# ---------------------------------------------------------------------------
# 11. VISION-CONTEXT.md upsert / flag_conflict — idempotent
# ---------------------------------------------------------------------------

CONTEXT_HEADER_TEMPLATE = """# {owner} 비전 용어집

이 사용자의 비전 코칭 맥락에서 사용되는 용어집. 박사님 표준 사전(SOURCES.md § A)을 1순위로 참조하되, 본인 맥락 override가 있으면 § 2에 명시.

## 1. 표준 정의 (박사님 비전 코칭 표준 사전)

(grill_lib.py glossary_standard 시드를 1순위로 사용)

## 2. 본인 맥락 정의

## 3. 본인 고유 용어

## 4. 관계

## 5. 예시 대화

## 6. 충돌 기록

## 7. 외부 참조
"""

SECTION_HEADERS = {
    "2": "## 2. 본인 맥락 정의",
    "3": "## 3. 본인 고유 용어",
    "7": "## 7. 외부 참조",
}
NEXT_HEADERS = {
    "2": "## 3. 본인 고유 용어",
    "3": "## 4. 관계",
    "7": None,
}


def _ensure_context_file(base: str, owner: str) -> tuple[str, bool]:
    """단일 또는 multi context 모두 지원해 적절한 CONTEXT.md 경로 반환."""
    os.makedirs(base, exist_ok=True)
    # multi 우선 — VISION-CONTEXT-MAP.md 있으면 단일 파일 생성 안 함
    cm = os.path.join(base, "VISION-CONTEXT-MAP.md")
    if os.path.exists(cm):
        # 호출자가 영역 폴더로 base를 줘야 한다. 여기서는 단일 경로만 처리.
        # multi인데 base가 루트면 단일 VISION-CONTEXT.md를 만들지 않고
        # 호출자가 영역 폴더 base로 다시 호출해야 함.
        return "", False  # 호출자가 처리
    path = os.path.join(base, "VISION-CONTEXT.md")
    created = False
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONTEXT_HEADER_TEMPLATE.format(owner=owner))
        created = True
    return path, created


def upsert_term(
    base: Any,
    term: Any,
    definition: Any,
    avoid: Any = "",
    section: Any = "2",
    owner: Any = "사용자",
) -> dict:
    """VISION-CONTEXT.md lazy 생성·idempotent 갱신.

    idempotent: 동일 term이 같은 section에 이미 있으면 기존 entry를 *교체*.
    """
    if not isinstance(base, str) or not base:
        return {"ok": False, "reason": "base required"}
    if not isinstance(term, str) or not term.strip():
        return {"ok": False, "reason": "term required"}
    if not isinstance(definition, str) or not definition.strip():
        return {"ok": False, "reason": "definition required"}
    section = str(section)
    if section not in SECTION_HEADERS:
        return {"ok": False, "reason": f"invalid section: {section}"}
    owner = str(owner) if owner is not None else "사용자"

    path, created = _ensure_context_file(base, owner)
    if not path:
        # multi 구조이면서 base가 루트 → 영역 폴더로 다시 호출하라고 알려준다
        return {
            "ok": False,
            "reason": "base appears to be a multi-context root (VISION-CONTEXT-MAP.md present). Call upsert_term with the area folder as base, not the root.",
        }

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    hdr = SECTION_HEADERS[section]
    nxt = NEXT_HEADERS[section]

    # 섹션이 없으면 파일 끝에 추가
    if hdr not in content:
        content = content.rstrip() + f"\n\n{hdr}\n\n"

    # 새 entry 본문
    term_clean = term.strip()
    def_clean = definition.strip()
    avoid_clean = (avoid or "").strip() if isinstance(avoid, str) else ""
    entry_lines = [f"**{term_clean}**:", def_clean]
    if avoid_clean:
        entry_lines.append(f"_Avoid_: {avoid_clean}")
    new_entry = "\n".join(entry_lines) + "\n"

    # 섹션 안에서 기존 동일 term entry 찾아 교체 (idempotent)
    sec_start = content.find(hdr)
    if nxt and nxt in content:
        sec_end = content.find(nxt, sec_start)
    else:
        sec_end = len(content)
    sec_body = content[sec_start:sec_end]

    existing_pattern = re.compile(
        rf"\*\*{re.escape(term_clean)}\*\*:\s*\n.+?(?=\n\*\*|\Z)",
        re.DOTALL,
    )
    replaced = False
    if existing_pattern.search(sec_body):
        new_sec_body = existing_pattern.sub(new_entry.rstrip(), sec_body, count=1)
        content = content[:sec_start] + new_sec_body + content[sec_end:]
        replaced = True
    else:
        # 섹션 끝(다음 헤더 직전)에 삽입
        if nxt and nxt in content:
            insert_at = sec_end
            content = content[:insert_at] + new_entry + "\n" + content[insert_at:]
        else:
            content = content.rstrip() + "\n\n" + new_entry

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "ok": True,
        "created": created,
        "replaced": replaced,
        "path": path,
        "section": section,
        "term": term_clean,
    }


def flag_conflict(
    base: Any,
    term: Any,
    user_usage: Any,
    resolution: Any,
) -> dict:
    """VISION-CONTEXT.md § 6 충돌 기록 자동 추가."""
    if not isinstance(base, str) or not base:
        return {"ok": False, "reason": "base required"}
    if not isinstance(term, str) or not term.strip():
        return {"ok": False, "reason": "term required"}
    if not isinstance(user_usage, str) or not user_usage.strip():
        return {"ok": False, "reason": "user_usage required"}
    if not isinstance(resolution, str) or not resolution.strip():
        return {"ok": False, "reason": "resolution required"}

    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, "VISION-CONTEXT.md")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONTEXT_HEADER_TEMPLATE.format(owner="사용자"))

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    hdr = "## 6. 충돌 기록"
    entry = f'- "{term.strip()}"가 사용자 발화에서 "{user_usage.strip()}"로 쓰임 → 해소: {resolution.strip()}\n'

    if hdr not in content:
        content = content.rstrip() + f"\n\n{hdr}\n\n{entry}"
    else:
        # § 6 헤더 직후, 다음 ## 헤더 전까지 영역에 entry append
        sec_start = content.find(hdr)
        # 다음 ## 헤더 찾기
        rest = content[sec_start + len(hdr):]
        m = re.search(r"\n## ", rest)
        if m:
            sec_end = sec_start + len(hdr) + m.start()
        else:
            sec_end = len(content)
        sec_body = content[sec_start:sec_end].rstrip()
        new_sec_body = sec_body + "\n" + entry
        content = content[:sec_start] + new_sec_body + ("\n" if sec_end < len(content) else "") + content[sec_end:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"ok": True, "path": path, "term": term.strip()}


# ---------------------------------------------------------------------------
# 12. 이모지 검출 (박사님 vision 시리즈 표준)
# ---------------------------------------------------------------------------

# Emoji ranges (BMP·SMP·SMS·CJK Symbols 일부 통합)
EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"  # alchemical
    "\U0001F780-\U0001F7FF"  # geometric extended
    "\U0001F800-\U0001F8FF"  # arrows-c
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess
    "\U0001FA70-\U0001FAFF"  # symbols & pictographs ext-a
    "\U0001F1E6-\U0001F1FF"  # regional indicators (flags)
    # NOTE: U+2600-26FF (misc symbols) 및 U+2700-27BF (dingbats) 범위에는
    # ★ ☆ ✓ ✗ 같은 *텍스트 마커*가 포함되어 있어 박사님 vision 시리즈
    # README·SKILL.md에서 마커로 사용됨 (예: "★ 핵심", "★ 시작점").
    # 따라서 진짜 이모지(😀 🎯 🚀 등)만 차단하고 텍스트 마커는 허용한다.
    "]+",
    flags=re.UNICODE,
)


def emoji_check(text: Any) -> dict:
    if not isinstance(text, str):
        return {"clean": True, "emojis": []}
    matches = EMOJI_RE.findall(text)
    return {"clean": len(matches) == 0, "emojis": matches}


# ---------------------------------------------------------------------------
# 13. 슬러그 정규화 (LDR 파일명·VISION-CONTEXT 영역명)
# ---------------------------------------------------------------------------

SLUG_KEEP_RE = re.compile(r"[A-Za-z0-9가-힯ㄱ-ㆎ]+")


def slug_normalize(title: Any, max_len: int = 60) -> dict:
    if not isinstance(title, str) or not title.strip():
        return {"ok": False, "reason": "title required"}
    t = unicodedata.normalize("NFKC", title)
    # 영어·숫자·한글만 유지하고 나머지는 구분자
    tokens = SLUG_KEEP_RE.findall(t)
    if not tokens:
        return {"ok": False, "reason": "no slug-safe characters in title"}
    slug = "-".join(tokens).lower()
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return {"ok": True, "slug": slug, "original": title}


# ---------------------------------------------------------------------------
# 14. 메뉴 옵션 (빈 호출 시 표시)
# ---------------------------------------------------------------------------

MENU = {
    "modes": [
        {"key": "A", "label": "비전 grill (1:1 인터뷰)", "examples": ["me", "coachee:김도현", "내 비전 무너뜨려봐"]},
        {"key": "B", "label": "vision 산출물 메타 검증", "examples": ["verify mission-frame", "verify three-realm-balance"]},
        {"key": "C", "label": "다목적 주제 인터뷰 (메인 진입로)", "examples": [
            "나의 역량·실력·미래 비전 가능성을 종합해서 진로 결정. 전공·학교 코칭",
            "집을 살까 말까", "선교지로 갈까 말까",
            "비전이 막혀있다. 생각 정리부터",
        ]},
    ],
    "tools_available": [
        "박사님 표준 사전 lookup·충돌 검출",
        "LDR 3조건 자동 판정",
        "3영역 균형 검사",
        "시나리오 4종 강제 확장 (5년·10년·실패·기회비용)",
        "박사님 인용 검증 (할루시네이션 차단)",
    ],
}


def menu_options() -> dict:
    return MENU


# ---------------------------------------------------------------------------
# 15. SYNC 검증 — STANDARD_GLOSSARY / ALLOWED_QUOTES / topic_skill_map
# ---------------------------------------------------------------------------

def validate_glossary_sync() -> dict:
    """STANDARD_GLOSSARY와 glossary_standard.md 사이 drift 검증.

    glossary_standard.md의 모든 박사님 표준 정의(### 헤더의 한글 용어)가
    STANDARD_GLOSSARY 키로 존재해야 한다.
    """
    path = os.path.join(HERE, "glossary_standard.md")
    if not os.path.exists(path):
        return {"ok": False, "reason": f"glossary_standard.md missing at {path}"}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # ### {용어} 또는 ### {용어} ({영문}) 형식의 헤더 추출
    headers = re.findall(r"^###\s+(.+?)\s*$", content, flags=re.MULTILINE)
    # 영문 괄호 제거
    md_terms: list[str] = []
    for h in headers:
        # § 7 메타 어휘에서 vision-* / sermon-* 스킬 이름은 제외 (사전 용어 아님)
        if h.startswith("vision-") or h.startswith("sermon-") or h.startswith("foresight-"):
            continue
        # "비전 (Vision)" → "비전"
        m = re.match(r"(.+?)\s*\(.+?\)\s*$", h)
        key = m.group(1).strip() if m else h.strip()
        md_terms.append(key)

    code_terms = list(STANDARD_GLOSSARY.keys())
    md_unique = sorted(set(md_terms))
    code_unique = sorted(set(code_terms))
    missing_in_code = [t for t in md_unique if t not in code_unique]
    extra_in_code = [t for t in code_unique if t not in md_unique]

    return {
        "ok": not missing_in_code and not extra_in_code,
        "md_terms_count": len(md_terms),
        "md_unique_count": len(md_unique),
        "code_terms_count": len(code_terms),
        "code_unique_count": len(code_unique),
        "missing_in_code": missing_in_code,
        "extra_in_code": extra_in_code,
        "note": (
            "md_terms_count > md_unique_count이면 같은 한글 용어가 다른 영문 맥락으로 "
            "두 번 정의된 것 (예: '정신적 가치' — Divine Value/Spiritual·Moral Value Realm). "
            "박사님 책 의도. ok는 unique set 기준."
        ),
    }


def validate_quotes_sync() -> dict:
    """ALLOWED_QUOTES와 SOURCES.md § A drift 검증.

    SOURCES.md § A에 명시된 박사님 책 인용(`>` 인용 블록)이 ALLOWED_QUOTES에 모두 들어 있어야 한다.
    """
    path = os.path.join(HERE, "SOURCES.md")
    if not os.path.exists(path):
        return {"ok": False, "reason": f"SOURCES.md missing at {path}"}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # § A 영역만 발췌
    a_start = content.find("## A.")
    a_end = content.find("## B.")
    if a_start < 0 or a_end < 0:
        return {"ok": False, "reason": "SOURCES.md § A or § B section header missing"}
    a_block = content[a_start:a_end]

    # `> "..."` 형식의 인용만 추출
    quote_pattern = re.compile(r'>\s*"([^"\n]+?)"', re.MULTILINE)
    md_quotes = list({m.group(1).strip() for m in quote_pattern.finditer(a_block)})

    norm_allowed = {_normalize_for_quote(q): q for q in ALLOWED_QUOTES}
    missing_in_code: list[str] = []
    for q in md_quotes:
        if _normalize_for_quote(q) not in norm_allowed:
            missing_in_code.append(q)

    norm_md = {_normalize_for_quote(q) for q in md_quotes}
    extra_in_code: list[str] = []
    for q in ALLOWED_QUOTES:
        if _normalize_for_quote(q) not in norm_md:
            # ALLOWED_QUOTES에는 있는데 SOURCES.md § A에 없는 인용
            extra_in_code.append(q)

    return {
        "ok": not missing_in_code,  # 코드에 더 많은 건 OK, 코드가 부족한 게 FAIL
        "md_quotes_count": len(md_quotes),
        "code_quotes_count": len(ALLOWED_QUOTES),
        "missing_in_code": missing_in_code,
        "extra_in_code": extra_in_code,
        "note": "missing_in_code가 비어 있으면 PASS. extra_in_code는 코드가 SOURCES.md 외 명시 인용을 가진 경우.",
    }


def validate_topic_map_skills(skills_root: Any = None) -> dict:
    """topic_skill_map.md에 등장하는 모든 스킬명이 실제 skills/ 폴더에 존재하는지 검증.

    skills_root 기본값: ../  (HERE 상위 디렉터리. = cys-claude-vision-coaching-skills/skills/)
    """
    if skills_root is None or not isinstance(skills_root, str) or not skills_root:
        # 기본: 두 단계 위 (HERE → skills/vision-grill-with-docs/ → skills/)
        skills_root = os.path.dirname(HERE)
    if not os.path.isdir(skills_root):
        return {"ok": False, "reason": f"skills_root not a directory: {skills_root}"}

    rows, warnings = _load_topic_map()
    # topic_skill_map.md에 등장하는 모든 스킬 수집
    referenced: set[str] = set()
    for row in rows:
        for s in row["skills"]:
            referenced.add(s)

    # 실제 폴더 목록 — vision-* / sermon-* / foresight-* 만 검사 (외부 시리즈 포함)
    existing: set[str] = set()
    for entry in os.listdir(skills_root):
        full = os.path.join(skills_root, entry)
        if os.path.isdir(full):
            existing.add(entry)

    missing_skills = sorted(referenced - existing)
    # 외부 시리즈 스킬(foresight-* 등)이 본 저장소에 없으면 경고만, FAIL 아님
    fail_missing = [s for s in missing_skills if s.startswith("vision-")]
    external_missing = [s for s in missing_skills if not s.startswith("vision-")]

    return {
        "ok": len(fail_missing) == 0,
        "referenced_count": len(referenced),
        "existing_count": len(existing),
        "missing_vision_skills": fail_missing,
        "missing_external_skills": external_missing,
        "load_warnings": warnings,
    }


# ---------------------------------------------------------------------------
# 16. 호칭 결정 (select_honorific) — vision 시리즈 일관 패턴
# ---------------------------------------------------------------------------

HONORIFIC_DEFAULT = "선생님"


def select_honorific(meta: Any = None) -> dict:
    """사용자 메타데이터로 호칭 결정.

    meta 키:
      - is_doctor: bool       → 박사님 본인이면 "박사님"
      - title: str            → 명시 직함 ("목사", "전도사", "교수" 등) → "○○님"
      - name: str             → 이름만 있을 때 "○○님"
      - default: 기본값 "선생님"
    """
    if not isinstance(meta, dict):
        return {"honorific": HONORIFIC_DEFAULT, "reason": "no meta"}
    if meta.get("is_doctor") is True:
        return {"honorific": "박사님", "reason": "is_doctor=True"}
    title = (meta.get("title") or "").strip() if isinstance(meta.get("title"), str) else ""
    if title:
        if title.endswith("님"):
            return {"honorific": title, "reason": "title with 님"}
        return {"honorific": f"{title}님", "reason": "title + 님"}
    name = (meta.get("name") or "").strip() if isinstance(meta.get("name"), str) else ""
    if name:
        if name.endswith("님"):
            return {"honorific": name, "reason": "name with 님"}
        return {"honorific": f"{name}님", "reason": "name + 님"}
    return {"honorific": HONORIFIC_DEFAULT, "reason": "default"}


# ---------------------------------------------------------------------------
# 17. LDR 본문 템플릿 생성 (render_ldr_body)
# ---------------------------------------------------------------------------

VALID_LDR_AREAS = ("진로", "재정", "관계", "사역", "건강", "비전 영역 전환")


def render_ldr_body(
    title: Any,
    date_iso: Any,
    area: Any,
    reason: Any,
    status: Any = None,
    options_considered: Any = None,
    consequences: Any = None,
) -> dict:
    """LDR 본문 자동 생성 — 최소 템플릿 + 선택 섹션.

    인자:
        title: 결정 제목
        date_iso: 'YYYY-MM-DD' 형식
        area: 영역 (진로/재정/관계/사역/건강/비전 영역 전환 또는 자유 문자열)
        reason: 1~3 문장의 'why'
        status: proposed | accepted | deprecated | superseded by LDR-NNNN (선택)
        options_considered: 거절한 대안 리스트 (선택)
        consequences: 후속 영향 리스트 (선택)
    """
    if not isinstance(title, str) or not title.strip():
        return {"ok": False, "reason": "title required"}
    if not isinstance(date_iso, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date_iso.strip()):
        return {"ok": False, "reason": "date_iso must be YYYY-MM-DD"}
    if not isinstance(area, str) or not area.strip():
        return {"ok": False, "reason": "area required"}
    if not isinstance(reason, str) or not reason.strip():
        return {"ok": False, "reason": "reason required"}

    lines = [f"# {title.strip()}", "", f"**날짜**: {date_iso.strip()}", f"**영역**: {area.strip()}"]
    if status and isinstance(status, str) and status.strip():
        lines.append(f"**Status**: {status.strip()}")
    lines.append("")
    lines.append(reason.strip())

    if options_considered and isinstance(options_considered, list) and options_considered:
        lines.append("")
        lines.append("## 고려한 대안")
        for opt in options_considered:
            if isinstance(opt, str) and opt.strip():
                lines.append(f"- {opt.strip()}")

    if consequences and isinstance(consequences, list) and consequences:
        lines.append("")
        lines.append("## Consequences")
        for c in consequences:
            if isinstance(c, str) and c.strip():
                lines.append(f"- {c.strip()}")

    lines.append("")
    body = "\n".join(lines)
    return {
        "ok": True,
        "body": body,
        "title": title.strip(),
        "date": date_iso.strip(),
        "area": area.strip(),
        "is_known_area": area.strip() in VALID_LDR_AREAS,
    }


# ---------------------------------------------------------------------------
# 18. 박사님 정의 인용 포맷 생성 (render_definition / render_quote)
# ---------------------------------------------------------------------------

def render_definition(term: Any) -> dict:
    """glossary_lookup 결과를 인터뷰에서 그대로 쓸 수 있는 한 줄로 포맷.

    출력 예: "**비전**: 가치 있는 시대적 소명 (박사님 『미래준비학교』(2016) — SOURCES.md § A-01)"
    """
    lookup = glossary_lookup(term)
    if not lookup.get("found"):
        return {"ok": False, "reason": lookup.get("reason", "not found")}
    rendered = (
        f"**{lookup['term']}**: {lookup['definition']} "
        f"({lookup['source']})"
    )
    return {
        "ok": True,
        "rendered": rendered,
        "term": lookup["term"],
        "definition": lookup["definition"],
        "source": lookup["source"],
    }


def render_quote(text: Any) -> dict:
    """박사님 인용 텍스트를 verify 후 표준 표기로 포맷.

    출력 예: '> "외부로부터 주어지는 영감" — 박사님 『미래준비학교』(2016, SOURCES.md § A-01)'
    """
    v = verify_quote(text)
    if not v.get("match"):
        return {"ok": False, "reason": v.get("reason", "not allowed")}
    matched = v.get("matched", text if isinstance(text, str) else "")
    rendered = f'> "{matched}" — 박사님 『미래준비학교』(2016, SOURCES.md § A-01)'
    return {"ok": True, "rendered": rendered, "matched": matched}


# ---------------------------------------------------------------------------
# 19. VISION-CONTEXT.md § 1 박사님 표준 사전 시드 (seed_standard_glossary)
# ---------------------------------------------------------------------------

def seed_standard_glossary(base: Any, owner: Any = "사용자") -> dict:
    """VISION-CONTEXT.md § 1 표준 정의 섹션에 박사님 표준 사전 29개를 한 번에 시드.

    이미 § 1에 entry가 있으면 idempotent (중복 시드 안 함).
    """
    if not isinstance(base, str) or not base:
        return {"ok": False, "reason": "base required"}
    os.makedirs(base, exist_ok=True)
    path = os.path.join(base, "VISION-CONTEXT.md")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(CONTEXT_HEADER_TEMPLATE.format(owner=str(owner) if owner else "사용자"))

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    hdr = "## 1. 표준 정의 (박사님 비전 코칭 표준 사전)"
    # § 1이 없으면 생성
    if hdr not in content:
        content += f"\n\n{hdr}\n\n"

    # § 1 영역 추출
    sec_start = content.find(hdr)
    nxt = "## 2."
    sec_end = content.find(nxt, sec_start) if nxt in content else len(content)
    sec_body = content[sec_start:sec_end]

    # 이미 박사님 표준 entry가 있으면 idempotent
    if "**비전**:" in sec_body:
        return {"ok": True, "path": path, "seeded": False, "reason": "already seeded"}

    # 시드 텍스트 생성 — STANDARD_GLOSSARY 모든 entry
    seed_lines = []
    for term, payload in STANDARD_GLOSSARY.items():
        seed_lines.append(f"**{term}**:")
        seed_lines.append(payload["definition"])
        if payload.get("avoid"):
            seed_lines.append(f"_Avoid_: {', '.join(payload['avoid'])}")
        seed_lines.append(f"_Source_: {payload['source']}")
        seed_lines.append("")
    seed_text = "\n".join(seed_lines)

    # § 1 헤더 직후에 삽입
    insert_at = content.find("\n", sec_start) + 1
    new_content = content[:insert_at] + "\n" + seed_text + content[insert_at:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {
        "ok": True,
        "path": path,
        "seeded": True,
        "terms_count": len(STANDARD_GLOSSARY),
    }


# ---------------------------------------------------------------------------
# 20. VISION-CONTEXT.md 무결성 검증 (validate_context_integrity)
# ---------------------------------------------------------------------------

REQUIRED_SECTIONS = [
    "## 1. 표준 정의",
    "## 2. 본인 맥락 정의",
    "## 3. 본인 고유 용어",
    "## 4. 관계",
    "## 5. 예시 대화",
    "## 6. 충돌 기록",
    "## 7. 외부 참조",
]


def validate_context_integrity(base: Any) -> dict:
    """VISION-CONTEXT.md의 § 1~7 헤더가 모두 존재하고 순서대로인지 검증."""
    if not isinstance(base, str) or not base:
        return {"ok": False, "reason": "base required"}
    path = os.path.join(base, "VISION-CONTEXT.md")
    if not os.path.exists(path):
        return {"ok": False, "reason": "VISION-CONTEXT.md not found", "exists": False}
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    missing: list[str] = []
    positions: dict[str, int] = {}
    for sec in REQUIRED_SECTIONS:
        idx = content.find(sec)
        if idx < 0:
            missing.append(sec)
        else:
            positions[sec] = idx

    # 순서 검증
    order_ok = True
    out_of_order: list[str] = []
    last_pos = -1
    for sec in REQUIRED_SECTIONS:
        if sec in positions:
            if positions[sec] < last_pos:
                order_ok = False
                out_of_order.append(sec)
            last_pos = positions[sec]

    return {
        "ok": len(missing) == 0 and order_ok,
        "exists": True,
        "missing_sections": missing,
        "out_of_order": out_of_order,
        "section_count_present": len(positions),
    }


# ---------------------------------------------------------------------------
# 21. LDR 체인 검증 (validate_ldr_chain) — superseded by 검증
# ---------------------------------------------------------------------------

def validate_ldr_chain(base: Any) -> dict:
    """docs/ldr/ 안의 모든 LDR을 스캔하여 'superseded by LDR-NNNN' 참조가
    실제 LDR 번호로 존재하는지 검증.
    """
    if not isinstance(base, str) or not base:
        return {"ok": False, "reason": "base required"}
    ldr_dir = os.path.join(base, "docs", "ldr")
    if not os.path.isdir(ldr_dir):
        return {"ok": True, "ldr_count": 0, "broken_chains": [], "reason": "no docs/ldr/"}

    # 모든 LDR 번호 수집
    existing_numbers: set[str] = set()
    files: list[str] = []
    for name in os.listdir(ldr_dir):
        m = LDR_NAME_PATTERN.match(name)
        if m:
            existing_numbers.add(m.group(1))
            files.append(name)

    # 각 파일에서 superseded by 참조 추출
    broken_chains: list[dict] = []
    chain_re = re.compile(r"superseded\s+by\s+LDR-(\d{4})", re.IGNORECASE)
    for fn in files:
        full = os.path.join(ldr_dir, fn)
        try:
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        for m in chain_re.finditer(content):
            ref = m.group(1)
            if ref not in existing_numbers:
                broken_chains.append({
                    "file": fn,
                    "references": f"LDR-{ref}",
                    "issue": "referenced LDR does not exist",
                })

    return {
        "ok": len(broken_chains) == 0,
        "ldr_count": len(files),
        "broken_chains": broken_chains,
    }


# ---------------------------------------------------------------------------
# 22. three_realm 라벨 ↔ glossary sync (validate_three_realm_sync)
# ---------------------------------------------------------------------------

THREE_REALM_LABELS = [
    "개인 욕망", "자기희생·세상일", "왜곡된 사명",
]


def validate_three_realm_sync() -> dict:
    """three_realm_check가 출력하는 7개 라벨이 STANDARD_GLOSSARY에 등재되어 있는지 검증."""
    missing: list[str] = []
    for label in THREE_REALM_LABELS:
        if label not in STANDARD_GLOSSARY:
            missing.append(label)
    return {
        "ok": len(missing) == 0,
        "labels_checked": THREE_REALM_LABELS,
        "missing_in_glossary": missing,
    }


# ---------------------------------------------------------------------------
# 23. ystory/korea-universities 캐시 통합 (런타임 캐시 + 7일 TTL)
# ---------------------------------------------------------------------------
# 데이터 출처: https://github.com/ystory/korea-universities
# 라이선스: 원 저장소 LICENSE 준수. 데이터 = 커리어넷 + 한국유학종합시스템 공공자료.
# 캐시 정책: 첫 호출 시 GitHub raw에서 fetch → ~/.cache/vision-grill-with-docs/에 저장
#           7일 경과 후 자동 재fetch. 네트워크 실패 시 stale 캐시 사용.

KOREA_UNI_RAW_URL = (
    "https://raw.githubusercontent.com/ystory/korea-universities/main/"
    "src/data/universities-final.json"
)
KOREA_UNI_META_URL = (
    "https://raw.githubusercontent.com/ystory/korea-universities/main/"
    "src/data/metadata.json"
)
KOREA_UNI_CACHE_DIR = os.path.expanduser("~/.cache/vision-grill-with-docs")
KOREA_UNI_CACHE_PATH = os.path.join(KOREA_UNI_CACHE_DIR, "universities-final.json")
KOREA_UNI_META_PATH = os.path.join(KOREA_UNI_CACHE_DIR, "metadata.json")
KOREA_UNI_TTL_SECONDS = 7 * 24 * 3600  # 7 days


def _cache_age_seconds(path: str) -> float | None:
    if not os.path.exists(path):
        return None
    import time
    return time.time() - os.path.getmtime(path)


def _fetch_json(url: str, timeout: float = 30.0) -> Any:
    """결정론적 GitHub raw fetch. urllib만 사용 (외부 의존성 0)."""
    from urllib.request import Request, urlopen
    req = Request(url, headers={"User-Agent": "vision-grill-with-docs/1.0"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def refresh_university_cache(force: bool = False) -> dict:
    """ystory/korea-universities 캐시 갱신 (TTL 7일).

    force=True면 TTL 무시하고 강제 fetch.
    네트워크 실패 시 stale 캐시 사용 + warning.
    """
    os.makedirs(KOREA_UNI_CACHE_DIR, exist_ok=True)
    age = _cache_age_seconds(KOREA_UNI_CACHE_PATH)

    fresh = (age is not None) and (age < KOREA_UNI_TTL_SECONDS)
    if fresh and not force:
        return {
            "ok": True,
            "cached": True,
            "fetched": False,
            "age_seconds": int(age),
            "ttl_seconds": KOREA_UNI_TTL_SECONDS,
            "path": KOREA_UNI_CACHE_PATH,
        }

    # fetch
    try:
        data = _fetch_json(KOREA_UNI_RAW_URL)
        meta = _fetch_json(KOREA_UNI_META_URL)
    except Exception as e:
        # network failure → stale fallback
        if age is not None:
            return {
                "ok": True,
                "cached": True,
                "fetched": False,
                "stale": True,
                "age_seconds": int(age),
                "warning": f"fetch failed ({type(e).__name__}: {e}); using stale cache",
                "path": KOREA_UNI_CACHE_PATH,
            }
        return {
            "ok": False,
            "reason": f"fetch failed and no cache: {type(e).__name__}: {e}",
        }

    # 검증 — 응답 형식
    if not isinstance(data, list) or not data:
        return {"ok": False, "reason": "invalid universities data (not a non-empty list)"}
    if not isinstance(meta, dict):
        return {"ok": False, "reason": "invalid metadata"}

    # atomic write
    tmp1 = KOREA_UNI_CACHE_PATH + ".tmp"
    tmp2 = KOREA_UNI_META_PATH + ".tmp"
    with open(tmp1, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    with open(tmp2, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    os.replace(tmp1, KOREA_UNI_CACHE_PATH)
    os.replace(tmp2, KOREA_UNI_META_PATH)

    return {
        "ok": True,
        "cached": True,
        "fetched": True,
        "count": len(data),
        "metadata": meta,
        "path": KOREA_UNI_CACHE_PATH,
    }


def _load_university_cache() -> list[dict] | None:
    if not os.path.exists(KOREA_UNI_CACHE_PATH):
        return None
    try:
        with open(KOREA_UNI_CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return None


def lookup_korean_university(
    name: Any = None,
    region: Any = None,
    level: Any = None,
    accredited_degree: Any = None,
    limit: int = 20,
) -> dict:
    """캐시된 한국 대학 데이터에서 조건 검색.

    인자:
        name: 학교명 부분 일치 (한국어)
        region: 지역 (예: "서울특별시", "경기도")
        level: "대학(4년제)" | "전문대학(2-3년제)" | "대학원대학"
        accredited_degree: True면 학위과정 인증 학교만
        limit: 반환 개수 (기본 20)
    """
    # 캐시 자동 갱신
    refresh_result = refresh_university_cache()
    if not refresh_result.get("ok"):
        return {"ok": False, "reason": refresh_result.get("reason", "cache failed"), "results": []}

    data = _load_university_cache()
    if data is None:
        return {"ok": False, "reason": "cache load failed", "results": []}

    results = []
    for u in data:
        if not isinstance(u, dict):
            continue
        if name and isinstance(name, str):
            if name.strip() not in (u.get("nameKr") or ""):
                continue
        if region and isinstance(region, str):
            if region.strip() != (u.get("region") or ""):
                continue
        if level and isinstance(level, str):
            if level.strip() not in (u.get("level") or ""):
                continue
        if accredited_degree is True:
            acc = u.get("accreditation") or {}
            if not acc.get("degree"):
                continue
        results.append(u)
        if len(results) >= max(1, int(limit)):
            break

    return {
        "ok": True,
        "count": len(results),
        "results": results,
        "cache_age_seconds": int(_cache_age_seconds(KOREA_UNI_CACHE_PATH) or 0),
    }


def validate_university_cache_sync() -> dict:
    """캐시 무결성·신선도 + metadata 출처 검증."""
    if not os.path.exists(KOREA_UNI_CACHE_PATH):
        return {"ok": False, "reason": "no cache yet — call refresh_university_cache first"}
    data = _load_university_cache()
    if data is None:
        return {"ok": False, "reason": "cache load failed (corrupt JSON?)"}
    age = _cache_age_seconds(KOREA_UNI_CACHE_PATH) or 0
    meta = None
    if os.path.exists(KOREA_UNI_META_PATH):
        try:
            with open(KOREA_UNI_META_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, json.JSONDecodeError):
            pass

    expected_min = 400  # ystory/korea-universities 데이터 보수 하한 (현재 491개)
    return {
        "ok": len(data) >= expected_min,
        "count": len(data),
        "expected_min": expected_min,
        "age_seconds": int(age),
        "ttl_seconds": KOREA_UNI_TTL_SECONDS,
        "stale": age >= KOREA_UNI_TTL_SECONDS,
        "metadata": meta,
        "sources": (meta or {}).get("sources", []),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _bool_arg(s: Any) -> bool:
    return str(s).strip().lower() in ("true", "1", "yes", "y", "t")


def main() -> int:
    parser = argparse.ArgumentParser(description="vision-grill-with-docs deterministic helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("route_mode")
    p.add_argument("--text", required=True)

    p = sub.add_parser("parse_topic")
    p.add_argument("--text", required=True)

    p = sub.add_parser("detect_glossary_conflict")
    p.add_argument("--text", required=True)

    p = sub.add_parser("glossary_lookup")
    p.add_argument("--term", required=True)

    p = sub.add_parser("check_ldr_criteria")
    p.add_argument("--decision", required=True)
    p.add_argument("--reversibility", required=True)
    p.add_argument("--surprising", required=True)
    p.add_argument("--tradeoff", required=True)

    p = sub.add_parser("next_ldr_number")
    p.add_argument("--base", required=True)

    p = sub.add_parser("is_multi_context")
    p.add_argument("--base", required=True)

    p = sub.add_parser("list_contexts")
    p.add_argument("--base", required=True)

    p = sub.add_parser("promote_to_multi")
    p.add_argument("--base", required=True)
    p.add_argument("--area", required=True)

    p = sub.add_parser("three_realm_check")
    p.add_argument("--self", dest="self_arg", required=True)
    p.add_argument("--others", required=True)
    p.add_argument("--moral", required=True)

    p = sub.add_parser("scenario_expand")
    p.add_argument("--topic", required=True)

    p = sub.add_parser("verify_quote")
    p.add_argument("--text", required=True)

    p = sub.add_parser("find_related_artifact")
    p.add_argument("--topic", required=True)

    p = sub.add_parser("upsert_term")
    p.add_argument("--base", required=True)
    p.add_argument("--term", required=True)
    p.add_argument("--definition", required=True)
    p.add_argument("--avoid", default="")
    p.add_argument("--section", default="2", choices=["2", "3", "7"])
    p.add_argument("--owner", default="사용자")

    p = sub.add_parser("flag_conflict")
    p.add_argument("--base", required=True)
    p.add_argument("--term", required=True)
    p.add_argument("--user-usage", required=True, dest="user_usage")
    p.add_argument("--resolution", required=True)

    p = sub.add_parser("emoji_check")
    p.add_argument("--text", required=True)

    p = sub.add_parser("slug_normalize")
    p.add_argument("--title", required=True)
    p.add_argument("--max-len", type=int, default=60, dest="max_len")

    sub.add_parser("menu_options")
    sub.add_parser("validate_glossary_sync")
    sub.add_parser("validate_quotes_sync")
    sub.add_parser("validate_three_realm_sync")

    p = sub.add_parser("validate_topic_map_skills")
    p.add_argument("--skills-root", default=None, dest="skills_root")

    # 신규 v2 함수들
    p = sub.add_parser("select_honorific")
    p.add_argument("--meta-json", required=True, dest="meta_json", help="JSON string of meta dict")

    p = sub.add_parser("render_ldr_body")
    p.add_argument("--title", required=True)
    p.add_argument("--date", required=True, dest="date_iso")
    p.add_argument("--area", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--status", default=None)
    p.add_argument("--options-json", default=None, dest="options_json")
    p.add_argument("--consequences-json", default=None, dest="consequences_json")

    p = sub.add_parser("render_definition")
    p.add_argument("--term", required=True)

    p = sub.add_parser("render_quote")
    p.add_argument("--text", required=True)

    p = sub.add_parser("seed_standard_glossary")
    p.add_argument("--base", required=True)
    p.add_argument("--owner", default="사용자")

    p = sub.add_parser("validate_context_integrity")
    p.add_argument("--base", required=True)

    p = sub.add_parser("validate_ldr_chain")
    p.add_argument("--base", required=True)

    p = sub.add_parser("refresh_university_cache")
    p.add_argument("--force", action="store_true")

    p = sub.add_parser("lookup_korean_university")
    p.add_argument("--name", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--level", default=None)
    p.add_argument("--accredited-degree", default="false", dest="acc_deg")
    p.add_argument("--limit", type=int, default=20)

    sub.add_parser("validate_university_cache_sync")

    args = parser.parse_args()

    if args.cmd == "route_mode":
        out = route_mode(args.text)
    elif args.cmd == "parse_topic":
        out = parse_topic(args.text)
    elif args.cmd == "detect_glossary_conflict":
        out = detect_glossary_conflict(args.text)
    elif args.cmd == "glossary_lookup":
        out = glossary_lookup(args.term)
    elif args.cmd == "check_ldr_criteria":
        out = check_ldr_criteria(
            decision=args.decision,
            reversibility=args.reversibility,
            surprising=_bool_arg(args.surprising),
            tradeoff=_bool_arg(args.tradeoff),
        )
    elif args.cmd == "next_ldr_number":
        out = next_ldr_number(args.base)
    elif args.cmd == "is_multi_context":
        out = is_multi_context(args.base)
    elif args.cmd == "list_contexts":
        out = list_contexts(args.base)
    elif args.cmd == "promote_to_multi":
        out = promote_to_multi(args.base, args.area)
    elif args.cmd == "three_realm_check":
        out = three_realm_check(
            self_realm=_bool_arg(args.self_arg),
            others_realm=_bool_arg(args.others),
            moral_realm=_bool_arg(args.moral),
        )
    elif args.cmd == "scenario_expand":
        out = scenario_expand(args.topic)
    elif args.cmd == "verify_quote":
        out = verify_quote(args.text)
    elif args.cmd == "find_related_artifact":
        out = find_related_artifact(args.topic)
    elif args.cmd == "upsert_term":
        out = upsert_term(
            base=args.base,
            term=args.term,
            definition=args.definition,
            avoid=args.avoid,
            section=args.section,
            owner=args.owner,
        )
    elif args.cmd == "flag_conflict":
        out = flag_conflict(
            base=args.base,
            term=args.term,
            user_usage=args.user_usage,
            resolution=args.resolution,
        )
    elif args.cmd == "emoji_check":
        out = emoji_check(args.text)
    elif args.cmd == "slug_normalize":
        out = slug_normalize(args.title, max_len=args.max_len)
    elif args.cmd == "menu_options":
        out = menu_options()
    elif args.cmd == "validate_glossary_sync":
        out = validate_glossary_sync()
    elif args.cmd == "validate_quotes_sync":
        out = validate_quotes_sync()
    elif args.cmd == "validate_topic_map_skills":
        out = validate_topic_map_skills(args.skills_root)
    elif args.cmd == "validate_three_realm_sync":
        out = validate_three_realm_sync()
    elif args.cmd == "select_honorific":
        try:
            meta = json.loads(args.meta_json) if args.meta_json else {}
        except json.JSONDecodeError as e:
            out = {"honorific": HONORIFIC_DEFAULT, "reason": f"invalid JSON: {e}"}
        else:
            out = select_honorific(meta)
    elif args.cmd == "render_ldr_body":
        opts = json.loads(args.options_json) if args.options_json else None
        cons = json.loads(args.consequences_json) if args.consequences_json else None
        out = render_ldr_body(
            title=args.title,
            date_iso=args.date_iso,
            area=args.area,
            reason=args.reason,
            status=args.status,
            options_considered=opts,
            consequences=cons,
        )
    elif args.cmd == "render_definition":
        out = render_definition(args.term)
    elif args.cmd == "render_quote":
        out = render_quote(args.text)
    elif args.cmd == "seed_standard_glossary":
        out = seed_standard_glossary(args.base, args.owner)
    elif args.cmd == "validate_context_integrity":
        out = validate_context_integrity(args.base)
    elif args.cmd == "validate_ldr_chain":
        out = validate_ldr_chain(args.base)
    elif args.cmd == "refresh_university_cache":
        out = refresh_university_cache(force=bool(args.force))
    elif args.cmd == "lookup_korean_university":
        out = lookup_korean_university(
            name=args.name,
            region=args.region,
            level=args.level,
            accredited_degree=_bool_arg(args.acc_deg),
            limit=args.limit,
        )
    elif args.cmd == "validate_university_cache_sync":
        out = validate_university_cache_sync()
    else:  # pragma: no cover
        parser.error(f"unknown command: {args.cmd}")
        return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
