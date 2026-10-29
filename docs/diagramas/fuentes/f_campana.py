from fc import *
d = Diagrama()
XR, XL = 482, 9
M = Col(d, 236, 12, w=232, gap=17)
m1 = M.add("term", ["Inicio"], w=110)
m2 = M.add("io", ["Leer los parámetros: bloque,", "repeticiones, grupos y tamaños"])
m3 = M.add("box", ["Generar el plan aleatorio", "(grupo × tamaño × repetición,", "semilla 42)"])
m4 = M.add("box", ["Lanzar el registrador de", "potencia en el núcleo 3"])
m5 = M.add("dec", ["¿Registrador", "activo?"], w=160, h=58)
te = d.nodo("term", XR, m5["cy"] - 14, ["Terminar con error"], w=170)
d.flecha(m5["right"], te["left"]); d.etq(m5["right"][0] + 6, m5["cy"] - 5, "No")
m6 = M.add("box", ["Reposo inicial de 60 s", "(potencia de reposo)"], etq="Sí")
yj1 = m6["b"] + 13
m7 = M.add("dec", ["¿Quedan corridas", "en el plan?"], w=190, h=62, gap=26)
yj2 = m7["b"] + 22
m8 = M.add("dec", ["¿Temperatura", "> 75 °C?"], w=170, h=60, gap=34)
d.etq(M.cx + 6, m7["b"] + 13, "Sí")
esp = d.nodo("box", 72, m8["cy"] - 14, ["Esperar 10 s"], w=100)
d.flecha(m8["left"], esp["right"]); d.etq(m8["left"][0] - 6, m8["cy"] - 5, "Sí", "end")
d.flecha(esp["top"], (esp["cx"], yj2), (M.cx - 1, yj2))
m9 = M.add("pre", ["Ejecutar la corrida", "(servidor TLS, figura 4)"], etq="No")
m10 = M.add("io", ["Guardar el resultado en JSONL", "(con temperatura y throttling)"])
m11 = M.add("box", ["Pausa de 3 s"])
yb = m11["b"] + 14
d.flecha(m11["bot"], (M.cx, yb), (XL, yb), (XL, yj1), (M.cx - 1, yj1), cabeza=True)
# salida del ciclo
r1 = d.nodo("box", XR, m8["y"], ["Reposo final de 60 s", "(deriva de la potencia)"], w=200)
d.flecha(m7["right"], (XR, m7["cy"]), r1["top"]); d.etq(m7["right"][0] + 6, m7["cy"] - 5, "No")
r2 = d.nodo("io", XR, r1["b"] + 17, ["Detener el registrador", "y guardar meta.json"], w=200)
d.flecha(r1["bot"], r2["top"])
r3 = d.nodo("term", XR, r2["b"] + 17, ["Fin"], w=100)
d.flecha(r2["bot"], r3["top"])
d.marco(2, yj1 - 7, 372, yb - yj1 + 15, "Ciclo de corridas")
d.guardar("flujo_campana")
