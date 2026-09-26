#!/usr/bin/env python3
"""
Take a Break — generador de frames para Figma.

Cada pantalla se genera como un SVG de 360x800 (dp de Android, ventana compacta).
Arrastrar los .svg de `screens/` y `boards/` a Figma crea un frame por archivo con
capas vectoriales y texto editable (Figma trae Bricolage Grotesque y DM Sans).

Uso:
    python build.py            # genera screens/, boards/ e index.html
    python build.py --png      # además exporta png/ con Edge headless (para LaTeX)
"""
import html
import math
import os
import random
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 360, 800

# ---------------------------------------------------------------- tokens ----
C = dict(
    forest="#0B3B2C",   # superficie de marca / hero
    green="#136B4A",    # primario sobre claro
    lime="#E4F56A",     # acento: puntos, CTA sobre oscuro
    cream="#F7F3EC",    # fondo
    paper="#FFFFFF",    # tarjetas
    ink="#16211C",      # texto
    muted="#5F6B64",    # texto secundario
    line="#E7E1D6",     # bordes / divisores
    skel="#ECE6DA",     # skeleton
    pink="#FFD3F2", pinkInk="#6A1B54",
    sky="#DCEBFF", skyInk="#1E3A6B",
    sand="#FFEBC2", sandInk="#6B4A0E",
    mint="#DDF2E6", mintInk="#136B4A",
    lilac="#ECE3FF", lilacInk="#4B2E83",
    amber="#C98A12", amberBg="#FFF3D6",
    red="#C2412D", redBg="#FDE7E2",
    blue="#2F6BFF",
)
DISPLAY = "Bricolage Grotesque, sans-serif"
BODY = "DM Sans, sans-serif"
MONO = "JetBrains Mono, monospace"
FONTS = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800"
         "&family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@700&display=swap")

# Datos de ejemplo (coherentes entre pantallas: saldo 340 pts, meta = clase de yoga 400 pts)
R = {
    "cuervo": dict(icon="coffee", bg=C["pink"], fg=C["pinkInk"], title="Café + medialuna",
                   biz="Cuervo Café", dist="350 m", barrio="Palermo", pts=120),
    "nube": dict(icon="icecream", bg=C["sky"], fg=C["skyInk"], title="Cucurucho doble",
                 biz="Heladería Nube", dist="600 m", barrio="Villa Crespo", pts=150),
    "bosque": dict(icon="book", bg=C["sand"], fg=C["sandInk"], title="15% off en libros",
                   biz="Bosque Libros", dist="900 m", barrio="Palermo", pts=300),
    "prana": dict(icon="leaf", bg=C["mint"], fg=C["mintInk"], title="Clase de yoga",
                  biz="Estudio Prana", dist="1,2 km", barrio="Chacarita", pts=400),
    "lupa": dict(icon="bag", bg=C["lilac"], fg=C["lilacInk"], title="Pan de masa madre",
                 biz="Panadería Lupa", dist="1,4 km", barrio="Colegiales", pts=200),
    "ombu": dict(icon="coffee", bg=C["lilac"], fg=C["lilacInk"], title="Brunch para dos",
                 biz="Casa Ombú", dist="1,8 km", barrio="Belgrano", pts=600),
}
BALANCE = 340


# ------------------------------------------------------------ primitives ----
def esc(s):
    return html.escape(str(s), quote=True)


def rect(x, y, w, h, r=0, fill="none", stroke=None, sw=1, opacity=None, dash=None):
    a = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"'
    if stroke:
        a += f' stroke="{stroke}" stroke-width="{sw}"'
    if dash:
        a += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return a + "/>"


def circle(cx, cy, r, fill="none", stroke=None, sw=1, opacity=None):
    a = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'
    if stroke:
        a += f' stroke="{stroke}" stroke-width="{sw}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return a + "/>"


def line(x1, y1, x2, y2, stroke=C["line"], sw=1, dash=None, opacity=None):
    a = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}" stroke-linecap="round"'
    if dash:
        a += f' stroke-dasharray="{dash}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return a + "/>"


def text(x, y, s, size=14, weight=400, fill=C["ink"], family=BODY, anchor="start",
         lh=None, ls=None, opacity=None):
    """Texto con baseline en y. Los saltos de línea (\\n) generan tspans."""
    lines = str(s).split("\n")
    lh = lh or round(size * 1.35)
    a = (f'x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
         f'fill="{fill}" text-anchor="{anchor}"')
    if ls is not None:
        a += f' letter-spacing="{ls}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    if len(lines) == 1:
        return f"<text {a}>{esc(s)}</text>"
    spans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{esc(l)}</tspan>'
                    for i, l in enumerate(lines))
    return f"<text {a}>{spans}</text>"


def rich(x, y, lines, size, weight=800, family=DISPLAY, anchor="start", lh=None, ls=None):
    """Texto multicolor: lines = [[(txt, fill[, size[, weight]]), ...], ...]."""
    lh = lh or round(size * 1.08)
    a = (f'x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
         f'text-anchor="{anchor}"')
    if ls is not None:
        a += f' letter-spacing="{ls}"'
    out = [f"<text {a}>"]
    for i, ln in enumerate(lines):
        for j, seg in enumerate(ln):
            extra = ""
            if len(seg) > 2:
                extra += f' font-size="{seg[2]}"'
            if len(seg) > 3:
                extra += f' font-weight="{seg[3]}"'
            pos = f' x="{x}" dy="{0 if i == 0 else lh}"' if j == 0 else ""
            out.append(f'<tspan{pos} fill="{seg[1]}"{extra}>{esc(seg[0])}</tspan>')
    out.append("</text>")
    return "".join(out)


def g(content, name=None, transform=None, opacity=None):
    a = ""
    if name:
        a += f' id="{esc(name)}"'
    if transform:
        a += f' transform="{transform}"'
    if opacity is not None:
        a += f' opacity="{opacity}"'
    return f"<g{a}>{''.join(content) if isinstance(content, list) else content}</g>"


def arc(cx, cy, r, frac):
    frac = max(0.001, min(frac, 0.9999))
    a0 = -math.pi / 2
    a1 = a0 + 2 * math.pi * frac
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    return f"M{x0:.1f} {y0:.1f} A{r} {r} 0 {1 if frac > 0.5 else 0} 1 {x1:.1f} {y1:.1f}"


def tw(s, size, k=0.56):
    """Ancho aproximado de un texto (para chips)."""
    return len(str(s)) * size * k


# ---------------------------------------------------------------- iconos ----
# Trazos de 2px en grilla de 24 — línea redondeada, coherente con un look minimalista.
IC = {
    "home": '<path d="M4 10.5 12 4l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5.5h-5V20H5a1 1 0 0 1-1-1z"/>',
    "pin": '<path d="M12 21s-6.5-5.8-6.5-11a6.5 6.5 0 0 1 13 0c0 5.2-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
    "chart": '<path d="M5 19v-6M10 19V6M15 19v-4M20 19V9"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5c.8-3.8 3.9-6 7.5-6s6.7 2.2 7.5 6"/>',
    "bell": '<path d="M6 16.5V11a6 6 0 0 1 12 0v5.5l1.5 1.5h-15z"/><path d="M10 21h4"/>',
    "coffee": '<path d="M4 9h12v4.5A5.5 5.5 0 0 1 10.5 19h-1A5.5 5.5 0 0 1 4 13.5z"/><path d="M16 10.5h1.5a2.5 2.5 0 0 1 0 5H16"/><path d="M8 3.5V6M12 3.5V6"/>',
    "book": '<path d="M5 19.5v-14A2.5 2.5 0 0 1 7.5 3H19v14H7.5A2.5 2.5 0 0 0 5 19.5 2.5 2.5 0 0 0 7.5 22H19"/>',
    "leaf": '<path d="M5 19C5 10 11 5 20 4c0 9-5 15-13.5 15z"/><path d="M5 19l8-8"/>',
    "icecream": '<path d="M7.5 11a4.5 4.5 0 1 1 9 0z"/><path d="M8 11l4 10 4-10"/>',
    "bag": '<path d="M5 8h14l-1.2 12H6.2z"/><path d="M9 8V6.5a3 3 0 0 1 6 0V8"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "chev": '<path d="M9.5 6l6 6-6 6"/>',
    "chevdown": '<path d="M6 9.5l6 6 6-6"/>',
    "back": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "cloudoff": '<path d="M7.5 18.5h9.5a3.8 3.8 0 0 0 1.3-7.4 6 6 0 0 0-10.9-2.4A4.9 4.9 0 0 0 7.5 18.5z"/><path d="M3.5 3.5l17 17"/>',
    "locate": '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
    "flame": '<path d="M12 3c.8 3.6 5.5 5.4 5.5 10.3a5.5 5.5 0 0 1-11 .2c0-2.6 1.4-4 2.6-5.2.2 1.7 1 2.8 2.2 3C11.3 8 11 5.6 12 3z"/>',
    "moon": '<path d="M19.5 14.5A7.5 7.5 0 0 1 9.5 4.5a7.5 7.5 0 1 0 10 10z"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "ticket": '<path d="M3.5 7.5h17v3a1.8 1.8 0 0 0 0 3.6v3.4h-17v-3.4a1.8 1.8 0 0 0 0-3.6z"/><path d="M14.5 8.5v1.5M14.5 12v1M14.5 15v1.5"/>',
    "shield": '<path d="M12 3l7 2.8v5.4c0 4.8-3 8.2-7 9.8-4-1.6-7-5-7-9.8V5.8z"/>',
    "shieldcheck": '<path d="M12 3l7 2.8v5.4c0 4.8-3 8.2-7 9.8-4-1.6-7-5-7-9.8V5.8z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
    "shieldx": '<path d="M12 3l7 2.8v5.4c0 4.8-3 8.2-7 9.8-4-1.6-7-5-7-9.8V5.8z"/><path d="M9.5 9.5l5 5M14.5 9.5l-5 5"/>',
    "alert": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V13M12 16.3v.2"/>',
    "info": '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.2"/>',
    "mail": '<rect x="3.5" y="5.5" width="17" height="13" rx="2.5"/><path d="M4 7l8 6 8-6"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
    "refresh": '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3"/><path d="M19.5 4.5V9H15"/>',
    "undo": '<path d="M9 14 4.5 9.5 9 5"/><path d="M4.5 9.5H14a5.5 5.5 0 0 1 0 11h-3"/>',
    "flag": '<path d="M6 21V4M6 4.5h11l-2.5 4 2.5 4H6"/>',
    "target": '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1" fill="currentColor"/>',
    "logout": '<path d="M14 4.5h4.5v15H14M9.5 8l-4 4 4 4M5.5 12h9"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "finger": '<path d="M8.5 20c-1.2-2-1.8-4.3-1.8-6.7a5.3 5.3 0 0 1 10.6 0"/><path d="M12 13.3c0 2.8.8 5.3 2.3 7.2"/><path d="M5 9.5A8 8 0 0 1 19 9"/><path d="M9.6 17.5c-.4-1.3-.6-2.7-.6-4.2a3 3 0 0 1 6 0c0 1 .1 2 .3 3"/>',
    "phone": '<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 18h2"/>',
    "map": '<path d="M9 4.5l-5 2v13l5-2 6 2 5-2v-13l-5 2z"/><path d="M9 4.5v13M15 6.5v13"/>',
    "list": '<path d="M9 7h11M9 12h11M9 17h11M4.5 7h.5M4.5 12h.5M4.5 17h.5"/>',
    "wifi": '<path d="M2.5 9a14 14 0 0 1 19 0M5.5 12.5a9.5 9.5 0 0 1 13 0M8.8 16a5 5 0 0 1 6.4 0"/><circle cx="12" cy="19.2" r=".6" fill="currentColor"/>',
    "store": '<path d="M4 9.5 5.5 4h13L20 9.5M4 9.5h16M4 9.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0M5.5 12.5V20h13v-7.5"/><path d="M10 20v-4.5h4V20"/>',
    "calendar": '<rect x="4" y="5.5" width="16" height="15" rx="2.5"/><path d="M4 10h16M8.5 3.5v4M15.5 3.5v4"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "share": '<path d="M12 15V4M7.5 8.5 12 4l4.5 4.5M5 13v6.5h14V13"/>',
}


