"""Generate GitHub stats cards (light + dark) for the chess and tech READMEs.

Data comes from the public contribution calendar and the REST API, so it runs
both locally and in GitHub Actions. Set GITHUB_TOKEN to avoid rate limits.

Outputs in assets/chess/:
  stats-*.svg     player card: totals, streaks, top languages
  heatmap-*.svg   the contribution calendar as a pixel grid
  weekdays-*.svg  contributions per weekday
and in assets/tech/:
  stats-*.svg     the same numbers as terminal output, plus a weekly sparkline

Run: python3 scripts/stats.py [username]
"""

import datetime as dt
from html import escape
import json
import os
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from pixel import text, text_width

OUT = Path(__file__).resolve().parent.parent / "assets" / "chess"
TECH = OUT.parent / "tech"
USER = sys.argv[1] if len(sys.argv) > 1 else "vincenzoparente04"

THEMES = {
    "light": {"fg": "#111111", "weak": "#6e7781", "faint": "#d0d7de",
              "levels": ["#eaeef2", "#c4c9cf", "#8c959f", "#57606a", "#111111"]},
    "dark": {"fg": "#f0f6fc", "weak": "#8b949e", "faint": "#30363d",
             "levels": ["#161b22", "#30363d", "#6e7681", "#b1bac4", "#f0f6fc"]},
}
# notebooks are mostly output cells, so their byte counts would drown everything else
IGNORED_LANGUAGES = {"Jupyter Notebook", "HTML", "CSS", "SCSS"}


def get(url, accept="application/vnd.github+json"):
    headers = {"Accept": accept, "User-Agent": "profile-stats"}
    if os.environ.get("GITHUB_TOKEN") and "api.github.com" in url:
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        return r.read().decode()


def contributions():
    """[(date, count, level)] for the last year, oldest first."""
    html = get(f"https://github.com/users/{USER}/contributions", "text/html")
    cells = {m[0]: (m[1], int(m[2])) for m in re.findall(
        r'data-date="([\d-]+)" id="([^"]+)" data-level="(\d)"', html)}
    counts = {}
    for cell_id, label in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]+)', html):
        m = re.match(r"(\d+) contribution", label)
        counts[cell_id] = int(m[1]) if m else 0
    days = [(dt.date.fromisoformat(d), counts.get(cid, 0), lvl) for d, (cid, lvl) in cells.items()]
    return sorted(days)


def languages():
    repos = json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner"))
    total = Counter()
    for repo in repos:
        if repo["fork"]:
            continue
        for lang, size in json.loads(get(repo["languages_url"])).items():
            if lang not in IGNORED_LANGUAGES:
                total[lang] += size
    s = sum(total.values()) or 1
    return [(lang, size / s) for lang, size in total.most_common(4)], len(repos)


def streaks(days):
    longest = run = 0
    for _, n, _ in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    current = 0
    tail = days[:-1] if days and days[-1][1] == 0 else days  # today may still be empty
    for _, n, _ in reversed(tail):
        if not n:
            break
        current += 1
    return current, longest


def frame(w, h, c):
    return f'<rect x="2" y="2" width="{w - 4}" height="{h - 4}" fill="none" stroke="{c["fg"]}" stroke-width="4"/>'


def svg_open(w, h, label, extra_css=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            f'role="img" aria-label="{label}">\n<style>path, rect {{ shape-rendering: crispEdges; }}{extra_css}'
            f' @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}</style>\n')


def right_text(s, px, right, y, cls):
    return text(s, px, right - text_width(s, px), y, cls)


def days_label(n):
    return f"{n} DAY" if n == 1 else f"{n} DAYS"


