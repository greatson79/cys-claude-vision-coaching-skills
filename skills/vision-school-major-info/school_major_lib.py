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
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# 0. 키 저장·진입 가드
# ---------------------------------------------------------------------------

CONFIG_DIR = os.environ.get("VISION_SMI_CONFIG_DIR") or os.path.expanduser("~/.config/vision-school-major-info")
KEYS_PATH = os.environ.get("VISION_SMI_KEYS_PATH") or os.path.join(CONFIG_DIR, "api_keys.json")
CACHE_DIR = os.environ.get("VISION_SMI_CACHE_DIR") or os.path.expanduser("~/.cache/vision-school-major-info")

VALID_KEY_NAMES = ("data_go_kr", "onet")

# 데이터셋 ID → 호출 endpoint URL.
# - 커리어넷 4개(15057878·15058917·15056641·15057135): 모두 career.go.kr OpenAPI 단일 게이트웨이 (svcCode 분기).
# - KCUE 3개(15116892·15037507·15116816): 공공데이터포털 apis.data.go.kr 게이트웨이.
# 각 endpoint 명세는 SOURCES.md A-01~A-07 참조.
DATA_GO_KR_ENDPOINTS = {
    "15057878": "https://www.career.go.kr/cnet/openapi/getOpenApi",   # 커리어넷 대학학과정보
    "15058917": "https://www.career.go.kr/cnet/openapi/getOpenApi",   # 커리어넷 학교정보
    "15056641": "https://www.career.go.kr/cnet/openapi/getOpenApi",   # 커리어넷 직업정보
    "15057135": "https://www.career.go.kr/cnet/openapi/getOpenApi",   # 커리어넷 진로자료
    "15116892": "https://apis.data.go.kr/B552103/UnivMajorInfoService/getUnivMajorInfo",
    "15037507": "https://apis.data.go.kr/B552103/HEducationInfoService/getUnivInfo",
    "15116816": "https://apis.data.go.kr/B552103/UnivInfoService/getUnivInfo",
}

# 데이터셋 ID → 사람-친화 명칭 (SOURCES.md A-01~A-07 1:1 대조)
DATA_GO_KR_DATASETS = {
    "15057878": "교육부_커리어넷 대학학과정보",
    "15058917": "교육부_커리어넷 학교정보",
    "15056641": "교육부_커리어넷 직업정보",
    "15057135": "교육부_커리어넷 진로자료",
    "15116892": "KCUE 대학별 학과정보",
    "15037507": "KCUE 대학알리미 대학 기본정보",
    "15116816": "KCUE 대학 및 전문대학정보",
}

ONET_BASE_URL = "https://api-v2.onetcenter.org/"

# 캐시 TTL (초)
KR_CACHE_TTL_SEC = 24 * 3600         # 24 시간
ONET_CACHE_TTL_SEC = 90 * 24 * 3600  # 90 일 (ONET 분기 갱신 주기)


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

