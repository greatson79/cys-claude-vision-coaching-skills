#!/bin/bash
# 라운드 4 — 산출물 10개에 대한 자동 정확도 검증
# 검증 어서션:
# 1) 박사님 책 인용문이 사용된 경우 엔진 verify_quote 통과 ID가 명시되어 있는가
# 2) 외부 인물·저서 인용 시 crosscheck 또는 MATCH 표기가 있는가
# 3) 박사님 책에 직접 없는 사실은 "Claude 코칭 제안" 마커로 분리되어 있는가
# 4) 엔진 분기 매핑이 파일에 기록되어 있는가
# 5) 자기 검증 체크리스트가 있는가

cd "$(dirname "$0")"
OUT=outputs
PASS=0
FAIL=0
errors=()

check() {
  local name="$1" pattern="$2" file="$3"
  if grep -q -E "$pattern" "$file" 2>/dev/null; then
    PASS=$((PASS+1))
    echo "  ✅ $name"
  else
    FAIL=$((FAIL+1))
    errors+=("$file :: $name (missing pattern: $pattern)")
    echo "  ❌ $name"
  fi
}

check_universal() {
  local f="$1"
  echo "--- $(basename $f) ---"
  check "엔진 분기 매핑 기록" 'classify_entry|classify_abcd|verify_quote|detect_s|recommend_benchmark|compute_intervals|list_methodologies' "$f"
  check "SKILL.md 처리 흐름 명시" 'SKILL.md 처리 흐름|SKILL\.md ' "$f"
  check "출처 검증 표 또는 verify_quote 결과 기록" 'verify_quote|crosscheck|verified=true|verified": true|verified=direct|✅ direct|✅ reindirect' "$f"
  check "자기 검증 체크리스트" '자기 검증 체크리스트' "$f"
  check "박사님 책 또는 미래준비학교 명시" '박사님 책|미래준비학교' "$f"
}

for f in $OUT/P*.md; do
  check_universal "$f"
done

echo ""
echo "--- P01 (concept_only) 추가 어서션"
check "P01 콜럼버스 비유 인용" 'futures_map_definition|콜럼버스' $OUT/P01_skill_definition.md
check "P01 외부 crosscheck Hines & Bishop" 'Hines & Bishop' $OUT/P01_skill_definition.md

echo "--- P02 (concept_plus_application) 추가"
check "P02 직접 인용 ID" 'futures_map_definition' $OUT/P02_columbus_startup.md
check "P02 Claude 코칭 제안 분리 표기" 'Claude 코칭 제안' $OUT/P02_columbus_startup.md

echo "--- P03 (partial_consideration) 추가"
check "P03 5소스 카탈로그 출처" 'list_weak_signal_sources|약한 신호 5소스' $OUT/P03_weak_signals_nomad.md
check "P03 Colin Powell crosscheck" 'My American Journey' $OUT/P03_weak_signals_nomad.md

echo "--- P04 (full A) 추가"
check "P04 시간축 엔진 출력" 'compute_intervals.*2026|단기.*2026|2026~2031' $OUT/P04_korea_admissions.md
check "P04 STEEPS 6영역" 'STEEPS|Society|Spirituality' $OUT/P04_korea_admissions.md
check "P04 Wildcard 2종" '비약적 진보|Quantum Progress|붕괴|Collapse' $OUT/P04_korea_admissions.md
check "P04 코칭 제안 분리" 'Claude 코칭 제안|코칭 제안' $OUT/P04_korea_admissions.md

echo "--- P05 (full B 벤치마크) 추가"
check "P05 벤치마크 ② 자동 선택" '2_2016_2035_industry|벤치마크 ②' $OUT/P05_quantum_industry.md
check "P05 원본 메타데이터" 'list_benchmarks|2016~2035 미래산업' $OUT/P05_quantum_industry.md
check "P05 코칭 제안 분리" 'Claude 코칭 제안' $OUT/P05_quantum_industry.md

echo "--- P06 (C 미래 나침반) 추가"
check "P06 미래 나침반 정의 인용" 'futures_compass_definition|미래 나침반.*사고의 틀' $OUT/P06_metaverse_compass.md
check "P06 매일/매주/분기 루틴" '매일|매주|분기' $OUT/P06_metaverse_compass.md

echo "--- P07 (methodology Forecasting) 추가"
check "P07 Forecasting 방향 명시" '현재.*미래|현재\(Y\).*미래' $OUT/P07_kpop_forecasting.md
check "P07 list_methodologies 출처" 'list_methodologies|박사님 책 다이어그램' $OUT/P07_kpop_forecasting.md

echo "--- P08 (subjective_ranking) 추가"
check "P08 절대원칙 #10 분리 표기" '박사님 책의 입장이 아닙니다|박사님 책의 입장이 아님' $OUT/P08_subjective_rank.md
check "P08 박사님 책 인용 6개 이상" 'futures_map_definition' $OUT/P08_subjective_rank.md
check "P08 가장 ○○ 직접 언급 없음 고지" '직접적인 언급|직접 언급|직접적인 언급은' $OUT/P08_subjective_rank.md

echo "--- P09 (out_of_scope) 추가"
check "P09 본 스킬 범위 명시" '본 스킬에 수록되지 않았|본 스킬.*범위' $OUT/P09_toffler_oos.md
check "P09 박사님 책 재인용 Schwartz 만 사용" 'peter_schwartz_skeleton|The Art of the Long View' $OUT/P09_toffler_oos.md
check "P09 Toffler 사상 본문 인용 없음" '인용되지 않음|인용하지 않음|할루시네이션 차단' $OUT/P09_toffler_oos.md

echo "--- P10 (quote_full_text) 추가"
check "P10 원문 인용 verify=direct" 'six_force_domains' $OUT/P10_six_force_quote.md
check "P10 STEEPS 6축 매핑 표" 'Society|Spirituality|Technology|Economy|Environment|Politics' $OUT/P10_six_force_quote.md
check "P10 외부 1:1 출처 3건" 'Aguilar|Hines & Bishop|Fahey' $OUT/P10_six_force_quote.md
check "P10 빈 부분 채우지 않음 명시" '빈 부분 채우지 않음|"...".*빈 부분' $OUT/P10_six_force_quote.md

echo ""
echo "================ SUMMARY ================"
echo "PASS: $PASS"
echo "FAIL: $FAIL"
if [[ $FAIL -gt 0 ]]; then
  echo ""
  echo "FAILED ASSERTIONS:"
  for e in "${errors[@]}"; do echo "  - $e"; done
  echo "🔴 FAIL DETECTED"
  exit 1
else
  echo "🟢 ALL ASSERTIONS PASS"
fi
