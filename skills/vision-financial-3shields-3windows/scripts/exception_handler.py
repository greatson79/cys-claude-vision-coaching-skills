#!/usr/bin/env python3
"""스킬 예외 처리 결정론 라우터.

SKILL.md 호출 전 사용자 입력을 분류하여 처리 분기를 결정한다.
LLM이 예외 케이스마다 "이건 어떻게 처리하지" 재추론하지 못하도록 차단.

입력: 사용자 요청 텍스트 (stdin 또는 --text)
출력: 처리 분기 결정 JSON
"""
import json
import sys
import argparse
import re

# 예외 케이스 정의 — 결정론적 키워드 매칭
EXCEPTION_RULES = [
    {
        "id": "E1_INVALID_DOMAIN",
        "description": "재정 외 도메인 (설교·신학·미래학·역사 등)",
        "patterns": [
            r"(설교|성경|예수|십자가|복음서|구약|신약|기독교\s*역사)",
            r"(시나리오 플래닝|델파이|MEPeace|미래학 방법론|로드맵|모르폴로지)",
            r"(주해|원어|헬라어|히브리어|어거스틴|칼빈|루터|MLJ|로이드|바빙크)",
        ],
        "action": "REDIRECT",
        "message": "본 스킬은 박사님 *3방패+3창 재정 모델* 전용입니다. 입력하신 주제는 다른 스킬 영역입니다. 적합한 스킬을 추천드릴까요?",
    },
    {
        "id": "E2_RAMSEY_ORMAN_COMPARISON",
        "description": "Dave Ramsey·Suze Orman 비교 요청",
        "patterns": [
            r"(Ramsey|Orman|램지|오먼|오만|데이브 램지|수즈 오만)",
        ],
        "action": "REDIRECT_PARTIAL",
        "message": "Dave Ramsey·Suze Orman 세부 내용은 vision-financial-coach 스킬에서 다룹니다. 박사님 3방패+3창 모델의 고유한 특징은 ①비전 우선·재정은 인프라 ②100세 시대·장기 저성장 한국 맥락 ③꿈 효과(타인을 부자로) 입니다.",
    },
    {
        "id": "E3_KOREAN_TAX_LAW_DETAIL",
        "description": "한국 세법·DB/DC형 연금 등 SKILL.md 범위 외 세부 제도",
        "patterns": [
            r"(DB형|DC형|연금저축\s*세액공제|IRP\s*한도|종합소득세\s*세율|양도세\s*세율)",
            r"(상속세|증여세\s*공제|부동산\s*취득세\s*세율)",
        ],
        "action": "DISCLOSE_OUT_OF_SCOPE",
        "message": "이 항목은 SKILL.md 범위 외 한국 금융·세법 영역입니다. 응답 시 '(SKILL.md 외 일반 금융 지식 적용)' 명시하고, 정확한 세율·한도는 국세청·금융감독원 공식 자료 또는 세무사 확인을 권장합니다.",
    },
    {
        "id": "E4_SPECIFIC_TICKER_OR_STOCK_PICK",
        "description": "구체 종목·티커 추천 요청 (박사님 모델 범위 외)",
        "patterns": [
            r"(삼성전자|애플|테슬라|엔비디아|코스피|S&P|나스닥|비트코인|이더리움|TSLA|AAPL|NVDA)",
            r"(어떤|무슨|어느)\s*(주식|종목|기업|회사|코인|ETF)",
            r"(어디|어느 곳)에?\s*(투자|투자해)",
            r"(주식|종목|ETF)\s*(추천|사야|살까|매수|매도|뭐|뭘)",
        ],
        "action": "DISCLOSE_OUT_OF_SCOPE",
        "message": "본 스킬은 박사님 *원칙 모델*만 다루며 구체 종목 추천은 하지 않습니다. 박사님 원칙은 ①장기 저성장 전제 ②7~10% 복리 목표 ③자산 배분(주식·채권·부동산·현금) ④본인 철학이 들어간 시스템 구축입니다.",
    },
    {
        "id": "E5_VISION_NOT_CLARIFIED",
        "description": "비전 선언문 명료화 미완료 신호",
        "patterns": [
            r"비전(이|을)?\s*(없|못 정|모르|아직|미정|안 정)",
            r"(뭘|무엇을)\s*하고 싶은지\s*(모르|몰라)",
            r"꿈(이|을)?\s*(없|모르|몰라)",
            r"인생\s*(방향|목표)(이|을)?\s*(없|모르|몰라)",
        ],
        "action": "ADVISE_PREREQUISITE",
        "message": "박사님 절대 원칙 2 '비전 우선·재정은 인프라'에 따라 vision-statement-writer로 비전 선언문을 먼저 정리하시는 것을 권장합니다. 재정 분석은 진행하되 비전 명료 후 전략을 최종 조율합니다.",
    },
    {
        "id": "E6_INSUFFICIENT_DATA",
        "description": "재정 정보 부족 (수입·자산·부채 미입력)",
        "patterns": [
            r"^(분석해|시뮬레이션|3방패\s*점검|재정\s*분석)\s*$",
        ],
        "action": "REQUEST_INPUT",
        "message": "재정 진단을 위해 다음 정보가 필요합니다: ①월 수입 (주수입+부수입) ②월 지출 (고정비+변동비) ③총자산 (현금·투자·부동산) ④총부채 (이자율 포함). 개략 수치라도 알려주시면 박사님 책 기준으로 진단을 시작합니다.",
    },
]


def classify(text: str) -> dict:
    matches = []
    for rule in EXCEPTION_RULES:
        for pat in rule["patterns"]:
            if re.search(pat, text, flags=re.IGNORECASE):
                matches.append({
                    "id": rule["id"],
                    "description": rule["description"],
                    "action": rule["action"],
                    "message": rule["message"],
                    "matched_pattern": pat,
                })
                break
    if not matches:
        return {
            "action": "PROCEED",
            "message": "예외 패턴 미감지 → 표준 5단계 처리 흐름 진행",
            "matches": [],
        }
    return {
        "action": "EXCEPTION",
        "message": "예외 케이스 감지됨 — 아래 분기에 따라 처리하세요",
        "matches": matches,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="사용자 요청을 예외 케이스로 분류")
    parser.add_argument("--text", help="사용자 요청 텍스트 (기본: stdin)")
    args = parser.parse_args(argv[1:])

    if args.text is not None:
        text = args.text
    else:
        text = sys.stdin.read()

    if not text.strip():
        print("ERROR: 입력 텍스트가 비어 있습니다.", file=sys.stderr)
        return 2

    result = classify(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