【선택】 ONET Web Services v2.0 — 미국 직업 (유학·해외 진로용)
  1) https://services.onetcenter.org/developer/signup 회원가입
  2) 회원가입 후 https://services.onetcenter.org/developer/ "My Account"
     → "API Keys" 섹션에서 "Generate New Key" → API key 발급(즉시 활성).
  3) 발급된 API key를 그대로 복사 (X-API-Key 헤더 전용·Basic Auth 폐지)
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

    if keys.get("data_go_kr"):
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
        ok = status == 200 and ("dataSearch" in body or "totalCount" in body)
        result["data_go_kr"] = {
            "ok": ok,
            "status": status,
            "note": "200 + dataSearch/totalCount → valid" if ok else "키 무효 또는 활용신청 미완료. 안내 다시 확인.",
        }

    if keys.get("onet"):
        # ONET v2.0 — X-API-Key 헤더 전용 + api-v2.onetcenter.org base URL.
        # 공식 샘플: https://github.com/onetcenter/web-services-v2-samples/python/OnetWebService.py
        url = ONET_BASE_URL + "about/"
        req = Request(
            url,
            headers={
                "X-API-Key": keys["onet"],
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
# 1. 캐시 — 결정론 파일 캐시 (TTL 검증)
# ---------------------------------------------------------------------------

def _cache_path(namespace: str, key: str) -> str:
    safe_key = re.sub(r"[^A-Za-z0-9_.\-]", "_", key)[:120]
    return os.path.join(CACHE_DIR, namespace, safe_key + ".json")


def _cache_get(namespace: str, key: str, ttl_sec: int) -> Any:
    p = _cache_path(namespace, key)
    if not os.path.exists(p):
        return None
    try:
        st = os.stat(p)
    except OSError:
        return None
    if (time.time() - st.st_mtime) > ttl_sec:
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _cache_put(namespace: str, key: str, data: Any) -> str:
    p = _cache_path(namespace, key)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, p)
    return p


def refresh_korean_data_cache(prune: Any = False) -> dict:
    """한국 데이터 캐시 정리. prune=True 시 24h TTL 초과 항목 삭제."""
    ns = os.path.join(CACHE_DIR, "kr")
    pruned: list[str] = []
    kept: list[str] = []
    if os.path.isdir(ns):
        now = time.time()
        for fn in os.listdir(ns):
            fp = os.path.join(ns, fn)
            try:
                age = now - os.stat(fp).st_mtime
            except OSError:
                continue
            if age > KR_CACHE_TTL_SEC and (prune is True or str(prune).lower() in ("true", "1", "yes")):
                try:
                    os.remove(fp)
                    pruned.append(fn)
                except OSError:
                    pass
            else:
                kept.append(fn)
    return {
        "ok": True,
        "namespace": ns,
        "ttl_sec": KR_CACHE_TTL_SEC,
        "pruned": pruned,
        "kept": kept,
    }


def refresh_onet_cache(prune: Any = False) -> dict:
    """ONET 캐시 정리. prune=True 시 90일 TTL 초과 항목 삭제."""
    ns = os.path.join(CACHE_DIR, "onet")
    pruned: list[str] = []
    kept: list[str] = []
    if os.path.isdir(ns):
        now = time.time()
        for fn in os.listdir(ns):
            fp = os.path.join(ns, fn)
            try:
                age = now - os.stat(fp).st_mtime
            except OSError:
                continue
            if age > ONET_CACHE_TTL_SEC and (prune is True or str(prune).lower() in ("true", "1", "yes")):
                try:
                    os.remove(fp)
                    pruned.append(fn)
                except OSError:
                    pass
            else:
                kept.append(fn)
    return {
        "ok": True,
        "namespace": ns,
        "ttl_sec": ONET_CACHE_TTL_SEC,
        "pruned": pruned,
        "kept": kept,
    }


# ---------------------------------------------------------------------------
# 2. 한국 데이터 호출 — 커리어넷·KCUE
# ---------------------------------------------------------------------------

def _require_kr_key() -> str | None:
    keys = _load_keys()
    v = keys.get("data_go_kr")
    return v if isinstance(v, str) and v.strip() else None


def _kr_career_call(svc_code: str, gubun: str, extra: dict | None = None, per_page: int = 10) -> dict:
    """커리어넷 OpenAPI 단일 게이트웨이 호출 (캐시 통합)."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered. Run check_api_keys."}
    per = max(1, min(int(per_page), 100))
    params = {
        "apiKey": key,
        "svcType": "api",
        "svcCode": svc_code,
        "contentType": "json",
        "gubun": gubun,
        "thisPage": 1,
        "perPage": per,
    }
    if extra:
        for k, v in extra.items():
            if v is not None and str(v).strip():
                params[k] = str(v).strip()
    cache_key = svc_code + "_" + gubun + "_" + "_".join(f"{k}={v}" for k, v in sorted(params.items()) if k != "apiKey")
    cached = _cache_get("kr", cache_key, KR_CACHE_TTL_SEC)
    if cached is not None:
        cached["from_cache"] = True
        return cached
    status, body = _http_get("https://www.career.go.kr/cnet/openapi/getOpenApi", params)
    payload = {
        "ok": status == 200,
        "status": status,
        "raw": body[:5000] if body else "",
        "attribution": attribution_text(),
        "from_cache": False,
    }
    if payload["ok"]:
        _cache_put("kr", cache_key, payload)
    return payload


def kr_search_university(name: Any = None, region: Any = None, per_page: int = 10) -> dict:
    """커리어넷 학교정보 검색 (15058917)."""
    return _kr_career_call("SCHOOL", "univ_list", {"searchSchulNm": name, "region": region}, per_page)


def kr_search_major(keyword: Any = None, per_page: int = 10) -> dict:
    """커리어넷 학과정보 검색 (15057878)."""
    return _kr_career_call("MAJOR", "univ_list", {"searchMajorName": keyword}, per_page)


def kr_career_search(keyword: Any = None, per_page: int = 10) -> dict:
    """커리어넷 직업정보 검색 (15056641)."""
    return _kr_career_call("JOB", "job_dic_list", {"searchJobNm": keyword}, per_page)


def kr_major_detail(major_seq: Any = None, keyword: Any = None) -> dict:
    """커리어넷 학과 상세 (15057878). major_seq 또는 keyword로 조회."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered"}
    if not (major_seq or keyword):
        return {"ok": False, "reason": "major_seq 또는 keyword 중 하나 필요"}
    extra: dict = {}
    if major_seq:
        extra["majorSeq"] = major_seq
    if keyword:
        extra["searchMajorName"] = keyword
    return _kr_career_call("MAJOR", "univ_detail", extra, per_page=1)


