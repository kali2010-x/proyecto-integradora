"""
ataque.py - Pruebas de confidencialidad e integridad (semanas 7-8).

Simula un atacante con acceso físico al bus que modifica o reinyecta tramas
RECALCULANDO el CRC (la capa de enlace no puede detectarlo). TLS debe rechazarlas.

  python3 ataque.py --sim            (o sin --sim con el ESP32 real)

Pruebas:
  claro_sin_tls     : control. La telemetría viaja en claro -> el marcador SE VE en el bus.
  claro_con_tls     : con TLS híbrido -> el marcador NO debe aparecer en el bus.
  alterar_esp_a_pi  : se invierte 1 bit de un registro cifrado ESP32->Pi.
  alterar_pi_a_esp  : se invierte 1 bit de un registro cifrado Pi->ESP32.
  reinyectar        : se reenvía un registro cifrado ya entregado (ataque de repetición).
"""
import argparse, json, os, ssl, time
import servidor_tls as st
from enlace import T_DATOS

MARCADOR = b"TELEMETRIA"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def invertir_bit_una_vez():
    hecho = {"v": False}

    def f(p):
        if p and not hecho["v"]:
            hecho["v"] = True
            b = bytearray(p)
            b[len(b) // 2] ^= 0x01
            return bytes(b)
        return p
    return f


def marcador_en_log(ruta):
    """Busca el texto del marcador dentro de los bytes de todas las tramas registradas."""
    with open(ruta) as f:
        for linea in f:
            if MARCADOR in bytes.fromhex(linea.split()[2]):
                return True
    return False


def prueba_claro(enlace, ctx, grupo, ruta_log):
    with open(ruta_log, "w") as log:
        enlace.log_tramas = log
        r = st.ejecutar_corrida(enlace, ctx, grupo, msg=64, n_msgs=3, bulk=0, run_id=900 + grupo)
        enlace.log_tramas = None
    visible = marcador_en_log(ruta_log)
    return {"error_corrida": r["error"], "marcador_visible_en_bus": visible, "log": ruta_log}


def prueba_manipulacion(enlace, ctx, modo):
    out = {"modo": modo}
    enlace.reset(); enlace.stats.reiniciar()
    enlace.enviar_ctrl(st.orden_start(st.GRUPOS["hibrido"], 64, 3, 0, 950))
    s = st.SesionTLS(enlace, ctx)
    try:
        s.handshake()
        out["handshake"] = "ok"
        if modo == "alterar_esp_a_pi":
            enlace.manip_rx = invertir_bit_una_vez()
            s.escribir(s.leer_exacto(64))
        elif modo == "alterar_pi_a_esp":
            m = s.leer_exacto(64)
            enlace.manip_tx = invertir_bit_una_vez()
            s.escribir(m)
            s.leer_exacto(64)
        elif modo == "reinyectar":
            m = s.leer_exacto(64)
            s.obj.write(m)
            registro = s.out.read()           # registro cifrado legítimo (eco #1)
            enlace.enviar(registro)
            m2 = s.leer_exacto(64)            # en vez del eco #2 se reenvía el registro #1
            enlace.enviar(registro)
            s.leer_exacto(64)
        out["servidor"] = "sin_error"
    except ssl.SSLError as ex:
        out["servidor"] = f"SSLError:{ex.reason or ex}"
    except (TimeoutError, ConnectionError) as ex:
        out["servidor"] = f"{type(ex).__name__}"
    finally:
        enlace.manip_rx = enlace.manip_tx = None
    rep = st.esperar_reporte(enlace)
    out["esp32_estado"] = rep.get("esp_estado")
    out["rechazado"] = out.get("servidor", "").startswith("SSLError") or \
        (isinstance(out["esp32_estado"], int) and out["esp32_estado"] != 0)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    st.argumentos_comunes(ap)
    a = ap.parse_args()
    e = st.crear_enlace(a)
    ctx = st.crear_contexto()
    sello = time.strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(RAIZ, "data", "raw")
    os.makedirs(dest, exist_ok=True)
    res = {
        "claro_sin_tls": prueba_claro(e, ctx, st.GRUPOS["sin_tls"], os.path.join(dest, f"tramas_sin_tls_{sello}.log")),
        "claro_con_tls": prueba_claro(e, ctx, st.GRUPOS["hibrido"], os.path.join(dest, f"tramas_con_tls_{sello}.log")),
    }
    for modo in ("alterar_esp_a_pi", "alterar_pi_a_esp", "reinyectar"):
        res[modo] = prueba_manipulacion(e, ctx, modo)
    ok = (res["claro_sin_tls"]["marcador_visible_en_bus"] and not res["claro_con_tls"]["marcador_visible_en_bus"]
          and all(res[m]["rechazado"] for m in ("alterar_esp_a_pi", "alterar_pi_a_esp", "reinyectar")))
    res["CONCLUSION"] = "TODAS LAS PRUEBAS PASARON" if ok else "REVISAR: alguna prueba no dio lo esperado"
    ruta = os.path.join(dest, f"ataques_{sello}.json")
    with open(ruta, "w") as f:
        json.dump(res, f, indent=2)
    print(json.dumps(res, indent=2))
    print("Guardado en", ruta)
