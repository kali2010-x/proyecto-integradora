"""
prueba_eco.py - Semanas 3-4: verifica que el bus I2C Raspberry<->ESP32 transmite sin errores.
El ESP32 debe tener el firmware con MODO_ECO=1 (devuelve cada trama tal cual).

  python3 prueba_eco.py --frame 128 --n 10000              (bus real)
  python3 prueba_eco.py --sim --frame 128 --n 2000         (simulador en modo eco)
"""
import argparse, json, os, time, random
from enlace import BusI2C, BusSimulado
import sistema

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--sim", action="store_true")
ap.add_argument("--puerto", type=int, default=5555)
ap.add_argument("--bus", type=int, default=3)
ap.add_argument("--dir", type=lambda x: int(x, 0), default=0x28)
ap.add_argument("--ready", type=int, default=17)
ap.add_argument("--frame", type=int, default=128)
ap.add_argument("--n", type=int, default=10000)
ap.add_argument("--timeout-ready", type=float, default=0.2)
a = ap.parse_args()

bus = BusSimulado(puerto=a.puerto, frame_size=a.frame) if a.sim else BusI2C(a.bus, a.dir, a.ready)
rnd = random.Random(42)
ok = distintas = err_io = sin_ready = 0
bits_erroneos = 0
t0 = time.monotonic()
for i in range(a.n):
    trama = bytes(rnd.getrandbits(8) for _ in range(a.frame))
    try:
        bus.escribir(trama)
    except OSError:
        err_io += 1
        continue                       # sin escritura exitosa no se lee (mantiene 1:1)
    if not bus.esperar_ready(a.timeout_ready):
        sin_ready += 1
    try:
        resp = bus.leer(a.frame)
    except OSError:
        err_io += 1
        continue
    if resp == trama:
        ok += 1
    else:
        distintas += 1
        bits_erroneos += sum(bin(x ^ y).count("1") for x, y in zip(resp, trama))
    if (i + 1) % 1000 == 0:
        print(f"  {i+1}/{a.n}  ok={ok} distintas={distintas} err_io={err_io} sin_ready={sin_ready}")
dt = time.monotonic() - t0
bits_bus = 2 * a.frame * 8 * (ok + distintas)
res = {
    "fecha": time.strftime("%Y-%m-%d %H:%M:%S"), "modo": "sim" if a.sim else "i2c",
    "frame_bytes": a.frame, "tramas": a.n, "correctas": ok, "distintas": distintas,
    "errores_io": err_io, "timeouts_ready": sin_ready,
    "tasa_error_trama": (distintas + err_io) / a.n,
    "ber_estimado": bits_erroneos / bits_bus if bits_bus else None,
    "duracion_s": round(dt, 3), "intercambios_por_s": round((ok + distintas) / dt, 1),
    "tasa_bus_kbps": round(bits_bus / dt / 1e3, 2),
    **({} if a.sim else sistema.estado(bus=a.bus)),
}
print(json.dumps(res, indent=2))
dest = os.path.join(RAIZ, "docs", "evidencias")
os.makedirs(dest, exist_ok=True)
ruta = os.path.join(dest, f"eco_{res['modo']}_f{a.frame}_{time.strftime('%Y%m%d_%H%M%S')}.json")
json.dump(res, open(ruta, "w"), indent=2)
print("Guardado en", ruta)
print("RESULTADO:", "APROBADO (0 errores)" if distintas + err_io == 0 else "HAY ERRORES: revisar cableado/velocidad/tamaño de trama")