def icon(name, x, y, size=24, color=C["ink"], sw=2):
    s = size / 24
    body = IC[name].replace("currentColor", color)
    return (f'<g transform="translate({x} {y}) scale({s:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{body}</g>')


def icon_tile(x, y, name, bg, fg, size=48, r=16, isz=24):
    o = (size - isz) / 2
    return rect(x, y, size, size, r, bg) + icon(name, x + o, y + o, isz, fg)


# ------------------------------------------------------------ componentes ----
def status_bar(dark=False):
    c = "#FFFFFF" if dark else C["ink"]
    out = [text(24, 17, "9:41", 13, 600, c)]
    for i, hgt in enumerate([4, 6, 8, 10]):
        out.append(rect(290 + i * 4, 14 - hgt, 2.5, hgt, 1, c))
    out.append(icon("wifi", 306, 3, 14, c, 2.4))
    out.append(rect(324, 6, 20, 10, 3, "none", c, 1.4))
    out.append(rect(326, 8, 13, 6, 1.5, c))
    return g(out, "Status bar")


def gesture_bar(dark=False):
    return rect(140, 788, 80, 4, 2, "#FFFFFF" if dark else C["ink"], opacity=0.35 if not dark else 0.6)


def logo_mark(cx, cy, r, bg=C["lime"], fg=C["forest"]):
    bw, bh = r * 0.2, r * 0.82
    return g([circle(cx, cy, r, bg),
              rect(cx - r * 0.3 - bw / 2, cy - bh / 2, bw, bh, bw / 2, fg),
              rect(cx + r * 0.3 - bw / 2, cy - bh / 2, bw, bh, bw / 2, fg)], "Logo")


def wordmark(x, y, size, fill=C["forest"], anchor="start"):
    return text(x, y, "take a break", size, 800, fill, DISPLAY, anchor, ls=-0.5)


def header_logo(dark=False, avatar=True):
    out = [logo_mark(36, 52, 14), wordmark(58, 59, 20, "#FFFFFF" if dark else C["forest"])]
    if avatar:
        out += [circle(316, 52, 20, C["pink"]), text(316, 58, "M", 16, 700, C["pinkInk"], BODY, "middle")]
    return g(out, "Top bar")


def top_bar(title, back=True, dark=False, right=None):
    c = "#FFFFFF" if dark else C["ink"]
    out = []
    if back:
        out += [circle(44, 56, 24, "none"), icon("back", 32, 44, 24, c)]
    out.append(text(80 if back else 20, 63, title, 22, 800, c, DISPLAY))
    if right:
        out.append(right)
    return g(out, "Top bar")


def nav(active):
    items = [("home", "Inicio"), ("pin", "Explorar"), ("chart", "Actividad")]
    out = [rect(0, 720, W, 80, 0, C["paper"]), line(0, 720, W, 720, C["line"])]
    for i, (ic, label) in enumerate(items):
        cx = 60 + i * 120
        on = i == active
        if on:
            out.append(rect(cx - 32, 730, 64, 32, 16, C["lime"]))
        out.append(icon(ic, cx - 12, 734, 24, C["forest"] if on else C["muted"]))
        out.append(text(cx, 780, label, 12, 700 if on else 500, C["forest"] if on else C["muted"], BODY, "middle"))
    out.append(gesture_bar())
    return g(out, "Bottom navigation")


def button(x, y, w, label, kind="primary", h=56, ic=None, size=16):
    styles = {
        "primary": (C["forest"], None, "#FFFFFF"),
        "lime": (C["lime"], None, C["forest"]),
        "white": (C["paper"], None, C["forest"]),
        "outline": ("none", C["forest"], C["forest"]),
        "outline-light": ("none", "#FFFFFF", "#FFFFFF"),
        "ghost": ("none", None, C["forest"]),
        "disabled": (C["skel"], None, "#A39E93"),
        "danger": ("none", None, C["red"]),
    }
    fill, stroke, fg = styles[kind]
    out = [rect(x, y, w, h, h / 2, fill, stroke, 1.5)]
    cy = y + h / 2
    if ic:
        lw = tw(label, size, 0.52)
        ix = x + w / 2 - (lw + 32) / 2
        out.append(icon(ic, ix, cy - 11, 22, fg))
        out.append(text(ix + 32, cy + size * 0.35, label, size, 700, fg, BODY))
    else:
        out.append(text(x + w / 2, cy + size * 0.35, label, size, 700, fg, BODY, "middle"))
    return g(out, f"Button/{kind}")


def chip(x, y, label, fill, fg, h=28, size=13, ic=None, stroke=None, weight=700, anchor="start"):
    w = tw(label, size, 0.56) + 24 + (20 if ic else 0)
    if anchor == "end":
        x = x - w
    elif anchor == "middle":
        x = x - w / 2
    out = [rect(x, y, w, h, h / 2, fill, stroke, 1)]
    tx = x + 12
    if ic:
        out.append(icon(ic, x + 9, y + h / 2 - 8, 16, fg, 2.2))
        tx += 20
    out.append(text(tx, y + h / 2 + size * 0.35, label, size, weight, fg, BODY))
    return g(out, "Chip"), w


def pts_chip(xr, y, pts, affordable=True, h=28):
    if affordable:
        return chip(xr, y, f"{pts} pts", C["lime"], C["forest"], h, anchor="end")[0]
    return chip(xr, y, f"{pts} pts", C["paper"], C["muted"], h, stroke=C["line"], anchor="end")[0]


def progress(x, y, w, frac, h=10, bg=C["skel"], fg=C["green"]):
    return g([rect(x, y, w, h, h / 2, bg), rect(x, y, max(h, w * frac), h, h / 2, fg)], "Progress")


def reward_row(y, key, sub=None, card=True, x=20, w=320, balance=BALANCE, h=72, right=None):
    r = R[key]
    out = []
    if card:
        out.append(rect(x, y, w, h, 20, C["paper"], C["line"]))
    out.append(icon_tile(x + 12, y + (h - 48) / 2, r["icon"], r["bg"], r["fg"]))
    out.append(text(x + 72, y + h / 2 - 3, r["title"], 15, 700, C["ink"]))
    out.append(text(x + 72, y + h / 2 + 16, sub or f'{r["biz"]} · {r["dist"]}', 13, 400, C["muted"]))
    out.append(right if right is not None else pts_chip(x + w - 12, y + h / 2 - 14, r["pts"], r["pts"] <= balance))
    if not card:
        out.append(line(x + 72, y + h, x + w, y + h, C["line"]))
    return g(out, f'Reward row/{r["biz"]}')


def banner(y, msg, ic="cloudoff", fg=C["sandInk"], bg=C["amberBg"], x=20, w=320, h=44):
    return g([rect(x, y, w, h, 14, bg), icon(ic, x + 14, y + h / 2 - 10, 20, fg),
              text(x + 44, y + h / 2 + 5, msg, 13, 600, fg)], "Banner")


def section_title(y, title, action=None):
    out = [text(20, y, title, 18, 800, C["ink"], DISPLAY)]
    if action:
        out.append(text(340, y, action, 14, 700, C["green"], BODY, "end"))
    return g(out, "Section title")


def fake_shadow(x, y, w, h, r):
    return rect(x, y + 3, w, h, r, C["forest"], opacity=0.08)


def map_art(sid, x, y, w, h, pins, me=None, selected=None, r=0):
    cid = f"{sid}-mapclip"
    P = lambda fx, fy: (x + fx * w, y + fy * h)
    out = [f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/></clipPath>',
           f'<g clip-path="url(#{cid})">', rect(x, y, w, h, r, "#EAE4D6")]
    # agua y parques
    out.append(f'<path d="M{x} {y + h * .78} C {x + w * .18} {y + h * .70}, {x + w * .28} {y + h * .92}, {x + w * .42} {y + h} L {x} {y + h} Z" fill="#CFE0EA"/>')
    px, py = P(.50, .46)
    out.append(rect(px, py, w * .24, h * .17, 18, "#CDE4C2"))
    px, py = P(.04, .08)
    out.append(rect(px, py, w * .14, h * .12, 14, "#CDE4C2"))
    for (a, b, c_, d, sw) in [(-.1, .27, 1.1, .08, 13), (.16, -.1, .44, 1.1, 13), (-.1, .72, 1.1, .88, 13),
                              (.78, -.1, .92, 1.1, 13), (0, .47, 1, .40, 6), (.30, 0, .24, 1, 6),
                              (.62, 0, .58, 1, 6), (0, .60, 1, .58, 6), (0, .12, 1, .20, 5)]:
        x1, y1 = P(a, b)
        x2, y2 = P(c_, d)
        out.append(line(f"{x1:.1f}", f"{y1:.1f}", f"{x2:.1f}", f"{y2:.1f}", "#FFFFFF", sw))
    if me:
        mx, my = P(*me)
        out += [circle(mx, my, 28, C["blue"], opacity=0.14), circle(mx, my, 9, C["blue"], "#FFFFFF", 3)]
    for key, fx, fy in pins:
        cx, cy = P(fx, fy)
        rr = R[key]
        if key == selected:
            label = f'{rr["biz"]} · {rr["pts"]} pts'
            bw = tw(label, 13, 0.55) + 24
            out += [fake_shadow(cx - bw / 2, cy - 64, bw, 32, 16),
                    rect(cx - bw / 2, cy - 64, bw, 32, 16, C["paper"]),
                    text(cx, cy - 43, label, 13, 700, C["ink"], BODY, "middle"),
                    circle(cx, cy, 22, C["lime"], C["forest"], 3), icon(rr["icon"], cx - 11, cy - 11, 22, C["forest"])]
        else:
            out += [circle(cx, cy, 17, C["forest"], "#FFFFFF", 3), icon(rr["icon"], cx - 9, cy - 9, 18, C["lime"])]
    out.append("</g>")
    return g(out, "Map")


def qr(x, y, size, seed=7):
    n = 25
    c = size / n
    rnd = random.Random(seed)
    out = [rect(x, y, size, size, 0, C["paper"])]

    def finder(i, j):
        return [rect(x + i * c, y + j * c, 7 * c, 7 * c, c, C["forest"]),
                rect(x + (i + 1) * c, y + (j + 1) * c, 5 * c, 5 * c, c * .6, C["paper"]),
                rect(x + (i + 2) * c, y + (j + 2) * c, 3 * c, 3 * c, c * .4, C["forest"])]
    zones = [(0, 0), (n - 7, 0), (0, n - 7)]
    for i in range(n):
        for j in range(n):
            if any(zx - 1 <= i <= zx + 7 and zy - 1 <= j <= zy + 7 for zx, zy in zones):
                continue
            if rnd.random() < 0.48:
                out.append(rect(f"{x + i * c:.2f}", f"{y + j * c:.2f}", f"{c:.2f}", f"{c:.2f}", 0.8, C["forest"]))
    for zx, zy in zones:
        out += finder(zx, zy)
    return g(out, "QR")


def sheet(y, h=None, fill=C["paper"], handle=True):
    h = h or (H - y + 40)
    out = [rect(0, y, W, h, 28, fill)]
    if handle:
        out.append(rect(162, y + 10, 36, 4, 2, C["line"] if fill != C["cream"] else "#D8D1C4"))
    return g(out, "Bottom sheet")


