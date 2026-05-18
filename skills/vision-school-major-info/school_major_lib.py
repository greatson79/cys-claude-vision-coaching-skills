"""
vision-school-major-info — 결정론적 헬퍼 라이브러리.

박사님 미래비전코칭 데이터 백본. 한국 공공데이터포털 7개 API + 미국 ONET 통합.
사용자 본인 API 키 — `~/.config/vision-school-major-info/api_keys.json` (chmod 600).

호출 예 (CLI):
    python3 school_major_lib.py check_api_keys
    python3 school_major_lib.py setup_api_key --name data_go_kr --value "<키>"
    python3 school_major_lib.py setup_api_key --name onet --value "<키>"
    python3 school_major_lib.py validate_api_keys
    python3 school_major_lib.py kr_search_university --name 서울대
    python3 school_major_lib.py kr_search_major --keyword 컴퓨터
    python3 school_major_lib.py onet_search_occupation --keyword software
    python3 school_major_lib.py holland_to_onet --code R
    python3 school_major_lib.py attribution_text
    python3 school_major_lib.py onet_attribution_text
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 0. 키 저장·진입 가드
# ---------------------------------------------------------------------------

CONFIG_DIR = os.path.expanduser("~/.config/vision-school-major-info")
KEYS_PATH = os.path.join(CONFIG_DIR, "api_keys.json")

VALID_KEY_NAMES = ("data_go_kr", "onet")

DATA_GO_KR_ENDPOINTS = {
    # 데이터셋 ID: (도메인 + 경로)
    "15057878": "https://www.career.go.kr/cnet/openapi/getOpenApi",  # 커리어넷 학과정보
    "15058917": "https://www.career.go.kr/cnet/openapi/getOpenApi",  # 커리어넷 학교정보
    "15056641": "https://www.career.go.kr/cnet/openapi/getOpenApi",  # 커리어넷 직업정보
    "15057135": "https://www.career.go.kr/cnet/openapi/getOpenApi",  # 커리어넷 진로자료
    "15116892": "https://apis.data.go.kr/B552103/UnivMajorInfoService/getUnivMajorInfo",
    "15037507": "https://apis.data.go.kr/B552103/HEducationInfoService/getUnivInfo",
    "15116816": "https://apis.data.go.kr/B552103/UnivInfoService/getUnivInfo",
}

ONET_BASE_URL = "https://services.onetcenter.org/ws/"


SETUP_GUIDE = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
vision-school-major-info — API 키 등록 안내
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

본 스킬은 *본인의* API 키를 사용합니다. 모두 무료.

【필수】 공공데이터포털 (data.go.kr) — 한국 7개 API 통합
  1) https://www.data.go.kr 회원가입 (무료)
  2) 다음 7개 API "활용신청" (각각 자동승인·즉시 사용 가능):
     · 15057878 교육부_커리어넷 대학학과정보
     · 15058917 교육부_커리어넷 학교정보
     · 15056641 교육부_커리어넷 직업정보
     · 15057135 교육부_커리어넷 진로자료
     · 15116892 KCUE 대학별 학과정보
     · 15037507 KCUE 대학알리미 대학 기본정보
     · 15116816 KCUE 대학 및 전문대학정보
  3) 마이페이지 → 개발계정 → 일반 인증키(Encoding) 복사
  4) python3 school_major_lib.py setup_api_key --name data_go_kr --value "복사한_키"

【선택】 ONET Web Services — 미국 직업 (유학·해외 진로용)
  1) https://services.onetcenter.org/developer/signup 회원가입
  2) 조직·프로젝트 정보 입력 → 승인 이메일 1~2일 대기
  3) 발급된 API v2.0 키 복사
  4) python3 school_major_lib.py setup_api_key --name onet --value "복사한_키"

★ 한국만 쓰실 거면 필수 1개만 등록.
★ 유학·해외 진로 코칭하실 거면 ONET까지 등록 권장.

ONET 데이터 라이선스(CC-BY) attribution은 본 스킬이 자동 처리.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


def _load_keys() -> dict:
    if not os.path.exists(KEYS_PATH):
        return {}
    try:
        with open(KEYS_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_keys(keys: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp = KEYS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)
    os.replace(tmp, KEYS_PATH)
    # chmod 600 — owner read/write only
    try:
        os.chmod(KEYS_PATH, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def check_api_keys() -> dict:
    """등록된 키 상태 검증. 미등록 시 setup_guide 동봉."""
    keys = _load_keys()
    has_kr = bool(keys.get("data_go_kr"))
    has_onet = bool(keys.get("onet"))
    missing: list[str] = []
    if not has_kr:
        missing.append("data_go_kr")
    # onet은 선택이므로 missing이지만 가드 통과는 가능
    optional_missing: list[str] = []
    if not has_onet:
        optional_missing.append("onet")

    ok_required = has_kr  # data_go_kr만 필수
    return {
        "ok": ok_required,
        "data_go_kr": has_kr,
        "onet": has_onet,
        "mode": (
            "full" if has_kr and has_onet
            else "korean_only" if has_kr
            else "onet_only" if has_onet
            else "none"
        ),
        "missing_required": missing,
        "missing_optional": optional_missing,
        "config_path": KEYS_PATH,
        "setup_guide": SETUP_GUIDE if (missing or optional_missing) else "",
    }


def setup_api_key(name: Any, value: Any) -> dict:
    """API 키를 ~/.config/vision-school-major-info/api_keys.json에 저장 (chmod 600)."""
    if not isinstance(name, str) or name not in VALID_KEY_NAMES:
        return {"ok": False, "reason": f"name must be one of {VALID_KEY_NAMES}, got {name!r}"}
    if not isinstance(value, str) or not value.strip():
        return {"ok": False, "reason": "value required (non-empty string)"}
    keys = _load_keys()
    keys[name] = value.strip()
    _save_keys(keys)
    # 권한 확인
    mode = "unknown"
    try:
        st = os.stat(KEYS_PATH)
        mode = oct(st.st_mode & 0o777)
    except OSError:
        pass
    return {
        "ok": True,
        "name": name,
        "saved_to": KEYS_PATH,
        "file_mode": mode,
        "note": "이제 본 스킬을 다시 호출하시면 진입 가드를 통과합니다.",
    }


def _http_get(url: str, params: dict | None = None, timeout: float = 20.0) -> tuple[int, str]:
    """결정론적 HTTP GET. (status, body) 반환. urllib만 사용."""
    if params:
        url = url + ("&" if "?" in url else "?") + urlencode(params)
    req = Request(url, headers={"User-Agent": "vision-school-major-info/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except Exception as e:
        return -1, f"{type(e).__name__}: {e}"


def validate_api_keys() -> dict:
    """등록된 키를 실제 API 1회 ping으로 검증."""
    keys = _load_keys()
    result: dict = {"data_go_kr": None, "onet": None}

    # data_go_kr ping — 커리어넷 학과정보 1건 호출 시도
    if keys.get("data_go_kr"):
        # 커리어넷 학과정보 minimal call
        status, body = _http_get(
            "https://www.career.go.kr/cnet/openapi/getOpenApi",
            {
                "apiKey": keys["data_go_kr"],
                "svcType": "api",
                "svcCode": "MAJOR",
                "contentType": "json",
                "gubun": "univ_list",
                "thisPage": 1,
                "perPage": 1,
            },
        )
        # 키 유효: HTTP 200 + 응답 본문에 'dataSearch' 또는 'totalCount'
        ok = status == 200 and ("dataSearch" in body or "totalCount" in body)
        result["data_go_kr"] = {
            "ok": ok,
            "status": status,
            "note": "200 + dataSearch/totalCount → valid" if ok else "키 무효 또는 활용신청 미완료. 안내 다시 확인.",
        }

    # onet ping — Basic Auth로 occupation list 1건
    if keys.get("onet"):
        import base64
        # ONET v2는 username:password 형식. 사용자가 입력한 키가 이미 그 형식이라고 가정.
        token = base64.b64encode(keys["onet"].encode("utf-8")).decode("ascii")
        url = ONET_BASE_URL + "online/occupations/15-1252.00/details"
        req = Request(
            url,
            headers={
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
                "User-Agent": "vision-school-major-info/1.0",
            },
        )
        try:
            with urlopen(req, timeout=20) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                ok = resp.status == 200
                result["onet"] = {
                    "ok": ok,
                    "status": resp.status,
                    "note": "200 → valid" if ok else f"status {resp.status}",
                }
        except Exception as e:
            result["onet"] = {
                "ok": False,
                "status": -1,
                "note": f"키 무효 또는 형식 오류: {type(e).__name__}: {e}",
            }

    return {
        "ok": (result["data_go_kr"] is None or result["data_go_kr"].get("ok"))
              and (result["onet"] is None or result["onet"].get("ok")),
        **result,
    }


# ---------------------------------------------------------------------------
# 1. 한국 데이터 호출 — 커리어넷·KCUE
# ---------------------------------------------------------------------------

def _require_kr_key() -> str | None:
    keys = _load_keys()
    return keys.get("data_go_kr") if isinstance(keys.get("data_go_kr"), str) else None


def kr_search_university(name: Any = None, region: Any = None, per_page: int = 10) -> dict:
    """커리어넷 학교정보 검색."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered. Run check_api_keys."}
    params = {
        "apiKey": key,
        "svcType": "api",
        "svcCode": "SCHOOL",
        "contentType": "json",
        "gubun": "univ_list",
        "thisPage": 1,
        "perPage": max(1, min(int(per_page), 100)),
    }
    if name and isinstance(name, str):
        params["searchSchulNm"] = name.strip()
    if region and isinstance(region, str):
        params["region"] = region.strip()
    status, body = _http_get("https://www.career.go.kr/cnet/openapi/getOpenApi", params)
    return {
        "ok": status == 200,
        "status": status,
        "raw": body[:5000] if body else "",
        "attribution": attribution_text(),
    }


