"""Diagrama de bloques general del proyecto (v5): 6 fases, una por franja, ligadas a los objetivos."""
import re
from PIL import ImageFont
FD = "/usr/share/fonts/truetype/liberation/"
_fT = ImageFont.truetype(FD + "LiberationSans-Bold.ttf", 96); _fB = ImageFont.truetype(FD + "LiberationSans-Regular.ttf", 96)
FT, FB, LB, LT = 9.6, 8.8, 10.6, 12.0
W = 602; SX0, SW = 4, 96; CX0 = SX0 + SW + 6
BW, GAP = 100, 24
colx = [CX0 + 9 + i * (BW + GAP) for i in range(4)]
D3 = 6
fondo, marcos, o, rotulos, errores = [], [], [], [], []
SUB = re.compile(r"_\{([^}]*)\}")

def esc(t): return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
def ancho(t, s=FB, bold=False):
    f = _fT if bold else _fB; w = 0; pos = 0
    for m in SUB.finditer(t):
        w += f.getlength(t[pos:m.start()]) * s / 96 + f.getlength(m.group(1)) * s * 0.72 / 96; pos = m.end()
    return w + f.getlength(t[pos:]) * s / 96
def svg_txt(t):
    out, pos, baja = "", 0, False
    for m in SUB.finditer(t):
        seg = t[pos:m.start()]
        if seg: out += (f'<tspan dy="-2.6">{esc(seg)}</tspan>' if baja else esc(seg)); baja = False
        elif baja: out += '<tspan dy="-2.6">\u200b</tspan>'; baja = False
        out += f'<tspan font-size="{FB*0.72:.1f}" dy="2.6">{esc(m.group(1))}</tspan>'; baja = True; pos = m.end()
    resto = t[pos:]
    if resto: out += (f'<tspan dy="-2.6">{esc(resto)}</tspan>' if baja else esc(resto))
    return out

def alto(titulo, lineas):
    return 8 + LT * len(titulo) + LB * len(lineas) + 6 + (2 if any(l.startswith("~") for l in lineas) else 0)

def texto(cx, y, h, titulo, lineas, w):
    for t in titulo:
        if ancho(t, FT, True) > w - 10: errores.append(t)
    for t in lineas:
        if ancho(t.lstrip("~"), 7.6 if t.startswith("~") else FB) > w - 10: errores.append(t)
    yy = y + (h - (LT * len(titulo) + LB * len(lineas))) / 2 + 9
    for t in titulo:
        o.append(f'<text x="{cx:.1f}" y="{yy:.1f}" text-anchor="middle" font-weight="bold" font-size="{FT}">{esc(t)}</text>'); yy += LT
    for t in lineas:
        if t.startswith("~"):
            o.append(f'<text x="{cx:.1f}" y="{yy + 1:.1f}" text-anchor="middle" font-size="7.6" font-style="italic" fill="#333">{esc(t[1:])}</text>')
        else:
            o.append(f'<text x="{cx:.1f}" y="{yy:.1f}" text-anchor="middle" font-size="{FB}" fill="#222">{svg_txt(t)}</text>')
        yy += LB

def bloque(x, y, w, h, titulo, lineas, tipo="p"):
    if tipo == "hw":
        fx, fy, fw, fh = x, y + D3, w - D3, h - D3
        o.append(f'<polygon points="{x},{fy} {x+D3},{y} {x+w},{y} {fx+fw},{fy}" fill="#bdbdbd" stroke="#111" stroke-width="1"/>')
        o.append(f'<polygon points="{fx+fw},{fy} {x+w},{y} {x+w},{y+h-D3} {fx+fw},{y+h}" fill="#8f8f8f" stroke="#111" stroke-width="1"/>')
        o.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="#fff" stroke="#111" stroke-width="1.2"/>')
        texto(fx + fw / 2, fy, fh, titulo, lineas, fw)
        return dict(x=x, y=y, w=w, h=h, cx=fx + fw / 2, cy=fy + fh / 2, r=x + w, b=y + h, top=fy)
    st = {"ext": 'fill="#fff" stroke="#111" stroke-width="1" stroke-dasharray="4 2.5"',
          "out": 'fill="#e3e3e3" stroke="#111" stroke-width="1"', "p": 'fill="#fff" stroke="#111" stroke-width="1"',
          "fin": 'fill="#fff" stroke="#111" stroke-width="1.2"'}[tipo]
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" {st}/>')
    if tipo == "fin":
        o.append(f'<rect x="{x+3}" y="{y+3}" width="{w-6}" height="{h-6}" fill="none" stroke="#111" stroke-width="1.2"/>')
    texto(x + w / 2, y, h, titulo, lineas, w)
    return dict(x=x, y=y, w=w, h=h, cx=x + w / 2, cy=y + h / 2, r=x + w, b=y + h, top=y)

