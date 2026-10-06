"""Task 7 — 내비게이터 대시보드 생성 (코드).

사용법:
  python tools/build_dashboard.py <run_dir> <briefing.md> <eval.md> <out.html>

- briefing.md : Evaluator PASS(또는 최대 반복 도달)된 AI ① 결과
- eval.md     : 마지막 Evaluator 결과 (판정 PASS/FAIL 표시용)
- run_dir     : Task 2~5 결과 폴더
    - task3_history.md : 대기시간 표
    - kind_04.json     : 에버랜드 식당 공식 한글명·키워드 (있으면 영문 식당명을 한글로 바꿈)
"""
import html
import json
import re
import sys
from pathlib import Path

ZONES_KO = {"European Adventure": "유러피언 어드벤처", "Global Fair": "글로벌 페어", "American Adventure": "아메리칸 어드벤처",
            "Magic Land": "매직랜드", "Zootopia": "주토피아"}


def sections(md):
    out, cur = {}, None
    for line in md.splitlines():
        m = re.match(r"^##\s+(.+)$", line)
        if m:
            cur = m.group(1).strip()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return out


def table(lines):
    rows = [l for l in lines if l.strip().startswith("|")]
    rows = [r for r in rows if not re.match(r"^\|\s*-", r.strip())]
    parsed = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    return parsed[0], parsed[1:]


def inline(s):
    s = html.escape(s)
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def load_ko(run):
    """영문 식당명 → (한글명, 공식 한글 키워드). kind_04.json이 없으면 빈 매핑."""
    f = run / "kind_04.json"
    if not f.exists():
        return {}
    out = {}
    for x in json.loads(f.read_text(encoding="utf-8"))["faciltList"]:
        kws = [k.strip() for k in re.split(r"[#]", x.get("keywordDescrt") or "") if k.strip()]
        kws = [k for k in kws if k.replace(" ", "") != x["faciltName"].replace(" ", "")]
        out[x["faciltNameEng"].strip()] = (x["faciltName"].strip(), kws[:4])
    return out


def localize(text, ko):
    for en in sorted(ko, key=len, reverse=True):
        text = text.replace(en, ko[en][0])
    for en in sorted(ZONES_KO, key=len, reverse=True):
        text = text.replace(en, ZONES_KO[en])
    return text


