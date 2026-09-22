"""Generate the retro chess banner and pixel section headings (light + dark).

The banner replays the Scholar's mate on an 8-bit board:
1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7#

Run: python3 scripts/chess.py
"""

from pathlib import Path

from pixel import bitmap_path, text, text_path, text_width

OUT = Path(__file__).resolve().parent.parent / "assets" / "chess"

THEMES = {
    "light": {"fg": "#111111", "weak": "#6e7781", "faint": "#d0d7de", "bg": "#ffffff", "solid": "b"},
    "dark": {"fg": "#f0f6fc", "weak": "#8b949e", "faint": "#30363d", "bg": "#0d1117", "solid": "w"},
}

# 10x10 sprites. '#' = outline, 'o' = body (filled for the solid side, paper for the other).
SPRITES = {
    "K": ["....##....", "...####...", "....##....", "..######..", ".#oooooo#.",
          ".#oooooo#.", "..#oooo#..", "..#oooo#..", ".########.", ".........."],
    "Q": [".#..##..#.", ".#.#oo#.#.", ".##oooo##.", ".#oooooo#.", "..#oooo#..",
          "..#oooo#..", "..#oooo#..", ".#oooooo#.", ".########.", ".........."],
    "R": ["..........", ".##.##.##.", ".#oooooo#.", "..#oooo#..", "..#oooo#..",
          "..#oooo#..", "..#oooo#..", ".#oooooo#.", ".########.", ".........."],
    "B": ["....##....", "...#oo#...", "..#oo#o#..", "..#o#oo#..", "..#oooo#..",
          "...#oo#...", "....##....", "...#oo#...", ".########.", ".........."],
    "N": ["....##....", "...#oo##..", "..#o#ooo#.", ".#oooooo#.", "#ooooooo#.",
          "####.#oo#.", "....#ooo#.", "...#oooo#.", ".########.", ".........."],
    "P": ["..........", "....##....", "...#oo#...", "...#oo#...", "....##....",
          "...#oo#...", "...#oo#...", "..#oooo#..", ".########.", ".........."],
}

SQ = 48          # board square
PX = 4           # sprite pixel
PAD = (SQ - 10 * PX) // 2
BX, BY = 752, 28  # board origin
W, H = 1200, 440

DURATION = 18.0
MOVE_DUR = 0.5
MOVES = [  # (piece id, from, to, notation)
    ("wPe", "e2", "e4", "1. e4"),
    ("bPe", "e7", "e5", "1... e5"),
    ("wBf", "f1", "c4", "2. Bc4"),
    ("bNb", "b8", "c6", "2... Nc6"),
    ("wQd", "d1", "h5", "3. Qh5"),
    ("bNg", "g8", "f6", "3... Nf6"),
    ("wQd", "h5", "f7", "4. Qxf7#"),
]
CAPTURED = "bPf"  # taken on the last move
MATED = "bKe"
MOVE_TIMES = [1.6 + k * 1.7 for k in range(len(MOVES))]
MATE_TIME = MOVE_TIMES[-1] + MOVE_DUR
RESET = DURATION - 0.8  # pieces blink out, then the game restarts


def pct(t):
    return f"{100 * t / DURATION:.2f}%"


def square_xy(sq):
    f = ord(sq[0]) - ord("a")
    r = int(sq[1])
    return BX + f * SQ, BY + (8 - r) * SQ


def start_position():
    back = "RNBQKBNR"
    pieces = {}
    for i, f in enumerate("abcdefgh"):
        pieces[f"w{back[i]}{f}"] = f"{f}1"
        pieces[f"wP{f}"] = f"{f}2"
        pieces[f"bP{f}"] = f"{f}7"
        pieces[f"b{back[i]}{f}"] = f"{f}8"
    return pieces


def tr(sq):
    x, y = square_xy(sq)
    return f"transform: translate({x}px, {y}px);"


def sprite_defs(c):
    defs = []
    for name, bmp in SPRITES.items():
        solid = bitmap_path(bmp, PX, PAD, PAD, "#") + bitmap_path(bmp, PX, PAD, PAD, "o")
        defs.append(f'<g id="s{name}"><path fill="{c["fg"]}" d="{solid}"/></g>')
        defs.append(
            f'<g id="o{name}"><path fill="{c["bg"]}" d="{bitmap_path(bmp, PX, PAD, PAD, "o")}"/>'
            f'<path fill="{c["fg"]}" d="{bitmap_path(bmp, PX, PAD, PAD, "#")}"/></g>'
        )
    return "\n    ".join(defs)


