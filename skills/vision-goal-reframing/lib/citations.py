"""인용 출처 결정론 레지스트리.

data/citations.json에 사전 등록된 출처만 허용한다. LLM이 자연어로
"Doran 1981, Management Review" 같은 키 정보를 추론·변형하는 것을 차단한다.

사용 예:
    from lib.citations import cite, get_record
    print(cite("SMART_DORAN_1981"))
"""

from __future__ import annotations

import json
import os
from typing import Dict, List


_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "citations.json",
)


def _load() -> Dict:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_record(key: str) -> dict:
    """등록된 인용 레코드 반환. 없으면 KeyError."""
    data = _load()
    if key not in data or key == "_meta":
        raise KeyError(f"인용 키 '{key}'가 citations.json에 등록되지 않음. "
                       f"신규 등록 없이 사용 금지 (할루시네이션 방지 규약).")
    return data[key]


def cite(key: str) -> str:
    """워크북 본문에 삽입할 인용 한 줄."""
    rec = get_record(key)
    return rec["citation"]


def all_keys() -> List[str]:
    return [k for k in _load().keys() if k != "_meta"]


def references_block(keys: List[str]) -> str:
    """워크북 말미에 붙는 참고문헌 블록."""
    out = ["## 참고문헌 (검증된 출처)"]
    for k in keys:
        rec = get_record(k)
        line = f"- **[{k}]** {rec['citation']}"
        urls = rec.get("source_urls", [])
        if urls:
            line += f"\n  출처 URL: {' · '.join(urls)}"
        out.append(line)
    return "\n".join(out)


# 본 스킬이 출력 워크북에서 *반드시* 인용해야 하는 코어 세트
CORE_REFERENCES = [
    "SMART_DORAN_1981",
    "BACKCASTING_ROBINSON_1982",
    "BACKCASTING_ROBINSON_1990",
    "OKR_GROVE_1983",
    "OKR_DOERR_2018",
    "OKR_GOOGLE_GRADING",
]


if __name__ == "__main__":
    for k in all_keys():
        print(f"[{k}] {cite(k)}")
    print()
    print(references_block(CORE_REFERENCES))
