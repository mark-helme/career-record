#!/usr/bin/env python3
"""Builds <workspace>/output/achievements.html from career.json, notes/*.md and raw exports.

Usage: python3 build.py <workspace>
"""
import html, json, math, re, sys
from collections import Counter, OrderedDict
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
WS = Path(sys.argv[1] if len(sys.argv) > 1 else ".").expanduser().resolve()
N, R, OUT = WS / "notes", WS / "raw", WS / "output"
CFG = json.loads((WS / "career.json").read_text())
esc = html.escape
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

SRC_RE = re.compile(r"\s*\((?:src|source):[^()]*(?:\([^()]*\)[^()]*)*\)", re.I)
SRC_TAIL_RE = re.compile(r"\s*\(src:.*$", re.I)
REDACT = [(re.compile(p, re.I), r) for p, r in CFG.get("redact", [])]


def clean(text):
    text = SRC_RE.sub("", text)
    text = SRC_TAIL_RE.sub("", text)
    text = re.sub(r"\s*\[ASK [^\]]*\]", "", text)
    text = re.sub(r"^\d{10}\.\d+\s*\|\s*", "", text)  # Slack message timestamps
    for rx, rep in REDACT:
        text = rx.sub(rep, text)
    return text.rstrip()


def inline(text):
    text = clean(text)
    out = esc(text, quote=False)
    out = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^)]*\))*\)", r"\1", out)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", out)
    out = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", out)
    return out


def md(text, hshift=0):
    """Small markdown subset: headings, nested lists, tables, paragraphs."""
    lines = text.split("\n")
    out, i = [], 0
    stack = []  # (indent, tag)

    def close_lists(to=-1):
        while stack and stack[-1][0] > to:
            out.append(f"</li></{stack.pop()[1]}>")

    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s or s == "---":
            close_lists()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", s)
        if m:
            close_lists()
            lvl = min(6, len(m.group(1)) + hshift)
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue
        if s.startswith("|"):
            close_lists()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            body = [c for c in cells[1:] if not all(re.fullmatch(r":?-+:?", x) for x in c)]
            t = ['<div class="tablewrap"><table><thead><tr>']
            t += [f"<th>{inline(c)}</th>" for c in cells[0]]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", line)
        if m:
            ind = len(m.group(1))
            tag = "ol" if m.group(2)[0].isdigit() else "ul"
            if not stack or ind > stack[-1][0]:
                out.append(f"<{tag}><li>")
                stack.append((ind, tag))
            else:
                close_lists(ind)
                if stack and stack[-1][0] == ind:
                    out.append("</li><li>")
                else:
                    out.append(f"<{tag}><li>")
                    stack.append((ind, tag))
            out.append(inline(m.group(3)))
            i += 1
            continue
        if stack and line.startswith(" "):
            out.append(" " + inline(s))
            i += 1
            continue
        close_lists()
        para = [s]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\s*([-*]|\d+\.)\s|#|\|)", lines[i].strip()) and not lines[i].strip().startswith("**"):
            para.append(lines[i].strip())
            i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    close_lists()
    return "\n".join(out)


def sections(path, level=2):
    """Split a markdown file into OrderedDict{title: body} at the given heading level."""
    res = OrderedDict()
    if not Path(path).exists():
        return res
    parts = re.split(rf"^{'#' * level} (.+)$", Path(path).read_text(), flags=re.M)
    res["_intro"] = parts[0]
    for t, b in zip(parts[1::2], parts[2::2]):
        res[t.strip()] = b
    return res


def find(secs, word):
    return next((v for k, v in secs.items() if word.lower() in k.lower()), "")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48]


def jsonl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if p.exists() else []


def repo_name(r):
    r = r["nameWithOwner"] if isinstance(r, dict) else str(r)
    return r.split("/")[-1]


# ---------- data ----------
prs = jsonl(R / "github/authored_prs.jsonl")
reviewed = jsonl(R / "github/reviewed_prs.jsonl")
jira = OrderedDict()
for f in ("assigned", "reported"):
    for j in jsonl(R / f"jira/{f}.jsonl"):
        jira.setdefault(j["key"], j)
conf_tsv = N / "confluence-authored.tsv"
conf = [l.rstrip("\n").split("\t") for l in open(conf_tsv) if l.strip()] if conf_tsv.exists() else []

