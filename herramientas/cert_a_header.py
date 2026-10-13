"""Convierte certs/servidor.pem en esp32/firmware/main/cert_servidor.h (para compilarlo en el ESP32).
Uso: python3 herramientas/cert_a_header.py"""
import os
raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pem = open(os.path.join(raiz, "certs", "servidor.pem")).read()
lineas = "".join(f'"{l}\\n"\n' for l in pem.strip().splitlines())
out = os.path.join(raiz, "esp32", "firmware", "main", "cert_servidor.h")
open(out, "w").write("/* Generado por herramientas/cert_a_header.py - NO editar */\n"
                     "#pragma once\nstatic const char CERT_SERVIDOR_PEM[] =\n" + lineas + ";\n")
print("escrito", out)
