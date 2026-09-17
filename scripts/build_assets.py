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
# Paleta tomada del sticker (marcador azul tinta, verde, amarillo y el rojo
# del corazon). Solo el hero la usa; el resto de assets conserva sus tokens.
import base64

HERO_TOKENS = {
    "dark": {
        "bg": "#0B1033", "paper": "#FFFFFF", "dotop": "0.07",
        "ink": "#F6F2E7", "muted": "#AEB5DC", "faint": "#2A3263",
        "blue": "#7D8CFF", "green": "#2FD6A4", "yellow": "#FFD93D", "red": "#FF5A6E",
        "shadow": "#000000", "shadowop": "0.55", "hl": "1", "hltext": "#0B1033",
    },
    "light": {
        "bg": "#FBF6EA", "paper": "#1424A8", "dotop": "0.09",
        "ink": "#101A78", "muted": "#48507F", "faint": "#E4DCC6",
        "blue": "#1B2FD0", "green": "#0B9B74", "yellow": "#F4CF1B", "red": "#E8304A",
        "shadow": "#1424A8", "shadowop": "0.22", "hl": "0.55", "hltext": "#101A78",
    },
}

STICKER = Path(__file__).resolve().parent.parent / "assets" / "sticker-heart.webp"
STICKER_RATIO = 1162 / 1076  # ancho / alto del recorte