sy, sm = int(CFG["start"][:4]), int(CFG["start"][5:7])
ey, em = int(CFG["end"][:4]), int(CFG["end"][5:7])
QUARTERS = []
y, q = sy, (sm - 1) // 3
while (y, q) <= (ey, (em - 1) // 3):
    QUARTERS.append(f"{y}-Q{q + 1}")
    y, q = (y + 1, 0) if q == 3 else (y, q + 1)
last_partial = em % 3 != 0
partial_note = f" {QUARTERS[-1]} covers up to {MONTHS[em - 1]} only." if last_partial else ""


def quarter(pr):
    d = pr.get("mergedAt") or pr["createdAt"]
    return f"{d[:4]}-Q{(int(d[5:7]) - 1) // 3 + 1}"


qcount = Counter(quarter(p) for p in prs)
merged = sum(1 for p in prs if p["state"] == "MERGED")
repos = Counter(repo_name(p["repository"]) for p in prs)
review_authors = {(r.get("author") or {}).get("login", "") for r in reviewed}
humans = {a for a in review_authors if a and "bot" not in a.lower()}


def chart_svg():
    vals = [qcount[q] for q in QUARTERS]
    W, H, L, B, T = 760, 300, 40, 64, 24
    pw, ph = W - L - 12, H - B - T
    step = max(5, math.ceil(max(vals) / 4 / 5) * 5)
    ymax = step * math.ceil(max(vals) / step)
    bw = pw / len(vals)
    y = lambda v: T + ph - v / ymax * ph
    g = []
    for t in range(0, ymax + 1, step):
        g.append(f'<line class="grid" x1="{L}" x2="{W - 12}" y1="{y(t):.1f}" y2="{y(t):.1f}"/>'
                 f'<text class="tick" x="{L - 8}" y="{y(t) + 4:.1f}" text-anchor="end">{t}</text>')
    for band in CFG.get("chart_bands", []):
        if band["from"] not in QUARTERS or band["to"] not in QUARTERS:
            continue
        a, b = QUARTERS.index(band["from"]), QUARTERS.index(band["to"])
        x0, x1 = L + a * bw + 2, L + (b + 1) * bw - 2
        g.append(f'<rect class="band" x="{x0:.1f}" y="{T}" width="{x1 - x0:.1f}" height="{ph}" rx="4"/>'
                 f'<text class="bandlabel" x="{(x0 + x1) / 2:.1f}" y="{T - 8}" text-anchor="middle">{esc(band["label"])}</text>')
    hi = {0, len(vals) - 1, vals.index(max(vals))}
    for k, (q, v) in enumerate(zip(QUARTERS, vals)):
        x = L + k * bw + bw * 0.2
        w = bw * 0.6
        top = y(v)
        h = T + ph - top
        r = min(4, h)
        d = (f"M{x:.1f},{T + ph:.1f} V{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} "
             f"H{x + w - r:.1f} Q{x + w:.1f},{top:.1f} {x + w:.1f},{top + r:.1f} V{T + ph:.1f} Z")
        partial = " (partial)" if last_partial and k == len(vals) - 1 else ""
        g.append(f'<g class="bar" tabindex="0"><title>{q}{partial}: {v} PRs</title>'
                 f'<rect class="hit" x="{L + k * bw:.1f}" y="{T}" width="{bw:.1f}" height="{ph}"/>'
                 f'<path d="{d}"/>'
                 f'<text class="val{"" if k in hi else " soft"}" x="{x + w / 2:.1f}" y="{top - 6:.1f}" text-anchor="middle">{v}</text></g>')
        yy, qq = q.split("-")
        g.append(f'<text class="tick" x="{x + w / 2:.1f}" y="{T + ph + 18}" text-anchor="middle">{qq}</text>')
        if qq == "Q1" or k == 0:
            g.append(f'<text class="tick year" x="{x + w / 2:.1f}" y="{T + ph + 36}" text-anchor="middle">{yy}</text>')
    g.append(f'<line class="axis" x1="{L}" x2="{W - 12}" y1="{T + ph}" y2="{T + ph}"/>')
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Authored pull requests per quarter, '
            f'{QUARTERS[0]} to {QUARTERS[-1]}, {len(prs)} in total">{"".join(g)}</svg>')


# ---------- notes ----------
cv = sections(N / "cv-and-stories.md")
bullets_md = find(cv, "CV bullets")
bullets_md = bullets_md[re.search(r"^\s*(\d+\.|[-*])\s", bullets_md, re.M).start():] if re.search(r"^\s*(\d+\.|[-*])\s", bullets_md, re.M) else ""
star = sections(N / "cv-and-stories.md", 3)
star_items = [(k, v.split("\n---")[0]) for k, v in star.items() if re.match(r"\d+\.", k)]

cards = sections(N / "project-cards.md")
cards.pop("_intro", None)

psr = sections(N / "people-skills-recognition.md")
skills = find(psr, "Skills")
leader = find(psr, "Leadership")
recog = find(psr, "Recognition")
growth = find(psr, "Growth")

tl = sections(N / "timeline.md")
tl.pop("_intro", None)
arc = tl.pop("Career arc", "")


