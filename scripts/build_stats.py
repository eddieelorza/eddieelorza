#!/usr/bin/env python3
"""
Generador de las tarjetas de estadisticas del README.

Consulta la GraphQL API de GitHub y emite SVG propios en assets/:
  stats-{dark,light}.svg     metricas de perfil
  langs-{dark,light}.svg     top lenguajes por bytes
  activity-{dark,light}.svg  heatmap de contribuciones del ultimo ano

Cero dependencias de terceros: los SVG viven en el repo, no en un
servicio que se pueda quedar sin cuota.

Uso:
    GITHUB_TOKEN=$(gh auth token) python3 scripts/build_stats.py [usuario]

Notas de token:
  - Un PAT propio incluye `restrictedContributionsCount` (commits en
    repos privados). El GITHUB_TOKEN de Actions no los ve; para
    incluirlos guarda un PAT como secret PROFILE_TOKEN.
"""

import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_assets import THEMES, FONT, MONO, fill  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(parents=True, exist_ok=True)

USER = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GH_USER") or "eddieelorza")
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    sys.exit("falta GITHUB_TOKEN (usa: GITHUB_TOKEN=$(gh auth token) python3 scripts/build_stats.py)")

# Rampa del heatmap, alineada con la paleta del snake.
LEVELS = {
    "dark":  ["#131A2B", "#3B0764", "#5B21B6", "#8B5CF6", "#22D3EE"],
    "light": ["#EDF0F7", "#DDD6FE", "#A78BFA", "#6D28D9", "#0891B2"],
}


# ---------------------------------------------------------------- API
def gql(query: str, **variables) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-stats",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if "errors" in payload:
        sys.exit("GraphQL: " + json.dumps(payload["errors"], indent=2))
    return payload["data"]


PROFILE_Q = """
query($login:String!){
  user(login:$login){
    createdAt
    followers{ totalCount }
    pullRequests{ totalCount }
    contributionsCollection{
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount weekday } }
      }
    }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false){
      totalCount
      nodes{
        stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){
          edges{ size node{ name color } }
        }
      }
    }
  }
}
"""

YEAR_Q = """
query($login:String!,$from:DateTime!,$to:DateTime!){
  user(login:$login){
    contributionsCollection(from:$from,to:$to){
      restrictedContributionsCount
      contributionCalendar{
        totalContributions
        weeks{ contributionDays{ date contributionCount } }
      }
    }
  }
}
"""


def streaks(day_counts: dict) -> tuple:
    """(streak actual, streak mas largo, rango del mas largo) sobre el historial completo."""
    if not day_counts:
        return 0, 0, ""
    days = sorted(day_counts)
    best = cur = 0
    best_end = cur_start = best_start = None
    for d in days:
        if day_counts[d] > 0:
            cur = cur + 1 if cur else 1
            if cur == 1:
                cur_start = d
            if cur > best:
                best, best_start, best_end = cur, cur_start, d
        else:
            cur = 0
            cur_start = None

    # El dia de hoy sin commits no rompe el streak todavia (aun no acaba).
    tail = 0
    for d in reversed(days):
        if day_counts[d] > 0:
            tail += 1
        elif tail or d != days[-1]:
            break
    rng = ""
    if best_start:
        f = datetime.fromisoformat(best_start).strftime("%d %b %Y")
        t = datetime.fromisoformat(best_end).strftime("%d %b %Y")
        rng = f"{f} - {t}" if best > 1 else f
    return tail, best, rng