def hero(t: dict) -> str:
    W, H = 1200, 340
    h = HERO_TOKENS["dark" if t is THEMES["dark"] else "light"]
    data = base64.b64encode(STICKER.read_bytes()).decode()

    sh = 300                       # alto del sticker
    sw = round(sh * STICKER_RATIO)
    sx, sy = 1150 - sw, 22
    cx, cy = sx + sw / 2, sy + sh / 2
    # el corazon del dibujo queda arriba a la izquierda del sticker
    hx, hy = sx + sw * 0.25, sy + sh * 0.30

    hearts = []
    for i, (dx, size, dur, begin) in enumerate([(-6, 11, 3.6, 0.8), (14, 8, 4.2, 2.1), (-18, 7, 3.9, 3.3)]):
        x0 = hx + dx
        hearts.append(f"""
    <path d="M0 3.2C0 1.4 1.4 0 3.1 0c1.1 0 2.1.6 2.6 1.5C6.2.6 7.2 0 8.3 0 10 0 11.4 1.4 11.4 3.2c0 3.1-5.7 6.8-5.7 6.8S0 6.3 0 3.2z"
          fill="none" stroke="{h['red']}" stroke-width="1.8" stroke-linejoin="round" opacity="0">
      <animateTransform attributeName="transform" type="translate"
        values="{x0:.0f} {hy:.0f}; {x0 - 10:.0f} {hy - 70:.0f}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>
      <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.15;.6;1" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>
    </path>""")

    def spark(x, y, r, color, begin):
        return (f'<path d="M{x} {y - r}Q{x + r * .18} {y - r * .18} {x + r} {y}Q{x + r * .18} {y + r * .18} {x} {y + r}'
                f'Q{x - r * .18} {y + r * .18} {x - r} {y}Q{x - r * .18} {y - r * .18} {x} {y - r}Z" fill="{color}">'
                f'<animate attributeName="opacity" values=".25;1;.25" dur="2.6s" begin="{begin}s" repeatCount="indefinite"/>'
                f'</path>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img"
     aria-label="Eddie Elorza - Software Engineer, Product Builder. Designing and building products end to end.">
  <defs>
    <pattern id="h_dots" width="22" height="22" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.3" fill="{h['paper']}" fill-opacity="{h['dotop']}"/>
    </pattern>
    <filter id="h_rough" x="-5%" y="-40%" width="110%" height="180%">
      <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="7"/>
      <feDisplacementMap in="SourceGraphic" scale="4"/>
    </filter>
    <filter id="h_shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="{h['shadow']}" flood-opacity="{h['shadowop']}"/>
    </filter>
  </defs>
  <style>
    .f  {{ opacity:0; animation: rise .8s cubic-bezier(.22,.68,.24,1) forwards; }}
    @keyframes rise {{ from {{ opacity:0; transform: translateY(12px); }} to {{ opacity:1; transform: none; }} }}
    .draw {{ stroke-dasharray: 420; stroke-dashoffset: 420; animation: draw 1s cubic-bezier(.3,.7,.3,1) .55s forwards; }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    .pop {{ opacity:0; transform-box: fill-box; transform-origin: center;
            animation: pop .7s cubic-bezier(.2,1.5,.4,1) .15s forwards; }}
    @keyframes pop {{ from {{ opacity:0; transform: scale(.82) rotate(-6deg); }} to {{ opacity:1; transform: none; }} }}
    .caret {{ animation: blink 1.05s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity:0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .f, .pop {{ animation: none; opacity: 1; }} .draw {{ animation: none; stroke-dashoffset: 0; }} .caret {{ animation: none; }}
    }}
  </style>

  <rect width="{W}" height="{H}" rx="18" fill="{h['bg']}"/>
  <rect width="{W}" height="{H}" rx="18" fill="url(#h_dots)"/>

  <!-- trazos de marcador alrededor del sticker -->
  <g stroke-linecap="round" fill="none" class="f" style="animation-delay:.7s">
    <path d="M{sx - 34} {sy + 92}l-26 -10M{sx - 30} {sy + 116}h-30M{sx - 34} {sy + 140}l-26 10"
          stroke="{h['yellow']}" stroke-width="6" filter="url(#h_rough)"/>
    <path d="M{sx + sw + 8} {sy + 212}q14 -8 28 0M{sx + sw + 4} {sy + 232}q18 -9 34 0"
          stroke="{h['blue']}" stroke-width="5" filter="url(#h_rough)"/>
  </g>
  {spark(sx + sw - 18, sy + 18, 11, h['yellow'], 0.4)}
  {spark(sx - 8, sy + sh - 36, 7, h['green'], 1.5)}
  {spark(sx + sw * .55, sy + 4, 6, h['blue'], 2.2)}

  <!-- sticker: entra con un pop y luego se mece -->
  <g class="pop">
    <g filter="url(#h_shadow)">
      <animateTransform attributeName="transform" type="rotate"
        values="-2 {cx:.0f} {cy:.0f}; 2 {cx:.0f} {cy:.0f}; -2 {cx:.0f} {cy:.0f}" dur="7s"
        calcMode="spline" keyTimes="0;.5;1" keySplines=".45 0 .55 1;.45 0 .55 1" repeatCount="indefinite"/>
      <image x="{sx}" y="{sy}" width="{sw}" height="{sh}" href="data:image/webp;base64,{data}"/>
    </g>
  </g>
  <g>{''.join(hearts)}</g>

  <!-- texto -->
  <g font-family="@FONT@">
    <g class="f" style="animation-delay:.05s">
      <path d="M58 52h392l-4 26H62z" fill="{h['yellow']}" fill-opacity="{h['hl']}" filter="url(#h_rough)"/>
      <text x="70" y="70" font-family="@MONO@" font-size="12.5" font-weight="700" letter-spacing="3"
            fill="{h['hltext']}">SOFTWARE ENGINEER · PRODUCT BUILDER</text>
    </g>

    <text class="f" style="animation-delay:.16s" x="62" y="152" font-size="68" font-weight="800"
          letter-spacing="-2.2" fill="{h['ink']}">Eddie Elorza</text>
    <path class="draw" d="M66 170c70 -9 150 -10 225 -5s110 5 160 -3" fill="none"
          stroke="{h['green']}" stroke-width="7" stroke-linecap="round" filter="url(#h_rough)"/>

    <text class="f" style="animation-delay:.3s" x="65" y="214" font-size="21" font-weight="600"
          fill="{h['ink']}">Designing and building products end to end.</text>

    <g class="f" style="animation-delay:.4s" font-size="15.5" fill="{h['muted']}">
      <circle cx="70" cy="242" r="4" fill="{h['blue']}"/><text x="82" y="247">Fintech &amp; payments</text>
      <circle cx="248" cy="242" r="4" fill="{h['green']}"/><text x="260" y="247">Frontend architecture</text>
      <circle cx="441" cy="242" r="4" fill="{h['red']}"/><text x="453" y="247">AI First</text>
    </g>

    <g class="f" style="animation-delay:.6s" font-family="@MONO@" font-size="13" fill="{h['muted']}">
      <text x="64" y="294">
        <tspan fill="{h['red']}">♥</tspan> Mexico City, MX
        <tspan fill="{h['faint']}">  |  </tspan>MSc Applied AI
        <tspan fill="{h['faint']}">  |  </tspan>PSPO I
        <tspan fill="{h['faint']}">  |  </tspan>6+ yrs building software<tspan class="caret" fill="{h['blue']}">_</tspan>
      </text>
    </g>
  </g>
</svg>
"""


# ---------------------------------------------------------------- PIPELINE
STAGES = ["Problem", "Scope", "Solution", "Plan", "Build", "Quality", "Operate"]


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
     aria-label="Problem to Operate delivery method">
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
    from business problem → architecture → code → operation
  </text>
</svg>
"""


# ---------------------------------------------------------------- FOCUS
# Sin porcentajes: cada foco apunta al proyecto que lo respalda.
FOCUS = [
    ("Agent guard-rails &amp; evals",     "Spine"),
    ("LLM features in real products",   "Tastify"),
    ("Local-first AI",                  "English OS"),
    ("Product discovery with clients",  "Hotel CRM"),
]


def focus(t: dict) -> str:
    W = 1000
    rowh, top = 58, 22
    H = top + rowh * len(FOCUS) + 10
    idp = "f_"
    lx, rx = 30, W - 30
    accents = ["@VIOLET@", "@BLUE@", "@CYAN@", "@MAGENTA@"]
    aria = "Current focus: " + " · ".join(f"{l} ({p})" for l, p in FOCUS)

    rows = []
    for i, (label, proof) in enumerate(FOCUS):
        y = top + rowh * i
        cy = y + 22
        d = 0.15 + i * 0.16
        pw = text_w(proof) + PILL_PAD
        px = rx - pw
        lw = text_w(label.replace("&amp;", "&")) * 1.2
        x1, x2 = lx + 24 + lw + 18, px - 16
        rows.append(f"""
    <g>
      <circle cx="{lx + 6}" cy="{cy}" r="5" fill="{accents[i % 4]}" filter="url(#{idp}glow)"
              class="f" style="animation-delay:{d:.2f}s"/>
      <text x="{lx + 24}" y="{cy + 6}" font-family="@FONT@" font-size="16.5" font-weight="600"
            fill="@TEXT@" class="f" style="animation-delay:{d:.2f}s">{label}</text>
      <path d="M{x1:.0f} {cy}H{x2:.0f}" stroke="@FAINT@" stroke-width="1.6"
            stroke-dasharray="{x2 - x1:.0f}" stroke-dashoffset="{x2 - x1:.0f}">
        <animate attributeName="stroke-dashoffset" from="{x2 - x1:.0f}" to="0" dur=".9s"
                 begin="{d + 0.15:.2f}s" fill="freeze"/>
      </path>
      <g class="f" style="animation-delay:{d + 0.55:.2f}s">
        <rect x="{px:.0f}" y="{cy - 14}" width="{pw:.0f}" height="28" rx="14"
              fill="@SURFACE@" stroke="@FAINT@"/>
        <circle cx="{px + 15:.0f}" cy="{cy}" r="3.5" fill="{accents[i % 4]}"/>
        <text x="{px + 26:.0f}" y="{cy + 5}" font-family="@FONT@" font-size="13.5"
              font-weight="500" fill="@MUTED@">{proof}</text>
      </g>
    </g>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="{aria}">
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
    ("AI TOOLING",    ["Claude Code", "Cursor", "Warp", "Ollama"]),
    ("AGENTIC LAYER", ["Coding agents", "MCP servers", "Skills", "Guard-rails", "Evals"]),
    ("ARCHITECTURE",  ["Module Federation", "qiankun", "Microfrontends"]),
    ("TESTING",       ["Jest", "Testing Library", "Playwright"]),
    ("PRODUCT OPS",   ["Jira", "Miro"]),
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
    aria = " · ".join(f"{g}: " + ", ".join(i) for g, i in TOOLING)

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
     role="img" aria-label="{aria}">
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
