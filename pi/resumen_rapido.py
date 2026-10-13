"""
resumen_rapido.py - Revisión rápida de un archivo de corridas (.jsonl) recién generado.

  python3 resumen_rapido.py                       (el archivo de corridas más reciente)
  python3 resumen_rapido.py ../data/raw/campana_estandar_..._corridas.jsonl
"""
import glob, os, sys
import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ruta = sys.argv[1] if len(sys.argv) > 1 else max(glob.glob(os.path.join(RAIZ, "data", "raw", "*_corridas.jsonl")),
                                                  key=os.path.getmtime)
d = pd.read_json(ruta, lines=True)
d["error"] = d.error.fillna("")
ok = (d.error == "") & (d.esp_estado.astype(str) == "0")
print(f"Archivo: {os.path.relpath(ruta, RAIZ)}")
print(f"Corridas: {len(d)}   correctas: {int(ok.sum())}   con problema: {int((~ok).sum())}")
if (~ok).any():
    print("\nProblemas (tipo: cantidad):")
    print(d[~ok].assign(t=d.error.where(d.error != "", "esp_estado=" + d.esp_estado.astype(str)))
          .t.value_counts().to_string())
cont = [c for c in ["enl_retransmisiones", "enl_errores_crc", "enl_timeouts_ready", "enl_errores_io"] if c in d]
print("\nContadores del enlace (suma):"); print(d[cont].sum().to_string())
dur = (d.t_corrida_fin_ns - d.t_corrida_ini_ns) / 1e9
print(f"\nDuración por corrida: media {dur.mean():.2f} s, máx {dur.max():.2f} s")
if "esp_t_hs_us" in d:
    g = d[ok].groupby("grupo")
    cols = [c for c in ["esp_t_hs_us", "bytes_clienthello", "esp_heap_usado_hs", "esp_stack_libre", "rend_util_kbps"] if c in d]
    print("\nMedias por grupo (solo corridas correctas):"); print(g[cols].mean().round(1).to_string())
if "grupo_detectado" in d:
    mal = d[ok & d.grupo_detectado.notna() & (d.grupo != d.grupo_detectado)]
    print(f"\nConsistencia grupo pedido vs detectado: {'OK' if mal.empty else f'{len(mal)} DIFERENTES (revisar)'}")
