#!/usr/bin/env python3
"""Builds <workspace>/output/overview.html (short screening brief) from career.json "overview".

Usage: python3 build_overview.py <workspace>
"""
import html, json, math, re, sys
from collections import Counter
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
WS = Path(sys.argv[1] if len(sys.argv) > 1 else ".").expanduser().resolve()
CFG = json.loads((WS / "career.json").read_text())
OV = CFG["overview"]
esc = html.escape
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
prs_file = WS / "raw/github/authored_prs.jsonl"
prs = [json.loads(l) for l in open(prs_file) if l.strip()] if prs_file.exists() else []

SY, SM = int(CFG["start"][:4]), int(CFG["start"][5:7])


def mi(date):
    """'YYYY-MM[-DD]' -> months since the start month (fractional)."""
    y, m = int(date[:4]), int(date[5:7])
    d = int(date[8:10]) if len(date) >= 10 else 1
    return (y - SY) * 12 + (m - SM) + (d - 1) / 30


EY, EM = int(CFG["end"][:4]), int(CFG["end"][5:7])
TOTAL = mi(CFG["end"][:7]) + 1  # through the end of the end month
L, PW = 132, 800
x = lambda m: L + min(max(m, 0), TOTAL) * PW / TOTAL


def end_of(date):
    return TOTAL if date in ("now", "end") else mi(date)


def rich(text):
    out = esc(text, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)


def tip(label, detail):
    return esc(f"{label}|{detail or ''}", quote=True)


