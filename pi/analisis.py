"""
analisis.py - Semana 11: energía por corrida, estadística descriptiva/inferencial y figuras.

  python3 analisis.py ../data/raw/campana_estandar_*_meta.json ../data/raw/campana_rapido_*_meta.json

Salidas:
  data/processed/corridas_con_energia.csv   (una fila por corrida, con energía)
  data/processed/resumen.csv                (n, media, desv, IC95 % por configuración)
  data/processed/comparaciones.csv          (híbrido vs clásico: diferencia, %, p-valores, IC bootstrap)
  docs/figuras/*.png                        (figuras para la tesis)
"""
import glob, json, math, os, sys
import numpy as np
import pandas as pd
from scipy import stats

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(RAIZ, "data", "processed")
FIG = os.path.join(RAIZ, "docs", "figuras")

# Métricas del handshake (no dependen del tamaño del mensaje)
M_HS = ["esp_t_hs_us", "srv_t_hs_us", "etapa1_clienthello_y_proceso_srv_us", "etapa2_envio_vuelo_srv_us",
        "etapa3_proceso_cliente_y_finished_us", "srv_cpu_us", "bytes_clienthello", "bytes_vuelo_srv",
        "energia_hs_mJ", "esp_heap_usado_hs", "rend_util_kbps"]
# Métricas que dependen del tamaño del mensaje
M_MSG = ["esp_rtt_media_us", "enl_bytes_bus", "energia_corrida_mJ", "enl_retransmisiones", "enl_errores_crc"]


# ---------------------------------------------------------------- carga y energía
def cargar_bloque(ruta_meta):
    meta = json.load(open(ruta_meta))
    runs = pd.read_json(os.path.join(RAIZ, meta["archivos"]["corridas"]), lines=True)
    pot = pd.read_csv(os.path.join(RAIZ, meta["archivos"]["potencia"]))
    return meta, runs, pot


def potencia_media(pot, t0, t1):
    s = pot[(pot.t_ns >= t0) & (pot.t_ns <= t1)]
    return float(s.p_mW.mean()), float(s.p_mW.std()), len(s)


def energia_mJ(pot, t0, t1, p_rep):
    """Integra (P - P_reposo) entre t0 y t1 [ns] por trapecios. mW·s = mJ."""
    if pd.isna(t0) or pd.isna(t1) or t1 <= t0:
        return np.nan
    t = pot.t_ns.to_numpy(np.int64); p = pot.p_mW.to_numpy(float)
    dentro = (t > t0) & (t < t1)
    tt = np.concatenate([[t0], t[dentro], [t1]]).astype(float)
    pp = np.interp(tt, t.astype(float), p)
    return float(np.trapezoid(pp - p_rep, tt / 1e9))


def procesar(rutas_meta):
    filas, reposos = [], []
    for ruta in rutas_meta:
        meta, runs, pot = cargar_bloque(ruta)
        p_rep, p_sd, n = potencia_media(pot, *meta["reposo_ini"])
        p_rep_fin, _, _ = potencia_media(pot, *meta["reposo_fin"])
        reposos.append({"bloque": meta["bloque"], "p_reposo_ini_mW": p_rep, "p_reposo_sd_mW": p_sd,
                        "n_muestras": n, "p_reposo_fin_mW": p_rep_fin, "deriva_mW": p_rep_fin - p_rep,
                        "muestras_por_s": len(pot) / ((pot.t_ns.iloc[-1] - pot.t_ns.iloc[0]) / 1e9)})
        runs["p_reposo_mW"] = p_rep
        runs["energia_hs_mJ"] = [energia_mJ(pot, a, b, p_rep) for a, b in zip(runs.get("t_hs_ini_ns"), runs.get("t_hs_fin_ns"))]
        runs["energia_corrida_mJ"] = [energia_mJ(pot, a, b, p_rep) for a, b in zip(runs.t_corrida_ini_ns, runs.t_corrida_fin_ns)]
        runs["muestras_en_hs"] = [int(((pot.t_ns >= a) & (pot.t_ns <= b)).sum()) if not pd.isna(a) else 0
                                  for a, b in zip(runs.get("t_hs_ini_ns"), runs.get("t_hs_fin_ns"))]
        filas.append(runs)
    df = pd.concat(filas, ignore_index=True)
    df["valida"] = (df.error.fillna("") == "") & (df.esp_estado.astype(str) == "0") & \
                   (df.post_throttled.fillna("0x0").isin(["0x0", None]))
    return df, pd.DataFrame(reposos)


