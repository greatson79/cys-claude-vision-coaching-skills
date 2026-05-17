"""
vision-clarity-coaching — 결정론적 헬퍼 라이브러리.

LLM이 자연어 추론으로 결정하면 할루시네이션·드리프트 위험이 있는 단계를
결정론으로 환원한 함수들. SKILL.md에서 명시적으로 호출하도록 지정한다.

기준 사양: SKILL.md (같은 디렉터리). 모든 함수는 SKILL.md의 문구·표를 1:1 대응.

호출 예 (CLI):
    python3 clarity_lib.py honorific --doctor true
    python3 clarity_lib.py input_type --text "비전 모르겠어요" --diagnoses ""
    python3 clarity_lib.py step4 --age 55
    python3 clarity_lib.py diag_step --key enneagram
    python3 clarity_lib.py validate_sentence --sentence "..."
    python3 clarity_lib.py detect_assertive --text "ENFP니까 창작 비전이어야 한다"
    python3 clarity_lib.py emoji_check --text "..."
    python3 clarity_lib.py opening
    python3 clarity_lib.py diag_question --key enneagram --honorific "박사님" --type_num 9
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Any


# ---------------------------------------------------------------------------
# 1. 호칭 결정 (SKILL.md "호칭 처리 원칙" 표 1:1 대응)
# ---------------------------------------------------------------------------

HONORIFIC_DEFAULT = "선생님"


def select_honorific(meta: dict) -> str:
    """사용자 메타데이터로 호칭을 결정한다.

    meta 키 (모두 선택):
      - is_doctor: bool      → 최윤식 박사 본인 (True면 "박사님")
      - title: str            → 명시 직함 ("목사", "전도사", "교수" 등)
      - name: str             → 이름 (직함 없을 때 "○○님")
      - is_informal: bool     → 사용자가 반말로 입력 (호칭은 "선생님" 유지)

    반환: 단일 호칭 문자열. 빈 입력은 기본값 "선생님".
    """
    if not isinstance(meta, dict):
        return HONORIFIC_DEFAULT
    if meta.get("is_doctor") is True:
        return "박사님"

    title = (meta.get("title") or "").strip()
    if title:
        # 이미 "님"이 붙어 있으면 그대로, 아니면 "님" 부착
        if title.endswith("님"):
            return title
        return f"{title}님"

    name = (meta.get("name") or "").strip()
    if name:
        return f"{name}님"

    return HONORIFIC_DEFAULT


# ---------------------------------------------------------------------------
# 2. 입력 유형 A~E 분류 (SKILL.md "입력 유형별 처리 방식" 표 1:1 대응)
# ---------------------------------------------------------------------------

# SKILL.md "범위 밖" 키워드 (vision-goal-reframing / progress-review /
# career-recommendation 영역)
SCOPE_OUT_TOKENS: dict[str, list[str]] = {
    "goal-reframing": [
        "두 선택지", "두 가지 중", "두 가지 진로 중",
        "선택 비교", "어떤 걸 골라", "어떤 것을 골라",
        "결정해 줘", "결정해줘", "결정해야", "선택해야",
        "A vs B", "A냐 B냐", "둘 중", "두 길 중",
    ],
    "progress-review": [
        "진척", "현재 점검", "어디까지 왔", "진행 상황 점검",
        "지난주 점검", "월간 점검", "진행 점검",
    ],
    "career-recommendation": [
        "직업 추천", "어떤 직업", "직업 골라", "직업이 좋",
        "어떤 일자리", "job recommendation", "어떤 직군",
        "추천 직업", "맞는 직업",
    ],
}

INSTANT_TOKENS = [
    "한 문장 바로", "바로 말해", "바로 알려", "즉답",
    "빨리 한 문장", "한 줄로 바로",
]

COMPACT_TOKENS = [
    "압축", "빠르게 진행", "압축 모드", "단축", "3단계로", "짧게 진행",
]


def _contains_any(text: str, tokens: list[str]) -> str | None:
    t = text.lower() if text else ""
    for tok in tokens:
        if tok.lower() in t:
            return tok
    return None


def classify_input_type(
    text: str,
    diagnoses: list[str] | None = None,
    explicit_hint: str = "",
) -> dict:
    """사용자 첫 입력으로 유형 A~E를 결정한다.

    인자:
      text: 사용자 첫 발화 원문.
      diagnoses: 보유한 진단 이름 리스트 (예: ["mbti", "enneagram"]).
      explicit_hint: 사용자가 명시한 모드 ("compact"·"instant").

    반환:
      {"type": "A"|"B"|"C"|"D"|"E", "matched": str|None, "scope_out": str|None,
       "reason": str}
    """
    text = text or ""
    diagnoses = diagnoses or []
    hint = (explicit_hint or "").strip().lower()

    # E: 범위 밖 (우선 검사 — 사용자 다른 의도 보호)
    for redirect, tokens in SCOPE_OUT_TOKENS.items():
        matched = _contains_any(text, tokens)
        if matched:
            return {
                "type": "E",
                "matched": matched,
                "scope_out": redirect,
                "reason": (
                    f"본 스킬 범위 밖. '{matched}' 토큰 매치 → "
                    f"vision-{redirect} 안내"
                ),
            }

    # D: 즉답 요청
    if hint == "instant" or _contains_any(text, INSTANT_TOKENS):
        return {
            "type": "D",
            "matched": _contains_any(text, INSTANT_TOKENS) or "instant",
            "scope_out": None,
            "reason": "즉답 요청 — 5단계 안내 후 사용자 선택",
        }

    # C: 압축 모드 (다수 진단 보유 + 압축 요청)
    compact_match = _contains_any(text, COMPACT_TOKENS)
    if hint == "compact" or compact_match:
        if len(diagnoses) >= 2 or compact_match:
            return {
                "type": "C",
                "matched": compact_match or "compact",
                "scope_out": None,
                "reason": "압축 모드 — Step 1·3·4 + Step 5",
            }

    # B/A
    if diagnoses:
        return {
            "type": "B",
            "matched": ",".join(diagnoses),
            "scope_out": None,
            "reason": f"진단 결과 보유 ({len(diagnoses)}종) — Self-Route 활용",
        }
    return {
        "type": "A",
        "matched": None,
        "scope_out": None,
        "reason": "진단 결과 없음 — 5단계 풀 코칭 (30~45분)",
    }


# ---------------------------------------------------------------------------
# 3. Step 4 질문 선택 (나이 기반) — SKILL.md Step 4 "나이 불명 시 기본값"
# ---------------------------------------------------------------------------


def select_step4_question(age: int | None, honorific: str | None = None) -> dict:
    """나이로 Step 4 질문을 결정한다.

      age ≥ 40 → "80세 임종" 질문
      그 외(나이 불명·미만) → "5년 후 가장 아쉬울 것" 질문

    SKILL.md 원문:
      "80세 임종" 질문은 무게감이 크므로 명확히 중년 이상임이 확인될 때만 사용.
      나이 불명 시 기본값은 "5년 후" 버전.
    """
    h = honorific or HONORIFIC_DEFAULT
    q_eighty = (
        f"{h}이 80세에 임종을 맞이하셨을 때, "
        f"*추구하지 않은 것에 대해 가장 후회할 1순위*는 무엇일까요?"
    )
    q_five_year = (
        f"지금 {h}이 *못 추구하면 5년 후 가장 아쉬울* 것은 무엇일까요?"
    )
    q_legacy = (
        f"{h} 자녀(또는 다음 세대)에게 *반드시 전수하고 싶은* 것은 무엇인가요?"
    )

    if isinstance(age, int) and age >= 40:
        chosen = "eighty"
        primary = q_eighty
    else:
        chosen = "five_year"
        primary = q_five_year

    return {
        "chosen": chosen,
        "primary_question": primary,
        "supplementary": q_legacy,
        "age": age,
    }


# ---------------------------------------------------------------------------
# 4. 진단 종류 → Step 매핑 (SKILL.md "진단 결과 통합 (Self-Route) 가이드")
# ---------------------------------------------------------------------------

DIAGNOSIS_STEP_MAP: dict[str, int | list[int]] = {
    "values": 1,
    "enneagram": 1,
    "mbti": 2,
    "strong": 2,
    "multipleintel": 2,
    "readiness": 4,
    "cys-competence": [1, 2, 3, 4],
}

DIAGNOSIS_KEY_ALIASES: dict[str, str] = {
    "vision-values": "values",
    "가치진단": "values",
    "가치": "values",
    "vision-enneagram": "enneagram",
    "에니어그램": "enneagram",
    "vision-mbti": "mbti",
    "mbti": "mbti",
    "vision-strong": "strong",
    "strong": "strong",
    "riasec": "strong",
    "vision-multipleintel": "multipleintel",
    "다중지능": "multipleintel",
    "multiple-intelligences": "multipleintel",
    "vision-readiness": "readiness",
    "준비도": "readiness",
    "readiness": "readiness",
    "vision-cys-competence": "cys-competence",
    "cys-competence": "cys-competence",
    "cys 비전 역량": "cys-competence",
}


def normalize_diagnosis_key(raw_key: str) -> str | None:
    """진단 키 정규화. 미지원이면 None."""
    if not raw_key:
        return None
    k = raw_key.strip().lower()
    if k in DIAGNOSIS_STEP_MAP:
        return k
    return DIAGNOSIS_KEY_ALIASES.get(k)


def map_diagnosis_to_step(raw_key: str) -> dict:
    """진단 키 → Step 번호 반환.

    반환: {"key": <정규화 키>, "step": int|list[int]|None, "valid": bool}
    """
    norm = normalize_diagnosis_key(raw_key)
    if not norm:
        return {"key": raw_key, "step": None, "valid": False}
    return {
        "key": norm,
        "step": DIAGNOSIS_STEP_MAP[norm],
        "valid": True,
    }


# ---------------------------------------------------------------------------
# 5. 진단별 통합 질문 고정 출력 (SKILL.md 표 1:1 대응 — 단정형 누설 방지)
# ---------------------------------------------------------------------------


def render_diagnosis_question(
    raw_key: str,
    honorific: str | None = None,
    type_num: int | str | None = None,
) -> str:
    """진단별 통합 질문을 SKILL.md 표 원문대로 출력한다.

    LLM이 자유 추론으로 질문을 변형하면 "ENFP니까 ~"류 단정형이
    스며들 수 있다 → 고정 텍스트로 차단.
    """
    h = honorific or HONORIFIC_DEFAULT
    norm = normalize_diagnosis_key(raw_key)
    if not norm:
        raise ValueError(f"미지원 진단 키: {raw_key!r}")

    if norm == "values":
        return (
            f"가치 진단 결과를 보셨을 때, 어떤 가치가 가장 '{h} 답다'고 "
            "느껴지셨나요? 그 가치가 지금 추구하시는 것에 얼마나 담겨 있는 "
            "것 같으세요?"
        )
    if norm == "enneagram":
        num_str = f"{type_num}번 " if type_num not in (None, "", 0) else ""
        return (
            f"에니어그램 {num_str}결과를 보셨을 때, 가장 '이게 {h}답다' "
            "싶었던 부분이 있으셨나요? 그리고 그 부분이 지금 비전을 "
            "생각하시는 것과 어떻게 이어지는 것 같으세요?"
        )
    if norm == "mbti":
        return (
            "MBTI 결과가 '나답다'고 느껴진 부분이 있으셨나요? 특히 "
            "에너지를 얻는 방식(E/I)이나 일을 마무리하는 방식(J/P)이 "
            "활동 패턴에 어떻게 반영되는 것 같으세요?"
        )
    if norm == "strong":
        return (
            "STRONG 검사 결과를 보셨을 때, '아, 이게 내가 좋아하는 "
            "영역이구나' 하고 가장 공감됐던 부분이 있으셨나요? 그 영역의 "
            "활동을 실제로 하실 때 몰입되시나요?"
        )
    if norm == "multipleintel":
        return (
            "다중지능 결과 중 가장 '이건 정말 나답다'고 느껴진 지능이 "
            "있으셨나요? 그 지능을 쓸 때와 그렇지 않을 때 어떻게 다르게 "
            "느껴지시나요?"
        )
    if norm == "readiness":
        return (
            "준비도 진단에서 어떤 영역이 가장 약하게 나왔나요? 그 약한 "
            "영역이 비전 추구를 망설이게 하는 것과 어떻게 연결되는 것 "
            "같으세요?"
        )
    if norm == "cys-competence":
        return (
            "CYS 비전 역량 결과를 보셨을 때, 어떤 역량이 가장 낮게 "
            "나왔고 그 부분이 비전 방향과 어떻게 연결되는 것 같으세요?"
        )
    raise ValueError(f"미구현 진단 키 분기: {norm}")


# ---------------------------------------------------------------------------
# 6. 비전 한 문장 5요소 구조 검증 (SKILL.md Step 5)
# ---------------------------------------------------------------------------

# 동사구 명사형 ("~하는 것" 등)
# SKILL.md Step 5 형식 — 동사구: "~하는 것", "~를 이루는 것", "~를 전수하는 것"
# 즉 한국어 동사 명사형 "~는 것" 일반 패턴.
_VERB_PHRASE_RE = re.compile(
    r"[가-힣]+(?:는|던)\s*(?:것|일)"
    r"|[가-힣]+(?:음|기)(?:[을를이가는도]|\s|$)"
)

# 한 문장 검사 — 문장 종결부호 ≤ 1 개 (마침표·물음표·느낌표 합산)
_TERMINAL_RE = re.compile(r"[.!?。！？]")


def validate_vision_sentence(sentence: str) -> dict:
    """Step 5 산출 문장 5요소 구조 검증.

    형식: [동사구(명사형)] + [대상] + [가치] + [영향 범위] + [선택: 수단/맥락]

    검사 항목:
      - is_nonempty
      - is_single_sentence (종결부호 ≤ 1)
      - has_verb_phrase (동사구 명사형)
      - approx_length (10~120 글자 권장)
      - issues 리스트
    """
    s = (sentence or "").strip()
    issues: list[str] = []

    is_nonempty = bool(s)
    if not is_nonempty:
        issues.append("빈 문장")

    # 한 문장: 종결부호가 1개 이하 (없으면 0개로 통과 — 인용 시 마침표 생략 허용)
    n_terminal = len(_TERMINAL_RE.findall(s))
    is_single_sentence = n_terminal <= 1
    if not is_single_sentence:
        issues.append(f"종결부호 {n_terminal}개 — 한 문장 형식 위반")

    has_verb_phrase = bool(_VERB_PHRASE_RE.search(s))
    if not has_verb_phrase:
        issues.append("동사구 명사형(~하는 것·~를 이루는 것 등) 미발견")

    length = len(s)
    approx_length_ok = 10 <= length <= 120
    if not approx_length_ok:
        issues.append(f"길이 {length}자 — 권장 10~120자 벗어남")

    structure_ok = is_nonempty and is_single_sentence and has_verb_phrase
    return {
        "sentence": s,
        "is_nonempty": is_nonempty,
        "is_single_sentence": is_single_sentence,
        "has_verb_phrase": has_verb_phrase,
        "approx_length_ok": approx_length_ok,
        "length": length,
        "structure_ok": structure_ok,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# 7. 단정형 표현 검출 (SKILL.md 절대 원칙 8 — "○○형이니까 ~이다" 금지)
# ---------------------------------------------------------------------------

# 진단 결과 유형 토큰
_DIAG_TYPE = (
    r"(?:"
    r"ENFP|INFP|ENFJ|INFJ|ENTP|INTP|ENTJ|INTJ|"
    r"ESFP|ISFP|ESFJ|ISFJ|ESTP|ISTP|ESTJ|ISTJ|"
    r"\d+번\s*유형|\d+\s*유형|\d+번|타입\s*\d+|"
    r"(?:언어|논리수학|논리·수학|공간|음악|신체운동|신체·운동|"
    r"대인관계|자기성찰|자연친화|자연주의|존재)\s*지능|"
    r"\d+유형형?"
    r")"
)
# 인과 연결사
_LINK = r"(?:이?니까|이?라서|이라\s*면|이?면|이?기에|이?므로)"
# 단정 종결구 (이다·할 것·해야·입니다·한다·합니다·이어야 한다 등)
_VERDICT = (
    r"(?:해야(?:\s*한다|\s*합니다)?|"
    r"할\s*것(?:이다|입니다)?|"
    r"이어야(?:\s*한다|\s*합니다)|"
    r"여야(?:\s*한다|\s*합니다)|"
    r"일\s*것(?:이다|입니다)?|"
    r"이다|입니다|한다|합니다|"
    r"맞다|맞습니다|"
    r"어울린다|어울립니다)"
)

# 진단 결과 결과지(MBTI·에니어그램 등) 단정형
_DIAG_RESULT = r"(?:MBTI|에니어그램|다중지능|STRONG|RIASEC|가치\s*진단)"

_ASSERTIVE_PATTERNS: list[tuple[str, str]] = [
    # ① "[진단 토큰] + 니까/라서 + ... + 종결구"
    (
        rf"(?P<token>{_DIAG_TYPE})\s*{_LINK}\s*[^\.\?!]{{0,80}}?{_VERDICT}",
        "type-based 단정",
    ),
    # ② "[진단 토큰] + 은/는 + 반드시/꼭/항상 + ... + 종결구"
    (
        rf"(?P<token>{_DIAG_TYPE})\s*(?:은|는)\s*"
        rf"(?:반드시|꼭|항상|언제나|당연히|무조건)\s*"
        rf"[^\.\?!]{{0,80}}?{_VERDICT}",
        "type-then-must 단정",
    ),
    # ③ "[MBTI/에니어그램 등] 결과 + 니까/라서 + ... + 종결구"
    (
        rf"(?P<token>{_DIAG_RESULT})\s*결과(?:가|는|에)?\s*"
        rf"[^\.\?!]{{0,40}}?{_LINK}\s*"
        rf"[^\.\?!]{{0,80}}?{_VERDICT}",
        "diagnosis-result 단정",
    ),
]


def detect_assertive_phrases(text: str) -> list[dict]:
    """단정형 표현 검출. 매치 리스트 반환.

    검출 시 SKILL.md 절대 원칙 8 위반 → 코치가 즉시 질문형으로 재작성해야 함.
    """
    if not text:
        return []
    hits: list[dict] = []
    for pat, label in _ASSERTIVE_PATTERNS:
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            hits.append({
                "label": label,
                "match": m.group(0),
                "token": m.group("token"),
                "span": [m.start(), m.end()],
            })
    return hits


# ---------------------------------------------------------------------------
# 8. 이모지 검증 (SKILL.md 톤·스타일 — 5종만 허용)
# ---------------------------------------------------------------------------

ALLOWED_EMOJIS = {"🪞", "⚡", "🎬", "⏳", "✨"}


def _iter_emojis(text: str):
    for ch in text:
        cat = unicodedata.category(ch)
        # So = Symbol, other (emoji 대부분)
        if cat == "So":
            yield ch
        # 변형 셀렉터/스킨톤은 무시 — 핵심 emoji 코드포인트만 검사


def validate_emoji_usage(text: str) -> dict:
    """본 스킬 응답에 허용된 5종 외 이모지가 포함됐는지 검사."""
    found = list(_iter_emojis(text or ""))
    violations = [e for e in found if e not in ALLOWED_EMOJIS]
    return {
        "found": found,
        "violations": violations,
        "is_clean": len(violations) == 0,
    }


# ---------------------------------------------------------------------------
# 9. 세션 시작 문구 고정 출력 (SKILL.md "세션 시작 문구")
# ---------------------------------------------------------------------------


def render_opening_template() -> str:
    """SKILL.md 원문 그대로 — LLM 변형 차단."""
    return (
        "비전이 막연하거나 방향이 잘 안 잡히실 때, 함께 끄집어내 "
        "드리겠습니다.\n\n"
        "지금 마음속에 있는 것을 편하게 말씀해 주세요. 한 문장이어도 좋고, "
        "\"그냥 뭔가 하고 싶은데 모르겠다\"는 느낌이어도 좋습니다.\n\n"
        "혹시 이전에 하신 진단 결과가 있으시면 함께 알려 주세요 "
        "(MBTI · 에니어그램 · 다중지능 · STRONG · 가치 진단 · "
        "CYS 비전 역량 중 하나라도). 있으면 코칭 정밀도가 높아집니다."
    )


def render_step5_check(honorific: str, sentence: str) -> str:
    """Step 5 되돌려 반영 의무 문구."""
    h = honorific or HONORIFIC_DEFAULT
    return (
        f"{h} 비전 핵심을 제가 이렇게 정리했습니다 — \"{sentence}\". "
        "정확히 짚었나요? 보강할 부분이 있을까요?"
    )


# ---------------------------------------------------------------------------
# CLI 디스패처
# ---------------------------------------------------------------------------


def _emit(payload: Any) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="clarity_lib")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("honorific")
    p.add_argument("--doctor", default="false")
    p.add_argument("--title", default="")
    p.add_argument("--name", default="")
    p.add_argument("--informal", default="false")

    p = sub.add_parser("input_type")
    p.add_argument("--text", required=True)
    p.add_argument("--diagnoses", default="")
    p.add_argument("--hint", default="")

    p = sub.add_parser("step4")
    p.add_argument("--age", default="")
    p.add_argument("--honorific", default=HONORIFIC_DEFAULT)

    p = sub.add_parser("diag_step")
    p.add_argument("--key", required=True)

    p = sub.add_parser("diag_question")
    p.add_argument("--key", required=True)
    p.add_argument("--honorific", default=HONORIFIC_DEFAULT)
    p.add_argument("--type_num", default="")

    p = sub.add_parser("validate_sentence")
    p.add_argument("--sentence", required=True)

    p = sub.add_parser("detect_assertive")
    p.add_argument("--text", required=True)

    p = sub.add_parser("emoji_check")
    p.add_argument("--text", required=True)

    sub.add_parser("opening")

    p = sub.add_parser("step5_check")
    p.add_argument("--honorific", default=HONORIFIC_DEFAULT)
    p.add_argument("--sentence", required=True)

    args = parser.parse_args(argv)
    cmd = args.cmd

    if cmd == "honorific":
        meta = {
            "is_doctor": args.doctor.lower() == "true",
            "title": args.title,
            "name": args.name,
            "is_informal": args.informal.lower() == "true",
        }
        _emit({"honorific": select_honorific(meta), "meta": meta})
        return 0

    if cmd == "input_type":
        diagnoses = [d.strip() for d in args.diagnoses.split(",") if d.strip()]
        _emit(classify_input_type(args.text, diagnoses, args.hint))
        return 0

    if cmd == "step4":
        age = int(args.age) if args.age.strip().isdigit() else None
        _emit(select_step4_question(age, args.honorific))
        return 0

    if cmd == "diag_step":
        _emit(map_diagnosis_to_step(args.key))
        return 0

    if cmd == "diag_question":
        type_num = args.type_num if args.type_num else None
        try:
            q = render_diagnosis_question(args.key, args.honorific, type_num)
            _emit({"key": args.key, "question": q})
        except ValueError as e:
            _emit({"error": str(e)})
            return 2
        return 0

    if cmd == "validate_sentence":
        _emit(validate_vision_sentence(args.sentence))
        return 0

    if cmd == "detect_assertive":
        _emit({"hits": detect_assertive_phrases(args.text)})
        return 0

    if cmd == "emoji_check":
        _emit(validate_emoji_usage(args.text))
        return 0

    if cmd == "opening":
        _emit({"opening": render_opening_template()})
        return 0

    if cmd == "step5_check":
        _emit({
            "check": render_step5_check(args.honorific, args.sentence),
        })
        return 0

    parser.error(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
