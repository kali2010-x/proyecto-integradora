"""
tamano_muestra.py - Semana 9: calcula cuántas repeticiones hacen falta a partir de la prueba piloto.
Criterio de Jain (1991): n = (100·z·s / (r·media))^2, r = 5 % y 95 % de confianza; mínimo 30
(teorema del límite central, Montgomery & Runger, 2014).

  python3 tamano_muestra.py ../data/raw/piloto_estandar_*_meta.json
"""
import sys, glob, os
import pandas as pd
import analisis as an

rutas = sys.argv[1:] or sorted(glob.glob(os.path.join(an.RAIZ, "data", "raw", "piloto_*_meta.json")))
df, _ = an.procesar(rutas)
v = df[df.valida]
filas = []
for (bl, gr), g in v.groupby(["bloque", "grupo"]):
    for m in ["esp_t_hs_us", "srv_t_hs_us", "energia_hs_mJ", "rend_util_kbps"]:
        d = an.describir(g[m])
        filas.append({"bloque": bl, "grupo": gr, "metrica": m, "n_piloto": d["n"], "media": d.get("media"),
                      "cv_pct": d.get("cv_pct"), "n_requerido": an.n_requerido(g[m])})
t = pd.DataFrame(filas)
print(t.to_string(index=False, float_format=lambda x: f"{x:.3g}"))
import math, argparse
n = max(30, int(t.n_requerido.max()))
print(f"\nRepeticiones recomendadas por configuración: {n}  (máximo entre métricas, mínimo 30)")
# Si n es inalcanzable en el tiempo disponible, se fija un n factible y se REPORTA la precisión lograda:
#   r = 100·z·s / (media·raíz(n))   (despeje de la misma fórmula de Jain)
print("\nPrecisión relativa (± %, 95 %) que se lograría con distintos n:")
for nn in (30, 60, 100):
    t[f"r_pct_n{nn}"] = 100 * 1.96 * (t.cv_pct / 100) / math.sqrt(nn)
print(t[["bloque", "grupo", "metrica", "r_pct_n30", "r_pct_n60", "r_pct_n100"]].to_string(index=False, float_format=lambda x: f"{x:.1f}"))
t.to_csv(os.path.join(an.RAIZ, "data", "processed", "tamano_muestra.csv"), index=False)
