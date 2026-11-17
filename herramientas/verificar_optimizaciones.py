"""
verificar_optimizaciones.py - Comprueba que el código optimizado se comporta igual que el original.

  python3 herramientas/verificar_optimizaciones.py

1) CRC en Python: binascii.crc_hqx frente al cálculo bit a bit original (equivalencia y tiempo).
2) Espera de READY por flanco: lógica probada con una línea GPIO simulada.
3) CRC por tabla y buffers circulares en C (enlace.c): compila y ejecuta sim/prueba_enlace.c.
No necesita el ESP32 ni el bus: en la Raspberry Pi, antes de la campaña, hay que repetir además la
prueba de eco de 10 000 tramas (pi/prueba_eco.py) y las pruebas de seguridad (pi/ataque.py).
"""
import os, random, subprocess, sys, threading, time, timeit
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "pi"))
import enlace

fallos = 0
# ---------------------------------------------------------------- 1) CRC en Python
rnd = random.Random(42)
assert enlace.crc16_ccitt(b"123456789") == 0x29B1
for _ in range(20000):
    d = bytes(rnd.getrandbits(8) for _ in range(rnd.randint(1, 126)))
    if enlace.crc16_ccitt(d) != enlace.crc16_ccitt_referencia(d):
        fallos += 1
d = bytes(rnd.getrandbits(8) for _ in range(126))
t_ref = timeit.timeit(lambda: enlace.crc16_ccitt_referencia(d), number=3000) / 3000 * 1e6
t_new = timeit.timeit(lambda: enlace.crc16_ccitt(d), number=3000) / 3000 * 1e6
print(f"1) CRC en Python: 20 000 tramas, diferencias = {fallos}. Bit a bit {t_ref:.0f} us/trama; optimizado {t_new:.2f} us/trama")

# ---------------------------------------------------------------- 2) READY por flanco (línea simulada)
class LineaFalsa:
    """Imita gpiod.LineRequest: nivel del pin y cola de flancos de subida."""
    def __init__(self): self.nivel, self.eventos, self.cv = 0, 0, threading.Condition()
    def subir(self):
        with self.cv: self.nivel = 1; self.eventos += 1; self.cv.notify_all()
    def bajar(self):
        with self.cv: self.nivel = 0
    def get_value(self, pin): return self.nivel
    def wait_edge_events(self, t):
        with self.cv:
            if not self.eventos and t: self.cv.wait(t)
            return self.eventos > 0
    def read_edge_events(self):
        with self.cv: n, self.eventos = self.eventos, 0; return [None] * n

bus = enlace.BusI2C.__new__(enlace.BusI2C)
bus.req, bus.pin, bus._activo, bus._por_flanco = LineaFalsa(), 17, 1, True
ok = True
t0 = time.monotonic(); ok &= bus.esperar_ready(0.05) is False and 0.04 < time.monotonic() - t0 < 0.2     # plazo agotado
bus.req.subir(); ok &= bus.esperar_ready(0.05) is True                                                 # ya estaba arriba
bus.req.bajar(); threading.Timer(0.02, bus.req.subir).start()
t0 = time.monotonic(); ok &= bus.esperar_ready(0.2) is True and time.monotonic() - t0 < 0.1               # sube mientras espera
bus.req.bajar(); bus.req.eventos = 3                                                                    # flancos viejos, pin abajo
t0 = time.monotonic(); ok &= bus.esperar_ready(0.05) is False and time.monotonic() - t0 >= 0.04
for _ in range(2000):                                                                                   # carrera subir/esperar
    bus.req.bajar(); threading.Thread(target=bus.req.subir).start(); ok &= bus.esperar_ready(0.5) is True
print("2) Espera de READY por flanco:", "correcta" if ok else "FALLO")
fallos += 0 if ok else 1

# ---------------------------------------------------------------- 3) enlace.c
src = os.path.join(RAIZ, "sim", "prueba_enlace.c"); exe = os.path.join(RAIZ, "sim", "prueba_enlace")
r = subprocess.run(["gcc", "-O2", "-Wall", "-I" + os.path.join(RAIZ, "esp32", "firmware", "main"), src, "-o", exe],
                   capture_output=True, text=True)
if r.returncode:
    print("3) No se pudo compilar sim/prueba_enlace.c:\n", r.stderr); fallos += 1
else:
    r = subprocess.run([exe], capture_output=True, text=True)
    print("3) enlace.c:", r.stdout.strip().replace("\n", "\n   "))
    fallos += 0 if r.returncode == 0 else 1
print("\nRESULTADO:", "todas las comprobaciones pasaron" if not fallos else f"{fallos} comprobaciones fallaron")
sys.exit(1 if fallos else 0)
