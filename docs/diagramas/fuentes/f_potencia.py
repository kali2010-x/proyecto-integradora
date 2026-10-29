from fc import *
d = Diagrama()
XR, XL = 470, 60
M = Col(d, 250, 12, w=240, gap=17)
m1 = M.add("term", ["Inicio"], w=110)
m2 = M.add("box", ["Fijar el proceso al núcleo 3", "de la Raspberry Pi"])
m3 = M.add("box", ["Configurar el INA219 (0x40):", "ADC de 12 bits, 1 muestra"])
m4 = M.add("io", ["Abrir el CSV (t_ns, V, mA, mW)"])
yj1 = m4["b"] + 13
m5 = M.add("io", ["Leer V e I del INA219 con", "marca de tiempo; P = V · I"], gap=26)
m6 = M.add("io", ["Escribir la fila en el CSV"])
m7 = M.add("dec", ["¿Pasó 1 s desde", "el último volcado?"], w=196, h=62)
yj2 = m7["b"] + 21
fl = d.nodo("box", XR, m7["cy"] - 14, ["Volcar a disco"], w=150)
d.flecha(m7["right"], fl["left"]); d.etq(m7["right"][0] + 6, m7["cy"] - 5, "Sí")
m8 = M.add("dec", ["¿Señal de parada o", "duración cumplida?"], w=206, h=64, gap=34, etq="No")
d.flecha(fl["bot"], (XR, yj2), (M.cx + 1, yj2))
d.flecha(m8["left"], (XL, m8["cy"]), (XL, yj1), (M.cx - 1, yj1)); d.etq(m8["left"][0] - 6, m8["cy"] - 5, "No", "end")
m9 = M.add("io", ["Cerrar el archivo e informar", "las muestras por segundo"], gap=30)
d.etq(M.cx + 6, m8["b"] + 22, "Sí")
m10 = M.add("term", ["Fin"], w=100)
d.marco(XL - 14, yj1 - 7, 560 - (XL - 14), m8["b"] - yj1 + 14, "Ciclo de muestreo")
d.guardar("flujo_potencia")