def piece_animations():
    """CSS for every piece that moves, is captured or gets mated."""
    start = start_position()
    css = []
    by_piece = {}
    for (pid, frm, to, _), t in zip(MOVES, MOVE_TIMES):
        by_piece.setdefault(pid, []).append((t, frm, to))
    for pid, moves in by_piece.items():
        frames = [f"0% {{ {tr(start[pid])} }}"]
        for t, frm, to in moves:
            frames.append(f"{pct(t)} {{ {tr(frm)} }}")
            frames.append(f"{pct(t + MOVE_DUR)} {{ {tr(to)} }}")
        frames.append(f"100% {{ {tr(moves[-1][2])} }}")
        css.append(f"@keyframes m{pid} {{ {' '.join(frames)} }}")
        css.append(f".m{pid} {{ animation: m{pid} {DURATION}s steps(4, jump-end) infinite; {tr(start[pid])} }}")
    css.append(
        f"@keyframes cap {{ 0%, {pct(MATE_TIME - 0.1)} {{ opacity: 1; }} {pct(MATE_TIME)}, 100% {{ opacity: 0; }} }}"
        f" .m{CAPTURED} {{ animation: cap {DURATION}s steps(1, end) infinite; }}"
    )
    # the mated king blinks
    blink = " ".join(
        f"{pct(MATE_TIME + 0.4 * k)} {{ opacity: {k % 2}; }}" for k in range(1, 9)
    )
    css.append(
        f"@keyframes mate {{ 0%, {pct(MATE_TIME)} {{ opacity: 1; }} {blink} {pct(MATE_TIME + 3.6)}, 100% {{ opacity: 1; }} }}"
        f" .m{MATED} {{ animation: mate {DURATION}s steps(1, end) infinite; }}"
    )
    return "\n    ".join(css)


def pieces_svg(c):
    out = []
    for pid, sq in start_position().items():
        side, kind = pid[0], pid[1]
        sprite = ("s" if side == c["solid"] else "o") + kind
        moving = any(pid == m[0] for m in MOVES) or pid in (CAPTURED, MATED)
        if moving and pid != MATED and pid != CAPTURED:
            out.append(f'<use href="#{sprite}" class="m{pid}"/>')
        else:
            x, y = square_xy(sq)
            cls = f' class="m{pid}"' if pid in (CAPTURED, MATED) else ""
            # static pieces use a nested <g> so the blink animation can't reset the position
            out.append(f'<g transform="translate({x} {y})"><use href="#{sprite}"{cls}/></g>')
    return "\n    ".join(out)


def cursor_svg(c):
    """Corner brackets that follow each move, like a selection cursor."""
    t = 4
    L = 12
    d = (f"M0 0h{L}v{t}h{-L + t}v{L - t}h{-t}z"
         f"M{SQ} 0v{L}h{-t}v{-L + t}h{-L + t}v{-t}z"
         f"M0 {SQ}v{-L}h{t}v{L - t}h{L - t}v{t}z"
         f"M{SQ} {SQ}h{-L}v{-t}h{L - t}v{-L + t}h{t}z")
    frames = [f"0% {{ {tr('e2')} opacity: 0; }}", f"{pct(MOVE_TIMES[0] - 0.6)} {{ {tr('e2')} opacity: 1; }}"]
    for (pid, frm, to, _), t0 in zip(MOVES, MOVE_TIMES):
        frames.append(f"{pct(t0 - 0.4)} {{ {tr(frm)} opacity: 1; }}")
        frames.append(f"{pct(t0)} {{ {tr(frm)} opacity: 1; }}")
        frames.append(f"{pct(t0 + MOVE_DUR)} {{ {tr(to)} opacity: 1; }}")
    frames.append(f"{pct(RESET)} {{ {tr(MOVES[-1][2])} opacity: 1; }}")
    frames.append(f"{pct(RESET + 0.01)}, 100% {{ {tr(MOVES[-1][2])} opacity: 0; }}")
    css = (f"@keyframes cur {{ {' '.join(frames)} }}"
           f" .cursor {{ animation: cur {DURATION}s steps(4, jump-end) infinite; opacity: 0; }}")
    return css, f'<path class="cursor" fill="{c["weak"]}" d="{d}"/>'


