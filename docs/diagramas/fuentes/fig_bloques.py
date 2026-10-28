import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, Rectangle

plt.rcParams["font.family"] = "DejaVu Sans"
VERDE, VERDE_O, FONDO = "#2a7f7a", "#1f7a6e", "#d7efed"
AMBAR, AMBAR_F = "#b38a1d", "#fff4d6"
ROJO, ROJO_F = "#aa3333", "#fbe3e3"
GRIS = "#3d5a59"

fig, ax = plt.subplots(figsize=(8.2, 7.6), dpi=220)
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")


def caja(x, y, w, h, t, fc=FONDO, ec=VERDE, fs=8.6, ls="-", tc="black", r=1.2):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=f"round,pad=0.2,rounding_size={r}",
                                fc=fc, ec=ec, lw=1.2, ls=ls))
    ax.text(x, y, t, ha="center", va="center", fontsize=fs, color=tc)


def hexa(x, y, w, h, t):
    d = w * 0.18
    ax.add_patch(Polygon([(x - w / 2, y), (x - w / 2 + d, y + h / 2), (x + w / 2 - d, y + h / 2), (x + w / 2, y),
                          (x + w / 2 - d, y - h / 2), (x - w / 2 + d, y - h / 2)], closed=True, fc=VERDE_O, ec=VERDE_O))
    ax.text(x, y, t, ha="center", va="center", fontsize=8.6, color="white", fontweight="bold")


def cilindro(x, y, w, h, t):
    e = 2.0
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc="#f3e6b8", ec="none"))
    ax.plot([x - w / 2, x - w / 2], [y - h / 2, y + h / 2], color=AMBAR, lw=1.2)
    ax.plot([x + w / 2, x + w / 2], [y - h / 2, y + h / 2], color=AMBAR, lw=1.2)
    ax.add_patch(Ellipse((x, y - h / 2), w, e, fc="#f3e6b8", ec=AMBAR, lw=1.2))
    ax.add_patch(Ellipse((x, y + h / 2), w, e, fc="#f7eecb", ec=AMBAR, lw=1.2))
    ax.text(x, y - 0.4, t, ha="center", va="center", fontsize=8)


def flecha(p, q, txt=None, color=GRIS, ls="-", ambos=False, tpos=None, fs=7.4, ha="center"):
    ax.annotate("", xy=q, xytext=p, arrowprops=dict(arrowstyle="<|-|>" if ambos else "-|>", color=color, lw=1.1,
                                                     ls=ls, shrinkA=0, shrinkB=0, mutation_scale=9))
    if txt:
        tx, ty = tpos if tpos else ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        ax.text(tx, ty, txt, fontsize=fs, color=color, ha=ha, va="center")


def poli(puntos, txt=None, color=GRIS, ls="-", tpos=None, ha="left"):
    xs, ys = zip(*puntos)
    ax.plot(xs[:-1], ys[:-1], color=color, lw=1.1, ls=ls)
    flecha(puntos[-2], puntos[-1], color=color, ls=ls)
    if txt:
        ax.text(*tpos, txt, fontsize=7.4, color=color, ha=ha, va="center")


def grupo(x0, y0, x1, y1, titulo, color=VERDE):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0.3,rounding_size=2",
                                fc="none", ec=color, lw=1.1, ls=(0, (4, 3))))
    ax.text((x0 + x1) / 2, y1 - 2.6, titulo, ha="center", va="center", fontsize=8.4, color=color, fontweight="bold")


# ---------------- Nodo sensor y unidad de borde ----------------
grupo(1.5, 40, 32.5, 99, "NODO SENSOR — ESP32\ncliente TLS · esclavo I2C")
grupo(67.5, 40, 98.5, 99, "UNIDAD DE BORDE — RPi 4\nservidor TLS · maestro I2C")
X1, X2 = 17, 83
caja(X1, 86, 24, 6, "Generador de telemetría\n(mensajes de prueba)")
hexa(X1, 73, 27, 8, "Cliente TLS 1.3\nwolfSSL 5.9.4")
caja(X1, 60, 24, 6, "Capa de enlace\ntramas · CRC-16 · ARQ")
caja(X1, 48, 24, 6, "I2C esclavo (0x28)\n+ salida READY")
caja(X2, 86, 24, 6, "Orquestador de campaña\ncampana.py")
hexa(X2, 73, 27, 8, "Servidor TLS 1.3\nOpenSSL 3.5.7")
caja(X2, 60, 24, 6, "Capa de enlace\nenlace.py")
caja(X2, 48, 24, 6, "I2C maestro (bus 3)\n+ lectura READY")
for X in (X1, X2):
    flecha((X, 82.8), (X, 77.2), ambos=(X == X2))
    flecha((X, 68.8), (X, 63.2), ambos=True)
    flecha((X, 56.8), (X, 51.2), ambos=True)