def kr_career_detail(career_seq: Any = None, keyword: Any = None) -> dict:
    """커리어넷 직업 상세 (15056641). career_seq 또는 keyword."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered"}
    if not (career_seq or keyword):
        return {"ok": False, "reason": "career_seq 또는 keyword 중 하나 필요"}
    extra: dict = {}
    if career_seq:
        extra["seq"] = career_seq
    if keyword:
        extra["searchJobNm"] = keyword
    return _kr_career_call("JOB", "job_dic_detail", extra, per_page=1)


def kr_career_resources(keyword: Any = None, per_page: int = 10) -> dict:
    """커리어넷 진로자료 (15057135) 검색."""
    return _kr_career_call("CAREERINFO", "resource_list", {"searchTitle": keyword}, per_page)


def kr_majors_by_university(univ_name: Any = None, per_page: int = 50) -> dict:
    """KCUE 대학별 학과정보 (15116892) — 특정 대학의 학과 목록.
    공공데이터포털 apis.data.go.kr 게이트웨이 호출."""
    key = _require_kr_key()
    if not key:
        return {"ok": False, "reason": "data_go_kr key not registered"}
    per = max(1, min(int(per_page), 100))
    params = {
        "serviceKey": key,
        "pageNo": 1,
        "numOfRows": per,
        "type": "json",
    }
    if univ_name and isinstance(univ_name, str) and univ_name.strip():
        params["schlKrnNm"] = univ_name.strip()
    cache_key = "kcue_majors_" + (univ_name or "all")
    cached = _cache_get("kr", cache_key, KR_CACHE_TTL_SEC)
    if cached is not None:
        cached["from_cache"] = True
        return cached
    status, body = _http_get(DATA_GO_KR_ENDPOINTS["15116892"], params)
    payload = {
        "ok": status == 200,
        "status": status,
        "endpoint": DATA_GO_KR_ENDPOINTS["15116892"],
        "raw": body[:5000] if body else "",
        "attribution": attribution_text(),
        "from_cache": False,
        "dataset_id": "15116892",
        "dataset_name": DATA_GO_KR_DATASETS["15116892"],
    }
    if payload["ok"]:
        _cache_put("kr", cache_key, payload)
    return payload


def kr_university_by_region(region: Any = None, per_page: int = 50) -> dict:
    """지역별 대학 — 커리어넷 학교정보 + KCUE 대학 기본정보 통합 (15058917 + 15037507)."""
    if not region or not isinstance(region, str) or not region.strip():
        return {"ok": False, "reason": "region required (예: 서울·경기·부산)"}
    # 1차: 커리어넷 학교정보 region 파라미터
    career = kr_search_university(name=None, region=region, per_page=per_page)
    # 2차: KCUE 대학알리미 기본정보 (지역 필터)
    key = _require_kr_key()
    kcue_payload: dict = {"ok": False, "reason": "data_go_kr key not registered"}
    if key:
        per = max(1, min(int(per_page), 100))
        params = {
            "serviceKey": key,
            "pageNo": 1,
            "numOfRows": per,
            "type": "json",
            "schlSido": region.strip(),
        }
        status, body = _http_get(DATA_GO_KR_ENDPOINTS["15037507"], params)
        kcue_payload = {
            "ok": status == 200,
            "status": status,
            "endpoint": DATA_GO_KR_ENDPOINTS["15037507"],
            "raw": body[:5000] if body else "",
            "dataset_id": "15037507",
            "dataset_name": DATA_GO_KR_DATASETS["15037507"],
        }
    return {
        "ok": career.get("ok") or kcue_payload.get("ok"),
        "region": region,
        "career_net_school_info": career,
        "kcue_univ_info": kcue_payload,
        "attribution": attribution_text(),
    }


# ---------------------------------------------------------------------------
# 3. ONET — 미국 직업 정보
# ---------------------------------------------------------------------------

def _require_onet_key() -> str | None:
    keys = _load_keys()
    v = keys.get("onet")
    return v if isinstance(v, str) and v.strip() else None


def _onet_get(path: str, timeout: float = 20.0) -> tuple[int, Any]:
    key = _require_onet_key()
    if not key:
        return -1, {"reason": "onet key not registered"}
    cache_key = "onet_" + path
    cached = _cache_get("onet", cache_key, ONET_CACHE_TTL_SEC)
    if cached is not None:
        return 200, cached
    # ONET v2.0 — X-API-Key 헤더 전용 (Basic Auth 폐지·query string 폐지).
    url = ONET_BASE_URL + path.lstrip("/")
    req = Request(
        url,
        headers={
            "X-API-Key": key,
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
            if resp.status == 200:
                _cache_put("onet", cache_key, data)
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


# ONET-SOC 정규식. 공식 형식: NN-NNNN.NN (예: 15-1252.00 Software Developers).
# 일부 코드는 분리 확장(예: 15-1252.01)이 존재하지만 NN-NNNN.NN 패턴은 유지된다.
ONET_SOC_PATTERN = re.compile(r"^\d{2}-\d{4}\.\d{2}$")


def onet_occupation_detail(soc_code: Any) -> dict:
    if not isinstance(soc_code, str) or not ONET_SOC_PATTERN.match(soc_code.strip()):
        return {"ok": False, "reason": "soc_code must be in format NN-NNNN.NN (e.g., 15-1252.00)"}
    # ONET v2.0: /online/occupations/{soc}/ (overview). /details/* sub-paths는 별도 호출.
    status, data = _onet_get(f"online/occupations/{soc_code.strip()}/")
    return {
        "ok": status == 200,
        "status": status,
        "data": data,
        "attribution": onet_attribution_text(),
    }


# Holland → ONET 매핑 (학계 표준).
# ONET Interest Profiler가 채택한 RIASEC 6 영역 (Holland 1997 Making Vocational Choices 3rd ed.).
# 각 코드별 ONET 검색 키워드는 ONET-SOC 분류에서 해당 interest area에 속하는 대표 직업명에서 추출.
# 출처: SOURCES.md § C-01, C-02 + ONET Career One Stop.
HOLLAND_ONET_KEYWORDS = {
    "R": ["mechanic", "engineer", "technician", "agricultural", "construction", "carpenter"],
    "I": ["scientist", "researcher", "analyst", "biologist", "physicist", "data", "statistician"],
    "A": ["artist", "designer", "musician", "writer", "actor", "creative", "photographer"],
    "S": ["teacher", "counselor", "social worker", "nurse", "therapist", "clergy"],
    "E": ["manager", "sales", "executive", "entrepreneur", "lawyer", "marketing"],
    "C": ["accountant", "auditor", "secretary", "clerk", "administrative", "bookkeeper"],
}

# Holland 코드 한글 명칭 (학계 표준 — Holland 1997 + 한국 직업능력연구원 STRONG 직업흥미검사)
HOLLAND_KO_LABELS = {
    "R": "현실형 (Realistic)",
    "I": "탐구형 (Investigative)",
    "A": "예술형 (Artistic)",
    "S": "사회형 (Social)",
    "E": "진취형 (Enterprising)",
    "C": "관습형 (Conventional)",
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
        "holland_label_ko": HOLLAND_KO_LABELS[c],
        "search_keywords": keywords,
        "note": "각 키워드를 onet_search_occupation에 넣어 직업 후보를 받을 수 있음.",
        "attribution": onet_attribution_text(),
        "source": "Holland 1997 + ONET Interest Profiler",
    }


# ---------------------------------------------------------------------------
# 4. 한↔영 학과명 매핑 사전 (시드 — 70+ 항목)
# ---------------------------------------------------------------------------

KO_EN_MAJOR_DICT = {
    # 공학
    "컴퓨터공학": "Computer Science",
    "컴퓨터과학": "Computer Science",
    "소프트웨어공학": "Software Engineering",
    "전자공학": "Electrical Engineering",
    "전기공학": "Electrical Engineering",
    "기계공학": "Mechanical Engineering",
    "화학공학": "Chemical Engineering",
    "산업공학": "Industrial Engineering",
    "건축학": "Architecture",
    "건축공학": "Architectural Engineering",
    "토목공학": "Civil Engineering",
    "환경공학": "Environmental Engineering",
    "정보통신공학": "Information & Communication Engineering",
    "재료공학": "Materials Engineering",
    "신소재공학": "Materials Science & Engineering",
    "자동차공학": "Automotive Engineering",
    "조선해양공학": "Naval Architecture & Ocean Engineering",
    "항공우주공학": "Aerospace Engineering",
    "원자력공학": "Nuclear Engineering",
    "생명공학": "Bioengineering",
    "바이오공학": "Biotechnology",
    # 자연과학
    "수학": "Mathematics",
    "통계학": "Statistics",
    "물리학": "Physics",
    "화학": "Chemistry",
    "생물학": "Biology",
    "지구과학": "Earth Science",
    "지질학": "Geology",
    "천문학": "Astronomy",
    "해양학": "Oceanography",
    "지리학": "Geography",
    # 사회과학·인문학
    "심리학": "Psychology",
    "사회학": "Sociology",
    "인류학": "Anthropology",
    "경영학": "Business Administration",
    "경제학": "Economics",
    "회계학": "Accounting",
    "재무학": "Finance",
    "법학": "Law",
    "정치외교학": "Political Science",
    "행정학": "Public Administration",
    "국제관계학": "International Relations",
    "국어국문학": "Korean Language & Literature",
    "영어영문학": "English Language & Literature",
    "중어중문학": "Chinese Language & Literature",
    "일어일문학": "Japanese Language & Literature",
    "독어독문학": "German Language & Literature",
    "불어불문학": "French Language & Literature",
    "역사학": "History",
    "사학": "History",
    "철학": "Philosophy",
    "고고학": "Archaeology",
    # 신학·종교
    "신학": "Theology",
    "기독교학": "Christian Studies",
    "종교학": "Religious Studies",
    # 의약·보건
    "의학": "Medicine",
    "한의학": "Korean Medicine",
    "치의학": "Dentistry",
    "약학": "Pharmacy",
    "수의학": "Veterinary Medicine",
    "간호학": "Nursing",
    "물리치료학": "Physical Therapy",
    "임상병리학": "Medical Laboratory Science",
    "방사선학": "Radiologic Science",
    "보건학": "Public Health",
    # 사회복지·교육
    "사회복지학": "Social Welfare",
    "교육학": "Education",
    "유아교육학": "Early Childhood Education",
    "초등교육학": "Elementary Education",
    "특수교육학": "Special Education",
    # 예술·체육
    "디자인": "Design",
    "시각디자인": "Visual Design",
    "산업디자인": "Industrial Design",
    "패션디자인": "Fashion Design",
    "음악": "Music",
    "성악": "Vocal Music",
    "작곡": "Composition",
    "미술": "Fine Arts",
    "회화": "Painting",
    "조소": "Sculpture",
    "사진학": "Photography",
    "연극영화학": "Theater & Film",
    "무용": "Dance",
    "체육학": "Physical Education",
    "스포츠과학": "Sports Science",
    # 농수산·식품
    "식품영양학": "Food and Nutrition",
    "식품공학": "Food Science & Technology",
    "농학": "Agriculture",
    "원예학": "Horticulture",
    "임학": "Forestry",
    "축산학": "Animal Science",
    "수산학": "Fisheries Science",
    # 첨단·신생
    "데이터사이언스": "Data Science",
    "인공지능": "Artificial Intelligence",
    "빅데이터": "Big Data",
    "사이버보안": "Cybersecurity",
    # 미디어
    "미디어커뮤니케이션": "Media & Communication",
    "신문방송학": "Journalism & Broadcasting",
    "광고홍보학": "Advertising & Public Relations",
    "언론정보학": "Communication & Information",
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


def cross_reference_major_career(ko_major: Any) -> dict:
    """한국 학과 → 한국 직업 (커리어넷) + ONET 직업 (한↔영 매핑) 통합 조회.
    결정론 결합 — LLM 추론으로 직업명 만들어내는 것 차단."""
    if not isinstance(ko_major, str) or not ko_major.strip():
        return {"ok": False, "reason": "ko_major required"}
    m = ko_major.strip()
    # 1) 한↔영 매핑
    mapping = ko_en_major_dict(m)
    en = None
    if mapping.get("ok") and mapping.get("en"):
        en = mapping["en"]
    elif mapping.get("partial_matches"):
        en = list(mapping["partial_matches"].values())[0]
    # 2) 한국 학과 검색 (커리어넷)
    kr_major_result = kr_search_major(m) if _require_kr_key() else {
        "ok": False, "reason": "data_go_kr key not registered"
    }
    # 3) 한국 직업 검색 (커리어넷, 학과 키워드로 직업 후보)
    kr_career_result = kr_career_search(m) if _require_kr_key() else {
        "ok": False, "reason": "data_go_kr key not registered"
    }
    # 4) ONET 직업 검색
    onet_result: dict = {"ok": False, "reason": "no en mapping"}
    if en and _require_onet_key():
        onet_result = onet_search_occupation(en)
    elif en:
        onet_result = {"ok": False, "reason": "onet key not registered", "en_major": en}
    return {
        "ok": True,
        "ko_major": m,
        "en_major": en,
        "kr_major_info": kr_major_result,
        "kr_career_candidates": kr_career_result,
        "onet_occupations": onet_result,
        "kr_attribution": attribution_text(),
        "onet_attribution": onet_attribution_text() if en else None,
    }


# ---------------------------------------------------------------------------
# 5. Attribution 자동 생성 (할루시네이션 차단)
# ---------------------------------------------------------------------------

def attribution_text() -> dict:
    """한국 데이터 출처 표기."""
    return {
        "rendered": "출처: 공공데이터포털 (data.go.kr) — 교육부 커리어넷 + 한국대학교육협의회(KCUE) 대학알리미.",
        "source": "data.go.kr",
        "license": "공공누리 제1유형 (출처 표시)",
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
# 6. SYNC 검증
# ---------------------------------------------------------------------------

def validate_api_endpoints_sync() -> dict:
    """등록된 endpoint URL 7+1개 형식 검증 (도메인·경로 무결성)."""
    expected_kr_count = 7
    actual_kr = len(DATA_GO_KR_ENDPOINTS)
    expected_ids = {"15057878", "15058917", "15056641", "15057135", "15116892", "15037507", "15116816"}
    actual_ids = set(DATA_GO_KR_ENDPOINTS.keys())
    missing_ids = expected_ids - actual_ids
    extra_ids = actual_ids - expected_ids
    invalid: list[str] = []
    for ds_id, url in DATA_GO_KR_ENDPOINTS.items():
        if not url.startswith("https://"):
            invalid.append(f"{ds_id}: not HTTPS")
        if " " in url:
            invalid.append(f"{ds_id}: whitespace in URL")
    return {
        "ok": (
            actual_kr == expected_kr_count
            and not invalid
            and not missing_ids
            and not extra_ids
            and ONET_BASE_URL.startswith("https://")
        ),
        "expected_kr": expected_kr_count,
        "actual_kr": actual_kr,
        "missing_dataset_ids": sorted(missing_ids),
        "extra_dataset_ids": sorted(extra_ids),
        "invalid_urls": invalid,
        "onet_base": ONET_BASE_URL,
    }


# ---------------------------------------------------------------------------
# 7. CLI
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

    p = sub.add_parser("kr_major_detail")
    p.add_argument("--major-seq", default=None, dest="major_seq")
    p.add_argument("--keyword", default=None)

    p = sub.add_parser("kr_career_detail")
    p.add_argument("--career-seq", default=None, dest="career_seq")
    p.add_argument("--keyword", default=None)

    p = sub.add_parser("kr_career_resources")
    p.add_argument("--keyword", default=None)
    p.add_argument("--per-page", type=int, default=10, dest="per_page")

    p = sub.add_parser("kr_majors_by_university")
    p.add_argument("--univ-name", default=None, dest="univ_name")
    p.add_argument("--per-page", type=int, default=50, dest="per_page")

    p = sub.add_parser("kr_university_by_region")
    p.add_argument("--region", required=True)
    p.add_argument("--per-page", type=int, default=50, dest="per_page")

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

    p = sub.add_parser("cross_reference_major_career")
    p.add_argument("--ko-major", required=True, dest="ko_major")

    p = sub.add_parser("validate_attribution_present")
    p.add_argument("--text", required=True)

    p = sub.add_parser("refresh_korean_data_cache")
    p.add_argument("--prune", default="false")

    p = sub.add_parser("refresh_onet_cache")
    p.add_argument("--prune", default="false")

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
    elif cmd == "kr_major_detail":
        out = kr_major_detail(args.major_seq, args.keyword)
    elif cmd == "kr_career_detail":
        out = kr_career_detail(args.career_seq, args.keyword)
    elif cmd == "kr_career_resources":
        out = kr_career_resources(args.keyword, args.per_page)
    elif cmd == "kr_majors_by_university":
        out = kr_majors_by_university(args.univ_name, args.per_page)
    elif cmd == "kr_university_by_region":
        out = kr_university_by_region(args.region, args.per_page)
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
    elif cmd == "cross_reference_major_career":
        out = cross_reference_major_career(args.ko_major)
    elif cmd == "attribution_text":
        out = attribution_text()
    elif cmd == "onet_attribution_text":
        out = onet_attribution_text()
    elif cmd == "validate_attribution_present":
        out = validate_attribution_present(args.text)
    elif cmd == "validate_api_endpoints_sync":
        out = validate_api_endpoints_sync()
    elif cmd == "refresh_korean_data_cache":
        out = refresh_korean_data_cache(_bool_arg(args.prune))
    elif cmd == "refresh_onet_cache":
        out = refresh_onet_cache(_bool_arg(args.prune))
    else:
        parser.error(f"unknown command: {cmd}")
        return 2

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
