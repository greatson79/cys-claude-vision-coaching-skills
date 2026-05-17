"""박사님 3영역 모델의 학계 주류 문헌 1:1 대조 결정론 모듈.

최윤식 박사 『미래준비학교』(2016)는 *대중적 미래학·자기계발* 서적이며 동료심사 학술지
출간이 아니다. 그러나 박사님의 3영역(나의 기쁨 · 가족·세상 · 정신적) 구조는
학계 주류 심리학·철학 전통의 다층 모델과 광범위한 사상적 친연성을 갖는다.

본 모듈은 박사님 모델이 *학계 주류 어디와 어떻게* 공통점·차이점을 갖는지를
*외부 출처 URL과 함께* 결정론적으로 기록한다. LLM이 학술 출처를 자연어 추론으로
재진술하지 못하게 차단한다.

사용 시점: SKILL.md 처리 흐름에서 사용자가 외부 모델 비교·학계적 입지·근거 출처를
요청하면 본 모듈을 *반드시* 호출해 등록된 학계 출처를 가져온다.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalSource:
    """학계 주류 모델 1건의 결정론적 메타데이터."""

    key: str                      # 슬러그
    model_name: str               # 모델 정식 명칭
    authors: str                  # 주 저자(연도)
    primary_text: str             # 1차 텍스트(책·논문)
    elements: tuple[str, ...]     # 모델 핵심 영역
    citation_source_urls: tuple[str, ...]  # 외부 검증 URL
    mapping_to_cys: dict[int, str]  # 박사님 ①②③에 대한 매핑


# 박사님 3영역 정의(SKILL.md 본문과 일치):
# ① 나에게 기쁨 (개인 욕망 영역)
# ② 가족·세상에 기쁨·가치 (자기희생·세상일 영역)
# ③ 정신적·도덕적 가치 (왜곡된 사명·질 영역)
CYS_REALM_LABELS = {
    1: "나에게 기쁨 (원 ①)",
    2: "가족·세상에 기쁨·가치 (원 ②)",
    3: "정신적·도덕적 가치 (원 ③)",
}


EXTERNAL_SOURCES: tuple[ExternalSource, ...] = (
    ExternalSource(
        key="sdt_deci_ryan",
        model_name="Self-Determination Theory (자기결정 이론)",
        authors="Edward L. Deci & Richard M. Ryan (1985, 2000, 2017)",
        primary_text=(
            "Ryan, R. M., & Deci, E. L. (2000). Self-determination theory and the "
            "facilitation of intrinsic motivation, social development, and well-being. "
            "American Psychologist, 55(1), 68–78."
        ),
        elements=("Autonomy (자율성)", "Competence (유능성)", "Relatedness (관계성)"),
        citation_source_urls=(
            "https://en.wikipedia.org/wiki/Self-determination_theory",
            "https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf",
            "https://selfdeterminationtheory.org/theory/",
            "https://www.apa.org/research-practice/conduct-research/self-determination-theory.html",
        ),
        mapping_to_cys={
            1: "Autonomy + Competence ≈ 박사님 원 ① (본인이 자기 비전을 선택·숙달하여 진정한 기쁨을 얻음). SDT 핵심 인용: 'people are driven by three innate psychological needs ... satisfying these needs produces higher-quality motivation, greater well-being'",
            2: "Relatedness ≈ 박사님 원 ② (타인과의 연결·소속·관계가 핵심 가치). SDT 정의: 'the need to feel connected and a sense of belongingness with others'",
            3: "직접 매핑 영역 없음 — SDT는 영적·도덕 차원을 별도로 다루지 않음. 박사님 원 ③의 *영적·소명* 차원은 SDT의 'autonomous motivation'·'integrated regulation'에 부분적으로 함의되나 별도 영역으로 정의되지 않음.",
        },
    ),
    ExternalSource(
        key="frankl_logotherapy",
        model_name="Logotherapy 의미요법 — 세 가지 의미 원천",
        authors="Viktor E. Frankl (1946, 『Man's Search for Meaning』)",
        primary_text=(
            "Frankl, V. E. (1946/2006). Man's Search for Meaning. Boston: Beacon Press. "
            "Originally published as Ein Psycholog erlebt das Konzentrationslager."
        ),
        elements=(
            "Creative Values (창조적 가치)",
            "Experiential Values (경험적 가치)",
            "Attitudinal Values (태도적 가치)",
        ),
        citation_source_urls=(
            "https://www.simplypsychology.org/logotherapy.html",
            "https://positivepsychology.com/viktor-frankl-logotherapy/",
            "https://themeaningmovement.com/viktor-frankl-logotherapy-meaning-life/",
        ),
        mapping_to_cys={
            1: "Experiential Values ≈ 박사님 원 ① (사랑·아름다움·문화를 깊이 경험하며 얻는 본인의 기쁨). Frankl: 'experiencing something or encountering someone ... love, beauty, art, and culture'",
            2: "Creative Values ≈ 박사님 원 ② (창조·일·기여를 통해 세상에 가치를 더함). Frankl: 'producing, building, or contributing to the world through work or projects'",
            3: "Attitudinal Values ≈ 박사님 원 ③ (불가피한 고난에 대한 태도·소명·인간 존엄). Frankl: 'attitude she/he takes toward unavoidable suffering ... the highest and most profound form, fundamentally grounding human dignity'. *세 모델 중 가장 정밀한 1:1 대응.*",
        },
    ),
    ExternalSource(
        key="seligman_perma",
        model_name="PERMA 모델 (긍정심리학 5요소)",
        authors="Martin E. P. Seligman (2011, 『Flourish』)",
        primary_text=(
            "Seligman, M. E. P. (2011). Flourish: A Visionary New Understanding of "
            "Happiness and Well-being. New York: Free Press."
        ),
        elements=(
            "Positive Emotion (긍정 정서)",
            "Engagement (몰입)",
            "Relationships (관계)",
            "Meaning (의미)",
            "Accomplishment (성취)",
        ),
        citation_source_urls=(
            "https://en.wikipedia.org/wiki/PERMA_model",
            "https://ppc.sas.upenn.edu/learn-more/perma-theory-well-being-and-perma-workshops",
            "https://positivepsychology.com/perma-model/",
        ),
        mapping_to_cys={
            1: "Positive Emotion + Engagement + Accomplishment ≈ 박사님 원 ① (개인의 기쁨·몰입·성취감). Seligman: 'hedonic feelings of happiness' + 'feeling absorbed, interested, and engaged in life' + 'making progress toward goals'",
            2: "Relationships ≈ 박사님 원 ② (사회적 연결·지지·관계 만족). Seligman: 'feeling socially integrated, cared about and supported by others, and satisfied with one's social connections'",
            3: "Meaning ≈ 박사님 원 ③ (자기 너머의 큰 의미·소명). Seligman: 'believing that one's life is valuable and feeling connected to something greater than oneself'. *박사님 책 '정신적 가치'·Seligman 'Meaning' 직접 대응.*",
        },
    ),
    ExternalSource(
        key="ikigai_western_venn",
        model_name="Ikigai (Westernized 4-circle Venn)",
        authors=(
            "Andrés Zuzunaga (2011, 'Purpose Venn diagram') + Marc Winn (2014, "
            "'ikigai' relabeling). 일본 원어 ikigai 개념은 神谷美恵子(Mieko Kamiya, 1966) "
            "『生きがいについて』가 학계 1차 자료."
        ),
        primary_text=(
            "주의: 박사님 책과 다른 *서양식 ikigai 4영역 Venn*은 학술 1차 자료가 아니라 "
            "Andres Zuzunaga(스페인, 2011)의 'Purpose Venn diagram'을 Marc Winn(2014)이 "
            "ikigai로 재명명한 *블로그 기원의 변용*이다. Wikipedia·Ikigai Tribe·Zen and "
            "Innovation 등 다수 출처가 이 사실을 확인한다."
        ),
        elements=(
            "What you love (사랑하는 것)",
            "What you are good at (잘하는 것)",
            "What the world needs (세상이 필요로 하는 것)",
            "What you can be paid for (보상받을 수 있는 것)",
        ),
        citation_source_urls=(
            "https://en.wikipedia.org/wiki/Ikigai",
            "https://ikigaitribe.com/ikigai/ikigai-misunderstood/",
            "https://zenschool.medium.com/the-real-ikigai-vs-western-ikigai-how-a-japanese-concept-got-lost-in-translation-3287a06bf2da",
        ),
        mapping_to_cys={
            1: "'What you love' + 'What you are good at' ≈ 박사님 원 ① (본인 적성·열정 기쁨)",
            2: "'What the world needs' ≈ 박사님 원 ② (세상에 가치 기여). 'What you can be paid for'는 박사님 책에 없음.",
            3: "직접 매핑 없음 — 서양식 ikigai 4영역은 *영적·도덕 차원*을 별도로 두지 않음. 박사님 원 ③(정신적·도덕적 가치)이 서양식 ikigai에는 부재 → 박사님 모델의 *차별점*.",
        },
    ),
    ExternalSource(
        key="aristotle_eudaimonia",
        model_name="Eudaimonia (인간 번영) — 미덕에 따른 영혼의 합리적 활동",
        authors="Aristotle (BCE 4세기, 『Nicomachean Ethics』)",
        primary_text=(
            "Aristotle. Nicomachean Ethics. Book I-X. Standard reference: Ross, W. D. "
            "(1908/1925) Oxford University Press translation."
        ),
        elements=(
            "Rational activity of soul (영혼의 합리적 활동)",
            "Virtue — intellectual & moral (지·도덕 미덕)",
            "Complete life of flourishing (완전한 번영의 삶)",
        ),
        citation_source_urls=(
            "https://plato.stanford.edu/entries/aristotle-ethics/",
            "https://www.britannica.com/topic/eudaimonia",
            "https://en.wikipedia.org/wiki/Nicomachean_Ethics",
        ),
        mapping_to_cys={
            1: "'Activity' 본인 영혼의 합리적 활동 자체가 본인의 진정한 기쁨 ≈ 박사님 원 ①. Aristotle: 'eudaimonia is an activity ... rather than a state'",
            2: "Aristotle은 인간을 *정치적 동물(zoon politikon)*로 정의 — 폴리스(공동체) 안에서의 우정·정의가 eudaimonia의 일부 ≈ 박사님 원 ②. 단 *가족·세상*이 분리된 영역으로 정식화되지는 않음.",
            3: "Intellectual virtue + Moral virtue ≈ 박사님 원 ③ (정신적·도덕적 가치). Aristotle: 'intellectual virtues belonging to the rational part of the soul' + 'moral virtues ... arise through long habituation'. *서양 윤리학 전통의 ③ 영역의 원형.*",
        },
    ),
)


# --------------------------------------------------------------------------
# 결정론 API
# --------------------------------------------------------------------------


def list_sources() -> list[ExternalSource]:
    """등록된 외부 학계 출처 5종을 반환."""
    return list(EXTERNAL_SOURCES)


def get_source(key: str) -> ExternalSource:
    """슬러그로 외부 출처 단건 조회. 없는 키 → KeyError."""
    for s in EXTERNAL_SOURCES:
        if s.key == key:
            return s
    raise KeyError(f"unknown external source key: {key!r}")


def realms_for(key: str) -> dict[int, str]:
    """특정 외부 모델의 박사님 ①②③ 매핑 사전을 반환."""
    return dict(get_source(key).mapping_to_cys)


def render_corroboration(key: str) -> str:
    """외부 출처 1건의 박사님 모델 대조 블록을 렌더링.

    SKILL.md "외부 모델 비교 요청" 흐름에서 이 출력을 그대로 붙여 넣어
    LLM의 자연어 재진술을 차단한다.
    """
    s = get_source(key)
    out = [
        f"### {s.model_name}",
        f"**저자**: {s.authors}",
        f"**1차 자료**: {s.primary_text}",
        f"**핵심 영역**: {', '.join(s.elements)}",
        "",
        "**박사님 3영역 매핑**:",
    ]
    for realm_num, mapping in s.mapping_to_cys.items():
        out.append(f"- {CYS_REALM_LABELS[realm_num]}")
        out.append(f"  - {mapping}")
    out.append("")
    out.append("**외부 검증 URL**:")
    for url in s.citation_source_urls:
        out.append(f"- {url}")
    return "\n".join(out)


def render_all_corroboration() -> str:
    """전 5개 외부 학계 출처를 한꺼번에 렌더링."""
    header = (
        "## 박사님 3영역 모델 — 학계 주류 문헌 1:1 대조\n\n"
        "박사님 책 『미래준비학교』(2016)는 *대중적 미래학·자기계발* 서적으로, 동료심사 "
        "학술지 출간이 아닙니다. 그러나 박사님이 제시한 3영역(나의 기쁨 · 가족·세상 · "
        "정신적) 구조는 학계 주류의 다층 모델과 광범위한 사상적 친연성을 가집니다. "
        "아래는 5개 학계 주류 모델과의 1:1 대조입니다.\n"
    )
    blocks = [render_corroboration(s.key) for s in EXTERNAL_SOURCES]
    footer = (
        "\n## 박사님 모델의 차별점\n\n"
        "- **3원 교집합 동시 만족**이라는 *균형 잃은 비전 = 위험* 명제는 학계 모델 중 "
        "Frankl logotherapy (의미의 다층성)와 SDT (3 needs 동시 만족 시 well-being 최적화)와 "
        "사상적으로 가장 가깝다.\n"
        "- 서양식 ikigai 4영역은 *영적·도덕 차원*을 별도로 두지 않아 박사님 원 ③에 직접 "
        "대응하는 영역이 없다 — 이것이 박사님 모델의 *차별점*이다.\n"
        "- Frankl의 Attitudinal Values와 박사님 원 ③은 *고난·도덕·소명* 측면에서 거의 "
        "1:1 대응한다. 둘 다 *상위 의미 차원*을 별도 영역으로 분리한 점에서 학계적 "
        "정합성이 높다.\n"
    )
    return header + "\n" + "\n".join(blocks) + footer


def verify_url_format(url: str) -> bool:
    """등록된 외부 출처 URL 형식 검증 — http(s):// 시작 + 도메인 포함."""
    if not url:
        return False
    return (url.startswith("http://") or url.startswith("https://")) and "/" in url[8:]


def all_urls_valid() -> bool:
    """등록된 모든 외부 URL이 올바른 형식인지 일괄 검증."""
    for s in EXTERNAL_SOURCES:
        for url in s.citation_source_urls:
            if not verify_url_format(url):
                return False
    return True