ax.text(X2 + 1.2, 80, "corridas", fontsize=7, color=GRIS)

# Sesión TLS extremo a extremo
flecha((30.6, 73), (69.4, 73), ambos=True, color=VERDE_O, ls=(0, (4, 2)))
ax.text(50, 76.4, "Sesión TLS 1.3 extremo a extremo", ha="center", fontsize=7.8, color=VERDE_O, fontweight="bold")
ax.text(50, 69.6, "X25519 (línea base)  |  X25519MLKEM768 (híbrido)", ha="center", fontsize=7.4, color=VERDE_O)

# Bus I2C
caja(50, 48, 26, 11, "BUS I2C DEDICADO\nSDA · SCL · pull-ups 4,7 kΩ\n100 kbit/s  |  400 kbit/s\ntramas de 128 bytes",
     fc=AMBAR_F, ec=AMBAR, fs=8, r=0.6)
flecha((29.2, 48), (36.8, 48), ambos=True)
flecha((63.2, 48), (70.8, 48), ambos=True)

# Pruebas de seguridad
caja(42, 31, 17, 6.5, "Pruebas de ataque\nataque.py", fc=ROJO_F, ec=ROJO, ls=(0, (3, 2)), fs=7.8)
caja(59, 31, 15, 6.5, "Analizador lógico\n(escucha el bus)", fc=ROJO_F, ec=ROJO, ls=(0, (3, 2)), fs=7.8)
flecha((42, 34.4), (44, 42.3), color=ROJO, ls=(0, (3, 2)))
flecha((59, 34.4), (56, 42.3), color=ROJO, ls=(0, (3, 2)))
ax.text(26.5, 31, "captura,\naltera y\nreinyecta\ntramas", fontsize=7, color=ROJO, ha="center", va="center")

# ---------------- Medición, datos y análisis ----------------
grupo(64, 2, 99, 19, "", color=AMBAR)
ax.text(81.5, 4.6, "MEDICIÓN DE ENERGÍA", ha="center", fontsize=8.4, color=AMBAR, fontweight="bold")
caja(91, 11, 11, 6, "Fuente\n5 V", fc=AMBAR_F, ec=AMBAR, fs=8)
caja(76, 11, 13, 6, "Sensor INA219\n(bus 1, 0x40)", fc=AMBAR_F, ec=AMBAR, fs=7.8)
caja(55, 11, 14, 6, "Registrador\npotencia.py", fc=AMBAR_F, ec=AMBAR, fs=7.8)
cilindro(38, 11, 13, 7, "Datos\nJSONL · CSV")
caja(21, 11, 13, 6, "Análisis\nanalisis.py", fs=7.8)
caja(6, 11, 9.5, 8, "Tiempo\nbytes\nmemoria\nenergía", fc="white", ec=GRIS, fs=7, r=0.4)
flecha((85.3, 11), (82.7, 11))
flecha((69.3, 11), (62.2, 11), "V · I · P", tpos=(65.8, 13.6), fs=7)
flecha((47.8, 11), (44.6, 11))
flecha((31.4, 11), (27.6, 11))
flecha((14.4, 11), (10.9, 11))
# alimentación hacia la Pi
poli([(78, 14.2), (78, 39.6)], color=AMBAR, ls=(0, (1, 2)))
ax.text(79, 28, "alimentación de\nla Pi y del ESP32\n(USB)", fontsize=6.8, color=AMBAR, ha="left", va="center")
# métricas de cada corrida hacia los datos
poli([(69, 40), (69, 26), (38, 26), (38, 15.4)], color=GRIS)
ax.text(51, 24.4, "métricas de cada corrida", fontsize=7, color=GRIS, ha="center")

plt.savefig("../fig1_bloques.png", bbox_inches="tight", facecolor="white")
print("ok")
