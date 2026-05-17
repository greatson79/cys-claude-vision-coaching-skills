"""vision-three-realm-balance 결정론 환원 모듈.

최윤식 박사 『미래준비학교』(2016) 비전 영역 3겹 다이어그램의
- 8개 패턴 매트릭스
- ○/△/✗ 정규화
- 호칭 분기
- 입력 유형 분류
- 특수 케이스 라우팅
- 박사님 책 인용 정확성 검증
을 결정론적으로 처리한다. LLM 자연어 추론을 통한 할루시네이션을 구조적으로 차단한다.

SKILL.md "3단계 — 균형 진단 (8개 패턴)" / "사용자 호칭 분기" / "입력 분기" / "처리 흐름 — 특수 입력 케이스" / "절대 원칙"의 1:1 결정론 환원이다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


# --------------------------------------------------------------------------
# 1. ○/△/✗ 정규화
# --------------------------------------------------------------------------

# 받아들이는 입력 토큰을 정규형으로 매핑한다. △는 SKILL.md "3단계" 규약에 따라
# 보수적으로 ✗로 환원한다.
_OK_TOKENS = {"O", "o", "○", "예", "강함", "yes", "Y", "y", "1", "ok", "OK", "true", "True"}
_MID_TOKENS = {"△", "M", "m", "mid", "MID", "보통", "애매", "부분", "0.5", "half", "maybe"}
_X_TOKENS = {"X", "x", "✗", "아니오", "약함", "no", "N", "n", "0", "false", "False", "ng", "NG"}


def normalize_mark(token: str) -> str:
    """입력 마크 한 글자/단어를 'O'/'M'/'X' 중 하나로 환원한다.

    △/'mid' 등 모호한 입력은 'M'으로 보존되며, diagnose() 단계에서 보수적으로 ✗ 처리된다.
    매칭 안 되는 입력은 ValueError.
    """
    if token is None:
        raise ValueError("mark token is None")
    s = str(token).strip()
    if s in _OK_TOKENS:
        return "O"
    if s in _MID_TOKENS:
        return "M"
    if s in _X_TOKENS:
        return "X"
    raise ValueError(f"unknown mark token: {token!r}")


def normalize_triple(raw: Iterable[str]) -> tuple[str, str, str]:
    """3개 마크 입력을 표준 (O/M/X, O/M/X, O/M/X) 튜플로 환원한다."""
    items = list(raw)
    if len(items) != 3:
        raise ValueError(f"triple must have exactly 3 marks, got {len(items)}")
    return tuple(normalize_mark(m) for m in items)  # type: ignore[return-value]


def conservative_collapse(triple: tuple[str, str, str]) -> tuple[str, str, str]:
    """SKILL.md 규약: △(M)는 진단 매트릭스 적용 시 ✗(X)로 환원한다.

    명료화 후에도 △가 유지된 경우의 보수적 처리. (원본 M 정보 보존이 필요한 경우
    호출 측에서 별도로 raw triple을 들고 있어야 한다.)
    """
    return tuple("X" if m == "M" else m for m in triple)  # type: ignore[return-value]


# --------------------------------------------------------------------------
# 2. 8개 패턴 매트릭스 — SKILL.md "3단계" 표를 1:1로 옮긴 결정론 사전
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Diagnosis:
    pattern: tuple[str, str, str]
    name: str
    risk: str
    remedy: str
    weak_realms: tuple[int, ...]
    next_step: str
    is_healthy: bool

    def display_marks(self) -> str:
        return " ".join("○" if m == "O" else ("△" if m == "M" else "✗") for m in self.pattern)


# (① 나, ② 가족·세상, ③ 정신적) 순서를 *반드시* 유지한다.
_PATTERN_TABLE: dict[tuple[str, str, str], Diagnosis] = {
    ("O", "O", "O"): Diagnosis(
        pattern=("O", "O", "O"),
        name="건강한 비전",
        risk="없음",
        remedy="5단계로 진행 — 균형 잡힌 한 문장으로 비전 재진술",
        weak_realms=(),
        next_step="5단계: 균형 잡힌 비전 한 문장 재진술",
        is_healthy=True,
    ),
    ("O", "O", "X"): Diagnosis(
        pattern=("O", "O", "X"),
        name="정신적 가치 결여",
        risk="중",
        remedy="원 ③ 강화 — 영감·소명감·도덕적 가치 보강 (vision-mission-frame 활용)",
        weak_realms=(3,),
        next_step="원 ③ 강화 후 재진단",
        is_healthy=False,
    ),
    ("O", "X", "O"): Diagnosis(
        pattern=("O", "X", "O"),
        name="가족·세상 단절",
        risk="중",
        remedy="원 ② 강화 — 비전 결과물이 가족·이웃·인류에 어떤 기여를 하는지 추가",
        weak_realms=(2,),
        next_step="원 ② 강화 후 재진단",
        is_healthy=False,
    ),
    ("X", "O", "O"): Diagnosis(
        pattern=("X", "O", "O"),
        name="자기 기쁨 부재",
        risk="중",
        remedy="원 ① 강화 — '이 비전이 나를 살아있게 하는가?' 재점검, 의무감만의 비전 경계",
        weak_realms=(1,),
        next_step="원 ① 강화 후 재진단",
        is_healthy=False,
    ),
    ("O", "X", "X"): Diagnosis(
        pattern=("O", "X", "X"),
        name="개인 욕망",
        risk="높음",
        remedy="원 ②③ 강화 — 가족·이웃·세상에 어떤 가치를 줄지 + 정신적·도덕 가치로 영감 검증",
        weak_realms=(2, 3),
        next_step="원 ②③ 강화 후 재진단",
        is_healthy=False,
    ),
    ("X", "O", "X"): Diagnosis(
        pattern=("X", "O", "X"),
        name="자기희생·세상일",
        risk="높음",
        remedy="원 ①③ 강화 — 본인의 진정한 기쁨 회복 + 지속 가능성 점검, 번아웃 위험 경고",
        weak_realms=(1, 3),
        next_step="원 ①③ 강화 후 재진단",
        is_healthy=False,
    ),
    ("X", "X", "O"): Diagnosis(
        pattern=("X", "X", "O"),
        name="왜곡된 사명·질",
        risk="높음",
        remedy="원 ①② 강화 — 도덕 기준이 본인·가족을 비참하게 만들지 않는지 점검, '균형 잃은 건강하지 않은 비전' 회피",
        weak_realms=(1, 2),
        next_step="원 ①② 강화 후 재진단",
        is_healthy=False,
    ),
    ("X", "X", "X"): Diagnosis(
        pattern=("X", "X", "X"),
        name="비전 아님",
        risk="최고",
        remedy="비전 재발견 필요 — vision-clarity-coaching · vision-readiness-visioncoding · vision-five-stages Stage 1 권유",
        weak_realms=(1, 2, 3),
        next_step="1단계로 복귀 — vision-clarity-coaching 등으로 비전 재발견",
        is_healthy=False,
    ),
}


def diagnose(triple: Iterable[str]) -> Diagnosis:
    """3개 마크 입력을 받아 SKILL.md 8개 패턴 중 정확히 하나의 Diagnosis를 반환.

    △(M) 입력은 보수적으로 ✗(X)로 환원되어 매트릭스 lookup이 수행된다.
    """
    raw = normalize_triple(triple)
    collapsed = conservative_collapse(raw)
    diag = _PATTERN_TABLE.get(collapsed)
    if diag is None:
        raise ValueError(f"no diagnosis for pattern {collapsed!r}")
    return diag


def all_patterns() -> list[Diagnosis]:
    """8개 패턴 전체를 반환 — 테스트·강의용."""
    return list(_PATTERN_TABLE.values())


# --------------------------------------------------------------------------
# 3. 호칭 분기 — SKILL.md "사용자 호칭 분기"의 결정론 환원
# --------------------------------------------------------------------------

# 박사님 본인 입력을 식별하는 토큰. 명시적 지칭만 박사님 호칭을 트리거한다.
_DOC_SELF_TOKENS = (
    "최윤식 박사",
    "최윤식박사",
    "박사 본인",
    "박사님 본인",
    "박사님이 직접",
    "박사님이 본인",
    "내가 최윤식",
    "저는 최윤식",
    "박사님 비전 점검",
)


def resolve_address(user_signal: str | None) -> str:
    """입력자에 대한 신호 문자열을 받아 호칭("박사님" 또는 "당신")을 결정.

    명시적으로 박사님 본인 표시가 없으면 일반 사용자로 간주하여 "당신" 반환.
    """
    if not user_signal:
        return "당신"
    s = str(user_signal)
    if any(tok in s for tok in _DOC_SELF_TOKENS):
        return "박사님"
    return "당신"


# --------------------------------------------------------------------------
# 4. 입력 유형 분류 (A·B·C·D) — SKILL.md "입력 처리 — 4유형"
# --------------------------------------------------------------------------

# B 유형(다중 후보)을 식별하는 토큰
_TYPE_B_TOKENS = (
    "후보", "여러 비전", "비전 후보", "어느 것이", "둘 중", "셋 중", "비교", "vs", " 또는 ",
    "두 가지 비전", "두 비전", "세 가지 비전", "세 비전",
    "비전이 충돌", "비전이 두", "비전이 세", "충돌합니다",
    "첫째 ", "둘째 ", "셋째 ",
    "어느 게", "어느 쪽", "어떤 게 더",
)

# D 유형(강의·코칭) 식별 토큰 — *진행 의도가 명확한 복합 패턴*만 사용한다.
# 단순히 "강의·세미나" 단어 하나로는 사용자 비전 텍스트 안에 들어간 경우와
# 강의·세미나 진행 요청을 구분할 수 없다. 따라서 "진행·안내·흐름·대상" 같은
# 진행 요청 신호와 결합한 복합 키워드만 D로 트리거한다.
_TYPE_D_TOKENS = (
    "세미나 진행", "세미나를 진행", "세미나에서 진행", "세미나에서 이 도구를 활용해 진행",
    "워크숍 진행", "워크숍을 진행", "워크샵 진행",
    "강의 진행", "강의 흐름", "강의 자료",
    "수련회 진행", "수련회 흐름", "수련회 청년",
    "청년부 진행", "청년부 세미나", "청년부 워크숍",
    "그룹 진행", "조모임 진행", "코칭 세션 진행",
    "흐름을 제안", "흐름과 자료를 제안", "진행 흐름", "진행 안내", "진행 방법",
    "흐름 짜", "흐름을 짜", "수련회 워크숍", "수련회 세미나",
    "강의 도입", "세미나 도입", "워크숍 도입", "강의를 어떻게 시작",
    "세미나를 어떻게 시작", "워크숍을 어떻게 시작",
    "1:1 코칭", "1대1 코칭", "일대일 코칭",
    "코칭 진행", "코칭 적용", "코칭에 적용",
    "도구 어떻게 적용", "도구 적용 방법", "도구를 적용",
    "청년부 코칭", "청년부 진행 중", "상담자 한 명",
    "명 대상", "대상으로 ", "대상 1시간", "대상 2시간", "대상 30분", "대상 90분",
    "분 세미나", "분 워크숍", "분 강의", "분 수련회",
)

# C 유형(박사님 본인) 식별 — 호칭 분기와 동일 토큰 재사용 + 직접 표현
_TYPE_C_TOKENS = _DOC_SELF_TOKENS

# 메타 질문(설명 흐름) 식별 — "정의" 같이 일반 단어는 결합 형태로만 매칭
# (사용자 비전 안에 "사회 정의"가 들어가면 false positive 위험).
_META_TOKENS = (
    "뭔가요", "뭐예요", "무엇인가요", "어떻게 활용", "어떻게 알", "활용법",
    "설명해", "다이어그램이",
    "개념 정의", "비전 정의", "비전이란 뭐", "비전이란 무엇",
    "도구 개념", "스킬 개념", "이론 개념",
)


# 메타 격상 트리거 — 외부 모델/개념 비교/도구 활용 질문은 진단이 아니라
# SKILL.md "처리 흐름 — 설명"으로 라우팅되어야 한다.
_META_ESCALATION_TOKENS = (
    "ikigai", "이키가이", "SMART 모델", "MBTI와", "에니어그램과",
    "차이가", "차이점", "어떻게 다른", "어떻게 비교", "비교 설명",
    "비전 vs 꿈", "비전 vs 목표", "비전과 꿈", "비전과 목표", "비전과 미션",
    "어떻게 사용", "사용법", "어떤 경우", "누구에게 쓸",
    "어떤 이론", "어떤 학계", "어떤 모델과", "닮았나요", "닮은",
    "유사한 이론", "유사한 모델", "학계 어떤", "학술적 입지",
    "학계 출처", "학계 자료", "선행 연구",
    "같이 사용", "함께 사용", "같이 쓰", "함께 쓰",
    "어디서 비롯", "어디서 왔", "기원이 어디", "이론적 근거",
)


def classify_input_type(user_text: str) -> str:
    """입력 텍스트를 'A'/'B'/'C'/'D'/'META'/'EMPTY' 중 하나로 분류.

    META는 SKILL.md "처리 흐름 — 설명"으로 라우팅.
    EMPTY는 비전 부재 케이스로 SKILL.md "비전 자체가 없는 사용자" 가지로 라우팅.
    분류 우선순위: EMPTY > META > C > B > D > A.

    외부 모델 비교(ikigai 등)·개념 차이 질문은 META로 자동 격상 — 진단이 아닌
    설명 흐름이기 때문이다.
    """
    if not user_text or not str(user_text).strip():
        return "EMPTY"
    s = str(user_text)

    if any(tok in s for tok in (
        "비전이 없", "비전을 모르", "무엇을 비전으로", "비전이 뭐인지",
        "비전이 도무지 떠오르지", "비전이 안 떠올라", "비전이 떠오르지 않",
        "비전이 흐릿", "비전을 못 찾", "비전을 찾을 수 없",
        "어디서 시작해야", "어떻게 비전을",
    )):
        return "EMPTY"

    if any(tok in s for tok in _META_TOKENS):
        return "META"

    if any(tok in s for tok in _META_ESCALATION_TOKENS):
        return "META"

    # D(강의·세미나) > C(박사님 본인) — 박사님이 청중에게 강의/세미나를 진행하는 경우
    # 처리 흐름은 D이며 호칭은 청중("당신")이어야 한다 (SKILL.md "처리 흐름 — 강의·코칭").
    if any(tok in s for tok in _TYPE_D_TOKENS):
        return "D"

    if any(tok in s for tok in _TYPE_C_TOKENS):
        return "C"

    if any(tok in s for tok in _TYPE_B_TOKENS):
        return "B"

    return "A"


# --------------------------------------------------------------------------
# 5. 특수 케이스 라우팅 — SKILL.md "처리 흐름 — 특수 입력 케이스"
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class SpecialCase:
    name: str
    handler: str
    note: str


# 키워드 → 특수 케이스 매핑. 결정론적 시그널만 사용한다.
_SPECIAL_CASE_RULES: tuple[tuple[tuple[str, ...], SpecialCase], ...] = (
    (
        ("10년 후", "20년 후", "30년 후", "n년 후", "단계별 비전", "시점 1", "시점 2"),
        SpecialCase(
            name="time_phased",
            handler="시간 순서 비전",
            note="각 시점 비전을 별도로 3영역 점검 후 시점별 결과 비교. 후기 ○○○으로 수렴 여부 확인.",
        ),
    ),
    (
        (
            "직장에서", "가정에서", "회사에서는", "교회에서는", "역할별",
            "역할에서만", "각 역할", "한 역할만", "이 역할만",
            "역할 하나만", "하나만 떼어",
        ),
        SpecialCase(
            name="role_split",
            handler="역할별 분리 비전",
            note="각 역할 비전을 별도로 점검하되 박사님 책 관점 통합 비전으로 재정렬 권유.",
        ),
    ),
    (
        # 자녀·아이는 본인 비전으로 잘못 제시되는 빈도가 높아 단독 키워드로 매칭한다.
        # 남편·아내는 *외부 강요 케이스의 주체*로 등장하는 경우가 많으므로 strict
        # 미래상 표현(되기를·되도록·잘 되는 것·행복 등)과 결합할 때만 매칭한다.
        (
            "자녀가", "아이가", "자녀를",
            "배우자가 잘", "배우자가 되", "배우자가 행복", "배우자가 성공",
            "제자가 잘", "제자가 되", "제자가 성공",
            "남편이 잘 되", "남편이 행복", "남편이 성공해",
            "아내가 잘 되", "아내가 행복", "아내가 성공해",
        ),
        SpecialCase(
            name="other_oriented",
            handler="타인에 대한 비전",
            note="타인 기대·바람을 본인 인생 방향으로 재구성 권유 후 3영역 점검.",
        ),
    ),
    (
        ("부부", "팀", "공동체", "교회 비전", "조 비전", "그룹 비전"),
        SpecialCase(
            name="group_vision",
            handler="그룹/팀/부부 공동 비전",
            note="개인 비전 별도 점검 후 공동 영역 도출. ① '나'를 공동체 구성원 전체로 확장은 코치 일반 해석임을 표시.",
        ),
    ),
    (
        ("천국", "영생", "하나님 영광", "내세", "영원", "신앙적 비전"),
        SpecialCase(
            name="eschatological",
            handler="내세적/영원 시점 비전",
            note="현세 삶의 향하는 방향으로 번역 권유 후 3영역 점검. 박사님 책 인용 범위 외 신학 판단 회피.",
        ),
    ),
    (
        ("100점", "점수", "정량화", "정량", "점수화", "환산", "%"),
        SpecialCase(
            name="quantification",
            handler="정량화·점수화 요청",
            note="박사님 책에 점수화 방식 명시 없음 — 임시 환산은 코치 일반 지식 표시 + 박사님 책 인용 위장 금지.",
        ),
    ),
    (
        # "차이" 단독은 너무 광범위해 사용자 비전 안의 "차이"에도 매칭될 위험이 있으므로
        # *비전·꿈·목표·미션* 결합 형태로만 매칭한다.
        (
            "비전 vs 꿈", "비전 vs 목표", "비전과 꿈", "비전과 목표", "비전과 미션",
            "비전 차이", "꿈 차이", "목표 차이", "미션 차이",
            "비전과 꿈의 차이", "비전과 목표의 차이", "비전·꿈·목표",
            "꿈과 비전", "목표와 비전",
        ),
        SpecialCase(
            name="concept_compare",
            handler="개념 비교 요청",
            note="본 스킬은 비전 건강도 점검 전담. 개념 정의는 vision-five-stages·vision-statement-writer로 전환 권유.",
        ),
    ),
    (
        ("ikigai", "이키가이", "SMART", "MBTI", "에니어그램", "다중지능", "Big5"),
        SpecialCase(
            name="external_model",
            handler="외부 모델 비교 요청",
            note="박사님 책 영역 명확화 후 외부 모델은 별도 표시. 박사님 인용으로 위장 금지.",
        ),
    ),
    (
        # *영역 확장 제안*만 매칭한다 — "환경 영역", "생태 영역" 같은 영역화 표현
        # + "추가하면", "넣으면", "포함" 등 확장 의도가 있어야 한다.
        (
            "영역 추가", "영역을 추가", "영역에 추가",
            "환경 영역", "지구 영역", "생태 영역", "기후 영역", "AI 영역", "기술 영역",
            "4영역으로", "5영역으로", "4번째 원", "5번째 원", "원 ④", "원 ⑤",
            "추가하면 어떨", "추가하면 안",
            "확장하면",
        ),
        SpecialCase(
            name="domain_extension",
            handler="사용자 확장 제안",
            note="박사님 책 3영역은 원본 그대로 유지. 사용자 확장은 개인적 해석으로 별도 표시 — 단 본 스킬 진단은 원본 3영역 기준.",
        ),
    ),
    (
        ("절대", "회피", "피하고 싶", "~하지 않겠", "안 ~겠다", "않겠다"),
        SpecialCase(
            name="negative_vision",
            handler="부정형/회피형 진술",
            note="회피 동기는 반-비전 — 향하는 방향(positive vision)으로 전환 질문 후 진단.",
        ),
    ),
    (
        (
            "부모가 시켜", "회사가 원해", "남이 시켜", "외부에서", "강요",
            "시키는 대로", "시켜서", "강요받아", "남편이 시키", "아내가 시키",
            "부모님이 원해", "윗사람이 시키",
        ),
        SpecialCase(
            name="externally_imposed",
            handler="외부 강요·타인 명령",
            note="진단 가능하되 점검 ①이 ✗ 가능성 사전 안내. 내면의 향하는 방향 재탐색 권유 가능.",
        ),
    ),
    (
        ("짧게", "결과만", "요약", "간단히", "quick", "퀵 진단"),
        SpecialCase(
            name="quick_mode",
            handler="Quick 진단 모드",
            note="각 점검 한 문장 질문 → 패턴명 + 한 줄 처방 + 박사님 책 인용 1줄로 압축.",
        ),
    ),
)


def detect_special_cases(user_text: str) -> list[SpecialCase]:
    """입력 텍스트에서 특수 케이스 시그널을 탐지해 모든 매칭을 반환.

    매칭이 없으면 빈 리스트. 동시 매칭(예: 시간 순서 + 정량화)도 모두 반환하여
    SKILL.md 흐름에 따라 코치가 우선순위 결정을 내릴 수 있게 한다.
    """
    if not user_text:
        return []
    s = str(user_text)
    hits: list[SpecialCase] = []
    for keywords, case in _SPECIAL_CASE_RULES:
        if any(k in s for k in keywords):
            hits.append(case)
    return hits


# --------------------------------------------------------------------------
# 6. 박사님 책 인용 정확성 검증
# --------------------------------------------------------------------------

# SKILL.md 본문에 *원문 그대로* 보존된 박사님 책 인용 5개.
# 한 글자라도 어긋나면 verify_quote()가 False를 반환해 할루시네이션을 차단.
CYS_QUOTES: dict[str, str] = {
    "role_opening": (
        "강한 비전은 높은 정신적 만족감을 준다. 그러나 참된 정신적 가치는 동시에 "
        "이웃(가족과 세상, 인류)에게도 기쁨이 되어야 하고, 나 자신에게도 진정한 기쁨을 "
        "주어야 한다. 윤리와 도덕, 양심을 추구하는 것은 매우 좋고 올바른 방향이지만 "
        "나와 가족 이웃 세상에 기쁨을 주지 못한다면, 그것은 건강하지 않은 비전이다."
    ),
    "circle3_warning": (
        "비전이란 이름으로, 높은 도덕적 기준을 내세워 나를 괴롭게 하고, 가족과 이웃을 "
        "비참하게 만드는 것은 균형을 잃은 건강하지 않은 비전이다."
    ),
    "core_intersection_1": (
        "진정한 비전은 건강한 방향감을 가져야 한다. 정신적으로도 가치 있고, "
        "이웃(가족과 세상, 인류)에도 가치 있고 동시에 나 자신에게도 가치 있어야 한다."
    ),
    "core_intersection_2": (
        "가족과 이웃에게만 가치 있고 즐거움을 주는 것이라면 단지 좋은 세상일일 뿐 "
        "나의 비전이 아닐 가능성이 크다... 비전이 나에게만 가치 있고 즐거움을 주는 "
        "욕망의 영역에 치우치지 않도록 경계해야 한다. 건강하고 균형 잡힌 비전은 "
        "나에게도 세상에도 정신적으로도 모두 기쁨이 되고 가치 있는 것이다."
    ),
    "closing": (
        "건강하고 균형 잡힌 비전은 나에게도 세상에도 정신적으로도 모두 기쁨이 되고 "
        "가치 있는 것이다. '정신적 가치'를 점검할 때 3가지 영역을 점검해야 하는 이유이다."
    ),
}

CITATION_SOURCE = "최윤식 박사 『미래준비학교』(2016)"


def get_quote(key: str) -> str:
    """등록된 5개 박사님 인용 중 하나를 정확히 반환. 없는 키 → KeyError."""
    if key not in CYS_QUOTES:
        raise KeyError(f"unknown quote key: {key!r}. Valid: {list(CYS_QUOTES.keys())}")
    return CYS_QUOTES[key]


def verify_quote(key: str, candidate: str) -> bool:
    """LLM이 만들어낸 인용 후보 candidate가 등록된 원문과 정확히 일치하는지 검증.

    공백 정규화는 하지 않는다. 한 글자라도 다르면 False — 박사님 인용을 LLM이
    *재진술*하여 발생하는 할루시네이션을 구조적으로 차단한다.
    """
    if key not in CYS_QUOTES:
        return False
    return candidate.strip() == CYS_QUOTES[key].strip()


def render_quote(key: str) -> str:
    """SKILL.md 출처 표시 규약(7번)에 맞춰 *원문 + 출처*를 한 블록으로 렌더링."""
    return f"> *\"{get_quote(key)}\"*\n> — {CITATION_SOURCE}"


# --------------------------------------------------------------------------
# 7. 절대 원칙 self-check
# --------------------------------------------------------------------------

ABSOLUTE_PRINCIPLES: tuple[tuple[str, str], ...] = (
    ("realm_names", "3영역 명칭 그대로: 개인 욕망 / 자기희생·세상일 / 왜곡된 사명·질"),
    ("simultaneous", "3영역 모두 동시 만족 — 한 영역 극대화 X"),
    ("ethics_only", "윤리·도덕만 강조 = 왜곡된 사명"),
    ("sacrifice_only", "자기희생만 = 자기 소진"),
    ("desire_only", "자기 기쁨만 = 개인 욕망"),
    ("healthy", "건강한 비전 = 3원 교집합 균형"),
    ("citation", "박사님 책 인용은 따옴표 표시 + 출처 명시(『미래준비학교』 2016)"),
    ("address", "호칭 분기 일관 — 한 응답 내 박사님/당신 혼용 금지"),
    ("no_hallucination", "할루시네이션 금지 — 박사님 책 외 내용은 별도 표시"),
    ("no_page_guess", "페이지 번호 추측·날조 금지 — 본 스킬에 페이지 단위 정보 없음"),
)


def list_principles() -> list[tuple[str, str]]:
    """SKILL.md '절대 원칙 — 박사님 책 충실' 10항을 코드 진실의 단일 소스로 반환."""
    return list(ABSOLUTE_PRINCIPLES)


# --------------------------------------------------------------------------
# 8. 통합 분석 API — 한 번의 호출로 입력 분류·특수 케이스·진단까지
# --------------------------------------------------------------------------

@dataclass
class AnalysisResult:
    input_type: str
    address: str
    special_cases: list[SpecialCase] = field(default_factory=list)
    diagnosis: Diagnosis | None = None
    notes: list[str] = field(default_factory=list)


def analyze(
    user_text: str,
    triple: Iterable[str] | None = None,
    user_signal: str | None = None,
) -> AnalysisResult:
    """결정론 통합 분석 — 호칭·입력 유형·특수 케이스·진단을 한 번에 산출.

    triple이 제공되면 진단까지 수행한다. None이면 분류·특수 케이스만 반환.
    user_signal이 None이면 user_text를 호칭 분기 입력으로도 사용한다.
    """
    address = resolve_address(user_signal if user_signal is not None else user_text)
    input_type = classify_input_type(user_text)
    specials = detect_special_cases(user_text or "")
    notes: list[str] = []

    # D 흐름에서는 청중 응대이므로 호칭이 "박사님"이어서는 안 된다
    # (SKILL.md 처리 흐름 — 강의·코칭: "코치 본인이 박사님인 경우 청중 응대 시
    # 청중을 '박사님'이라 부르지 않음 — 이는 박사님 본인 호칭 전용").
    if input_type == "D" and address == "박사님":
        address = "당신"
        notes.append("D 흐름 호칭 override — 청중 응대이므로 '박사님' → '당신'")

    if input_type == "EMPTY":
        notes.append(
            "비전 부재 케이스 — vision-clarity-coaching · vision-readiness-visioncoding · "
            "vision-five-stages Stage 1로 전환 권유"
        )
    elif input_type == "META":
        notes.append("메타 질문 — '처리 흐름 — 설명'으로 라우팅, 박사님 책 인용은 render_quote() 사용")
    elif input_type == "B":
        notes.append("다중 비전 후보 — '처리 흐름 — 비교'로 라우팅, 각 후보별 병렬 진단 후 비교 매트릭스 산출")
    elif input_type == "D":
        notes.append("강의·코칭 — '처리 흐름 — 강의·코칭'으로 라우팅, 청중·코치이 호칭은 그대로 사용")
    elif input_type == "C":
        notes.append("박사님 본인 입력 — 호칭 '박사님' 강제")
    else:
        notes.append("일반 진단 — '처리 흐름 — 진단'으로 라우팅")

    diag = diagnose(triple) if triple is not None else None
    return AnalysisResult(
        input_type=input_type,
        address=address,
        special_cases=specials,
        diagnosis=diag,
        notes=notes,
    )
