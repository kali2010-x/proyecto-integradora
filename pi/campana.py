"""
campana.py - Semanas 9-10: ejecuta un BLOQUE de la campaña de mediciones.

Un bloque = un modo de bus (estándar 100 kbit/s o rápido 400 kbit/s). La velocidad del bus se fija
en /boot/firmware/config.txt y requiere reiniciar, por eso cada modo es un bloque (diseño por bloques).
Dentro del bloque se aleatoriza el orden de (grupo x tamaño de mensaje) con semilla fija.

El script:
  1) lanza el registrador del INA219 en otro núcleo,
  2) deja una ventana de REPOSO al inicio (P_reposo del bloque),
  3) ejecuta las corridas en orden aleatorio, revisando temperatura y throttling,
  4) deja otra ventana de reposo al final y guarda todo en data/raw/.

  python3 campana.py --bloque estandar --reps 30                (real)
  python3 campana.py --bloque estandar --reps 10 --piloto       (prueba piloto)
  python3 campana.py --sim --simular-potencia --bloque sim --reps 3 --reposo 5   (simulador)
"""
import argparse, json, os, random, signal, ssl, subprocess, sys, time, platform
import servidor_tls as st
import sistema

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AQUI = os.path.dirname(os.path.abspath(__file__))


def git_commit():
    try:
        return subprocess.run(["git", "-C", RAIZ, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    st.argumentos_comunes(ap)
    ap.add_argument("--bloque", required=True, help="etiqueta del bloque: estandar | rapido | sim")
    ap.add_argument("--reps", type=int, default=30, help="repeticiones por configuración")
    ap.add_argument("--piloto", action="store_true", help="marca la campaña como piloto")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--grupos", default="clasico,hibrido")
    ap.add_argument("--tamanos", default="32,128,512", help="bytes del mensaje de telemetría")
    ap.add_argument("--n-msgs", type=int, default=10)
    ap.add_argument("--bulk", type=int, default=4096)
    ap.add_argument("--pausa", type=float, default=3.0, help="segundos de reposo entre corridas")
    ap.add_argument("--reposo", type=float, default=60.0, help="segundos de reposo al inicio y al final")
    ap.add_argument("--temp-max", type=float, default=75.0)
    ap.add_argument("--simular-potencia", action="store_true")
    a = ap.parse_args()

    if hasattr(os, "sched_setaffinity"):
        try: os.sched_setaffinity(0, {2})
        except OSError: pass
    tipo = "piloto" if a.piloto else "campana"
    sello = time.strftime("%Y%m%d_%H%M%S")
    base = os.path.join(RAIZ, "data", "raw", f"{tipo}_{a.bloque}_{sello}")
    ruta_pot, ruta_runs, ruta_meta = base + "_potencia.csv", base + "_corridas.jsonl", base + "_meta.json"

    # ---- plan aleatorizado ----
    grupos = a.grupos.split(",")
    tamanos = [int(x) for x in a.tamanos.split(",")]
    plan = [(g, t, r) for r in range(a.reps) for g in grupos for t in tamanos]
    random.Random(a.semilla).shuffle(plan)

    meta = {"tipo": tipo, "bloque": a.bloque, "sello": sello, "semilla": a.semilla, "reps": a.reps,
            "grupos": grupos, "tamanos": tamanos, "n_msgs": a.n_msgs, "bulk": a.bulk, "frame": a.frame,
            "pausa_s": a.pausa, "openssl": ssl.OPENSSL_VERSION, "python": platform.python_version(),
            "OPENSSL_CONF": os.environ.get("OPENSSL_CONF", ""), "git": git_commit(),
            "modo": "sim" if a.sim else "i2c", "estado_inicio": sistema.estado(None if a.sim else a.bus),
            "archivos": {"potencia": os.path.relpath(ruta_pot, RAIZ), "corridas": os.path.relpath(ruta_runs, RAIZ)}}

    # ---- registrador de potencia en otro proceso/núcleo ----
    cmd = [sys.executable, os.path.join(AQUI, "potencia.py"), "--salida", ruta_pot, "--nucleo", "3"]
    if a.simular_potencia: cmd.append("--simular")
    logger = subprocess.Popen(cmd)
    time.sleep(2)
    if logger.poll() is not None or not os.path.exists(ruta_pot):
        sys.exit("ERROR: el registrador del INA219 no arrancó. Pruebe:  python3 potencia.py --salida /tmp/x.csv --duracion 5")

    enlace = st.crear_enlace(a)
    ctx = st.crear_contexto()
    try:
        print(f"Reposo inicial {a.reposo:.0f} s ..."); meta["reposo_ini"] = [time.monotonic_ns()]
        time.sleep(a.reposo); meta["reposo_ini"].append(time.monotonic_ns())
        with open(ruta_runs, "w") as fr:
            for k, (g, tam, rep) in enumerate(plan, 1):
                est = sistema.estado(None if a.sim else a.bus)
                while est["temp_c"] is not None and est["temp_c"] > a.temp_max:
                    print(f"  temperatura {est['temp_c']} °C > {a.temp_max}: esperando..."); time.sleep(10)
                    est = sistema.estado(None if a.sim else a.bus)
                r = st.ejecutar_corrida(enlace, ctx, st.GRUPOS[g], tam, a.n_msgs, a.bulk, run_id=k)
                r.update({"orden": k, "rep": rep, "bloque": a.bloque, "tipo": tipo, "frame": a.frame,
                          **{f"pre_{x}": v for x, v in est.items()}, "post_throttled": sistema.throttled()})
                fr.write(json.dumps(r, default=str) + "\n"); fr.flush()
                print(f"[{k}/{len(plan)}] {g:8s} msg={tam:4d}  hs_esp={r.get('esp_t_hs_us')} us  "
                      f"err='{r['error']}' esp_estado={r.get('esp_estado')}")
                time.sleep(a.pausa)
        print(f"Reposo final {a.reposo:.0f} s ..."); meta["reposo_fin"] = [time.monotonic_ns()]
        time.sleep(a.reposo); meta["reposo_fin"].append(time.monotonic_ns())
    finally:
        logger.send_signal(signal.SIGINT); logger.wait(timeout=10)
        meta["estado_fin"] = sistema.estado(None if a.sim else a.bus)
        json.dump(meta, open(ruta_meta, "w"), indent=2)
        print("Archivos:\n ", ruta_meta, "\n ", ruta_runs, "\n ", ruta_pot)


if __name__ == "__main__":
    main()
