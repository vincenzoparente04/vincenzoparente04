"""Generate the animated hero banner (light + dark) for the profile README.

The animation loops through three states of the same 11 points:
  01 signal    - samples on a wave
  02 structure - nodes of a graph
  03 logic     - a truth assignment satisfying a formula

Run: python3 scripts/hero.py
"""

import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

THEMES = {
    "light": {"fg": "#111111", "weak": "#6e7781", "faint": "#d0d7de"},
    "dark": {"fg": "#f0f6fc", "weak": "#8b949e", "faint": "#30363d"},
}

W, H = 1200, 400
DURATION = 14  # seconds per loop
N = 11

SANS = "Inter, -apple-system, 'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

# --- the three layouts of the same points ------------------------------------

def wave_y(x):
    return 200 + 58 * math.sin((x - 660) / 46 * 0.9)

WAVE = [(660 + i * 46, wave_y(660 + i * 46)) for i in range(N)]

GRAPH = [
    (690, 140), (745, 255), (815, 105), (865, 205), (905, 305), (950, 130),
    (1000, 235), (1055, 110), (1075, 300), (1115, 195), (790, 320),
]
EDGES = [
    (0, 1), (0, 2), (1, 3), (2, 3), (2, 5), (3, 5), (3, 6), (1, 10), (10, 4),
    (3, 4), (4, 6), (5, 7), (6, 9), (7, 9), (6, 8), (8, 9),
]

ROW = [(700 + i * 40, 150) for i in range(N)]
ASSIGNMENT = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0]  # hollow = false

# keyframe percentages
MOVE_TO_GRAPH = (28, 38)
MOVE_TO_ROW = (60, 70)
MOVE_TO_WAVE = (92, 100)


def translate(p):
    return f"transform: translate({p[0]:.1f}px, {p[1]:.1f}px);"


def node_keyframes(i):
    w, g, r = WAVE[i], GRAPH[i], ROW[i]
    # small per-node delay so points travel as a ripple, not in lockstep
    d = i * 0.4
    fill = "" if ASSIGNMENT[i] else "fill-opacity: 1;"
    hollow = "" if ASSIGNMENT[i] else "fill-opacity: 0;"
    return f"""
    @keyframes n{i} {{
      0%, {MOVE_TO_GRAPH[0] + d:.1f}% {{ {translate(w)} {fill} }}
      {MOVE_TO_GRAPH[1] + d:.1f}%, {MOVE_TO_ROW[0] + d:.1f}% {{ {translate(g)} {fill} }}
      {MOVE_TO_ROW[1] + d * 0.5:.1f}% {{ {translate(r)} {hollow} }}
      {MOVE_TO_WAVE[0] - 2:.1f}% {{ {translate(r)} {hollow} }}
      {MOVE_TO_WAVE[0]:.1f}% {{ {translate(r)} {fill} }}
      100% {{ {translate(w)} }}
    }}
    .n{i} {{ animation: n{i} {DURATION}s cubic-bezier(.65,0,.35,1) infinite; {translate(w)} }}"""


