from fc import *
d = Diagrama()
XR, XE, XI = 478, 594, 34           # carril derecho, borde derecho y carril izquierdo
M = Col(d, 236, 12, w=232, gap=17)
m1 = M.add("term", ["Inicio de la corrida", "(grupo, tamaño, número)"], w=200)
m2 = M.add("box", ["Reiniciar el enlace en", "ambos extremos"])
m3 = M.add("dec", ["¿Reinicio", "correcto?"], w=150, h=56)
rf = d.nodo("box", XR, m3["cy"] - 20.5, ["Registrar el error", "«reset_fallido»"], w=170)
d.flecha(m3["right"], rf["left"]); d.etq(m3["right"][0] + 6, m3["cy"] - 5, "No")
m4 = M.add("io", ["Enviar la orden START al ESP32"], etq="Sí")
m5 = M.add("dec", ["¿Grupo sin TLS?"], w=160, h=48, gap=26)
eco = d.nodo("box", XR, m5["b"] + 6, ["Devolver en claro", "n mensajes (control)"], w=170)
d.flecha(m5["right"], (XR, m5["cy"]), eco["top"]); d.etq(m5["right"][0] + 6, m5["cy"] - 5, "Sí")
m6 = M.add("box", ["Handshake TLS 1.3: medir etapas,", "bytes y grupo; eco cifrado", "de n mensajes"], etq="No")
m7 = M.add("dec", ["¿Hay bloque de", "rendimiento?"], w=170, h=60)
m8 = M.add("box", ["Recibir 4 KiB, calcular", "kbit/s y responder «OK»"], etq="Sí")
yj = m8["b"] + 13
m9 = M.add("box", ["Esperar el cierre de la", "sesión (close_notify)"], gap=26)
d.flecha(m7["left"], (XI, m7["cy"]), (XI, yj), (M.cx - 1, yj)); d.etq(m7["left"][0] - 6, m7["cy"] - 5, "No", "end")
yj2 = m9["b"] + 13
d.marco(XI - 18, m5["y"] - 12, 576 - (XI - 18), m9["b"] - m5["y"] + 20, "Bloque protegido (try)")
m10 = M.add("dec", ["¿Ocurrió SSLError o", "tiempo agotado?"], w=210, h=66, gap=28)
d.flecha(eco["bot"], (XR, yj2), (M.cx + 1, yj2))
er = d.nodo("box", XR, m10["cy"] - 14, ["Registrar el error"], w=170)
d.flecha(m10["right"], er["left"]); d.etq(m10["right"][0] + 6, m10["cy"] - 5, "Sí")
yj3 = m10["b"] + 21
m11 = M.add("io", ["Esperar el reporte del ESP32", "(estado, tiempos, memoria)"], gap=33, etq="No")
d.flecha(er["bot"], (XR, yj3), (M.cx + 1, yj3))
yj4 = m11["b"] + 13
m12 = M.add("term", ["Fin: devolver el resultado", "con los contadores del enlace"], w=250, gap=26)
d.flecha(rf["right"], (XE, rf["cy"]), (XE, yj4), (M.cx + 1, yj4))
d.guardar("flujo_servidor")