def list_row(y, ic, title, value=None, chevron=True, x=20, w=320, h=56, fg=C["ink"], toggle=None, divider=True, value_color=None):
    out = [icon(ic, x + 16, y + h / 2 - 11, 22, fg if fg != C["ink"] else C["green"])]
    out.append(text(x + 52, y + h / 2 + 5, title, 15, 600, fg))
    rx = x + w - 16
    if chevron:
        out.append(icon("chev", rx - 18, y + h / 2 - 9, 18, C["muted"]))
        rx -= 24
    if toggle is not None:
        tx = x + w - 16 - 52
        out += [rect(tx, y + h / 2 - 16, 52, 32, 16, C["green"] if toggle else C["skel"]),
                circle(tx + (36 if toggle else 16), y + h / 2, 12, "#FFFFFF")]
    if value:
        out.append(text(rx, y + h / 2 + 5, value, 14, 500, value_color or C["muted"], BODY, "end"))
    if divider:
        out.append(line(x + 52, y + h, x + w - 16, y + h, C["line"]))
    return g(out, f"Row/{title}")


def overlay(opacity=0.55):
    return rect(0, 0, W, H, 0, C["forest"], opacity=opacity)


def skel(x, y, w, h, r=8, fill=C["skel"]):
    return rect(x, y, w, h, r, fill)


# ================================================================ PANTALLAS ==
SCREENS = []  # (id, slug, nombre, seccion, bg, fn)


def screen(sid, slug, name, section, bg=C["cream"]):
    def deco(fn):
        SCREENS.append((sid, slug, name, section, bg, fn))
        return fn
    return deco


# ---------------------------------------------------------- A. Acceso ------
@screen("01", "splash", "Splash", "A · Primer uso", C["forest"])
def s_splash(sid):
    return [circle(330, 90, 150, C["green"], opacity=0.35), circle(20, 760, 120, C["green"], opacity=0.35),
            status_bar(True), logo_mark(180, 360, 44),
            wordmark(180, 450, 36, "#FFFFFF", "middle"),
            text(180, 482, "Soltá el celu. Ganás vos.", 16, 500, C["lime"], BODY, "middle", opacity=0.85),
            gesture_bar(True)]


def onboarding(step, title_lines, body, illus, cta):
    out = [status_bar()]
    if step < 3:
        out.append(text(336, 64, "Saltar", 15, 700, C["muted"], BODY, "end"))
    out += illus
    out.append(rich(20, 488, title_lines, 36, lh=40))
    out.append(text(20, 590, body, 16, 400, C["muted"], lh=23))
    for i in range(3):
        if i + 1 == step:
            out.append(rect(20 + i * 16, 660, 24, 8, 4, C["forest"]))
        else:
            out.append(rect(20 + i * 16 + (16 if i + 1 > step else 0), 660, 8, 8, 4, "#CFC8BB"))
    out.append(button(20, 700, 320, cta, "primary"))
    out.append(gesture_bar())
    return out


@screen("02", "onboarding-1", "Onboarding 1 · Soltá el celu", "A · Primer uso")
def s_ob1(sid):
    illus = [circle(180, 262, 170, C["lime"], opacity=0.25),
             rect(60, 132, 240, 88, 44, C["paper"], C["forest"], 2.5),
             text(180, 190, "1 hora", 40, 800, C["forest"], DISPLAY, "middle"),
             circle(180, 262, 26, C["forest"]),
             text(180, 273, "=", 32, 800, C["lime"], DISPLAY, "middle"),
             rect(60, 306, 240, 88, 44, C["lime"]),
             text(180, 364, "60 pts", 40, 800, C["forest"], DISPLAY, "middle"),
             icon("moon", 292, 110, 28, C["green"])]
    return onboarding(1, [[("Soltá el celu.", C["ink"])], [("Ganás vos.", C["green"])]],
                      "Cada minuto que el teléfono descansa\nse convierte en puntos.", illus, "Siguiente")


@screen("03", "onboarding-2", "Onboarding 2 · Canjeá en tu barrio", "A · Primer uso")
def s_ob2(sid):
    illus = [circle(180, 262, 170, C["pink"], opacity=0.35),
             g([rect(44, 124, 272, 80, 24, C["paper"], C["line"]), icon_tile(60, 140, "coffee", C["pink"], C["pinkInk"]),
                text(120, 160, "Café + medialuna", 16, 700), text(120, 181, "Cuervo Café · 350 m", 13, 400, C["muted"]),
                pts_chip(324, 110, 120)], transform="rotate(-3 180 164)"),
             g([rect(44, 222, 272, 80, 24, C["paper"], C["line"]), icon_tile(60, 238, "book", C["sand"], C["sandInk"]),
                text(120, 258, "15% off en libros", 16, 700), text(120, 279, "Bosque Libros · 900 m", 13, 400, C["muted"]),
                pts_chip(324, 208, 300)], transform="rotate(2 180 262)"),
             g([rect(44, 320, 272, 80, 24, C["paper"], C["line"]), icon_tile(60, 336, "leaf", C["mint"], C["mintInk"]),
                text(120, 356, "Clase de yoga", 16, 700), text(120, 377, "Estudio Prana · 1,2 km", 13, 400, C["muted"]),
                pts_chip(324, 306, 400)], transform="rotate(-1.5 180 360)")]
    return onboarding(2, [[("Canjeá en tu", C["ink"])], [("barrio.", C["green"])]],
                      "Cafés, librerías y clases cerca tuyo\ncon premios reales.", illus, "Siguiente")


@screen("04", "onboarding-3", "Onboarding 3 · No tenés que hacer nada", "A · Primer uso")
def s_ob3(sid):
    illus = [circle(180, 262, 128, C["paper"]),
             f'<circle cx="180" cy="262" r="112" fill="none" stroke="{C["skel"]}" stroke-width="14"/>',
             f'<path d="{arc(180, 262, 112, 0.72)}" fill="none" stroke="{C["green"]}" stroke-width="14" stroke-linecap="round"/>',
             text(180, 262, "47:12", 48, 800, C["forest"], DISPLAY, "middle"),
             text(180, 290, "sin el celu", 15, 500, C["muted"], BODY, "middle"),
             chip(34, 120, "Sin botones", C["lime"], C["forest"], 32, 13, "check")[0],
             chip(236, 150, "Sin GPS", C["paper"], C["forest"], 32, 13, "check", C["line"])[0],
             chip(222, 392, "Sin cámara", C["paper"], C["forest"], 32, 13, "check", C["line"])[0]]
    return onboarding(3, [[("No tenés que", C["ink"])], [("hacer nada.", C["green"])]],
                      "Detectamos tus pausas solos: solo miramos\ncuándo la pantalla se prende y se apaga.", illus, "Empezar")


@screen("05", "acceso", "Acceso · Continuar con Google", "A · Primer uso", C["forest"])
def s_login(sid):
    return [circle(330, 200, 150, C["green"], opacity=0.4), status_bar(True),
            logo_mark(36, 64, 16), wordmark(60, 72, 22, "#FFFFFF"),
            rich(20, 360, [[("Tu tiempo lejos", "#FFFFFF")], [("del celu ", "#FFFFFF"), ("vale.", C["lime"])]], 40, lh=44),
            text(20, 440, "Entrás una vez y listo: el resto pasa solo.", 16, 400, "#FFFFFF", opacity=0.75),
            sheet(508, fill=C["cream"]),
            text(20, 558, "Entrá en un toque", 20, 800, C["ink"], DISPLAY),
            g([rect(20, 580, 320, 56, 28, C["forest"]), circle(78, 608, 13, "#FFFFFF"),
               text(78, 614, "G", 16, 800, "#4285F4", BODY, "middle"),
               text(196, 614, "Continuar con Google", 16, 700, "#FFFFFF", BODY, "middle")], "Button/google"),
            button(20, 648, 320, "Continuar con email", "outline", ic="mail"),
            text(180, 740, "Al continuar aceptás los Términos y la Política de privacidad.", 11, 400, C["muted"], BODY, "middle"),
            gesture_bar()]


@screen("06", "permisos", "Configuración · Dos permisos", "A · Primer uso")
def s_perms(sid):
    return [status_bar(),
            rich(20, 100, [[("Dos permisos", C["ink"])], [("y listo.", C["green"])]], 32, lh=36),
            text(20, 168, "Los pedimos una sola vez y podés\ncambiarlos cuando quieras.", 15, 400, C["muted"], lh=21),
            # paso 1: listo
            g([rect(20, 216, 320, 132, 24, C["paper"], C["green"], 1.5),
               icon_tile(36, 232, "check", C["mint"], C["mintInk"]),
               text(96, 252, "Acceso a uso", 16, 800), text(96, 272, "Obligatorio", 12, 600, C["muted"]),
               chip(324, 240, "Listo", C["mint"], C["mintInk"], 26, 12, anchor="end")[0],
               text(36, 306, "Solo vemos cuándo la pantalla se prende\ny se apaga. Nunca qué apps usás.", 13, 400, C["muted"], lh=19)],
              "Paso 1 · Acceso a uso (listo)"),
            # paso 2: pendiente
            g([rect(20, 364, 320, 188, 24, C["paper"], C["line"]),
               icon_tile(36, 380, "bell", C["amberBg"], C["amber"]),
               text(96, 400, "Notificaciones", 16, 800), text(96, 420, "Recomendado", 12, 600, C["muted"]),
               text(36, 454, "Te avisamos cuando sumás puntos\no cuando tu canje se confirma.", 13, 400, C["muted"], lh=19),
               button(36, 488, 136, "Permitir", "outline", h=48, size=15)], "Paso 2 · Notificaciones (pendiente)"),
            icon("pin", 20, 578, 20, C["muted"]),
            text(50, 593, "La ubicación la pedimos recién cuando\nabras el mapa, y es opcional.", 13, 400, C["muted"], lh=19),
            button(20, 700, 320, "Continuar", "primary"), gesture_bar()]


@screen("07", "permiso-rechazado", "Configuración · Acceso a uso rechazado (error)", "A · Primer uso")
def s_perm_denied(sid):
    steps = [("1", "Tocá ", "Abrir ajustes"), ("2", "Buscá ", "Take a Break"), ("3", "Activá ", "Permitir acceso")]
    out = [status_bar(), circle(180, 176, 52, C["redBg"]), icon("shieldx", 152, 148, 56, C["red"], 1.8),
           text(180, 280, "Sin este acceso no\npodemos contar tus pausas", 24, 800, C["ink"], DISPLAY, "middle", lh=28),
           text(180, 350, "Android lo llama “Acceso a uso”. Solo\nleemos cuándo se prende la pantalla.", 14, 400, C["muted"], BODY, "middle", lh=20),
           rect(20, 400, 320, 180, 24, C["paper"], C["line"])]
    for i, (n, a, b) in enumerate(steps):
        y = 416 + i * 54
        out += [circle(56, y + 20, 16, C["lime"]), text(56, y + 25, n, 14, 800, C["forest"], BODY, "middle"),
                rich(88, y + 25, [[(a, C["muted"], 15, 400), (b, C["ink"], 15, 700)]], 15, family=BODY)]
    out += [button(20, 636, 320, "Abrir ajustes", "primary"),
            button(20, 700, 320, "Ahora no, solo ver premios", "ghost", size=15), gesture_bar()]
    return out


# ------------------------------------------------------------ B. Inicio -----
def hero(y, pts, sub, today_frac, today_label, h=156):
    return g([rect(20, y, 320, h, 28, C["forest"]),
              f'<path d="M216 {y} A124 124 0 0 0 340 {y + 124} V{y + 28} A28 28 0 0 0 312 {y} Z" fill="{C["green"]}" opacity="0.45"/>',
              text(40, y + 34, "Tus puntos", 13, 700, C["lime"], opacity=0.85),
              rich(38, y + 100, [[(str(pts), C["lime"], 64), (" pts", "#FFFFFF", 20, 700)]], 64),
              text(40, y + 134, sub, 14, 400, "#FFFFFF", opacity=0.75),
              f'<circle cx="282" cy="{y + 82}" r="34" fill="none" stroke="{C["lime"]}" stroke-width="8" opacity="0.2"/>',
              f'<path d="{arc(282, y + 82, 34, today_frac)}" fill="none" stroke="{C["lime"]}" stroke-width="8" stroke-linecap="round"/>',
              text(282, y + 84, today_label, 15, 800, "#FFFFFF", DISPLAY, "middle"),
              text(282, y + 100, "hoy", 11, 500, "#FFFFFF", BODY, "middle", opacity=0.7)], "Hero · saldo")


