#!/usr/bin/env python3
"""
Generador de assets SVG animados para el README de GitHub.

Un solo source of truth (design tokens) -> emite variante dark y light
de cada asset. Los SVG usan SMIL + CSS: ambos animan cuando GitHub los
sirve como <img> a traves de camo. Nada de JS (camo lo ignora).

Uso:  python3 scripts/build_assets.py
Salida: assets/*.svg
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

FONT = "'Inter','Segoe UI',system-ui,-apple-system,'Helvetica Neue',Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace"

# ---------------------------------------------------------------- tokens
THEMES = {
    "dark": {
        "bg":        "#080B14",
        "bg2":       "#0D1220",
        "surface":   "#131A2B",
        "text":      "#EEF2FB",
        "muted":     "#8A97B1",
        "faint":     "#2A3346",
        "violet":    "#8B5CF6",
        "blue":      "#3B82F6",
        "cyan":      "#22D3EE",
        "magenta":   "#E879F9",
        "grid":      "#FFFFFF",
        "gridop":    "0.035",
        "blobop":    "0.55",
        "glowop":    "0.30",
    },
    "light": {
        "bg":        "#FBFCFF",
        "bg2":       "#F1F4FC",
        "surface":   "#FFFFFF",
        "text":      "#0A0E1A",
        "muted":     "#5B6478",
        "faint":     "#D3DAE8",
        "violet":    "#6D28D9",
        "blue":      "#1D4ED8",
        "cyan":      "#0891B2",
        "magenta":   "#C026D3",
        "grid":      "#0A0E1A",
        "gridop":    "0.045",
        "blobop":    "0.30",
        "glowop":    "0.18",
    },
}


def fill(tpl: str, t: dict) -> str:
    out = tpl
    for k, v in t.items():
        out = out.replace("@" + k.upper() + "@", v)
    return out.replace("@FONT@", FONT).replace("@MONO@", MONO)


# ---------------------------------------------------------------- shared defs
def base_defs(idp: str) -> str:
    """Gradientes, filtros y grid compartidos. idp = prefijo de ids."""
    return f"""
  <defs>
    <linearGradient id="{idp}brand" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="@VIOLET@"/>
      <stop offset="45%"  stop-color="@BLUE@"/>
      <stop offset="100%" stop-color="@CYAN@"/>
    </linearGradient>

    <!-- gradiente que se desplaza: da el "shimmer" del titulo -->
    <linearGradient id="{idp}shimmer" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="@VIOLET@"/>
      <stop offset="30%"  stop-color="@BLUE@"/>
      <stop offset="55%"  stop-color="@CYAN@"/>
      <stop offset="80%"  stop-color="@MAGENTA@"/>
      <stop offset="100%" stop-color="@VIOLET@"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        values="-1 0; 1 0; -1 0" dur="12s" repeatCount="indefinite"/>
    </linearGradient>

    <radialGradient id="{idp}b1"><stop offset="0%" stop-color="@VIOLET@" stop-opacity="1"/><stop offset="100%" stop-color="@VIOLET@" stop-opacity="0"/></radialGradient>
    <radialGradient id="{idp}b2"><stop offset="0%" stop-color="@CYAN@"   stop-opacity="1"/><stop offset="100%" stop-color="@CYAN@"   stop-opacity="0"/></radialGradient>
    <radialGradient id="{idp}b3"><stop offset="0%" stop-color="@MAGENTA@" stop-opacity="1"/><stop offset="100%" stop-color="@MAGENTA@" stop-opacity="0"/></radialGradient>

    <filter id="{idp}soft" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="42"/>
    </filter>
    <filter id="{idp}glow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="3.2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>

    <pattern id="{idp}grid" width="34" height="34" patternUnits="userSpaceOnUse">
      <path d="M34 0H0V34" fill="none" stroke="@GRID@" stroke-opacity="@GRIDOP@" stroke-width="1"/>
    </pattern>
  </defs>"""


# ---------------------------------------------------------------- HERO
NODES = [
    (824,  92), (902,  58), (978, 112), (1056,  68), (1126, 132),
    (858, 176), (942, 196), (1022, 168), (1102, 220),
    (884, 268), (976, 280), (1062, 292),
]
EDGES = [
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 2), (2, 7),
    (7, 4), (7, 8), (5, 9), (9, 10), (10, 6), (10, 11), (11, 8), (8, 4),
]


def hero(t: dict) -> str:
    W, H = 1200, 340
    idp = "h_"

    edges, motion = [], []
    for i, (a, b) in enumerate(EDGES):
        x1, y1 = NODES[a]
        x2, y2 = NODES[b]
        length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        edges.append(
            f'<path id="{idp}e{i}" d="M{x1} {y1}L{x2} {y2}" stroke="url(#{idp}brand)" '
            f'stroke-width="1.1" stroke-opacity=".45" fill="none" '
            f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
            f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" '
            f'dur="1.1s" begin="{0.25 + i * 0.055:.2f}s" fill="freeze"/></path>'
        )

    # 3 paquetes de datos viajando por la red
    for k, (eid, dur, begin) in enumerate([(1, 5.5, 1.2), (7, 6.4, 2.6), (12, 5.0, 3.8)]):
        motion.append(
            f'<circle r="2.6" fill="@CYAN@" filter="url(#{idp}glow)" opacity="0">'
            f'<animate attributeName="opacity" values="0;1;1;0" dur="{dur}s" '
            f'begin="{begin}s" repeatCount="indefinite"/>'
            f'<animateMotion dur="{dur}s" begin="{begin}s" repeatCount="indefinite" '
            f'keyPoints="0;1" keyTimes="0;1" calcMode="linear">'
            f'<mpath href="#{idp}e{eid}"/></animateMotion></circle>'
        )

    dots = []
    for i, (x, y) in enumerate(NODES):
        r = 4.2 if i in (2, 5, 10) else 2.8
        dots.append(
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#{idp}brand)" filter="url(#{idp}glow)" '
            f'class="node" style="animation-delay:{i * 0.31:.2f}s"/>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Eddie Elorza - AI Product Engineer">
{base_defs(idp)}
  <style>
    .f  {{ opacity:0; animation: rise .85s cubic-bezier(.22,.68,.24,1) forwards; }}
    @keyframes rise {{ from {{ opacity:0; transform: translateY(14px); }} to {{ opacity:1; transform: none; }} }}
    @keyframes bar  {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes node {{ 0%,100% {{ opacity:.45; }} 50% {{ opacity:1; }} }}
    .node {{ animation: node 3.6s ease-in-out infinite; }}
    .rule {{ transform-box: fill-box; transform-origin: left center; transform: scaleX(0);
             animation: bar 1.1s cubic-bezier(.22,.68,.24,1) .5s forwards; }}
    .caret {{ animation: node 1.05s steps(1) infinite; }}
  </style>

  <rect width="{W}" height="{H}" rx="16" fill="@BG@"/>
  <rect width="{W}" height="{H}" rx="16" fill="url(#{idp}grid)"/>

  <g opacity="@BLOBOP@" filter="url(#{idp}soft)">
    <circle cx="180" cy="90" r="190" fill="url(#{idp}b1)">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; 70 40; -30 20; 0 0" dur="18s" repeatCount="indefinite"/>
    </circle>
    <circle cx="600" cy="330" r="200" fill="url(#{idp}b2)">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; -80 -50; 50 -20; 0 0" dur="22s" repeatCount="indefinite"/>
    </circle>
    <circle cx="1010" cy="60" r="170" fill="url(#{idp}b3)">
      <animateTransform attributeName="transform" type="translate"
        values="0 0; 40 60; -60 30; 0 0" dur="26s" repeatCount="indefinite"/>
    </circle>
  </g>

  <g opacity="@GLOWOP@" filter="url(#{idp}soft)">
    <circle cx="975" cy="175" r="145" fill="url(#{idp}b1)"/>
  </g>

  <!-- red neuronal -->
  <g>{''.join(edges)}{''.join(dots)}{''.join(motion)}</g>

  <!-- texto -->
  <g font-family="@FONT@">
    <g class="f" style="animation-delay:.05s">
      <rect x="64" y="62" width="9" height="9" rx="2" fill="@CYAN@"/>
      <text x="86" y="71" font-family="@MONO@" font-size="12.5" letter-spacing="3.4"
            fill="@MUTED@">AI · PRODUCT · ENGINEERING</text>
    </g>

    <text class="f" style="animation-delay:.16s" x="62" y="158" font-size="66" font-weight="800"
          letter-spacing="-2.2" fill="url(#{idp}shimmer)">Eddie Elorza</text>

    <text class="f" style="animation-delay:.28s" x="65" y="196" font-size="20" font-weight="500"
          fill="@TEXT@" opacity=".92">Building intelligent products from idea to production.</text>

    <text class="f" style="animation-delay:.38s" x="65" y="226" font-size="15" fill="@MUTED@">
      Product strategy · AI systems · Frontend architecture · Fintech
    </text>

    <rect class="rule" x="64" y="252" width="330" height="2.5" rx="2" fill="url(#{idp}brand)"/>

    <g class="f" style="animation-delay:.62s" font-family="@MONO@" font-size="13" fill="@MUTED@">
      <text x="64" y="288">
        <tspan fill="@CYAN@">~</tspan> Mexico City, MX
        <tspan fill="@FAINT@">  |  </tspan>MSc Applied AI
        <tspan fill="@FAINT@">  |  </tspan>PSPO I
        <tspan fill="@FAINT@">  |  </tspan>6+ yrs fintech<tspan class="caret" fill="@CYAN@">_</tspan>
      </text>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------- PIPELINE
STAGES = ["Problem", "Discovery", "Strategy", "Architecture", "Engineering", "Data", "Impact"]


def pipeline(t: dict) -> str:
    W, H = 1200, 132
    idp = "p_"
    y = 56
    x0, x1 = 96, 1104
    step = (x1 - x0) / (len(STAGES) - 1)

    nodes, labels = [], []
    for i, s in enumerate(STAGES):
        x = x0 + step * i
        last = i == len(STAGES) - 1
        nodes.append(
            f'<circle cx="{x:.1f}" cy="{y}" r="{7.5 if last else 6}" fill="@BG@" '
            f'stroke="url(#{idp}brand)" stroke-width="2"/>'
            f'<circle cx="{x:.1f}" cy="{y}" r="{3.4 if last else 2.6}" fill="url(#{idp}brand)" '
            f'filter="url(#{idp}glow)" class="hop" style="animation-delay:{i * 0.42:.2f}s"/>'
        )
        labels.append(
            f'<text x="{x:.1f}" y="{y + 34}" text-anchor="middle" font-family="@MONO@" '
            f'font-size="11" letter-spacing="1.1" fill="{"@TEXT@" if last else "@MUTED@"}" '
            f'class="f" style="animation-delay:{0.2 + i * 0.09:.2f}s">{s.upper()}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Problem to Impact delivery pipeline">
{base_defs(idp)}
  <style>
    .f   {{ opacity:0; animation: rise .6s ease-out forwards; }}
    @keyframes rise {{ from {{ opacity:0; transform: translateY(8px);}} to {{ opacity:1; transform:none;}} }}
    @keyframes hop  {{ 0%,72%,100% {{ opacity:.35; }} 82% {{ opacity:1; }} }}
    .hop  {{ animation: hop 3s ease-in-out infinite; }}
    .flow {{ stroke-dasharray: 14 210; animation: flow 3s linear infinite; }}
    @keyframes flow {{ to {{ stroke-dashoffset: -224; }} }}
  </style>

  <rect width="{W}" height="{H}" rx="14" fill="@BG2@"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#{idp}grid)"/>

  <path id="{idp}track" d="M{x0} {y}H{x1}" stroke="@FAINT@" stroke-width="2" stroke-linecap="round"/>
  <path d="M{x0} {y}H{x1}" stroke="url(#{idp}brand)" stroke-width="2.5" stroke-linecap="round"
        stroke-dasharray="1008" stroke-dashoffset="1008" opacity=".85">
    <animate attributeName="stroke-dashoffset" from="1008" to="0" dur="1.6s" fill="freeze"/>
  </path>
  <path class="flow" d="M{x0} {y}H{x1}" stroke="@CYAN@" stroke-width="3.4"
        stroke-linecap="round" filter="url(#{idp}glow)" opacity=".9"/>

  <circle r="3.4" fill="@MAGENTA@" filter="url(#{idp}glow)">
    <animateMotion dur="3s" repeatCount="indefinite" calcMode="linear">
      <mpath href="#{idp}track"/>
    </animateMotion>
  </circle>

  <g>{''.join(nodes)}</g>
  <g>{''.join(labels)}</g>
  <text x="{W//2}" y="{H - 12}" text-anchor="middle" font-family="@FONT@" font-size="12"
        fill="@MUTED@" class="f" style="animation-delay:.9s" opacity="0">
    from product idea → architecture → code → measurable impact
  </text>
</svg>
"""