def stats_card(theme, data):
    c = THEMES[theme]
    W, H = 1000, 290
    rows = [
        ("CONTRIBUTIONS", f"{data['total']}"),
        ("CURRENT STREAK", days_label(data["current"])),
        ("LONGEST STREAK", days_label(data["longest"])),
        ("BEST DAY", f"{data['best']}"),
        ("PUBLIC REPOS", f"{data['repos']}"),
    ]
    css = (f" .fg {{ fill: {c['fg']}; }} .weak {{ fill: {c['weak']}; }}"
           " @keyframes grow { from { transform: scaleX(0); } }"
           " .bar { transform-box: fill-box; animation: grow 1.2s steps(20) backwards; }")
    out = [svg_open(W, H, f"GitHub stats: {data['total']} contributions in the last year", css), frame(W, H, c)]
    out.append(text("PLAYER STATS", 3, 36, 36, "fg"))
    out.append(f'<rect x="36" y="70" width="424" height="4" fill="{c["faint"]}"/>')
    for i, (k, v) in enumerate(rows):
        y = 96 + i * 36
        out.append(text(k, 3, 36, y, "weak"))
        out.append(right_text(v, 3, 460, y, "fg"))

    out.append(text("TOP LANGUAGES", 3, 540, 36, "fg"))
    out.append(f'<rect x="540" y="70" width="424" height="4" fill="{c["faint"]}"/>')
    blocks, bw, gap = 20, 14, 4
    for i, (lang, share) in enumerate(data["langs"]):
        y = 90 + i * 46
        out.append(text(lang.upper(), 3, 540, y, "weak"))
        out.append(right_text(f"{round(share * 100)}%", 3, 964, y, "fg"))
        filled = max(1, round(share * blocks))
        empty = "".join(f"M{540 + b * (bw + gap)} {y + 29}h{bw}v8h{-bw}z" for b in range(blocks))
        full = "".join(f"M{540 + b * (bw + gap)} {y + 29}h{bw}v8h{-bw}z" for b in range(filled))
        out.append(f'<path fill="{c["faint"]}" d="{empty}"/>')
        out.append(f'<path class="bar" style="animation-delay: {0.2 * i:.1f}s" fill="{c["fg"]}" d="{full}"/>')
    out.append("</svg>\n")
    return "\n".join(out)


def heatmap(theme, data):
    c = THEMES[theme]
    days = data["days"]
    cell, gap = 14, 3
    first = days[0][0]
    offset = (first.weekday() + 1) % 7  # GitHub weeks start on Sunday
    weeks = (len(days) + offset + 6) // 7
    W = 1000
    H = 84 + 7 * (cell + gap) - gap + 36
    left = (W - (weeks * (cell + gap) - gap)) // 2
    css = (f" .fg {{ fill: {c['fg']}; }}"
           " @keyframes pop { from { opacity: 0; } }"
           " .wk { animation: pop .1s steps(1) backwards; }")
    out = [svg_open(W, H, f"{data['total']} contributions in the last year", css), frame(W, H, c)]
    title = f"{data['total']} CONTRIBUTIONS IN THE LAST YEAR"
    out.append(text(title, 3, left, 36, "fg"))
    by_week = {}
    for i, (_, _, lvl) in enumerate(days):
        w, d = divmod(i + offset, 7)
        by_week.setdefault(w, []).append((d, lvl))
    for w, cells in sorted(by_week.items()):
        rects = "".join(
            f'<rect x="{left + w * (cell + gap)}" y="{84 + d * (cell + gap)}" width="{cell}" height="{cell}" fill="{c["levels"][lvl]}"/>'
            for d, lvl in cells
        )
        out.append(f'<g class="wk" style="animation-delay: {w * 0.03:.2f}s">{rects}</g>')
    out.append("</svg>\n")
    return "\n".join(out)


def weekdays(theme, data):
    c = THEMES[theme]
    names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    per_day = Counter()
    for d, n, _ in data["days"]:
        per_day[d.weekday()] += n
    top = max(per_day.values()) or 1
    fav = names[max(range(7), key=lambda i: per_day[i])]
    W, H = 1000, 290
    css = (f" .fg {{ fill: {c['fg']}; }} .weak {{ fill: {c['weak']}; }}"
           " @keyframes rise { from { transform: scaleY(0); } }"
           " .col { transform-box: fill-box; transform-origin: bottom; animation: rise .8s steps(10) backwards; }")
    out = [svg_open(W, H, f"Contributions per weekday, most active on {fav}", css), frame(W, H, c)]
    out.append(text("CONTRIBUTIONS BY WEEKDAY", 3, 36, 36, "fg"))
    out.append(right_text(f"MOST ACTIVE: {fav}", 3, W - 36, 36, "weak"))
    block, gap, max_blocks = 12, 4, 10
    colw = 96
    for i, name in enumerate(names):
        x = 36 + 40 + i * (colw + 32)
        n_blocks = round(per_day[i] / top * max_blocks)
        d = "".join(f"M{x} {228 - (b + 1) * (block + gap) + gap}h{colw}v{block}h{-colw}z" for b in range(n_blocks))
        out.append(f'<path class="col" style="animation-delay: {0.08 * i:.2f}s" fill="{c["fg"] if name == fav else c["weak"]}" d="{d or "M0 0"}"/>')
        out.append(text(name, 3, x + (colw - text_width(name, 3)) / 2, 244, "fg" if name == fav else "weak"))
    out.append("</svg>\n")
    return "\n".join(out)


MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def tech_card(theme, data):
    """Same data as the pixel card, drawn as quiet terminal output with a weekly sparkline."""
    c = THEMES[theme]
    W, H = 1000, 350
    per_day = Counter()
    for d, n, _ in data["days"]:
        per_day[d.weekday()] += n
    fav = WEEKDAYS[max(range(7), key=lambda i: per_day[i])]
    rows = [
        ("contributions", str(data["total"])),
        ("current streak", days_label(data["current"]).lower()),
        ("longest streak", days_label(data["longest"]).lower()),
        ("best day", str(data["best"])),
        ("most active", fav),
    ]
    out = [f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="GitHub stats: {data['total']} contributions in the last year">
<style>
  text {{ font-family: {MONO}; font-size: 16px; white-space: pre; }}
  .fg {{ fill: {c['fg']}; }} .weak {{ fill: {c['weak']}; }}
  .spark {{ fill: none; stroke: {c['fg']}; stroke-width: 1.5; stroke-linejoin: round; }}
  @keyframes draw {{ from {{ stroke-dashoffset: 2000; }} }}
  .spark {{ stroke-dasharray: 2000; stroke-dashoffset: 0; animation: draw 2.4s ease-out backwards; }}
  @keyframes grow {{ from {{ transform: scaleX(0); }} }}
  .bar {{ transform-box: fill-box; animation: grow 1s ease-out backwards; }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{c['faint']}"/>
<text x="32" y="44" class="weak">$ git stats --last 12 months</text>"""]
    for i, (k, v) in enumerate(rows):
        y = 92 + i * 30
        out.append(f'<text x="32" y="{y}" class="weak">{k}</text><text x="440" y="{y}" class="fg" text-anchor="end">{v}</text>')
    for i, (lang, share) in enumerate(data["langs"]):
        y = 92 + i * 36
        out.append(f'<text x="540" y="{y}" class="weak">{escape(lang.lower())}</text>'
                   f'<text x="968" y="{y}" class="fg" text-anchor="end">{round(share * 100)}%</text>')
        out.append(f'<rect x="540" y="{y + 10}" width="428" height="2" fill="{c["faint"]}"/>')
        out.append(f'<rect class="bar" style="animation-delay: {0.15 * i:.2f}s" x="540" y="{y + 10}" '
                   f'width="{max(2, round(428 * share))}" height="2" fill="{c["fg"]}"/>')

    days = data["days"]
    weeks = [sum(n for _, n, _ in days[i:i + 7]) for i in range(0, len(days), 7)]
    top = max(weeks) or 1
    x0, x1, y0, y1 = 32, 968, 318, 266
    step = (x1 - x0) / max(1, len(weeks) - 1)
    pts = " ".join(f"{x0 + i * step:.1f},{y0 - (y0 - y1) * n / top:.1f}" for i, n in enumerate(weeks))
    out.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="1" fill="{c["faint"]}"/>')
    out.append(f'<polyline class="spark" points="{pts}"/>')
    out.append(f'<text x="{x0}" y="{y1 - 14}" class="weak">contributions per week</text>')
    out.append("</svg>\n")
    return "\n".join(out)


if __name__ == "__main__":
    days = contributions()
    langs, repos = languages()
    current, longest = streaks(days)
    data = {"days": days, "total": sum(n for _, n, _ in days), "best": max(n for _, n, _ in days),
            "current": current, "longest": longest, "langs": langs, "repos": repos}
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"stats-{theme}.svg").write_text(stats_card(theme, data), encoding="utf-8")
        (OUT / f"heatmap-{theme}.svg").write_text(heatmap(theme, data), encoding="utf-8")
        (OUT / f"weekdays-{theme}.svg").write_text(weekdays(theme, data), encoding="utf-8")
        TECH.mkdir(parents=True, exist_ok=True)
        (TECH / f"stats-{theme}.svg").write_text(tech_card(theme, data), encoding="utf-8")
    print(f"{data['total']} contributions, streak {current}/{longest}, langs {[l for l, _ in langs]}")