def linea(*pts, ini=False, fin=True, dash=False, grosor=1, capa=None):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    m = (' marker-end="url(#p)"' if fin else "") + (' marker-start="url(#q)"' if ini else "")
    (capa if capa is not None else o).append(f'<polyline points="{d}" fill="none" stroke="#111" stroke-width="{grosor}"'
                                              f'{" stroke-dasharray=\"3 2\"" if dash else ""}{m}/>')

def etq(x, y, t, anchor="middle", fondo_blanco=False):
    if fondo_blanco:
        ww = _fB.getlength(t) * 8 / 96 * 1.06 + 8
        x0 = x - ww / 2 if anchor == "middle" else (x - 3 if anchor == "start" else x - ww + 3)
        o.append(f'<rect x="{x0:.1f}" y="{y - 8:.1f}" width="{ww:.1f}" height="11" fill="#fff"/>')
    o.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="8" font-style="italic" fill="#222">{esc(t)}</text>')

def marco(bls, rot, pad=6, abajo=False):
    x0 = min(b["x"] for b in bls) - pad; y0 = min(b["y"] for b in bls) - pad
    x1 = max(b["x"] + b["w"] for b in bls) + pad; y1 = max(b["y"] + b["h"] for b in bls) + pad
    marcos.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1-x0:.1f}" height="{y1-y0:.1f}" rx="4" fill="none" stroke="#8a8a8a" stroke-width="0.8"/>')
    an = _fT.getlength(rot) * 6.8 / 96 + 0.7 * len(rot) + 8; yr = y1 if abajo else y0
    rotulos.append(f'<rect x="{x1 - 8 - an:.1f}" y="{yr - 5:.1f}" width="{an:.1f}" height="10" fill="#fff"/>')
    rotulos.append(f'<text x="{x1 - 12:.1f}" y="{yr + 2.4:.1f}" text-anchor="end" font-size="6.8" font-weight="bold" letter-spacing="0.7" fill="#555">{rot}</text>')

def franja(y, h, n, nombre, objetivo):
    fondo.append(f'<rect x="{SX0}" y="{y}" width="{W - 2*SX0}" height="{h}" fill="none" stroke="#9a9a9a" stroke-width="0.8"/>')
    fondo.append(f'<rect x="{SX0}" y="{y}" width="{SW}" height="{h}" fill="#333"/>')
    tot = 14 + 12.5 * len(nombre) + 16; yy = y + (h - tot) / 2 + 9
    fondo.append(f'<text x="{SX0 + SW/2}" y="{yy:.1f}" text-anchor="middle" font-size="8.6" font-weight="bold" letter-spacing="1.4" fill="#fff">FASE {n}</text>'); yy += 15
    for t in nombre:
        if _fT.getlength(t) * 10 / 96 > SW - 8: errores.append(t)
        fondo.append(f'<text x="{SX0 + SW/2}" y="{yy:.1f}" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">{esc(t)}</text>'); yy += 12.5
    ow = _fB.getlength(objetivo) * 8.4 / 96 + 12
    fondo.append(f'<rect x="{SX0 + SW/2 - ow/2:.1f}" y="{yy - 5:.1f}" width="{ow:.1f}" height="14" rx="7" fill="none" stroke="#fff" stroke-width="0.8"/>')
    fondo.append(f'<text x="{SX0 + SW/2}" y="{yy + 5.3:.1f}" text-anchor="middle" font-size="8.4" fill="#fff">{esc(objetivo)}</text>')

PAD, PADB, RG, RGM, BG = 13, 12, 16, 24, 19
def hf(*bl): return max(alto(t, l) for t, l in bl)
bandas, salidas, entradas = [], [], []
y = 4

# ---------- Fase 1: requerimientos y diseño (Objetivo 1) ----------
y0 = y; yb = y + PAD
f0 = [(["Criptografía", "poscuántica"], ["FIPS 203 y", "RFC 10024"]), (["TLS 1.3 y bus I2C"], ["RFC 8446 y", "NXP UM10204"]),
      (["Hojas técnicas"], ["ESP32, Raspberry Pi", "e INA219"])]