def kr_search_major(keyword: Any = None, per_page: int = 10) -> dict:
    """커리어넷 학과정보 검색."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered"}
    params = {
        "apiKey": key,
        "svcType": "api",
        "svcCode": "MAJOR",
        "contentType": "json",
        "gubun": "univ_list",
        "thisPage": 1,
        "perPage": max(1, min(int(per_page), 100)),
    }
    if keyword and isinstance(keyword, str):
        params["searchMajorName"] = keyword.strip()
    status, body = _http_get("https://www.career.go.kr/cnet/openapi/getOpenApi", params)
    return {
        "ok": status == 200,
        "status": status,
        "raw": body[:5000] if body else "",
        "attribution": attribution_text(),
    }


def kr_career_search(keyword: Any = None, per_page: int = 10) -> dict:
    """커리어넷 직업정보 검색."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered"}
    params = {
        "apiKey": key,
        "svcType": "api",
        "svcCode": "JOB",
        "contentType": "json",
        "gubun": "job_dic_list",
        "thisPage": 1,
        "perPage": max(1, min(int(per_page), 100)),
    }
    if keyword and isinstance(keyword, str):
        params["searchJobNm"] = keyword.strip()
    status, body = _http_get("https://www.career.go.kr/cnet/openapi/getOpenApi", params)
    return {
        "ok": status == 200,
        "status": status,
        "raw": body[:5000] if body else "",
        "attribution": attribution_text(),
    }


