#!/bin/bash
# 10 신규 검증 프롬프트 — 이전 검증과 전혀 다른 것
cd "$(dirname "$0")"

echo "============================================================"
echo "TEST 1: 사용자 지정 horizon + A유형"
echo "프롬프트: 노인 돌봄 분야 미래지도, 시간축은 2050년까지로"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "노인 돌봄 분야 미래지도, 시간축은 2050년까지로"
python3 futures_timeline_engine.py classify_abcd "노인 돌봄 분야 미래지도, 시간축은 2050년까지로"
python3 futures_timeline_engine.py compute_intervals 2026 2050 3

echo "============================================================"
echo "TEST 2: partial_consideration"
echo "프롬프트: 보잘것없는 정보만 모아줘 — 우주 항공 분야"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "보잘것없는 정보만 모아줘 — 우주 항공 분야"

echo "============================================================"
echo "TEST 3: D유형 (박사님 본인)"
echo "프롬프트: 박사님 본인의 미출간 단행본 작업 사이클 미래지도"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_abcd "박사님 본인의 미출간 단행본 작업 사이클 미래지도"
python3 futures_timeline_engine.py classify_entry "박사님 본인의 미출간 단행본 작업 사이클 미래지도"

echo "============================================================"
echo "TEST 4: methodology_only (Forecasting 단독)"
echo "프롬프트: Forecasting만으로 K-콘텐츠 산업 단기 트렌드 예측"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "Forecasting만으로 K-콘텐츠 산업 단기 트렌드 예측"

echo "============================================================"
echo "TEST 5: S 양쪽 명시"
echo "프롬프트: S가 두 개인 거 알고 있는데 둘 다 분석해줘 — 한국 청년 1인가구"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py detect_s "S가 두 개인 거 알고 있는데 둘 다 분석해줘 — 한국 청년 1인가구"

echo "============================================================"
echo "TEST 6: concept_only"
echo "프롬프트: 미래지도와 미래 나침반의 차이가 뭐고 정의가 뭐야"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "미래지도와 미래 나침반의 차이가 뭐고 정의가 뭐야"

echo "============================================================"
echo "TEST 7: quote_full_text + 인용 검증"
echo "프롬프트: 콜린 파월 인용문 원문 전체를 보여줘"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "콜린 파월 인용문 원문 전체를 보여줘"
python3 futures_timeline_engine.py verify_quote "100% 정확한 정보는 쓸모없다. 100% 확실하게 폭발이 일어날 것이라 말할 수 있을 때는 이미 늦기 때문이다."
python3 futures_timeline_engine.py crosscheck_quote colin_powell_certainty

echo "============================================================"
echo "TEST 8: subjective_ranking"
echo "프롬프트: 박사님 책에 없지만 가장 결정적인 변수 5개만 골라줘 — 인구절벽 분야"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "박사님 책에 없지만 가장 결정적인 변수 5개만 골라줘 — 인구절벽 분야"

echo "============================================================"
echo "TEST 9: B유형 + 벤치마크 교차"
echo "프롬프트: 벤치마크처럼 글로벌 반도체 패권 미래지도 만들어줘"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_abcd "벤치마크처럼 글로벌 반도체 패권 미래지도 만들어줘"
python3 futures_timeline_engine.py recommend_benchmark "글로벌 반도체 패권 무역"

echo "============================================================"
echo "TEST 10: tool_fitness_no_vision"
echo "프롬프트: 비전이 없는데 이 도구가 필요한가요"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py classify_entry "비전이 없는데 이 도구가 필요한가요"

echo "============================================================"
echo "EXTRA: 인용문 출력 시도 — 박사님 책 미수록 가짜 인용"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py verify_quote "박사님이 미래학을 정의하기를 '예측이 아니라 준비'라고 했다."
echo "============================================================"
echo "EXTRA: STEEPS 6영역 카탈로그"
echo "------------------------------------------------------------"
python3 futures_timeline_engine.py list_steeps
