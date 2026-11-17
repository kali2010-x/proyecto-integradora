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
  # una tanda está terminada si hay un meta.json de este bloque y semilla con el reposo final y todas sus corridas
  hecho=$(python3 - "$BLOQUE" "$semilla" "$REPS" <<'PY'
import glob, json, sys
bloque, semilla, reps = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
for m in sorted(glob.glob(f"../data/raw/campana_{bloque}_*_meta.json")):
    try:
        d = json.load(open(m))
        n = sum(1 for _ in open(m.replace("_meta.json", "_corridas.jsonl")))
    except Exception:
        continue
    if d.get("semilla") == semilla and d.get("reps") == reps and len(d.get("reposo_fin", [])) == 2 \
            and n == reps * len(d["grupos"]) * len(d["tamanos"]):
        print(m); break
PY
)
  if [ -n "$hecho" ]; then echo "Tanda $((t + 1))/$TANDAS (semilla $semilla): ya está completa -> $hecho"; continue; fi
  echo "=== Tanda $((t + 1))/$TANDAS  bloque=$BLOQUE  semilla=$semilla  reps=$REPS  $(date '+%F %T') ==="
  python3 campana.py --bloque "$BLOQUE" --reps "$REPS" --semilla "$semilla" "$@" || { echo "La tanda $((t + 1)) terminó con error; se detiene."; exit 1; }
done
echo "Bloque $BLOQUE completo: $TANDAS tandas de $REPS repeticiones por configuración."