# ---------------------------------------------------------------- estadística
def describir(x):
    x = pd.Series(x).dropna().astype(float)
    n = len(x)
    if n == 0:
        return {"n": 0}
    m, s = x.mean(), x.std(ddof=1) if n > 1 else 0.0
    h = stats.t.ppf(0.975, n - 1) * s / math.sqrt(n) if n > 1 else np.nan
    return {"n": n, "media": m, "desv": s, "ic95_inf": m - h, "ic95_sup": m + h, "mediana": x.median(),
            "cv_pct": 100 * s / m if m else np.nan}


def n_requerido(x, r_pct=5.0, z=1.96):
    """Jain (1991): n = (100·z·s / (r·media))^2 para precisión relativa ±r % con confianza 95 %."""
    x = pd.Series(x).dropna().astype(float)
    if len(x) < 2 or x.mean() == 0:
        return np.nan
    return math.ceil((100 * z * x.std(ddof=1) / (r_pct * abs(x.mean()))) ** 2)


def bootstrap_pct(a, b, reps=2000, semilla=42):
    """IC 95 % bootstrap del sobrecosto porcentual 100·(media(b)-media(a))/media(a)."""
    rng = np.random.default_rng(semilla)
    a, b = np.asarray(a, float), np.asarray(b, float)
    v = [100 * (rng.choice(b, len(b)).mean() - (ma := rng.choice(a, len(a)).mean())) / ma for _ in range(reps)]
    return np.percentile(v, [2.5, 97.5])


def comparar(df, metrica, claves):
    out = []
    for k, g in df.groupby(claves):
        a = g[g.grupo == "clasico"][metrica].dropna().astype(float)
        b = g[g.grupo == "hibrido"][metrica].dropna().astype(float)
        if len(a) < 3 or len(b) < 3:
            continue
        k = k if isinstance(k, tuple) else (k,)
        lo, hi = bootstrap_pct(a, b) if a.mean() else (np.nan, np.nan)
        out.append({**dict(zip(claves, k)), "metrica": metrica, "n_clasico": len(a), "n_hibrido": len(b),
                    "media_clasico": a.mean(), "media_hibrido": b.mean(), "diferencia": b.mean() - a.mean(),
                    "sobrecosto_pct": 100 * (b.mean() - a.mean()) / a.mean() if a.mean() else np.nan,
                    "ic95_pct_inf": lo, "ic95_pct_sup": hi,
                    "p_welch": stats.ttest_ind(b, a, equal_var=False).pvalue if (a.std() > 0 or b.std() > 0) else np.nan,
                    "p_mann_whitney": stats.mannwhitneyu(b, a).pvalue,
                    "p_shapiro_clasico": stats.shapiro(a).pvalue if a.std() > 0 else np.nan,
                    "p_shapiro_hibrido": stats.shapiro(b).pvalue if b.std() > 0 else np.nan})
    return out


def resumir(df):
    filas = []
    for (bl, gr), g in df.groupby(["bloque", "grupo"]):
        for m in M_HS:
            if m in g:
                filas.append({"bloque": bl, "grupo": gr, "msg_bytes": "todos", "metrica": m, **describir(g[m])})
    for (bl, gr, ms), g in df.groupby(["bloque", "grupo", "msg_bytes"]):
        for m in M_MSG:
            if m in g:
                filas.append({"bloque": bl, "grupo": gr, "msg_bytes": ms, "metrica": m, **describir(g[m])})
    return pd.DataFrame(filas)