h0 = hf(*f0)
S = [bloque(colx[i], yb, BW, h0, *f0[i], "ext") for i in range(3)]
t2 = ["seguridad: intercambio híbrido · transporte: flujo confiable", "sobre I2C · recursos: memoria, tiempo y energía del nodo"]
req = bloque(colx[0], yb + h0 + RGM, 3 * BW + 2 * GAP, alto(["Requerimientos del modelo"], t2), ["Requerimientos del modelo"], t2)
for s_ in S: linea((s_["cx"], s_["b"]), (s_["cx"], req["y"]), dash=True)
r1 = bloque(colx[3], req["y"], BW, req["h"], ["Criterios", "de diseño"], ["del banco de", "pruebas"], "out")
linea((req["r"], req["cy"]), (r1["x"], r1["cy"]))
marco(S, "FUENTES EXTERNAS"); marco([req], "PROCESO", abajo=True); marco([r1], "RESULTADO")
y = req["b"] + PADB + 4; bandas.append((y0, y - y0, 1, ["Requerimientos", "y diseño"], "Objetivo 1"))
salidas.append((r1, "criterios de diseño")); entradas.append(None)

# ---------- Fase 2: banco de pruebas (Objetivo 2) ----------
y += BG; y0 = y; yb = y + PAD
f1 = [(["Nodo sensor"], ["ESP32"]), (["Bus I2C dedicado"], ["100 y 400 kbit/s"]), (["Unidad de borde"], ["Raspberry Pi 4"])]
f2 = [(["Fuente de 5 V"], ["alimentación", "del sistema"]), (["Sensor INA219"], ["voltaje, corriente", "y potencia"])]
h1, h2 = hf(*f1) + D3, hf(*f2) + D3
esp = bloque(colx[0], yb, BW, h1, *f1[0], "hw"); bus = bloque(colx[1], yb, BW, h1, *f1[1], "hw"); rpi = bloque(colx[2], yb, BW, h1, *f1[2], "hw")
yr2 = yb + h1 + RGM
fue = bloque(colx[1], yr2, BW, h2, *f2[0], "hw"); ina = bloque(colx[2], yr2, BW, h2, *f2[1], "hw")
r2 = bloque(colx[3], yb + D3, BW, yr2 + h2 - yb - D3, ["Banco operativo"], ["bus verificado;", "potencia de reposo", "medida", "~impacto económico:", "~costo en USD"], "out")
linea((esp["r"], esp["cy"]), (bus["x"], bus["cy"]), ini=True); linea((bus["r"], bus["cy"]), (rpi["x"], rpi["cy"]), ini=True)
linea((fue["r"], fue["cy"]), (ina["x"], ina["cy"]))
ym = (bus["b"] + fue["y"]) / 2
linea((ina["cx"], ina["top"]), (rpi["cx"], rpi["b"])); etq(ina["cx"] + 5, ym - 1, "bus 1", "start")
linea((rpi["r"], rpi["cy"]), (r2["x"], rpi["cy"])); linea((ina["r"], ina["cy"]), (r2["x"], ina["cy"]))
# instrumento externo: anotación fuera del marco de hardware, sin forma de bloque
ax, aw, ay, ah = colx[0] - 2, BW + 4, yr2 - 1, h2 + 1
o.append(f'<rect x="{ax}" y="{ay}" width="{aw}" height="{ah}" rx="6" fill="#f4f4f4" stroke="#8a8a8a" stroke-width="0.8" stroke-dasharray="2 2"/>')
cxa = ax + aw / 2
o.append(f'<text x="{cxa}" y="{ay + 12}" text-anchor="middle" font-size="6.8" font-weight="bold" letter-spacing="0.6" fill="#666">INSTRUMENTO EXTERNO</text>')
for i, t in enumerate(["Analizador lógico:", "solo visualiza los", "pulsos de SDA y SCL"]):
    o.append(f'<text x="{cxa}" y="{ay + 26 + i * 10.6:.1f}" text-anchor="middle" font-size="8.4" font-style="italic" fill="#444">{t}</text>')
    if ancho(t, 8.4) > aw - 8: errores.append(t)