def goal_card(y, frac=0.85, done=False):
    r = R["prana"]
    out = [rect(20, y, 320, 104 if not done else 120, 24, C["paper"], C["line"] if not done else C["green"], 1.5 if done else 1),
           icon_tile(36, y + 16, r["icon"], r["bg"], r["fg"], 40, 12, 20),
           text(88, y + 32, "Tu meta" if not done else "¡Ya te alcanza!", 12, 700, C["green"] if done else C["muted"]),
           text(88, y + 51, f'{r["title"]} · {r["biz"]}', 15, 700)]
    if not done:
        out += [progress(36, y + 70, 288, frac),
                text(36, y + 97, f"{BALANCE} / {r['pts']} pts", 12, 600, C["muted"]),
                text(324, y + 97, "Faltan 60 pts ≈ 1 h de break", 12, 700, C["green"], BODY, "end")]
    else:
        out += [progress(36, y + 70, 288, 1.0), button(212, y + 60 + 0, 112, "Canjear", "primary", 48, size=15)]
        out[-2] = progress(36, y + 82, 160, 1.0)
        out.append(text(36, y + 108, "400 / 400 pts", 12, 600, C["muted"]))
    return g(out, "Meta")


def stats_row(y):
    return g([rect(20, y, 154, 72, 20, C["paper"], C["line"]), icon("flame", 36, y + 16, 20, "#E0662E"),
              text(62, y + 31, "Racha", 12, 700, C["muted"]), text(36, y + 59, "6 días", 20, 800, C["ink"], DISPLAY),
              rect(186, y, 154, 72, 20, C["paper"], C["line"]), icon("clock", 202, y + 16, 20, C["green"]),
              text(228, y + 31, "Esta semana", 12, 700, C["muted"]), text(202, y + 59, "7 h 30 min", 20, 800, C["ink"], DISPLAY)],
             "Stats")


@screen("08", "inicio", "Inicio · contenido", "B · Inicio")
def s_home(sid):
    return [status_bar(), header_logo(),
            hero(88, BALANCE, "≈ 5 h 40 min lejos del celu", 0.5, "1 h"),
            goal_card(256), stats_row(372),
            section_title(484, "Te alcanza hoy", "Ver todo"),
            reward_row(500, "cuervo"), reward_row(580, "nube"), nav(0)]


@screen("09", "inicio-validado", "Inicio · break validado (feedback)", "B · Inicio")
def s_home_ok(sid):
    confetti = []
    rnd = random.Random(3)
    for _ in range(14):
        cx, cy = rnd.randint(180, 330), rnd.randint(100, 250)
        confetti.append(rect(cx, cy, 6, 12, 3, rnd.choice([C["forest"], C["paper"], C["pink"]]), opacity=0.55)
                        .replace("/>", f' transform="rotate({rnd.randint(0, 90)} {cx} {cy})"/>'))
    return [status_bar(), header_logo(),
            g([rect(20, 88, 320, 172, 28, C["lime"])] + confetti +
              [circle(58, 130, 20, C["forest"]), icon("check", 47, 119, 22, C["lime"], 2.6),
               icon("close", 304, 104, 20, C["forest"]),
               text(40, 186, "¡Break validado!", 15, 800, C["forest"]),
               text(40, 232, "+60 pts", 48, 800, C["forest"], DISPLAY),
               text(40, 252, "1 h sin el celu · de 16:00 a 17:00", 12, 600, C["forest"], opacity=0.75)],
              "Hero · break validado"),
            goal_card(272, done=True), stats_row(404),
            section_title(512, "Te alcanza hoy", "Ver todo"),
            reward_row(528, "cuervo", balance=400), reward_row(608, "nube", balance=400), nav(0)]


@screen("10", "inicio-vacio", "Inicio · vacío (primer día)", "B · Inicio")
def s_home_empty(sid):
    return [status_bar(), header_logo(),
            hero(88, 0, "Tu primera pausa suma a los 30 min", 0.001, "0 h"),
            g([rect(20, 256, 320, 196, 24, C["paper"], C["line"]),
               circle(180, 306, 30, C["mint"]), icon("phone", 164, 290, 32, C["green"]),
               text(180, 370, "Dejá el celu 30 minutos", 17, 800, C["ink"], DISPLAY, "middle"),
               text(180, 394, "Cuando vuelvas, tus puntos van a estar acá.\nNo hace falta tocar nada.", 13, 400, C["muted"], BODY, "middle", lh=19)],
              "Estado vacío"),
            section_title(488, "Premios cerca", "Ver todo"),
            reward_row(504, "cuervo", balance=0, sub="≈ 2 h de break"),
            reward_row(584, "nube", balance=0, sub="≈ 2 h 30 min de break"), nav(0)]


@screen("11", "inicio-cargando", "Inicio · cargando (skeleton)", "B · Inicio")
def s_home_loading(sid):
    out = [status_bar(), header_logo(),
           rect(20, 88, 320, 156, 28, C["forest"]),
           skel(40, 112, 80, 12, 6, "#2A5A48"), skel(40, 142, 150, 48, 12, "#2A5A48"), skel(40, 210, 180, 12, 6, "#2A5A48"),
           circle(282, 170, 34, "none", "#2A5A48", 8),
           rect(20, 256, 320, 104, 24, C["paper"], C["line"]), skel(36, 272, 40, 40, 12), skel(88, 276, 90, 10, 5),
           skel(88, 294, 180, 12, 6), skel(36, 326, 288, 10, 5), skel(36, 344, 120, 8, 4),
           skel(20, 372, 154, 72, 20), skel(186, 372, 154, 72, 20), skel(20, 470, 140, 16, 8)]
    for y in (500, 580):
        out += [rect(20, y, 320, 72, 20, C["paper"], C["line"]), skel(32, y + 12, 48, 48, 16),
                skel(92, y + 22, 140, 12, 6), skel(92, y + 42, 100, 10, 5), skel(270, y + 22, 58, 28, 14)]
    return out + [nav(0)]


@screen("12", "inicio-offline", "Inicio · sin conexión", "B · Inicio")
def s_home_offline(sid):
    return [status_bar(), header_logo(),
            banner(84, "Sin conexión · tus pausas se siguen contando"),
            hero(140, BALANCE, "≈ 5 h 40 min lejos del celu", 0.5, "1 h"),
            goal_card(308),
            section_title(452, "Te alcanza hoy"),
            text(20, 474, "Guardado · actualizado hoy 10:42", 12, 500, C["muted"]),
            reward_row(488, "cuervo"), reward_row(568, "nube"), nav(0)]


# ----------------------------------------------------------- C. Explorar ----
def explorar_top(sid, me, selected, blank_map=False):
    out = []
    if blank_map:
        out.append(rect(0, 0, W, 480, 0, "#EAE4D6"))
    else:
        out.append(map_art(sid, 0, 0, W, 480,
                           [("cuervo", .36, .56), ("nube", .72, .40), ("bosque", .12, .70), ("prana", .84, .68), ("lupa", .55, .82)],
                           me=me, selected=selected))
    out += [status_bar(),
            fake_shadow(20, 36, 320, 52, 26), rect(20, 36, 320, 52, 26, C["paper"]),
            icon("search", 38, 50, 22, C["muted"]), text(72, 67, "Buscar café, librería, clase…", 15, 400, C["muted"])]
    x = 20
    for i, lab in enumerate(["Todo", "Te alcanza", "Café", "Librerías", "Clases"]):
        on = i == 0
        c, w = chip(x, 100, lab, C["forest"] if on else C["paper"], "#FFFFFF" if on else C["ink"], 36, 14,
                    stroke=None if on else C["line"], weight=600)
        out.append(c)
        x += w + 8
    return out


@screen("13", "explorar", "Explorar · mapa + lista (con ubicación)", "C · Explorar")
def s_explore(sid):
    return explorar_top(sid, me=(.48, .66), selected="cuervo") + [
        g([fake_shadow(292, 400, 48, 48, 24), circle(316, 424, 24, C["paper"]), icon("locate", 304, 412, 24, C["blue"])], "FAB · mi ubicación"),
        sheet(460),
        text(20, 506, "12 premios cerca", 20, 800, C["ink"], DISPLAY),
        text(20, 528, "Ordenado por distancia", 12, 500, C["muted"]),
        chip(340, 488, "Lista", C["cream"], C["forest"], 32, 13, "list", anchor="end")[0],
        f'<clipPath id="{sid}-sheetclip"><rect x="0" y="540" width="360" height="180"/></clipPath>',
        f'<g clip-path="url(#{sid}-sheetclip)">',
        reward_row(540, "cuervo", card=False), reward_row(612, "nube", card=False), reward_row(684, "bosque", card=False),
        "</g>", nav(1)]


@screen("14", "explorar-sin-ubicacion", "Explorar · sin permiso de ubicación", "C · Explorar")
def s_explore_noloc(sid):
    return explorar_top(sid, me=None, selected=None) + [
        sheet(440),
        g([rect(20, 466, 320, 64, 18, C["cream"]), icon("pin", 36, 486, 22, C["green"]),
           text(68, 494, "Activá la ubicación para ver", 13, 600), text(68, 512, "primero lo más cercano", 13, 600),
           button(248, 474, 80, "Activar", "primary", 48, size=14)], "Banner · pedir ubicación (opcional)"),
        text(20, 560, "Todos los comercios · A–Z", 14, 800, C["ink"], DISPLAY),
        f'<clipPath id="{sid}-sheetclip"><rect x="0" y="572" width="360" height="148"/></clipPath>',
        f'<g clip-path="url(#{sid}-sheetclip)">',
        reward_row(572, "bosque", card=False, sub="Bosque Libros · Palermo"),
        reward_row(644, "ombu", card=False, sub="Casa Ombú · Belgrano"),
        "</g>", nav(1)]


@screen("15", "explorar-offline", "Explorar · sin conexión (catálogo guardado)", "C · Explorar")
def s_explore_offline(sid):
    return [status_bar(),
            text(20, 76, "Explorar", 28, 800, C["ink"], DISPLAY),
            banner(96, "Sin conexión · mostramos lo guardado"),
            g([rect(20, 152, 320, 132, 24, "#EAE4D6"), icon("cloudoff", 160, 176, 40, C["muted"], 1.8),
               text(180, 244, "El mapa necesita conexión", 15, 700, C["ink"], BODY, "middle"),
               text(180, 264, "La lista funciona igual", 13, 400, C["muted"], BODY, "middle")], "Mapa no disponible"),
            text(20, 318, "Todos los comercios · A–Z", 14, 800, C["ink"], DISPLAY),
            text(340, 318, "Actualizado 10:42", 12, 500, C["muted"], BODY, "end"),
            reward_row(332, "bosque", sub="Bosque Libros · Palermo"),
            reward_row(412, "ombu", sub="Casa Ombú · Belgrano"),
            reward_row(492, "cuervo", sub="Cuervo Café · Palermo"),
            reward_row(572, "prana", sub="Estudio Prana · Chacarita"),
            f'<clipPath id="{sid}-c"><rect x="0" y="652" width="360" height="68"/></clipPath>',
            f'<g clip-path="url(#{sid}-c)">', reward_row(652, "nube", sub="Heladería Nube · Villa Crespo"), "</g>",
            nav(1)]