def collect(login: str) -> dict:
    u = gql(PROFILE_Q, login=login)["user"]
    cc = u["contributionsCollection"]
    cal = cc["contributionCalendar"]

    repos = u["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])

    sizes, colors = Counter(), {}
    for n in repos["nodes"]:
        for e in n["languages"]["edges"]:
            sizes[e["node"]["name"]] += e["size"]
            colors[e["node"]["name"]] = e["node"]["color"] or "#8A97B1"

    # Contribuciones de por vida: la API solo da ventanas de <=1 ano.
    created = datetime.fromisoformat(u["createdAt"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    lifetime = 0
    all_days: dict = {}
    private = cc["restrictedContributionsCount"]
    for year in range(created.year, now.year + 1):
        frm = max(created, datetime(year, 1, 1, tzinfo=timezone.utc))
        to = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        if frm >= to:
            continue
        y = gql(YEAR_Q, login=login, **{"from": frm.isoformat(), "to": to.isoformat()})
        yc = y["user"]["contributionsCollection"]
        lifetime += yc["contributionCalendar"]["totalContributions"]
        private = max(private, yc["restrictedContributionsCount"])
        for w in yc["contributionCalendar"]["weeks"]:
            for day in w["contributionDays"]:
                if day["date"] <= now.strftime("%Y-%m-%d"):
                    all_days[day["date"]] = day["contributionCount"]

    by_year: dict = {}
    for day, n in all_days.items():
        dt = date.fromisoformat(day)
        iso = dt.isocalendar()
        by_year.setdefault(dt.year, {})
        by_year[dt.year][iso[1]] = by_year[dt.year].get(iso[1], 0) + n
    years = [(y, by_year.get(y, {}), sum(by_year.get(y, {}).values()))
             for y in range(created.year, now.year + 1)]

    cur_streak, best_streak, best_range = streaks(all_days)
    active = sum(1 for v in all_days.values() if v > 0)

    days = [d for w in cal["weeks"] for d in w["contributionDays"]]

    return {
        "login": login,
        "since": created.year,
        "lifetime": lifetime,
        "year_total": cal["totalContributions"],
        "private": private,
        "cur_streak": cur_streak,
        "best_streak": best_streak,
        "best_range": best_range,
        "active_days": active,
        "commits": cc["totalCommitContributions"],
        "prs": u["pullRequests"]["totalCount"],
        "repos": repos["totalCount"],
        "stars": stars,
        "followers": u["followers"]["totalCount"],
        "langs": sizes.most_common(6),
        "lang_colors": colors,
        "lang_total": sum(sizes.values()) or 1,
        "weeks": cal["weeks"],
        "years": years,
        "max_day": max((d["contributionCount"] for d in days), default=0),
        "generated": now.strftime("%d %b %Y"),
    }


def human(n: int) -> str:
    return f"{n:,}"


def esc(s: str) -> str:
    """XML-escape. Los nombres de lenguaje vienen de la API (p. ej. "F#", "C++")."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------- STATS card
def stats_card(t: dict, d: dict) -> str:
    W, H = 600, 190
    metrics = [
        (human(d["lifetime"]), "contributions", f"since {d['since']}"),
        (human(d["prs"]), "pull requests", "merged & open"),
        (human(d["repos"]), "repositories", f"{human(d['stars'])} stars"),
    ]
    sub = [
        (human(d["cur_streak"]), "day streak"),
        (human(d["best_streak"]), "best streak"),
        (human(d["active_days"]), "active days"),
    ]

    cells = []
    for i, (num, label, foot) in enumerate(metrics):
        x = 46 + i * 176
        cells.append(f"""
  <g class="m" style="animation-delay:{0.10 + i * 0.12:.2f}s">
    <text x="{x}" y="86" font-family="@MONO@" font-size="38" font-weight="700"
          fill="url(#st_shim)" letter-spacing="-1">{num}</text>
    <text x="{x}" y="108" font-family="@FONT@" font-size="12.5" font-weight="600"
          fill="@TEXT@" letter-spacing="0.2">{esc(label)}</text>
    <text x="{x}" y="126" font-family="@FONT@" font-size="11" fill="@MUTED@">{esc(foot)}</text>
  </g>""")

    chips = []
    for i, (num, label) in enumerate(sub):
        x = 46 + i * 176
        chips.append(f"""
  <g class="m" style="animation-delay:{0.46 + i * 0.10:.2f}s">
    <rect x="{x - 10}" y="146" width="150" height="26" rx="13" fill="@SURFACE@" opacity="0.75"/>
    <text x="{x + 2}" y="163.5" font-family="@MONO@" font-size="12" font-weight="700" fill="@CYAN@">{num}</text>
    <text x="{x + 2 + 9 * len(num)}" y="163.5" font-family="@FONT@" font-size="11" fill="@MUTED@">{label}</text>
  </g>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="GitHub stats de {d['login']}">
  <defs>
    <linearGradient id="st_shim" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="@VIOLET@"/>
      <stop offset="35%"  stop-color="@BLUE@"/>
      <stop offset="70%"  stop-color="@CYAN@"/>
      <stop offset="100%" stop-color="@MAGENTA@"/>
      <animateTransform attributeName="gradientTransform" type="translate"
        values="-0.5 0; 0.5 0; -0.5 0" dur="11s" repeatCount="indefinite"/>
    </linearGradient>
    <linearGradient id="st_rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="@VIOLET@"/>
      <stop offset="60%" stop-color="@CYAN@"/>
      <stop offset="100%" stop-color="@CYAN@" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .m {{ opacity:0; animation: st_rise .6s cubic-bezier(.2,.7,.3,1) forwards; }}
    @keyframes st_rise {{ from {{opacity:0; transform:translateY(9px);}} to {{opacity:1; transform:none;}} }}
  </style>

  <rect width="{W}" height="{H}" rx="16" fill="@BG2@"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="@FAINT@"/>

  <text x="46" y="42" font-family="@MONO@" font-size="11.5" font-weight="700"
        fill="@MUTED@" letter-spacing="2.4">GITHUB STATS</text>
  <rect x="46" y="52" width="200" height="2" rx="1" fill="url(#st_rule)"/>
  {''.join(cells)}
  {''.join(chips)}
</svg>
"""


# ---------------------------------------------------------------- LANGS card
def langs_card(t: dict, d: dict) -> str:
    W, H = 600, 190
    total = d["lang_total"]
    top = d["langs"]
    shown = sum(s for _, s in top)
    segs, rows = [], []

    x = 46.0
    bar_w = W - 92
    for i, (name, size) in enumerate(top):
        pct = size / total
        w = max(bar_w * pct, 2.0)
        color = d["lang_colors"][name]
        segs.append(
            f'<rect x="{x:.1f}" y="70" width="{w:.1f}" height="12" fill="{color}">'
            f'<animate attributeName="height" from="0" to="12" dur=".5s" begin="{0.1 + i * 0.07:.2f}s" fill="freeze"/>'
            f'<animate attributeName="y" from="82" to="70" dur=".5s" begin="{0.1 + i * 0.07:.2f}s" fill="freeze"/>'
            f"</rect>"
        )
        x += w

    other = total - shown
    if other > 0:
        w = max(bar_w * (other / total), 2.0)
        segs.append(f'<rect x="{x:.1f}" y="70" width="{w:.1f}" height="12" fill="@FAINT@"/>')

    for i, (name, size) in enumerate(top):
        col, row = i % 2, i // 2
        cx = 46 + col * 262
        cy = 116 + row * 25
        color = d["lang_colors"][name]
        pct = size / total * 100
        rows.append(f"""
  <g class="l" style="animation-delay:{0.28 + i * 0.07:.2f}s">
    <circle cx="{cx + 5}" cy="{cy - 4}" r="5" fill="{color}"/>
    <text x="{cx + 18}" y="{cy}" font-family="@FONT@" font-size="12" fill="@TEXT@">{esc(name)}</text>
    <text x="{cx + 232}" y="{cy}" text-anchor="end" font-family="@MONO@" font-size="11.5"
          font-weight="700" fill="@MUTED@">{pct:.1f}%</text>
  </g>""")

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="Lenguajes mas usados de {d['login']}">
  <defs>
    <linearGradient id="lg_rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="@VIOLET@"/>
      <stop offset="60%" stop-color="@CYAN@"/>
      <stop offset="100%" stop-color="@CYAN@" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="lg_clip"><rect x="46" y="70" width="{W - 92}" height="12" rx="6"/></clipPath>
  </defs>
  <style>
    .l {{ opacity:0; animation: lg_in .5s ease-out forwards; }}
    @keyframes lg_in {{ from {{opacity:0; transform:translateX(-6px);}} to {{opacity:1; transform:none;}} }}
  </style>

  <rect width="{W}" height="{H}" rx="16" fill="@BG2@"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="@FAINT@"/>

  <text x="46" y="42" font-family="@MONO@" font-size="11.5" font-weight="700"
        fill="@MUTED@" letter-spacing="2.4">MOST USED LANGUAGES</text>
  <rect x="46" y="52" width="200" height="2" rx="1" fill="url(#lg_rule)"/>

  <g clip-path="url(#lg_clip)">
    <rect x="46" y="70" width="{W - 92}" height="12" fill="@SURFACE@"/>
    {''.join(segs)}
  </g>
  {''.join(rows)}
</svg>
"""


# ---------------------------------------------------------------- ACTIVITY heatmap
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def activity_card(theme: str, t: dict, d: dict) -> str:
    """Heatmap multi-ano: una fila por ano, una celda por semana ISO.

    A escala de semana la actividad real se lee; a escala de dia un perfil
    cuyo trabajo vive en repos privados se ve vacio aunque no lo este.
    """
    ramp = LEVELS[theme]
    years = d["years"]           # [(ano, {semana: total}, total_ano), ...]
    cell, gap = 16, 4
    pitch = cell + gap
    pad_l, pad_t = 62, 88
    cols = 53
    W = pad_l + cols * pitch + 40
    H = pad_t + len(years) * pitch + 54

    peak = max((n for _, wk, _ in years for n in wk.values()), default=1) or 1

    def level(n: int) -> int:
        if n == 0:
            return 0
        return min(4, 1 + int(3 * (n - 1) / max(peak - 1, 1)))

    cells, labels = [], []
    for yi, (year, wk, ytot) in enumerate(years):
        y = pad_t + yi * pitch
        labels.append(
            f'<text x="{pad_l - 12}" y="{y + cell - 4}" text-anchor="end" font-family="@MONO@" '
            f'font-size="11" font-weight="700" fill="@MUTED@">{year}</text>'
        )
        labels.append(
            f'<text x="{pad_l + cols * pitch + 10}" y="{y + cell - 4}" font-family="@MONO@" '
            f'font-size="10.5" fill="@MUTED@">{ytot}</text>'
        )
        for w in range(1, cols + 1):
            n = wk.get(w, 0)
            x = pad_l + (w - 1) * pitch
            delay = 0.12 + w * 0.010 + yi * 0.04
            cells.append(
                f'<rect class="c" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" '
                f'fill="{ramp[level(n)]}" style="animation-delay:{delay:.2f}s">'
                f'<title>{year} W{w}: {n}</title></rect>'
            )

    for w, name in ((1, "Jan"), (10, "Mar"), (19, "May"), (27, "Jul"), (36, "Sep"), (45, "Nov")):
        labels.append(
            f'<text x="{pad_l + (w - 1) * pitch}" y="{pad_t - 12}" font-family="@FONT@" '
            f'font-size="10.5" fill="@MUTED@">{name}</text>'
        )

    ly = pad_t + len(years) * pitch + 22
    lx = pad_l
    legend = [f'<text x="{lx}" y="{ly + 11}" font-family="@FONT@" font-size="10.5" fill="@MUTED@">Less</text>']
    for i, c in enumerate(ramp):
        legend.append(f'<rect x="{lx + 36 + i * 20}" y="{ly}" width="{cell}" height="{cell}" rx="4" fill="{c}"/>')
    legend.append(f'<text x="{lx + 36 + 5 * 20 + 4}" y="{ly + 11}" font-family="@FONT@" '
                  f'font-size="10.5" fill="@MUTED@">More</text>')
    legend.append(f'<text x="{W - 40}" y="{ly + 11}" text-anchor="end" font-family="@FONT@" '
                  f'font-size="10.5" fill="@MUTED@">contributions per week</text>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"
     role="img" aria-label="Contribuciones semanales de {esc(d['login'])} por ano">
  <defs>
    <linearGradient id="ac_rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="@VIOLET@"/>
      <stop offset="60%" stop-color="@CYAN@"/>
      <stop offset="100%" stop-color="@CYAN@" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>
    .c {{ opacity:0; animation: ac_pop .45s ease-out forwards; }}
    @keyframes ac_pop {{ from {{opacity:0; transform:scale(.4);}} to {{opacity:1; transform:none;}} }}
    rect.c {{ transform-box: fill-box; transform-origin: center; }}
  </style>

  <rect width="{W}" height="{H}" rx="16" fill="@BG2@"/>
  <rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="15.5" fill="none" stroke="@FAINT@"/>

  <text x="{pad_l}" y="38" font-family="@MONO@" font-size="11.5" font-weight="700"
        fill="@MUTED@" letter-spacing="2.4">CONTRIBUTION ACTIVITY</text>
  <rect x="{pad_l}" y="48" width="220" height="2" rx="1" fill="url(#ac_rule)"/>
  <text x="{W - 40}" y="38" text-anchor="end" font-family="@FONT@" font-size="11.5" fill="@MUTED@">
    <tspan font-family="@MONO@" font-weight="700" fill="@CYAN@">{human(d['lifetime'])}</tspan> since {d['since']}
  </text>

  {''.join(labels)}
  {''.join(cells)}
  {''.join(legend)}
</svg>
"""


# ---------------------------------------------------------------- build
STATE = OUT / ".stats.json"

# Las contribuciones acumuladas nunca bajan. Si el API devuelve mucho menos
# que la ultima corrida buena es un glitch suyo (pasa: alterna entre contar
# y no contar la actividad privada), no una realidad que debamos publicar.
REGRESSION_FLOOR = 0.90


def guard(d: dict) -> bool:
    prev = {}
    if STATE.exists():
        try:
            prev = json.loads(STATE.read_text())
        except json.JSONDecodeError:
            prev = {}

    for key in ("lifetime", "prs", "repos"):
        old = prev.get(key)
        if old and d[key] < old * REGRESSION_FLOOR:
            print(f"  ! {key}: {d[key]} < {old} (ultima corrida buena). "
                  f"El API devolvio datos incompletos; no se regenera nada.")
            return False

    STATE.write_text(json.dumps(
        {k: d[k] for k in ("lifetime", "year_total", "private", "prs",
                           "repos", "stars", "followers", "active_days")},
        indent=2) + "\n", encoding="utf-8")
    return True


if __name__ == "__main__":
    data = collect(USER)
    print(f"  {USER}: {data['lifetime']:,} lifetime · {data['year_total']} past year "
          f"· {data['repos']} repos · {data['stars']} stars")

    if not guard(data):
        sys.exit(0)

    builders = {
        "stats": lambda th, tk: stats_card(tk, data),
        "langs": lambda th, tk: langs_card(tk, data),
        "activity": lambda th, tk: activity_card(th, tk, data),
    }
    for name, fn in builders.items():
        for theme, tokens in THEMES.items():
            svg = fill(fn(theme, tokens), tokens)
            path = OUT / f"{name}-{theme}.svg"
            path.write_text(svg, encoding="utf-8")
            print(f"  ✓ {path.relative_to(OUT.parent)}  ({len(svg) / 1024:.1f} KB)")