o.append(f'<polyline points="{bus["cx"]},{bus["b"]} {bus["cx"]},{ym} {cxa},{ym} {cxa},{ay}" fill="none" stroke="#777" stroke-width="0.9" stroke-dasharray="1.5 2"/>')
etq(cxa + 5, ym + 9, "sondas", "start")
# marco de hardware en forma de L (deja fuera el instrumento externo)
p = 6; xL, xR, yT, yB, xF, yC = esp["x"] - p, rpi["x"] + rpi["w"] + p, esp["y"] - p, ina["b"] + p, fue["x"] - p, esp["b"] + 4
marcos.append(f'<path d="M{xL + 4},{yT} H{xR - 4} Q{xR},{yT} {xR},{yT + 4} V{yB - 4} Q{xR},{yB} {xR - 4},{yB} H{xF + 4} Q{xF},{yB} {xF},{yB - 4} V{yC} H{xL + 4} Q{xL},{yC} {xL},{yC - 4} V{yT + 4} Q{xL},{yT} {xL + 4},{yT} Z" fill="none" stroke="#8a8a8a" stroke-width="0.8"/>')
an = _fT.getlength("HARDWARE") * 6.8 / 96 + 0.7 * 8 + 8
rotulos.append(f'<rect x="{xR - 8 - an:.1f}" y="{yT - 5:.1f}" width="{an:.1f}" height="10" fill="#fff"/>')
rotulos.append(f'<text x="{xR - 12:.1f}" y="{yT + 2.4:.1f}" text-anchor="end" font-size="6.8" font-weight="bold" letter-spacing="0.7" fill="#555">HARDWARE</text>')
marco([r2], "RESULTADO")
y = yr2 + h2 + PADB; bandas.append((y0, y - y0, 2, ["Banco", "de pruebas"], "Objetivo 2"))
salidas.append((r2, "plataforma de hardware")); entradas.append(esp)

# ---------- Fase 3: comunicación segura sobre I2C (Objetivo 2) ----------
y += BG; y0 = y; yb = y + PAD
te = ["tramas con CRC-16, confirmación y retransmisión; línea READY"]
enl = bloque(colx[0], yb, 3 * BW + 2 * GAP, alto(["Capa de enlace confiable sobre I2C"], te), ["Capa de enlace confiable sobre I2C"], te)
f1 = [(["Cliente TLS 1.3"], ["ESP32", "(wolfSSL)"]), (["Intercambio"], ["de claves: X25519", "o X25519MLKEM768"]), (["Servidor TLS 1.3"], ["Raspberry Pi", "(OpenSSL)"])]
h1 = hf(*f1); yr1 = enl["b"] + RG
cli = bloque(colx[0], yr1, BW, h1, *f1[0]); hs = bloque(colx[1], yr1, BW, h1, *f1[1]); srv = bloque(colx[2], yr1, BW, h1, *f1[2])
r3 = bloque(colx[3], yb, BW, yr1 + h1 - yb, ["Sesión segura"], ["telemetría cifrada", "de extremo", "a extremo"], "out")
linea((cli["r"], cli["cy"]), (hs["x"], hs["cy"]), ini=True); linea((hs["r"], hs["cy"]), (srv["x"], srv["cy"]), ini=True)
linea((cli["cx"], enl["b"]), (cli["cx"], cli["y"]), ini=True); linea((srv["cx"], enl["b"]), (srv["cx"], srv["y"]), ini=True)
linea((srv["r"], srv["cy"]), (r3["x"], srv["cy"]))
marco([enl, cli, hs, srv], "PROCESO", abajo=True); marco([r3], "RESULTADO")
y = yr1 + h1 + PADB + 4; bandas.append((y0, y - y0, 3, ["Comunicación", "segura", "sobre I2C"], "Objetivo 2"))
salidas.append((r3, "sesión TLS clásica o híbrida")); entradas.append(enl)

# ---------- Fase 4: validación de seguridad (Objetivo 3) ----------
y += BG; y0 = y; yb = y + PAD
f1 = [(["Atacante", "simulado"], ["con acceso físico", "al bus"]), (["Captura", "de tramas"], ["búsqueda de la", "telemetría en claro"]),
      (["Alteración y", "repetición"], ["de tramas con", "CRC válido"]), (["Confidencialidad", "e integridad"], ["telemetría ilegible;", "tramas rechazadas", "~impacto social: %", "~de tramas legibles"])]
h1 = hf(*f1)
V = [bloque(colx[i], yb, BW, h1, *f1[i], "out" if i == 3 else "p") for i in range(4)]
for i in range(3): linea((V[i]["r"], V[i]["cy"]), (V[i+1]["x"], V[i+1]["cy"]))
marco(V[:3], "PROCESO", abajo=True); marco([V[3]], "RESULTADO")
y = yb + h1 + PADB + 4; bandas.append((y0, y - y0, 4, ["Validación", "de seguridad"], "Objetivo 3"))
salidas.append((V[3], "modelo seguro")); entradas.append(V[0])