@screen("16", "explorar-error", "Explorar · error sin datos guardados", "C · Explorar")
def s_explore_error(sid):
    return [status_bar(), text(20, 76, "Explorar", 28, 800, C["ink"], DISPLAY),
            circle(180, 250, 56, C["amberBg"]), icon("cloudoff", 152, 222, 56, C["amber"], 1.8),
            text(180, 356, "No pudimos cargar\nlos premios", 26, 800, C["ink"], DISPLAY, "middle", lh=30),
            text(180, 430, "Todavía no hay premios guardados en\neste teléfono. Conectate y reintentá.", 14, 400, C["muted"], BODY, "middle", lh=20),
            chip(180, 470, "Tus pausas se siguen contando igual",
                 C["mint"], C["mintInk"], 32, 13, "check", anchor="middle")[0],
            button(20, 640, 320, "Reintentar", "primary", ic="refresh"), nav(1)]


# -------------------------------------------------------------- D. Canje ----
def detail(sid, key, balance=BALANCE):
    r = R[key]
    ok = r["pts"] <= balance
    out = [rect(0, 0, W, 300, 0, r["bg"]), circle(300, 60, 110, "#FFFFFF", opacity=0.25),
           circle(180, 168, 64, "#FFFFFF"), icon(r["icon"], 144, 132, 72, r["fg"], 1.6),
           status_bar(),
           circle(44, 60, 24, C["paper"]), icon("back", 32, 48, 24, C["ink"]),
           circle(316, 60, 24, C["paper"]), icon("flag", 304, 48, 24, C["ink"]),
           text(20, 340, r["biz"], 14, 700, C["muted"]),
           text(20, 376, r["title"], 30, 800, C["ink"], DISPLAY)]
    c1, w1 = chip(20, 392, f'{r["pts"]} pts', C["lime"], C["forest"], 32, 14)
    out.append(c1)
    if ok:
        out.append(chip(28 + w1, 392, "Te alcanza", C["mint"], C["mintInk"], 32, 13, "check")[0])
    else:
        out.append(chip(28 + w1, 392, f'Te faltan {r["pts"] - balance}', C["amberBg"], C["sandInk"], 32, 13)[0])
    rows = [("pin", f'{r["barrio"]} · a {r["dist"]}', "Ver en mapa"),
            ("clock", "Lun a sáb · 8 a 20 h", None),
            ("ticket", "Canje presencial · 1 vez cada 15 días", None),
            ("store", "Quedan 8 para hoy", None)]
    for i, (ic, t, act) in enumerate(rows):
        y = 444 + i * 52
        out += [icon(ic, 20, y + 4, 22, C["green"]), text(54, y + 20, t, 14, 500, C["ink"])]
        if act:
            out.append(text(340, y + 20, act, 14, 700, C["green"], BODY, "end"))
        if i < len(rows) - 1:
            out.append(line(54, y + 40, 340, y + 40))
    return out


@screen("17", "detalle", "Detalle de premio · te alcanza", "D · Canje")
def s_detail(sid):
    return detail(sid, "cuervo") + [
        g([rect(0, 676, W, 124, 0, C["paper"]), line(0, 676, W, 676),
           text(180, 700, f"Después del canje te quedan {BALANCE - 120} pts", 12, 500, C["muted"], BODY, "middle"),
           button(20, 712, 320, "Canjear por 120 pts", "primary"), gesture_bar()], "Bottom bar · CTA")]


@screen("18", "detalle-insuficiente", "Detalle de premio · puntos insuficientes", "D · Canje")
def s_detail_short(sid):
    r = R["ombu"]
    return detail(sid, "ombu") + [
        g([rect(0, 652, W, 148, 0, C["paper"]), line(0, 652, W, 652),
           progress(20, 670, 320, BALANCE / r["pts"]),
           text(20, 698, f"{BALANCE} / {r['pts']} pts", 12, 600, C["muted"]),
           text(340, 698, "≈ 4 h 20 min más de break", 12, 700, C["green"], BODY, "end"),
           button(20, 712, 320, "Fijar como meta", "primary", ic="flag"), gesture_bar()], "Bottom bar · CTA")]


@screen("19", "confirmar-canje", "Confirmar canje · mantener presionado", "D · Canje")
def s_confirm(sid):
    r = R["cuervo"]
    return detail(sid, "cuervo") + [
        overlay(),
        sheet(424, fill=C["cream"]),
        text(20, 480, "¿Lo canjeás ahora?", 26, 800, C["ink"], DISPLAY),
        text(20, 506, "Hacelo en el local: el código dura 10 minutos.", 14, 400, C["muted"]),
        g([rect(20, 526, 320, 72, 20, C["paper"], C["line"]), icon_tile(32, 538, r["icon"], r["bg"], r["fg"]),
           text(92, 557, r["title"], 15, 700), text(92, 577, r["biz"], 13, 400, C["muted"]),
           text(326, 568, "−120 pts", 16, 800, C["ink"], DISPLAY, "end")], "Resumen"),
        text(20, 628, "Saldo después", 13, 500, C["muted"]),
        text(340, 628, f"{BALANCE - 120} pts", 13, 700, C["ink"], BODY, "end"),
        g([rect(20, 652, 320, 64, 32, C["lime"]),
           f'<clipPath id="{sid}-hold"><rect x="20" y="652" width="320" height="64" rx="32"/></clipPath>',
           f'<g clip-path="url(#{sid}-hold)">', rect(20, 652, 150, 64, 0, C["green"], opacity=0.35), "</g>",
           icon("finger", 64, 672, 24, C["forest"]),
           text(196, 690, "Mantené para canjear", 16, 800, C["forest"], BODY, "middle")], "Hold to confirm · 45%"),
        text(180, 750, "Cancelar", 15, 700, C["muted"], BODY, "middle"),
        gesture_bar()]


@screen("20", "codigo", "Código de canje · mostrar en el local", "D · Canje", C["forest"])
def s_code(sid):
    return [circle(40, 140, 140, C["green"], opacity=0.35), status_bar(True),
            icon("close", 32, 48, 24, "#FFFFFF"),
            text(180, 118, "Mostrale esto\nal local", 28, 800, "#FFFFFF", DISPLAY, "middle", lh=32),
            rect(70, 176, 220, 220, 28, C["paper"]), qr(90, 196, 180),
            text(180, 456, "TAB·7K4Q", 36, 700, C["lime"], MONO, "middle", ls=3),
            text(180, 488, "Café + medialuna · Cuervo Café", 14, 500, "#FFFFFF", BODY, "middle", opacity=0.75),
            chip(180, 512, "Vence en 09:42", "none", C["lime"], 36, 14, "clock", C["lime"], anchor="middle")[0],
            icon("sun", 64, 590, 18, "#FFFFFF"),
            text(90, 604, "Subimos el brillo para que se lea bien", 13, 500, "#FFFFFF", opacity=0.7),
            button(20, 700, 320, "Listo", "lime"), gesture_bar(True)]


def status_screen(ic, ic_fg, ic_bg, title, body, card, cta, ghost):
    return [status_bar(), circle(180, 176, 52, ic_bg), icon(ic, 152, 148, 56, ic_fg, 1.8),
            text(180, 284, title, 28, 800, C["ink"], DISPLAY, "middle", lh=32),
            text(180, 350 if "\n" in title else 318, body, 14, 400, C["muted"], BODY, "middle", lh=20)] + card + [
            button(20, 636, 320, cta, "primary"), button(20, 700, 320, ghost, "ghost", size=15), gesture_bar()]


@screen("21", "canje-pendiente", "Canje pendiente · sin conexión (offline)", "D · Canje")
def s_pending(sid):
    steps = [("check", C["green"], C["mint"], "Canje guardado en el teléfono", C["ink"]),
             ("clock", C["amber"], C["amberBg"], "Esperando conexión…", C["ink"]),
             ("ticket", "#A39E93", C["skel"], "Código listo para mostrar", C["muted"])]
    card = [rect(20, 396, 320, 176, 24, C["paper"], C["line"])]
    for i, (ic, fg, bg, t, tc) in enumerate(steps):
        y = 412 + i * 52
        card += [icon_tile(36, y, ic, bg, fg, 36, 18, 20), text(86, y + 23, t, 15, 600, tc)]
        if i < 2:
            card.append(line(54, y + 38, 54, y + 50, C["line"], 2))
    card.append(chip(180, 588, "Reservamos tus 120 pts", C["amberBg"], C["sandInk"], 30, 13, anchor="middle")[0])
    return status_screen("clock", C["amber"], C["amberBg"], "Canje pendiente",
                         "Estás sin conexión. Lo confirmamos solos\napenas vuelva la señal y te avisamos.",
                         card, "Entendido", "Ver mis canjes")


@screen("22", "canje-fallido", "Canje fallido · puntos devueltos (error)", "D · Canje")
def s_failed(sid):
    card = [rect(20, 400, 320, 88, 24, C["mint"]), icon_tile(36, 420, "undo", C["paper"], C["green"]),
            text(96, 440, "+120 pts devueltos", 17, 800, C["forest"], DISPLAY),
            text(96, 462, "Ya están de nuevo en tu saldo", 13, 500, C["mintInk"])]
    return status_screen("alert", C["red"], C["redBg"], "No pudimos\ncompletar el canje",
                         "El premio se agotó mientras estabas\nsin conexión. No perdiste nada.",
                         card, "Ver otros premios", "Cerrar")


# ---------------------------------------------------------- E. Actividad ----
def activity_head(sid):
    return [status_bar(), text(20, 76, "Actividad", 28, 800, C["ink"], DISPLAY),
            g([rect(20, 96, 320, 44, 22, C["skel"]), rect(24, 100, 156, 36, 18, C["paper"]),
               text(102, 123, "Semana", 14, 700, C["ink"], BODY, "middle"),
               text(258, 123, "Mes", 14, 600, C["muted"], BODY, "middle")], "Segmented · Semana/Mes")]


def bars(y, vals, today, empty=False):
    days = "LMMJVSD"
    base, top = y + 150, y + 30
    maxv = 140
    out = [rect(20, y, 320, 188, 24, C["paper"], C["line"])]
    goal_y = base - (120 / maxv) * (base - top)
    out += [line(36, goal_y, 324, goal_y, C["muted"], 1, "4 4", 0.6),
            text(324, goal_y - 6, "meta 2 h", 11, 600, C["muted"], BODY, "end")]
    for i, v in enumerate(vals):
        cx = 52 + i * 43
        hh = 6 if (empty or v == 0) else (v / maxv) * (base - top)
        fill = C["forest"] if i == today else (C["skel"] if (empty or i > today) else "#BFE3CF")
        out.append(rect(cx - 12, base - hh, 24, hh, 8 if hh > 16 else 3, fill))
        out.append(text(cx, y + 174, days[i], 12, 700 if i == today else 500, C["ink"] if i == today else C["muted"], BODY, "middle"))
    return g(out, "Chart · minutos por día")


def pause_row(y, ic, fg, bg, title, sub, chip_label, ok):
    return g([icon_tile(20, y + 12, ic, bg, fg, 44, 14, 22),
              text(76, y + 32, title, 15, 700), text(76, y + 52, sub, 13, 400, C["muted"]),
              chip(340, y + 22, chip_label, C["mint"] if ok else C["skel"], C["mintInk"] if ok else C["muted"], 28, 13, anchor="end")[0],
              line(76, y + 68, 340, y + 68)], f"Pausa/{title}")