def card_html(title, body):
    m = re.match(r"(.*?)\s*\(([^()]*\d{4}[^()]*)\)\s*$", title)
    name, when = (m.group(1), m.group(2)) if m else (title, "")
    parts = re.split(r"^\*\*([^*]+):\*\*\s*", body.strip(), flags=re.M)
    rows = [f'<div class="lead">{md(parts[0])}</div>'] if parts[0].strip() else []
    for label, content in zip(parts[1::2], parts[2::2]):
        rows.append(f'<div class="field f-{slug(label)}"><h4>{esc(label)}</h4>{md(content)}</div>')
    return (f'<article class="card" id="p-{slug(name)}"><header><h3>{inline(name)}</h3>'
            f'<span class="when">{esc(clean(when))}</span></header>{"".join(rows)}</article>')


def star_html(title, body):
    t = re.sub(r"^\d+\.\s*", "", title)
    m = re.match(r"(.*?)\s*\(([^)]*)\)\s*$", t)
    name, tags = (m.group(1), m.group(2)) if m else (t, "")
    return (f'<article class="story"><header><h3>{inline(name)}</h3>'
            f'<p class="tags">{esc(tags)}</p></header>{md(body)}</article>')


def tl_html(title, body):
    m = re.match(r"(\d{4}-Q\d)\s*\(([^)]*)\):\s*(.*)", title)
    q, months, cnt = m.groups() if m else (title, "", "")
    meta = " · ".join(x for x in (clean(months), cnt) if x)
    return (f'<li class="q"><div class="qhead"><span class="qname">{esc(q)}</span>'
            f'<span class="qmeta">{esc(meta)}</span></div><div class="qbody">{md(body)}</div></li>')


def toc_item(title):
    name = re.sub(r"\s*\([^()]*\d{4}[^()]*\)\s*$", "", title)
    return f'<li><a href="#p-{slug(name)}">{inline(name)}</a></li>'


# ---------- body sections (empty ones are dropped) ----------
SECTIONS = [
    ("bullets", "CV bullets", f'<div class="bullets">{md(bullets_md)}</div>' if bullets_md.strip() else ""),
    ("stories", "Interview stories (STAR)", "\n".join(star_html(k, v) for k, v in star_items)),
    ("timeline", "Career timeline", (f'<div class="arc prose">{md(arc)}</div>' if arc.strip() else "")
     + (f'<ol class="quarters">{"".join(tl_html(k, v) for k, v in tl.items())}</ol>' if tl else "")),
    ("projects", "Key projects", (f'<ol class="cardtoc">{"".join(toc_item(k) for k in cards)}</ol>'
                                  + "\n".join(card_html(k, v) for k, v in cards.items())) if cards else ""),
    ("skills", "Skills &amp; technology", f'<div class="prose">{md(skills, 1)}</div>' if skills.strip() else ""),
    ("leadership", "Leadership &amp; collaboration", f'<div class="prose">{md(leader, 1)}</div>' if leader.strip() else ""),
    ("recognition", "Recognition &amp; feedback", f'<div class="prose">{md(recog, 1)}</div>' if recog.strip() else ""),
    ("growth", "Growth &amp; learning", f'<div class="prose">{md(growth, 1)}</div>' if growth.strip() else ""),
]
SECTIONS = [s for s in SECTIONS if s[2]]