# ---------- Fase 5: evaluación experimental (Objetivo 3) ----------
y += BG; y0 = y; yb = y + PAD
f1 = [(["Ensayo piloto"], ["corridas de", "prueba"]), (["Tamaño", "de muestra"], ["N = 60 corridas", "por configuración"]), (["Campaña de", "mediciones"], ["100 y 400 kbit/s;", "orden aleatorio"])]
h1 = hf(*f1)
P = [bloque(colx[i], yb, BW, h1, *f1[i]) for i in range(3)]
yr2 = yb + h1 + RGM
fj = (["Criterio de Jain"], ["precisión ±5 %,", "confianza 95 %"]); fi = (["Sensor INA219"], ["potencia continua", "en paralelo"])
h2 = max(alto(*fj), alto(*fi) + D3)
jain = bloque(colx[1], yr2 + D3, BW, h2 - D3, *fj, "ext"); ina2 = bloque(colx[2], yr2, BW, h2, *fi, "hw")
r5 = bloque(colx[3], yb, BW, yr2 + h2 - yb, ["Datos abiertos"], ["métricas y", "potencia de", "cada corrida"], "out")
for i in range(2): linea((P[i]["r"], P[i]["cy"]), (P[i+1]["x"], P[i+1]["cy"]))
linea((jain["cx"], jain["y"]), (jain["cx"], P[1]["b"]), dash=True)
linea((ina2["cx"], ina2["top"]), (ina2["cx"], P[2]["b"]), ini=True, dash=True); etq(ina2["cx"] + 6, P[2]["b"] + RGM / 2 + 3, "sincronizados", "start")
linea((P[2]["r"], P[2]["cy"]), (r5["x"], P[2]["cy"])); linea((ina2["r"], ina2["cy"]), (r5["x"], ina2["cy"]))
marco(P, "PROCESO"); marco([jain], "FUENTE EXTERNA", abajo=True); marco([ina2], "HARDWARE", abajo=True); marco([r5], "RESULTADO")
y = yr2 + h2 + PADB; bandas.append((y0, y - y0, 5, ["Evaluación", "experimental"], "Objetivo 3"))
salidas.append((r5, "datos de la campaña")); entradas.append(P[0])

# ---------- Fase 6: análisis de resultados (Objetivo 3) ----------
y += BG; y0 = y; yb = y + PAD
f1 = [(["Energía", "por handshake"], ["E_{hs} =", "∫ (P − P_{reposo}) dt", "~impacto ambiental:", "~mJ por sesión"]),
      (["Estadística"], ["media, IC 95 %,", "pruebas de Welch", "y bootstrap"]),
      (["Comparación"], ["sobrecosto (%) =", "100·(x̄_{híb} − x̄_{clás})", "/ x̄_{clás}"]),
      (["Recomendación"], ["intercambio de", "claves y velocidad", "del bus; informe", "técnico"])]
h1 = hf(*f1)
Z = [bloque(colx[i], yb, BW, h1, *f1[i], "fin" if i == 3 else "p") for i in range(4)]
for i in range(3): linea((Z[i]["r"], Z[i]["cy"]), (Z[i+1]["x"], Z[i+1]["cy"]))
marco(Z[:3], "PROCESO", abajo=True); marco([Z[3]], "PRODUCTO FINAL", abajo=True)
y = yb + h1 + PADB + 4; bandas.append((y0, y - y0, 6, ["Análisis de", "resultados"], "Objetivo 3"))
entradas.append(Z[0])
H = y + 4

# ---------- flechas entre fases ----------
for k in range(5):
    sal, txt = salidas[k]; ent = entradas[k + 1]
    ya = bandas[k][0] + bandas[k][1]; yz = bandas[k + 1][0]; ymm = (ya + yz) / 2
    xe = colx[0] + BW / 2
    linea((sal["cx"], sal["b"]), (sal["cx"], ymm), (xe, ymm), (xe, ent["y"]), grosor=1.3)
    etq((sal["cx"] + xe) / 2, ymm - 3.5, txt, fondo_blanco=True)

for (yy, hh, n, nom, obj) in bandas: franja(yy, hh, n, nom, obj)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H:.0f}" viewBox="0 0 {W} {H:.0f}" font-family="Liberation Sans, Arial, sans-serif">',
       '<defs><marker id="p" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M0,1 L10,5 L0,9 Z" fill="#111"/></marker>'
       '<marker id="q" viewBox="0 0 10 10" refX="0" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto"><path d="M10,1 L0,5 L10,9 Z" fill="#111"/></marker></defs>',
       f'<rect width="{W}" height="{H:.0f}" fill="#fff"/>'] + fondo + marcos + o + rotulos + ["</svg>"]
open("bloques_v5.html", "w").write('<!doctype html><meta charset="utf-8"><body style="margin:0;background:#fff"><div id="fig" style="display:inline-block;line-height:0">' + "\n".join(svg) + "</div>")
print("lienzo", W, "x", round(H), "| textos que no caben:", errores or "ninguno")
