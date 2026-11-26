#!/usr/bin/env bash
# campana_tandas.sh - Ejecuta un BLOQUE de la campaña definitiva en tandas.
#
# Cada tanda es una llamada a pi/campana.py con REPS repeticiones por configuración, su propia
# semilla (orden aleatorio distinto y reproducible) y sus reposos inicial y final. Las tandas
# terminadas se saltan, así que si algo se interrumpe basta con volver a lanzar el mismo comando.
#
#   herramientas/campana_tandas.sh estandar     # bus a 100 kbit/s: 10 tandas x 100 = 1 000 por configuración
#   herramientas/campana_tandas.sh rapido       # bus a 400 kbit/s
#   TANDAS=2 REPS=5 herramientas/campana_tandas.sh sim --sim --simular-potencia --reposo 3 --pausa 0.1   # ensayo
set -u
BLOQUE="${1:?uso: campana_tandas.sh <estandar|rapido|sim> [opciones de campana.py]}"; shift
TANDAS="${TANDAS:-10}"; REPS="${REPS:-100}"; SEMILLA0="${SEMILLA0:-42}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ/pi" || exit 1
for ((t = 0; t < TANDAS; t++)); do
  semilla=$((SEMILLA0 + t))
  # Una tanda está terminada si tiene meta.json con el reposo final, todas sus corridas y un registro de potencia
  # que llega hasta el final del reposo. Las tandas de la misma semilla que no cumplen esto (interrumpidas, o con el
  # registrador del INA219 detenido) se mueven a data/descartados/ para que no se mezclen en el análisis.
  hecho=$(python3 - "$BLOQUE" "$semilla" "$REPS" <<'PY'
import glob, gzip, json, os, shutil, sys
bloque, semilla, reps = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])

def ultimo_t(base):
    for ruta, abrir in ((base + ".csv", open), (base + ".csv.gz", gzip.open)):
        if os.path.exists(ruta):
            ult = None
            with abrir(ruta, "rt") as f:
                if abrir is open:                       # leer solo el final del archivo
                    f.seek(0, 2); f.seek(max(0, f.tell() - 4096)); f.readline()
                for l in f:
                    if l.strip():
                        ult = l
            try:
                return int(ult.split(",")[0])
            except Exception:
                return None
    return None

completa, incompletas = None, []
for m in sorted(glob.glob(f"../data/raw/campana_{bloque}_*_meta.json")):
    try:
        d = json.load(open(m))
    except Exception:
        continue
    if d.get("semilla") != semilla:
        continue
    base = m[:-len("_meta.json")]
    try:
        n = sum(1 for _ in open(base + "_corridas.jsonl"))
    except OSError:
        n = 0
    fin = d.get("reposo_fin", [])
    t_pot = ultimo_t(base + "_potencia")
    ok = (d.get("reps") == reps and len(fin) == 2 and n == reps * len(d["grupos"]) * len(d["tamanos"])
          and t_pot is not None and t_pot >= fin[1] - 2_000_000_000)
    if ok and completa is None:
        completa = m
    else:
        incompletas.append(base)
for base in incompletas:
    os.makedirs("../data/descartados", exist_ok=True)
    for f in glob.glob(base + "_*"):
        shutil.move(f, "../data/descartados/")
    print(f"apartada (incompleta o sin potencia completa): {os.path.basename(base)} -> data/descartados/", file=sys.stderr)
if completa:
    print(completa)
PY
)
  if [ -n "$hecho" ]; then echo "Tanda $((t + 1))/$TANDAS (semilla $semilla): ya está completa -> $hecho"; continue; fi
  echo "=== Tanda $((t + 1))/$TANDAS  bloque=$BLOQUE  semilla=$semilla  reps=$REPS  $(date '+%F %T') ==="
  python3 campana.py --bloque "$BLOQUE" --reps "$REPS" --semilla "$semilla" "$@" || { echo "La tanda $((t + 1)) terminó con error; se detiene."; exit 1; }
done
echo "Bloque $BLOQUE completo: $TANDAS tandas de $REPS repeticiones por configuración."