# ---------------------------------------------------------------- FOCUS BARS
FOCUS = [
    ("AI Product Management", 95),
    ("AI Agents &amp; Orchestration", 90),
    ("Product Analytics", 82),
    ("Digital Transformation", 78),
    ("Engineering Leadership", 74),
    ("Business Strategy", 70),
]


def focus(t: dict) -> str:
    W = 1000
    rowh, top = 38, 26
    H = top + rowh * len(FOCUS) + 12
    idp = "f_"
    lx, bx, bw = 26, 300, 610

    rows = []
    for i, (label, pct) in enumerate(FOCUS):
        y = top + rowh * i
        w = bw * pct / 100
        d = 0.18 + i * 0.11
        rows.append(f"""
    <g>
      <text x="{lx}" y="{y + 15}" font-family="@FONT@" font-size="14.5" font-weight="500"
            fill="@TEXT@" class="f" style="animation-delay:{d:.2f}s">{label}</text>
      <rect x="{bx}" y="{y + 4}" width="{bw}" height="9" rx="4.5" fill="@FAINT@" opacity=".55"/>
      <rect x="{bx}" y="{y + 4}" width="0" height="9" rx="4.5" fill="url(#{idp}brand)">
        <animate attributeName="width" from="0" to="{w:.0f}" dur="1.15s"
                 begin="{d + 0.1:.2f}s" fill="freeze"
                 calcMode="spline" keySplines="0.2 0.7 0.2 1" keyTimes="0;1"/>
      </rect>
      <circle cx="{bx}" cy="{y + 8.5}" r="5.5" fill="@CYAN@" filter="url(#{idp}glow)" opacity="0">
        <animate attributeName="cx" from="{bx}" to="{bx + w:.0f}" dur="1.15s"
                 begin="{d + 0.1:.2f}s" fill="freeze"
                 calcMode="spline" keySplines="0.2 0.7 0.2 1" keyTimes="0;1"/>
        <animate attributeName="opacity" values="0;1;1;.55" dur="1.15s"
                 begin="{d + 0.1:.2f}s" fill="freeze"/>
      </circle>
      <text x="{bx + bw + 34}" y="{y + 14}" text-anchor="end" font-family="@MONO@" font-size="12.5"
            fill="@MUTED@" class="f" style="animation-delay:{d + 0.85:.2f}s">{pct}%</text>
    </g>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="Current focus areas">
{base_defs(idp)}
  <style>
    .f {{ opacity:0; animation: rise .55s ease-out forwards; }}
    @keyframes rise {{ from {{opacity:0; transform:translateX(-8px);}} to {{opacity:1; transform:none;}} }}
  </style>
  <rect width="{W}" height="{H}" rx="14" fill="@BG2@"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#{idp}grid)"/>
  {''.join(rows)}
</svg>
"""


# ---------------------------------------------------------------- TOOLING
# Chips tipograficos: skillicons.dev no tiene iconos para Claude, Cursor,
# Warp ni Ollama (devuelve un placeholder "?"), y dibujar logos de marca a
# mano seria impreciso. El texto envejece mejor.
TOOLING = [
    ("AI TOOLING",    ["Claude Code", "Cursor", "Warp", "Ollama", "LLM orchestration"]),
    ("AGENTIC LAYER", ["LLM agents", "MCP servers", "Skills", "Vector search", "RAG"]),
    ("ARCHITECTURE",  ["Module Federation", "Microfrontends", "n8n"]),
    ("OBSERVABILITY", ["Dynatrace", "Elastic APM", "Core Web Vitals", "Event tracking"]),
    ("PRODUCT OPS",   ["Jira", "Miro", "A/B testing"]),
]

# No hay forma de medir texto sin las metricas de la fuente, y estirar el
# glifo con textLength deforma las palabras cortas ("S k i l l s"). Esta
# tabla aproxima el ancho por caracter en ems para un sans de UI: basta
# para que ningun chip se desborde y las proporciones se vean naturales.
_NARROW = "iljItfr.,;:'!|()[]-  "
_WIDE = "MWmw"
_EM = 13.5
# 26px hasta donde arranca el texto (punto + inset) + 16px de aire derecho.
PILL_PAD = 42


def text_w(s: str) -> float:
    w = 0.0
    for c in s:
        if c == " ":
            w += 0.28
        elif c in _NARROW:
            w += 0.31
        elif c in _WIDE:
            w += 0.86
        elif c.isupper() or c.isdigit():
            w += 0.63
        else:
            w += 0.545
    return w * _EM


def tooling(t: dict) -> str:
    pad, top = 30, 36
    rowh, gap = 54, 9
    idp = "t_"
    H = top + rowh * len(TOOLING) + 6

    # La tarjeta se ajusta al contenido: sobrarle 500px de fondo vacio se ve
    # como un bug de layout, no como aire.
    def row_w(items):
        return sum(text_w(n) + PILL_PAD for n in items) + gap * (len(items) - 1)

    W = int(max(row_w(items) for _, items in TOOLING) + pad * 2)

    groups = []
    for gi, (label, items) in enumerate(TOOLING):
        y = top + rowh * gi
        groups.append(
            f'<text x="{pad}" y="{y + 4}" font-family="@MONO@" font-size="10" font-weight="700" '
            f'fill="@MUTED@" letter-spacing="2">{label}</text>'
        )
        x = pad
        for ii, name in enumerate(items):
            w = text_w(name) + PILL_PAD
            d = 0.14 + gi * 0.20 + ii * 0.07
            accent = ["@VIOLET@", "@BLUE@", "@CYAN@", "@MAGENTA@"][ii % 4]
            groups.append(f"""
    <g class="p" style="animation-delay:{d:.2f}s">
      <rect x="{x:.0f}" y="{y + 12}" width="{w:.0f}" height="26" rx="13"
            fill="@SURFACE@" stroke="@FAINT@"/>
      <circle cx="{x + 15:.0f}" cy="{y + 25}" r="3.5" fill="{accent}"/>
      <text x="{x + 26:.0f}" y="{y + 29}" font-family="@FONT@" font-size="13.5"
            font-weight="500" fill="@TEXT@">{name}</text>
    </g>""")
            x += w + gap

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="AI tooling: Claude Code, Cursor, Warp, Obsidian, Ollama, LLM agents, MCP servers, Skills">
{base_defs(idp)}
  <style>
    .p {{ opacity:0; animation: t_pop .5s cubic-bezier(.2,.7,.3,1) forwards; }}
    @keyframes t_pop {{ from {{opacity:0; transform:translateY(7px);}} to {{opacity:1; transform:none;}} }}
  </style>
  <rect width="{W}" height="{H}" rx="14" fill="@BG2@"/>
  <rect width="{W}" height="{H}" rx="14" fill="url(#{idp}grid)"/>
  {''.join(groups)}
</svg>
"""


# ---------------------------------------------------------------- DIVIDER
def divider(t: dict) -> str:
    W, H = 1200, 6
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="presentation">
  <defs>
    <linearGradient id="d_g" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="@VIOLET@" stop-opacity="0"/>
      <stop offset="25%"  stop-color="@VIOLET@"/>
      <stop offset="50%"  stop-color="@BLUE@"/>
      <stop offset="75%"  stop-color="@CYAN@"/>
      <stop offset="100%" stop-color="@CYAN@" stop-opacity="0"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        values="-0.6 0; 0.6 0; -0.6 0" dur="9s" repeatCount="indefinite"/>
    </linearGradient>
  </defs>
  <rect y="2" width="{W}" height="2" rx="1" fill="url(#d_g)"/>
</svg>
"""


# ---------------------------------------------------------------- build
BUILDERS = {"hero": hero, "pipeline": pipeline, "focus": focus,
            "tooling": tooling, "divider": divider}

if __name__ == "__main__":
    for name, fn in BUILDERS.items():
        for theme, tokens in THEMES.items():
            svg = fill(fn(tokens), tokens)
            path = OUT / f"{name}-{theme}.svg"
            path.write_text(svg, encoding="utf-8")
            print(f"  ✓ {path.relative_to(OUT.parent)}  ({len(svg)/1024:.1f} KB)")
    print("\nListo. Commitea la carpeta assets/ en tu repo de perfil.")