# ---------------------------------------------------------------- figuras
COL = {"clasico": "#2a78d6", "hibrido": "#eb6834"}          # paleta validada (ver skill dataviz)
ETAPAS_COL = ["#2a78d6", "#eb6834", "#1baf7a"]
TXT, TXT2, GRID, FONDO = "#1f1f1e", "#5c5b55", "#e4e3de", "#fcfcfb"


def _estilo(ax, titulo, ylabel):
    ax.set_facecolor(FONDO)
    ax.set_title(titulo, loc="left", color=TXT, fontsize=11, fontweight="bold")
    ax.set_ylabel(ylabel, color=TXT2)
    ax.grid(axis="y", color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(GRID)
    ax.tick_params(colors=TXT2)


def figuras(df, resumen):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(FIG, exist_ok=True)
    bloques = sorted(df.bloque.unique())
    grupos = [g for g in ("clasico", "hibrido") if g in df.grupo.unique()]

    def barras_ic(metrica, titulo, ylabel, archivo, escala=1.0):
        fig, ax = plt.subplots(figsize=(6.4, 3.8), facecolor=FONDO)
        x = np.arange(len(bloques)); w = 0.36
        for i, gr in enumerate(grupos):
            r = resumen[(resumen.metrica == metrica) & (resumen.grupo == gr)].set_index("bloque").reindex(bloques)
            m = r.media.to_numpy() * escala
            err = np.vstack([m - r.ic95_inf.to_numpy() * escala, r.ic95_sup.to_numpy() * escala - m])
            ax.bar(x + (i - 0.5) * (w + 0.02), m, w, color=COL[gr], label=gr, yerr=err,
                   error_kw={"ecolor": TXT2, "elinewidth": 1, "capsize": 3})
            tope = np.fmax(m, r.ic95_sup.to_numpy() * escala)        # etiqueta sobre la barra de error
            for xi, mi, ti in zip(x + (i - 0.5) * (w + 0.02), m, tope):
                if not np.isnan(mi):
                    ax.annotate(f"{mi:.1f}", (xi, ti), textcoords="offset points", xytext=(0, 4),
                                ha="center", fontsize=8, color=TXT)
        ax.set_xticks(x, [f"bus {b}" for b in bloques])
        ax.set_ylim(top=ax.get_ylim()[1] * 1.08)
        _estilo(ax, titulo, ylabel); ax.legend(frameon=False, labelcolor=TXT)
        fig.tight_layout(); fig.savefig(os.path.join(FIG, archivo), dpi=200); plt.close(fig)

    barras_ic("esp_t_hs_us", "Duración del handshake (medida en el nodo)", "ms (media ± IC 95 %)", "fig1_tiempo_handshake.png", 1e-3)
    barras_ic("energia_hs_mJ", "Energía adicional del sistema por handshake", "mJ (media ± IC 95 %)", "fig2_energia_handshake.png")
    barras_ic("rend_util_kbps", "Rendimiento útil del flujo cifrado", "kbit/s (media ± IC 95 %)", "fig3_rendimiento.png")
    barras_ic("bytes_clienthello", "Tamaño del ClientHello", "bytes", "fig4_bytes_clienthello.png")

    # Etapas del handshake (barras apiladas) por bloque y grupo
    et = ["etapa1_clienthello_y_proceso_srv_us", "etapa2_envio_vuelo_srv_us", "etapa3_proceso_cliente_y_finished_us"]
    nombres = ["ClientHello + proceso servidor", "envío vuelo del servidor", "proceso cliente + Finished"]
    fig, ax = plt.subplots(figsize=(6.8, 3.8), facecolor=FONDO)
    etiquetas, base = [], None
    combos = [(b, g) for b in bloques for g in grupos]
    acum = np.zeros(len(combos))
    for j, (m, nom) in enumerate(zip(et, nombres)):
        vals = np.array([resumen[(resumen.metrica == m) & (resumen.bloque == b) & (resumen.grupo == g)].media.mean()
                         for b, g in combos]) / 1e3
        ax.bar(range(len(combos)), vals, 0.6, bottom=acum, color=ETAPAS_COL[j], label=nom,
               edgecolor=FONDO, linewidth=2)
        acum += np.nan_to_num(vals)
    ax.set_xticks(range(len(combos)), [f"{g}\nbus {b}" for b, g in combos])
    _estilo(ax, "Etapas del handshake (medidas en el servidor)", "ms (media)")
    ax.legend(frameon=False, fontsize=8, labelcolor=TXT, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig5_etapas_handshake.png"), dpi=200); plt.close(fig)

    # Latencia de telemetría vs tamaño del mensaje (una figura por bloque, mismas escalas)
    for b in bloques:
        fig, ax = plt.subplots(figsize=(6.0, 3.6), facecolor=FONDO)
        for gr in grupos:
            r = resumen[(resumen.metrica == "esp_rtt_media_us") & (resumen.bloque == b) & (resumen.grupo == gr)]
            r = r.sort_values("msg_bytes")
            ax.errorbar(r.msg_bytes.astype(int), r.media / 1e3, yerr=[(r.media - r.ic95_inf) / 1e3, (r.ic95_sup - r.media) / 1e3],
                        color=COL[gr], linewidth=2, marker="o", markersize=7, capsize=3, label=gr)
        ax.set_xscale("log", base=2)
        ax.set_xlabel("tamaño del mensaje (bytes)", color=TXT2)
        _estilo(ax, f"Latencia ida y vuelta de un mensaje (bus {b})", "ms (media ± IC 95 %)")
        ax.legend(frameon=False, labelcolor=TXT)
        fig.tight_layout(); fig.savefig(os.path.join(FIG, f"fig6_latencia_{b}.png"), dpi=200); plt.close(fig)


# ---------------------------------------------------------------- principal
if __name__ == "__main__":
    rutas = sys.argv[1:] or sorted(glob.glob(os.path.join(RAIZ, "data", "raw", "campana_*_meta.json")))
    if not rutas:
        sys.exit("No hay archivos *_meta.json de campaña")
    os.makedirs(PROC, exist_ok=True)
    df, reposos = procesar(rutas)
    df.to_csv(os.path.join(PROC, "corridas_con_energia.csv"), index=False)
    reposos.to_csv(os.path.join(PROC, "reposo_por_bloque.csv"), index=False)
    print(f"Corridas: {len(df)}  válidas: {int(df.valida.sum())}  excluidas: {int((~df.valida).sum())}")
    if (~df.valida).any():
        print(df[~df.valida][["bloque", "orden", "grupo", "error", "esp_estado", "post_throttled"]].to_string(index=False))
    v = df[df.valida]
    res = resumir(v)
    res.to_csv(os.path.join(PROC, "resumen.csv"), index=False)
    comps = []
    for m in M_HS:
        if m in v: comps += comparar(v, m, ["bloque"])
    for m in M_MSG:
        if m in v: comps += comparar(v, m, ["bloque", "msg_bytes"])
    comp = pd.DataFrame(comps)
    comp.to_csv(os.path.join(PROC, "comparaciones.csv"), index=False)
    print(reposos.to_string(index=False))
    cols = ["bloque", "metrica", "media_clasico", "media_hibrido", "sobrecosto_pct", "ic95_pct_inf", "ic95_pct_sup", "p_welch"]
    print(comp[comp.metrica.isin(["esp_t_hs_us", "energia_hs_mJ", "bytes_clienthello", "rend_util_kbps"])][cols]
          .to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    figuras(v, res)
    print("Listo: data/processed/*.csv y docs/figuras/*.png")
