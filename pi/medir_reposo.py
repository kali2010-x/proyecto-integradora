"""
medir_reposo.py - Mide la potencia del sistema en REPOSO (P_reposo de la fórmula de energía).
Hacerlo con el ESP32 conectado y alimentado desde la Raspberry, sin ningún programa del experimento
corriendo. Se repite al inicio de cada bloque de la campaña.

  python3 medir_reposo.py --duracion 300 --etiqueta inicial
"""
import argparse, json, os, statistics, time
from potencia import registrar
import sistema

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def medir(duracion=300, etiqueta="reposo", simular=False):
    sello = time.strftime("%Y%m%d_%H%M%S")
    csv_ruta = os.path.join(RAIZ, "data", "raw", f"reposo_{etiqueta}_{sello}.csv")
    est_ini = sistema.estado()
    registrar(csv_ruta, simular, duracion)
    p = [float(l.split(",")[3]) for l in open(csv_ruta).readlines()[1:]]
    i = [float(l.split(",")[2]) for l in open(csv_ruta).readlines()[1:]]
    res = {"etiqueta": etiqueta, "fecha": sello, "duracion_s": duracion, "n_muestras": len(p),
           "p_reposo_mW": statistics.mean(p), "p_desv_mW": statistics.stdev(p),
           "i_media_mA": statistics.mean(i), "estado_inicio": est_ini, "estado_fin": sistema.estado(),
           "csv": os.path.relpath(csv_ruta, RAIZ)}
    ruta = os.path.join(RAIZ, "docs", "evidencias", f"reposo_{etiqueta}_{sello}.json")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    json.dump(res, open(ruta, "w"), indent=2)
    print(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--duracion", type=float, default=300)
    ap.add_argument("--etiqueta", default="reposo")
    ap.add_argument("--simular", action="store_true")
    a = ap.parse_args()
    medir(a.duracion, a.etiqueta, a.simular)
