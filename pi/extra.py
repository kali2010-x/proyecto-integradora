import pandas as pd
pd.set_option("display.width", 200); pd.set_option("display.max_columns", 20)
d = pd.read_csv("../data/processed/corridas_con_energia.csv")
d = d[d.valida]
print("1) Handshake (mediana, us) por grupo y modo de bus")
print(d.groupby(["grupo", "bloque"]).esp_t_hs_us.median().unstack())
print("\n2) Etapas del handshake (media, us): bus vs cómputo")
et = ["etapa1_clienthello_y_proceso_srv_us", "etapa2_envio_vuelo_srv_us",
      "etapa3_proceso_cliente_y_finished_us", "srv_cpu_us"]
print(d.groupby(["grupo", "bloque"])[et].mean().round(0))
print("\n3) Correlación de Spearman tiempo-energía, por grupo y bloque")
for (g, b), x in d.groupby(["grupo", "bloque"]):
    print(f"{g:8s} {b:9s} rho = {x.esp_t_hs_us.corr(x.energia_hs_mJ, method='spearman'):.2f}")