@screen("23", "actividad", "Actividad · semana, racha e historial", "E · Actividad")
def s_activity(sid):
    return activity_head(sid) + [
        rich(20, 188, [[("7 h 30 min", C["ink"])]], 30),
        text(20, 210, "lejos del celu esta semana · +450 pts", 13, 500, C["muted"]),
        bars(224, [60, 95, 30, 120, 85, 60, 0], 5),
        g([rect(20, 424, 320, 52, 18, C["amberBg"]), icon("flame", 34, 438, 22, "#E0662E"),
           text(66, 455, "Racha de 6 días", 15, 800, C["sandInk"]),
           text(326, 455, "Récord: 11", 13, 600, C["sandInk"], BODY, "end")], "Racha"),
        text(20, 504, "HOY", 12, 800, C["muted"], ls=1),
        f'<clipPath id="{sid}-c"><rect x="0" y="508" width="360" height="212"/></clipPath>',
        f'<g clip-path="url(#{sid}-c)">',
        pause_row(508, "check", C["green"], C["mint"], "14:10 – 15:10", "1 h · pausa válida", "+60 pts", True),
        pause_row(578, "clock", C["muted"], C["skel"], "09:30 – 09:50", "20 min · finde: mínimo 45", "0 pts", False),
        pause_row(648, "moon", C["muted"], C["skel"], "00:30 – 08:10", "Horario de descanso · no suma", "0 pts", False),
        "</g>", nav(2)]


@screen("24", "actividad-vacia", "Actividad · vacío + reglas", "E · Actividad")
def s_activity_empty(sid):
    rules = [("clock", "1 minuto de pausa = 1 punto"), ("check", "Desde 30 min (45 min el finde)"),
             ("moon", "De 23 a 9 h no suma (dormir)"), ("target", "Hasta 240 pts por día")]
    out = activity_head(sid) + [
        rich(20, 188, [[("0 min", C["ink"])]], 30),
        text(20, 210, "Tu semana arranca con tu primera pausa", 13, 500, C["muted"]),
        bars(224, [0] * 7, 5, empty=True),
        text(20, 450, "Cómo sumás", 18, 800, C["ink"], DISPLAY),
        rect(20, 466, 320, 232, 24, C["paper"], C["line"])]
    for i, (ic, t) in enumerate(rules):
        y = 482 + i * 54
        out += [icon_tile(36, y, ic, C["cream"], C["green"], 40, 12, 20), text(90, y + 25, t, 14, 600)]
    return out + [nav(2)]


# ------------------------------------------------------------ F. Perfil -----
@screen("25", "perfil", "Perfil y ajustes", "F · Perfil")
def s_profile(sid):
    out = [status_bar(), top_bar("Perfil"),
           circle(56, 138, 36, C["pink"]), text(56, 148, "M", 28, 800, C["pinkInk"], DISPLAY, "middle"),
           text(108, 134, "Martina", 24, 800, C["ink"], DISPLAY), text(108, 156, "martina@mail.com", 13, 400, C["muted"])]
    for i, (lab, val) in enumerate([("Total", "42 h"), ("Canjes", "7"), ("Récord", "11 días")]):
        x = 20 + i * 110
        out += [rect(x, 196, 100, 68, 18, C["paper"], C["line"]), text(x + 14, 222, lab, 12, 700, C["muted"]),
                text(x + 14, 250, val, 18, 800, C["ink"], DISPLAY)]
    out.append(rect(20, 280, 320, 336, 24, C["paper"], C["line"]))
    rows = [("ticket", "Mis canjes", "1 activo", True, None, C["green"]),
            ("flag", "Mi meta", "Clase de yoga", True, None, None),
            ("target", "Meta diaria", "2 h", True, None, None),
            ("bell", "Notificaciones", None, False, True, None),
            ("shieldcheck", "Permisos", "Todo en orden", True, None, None),
            ("info", "Cómo sumamos puntos", None, True, None, None)]
    for i, (ic, t, v, ch, tg, vc) in enumerate(rows):
        out.append(list_row(280 + i * 56, ic, t, v, ch, toggle=tg, divider=i < len(rows) - 1, value_color=vc))
    out += [list_row(636, "logout", "Cerrar sesión", chevron=False, fg=C["red"], divider=False), gesture_bar()]
    return out


@screen("26", "mis-canjes", "Mis canjes · activo, pendiente e historial", "F · Perfil")
def s_redemptions(sid):
    r = R["cuervo"]
    out = [status_bar(), top_bar("Mis canjes"),
           text(20, 112, "ACTIVOS", 12, 800, C["muted"], ls=1),
           g([rect(20, 124, 320, 132, 24, C["forest"]), icon_tile(36, 140, r["icon"], r["bg"], r["fg"], 40, 12, 20),
              text(88, 156, r["title"], 15, 700, "#FFFFFF"), text(88, 174, "Cuervo Café · vence en 08:12", 12, 500, "#FFFFFF", opacity=0.7),
              text(36, 228, "TAB·7K4Q", 22, 700, C["lime"], MONO, ls=2),
              button(212, 196, 112, "Mostrar", "lime", 48, size=15)], "Canje activo"),
           g([rect(20, 268, 320, 72, 20, C["amberBg"]), icon_tile(32, 280, "clock", C["paper"], C["amber"]),
              text(92, 299, "Cucurucho doble", 15, 700), text(92, 319, "Pendiente · se confirma al conectarte", 12, 500, C["sandInk"])],
             "Canje pendiente"),
           text(20, 380, "ANTERIORES", 12, 800, C["muted"], ls=1)]
    hist = [("bosque", "Usado · 12 sep", "Usado", C["skel"], C["muted"]),
            ("lupa", "Usado · 3 sep", "Usado", C["skel"], C["muted"]),
            ("prana", "Sin stock · 28 ago", "Devuelto", C["mint"], C["mintInk"])]
    for i, (k, sub, lab, bg, fg) in enumerate(hist):
        out.append(reward_row(392 + i * 72, k, sub=sub, card=False,
                              right=chip(340, 392 + i * 72 + 22, lab, bg, fg, 28, 12, anchor="end")[0]))
    return out + [gesture_bar()]


# ---------------------------------------------------------- G. Sistema ------
@screen("27", "notificacion", "Notificación · break validado", "G · Sistema", "#10251C")
def s_notif(sid):
    return [circle(300, 700, 260, C["green"], opacity=0.35), circle(40, 120, 160, C["forest"], opacity=0.8),
            status_bar(True),
            text(180, 190, "17:00", 76, 600, "#FFFFFF", DISPLAY, "middle"),
            text(180, 224, "Sábado 26 de septiembre", 15, 500, "#FFFFFF", BODY, "middle", opacity=0.8),
            g([rect(16, 290, 328, 136, 26, "#FFFFFF", opacity=0.95),
               logo_mark(44, 318, 12), text(64, 323, "Take a Break · ahora", 12, 600, C["muted"]),
               text(32, 356, "Break validado: +60 pts", 16, 800, C["ink"]),
               text(32, 378, "1 h sin el celu. Ya te alcanza para la\nclase de yoga en Estudio Prana.", 13, 400, C["muted"], lh=18),
               text(32, 414, "VER PREMIO", 12, 800, C["green"], ls=0.8)], "Notificación"),
            text(180, 740, "Deslizá hacia arriba para desbloquear", 12, 500, "#FFFFFF", BODY, "middle", opacity=0.6),
            gesture_bar(True)]



# ================================================================ NOTAS ======
# Estado que representa cada frame + decisión de diseño que lo justifica.
# Se usan en index.html y sirven de base para la sección 4.8 del documento LaTeX.
NOTES = {
    "01": ("Carga", "Marca y promesa en una línea. Se muestra solo mientras se inicializan Room y DataStore (<1 s)."),
    "02": ("Contenido", "Modelo mental en una ecuación (1 h = 60 pts): la moneda ES el tiempo, sin conversiones que memorizar. Replica el boceto original."),
    "03": ("Contenido", "Muestra premios concretos y cercanos: la recompensa tangible es la diferencia contra Digital Wellbeing (insight de la etapa Empatizar)."),
    "04": ("Contenido", "Baja la ansiedad de privacidad antes de pedir permisos: sin botones, sin GPS, sin cámara. El CTA está siempre en el mismo lugar en los 3 pasos."),
    "05": ("Contenido", "Iniciar sesión y registrarse se unifican en Continuar con… (ley de Hick: 2 opciones, no 3). Google = 1 toque."),
    "06": ("Contenido · parcial", "Pre-permiso: se explica el porqué antes del diálogo del sistema. Un solo permiso obligatorio; la ubicación se pide recién en el mapa (contextual)."),
    "07": ("Error · permiso rechazado", "Error recuperable con pasos concretos y una salida digna (solo ver premios): la app nunca queda en un callejón sin salida."),
    "08": ("Contenido", "Jerarquía: saldo → meta → progreso → qué puedo canjear ya. Filas de 72 dp y navegación inferior en la zona natural del pulgar."),
    "09": ("Feedback · éxito", "Cierra el loop de recompensa: el feedback aparece donde el usuario mira y el CTA Canjear aparece dentro de la tarjeta de meta (distancia mínima)."),
    "10": ("Vacío", "Estado vacío que enseña qué hacer (dejar el celu 30 min) y aclara que no hay que tocar nada. Los premios muestran su costo en horas."),
    "11": ("Carga", "Skeleton con la misma geometría que el contenido: evita saltos de layout y comunica progreso sin spinner."),
    "12": ("Offline", "Mensaje clave: la detección sigue funcionando sin red. El catálogo muestra la hora de la última sincronización."),
    "13": ("Contenido", "Mapa + hoja inferior con lista: el mapa orienta, la lista (en la zona del pulgar) es la que se toca. El filtro Te alcanza reduce opciones."),
    "14": ("Permiso rechazado", "Sin ubicación la app funciona igual: lista A–Z y un pedido opcional, no bloqueante (degradación elegante)."),
    "15": ("Offline", "Sin tiles de mapa se muestra la lista cacheada en Room; las filas siguen siendo tocables y el detalle se abre offline."),
    "16": ("Error · sin caché", "Único caso sin datos: explica la causa, ofrece Reintentar y aclara que las pausas no se pierden."),
    "17": ("Contenido", "Toda la información para decidir en una pantalla (distancia, horario, reglas, stock). CTA fijo abajo con el costo y el saldo resultante."),
    "18": ("Contenido · insuficiente", "Nunca un botón deshabilitado sin salida: el CTA se transforma en Fijar como meta y muestra cuánto falta en horas."),
    "19": ("Confirmación", "Canjear es irreversible: se confirma manteniendo presionado (64 dp) en vez de con un diálogo extra. Previene toques accidentales sin sumar pantallas."),
    "20": ("Contenido · éxito", "Pensado para el mostrador: código grande, QR, brillo alto y vencimiento visible. Listo en lima sobre bosque, al alcance del pulgar."),
    "21": ("Offline · pendiente", "El canje offline no falla: queda pendiente, se reservan los puntos y el estado se muestra en una línea de tiempo simple."),
    "22": ("Error · conflicto de sync", "Conflicto de sincronización resuelto a favor del usuario: se devuelven los puntos y se ofrece una alternativa inmediata."),
    "23": ("Contenido", "Transparencia de las reglas anti-abuso: cada pausa que no suma dice por qué (horario de descanso, mínimo de finde)."),
    "24": ("Vacío", "El estado vacío enseña las reglas del juego en 4 líneas en vez de mostrar un gráfico en cero sin contexto."),
    "25": ("Contenido", "Acciones poco frecuentes agrupadas fuera de la navegación principal (se llega desde el avatar). Cerrar sesión separado y en rojo."),
    "26": ("Contenido", "El canje activo va primero y tiene Mostrar a un toque; pendientes y devoluciones con un color de estado consistente."),
    "27": ("Sistema", "Notificación local con deep link al premio: del bloqueo al canje en 1 toque. Es la única interrupción que genera la app."),
}


