"""Diagrama de flujo de ataque.py — SVG con coordenadas explícitas y verificación de que el texto cabe."""
from PIL import ImageFont
FS, LH = 11, 13.6
FONT = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", FS)
tw = lambda t: FONT.getlength(t)
W_CANVAS, G = 602, 20
L, R, WB = 150, 438, 232
nodos, aristas, etiquetas, marcos, errores = [], [], [], [], []

def alto(kind, lines, h=None):
    if h: return h
    return {"term": 28, "con": 22}.get(kind, round(len(lines) * LH + 14))

def nodo(kind, cx, ytop, lines, w=WB, h=None):
    h = alto(kind, lines, h); n = dict(kind=kind, cx=cx, y=ytop, w=w, h=h, lines=lines)
    n["cy"] = ytop + h / 2; n["bot"] = ytop + h
    # verificación de ajuste del texto
    anc = max((tw(l) for l in lines), default=0); th = len(lines) * LH
    if kind == "dec":
        ok = anc / w + th / h <= 0.93
    elif kind == "io":
        ok = anc <= w - 2 * 14 - 12
    elif kind == "con":
        ok = True
    else:
        ok = anc <= w - 14
    if not ok: errores.append((lines, round(anc), w, h))
    nodos.append(n); return n

def flecha(*pts, cabeza=True): aristas.append((pts, cabeza))
def etq(x, y, t, anchor="start"): etiquetas.append((x, y, t, anchor))

# ---------------- columna izquierda ----------------
y = 14
l1 = nodo("term", L, y, ["Inicio"], w=110); y = l1["bot"] + G
l2 = nodo("box", L, y, ["Crear el enlace I2C y el contexto TLS"]); y = l2["bot"] + G + 8
l3 = nodo("box", L, y, ["Corrida de control sin TLS,", "registrando las tramas del bus"]); y = l3["bot"] + G
l4 = nodo("box", L, y, ["Corrida con TLS híbrido,", "registrando las tramas del bus"]); y = l4["bot"] + G
l5 = nodo("box", L, y, ["Buscar el texto «TELEMETRIA»", "en los dos registros de tramas"]); y = l5["bot"] + G + 4
l6 = nodo("con", L, y, ["A"], w=22)
for a, b in [(l1, l2), (l2, l3), (l3, l4), (l4, l5), (l5, l6)]:
    flecha((L, a["bot"]), (L, b["y"]))
marcos.append((L - WB / 2 - 10, l3["y"] - 18, WB + 20, l5["bot"] - l3["y"] + 28, "Confidencialidad"))

# ---------------- columna derecha ----------------
y = 14
r1 = nodo("con", R, y + 3, ["A"], w=22); y = r1["bot"] + G + 8
r2 = nodo("box", R, y, ["Tomar la siguiente manipulación:", "alterar ESP32 → Pi, alterar Pi → ESP32", "o reinyectar un registro cifrado"]); y = r2["bot"] + G
r3 = nodo("box", R, y, ["Reiniciar el enlace, enviar START", "y realizar el handshake TLS híbrido"]); y = r3["bot"] + G
r4 = nodo("box", R, y, ["Invertir un bit del registro o reenviarlo,", "recalculando el CRC de la trama"]); y = r4["bot"] + G
r5 = nodo("io", R, y, ["Leer el reporte del ESP32"]); y = r5["bot"] + G
r6 = nodo("box", R, y, ["Marcar como rechazada si hubo SSLError", "o el estado del ESP32 es distinto de 0"]); y = r6["bot"] + G
r7 = nodo("dec", R, y, ["¿Quedan", "manipulaciones?"], w=176, h=62)
for a, b in [(r1, r2), (r2, r3), (r3, r4), (r4, r5), (r5, r6), (r6, r7)]:
    flecha((R, a["bot"]), (R, b["y"]))
XB = 584   # canal del bucle
flecha((R + r7["w"] / 2, r7["cy"]), (XB, r7["cy"]), (XB, r2["cy"]), (R + WB / 2, r2["cy"]))
etq(R + r7["w"] / 2 + 6, r7["cy"] - 5, "Sí")
marcos.append((R - WB / 2 - 10, r2["y"] - 18, XB - (R - WB / 2 - 10) + 10, r7["bot"] - r2["y"] + 24, "Integridad"))