def main(run_dir, briefing_path, eval_path, out_path):
    run = Path(run_dir)
    ev = Path(eval_path).read_text(encoding="utf-8")
    verdict = "PASS" if re.search(r"판정:\s*PASS", ev) else "FAIL"
    raw = Path(briefing_path).read_text(encoding="utf-8")
    attempt = re.search(r"시도\s*(\d+)회차", raw)
    attempt = attempt.group(1) if attempt else "?"

    ko = load_ko(run)
    sec_raw = sections(raw)
    _, rests_raw = table(sec_raw["식당 정보"])
    b = localize(raw, ko)
    sec = sections(b)

    brief = " ".join(l.strip() for l in sec.get("06:00 브리핑", []) if l.strip())
    _, status = table(sec["현황판"])
    checks = [l.strip()[6:] for l in sec["준비해야 할 것들"] if l.strip().startswith("- [ ]")]
    _, sched = table(sec["스케줄러"])
    reviews = [l.strip()[2:] for l in sec["이용자 후기 요약"] if l.strip().startswith("- ")]
    rest_note = " ".join(l.strip() for l in sec["식당 정보"] if l.strip().startswith("※"))

    hist = (run / "task3_history.md").read_text(encoding="utf-8")
    _, waits = table(sections(hist)["어트랙션 대기시간 (기록 시각 기준, 분)"])
    rec_at = re.search(r"기록 시각:\s*([^\n—]+)", hist).group(1).strip()
    waits = [w for w in waits if w[2].isdigit()][:8]
    max_w = max(int(w[2]) for w in waits) if waits else 1

    icons = {"발렛": ("bi-car-front-fill", "red"), "정문주차장": ("bi-p-square-fill", "yellow"), "예약 상태": ("bi-calendar-check-fill", "green"),
             "날씨": ("bi-cloud-sun-fill", "blue"), "이벤트·퍼레이드": ("bi-stars", "purple"), "지난 주말 대기열": ("bi-hourglass-split", "navy")}
    kpi = "".join(
        f'<div class="card stat"><div class="stats-icon {icons.get(r[0], ("bi-info-circle-fill", "navy"))[1]}">'
        f'<i class="bi {icons.get(r[0], ("bi-info-circle-fill",))[0]}"></i></div>'
        f'<div><h6>{inline(r[0])}</h6><div class="val">{inline(r[1])}</div><div class="src">출처: {inline(r[2])}</div></div></div>'
        for r in status)
    chk = "".join(f'<li><input type="checkbox" id="c{i}"><label for="c{i}">{inline(c)}</label></li>' for i, c in enumerate(checks))

    def point(what):
        if "점심" in what or "저녁" in what:
            return "p-red"
        if "사파리" in what or "사바나" in what:
            return "p-green"
        if re.search(r"애니멀톡|윙스|톡", what):
            return "p-blue"
        return ""
    tl = "".join(
        f'<li class="{point(r[1])}"><div class="t">{inline(r[0])}</div><div><div>{inline(r[1])}</div><div class="d">근거: {inline(r[2])}</div></div></li>'
        for r in sched)
    color = lambda m: "red" if m >= 40 else "yellow" if m >= 20 else "green"
    wt = "".join(
        f'<tr><td>{inline(w[0])}</td><td>{inline(ZONES_KO.get(w[1], w[1]))}</td><td class="num">{w[2]}</td>'
        f'<td><div class="bar"><span style="width:{int(w[2]) * 100 // max_w}%;background:var(--{color(int(w[2]))})"></span></div></td></tr>'
        for w in waits)
    tag = {"주차": ("bi-p-circle-fill", "yellow"), "혼잡": ("bi-people-fill", "red"), "퍼레이드": ("bi-balloon-fill", "purple")}
    def rv_icon(r):
        for k, v in tag.items():
            if r.startswith(k):
                return v
        return ("bi-chat-dots-fill", "blue")
    rv = "".join(
        f'<div class="review"><div class="avatar sm" style="background:var(--{rv_icon(r)[1]})"><i class="bi {rv_icon(r)[0]}"></i></div><div>{inline(r)}</div></div>'
        for r in reviews)

    rs = ""
    for r in rests_raw:
        en_name = r[0].strip()
        name, menu = (ko[en_name][0], "·".join(ko[en_name][1])) if en_name in ko else (en_name, r[1])
        where = localize(r[2], ko)
        note = localize(r[3], ko)
        outside = "파크 밖" in en_name
        rs += (f'<div class="rest"><div class="avatar sm" style="background:var(--{"green" if outside else "purple"})">'
               f'<i class="bi {"bi-geo-alt-fill" if outside else "bi-cup-hot-fill"}"></i></div><div><div class="name">{inline(name)}</div>'
               f'<div class="info">추천: {inline(menu)}</div><div class="sub">{inline(where)} · {inline(note)}</div></div></div>')

    banner = "" if verdict == "PASS" else '<div class="warnbox"><b>검토 미통과</b> · 최대 반복 횟수에 도달해 Evaluator 기준을 모두 통과하지 못했어요. 내용을 직접 확인하세요.</div>'

    tpl = Path(__file__).with_name("dashboard_template.html").read_text(encoding="utf-8")
    page = (tpl.replace("{{BRIEF}}", inline(brief)).replace("{{KPI}}", kpi).replace("{{CHECKS}}", chk)
            .replace("{{TIMELINE}}", tl).replace("{{WAITS}}", wt).replace("{{WAIT_AT}}", html.escape(rec_at))
            .replace("{{REVIEWS}}", rv).replace("{{RESTS}}", rs).replace("{{REST_NOTE}}", inline(rest_note))
            .replace("{{BANNER}}", banner).replace("{{VERDICT}}", verdict).replace("{{ATTEMPT}}", attempt)
            .replace("{{N_CHECKS}}", str(len(checks))))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(page, encoding="utf-8")
    left = sorted(set(re.findall(r"\b(?:Cafe|Food|Village|Kuche|Snack|Restaurant|Zootopia|Adventure)\b", re.sub(r"<[^>]+>", " ", page))))
    print(f"wrote {out_path} (verdict={verdict}, attempt={attempt}, ko_map={len(ko)}, leftover_en={left})")


if __name__ == "__main__":
    main(*sys.argv[1:5])