def status_lines(c):
    """Bottom-left status: '> READY', then each move, then CHECKMATE."""
    states = [("> READY", 0.0, MOVE_TIMES[0])]
    for (_, _, _, note), t0, t1 in zip(MOVES, MOVE_TIMES, MOVE_TIMES[1:] + [MATE_TIME + 0.3]):
        states.append((f"> {note}", t0, t1))
    states.append(("> CHECKMATE!", MATE_TIME + 0.3, RESET))
    px, x, y = 4, 64, 366
    css, svg = [], []
    for i, (label, t0, t1) in enumerate(states):
        first = i == 0
        if first:
            frames = f"0%, {pct(t1 - 0.01)} {{ opacity: 1; }} {pct(t1)}, 100% {{ opacity: 0; }}"
        else:
            frames = (f"0%, {pct(t0 - 0.01)} {{ opacity: 0; }} {pct(t0)}, {pct(t1 - 0.01)} {{ opacity: 1; }}"
                      f" {pct(t1)}, 100% {{ opacity: 0; }}")
        css.append(f"@keyframes st{i} {{ {frames} }} .st{i} {{ animation: st{i} {DURATION}s steps(1, end) infinite; opacity: {1 if first else 0}; }}")
        cx = x + text_width(label, px) + 2 * px
        svg.append(
            f'<g class="st{i}">{text(label, px, x, y, "fg")}'
            f'<rect class="blink" x="{cx}" y="{y}" width="{5 * px}" height="{7 * px}"/></g>'
        )
    css.append("@keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }"
               " .blink { animation: blink 1s steps(1, end) infinite; }")
    return "\n    ".join(css), "\n  ".join(svg)


def hero(theme):
    c = THEMES[theme]
    cursor_css, cursor = cursor_svg(c)
    status_css, status = status_lines(c)
    squares = "".join(
        f"M{BX + f * SQ} {BY + r * SQ}h{SQ}v{SQ}h{-SQ}z"
        for r in range(8) for f in range(8) if (r + f) % 2 == 1
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="title desc">
  <title id="title">Vincenzo Parente</title>
  <desc id="desc">MSc Computer Science and Engineering at Politecnico di Milano. A pixel-art chessboard replays the Scholar's mate.</desc>
  <style>
    path {{ shape-rendering: crispEdges; }}
    .fg {{ fill: {c['fg']}; }} .weak {{ fill: {c['weak']}; }} .blink {{ fill: {c['fg']}; }}
    {piece_animations()}
    {cursor_css}
    {status_css}
    @keyframes reset {{ 0%, {pct(RESET)} {{ opacity: 1; }} {pct(RESET + 0.01)}, 100% {{ opacity: 0; }} }}
    .pieces {{ animation: reset {DURATION}s steps(1, end) infinite; }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
  </style>
  <defs>
    {sprite_defs(c)}
  </defs>

  <rect x="2" y="2" width="{W - 4}" height="{H - 4}" fill="none" stroke="{c['fg']}" stroke-width="4"/>

  {text("POLITECNICO DI MILANO / MSC CSE", 3, 64, 64, "weak")}
  {text("VINCENZO", 10, 60, 118, "fg")}
  {text("PARENTE", 10, 60, 208, "fg")}
  {text("APPLIED AI / LOGIC / CURIOSITY", 3, 64, 306, "weak")}
  {status}

  <rect x="{BX}" y="{BY}" width="{8 * SQ}" height="{8 * SQ}" fill="{c['bg']}"/>
  <path fill="{c['faint']}" d="{squares}"/>
  <rect x="{BX - 4}" y="{BY - 4}" width="{8 * SQ + 8}" height="{8 * SQ + 8}" fill="none" stroke="{c['fg']}" stroke-width="4"/>
  {cursor}
  <g class="pieces">
    {pieces_svg(c)}
  </g>
</svg>
"""


HEADINGS = {"about": ("K", "ABOUT"), "projects": ("R", "PROJECTS"), "toolbox": ("B", "TOOLBOX"),
            "stats": ("N", "STATS"), "contact": ("Q", "CONTACT")}


def heading(theme, sprite, label):
    c = THEMES[theme]
    px, sp = 4, 3
    h = 10 * sp
    tw = text_width(label, px)
    w = 10 * sp + 14 + tw
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label.title()}">
  <style>path {{ shape-rendering: crispEdges; }}</style>
  <path fill="{c['fg']}" d="{bitmap_path(SPRITES[sprite], sp, 0, 0, '#') + bitmap_path(SPRITES[sprite], sp, 0, 0, 'o')}"/>
  <path fill="{c['fg']}" d="{text_path(label, px, 10 * sp + 14, (h - 7 * px) / 2)}"/>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (OUT / f"hero-{theme}.svg").write_text(hero(theme), encoding="utf-8")
        for key, (sprite, label) in HEADINGS.items():
            (OUT / f"h-{key}-{theme}.svg").write_text(heading(theme, sprite, label), encoding="utf-8")
    print(f"wrote {len(list(OUT.glob('*.svg')))} files to {OUT.relative_to(OUT.parent.parent)}")