# ---------------- evaluación (columna izquierda, abajo) ----------------
ym = r7["bot"] + 30
etq(R + 6, r7["bot"] + 21, "No")
y = ym + G
l7 = nodo("dec", L, y, ["¿Las cinco pruebas", "dieron el resultado", "esperado?"], w=214, h=88)
flecha((R, r7["bot"]), (R, ym), (L, ym), (L, l7["y"]))
y = l7["bot"] + G + 6
l8 = nodo("box", L, y, ["Conclusión:", "todas las pruebas pasaron"])
l8b = nodo("box", R, y, ["Conclusión:", "revisar los resultados"])
flecha((L, l7["bot"]), (L, l8["y"])); etq(L + 6, l7["bot"] + 14, "Sí")
flecha((L + l7["w"] / 2, l7["cy"]), (R, l7["cy"]), (R, l8b["y"])); etq(L + l7["w"] / 2 + 8, l7["cy"] - 5, "No")
yj = l8["bot"] + 18
y = yj + 16
l9 = nodo("io", L, y, ["Guardar los resultados en", "ataques_<fecha>.json"])
flecha((L, l8["bot"]), (L, l9["y"]))
flecha((R, l8b["bot"]), (R, yj), (L + 1, yj))
y = l9["bot"] + G
l10 = nodo("term", L, y, ["Fin"], w=110)
flecha((L, l9["bot"]), (L, l10["y"]))
H_CANVAS = l10["bot"] + 14

# ---------------- SVG ----------------
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_CANVAS}" height="{H_CANVAS}" viewBox="0 0 {W_CANVAS} {H_CANVAS}" '
     f'font-family="Liberation Sans, Arial, sans-serif" font-size="{FS}">',
     '<defs><marker id="p" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
     '<path d="M0,1 L10,5 L0,9 Z" fill="#111"/></marker></defs>',
     f'<rect width="{W_CANVAS}" height="{H_CANVAS}" fill="#fff"/>']
for x, y0, w, h, t in marcos:
    o.append(f'<rect x="{x}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="#8c8c8c" stroke-width="0.8" stroke-dasharray="4 3"/>')
    ancho = tw(t) * 10 / 11 * 1.06
    o.append(f'<rect x="{x + w - 16 - ancho}" y="{y0 - 6}" width="{ancho + 12}" height="12" fill="#fff"/>')
    o.append(f'<text x="{x + w - 10}" y="{y0 + 3.5}" font-size="10" font-style="italic" fill="#444" text-anchor="end">{t}</text>')
for pts, cab in aristas:
    d = " ".join(f"{x},{y}" for x, y in pts)
    o.append(f'<polyline points="{d}" fill="none" stroke="#111" stroke-width="1"{" marker-end=\"url(#p)\"" if cab else ""}/>')
for n in nodos:
    cx, y0, w, h, k = n["cx"], n["y"], n["w"], n["h"], n["kind"]
    x0 = cx - w / 2; st = 'fill="#fff" stroke="#111" stroke-width="1.1"'
    if k == "term": o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="{h/2}" {st}/>')
    elif k == "box": o.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" {st}/>')
    elif k == "io":
        s = 14; o.append(f'<polygon points="{x0+s},{y0} {x0+w},{y0} {x0+w-s},{y0+h} {x0},{y0+h}" {st}/>')
    elif k == "dec":
        o.append(f'<polygon points="{cx},{y0} {cx+w/2},{y0+h/2} {cx},{y0+h} {cx-w/2},{y0+h/2}" {st}/>')
    elif k == "con": o.append(f'<circle cx="{cx}" cy="{y0+h/2}" r="{h/2}" {st}/>')
    n0 = len(n["lines"]); yy = n["cy"] - (n0 - 1) * LH / 2 + FS * 0.36
    for i, l in enumerate(n["lines"]):
        fw = ' font-weight="bold"' if k in ("term", "con") else ""
        l = l.replace("<", "&lt;").replace(">", "&gt;")
        o.append(f'<text x="{cx}" y="{yy + i * LH:.1f}" text-anchor="middle"{fw}>{l}</text>')
for x, y0, t, a in etiquetas:
    o.append(f'<text x="{x}" y="{y0}" font-size="10" text-anchor="{a}">{t}</text>')
o.append("</svg>")
open("flujo_ataque.svg", "w").write("\n".join(o))
open("flujo_ataque.html", "w").write('<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff">'
                                     '<div id="fig" style="display:inline-block">' + "\n".join(o) + "</div>")
print("lienzo", W_CANVAS, "x", round(H_CANVAS), "| textos que no caben:", errores or "ninguno")