def appendix():
    out, n = [], 0

    def block(title, count, head, rows):
        nonlocal n
        n += 1
        th = "".join(f"<th>{h}</th>" for h in head)
        out.append(f'<details open><summary>A{n} · {title}<span class="c">{count}</span></summary>'
                   f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div></details>')

    if prs:
        rows = "".join(
            f'<tr><td class="num">{(p.get("mergedAt") or p["createdAt"])[:10]}</td><td>{esc(repo_name(p["repository"]))}#{p["number"]}</td>'
            f'<td>{esc(clean(p["title"]))}</td><td><span class="st st-{p["state"].lower()}">{p["state"].lower()}</span></td></tr>'
            for p in sorted(prs, key=lambda p: p["createdAt"]))
        block("Authored pull requests", f"{len(prs)} · {merged} merged", ["Date", "Repo / PR", "Title", "State"], rows)
    if jira:
        rows = "".join(
            f'<tr><td class="num">{(j.get("created") or "")[:10]}</td><td>{esc(k)}</td><td>{esc(j.get("issuetype", ""))}</td>'
            f'<td>{esc(clean(j.get("summary", "")))}</td><td>{esc(j.get("status", ""))}</td></tr>'
            for k, j in sorted(jira.items(), key=lambda kv: kv[1].get("created", "")))
        block("Jira issues", f"{len(jira)} assigned or reported", ["Created", "Key", "Type", "Summary", "Status"], rows)
    if conf:
        rows = "".join(f'<tr><td class="num">{esc(c[0])}</td><td>{esc(c[1])}</td><td>{esc(clean(c[2]))}</td></tr>' for c in conf)
        block("Confluence pages", f"{len(conf)} authored or co-authored", ["Date", "Space", "Title"], rows)
    if prs:
        n += 1
        a = "".join(f"<tr><td>{esc(k)}</td><td class='num'>{v}</td></tr>" for k, v in repos.most_common())
        rv = "".join(f"<tr><td>{esc(k)}</td><td class='num'>{v}</td></tr>"
                     for k, v in Counter(repo_name(r["repository"]) for r in reviewed).most_common())
        out.append(f'<details open><summary>A{n} · Repositories<span class="c">authored and reviewed PRs</span></summary><div class="two">'
                   f'<div class="tablewrap"><table><thead><tr><th>Authored in</th><th>PRs</th></tr></thead><tbody>{a}</tbody></table></div>'
                   f'<div class="tablewrap"><table><thead><tr><th>Reviewed in</th><th>PRs</th></tr></thead><tbody>{rv}</tbody></table></div></div></details>')
    return "\n".join(out)


def tile(t):
    small = f'<small> {esc(t["small"])}</small>' if t.get("small") else ""
    return f'<div class="tile"><div class="v">{esc(str(t["v"]))}{small}</div><div class="l">{inline(t["l"])}</div></div>'


auto_tiles = []
if prs:
    auto_tiles += [{"v": len(prs), "l": f"PRs authored, {merged} merged"}, {"v": len(repos), "l": "repositories contributed to"}]
if reviewed:
    auto_tiles.append({"v": len(reviewed), "l": f"PRs reviewed, for {len(humans)} colleagues"})
if jira:
    auto_tiles.append({"v": len(jira), "l": "Jira issues assigned or reported"})
if conf:
    auto_tiles.append({"v": len(conf), "l": "Confluence pages authored"})
number_tiles = auto_tiles + CFG.get("number_tiles", [])

toc = [("summary", "01", "Summary")] + [(sid, f"{i + 2:02d}", title) for i, (sid, title, _) in enumerate(SECTIONS)]
appx = appendix()
if appx:
    toc.append(("appendix", "A", "Appendix"))
body_sections = "\n".join(
    f'<section class="s brk" id="{sid}"><div class="shead"><span class="n">{i + 2:02d}</span><h2>{title}</h2></div>{content}</section>'
    for i, (sid, title, content) in enumerate(SECTIONS))

FILL = {
    "TITLE": esc(f'{CFG["name"]} Engineering Record'),
    "EYEBROW": esc(CFG.get("eyebrow", "Engineering record")),
    "NAME": esc(CFG["name"]),
    "SUBTITLE": inline(CFG.get("subtitle", "")),
    "META": inline(CFG.get("meta", "")),
    "TOC": "".join(f'<a href="#{a}"><span class="n">{n}</span>{t.split(" (")[0]}</a>' for a, n, t in toc),
    "LEDE": "".join(f'<p class="lede">{inline(p)}</p>' for p in CFG.get("summary", [])),
    "IMPACT_TILES": "".join(tile(t) for t in CFG.get("impact_tiles", [])),
    "NUMBER_TILES": "".join(tile(t) for t in number_tiles),
    "NUMBERS_NOTE": f'<p class="note">{inline(CFG["numbers_note"])}</p>' if CFG.get("numbers_note") else "",
    "CHART": chart_svg() if prs else "",
    "PARTIAL_NOTE": esc(partial_note),
    "SECTIONS": body_sections,
    "APPENDIX": appx,
    "FOOTER": inline(CFG.get("footer", "")),
}


def drop_empty(page, key, empty):
    if empty:
        return re.sub(rf"<!--opt:{key}-->.*?<!--/opt:{key}-->", "", page, flags=re.S)
    return page.replace(f"<!--opt:{key}-->", "").replace(f"<!--/opt:{key}-->", "")


page = (SKILL / "templates/template.html").read_text()
page = drop_empty(page, "impact", not CFG.get("impact_tiles"))
page = drop_empty(page, "chart", not prs)
page = drop_empty(page, "appendix", not appx)
for k, v in FILL.items():
    page = page.replace("{{" + k + "}}", str(v))
assert "{{" not in page, re.findall(r"\{\{\w+\}\}", page)
OUT.mkdir(exist_ok=True)
(OUT / "achievements.html").write_text(page)
print(f"ok {OUT / 'achievements.html'}: {len(page)} bytes; prs {len(prs)} ({merged} merged), reviewed {len(reviewed)}, jira {len(jira)}, confluence {len(conf)}")