# ---------------------------------------------------------------------------
# 2. ONET — 미국 직업 정보
# ---------------------------------------------------------------------------

def _require_onet_key() -> str | None:
    keys = _load_keys()
    v = keys.get("onet")
    return v if isinstance(v, str) and v.strip() else None


def _onet_get(path: str, timeout: float = 20.0) -> tuple[int, Any]:
    key = _require_onet_key()
    if not key:
        return -1, {"reason": "onet key not registered"}
    import base64
    token = base64.b64encode(key.encode("utf-8")).decode("ascii")
    url = ONET_BASE_URL + path.lstrip("/")
    req = Request(
        url,
        headers={
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": "vision-school-major-info/1.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {"raw": body[:2000]}
            return resp.status, data
    except Exception as e:
        return -1, {"reason": f"{type(e).__name__}: {e}"}


def onet_search_occupation(keyword: Any) -> dict:
    if not isinstance(keyword, str) or not keyword.strip():
        return {"ok": False, "reason": "keyword required"}
    status, data = _onet_get(f"online/search?keyword={keyword.strip()}")
    return {
        "ok": status == 200,
        "status": status,
        "data": data,
        "attribution": onet_attribution_text(),
    }


def onet_occupation_detail(soc_code: Any) -> dict:
    if not isinstance(soc_code, str) or not re.match(r"^\d{2}-\d{4}\.\d{2}$", soc_code.strip()):
        return {"ok": False, "reason": "soc_code must be in format NN-NNNN.NN (e.g., 15-1252.00)"}
    status, data = _onet_get(f"online/occupations/{soc_code.strip()}/details")
    return {
        "ok": status == 200,
        "status": status,
        "data": data,
        "attribution": onet_attribution_text(),
    }


# Holland → ONET 매핑 (학계 표준)
HOLLAND_ONET_KEYWORDS = {
    "R": ["mechanic", "engineer", "technician", "agricultural", "construction"],
    "I": ["scientist", "researcher", "analyst", "biologist", "physicist", "data"],
    "A": ["artist", "designer", "musician", "writer", "actor", "creative"],
    "S": ["teacher", "counselor", "social worker", "nurse", "therapist"],
    "E": ["manager", "sales", "executive", "entrepreneur", "lawyer", "marketing"],
    "C": ["accountant", "auditor", "secretary", "clerk", "administrative", "bookkeeper"],
}


def holland_to_onet(code: Any) -> dict:
    """Holland 6 영역 코드 → ONET 직업 검색 결과 매핑."""
    if not isinstance(code, str) or code.strip().upper() not in HOLLAND_ONET_KEYWORDS:
        return {"ok": False, "reason": f"code must be one of R/I/A/S/E/C, got {code!r}"}
    c = code.strip().upper()
    keywords = HOLLAND_ONET_KEYWORDS[c]
    return {
        "ok": True,
        "holland_code": c,
        "search_keywords": keywords,
        "note": "각 키워드를 onet_search_occupation에 넣어 직업 후보를 받을 수 있음.",
        "attribution": onet_attribution_text(),
    }


# ---------------------------------------------------------------------------
# 3. 한↔영 학과명 매핑 사전 (시드)
# ---------------------------------------------------------------------------

KO_EN_MAJOR_DICT = {
    "컴퓨터공학": "Computer Science",
    "컴퓨터과학": "Computer Science",
    "소프트웨어공학": "Software Engineering",
    "전자공학": "Electrical Engineering",
    "기계공학": "Mechanical Engineering",
    "화학공학": "Chemical Engineering",
    "산업공학": "Industrial Engineering",
    "건축학": "Architecture",
    "건축공학": "Architectural Engineering",
    "토목공학": "Civil Engineering",
    "수학": "Mathematics",
    "통계학": "Statistics",
    "물리학": "Physics",
    "화학": "Chemistry",
    "생물학": "Biology",
    "심리학": "Psychology",
    "사회학": "Sociology",
    "경영학": "Business Administration",
    "경제학": "Economics",
    "회계학": "Accounting",
    "법학": "Law",
    "정치외교학": "Political Science",
    "행정학": "Public Administration",
    "국어국문학": "Korean Language & Literature",
    "영어영문학": "English Language & Literature",
    "역사학": "History",
    "철학": "Philosophy",
    "신학": "Theology",
    "기독교학": "Christian Studies",
    "사회복지학": "Social Welfare",
    "교육학": "Education",
    "의학": "Medicine",
    "간호학": "Nursing",
    "치의학": "Dentistry",
    "약학": "Pharmacy",
    "수의학": "Veterinary Medicine",
    "디자인": "Design",
    "시각디자인": "Visual Design",
    "산업디자인": "Industrial Design",
    "음악": "Music",
    "미술": "Fine Arts",
    "체육학": "Physical Education",
    "식품영양학": "Food and Nutrition",
    "농학": "Agriculture",
    "임학": "Forestry",
    "해양학": "Oceanography",
    "지리학": "Geography",
    "환경공학": "Environmental Engineering",
    "정보통신공학": "Information & Communication Engineering",
    "데이터사이언스": "Data Science",
    "인공지능": "Artificial Intelligence",
    "미디어커뮤니케이션": "Media & Communication",
    "신문방송학": "Journalism & Broadcasting",
    "광고홍보학": "Advertising & Public Relations",
}


def ko_en_major_dict(ko: Any = None) -> dict:
    """한국 학과명 → 영문 학과명. ko 미지정이면 전체 dict 반환."""
    if ko is None or (isinstance(ko, str) and not ko.strip()):
        return {"ok": True, "all": KO_EN_MAJOR_DICT, "count": len(KO_EN_MAJOR_DICT)}
    if not isinstance(ko, str):
        return {"ok": False, "reason": "ko must be string"}
    k = ko.strip()
    if k in KO_EN_MAJOR_DICT:
        return {"ok": True, "ko": k, "en": KO_EN_MAJOR_DICT[k]}
    # 부분 매칭
    matches = {key: val for key, val in KO_EN_MAJOR_DICT.items() if k in key or key in k}
    if matches:
        return {"ok": True, "ko": k, "partial_matches": matches}
    return {"ok": False, "ko": k, "reason": "no match in seed dictionary"}


def major_to_onet(ko_major: Any) -> dict:
    """한국 학과명 → 영문 변환 → ONET 검색 통합."""
    if not isinstance(ko_major, str) or not ko_major.strip():
        return {"ok": False, "reason": "ko_major required"}
    mapping = ko_en_major_dict(ko_major)
    if not mapping.get("ok") and not mapping.get("partial_matches"):
        return {
            "ok": False,
            "reason": f"한국 학과명 '{ko_major}' → 영문 매핑 사전에 없음. ko_en_major_dict 시드에 추가 필요.",
        }
    en = mapping.get("en") or list((mapping.get("partial_matches") or {}).values())[0]
    # ONET 검색 호출 (키 있을 때만)
    search_result = onet_search_occupation(en) if _require_onet_key() else {
        "ok": False, "reason": "onet key not registered — 한↔영 매핑만 반환",
    }
    return {
        "ok": True,
        "ko_major": ko_major,
        "en_major": en,
        "onet_search": search_result,
        "attribution": onet_attribution_text(),
    }


# ---------------------------------------------------------------------------
# 4. Attribution 자동 생성 (할루시네이션 차단)
# ---------------------------------------------------------------------------

def attribution_text() -> dict:
    """한국 데이터 출처 표기."""
    return {
        "rendered": "출처: 공공데이터포털 (data.go.kr) — 교육부 커리어넷 + 한국대학교육협의회(KCUE) 대학알리미.",
        "source": "data.go.kr",
        "datasets": [
            "15057878 교육부_커리어넷 대학학과정보",
            "15058917 교육부_커리어넷 학교정보",
            "15056641 교육부_커리어넷 직업정보",
            "15057135 교육부_커리어넷 진로자료",
            "15116892 KCUE 대학별 학과정보",
            "15037507 KCUE 대학알리미 대학 기본정보",
            "15116816 KCUE 대학 및 전문대학정보",
        ],
    }


def onet_attribution_text() -> dict:
    """ONET CC-BY attribution 자동 생성 (라이선스 법적 의무)."""
    return {
        "rendered": (
            "This output incorporates data from O*NET® OnLine (services.onetcenter.org), "
            "U.S. Department of Labor. O*NET® is a registered trademark of the U.S. Department of Labor, "
            "Employment and Training Administration. Used under CC BY 4.0."
        ),
        "license": "CC BY 4.0",
        "source": "O*NET Web Services",
        "publisher": "U.S. Department of Labor, Employment and Training Administration",
    }


def validate_attribution_present(text: Any) -> dict:
    """출력 텍스트에 attribution이 포함되었는지 검증."""
    if not isinstance(text, str):
        return {"ok": False, "reason": "non-string"}
    has_kr = "data.go.kr" in text or "공공데이터포털" in text
    has_onet = "O*NET" in text or "onetcenter" in text.lower()
    return {
        "ok": has_kr or has_onet,
        "has_kr_attribution": has_kr,
        "has_onet_attribution": has_onet,
    }


# ---------------------------------------------------------------------------
# 5. SYNC 검증
# ---------------------------------------------------------------------------

def validate_api_endpoints_sync() -> dict:
    """등록된 endpoint URL 7+1개 형식 검증 (도메인·경로 무결성)."""
    expected_kr_count = 7
    actual_kr = len(DATA_GO_KR_ENDPOINTS)
    invalid: list[str] = []
    for ds_id, url in DATA_GO_KR_ENDPOINTS.items():
        if not url.startswith("https://"):
            invalid.append(f"{ds_id}: not HTTPS")
    return {
        "ok": actual_kr == expected_kr_count and not invalid,
        "expected_kr": expected_kr_count,
        "actual_kr": actual_kr,
        "invalid_urls": invalid,
        "onet_base": ONET_BASE_URL,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _bool_arg(s: Any) -> bool:
    return str(s).strip().lower() in ("true", "1", "yes", "y", "t")


def main() -> int:
    parser = argparse.ArgumentParser(description="vision-school-major-info deterministic helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check_api_keys")
    sub.add_parser("validate_api_keys")
    sub.add_parser("attribution_text")
    sub.add_parser("onet_attribution_text")
    sub.add_parser("validate_api_endpoints_sync")

    p = sub.add_parser("setup_api_key")
    p.add_argument("--name", required=True, choices=list(VALID_KEY_NAMES))
    p.add_argument("--value", required=True)

    p = sub.add_parser("kr_search_university")
    p.add_argument("--name", default=None)
    p.add_argument("--region", default=None)
    p.add_argument("--per-page", type=int, default=10, dest="per_page")

    p = sub.add_parser("kr_search_major")
    p.add_argument("--keyword", default=None)
    p.add_argument("--per-page", type=int, default=10, dest="per_page")

    p = sub.add_parser("kr_career_search")
    p.add_argument("--keyword", default=None)
    p.add_argument("--per-page", type=int, default=10, dest="per_page")

    p = sub.add_parser("onet_search_occupation")
    p.add_argument("--keyword", required=True)

    p = sub.add_parser("onet_occupation_detail")
    p.add_argument("--soc-code", required=True, dest="soc_code")

    p = sub.add_parser("holland_to_onet")
    p.add_argument("--code", required=True)

    p = sub.add_parser("ko_en_major_dict")
    p.add_argument("--ko", default=None)

    p = sub.add_parser("major_to_onet")
    p.add_argument("--ko-major", required=True, dest="ko_major")

    p = sub.add_parser("validate_attribution_present")
    p.add_argument("--text", required=True)

    args = parser.parse_args()
    cmd = args.cmd

    if cmd == "check_api_keys":
        out = check_api_keys()
    elif cmd == "setup_api_key":
        out = setup_api_key(args.name, args.value)
    elif cmd == "validate_api_keys":
        out = validate_api_keys()
    elif cmd == "kr_search_university":
        out = kr_search_university(args.name, args.region, args.per_page)
    elif cmd == "kr_search_major":
        out = kr_search_major(args.keyword, args.per_page)
    elif cmd == "kr_career_search":
        out = kr_career_search(args.keyword, args.per_page)
    elif cmd == "onet_search_occupation":
        out = onet_search_occupation(args.keyword)
    elif cmd == "onet_occupation_detail":
        out = onet_occupation_detail(args.soc_code)
    elif cmd == "holland_to_onet":
        out = holland_to_onet(args.code)
    elif cmd == "ko_en_major_dict":
        out = ko_en_major_dict(args.ko)
    elif cmd == "major_to_onet":
        out = major_to_onet(args.ko_major)
    elif cmd == "attribution_text":
        out = attribution_text()
    elif cmd == "onet_attribution_text":
        out = onet_attribution_text()
    elif cmd == "validate_attribution_present":
        out = validate_attribution_present(args.text)
    elif cmd == "validate_api_endpoints_sync":
        out = validate_api_endpoints_sync()
    else:
        parser.error(f"unknown command: {cmd}")
        return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