def timeline():
    lanes, milestones = OV.get("lanes", []), OV.get("milestones", [])
    W, g = L + PW + 24, []
    top, lane_h, bar_h, ms_y = 78, 44, 22, 56
    bottom = top + lane_h * len(lanes)
    for yr in range(SY + 1, EY + 1):
        xx = x(mi(f"{yr}-01"))
        g.append(f'<line class="ygrid" x1="{xx:.1f}" x2="{xx:.1f}" y1="{ms_y - 8}" y2="{bottom + 96}"/>')
    for ms in milestones:
        xx = x(mi(ms["date"]))
        ly = 18 if ms.get("row") else 34
        anchor = ms.get("anchor") or ("end" if xx > L + PW - 60 else ("start" if xx < L + 60 else "middle"))
        g.append(f'<g class="ms" tabindex="0" data-tip="{tip(ms["label"], ms.get("detail"))}">'
                 f'<line class="mstem" x1="{xx:.1f}" x2="{xx:.1f}" y1="{ly + 4}" y2="{bottom}"/>'
                 f'<rect class="hit" x="{xx - 10:.1f}" y="{ly - 14}" width="20" height="{ms_y + 10 - ly + 14}"/>'
                 f'<path class="dia" d="M{xx:.1f},{ms_y - 6} l6,6 l-6,6 l-6,-6 Z"/>'
                 f'<text class="mslabel" x="{xx:.1f}" y="{ly}" text-anchor="{anchor}">{esc(ms["label"])}</text></g>')
    for i, lane in enumerate(lanes):
        y0 = top + i * lane_h
        g.append(f'<text class="lane" x="0" y="{y0 + lane_h / 2 + 4:.1f}">{esc(lane["name"])}</text>')
        g.append(f'<line class="lgrid" x1="{L}" x2="{L + PW}" y1="{y0 + lane_h:.1f}" y2="{y0 + lane_h:.1f}"/>')
        for bar in lane["bars"]:
            label, kind = bar["label"], bar.get("kind", "work")
            xa, xb = x(mi(bar["from"])), x(end_of(bar["to"]))
            thin = kind == "oncall"
            h = 6 if thin else bar_h
            by = y0 + (lane_h - h) / 2
            g.append(f'<g class="seg {kind}" tabindex="0" data-tip="{tip(label, bar.get("detail"))}">'
                     f'<rect x="{xa + 1:.1f}" y="{by:.1f}" width="{max(4, xb - xa - 2):.1f}" height="{h}" rx="{min(4, h / 2)}"/>')
            if thin:
                g.append(f'<text class="seglabel out" x="{xa + 4:.1f}" y="{by - 5:.1f}">{esc(label)}</text></g>')
            elif (xb - xa) > len(label) * 6.4 + 12:
                g.append(f'<text class="seglabel" x="{xa + 8:.1f}" y="{by + 15:.1f}">{esc(label)}</text></g>')
            else:
                g.append(f'<text class="seglabel out" x="{(xa + xb) / 2:.1f}" y="{by - 4:.1f}" text-anchor="middle">{esc(label)}</text></g>')
    py, ph = bottom + 14, 48
    if prs:
        q = Counter()
        for p in prs:
            d = p.get("mergedAt") or p["createdAt"]
            q[(int(d[:4]), (int(d[5:7]) - 1) // 3)] += 1
        g.append(f'<text class="lane" x="0" y="{py + ph / 2 - 2:.1f}">PRs / quarter</text>'
                 f'<text class="lane sub" x="0" y="{py + ph / 2 + 13:.1f}">{len(prs)} total</text>')
        vmax = max(10, math.ceil(max(q.values()) / 10) * 10)
        for (y, qi), v in sorted(q.items()):
            q0 = mi(f"{y}-{qi * 3 + 1:02d}")
            m0, m1 = max(0, q0), min(TOTAL, q0 + 3)
            if m1 <= m0:
                continue
            xa, xb = x(m0) + 5, x(m1) - 5
            h = v / vmax * ph
            g.append(f'<g class="pr" tabindex="0" data-tip="{y} Q{qi + 1}|{v} PRs authored">'
                     f'<rect class="hit" x="{x(m0):.1f}" y="{py}" width="{x(m1) - x(m0):.1f}" height="{ph + 2}"/>'
                     f'<path d="M{xa:.1f},{py + ph} V{py + ph - h + 3:.1f} Q{xa:.1f},{py + ph - h:.1f} {xa + 3:.1f},{py + ph - h:.1f} '
                     f'H{xb - 3:.1f} Q{xb:.1f},{py + ph - h:.1f} {xb:.1f},{py + ph - h + 3:.1f} V{py + ph} Z"/>'
                     f'<text class="prv" x="{(xa + xb) / 2:.1f}" y="{py + ph - h - 4:.1f}" text-anchor="middle">{v}</text></g>')
        g.append(f'<line class="axis" x1="{L}" x2="{L + PW}" y1="{py + ph}" y2="{py + ph}"/>')
    else:
        ph = 0
    ay = py + ph + 20
    g.append(f'<text class="year" x="{x(0) + 4:.1f}" y="{ay}">{MONTHS[SM - 1]} {SY}</text>')
    for yr in range(SY + 1, EY + 1):
        m = mi(f"{yr}-01")
        if m >= 3 and TOTAL - m >= 3:
            g.append(f'<text class="year" x="{x(m) + 4:.1f}" y="{ay}">{yr}</text>')
    g.append(f'<text class="year" x="{L + PW:.1f}" y="{ay}" text-anchor="end">{MONTHS[EM - 1]} {EY}</text>')
    return (f'<svg viewBox="0 0 {W} {ay + 10}" role="img" aria-label="Career timeline from {MONTHS[SM - 1]} {SY} to '
            f'{MONTHS[EM - 1]} {EY}: roles, missions, milestones and pull requests per quarter">{"".join(g)}</svg>')


LEGEND = {"role": "Role", "promoted": "After promotion", "lead": "Leadership role",
          "work": "Mission / main project", "oncall": "On-call", "alt": "Other"}
LEGEND.update(OV.get("legend", {}))
kinds = []
for lane in OV.get("lanes", []):
    for bar in lane["bars"]:
        k = bar.get("kind", "work")
        if k not in kinds:
            kinds.append(k)
var = {"role": "--c-role", "promoted": "--c-mid", "lead": "--c-lead", "work": "--c-work", "oncall": "--c-oncall", "alt": "--c-alt"}
legend = "".join(f'<span><i style="background:var({var[k]})"></i>{esc(LEGEND[k])}</span>' for k in kinds if k in var)
if OV.get("milestones"):
    legend += '<span><i class="dia"></i>Milestone</span>'

wins = "".join(
    f'<article class="win"><div class="metric">{esc(w["metric"])}<small>{esc(w.get("small", ""))}</small></div>'
    f'<h3>{esc(w["title"])}</h3><p>{rich(w["text"])}</p><span class="when">{esc(w.get("when", ""))}</span></article>'
    for w in OV.get("wins", []))
quotes = "".join(
    f'<figure class="q{" big" if q.get("big") else ""}"><blockquote>“{esc(q["text"])}”</blockquote>'
    f'<figcaption><b>{esc(q["who"])}</b>{", " + esc(q["context"]) if q.get("context") else ""}</figcaption></figure>'
    for q in OV.get("quotes", []))
partial = f" The last quarter covers up to {MONTHS[EM - 1]} only." if EM % 3 else ""

FILL = {
    "TITLE": esc(f'{CFG["name"]} at a Glance'),
    "EYEBROW": esc(OV.get("eyebrow", CFG.get("eyebrow", ""))),
    "NAME": esc(CFG["name"]),
    "ROLE": rich(OV.get("role", "")),
    "PITCH": rich(OV.get("pitch", "")),
    "FACTS": "".join(f'<div class="fact"><span class="v">{esc(str(f["v"]))}</span><span class="l">{esc(f["l"])}</span></div>'
                     for f in OV.get("facts", [])),
    "TIMELINE": timeline(),
    "LEGEND": legend,
    "PARTIAL_NOTE": esc(partial),
    "WINS": wins,
    "QUOTES": quotes,
    "PROMO": f'<p class="promo">{rich(OV["promo"])}</p>' if OV.get("promo") else "",
    "STACK": "".join(f"<span>{esc(s)}</span>" for s in OV.get("stack", [])),
    "FOOTER": rich(OV.get("footer", "")),
}

page = (SKILL / "templates/overview_template.html").read_text()
for key, empty in (("wins", not wins), ("quotes", not quotes), ("stack", not OV.get("stack"))):
    if empty:
        page = re.sub(rf"<!--opt:{key}-->.*?<!--/opt:{key}-->", "", page, flags=re.S)
    page = page.replace(f"<!--opt:{key}-->", "").replace(f"<!--/opt:{key}-->", "")
for k, v in FILL.items():
    page = page.replace("{{" + k + "}}", str(v))
assert "{{" not in page, re.findall(r"\{\{\w+\}\}", page)
(WS / "output").mkdir(exist_ok=True)
(WS / "output/overview.html").write_text(page)
print(f"ok {WS / 'output/overview.html'}")
