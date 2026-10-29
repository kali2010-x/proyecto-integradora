"""Motor mínimo para diagramas de flujo ISO 5807 en SVG, con coordenadas explícitas y control de ajuste del texto."""
from PIL import ImageFont
_F = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 110)
_FB = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 110)
FS, LH, SK = 11, 13.6, 13

import re
SUB = re.compile(r"_\{([^}]*)\}")
def tw(t, s=FS, b=False):
    f = _FB if b else _F; w, pos = 0, 0
    for m in SUB.finditer(t):
        w += f.getlength(t[pos:m.start()]) * s / 110 + f.getlength(m.group(1)) * s * 0.72 / 110; pos = m.end()
    return w + f.getlength(t[pos:]) * s / 110
def txt(t):
    out, pos, baja = "", 0, False
    for m in SUB.finditer(t):
        seg = t[pos:m.start()]
        if seg: out += (f'<tspan dy="-2.6">{esc(seg)}</tspan>' if baja else esc(seg)); baja = False
        elif baja: out += '<tspan dy="-2.6">\u200b</tspan>'; baja = False
        out += f'<tspan font-size="{FS*0.72:.1f}" dy="2.6">{esc(m.group(1))}</tspan>'; baja = True; pos = m.end()
    resto = t[pos:]
    if resto: out += (f'<tspan dy="-2.6">{esc(resto)}</tspan>' if baja else esc(resto))
    return out
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

class Diagrama:
    def __init__(self, W=602):
        self.W, self.nodos, self.aristas, self.etqs, self.marcos, self.errores = W, [], [], [], [], []
        self.H = 0

    def nodo(self, kind, cx, y, lines, w=230, h=None):
        if h is None:
            h = {"term": max(28, len(lines) * LH + 12), "con": 22}.get(kind, round(len(lines) * LH + 14))
        n = dict(kind=kind, cx=cx, y=y, w=w, h=h, lines=lines, x=cx - w / 2, r=cx + w / 2, b=y + h, cy=y + h / 2)
        n["top"], n["bot"], n["left"], n["right"] = (cx, y), (cx, y + h), (cx - w / 2, y + h / 2), (cx + w / 2, y + h / 2)
        anc = max((tw(l, b=kind in ("term", "con")) for l in lines), default=0); th = len(lines) * LH
        ok = {"dec": anc / w + th / h <= 0.93, "io": anc <= w - 2 * SK - 10, "term": anc <= w - 20,
              "con": True, "pre": anc <= w - 26}.get(kind, anc <= w - 12)
        if not ok: self.errores.append((lines, round(anc), w, h))
        self.nodos.append(n); self.H = max(self.H, y + h); return n

    def flecha(self, *pts, cabeza=True, dash=False):
        self.aristas.append((pts, cabeza, dash)); self.H = max(self.H, max(p[1] for p in pts))

    def etq(self, x, y, t, anchor="start", size=10, italic=False):
        self.etqs.append((x, y, t, anchor, size, italic))

    def marco(self, x, y, w, h, t):
        self.marcos.append((x, y, w, h, t)); self.H = max(self.H, y + h)

    def svg(self, margen=12):
        W, H = self.W, self.H + margen
        o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" '
             f'font-family="Liberation Sans, Arial, sans-serif" font-size="{FS}">',
             '<defs><marker id="p" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
             '<path d="M0,1 L10,5 L0,9 Z" fill="#111"/></marker></defs>', f'<rect width="{W}" height="{H:.0f}" fill="#fff"/>']
        for x, y, w, h, t in self.marcos:
            o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#8c8c8c" stroke-width="0.8" stroke-dasharray="4 3"/>')
        for pts, cab, dash in self.aristas:
            d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
            o.append(f'<polyline points="{d}" fill="none" stroke="#111" stroke-width="1"'
                     f'{" stroke-dasharray=\"4 3\"" if dash else ""}{" marker-end=\"url(#p)\"" if cab else ""}/>')
        for n in self.nodos:
            cx, y0, w, h, k = n["cx"], n["y"], n["w"], n["h"], n["kind"]; x0 = cx - w / 2
            st = 'fill="#fff" stroke="#111" stroke-width="1.1"'
            if k == "term": o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="{h/2}" {st}/>')
            elif k == "box": o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" {st}/>')
            elif k == "pre":
                o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" {st}/>')
                o.append(f'<line x1="{x0+8}" y1="{y0}" x2="{x0+8}" y2="{y0+h}" stroke="#111" stroke-width="1"/>')
                o.append(f'<line x1="{x0+w-8}" y1="{y0}" x2="{x0+w-8}" y2="{y0+h}" stroke="#111" stroke-width="1"/>')
            elif k == "io": o.append(f'<polygon points="{x0+SK},{y0} {x0+w},{y0} {x0+w-SK},{y0+h} {x0},{y0+h}" {st}/>')
            elif k == "dec": o.append(f'<polygon points="{cx},{y0} {cx+w/2},{y0+h/2} {cx},{y0+h} {cx-w/2},{y0+h/2}" {st}/>')
            elif k == "con": o.append(f'<circle cx="{cx}" cy="{y0+h/2}" r="{h/2}" {st}/>')
            nl = len(n["lines"]); yy = n["cy"] - (nl - 1) * LH / 2 + FS * 0.36
            for i, l in enumerate(n["lines"]):
                fw = ' font-weight="bold"' if k in ("term", "con") else ""
                o.append(f'<text x="{cx}" y="{yy + i * LH:.1f}" text-anchor="middle"{fw}>{txt(l)}</text>')
        for x, y, w, h, t in self.marcos:
            a = tw(t, 10) * 1.06 + 12
            o.append(f'<rect x="{x + w - 16 - a + 6:.1f}" y="{y - 6}" width="{a:.1f}" height="12" fill="#fff"/>')
            o.append(f'<text x="{x + w - 10}" y="{y + 3.5}" font-size="10" font-style="italic" fill="#444" text-anchor="end">{esc(t)}</text>')
        for x, y, t, a, s, it in self.etqs:
            o.append(f'<text x="{x}" y="{y}" font-size="{s}" text-anchor="{a}"{" font-style=\"italic\"" if it else ""}>{esc(t)}</text>')
        o.append("</svg>")
        return "\n".join(o)

    def guardar(self, nombre):
        s = self.svg()
        open(nombre + ".svg", "w").write(s)
        open(nombre + ".html", "w").write('<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff">'
                                          '<div id="fig" style="display:inline-block;line-height:0">' + s + "</div>")
        print(nombre, "lienzo", self.W, "x", round(self.H + 12), "| no caben:", self.errores or "ninguno")


class Col:
    """Columna: apila nodos hacia abajo y los une con flechas."""
    def __init__(self, d, cx, y, w=230, gap=20):
        self.d, self.cx, self.y, self.w, self.gap, self.ult = d, cx, y, w, gap, None

    def add(self, kind, lines, w=None, h=None, link=True, gap=None, etq=None):
        g = self.gap if gap is None else gap
        n = self.d.nodo(kind, self.cx, self.y + (g if self.ult or self.y else 0), lines, w or self.w, h)
        if link and self.ult is not None:
            self.d.flecha(self.ult["bot"], n["top"])
            if etq: self.d.etq(self.cx + 6, self.ult["b"] + 13, etq)
        self.ult, self.y = n, n["b"]
        return n