def wave_path():
    pts = [(x, wave_y(x)) for x in range(646, 1135, 4)]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def svg(theme):
    c = THEMES[theme]
    wave_len = 620  # approx path length, used for the draw-on effect

    edges = "\n    ".join(
        f'<line x1="{GRAPH[a][0]}" y1="{GRAPH[a][1]}" x2="{GRAPH[b][0]}" y2="{GRAPH[b][1]}"/>'
        for a, b in EDGES
    )
    nodes = "\n    ".join(f'<circle class="n{i}" r="6"/>' for i in range(N))
    grid = "\n    ".join(
        f'<circle cx="{x}" cy="{y}" r="1"/>'
        for x in range(660, 1141, 40)
        for y in range(80, 341, 40)
    )
    keyframes = "".join(node_keyframes(i) for i in range(N))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">Vincenzo Parente</title>
  <desc id="desc">MSc Computer Science and Engineering at Politecnico di Milano. An animation turns a signal into a graph and then into a satisfied logic formula.</desc>
  <style>
    .sans {{ font-family: {SANS}; fill: {c['fg']}; }}
    .mono {{ font-family: {MONO}; fill: {c['weak']}; }}
    .expr {{ font-family: {MONO}; fill: {c['fg']}; }}

    .wave {{ fill: none; stroke: {c['weak']}; stroke-width: 1.5; stroke-dasharray: {wave_len}; animation: wave {DURATION}s linear infinite; }}
    @keyframes wave {{
      0%, 28% {{ stroke-dashoffset: 0; opacity: 1; }}
      34% {{ stroke-dashoffset: 0; opacity: 0; }}
      35%, 91% {{ stroke-dashoffset: {wave_len}; opacity: 0; }}
      92% {{ stroke-dashoffset: {wave_len}; opacity: 1; }}
      100% {{ stroke-dashoffset: 0; opacity: 1; }}
    }}

    .edges line {{ stroke: {c['weak']}; stroke-width: 1.2; }}
    .edges {{ opacity: 0; animation: edges {DURATION}s ease-in-out infinite; }}
    @keyframes edges {{ 0%, 40% {{ opacity: 0; }} 46%, 58% {{ opacity: 1; }} 62%, 100% {{ opacity: 0; }} }}

    .nodes circle {{ fill: {c['fg']}; stroke: {c['fg']}; stroke-width: 1.5; }}
    {keyframes}

    .formula {{ opacity: 0; animation: formula {DURATION}s ease-in-out infinite; }}
    @keyframes formula {{ 0%, 72% {{ opacity: 0; }} 77%, 88% {{ opacity: 1; }} 91%, 100% {{ opacity: 0; }} }}

    .label {{ opacity: 0; animation: {DURATION}s ease-in-out infinite; }}
    .l1 {{ opacity: 1; animation-name: l1; }} .l2 {{ animation-name: l2; }} .l3 {{ animation-name: l3; }}
    @keyframes l1 {{ 0%, 28% {{ opacity: 1; }} 32%, 94% {{ opacity: 0; }} 98%, 100% {{ opacity: 1; }} }}
    @keyframes l2 {{ 0%, 34% {{ opacity: 0; }} 40%, 60% {{ opacity: 1; }} 64%, 100% {{ opacity: 0; }} }}
    @keyframes l3 {{ 0%, 66% {{ opacity: 0; }} 72%, 90% {{ opacity: 1; }} 94%, 100% {{ opacity: 0; }} }}

    @media (prefers-reduced-motion: reduce) {{
      *, .l1, .l2, .l3 {{ animation: none !important; }}
    }}
  </style>

  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="20" fill="none" stroke="{c['faint']}"/>

  <text class="mono" x="64" y="118" font-size="14" letter-spacing="3">POLITECNICO DI MILANO · MSC CSE</text>
  <text class="sans" x="60" y="210" font-size="84" font-weight="700" letter-spacing="-3">Vincenzo</text>
  <text class="sans" x="60" y="292" font-size="84" font-weight="700" letter-spacing="-3">Parente</text>
  <text class="mono" x="64" y="342" font-size="16">applied AI · logic · curiosity</text>

  <g fill="{c['faint']}">
    {grid}
  </g>

  <path class="wave" d="{wave_path()}"/>
  <g class="edges">
    {edges}
  </g>
  <g class="nodes">
    {nodes}
  </g>

  <g class="formula" text-anchor="middle">
    <text class="expr" x="900" y="232" font-size="20">(x₁ ∨ ¬x₂) ∧ (x₃ ∨ x₅) ∧ ¬x₁₁</text>
    <text class="mono" x="900" y="272" font-size="14" letter-spacing="2">→ SAT</text>
  </g>

  <g class="mono" font-size="13" letter-spacing="1">
    <text class="label l1" x="660" y="368">01 — signal</text>
    <text class="label l2" x="660" y="368">02 — structure</text>
    <text class="label l3" x="660" y="368">03 — logic</text>
  </g>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        path = OUT / f"hero-{theme}.svg"
        path.write_text(svg(theme), encoding="utf-8")
        print(f"wrote {path.relative_to(OUT.parent)}")
