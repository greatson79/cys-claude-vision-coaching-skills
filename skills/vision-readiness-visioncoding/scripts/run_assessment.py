#!/usr/bin/env python3
"""
vision-readiness-visioncoding 실행 진입점.

SKILL.md의 3·4·5단계(점수 집계, 그래프, 코칭) 결정론 처리를 위해
LLM이 직접 호출하는 단일 CLI. 입력 raw 문자열을 받아 JSON으로 모든
산출물을 반환한다.

사용:
  python scripts/run_assessment.py "Q01: 7, Q02: 8, ..."
  echo "7, 8, 6, ..." | python scripts/run_assessment.py
"""

import os
import sys

# lib 경로 추가
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIB = os.path.join(ROOT, "lib")
sys.path.insert(0, LIB)

from readiness_engine import main  # noqa: E402

if __name__ == "__main__":
    main()
