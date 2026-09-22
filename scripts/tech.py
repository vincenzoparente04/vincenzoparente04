"""Generate the minimal header for README-tech (light + dark).

Run: python3 scripts/tech.py
"""

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "tech"

THEMES = {
    "light": {"fg": "#111111", "weak": "#6e7781", "faint": "#d0d7de"},
    "dark": {"fg": "#f0f6fc", "weak": "#8b949e", "faint": "#30363d"},
}

SANS = "Inter, -apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

LINES = [
    ("msc", "Computer Science & Engineering @ Politecnico di Milano"),
    ("focus", "AI track, applied ML, logic & math"),
    ("curious", "about everything"),
]

W, H = 1000, 268


def header(theme):
    c = THEMES[theme]
    rows = []
    for i, (key, value) in enumerate(LINES):
        y = 150 + i * 30
        rows.append(
            f'<text class="mono" x="4" y="{y}"><tspan class="weak">{key.ljust(10)}</tspan>'
            f'<tspan class="fg">{escape(value)}</tspan></text>'
        )
    last_y = 150 + (len(LINES) - 1) * 30
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">Vincenzo Parente</title>
  <desc id="desc">MSc Computer Science and Engineering at Politecnico di Milano. AI track, applied machine learning, logic and math. Curious about everything.</desc>
  <style>
    .sans {{ font-family: {SANS}; fill: {c['fg']}; }}
    .mono {{ font-family: {MONO}; font-size: 17px; white-space: pre; }}
    .fg {{ fill: {c['fg']}; }} .weak {{ fill: {c['weak']}; }}
    .cursor {{ fill: {c['fg']}; animation: blink 1.1s steps(1, end) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}
  </style>
  <text class="mono weak" x="4" y="30">$ whoami</text>
  <text class="sans" x="0" y="96" font-size="60" font-weight="700" letter-spacing="-2">Vincenzo Parente</text>
  <rect x="4" y="118" width="{W - 8}" height="1" fill="{c['faint']}"/>
  {chr(10).join('  ' + r for r in rows).strip()}
  <text class="mono weak" x="4" y="{last_y + 42}">$</text>
  <rect class="cursor" x="22" y="{last_y + 28}" width="10" height="18"/>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"header-{theme}.svg").write_text(header(theme), encoding="utf-8")
    print(f"wrote header to {OUT.relative_to(OUT.parent.parent)}")
