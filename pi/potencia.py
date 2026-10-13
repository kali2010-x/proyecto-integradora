"""
potencia.py - Lectura del INA219 (bus I2C 1 de la Raspberry) para medir el consumo del sistema.

El INA219 está EN SERIE con la alimentación de 5 V de la Raspberry; el ESP32 se alimenta
desde un puerto USB de la Raspberry, así que su consumo queda incluido (consumo total del sistema).

Uso como registrador continuo (en una terminal aparte, durante la campaña):
  taskset -c 3 python3 potencia.py --salida ../data/raw/potencia_bloqueA.csv
  (Ctrl+C para detener)
"""
import argparse, csv, os, signal, sys, time


class MedidorINA219:
    def __init__(self, direccion=0x40):
        import board, busio
        from adafruit_ina219 import INA219, ADCResolution
        self.ina = INA219(busio.I2C(board.SCL, board.SDA), addr=direccion)
        # 12 bits, 1 muestra: conversión de ~532 us por canal (la más rápida con 12 bits)
        self.ina.bus_adc_resolution = ADCResolution.ADCRES_12BIT_1S
        self.ina.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_1S

    def leer(self):
        """Devuelve (t_ns, voltaje_V, corriente_mA, potencia_mW)."""
        v = self.ina.bus_voltage          # V en VIN- (lado de la Raspberry)
        i = self.ina.current              # mA
        return time.monotonic_ns(), v, i, v * i


class MedidorSimulado:
    """Para probar el flujo sin hardware: ~2,9 W en reposo + carga proporcional a la CPU."""
    def __init__(self, *a, **k):
        import psutil, random
        self.ps, self.rnd = psutil, random.Random(1)
        self.ps.cpu_percent(None)

    def leer(self):
        time.sleep(0.002)
        cpu = self.ps.cpu_percent(None)
        i = 570 + 3.0 * cpu + self.rnd.gauss(0, 4)
        return time.monotonic_ns(), 5.05, i, 5.05 * i


def crear_medidor(simular=False):
    return MedidorSimulado() if simular else MedidorINA219()


def registrar(ruta, simular=False, duracion_s=None):
    m = crear_medidor(simular)
    detener = {"v": False}
    signal.signal(signal.SIGINT, lambda *_: detener.update(v=True))
    signal.signal(signal.SIGTERM, lambda *_: detener.update(v=True))
    os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
    n, t_ini, ultimo_flush = 0, time.monotonic(), time.monotonic()
    with open(ruta, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t_ns", "v_V", "i_mA", "p_mW"])
        while not detener["v"]:
            w.writerow(m.leer())
            n += 1
            ahora = time.monotonic()
            if ahora - ultimo_flush > 1:
                f.flush(); ultimo_flush = ahora
            if duracion_s and ahora - t_ini >= duracion_s:
                break
    dt = time.monotonic() - t_ini
    print(f"{n} muestras en {dt:.1f} s ({n/dt:.0f} muestras/s) -> {ruta}", file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", help="archivo CSV donde registrar")
    ap.add_argument("--resumen", help="en vez de registrar, resume un CSV ya registrado")
    ap.add_argument("--simular", action="store_true")
    ap.add_argument("--duracion", type=float, default=None, help="segundos (por defecto hasta Ctrl+C)")
    ap.add_argument("--nucleo", type=int, default=None, help="fijar el proceso a un núcleo de CPU (p. ej. 3)")
    a = ap.parse_args()
    if a.resumen:
        import pandas as pd
        d = pd.read_csv(a.resumen)
        dur = (d.t_ns.iloc[-1] - d.t_ns.iloc[0]) / 1e9
        print(f"{a.resumen}: V={d.v_V.mean():.3f} V  I={d.i_mA.mean():.1f} mA (desv {d.i_mA.std():.1f})  "
              f"P={d.p_mW.mean():.0f} mW  muestras/s={len(d)/dur:.0f}")
        sys.exit(0)
    if not a.salida:
        ap.error("indique --salida o --resumen")
    if a.nucleo is not None and hasattr(os, "sched_setaffinity"):
        try:
            os.sched_setaffinity(0, {a.nucleo})
        except OSError:
            print(f"aviso: no se pudo fijar el núcleo {a.nucleo}", file=sys.stderr)
    registrar(a.salida, a.simular, a.duracion)