# ================================================================ BOARDS =====
def svg_doc(w, h, body, bg, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<title>{esc(title)}</title><style>@import url(\'{esc(FONTS)}\');</style>'
            f'<rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>')


def render_screen(entry):
    sid, slug, name, section, bg, fn = entry
    return svg_doc(W, H, "".join(fn(f"s{sid}")), bg, f"{sid} · {name}")


def thumb(entry, x, y, scale):
    sid, slug, name, section, bg, fn = entry
    body = "".join(fn(f"t{sid}x{int(x)}y{int(y)}"))
    w, h = W * scale, H * scale
    return (f'<g id="Thumb {sid}"><rect x="{x - 1}" y="{y - 1}" width="{w + 2}" height="{h + 2}" rx="{14 * scale + 1}" fill="{C["line"]}"/>'
            f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="0 0 {W} {H}">'
            f'<clipPath id="tc{sid}{int(x)}{int(y)}"><rect width="{W}" height="{H}" rx="28"/></clipPath>'
            f'<g clip-path="url(#tc{sid}{int(x)}{int(y)})"><rect width="{W}" height="{H}" fill="{bg}"/>{body}</g></svg>'
            f'{text(x, y + h + 22, sid + " · " + name.split(" · ")[0], 14, 700, C["ink"])}'
            f'{text(x, y + h + 40, name.split(" · ")[1] if " · " in name else "", 12, 500, C["muted"])}</g>')


def by_id(sid):
    return next(e for e in SCREENS if e[0] == sid)


def arrow(x1, y1, x2, y2, label=None, color=C["forest"], dash=None, via=None):
    pts = [(x1, y1)] + (via or []) + [(x2, y2)]
    d = "M" + " L".join(f"{a} {b}" for a, b in pts)
    out = [f'<path d="{d}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"'
           + (f' stroke-dasharray="{dash}"' if dash else "") + "/>"]
    (ax, ay), (bx, by) = pts[-2], pts[-1]
    ang = math.atan2(by - ay, bx - ax)
    hx1, hy1 = bx - 12 * math.cos(ang - 0.45), by - 12 * math.sin(ang - 0.45)
    hx2, hy2 = bx - 12 * math.cos(ang + 0.45), by - 12 * math.sin(ang + 0.45)
    out.append(f'<path d="M{hx1:.1f} {hy1:.1f} L{bx} {by} L{hx2:.1f} {hy2:.1f}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    if label:
        mx, my = pts[len(pts) // 2 - 1] if len(pts) > 2 else ((x1 + x2) / 2, (y1 + y2) / 2)
        if len(pts) > 2:
            mx, my = (pts[1][0] + pts[2][0]) / 2, (pts[1][1] + pts[2][1]) / 2
        lw = tw(label, 13, 0.55) + 20
        out += [rect(mx - lw / 2, my - 14, lw, 28, 14, C["paper"], color, 1.5),
                text(mx, my + 5, label, 13, 700, color, BODY, "middle")]
    return g(out, "Arrow")


def diamond(cx, cy, label, w=170, h=84):
    return g([f'<path d="M{cx} {cy - h / 2} L{cx + w / 2} {cy} L{cx} {cy + h / 2} L{cx - w / 2} {cy} Z" fill="{C["lime"]}" stroke="{C["forest"]}" stroke-width="2"/>',
              text(cx, cy + 5, label, 14, 800, C["forest"], BODY, "middle")], f"Decisión/{label}")


def pill_node(cx, cy, label, fill=C["forest"], fg="#FFFFFF", w=None):
    w = w or tw(label, 15, 0.56) + 40
    return g([rect(cx - w / 2, cy - 24, w, 48, 24, fill), text(cx, cy + 5, label, 15, 700, fg, BODY, "middle")], f"Nodo/{label}")


def board_flow():
    s = 0.34
    tw_, th = W * s, H * s   # 122 x 272
    out = [text(60, 90, "Flujo principal · Take a Break", 44, 800, C["ink"], DISPLAY),
           text(60, 126, "Punto de entrada → detección pasiva → validación → premio → canje. Las flechas punteadas son transiciones del sistema (sin acción del usuario).", 18, 400, C["muted"])]
    # fila 1: primer uso
    row1 = 190
    out.append(text(60, row1 - 16, "A · PRIMER USO (una sola vez)", 14, 800, C["green"], ls=1))
    xs = [60, 240, 420, 600, 780, 960]
    for sid, x in zip(["01", "02", "03", "04", "05", "06"], xs):
        out.append(thumb(by_id(sid), x, row1, s))
    for a, b in zip(xs, xs[1:]):
        out.append(arrow(a + tw_ + 8, row1 + th / 2, b - 8, row1 + th / 2))
    out.append(diamond(1260, row1 + th / 2, "¿Acceso a uso?"))
    out.append(arrow(960 + tw_ + 8, row1 + th / 2, 1175, row1 + th / 2))
    out.append(thumb(by_id("07"), 1460, row1, s))
    out.append(arrow(1345, row1 + th / 2, 1452, row1 + th / 2, "No"))
    out.append(arrow(1521, row1 + th + 50, 1260, row1 + th / 2 + 42, "Reintentar", C["muted"], "6 6",
                     via=[(1521, row1 + th + 80), (1260, row1 + th + 80)]))
    # fila 2: loop principal
    row2 = 640
    out.append(text(60, row2 - 58, "B · LOOP PRINCIPAL (caso de uso central)", 14, 800, C["green"], ls=1))
    out.append(arrow(1260, row1 + th / 2 + 42, 1260, row2 - 40, "Sí", via=[(1260, row2 - 40)]))
    out.append(thumb(by_id("08"), 60, row2, s))
    out.append(arrow(1260, row2 - 40, 121, row2 - 8, via=[(121, row2 - 40)]))
    out.append(pill_node(330, row2 + th / 2 - 60, "WorkManager lee UsageStats", C["paper"], C["forest"], 250))
    out.append(rect(205, row2 + th / 2 - 84, 250, 48, 24, "none", C["forest"], 2))
    out.append(arrow(60 + tw_ + 8, row2 + th / 2 - 60, 203, row2 + th / 2 - 60, None, C["muted"], "6 6"))
    out.append(diamond(560, row2 + th / 2 - 60, "¿Pausa válida?", 180))
    out.append(arrow(457, row2 + th / 2 - 60, 468, row2 + th / 2 - 60, None, C["muted"], "6 6"))
    out.append(text(560, row2 + th / 2 - 116, "≥30 min (45 finde) · fuera de 23–9 h · tope 240/día", 12, 600, C["muted"], BODY, "middle"))
    out.append(arrow(560, row2 + th / 2 - 18, 330, row2 + th / 2 - 36, "No · queda en el historial", C["muted"], "6 6",
                     via=[(560, row2 + th / 2 + 40), (330, row2 + th / 2 + 40)]))
    xs2 = [720, 900, 1080, 1260]
    for sid, x in zip(["27", "09", "17", "19"], xs2):
        out.append(thumb(by_id(sid), x, row2, s))
    out.append(arrow(650, row2 + th / 2 - 60, 712, row2 + th / 2 - 60, "Sí"))
    for a, b in zip(xs2, xs2[1:]):
        out.append(arrow(a + tw_ + 8, row2 + th / 2, b - 8, row2 + th / 2))
    out.append(diamond(1540, row2 + th / 2, "¿Hay conexión?"))
    out.append(arrow(1260 + tw_ + 8, row2 + th / 2, 1455, row2 + th / 2, "Mantener"))
    out.append(thumb(by_id("20"), 1700, row2 - 60, s))
    out.append(thumb(by_id("21"), 1700, row2 + 290, s))
    out.append(arrow(1540, row2 + th / 2 - 42, 1692, row2 + 76, "Sí", via=[(1540, row2 + 76)]))
    out.append(arrow(1540, row2 + th / 2 + 42, 1692, row2 + 426, "No", via=[(1540, row2 + 426)]))
    out.append(diamond(1990, row2 + 426, "¿Sigue en stock?", 180))
    out.append(arrow(1700 + tw_ + 8, row2 + 426, 1898, row2 + 426, "Vuelve la red", C["muted"], "6 6"))
    out.append(arrow(1990, row2 + 384, 1700 + tw_ + 8, row2 + 76, "Sí", via=[(1990, row2 + 76)]))
    out.append(thumb(by_id("22"), 2140, row2 + 560, s))
    out.append(arrow(1990, row2 + 468, 2132, row2 + 696, "No", via=[(1990, row2 + 696)]))
    out.append(pill_node(1990, row2 + 30 - 90, "Fin · canje en el local", C["lime"], C["forest"], 230))
    out.append(arrow(1700 + tw_ / 2, row2 - 68, 1880, row2 - 60, None, C["forest"], None, via=[(1700 + tw_ / 2, row2 - 60)]))
    # fila 3: navegación
    row3 = 1330
    out.append(text(60, row3 - 84, "C · NAVEGACIÓN (bottom bar de 3 destinos + perfil)", 14, 800, C["green"], ls=1))
    for sid, x in [("08", 60), ("13", 300), ("23", 540), ("25", 840), ("26", 1080), ("18", 300 + 0)]:
        pass
    out += [thumb(by_id("08"), 60, row3, s), thumb(by_id("13"), 300, row3, s), thumb(by_id("23"), 540, row3, s),
            thumb(by_id("25"), 840, row3, s), thumb(by_id("26"), 1080, row3, s), thumb(by_id("18"), 1320, row3, s)]
    out.append(arrow(60 + tw_ + 8, row3 + 80, 292, row3 + 80, "Tab"))
    out.append(arrow(300 + tw_ + 8, row3 + 80, 532, row3 + 80, "Tab"))
    out.append(arrow(121, row3 - 4, 900, row3 - 4, "Avatar", via=[(121, row3 - 60), (900, row3 - 60)]))
    out.append(arrow(840 + tw_ + 8, row3 + 80, 1072, row3 + 80, "Mis canjes"))
    out.append(arrow(300 + tw_ / 2, row3 + th + 50, 1381, row3 + th + 8, "Premio caro", via=[(361, row3 + th + 90), (1381, row3 + th + 90)]))
    out.append(pill_node(1640, row3 + 136, "Fijar meta → vuelve a Inicio", C["paper"], C["forest"], 280))
    out.append(rect(1500, row3 + 112, 280, 48, 24, "none", C["forest"], 2))
    out.append(arrow(1320 + tw_ + 8, row3 + 136, 1492, row3 + 136))
    return svg_doc(2400, 1760, "".join(out), C["cream"], "Flujo principal")


def board_system():
    out = [text(60, 90, "Sistema de diseño · Take a Break", 44, 800, C["ink"], DISPLAY),
           text(60, 126, "Minimalista, inspirado en el look & feel de Pasito: verde bosque + lima, fondo crema, formas de píldora, una sola acción primaria por pantalla.", 18, 400, C["muted"])]
    # colores
    out.append(text(60, 200, "COLOR", 14, 800, C["green"], ls=1))
    sw = [("forest", "Bosque", "Marca / hero"), ("green", "Verde", "Primario"), ("lime", "Lima", "Puntos / acento"),
          ("cream", "Crema", "Fondo"), ("paper", "Papel", "Tarjetas"), ("ink", "Tinta", "Texto"),
          ("muted", "Gris", "Texto 2°"), ("amberBg", "Ámbar", "Offline / pendiente"), ("redBg", "Rojo", "Error"),
          ("mint", "Menta", "Éxito")]
    for i, (k, n, u) in enumerate(sw):
        x = 60 + i * 150
        out += [rect(x, 220, 130, 96, 20, C[k], C["line"]), text(x, 342, n, 16, 700), text(x, 362, C[k].upper(), 13, 500, C["muted"], MONO),
                text(x, 380, u, 13, 400, C["muted"])]
    # tipografía
    out.append(text(60, 450, "TIPOGRAFÍA", 14, 800, C["green"], ls=1))
    ty = [("Display · Bricolage Grotesque 800 · 64", 64, 800, DISPLAY, "340 pts"),
          ("Title L · Bricolage 800 · 32", 32, 800, DISPLAY, "Dos permisos y listo."),
          ("Title M · Bricolage 800 · 20", 20, 800, DISPLAY, "Te alcanza hoy"),
          ("Body · DM Sans 400 · 16", 16, 400, BODY, "Cada minuto que el teléfono descansa se convierte en puntos."),
          ("Label · DM Sans 700 · 14", 14, 700, BODY, "Canjear por 120 pts"),
          ("Caption · DM Sans 500 · 12", 12, 500, BODY, "Actualizado hoy 10:42")]
    y = 520
    for lab, size, wgt, fam, sample in ty:
        out += [text(60, y, lab, 13, 600, C["muted"]), text(460, y, sample, size, wgt, C["ink"], fam)]
        y += max(size + 26, 44)
    # componentes
    out.append(text(60, 900, "COMPONENTES", 14, 800, C["green"], ls=1))
    comps = [button(60, 930, 320, "Canjear por 120 pts", "primary"), button(400, 930, 320, "Listo", "lime"),
             button(740, 930, 320, "Continuar con email", "outline", ic="mail"), button(1080, 930, 320, "Te faltan 60 pts", "disabled"),
             chip(60, 1010, "120 pts", C["lime"], C["forest"])[0], chip(160, 1010, "400 pts", C["paper"], C["muted"], stroke=C["line"])[0],
             chip(260, 1010, "Te alcanza", C["mint"], C["mintInk"], ic="check")[0], chip(400, 1010, "Pendiente", C["amberBg"], C["sandInk"], ic="clock")[0],
             banner(1060, "Sin conexión · tus pausas se siguen contando", x=60, w=360),
             g([reward_row(1000, "cuervo", x=740, w=360)]),
             g([reward_row(1080, "prana", x=740, w=360)]),
             f'<g transform="translate(1180 360)">{nav(0)}</g>']
    out += comps
    out.append(text(1180, 1062, "Bottom navigation · 3 destinos, 120 dp por destino", 13, 600, C["muted"]))
    # espaciado / forma
    out.append(text(1560, 200, "FORMA Y ESPACIO", 14, 800, C["green"], ls=1))
    spec = [("Grilla", "8 dp · márgenes laterales 20 dp"), ("Radios", "Tarjetas 20–28 · botones y chips en píldora"),
            ("Íconos", "Línea 2 dp, grilla 24, extremos redondeados"), ("Elevación", "Sin sombras: jerarquía por color y tamaño"),
            ("Contraste", "Texto ≥ 4.5:1 (WCAG AA) · lima solo sobre bosque"), ("Movimiento", "150–250 ms · feedback háptico al canjear")]
    for i, (a, b) in enumerate(spec):
        out += [text(1560, 250 + i * 56, a, 16, 800, C["ink"], DISPLAY), text(1560, 272 + i * 56, b, 14, 400, C["muted"])]
    return svg_doc(2000, 1200, "".join(out), C["cream"], "Sistema de diseño")


def board_fitts():
    """Zona del pulgar + objetivos táctiles (ley de Fitts) sobre la pantalla de Inicio y Detalle."""
    out = [text(60, 90, "Ley de Fitts y zona del pulgar", 44, 800, C["ink"], DISPLAY),
           text(60, 126, "T = a + b·log2(1 + D/W): las acciones frecuentes o críticas son grandes (W↑) y viven donde el pulgar ya está (D↓).", 18, 400, C["muted"])]

    def zone_phone(x, y, entry, marks):
        sid = entry[0]
        body = "".join(entry[5](f"f{sid}"))
        o = [f'<svg x="{x}" y="{y}" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
             f'<clipPath id="fz{sid}"><rect width="{W}" height="{H}" rx="32"/></clipPath><g clip-path="url(#fz{sid})">'
             f'<rect width="{W}" height="{H}" fill="{entry[4]}"/>{body}'
             # zonas (mano derecha): difícil arriba, ok medio, natural abajo
             f'<rect width="{W}" height="260" fill="#C2412D" opacity="0.12"/>'
             f'<rect y="260" width="{W}" height="220" fill="#F2B544" opacity="0.14"/>'
             f'<path d="M0 480 H{W} V{H} H0 Z" fill="#136B4A" opacity="0.14"/>'
             f'</g></svg>', rect(x - 2, y - 2, W + 4, H + 4, 34, "none", C["ink"], 2)]
        for (mx, my, mw, mh, lab, side) in marks:
            o.append(rect(x + mx, y + my, mw, mh, min(mh / 2, 20), "none", C["red"], 2.5, dash="6 4"))
            lx = x + W + 24 if side == "r" else x - 24
            o.append(line(x + mx + (mw if side == "r" else 0), y + my + mh / 2, lx, y + my + mh / 2, C["red"], 1.5))
            o.append(text(lx + (8 if side == "r" else -8), y + my + mh / 2 + 5, lab, 14, 700, C["red"], BODY, "start" if side == "r" else "end"))
        return o

    out += zone_phone(360, 190, by_id("08"), [
        (20, 256, 320, 104, "Meta: toda la tarjeta es tocable", "r"),
        (20, 500, 320, 72, "Filas de 72 dp", "r"),
        (0, 720, 360, 80, "Nav: 3 destinos × 120 dp", "r"),
        (296, 32, 40, 40, "Perfil (poco frecuente) → arriba", "r")])
    out += zone_phone(1180, 190, by_id("19"), [
        (20, 652, 320, 64, "Hold 64 dp: previene toques accidentales", "r"),
        (20, 526, 320, 72, "Resumen = lo que confirmás", "r"),
        (120, 732, 120, 36, "Cancelar: lejos del CTA", "l")])
    leg = [("#C2412D", "Difícil: acciones raras o destructivas"), ("#F2B544", "Alcanzable: contenido y lectura"),
           ("#136B4A", "Natural: CTA primario y navegación")]
    for i, (col, lab) in enumerate(leg):
        out += [rect(60, 1040 + i * 36, 24, 24, 6, col, opacity=0.5), text(96, 1058 + i * 36, lab, 15, 600)]
    rules = ["Objetivos táctiles ≥ 48 dp; CTA primario 56 dp de alto y 320 dp de ancho.",
             "Una sola acción primaria por pantalla, siempre en el mismo lugar (abajo).",
             "Acción irreversible (canjear) = mantener presionado, no un diálogo extra.",
             "Lo pasivo no requiere toques: la pausa se detecta sola (0 interacciones).",
             "Notificación → pantalla del premio en 1 toque (deep link)."]
    for i, r_ in enumerate(rules):
        out += [circle(620, 1052 + i * 30, 5, C["green"]), text(636, 1058 + i * 30, r_, 15, 500)]
    return svg_doc(2000, 1220, "".join(out), C["cream"], "Ley de Fitts y zona del pulgar")


BOARDS = [("00-sistema-de-diseno", board_system), ("00-flujo-principal", board_flow), ("00-fitts-zona-pulgar", board_fitts)]




def build_index(path):
    """Galería autocontenida (SVG inline) con el estado y la decisión de diseño de cada pantalla."""
    sections = {}
    for e in SCREENS:
        sections.setdefault(e[3], []).append(e)
    cards = []
    for sec, entries in sections.items():
        cards.append(f'<h2>{esc(sec)}</h2><div class="grid">')
        for e in entries:
            sid, slug, name, _, bg, fn = e
            state, why = NOTES.get(sid, ("", ""))
            svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{esc(name)}"><rect width="{W}" height="{H}" fill="{bg}"/>'
                   + "".join(fn(f"g{sid}")) + "</svg>")
            cards.append(f'<figure id="s{sid}"><div class="phone">{svg}</div><figcaption><span class="id">{sid}</span>'
                         f'<strong>{esc(name)}</strong><span class="state">{esc(state)}</span><p>{esc(why)}</p></figcaption></figure>')
        cards.append("</div>")
    boards = "".join(f'<h2>{esc(t)}</h2><div class="board"><img src="boards/{slug}.svg" alt="{esc(t)}"></div>'
                     for slug, t in [("00-flujo-principal", "Flujo principal"), ("00-sistema-de-diseno", "Sistema de diseño"),
                                     ("00-fitts-zona-pulgar", "Ley de Fitts y zona del pulgar")])
    css = (":root{--bg:%(cream)s;--card:%(paper)s;--ink:%(ink)s;--muted:%(muted)s;--line:%(line)s;--brand:%(forest)s;--accent:%(lime)s;--green:%(green)s}" % C) + """
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 'DM Sans',sans-serif}
header{background:var(--brand);color:#fff;padding:48px 24px}header div,main{max-width:1320px;margin:0 auto}
h1{font:800 clamp(32px,5vw,56px)/1 'Bricolage Grotesque',sans-serif;margin:0 0 12px}h1 em{color:var(--accent);font-style:normal}
header p{max-width:760px;opacity:.8;margin:0}main{padding:8px 16px 80px}
h2{font:800 24px 'Bricolage Grotesque',sans-serif;margin:48px 0 16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:28px}
figure{margin:0}.phone{border-radius:28px;overflow:hidden;border:1px solid var(--line);background:var(--card)}.phone svg{display:block;width:100%;height:auto}
figcaption{padding:12px 4px 0}figcaption strong{display:block;font-weight:700}
.id{font:700 12px 'JetBrains Mono',monospace;color:var(--green)}
.state{display:inline-block;margin:6px 0;padding:2px 10px;border-radius:99px;background:var(--accent);color:var(--brand);font-size:12px;font-weight:700}
figcaption p{margin:0;color:var(--muted);font-size:14px}
.board{overflow-x:auto;border:1px solid var(--line);border-radius:20px;background:var(--card)}.board img{display:block;min-width:1100px;width:100%}
"""
    page = ('<!doctype html><html lang="es"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Take a Break · Pantallas</title>'
            f'<link rel="stylesheet" href="{esc(FONTS)}"><style>{css}</style></head><body>'
            '<header><div><h1>take a break · <em>pantallas</em></h1>'
            f'<p>Preentrega DA1 · {len(SCREENS)} frames Android (360×800 dp) con sus estados de carga, contenido, vacío, error y offline. '
            'Cada frame indica qué estado representa y qué decisión de diseño lo justifica.</p></div></header>'
            f'<main>{"".join(cards)}{boards}</main></body></html>')
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


# ============================================================== SALIDA =======
def main(png=False):
    sdir, bdir, pdir = (os.path.join(ROOT, d) for d in ("screens", "boards", "png"))
    for d in (sdir, bdir):
        os.makedirs(d, exist_ok=True)
    files = []
    for e in SCREENS:
        p = os.path.join(sdir, f"{e[0]}-{e[1]}.svg")
        with open(p, "w", encoding="utf-8") as f:
            f.write(render_screen(e))
        files.append((p, W, H))
    for slug, fn in BOARDS:
        p = os.path.join(bdir, f"{slug}.svg")
        svg = fn()
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg)
        bw, bh = (int(v) for v in svg.split('viewBox="0 0 ')[1].split('"')[0].split())
        files.append((p, bw, bh))
    build_index(os.path.join(ROOT, "index.html"))
    print(f"{len(SCREENS)} pantallas + {len(BOARDS)} boards + index.html generados")
    if png:
        os.makedirs(pdir, exist_ok=True)
        edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        profile = tempfile.mkdtemp(prefix="tab-edge-")  # perfil limpio: evita PNG cacheados
        for p, w, h in files:
            out = os.path.join(pdir, os.path.basename(p)[:-4] + ".png")
            subprocess.run([edge, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                            "--force-device-scale-factor=2", f"--window-size={w},{h}",
                            "--virtual-time-budget=4000", f"--user-data-dir={profile}", f"--screenshot={out}",
                            "file:///" + p.replace("\\", "/") + f"?v={time.time_ns()}"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{len(files)} png exportados en {pdir}")


if __name__ == "__main__":
    main(png="--png" in sys.argv)
