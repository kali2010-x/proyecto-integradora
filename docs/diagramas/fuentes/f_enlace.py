from fc import *
d = Diagrama()
XL, XS = 305, 596          # carril auxiliar del maestro y carril derecho del esclavo
M = Col(d, 128, 30, w=196, gap=18)
m1 = M.add("term", ["Inicio del intercambio"], w=170)
m2 = M.add("dec", ["¿Trama pendiente", "o datos en cola?"], w=196, h=64)
m3 = M.add("box", ["Armar trama DATOS:", "nueva o retransmitida"], etq="Sí")
poll = d.nodo("box", XL, m3["y"], ["Armar trama de", "sondeo (POLL)"], w=140)
d.flecha(m2["right"], (XL, m2["cy"]), poll["top"]); d.etq(m2["right"][0] + 6, m2["cy"] - 5, "No")
yj = m3["b"] + 14
m4 = M.add("io", ["Escribir la trama por I2C"], gap=28)
d.flecha(poll["bot"], (XL, yj), (M.cx + 1, yj))
m5 = M.add("box", ["Esperar READY = 1 (máx. 200 ms;", "si vence, contar tiempo agotado)"])
m6 = M.add("io", ["Leer la respuesta", "de 128 bytes"])
m7 = M.add("dec", ["¿CRC-16", "válido?"], w=140, h=58)
crc = d.nodo("box", XL, m7["b"] - 6, ["Contar error de", "CRC (reintento)"], w=140)
d.flecha(m7["right"], (XL, m7["cy"]), crc["top"]); d.etq(m7["right"][0] + 6, m7["cy"] - 5, "No")
m8 = M.add("box", ["Si el ACK confirma la trama", "pendiente, liberarla"], etq="Sí")
m9 = M.add("dec", ["¿Secuencia", "esperada?"], w=150, h=58)
d.flecha(m9["right"], (XL - 1, m9["cy"])); d.etq(m9["right"][0] + 6, m9["cy"] - 5, "No (duplicada)")
m10 = M.add("box", ["Entregar los datos a TLS", "o el mensaje de control"], etq="Sí")
yf = m10["b"] + 14
m11 = M.add("term", ["Fin"], w=100, gap=28)
d.flecha(crc["bot"], (XL, yf), (M.cx + 1, yf))
d.marco(4, 14, 382, m11["b"] - 14 + 10, "Raspberry Pi: maestro (enlace.py)")

# ---------- esclavo ----------
E_ = Col(d, 500, m4["y"] - 8, w=176, gap=18)
e1 = E_.add("term", ["Trama recibida", "(interrupción I2C)"], w=170)
e2 = E_.add("box", ["READY = 0 y poner", "la trama en la cola"])
e3 = E_.add("dec", ["¿CRC-16", "válido?"], w=140, h=58)
e4 = E_.add("box", ["Procesar RESET, ACK,", "secuencia y datos"], etq="Sí")
yj2 = e4["b"] + 14
e5 = E_.add("box", ["Armar la respuesta", "(pendiente o POLL)", "con ACK y CRC-16"], gap=28)
d.flecha(e3["right"], (XS, e3["cy"]), (XS, yj2), (E_.cx + 1, yj2)); d.etq(e3["right"][0] + 4, e3["cy"] - 5, "No")
e6 = E_.add("io", ["Cargar la respuesta en", "el búfer del esclavo"])
e7 = E_.add("term", ["READY = 1"], w=120)
d.marco(400, m4["y"] - 22, 200, e7["b"] - m4["y"] + 32, "ESP32: esclavo (enlace.c)")
# ---------- tráfico por el bus (punteado) ----------
d.flecha(m4["right"], (e1["x"], m4["cy"]), dash=True); d.etq((m4["right"][0] + e1["x"]) / 2 + 30, m4["cy"] - 5, "trama", "middle", 9.5, True)
XB = 393
d.flecha(e7["left"], (XB, e7["cy"]), (XB, m6["cy"]), (m6["r"] - 8, m6["cy"]), dash=True)
d.etq((m6["r"] + XB) / 2 + 20, m6["cy"] - 5, "respuesta", "middle", 9.5, True)
d.guardar("flujo_enlace")
