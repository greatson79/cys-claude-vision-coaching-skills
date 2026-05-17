#!/usr/bin/env python3
"""
vision-mbti-visioncoding ROUND 4 적대적 검증 — 학자 시각 10개 시나리오.

ROUND 1·2·3과 *완전히 다른* 적대적 검증.
"근거 대시오·페이지 줘봐·진짜 그렇소" 식의 *학자/검증자 시각* 프롬프트.
스킬이 자작·할루시네이션 없이 결정론 메타데이터로 답하는지 검증.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = os.path.join(os.path.dirname(HERE), "mbti_engine.py")


def call(cmd_args, stdin_payload=None):
    proc = subprocess.run(
        ["python3", ENGINE] + cmd_args,
        input=stdin_payload.encode() if stdin_payload else None,
        capture_output=True, timeout=10,
    )
    try:
        return json.loads(proc.stdout.decode().strip())
    except json.JSONDecodeError:
        return {"_raw": proc.stdout.decode(), "_err": proc.stderr.decode()}


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {name}" + (f"  -- {detail}" if not condition and detail else ""))
    return condition


def main():
    failures = []

    # A1: "Pittenger 1993의 정확한 저널·권·호·페이지를 보여달라"
    r = call(["refs", "pittenger_1993"])
    p93 = r.get("pittenger_1993", {})
    cond = (p93.get("journal") == "Journal of Career Planning and Employment"
            and p93.get("volume_issue_pages") == "54(1), 48–52"
            and p93.get("year") == 1993)
    if not check("A1 Pittenger 1993 서지 정확", cond, f"got={p93}"):
        failures.append(("A1", p93))

    # A2: "Pittenger 2005에 DOI가 있다고? 검증 가능한가?"
    r = call(["refs", "pittenger_2005"])
    p05 = r.get("pittenger_2005", {})
    cond = (p05.get("doi") == "10.1037/1065-9293.57.3.210"
            and p05.get("journal") == "Consulting Psychology Journal: Practice and Research"
            and p05.get("publisher") == "American Psychological Association (APA)")
    if not check("A2 Pittenger 2005 DOI + 저널 + APA", cond, f"got={p05}"):
        failures.append(("A2", p05))

    # A3: "Myers 1980 'Gifts Differing' 출판사·장소 정확히"
    r = call(["refs", "myers_1980_gifts_differing"])
    m80 = r.get("myers_1980_gifts_differing", {})
    cond = ("Consulting Psychologists Press" in m80.get("publisher", "")
            and "Mountain View" in m80.get("place", "")
            and m80.get("year") == 1980)
    if not check("A3 Myers 1980 CPP·Mountain View", cond, f"got={m80}"):
        failures.append(("A3", m80))

    # A4: "MBTI Manual 3rd ed.의 정확한 표 번호와 sample N은?"
    r = call(["refs", "mbti_manual_1998_3rd"])
    mm = r.get("mbti_manual_1998_3rd", {})
    cond = ("Table 7.6" in mm.get("table_cited", "")
            and "N=3009" in mm.get("table_cited", "")
            and "1996" in mm.get("table_cited", ""))
    if not check("A4 MBTI Manual Table 7.6 Sample 1 N=3009 1996", cond,
                 f"got={mm.get('table_cited')}"):
        failures.append(("A4", mm))

    # A5: "Jung 1921의 영어 번역자는?"
    r = call(["refs", "jung_1921_psychological_types"])
    j = r.get("jung_1921_psychological_types", {})
    cond = ("R. F. C. Hull" in j.get("english_translation", "")
            and "Princeton University Press" in j.get("english_translation", "")
            and "Bollingen Series XX" in j.get("english_translation", "")
            and "H. G. Baynes" in j.get("english_translation", "")  # 1923 원역자
            and j.get("original_year") == 1921)
    if not check("A5 Jung 1921 Hull/Baynes 번역 + Bollingen + Princeton", cond,
                 f"got={j.get('english_translation')}"):
        failures.append(("A5", j))

    # A6: "Quenk 2002의 정확한 부제는?"
    r = call(["refs", "quenk_2002_grip"])
    q = r.get("quenk_2002_grip", {})
    cond = ("How Everyday Stress Brings Out Our Hidden Personality" in q.get("title", "")
            and "Davies-Black" in q.get("publisher", ""))
    if not check("A6 Quenk 부제 'Everyday Stress' + Davies-Black", cond,
                 f"got={q.get('title')} pub={q.get('publisher')}"):
        failures.append(("A6", q))

    # A7: "Keirsey 1998 출판사·장소는?"
    r = call(["refs", "keirsey_1998_pumii"])
    k = r.get("keirsey_1998_pumii", {})
    cond = ("Prometheus Nemesis" in k.get("publisher", "")
            and "Del Mar" in k.get("place", "")
            and k.get("year") == 1998)
    if not check("A7 Keirsey Prometheus Nemesis · Del Mar 1998", cond,
                 f"got={k}"):
        failures.append(("A7", k))

    # A8: "Beebe 2017 출판사는? 시리즈는?"
    r = call(["refs", "beebe_2017_8function"])
    b = r.get("beebe_2017_8function", {})
    cond = (b.get("publisher") == "Routledge"
            and "Routledge Mental Health Classic Editions" in b.get("series", ""))
    if not check("A8 Beebe 2017 Routledge Classic Editions", cond, f"got={b}"):
        failures.append(("A8", b))

    # A9: "16personalities의 NERIS와 Myers MBTI 차이를 정확히 알고 있나?"
    r = call(["refs", "neris_16personalities"])
    n = r.get("neris_16personalities", {})
    cond = ("NERIS Analytics" in n.get("authors", "")
            and "A/T" in n.get("notes", "")  # 5번째 축 명시
            and "공식 명칭이 아님" in n.get("notes", "")
            and n.get("year_first_published") == 2013)
    if not check("A9 NERIS 모델 차이 (5번째 축 A/T) + Myers 비공식 명시", cond,
                 f"got={n}"):
        failures.append(("A9", n))

    # A10: "lookup 응답에 학술 메타데이터 *전체*가 실려 있는지 확인" (verifiability)
    r = call(["lookup", "ENFP"])
    cond = ("sources" in r and "critique_sources" in r
            and len(r["sources"]) >= 5
            and "pittenger_1993" in r["critique_sources"]
            and "pittenger_2005" in r["critique_sources"]
            and r["sources"]["mbti_manual_1998_3rd"]["table_cited"].startswith("Table 7.6"))
    if not check("A10 lookup 응답에 풀 메타데이터 5+2개 포함", cond,
                 f"keys={list(r.get('sources', {}).keys())}"):
        failures.append(("A10", r))

    print()
    if failures:
        print(f"FAIL: {len(failures)}/10 (실패: {[f[0] for f in failures]})")
        sys.exit(1)
    print("ROUND 4 ALL PASS: 10/10 — 적대적 학자 검증 통과")


if __name__ == "__main__":
    main()
