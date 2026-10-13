"""
servidor_tls.py - Servidor TLS 1.3 (OpenSSL 3.5 vía módulo ssl de Python) sobre el enlace I2C.

Ejecuta UNA corrida del experimento:
  1) reinicia el enlace, 2) envía la orden START al ESP32,
  3) handshake TLS (mide etapas), 4) telemetría con eco (latencia),
  5) bloque grande (rendimiento), 6) cierre, 7) recoge el reporte del ESP32.

Uso de prueba (simulador):  python3 servidor_tls.py --sim --grupo hibrido
Uso real (I2C):             python3 servidor_tls.py --grupo hibrido
Requiere: export OPENSSL_CONF=.../pi/conf/openssl_grupos.cnf
"""
import argparse, os, ssl, struct, time, json
from enlace import EnlaceMaestro, BusI2C, BusSimulado

GRUPOS = {"clasico": 0, "hibrido": 1, "sin_tls": 2}
NOMBRE_GRUPO = {v: k for k, v in GRUPOS.items()}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def crear_contexto(cert=os.path.join(RAIZ, "certs/servidor.pem"), key=os.path.join(RAIZ, "certs/servidor.key")):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.load_cert_chain(cert, key)
    ctx.num_tickets = 0          # sin NewSessionTicket: no agrega tráfico al bus
    return ctx


def orden_start(grupo, msg, n_msgs, bulk, run_id):
    return struct.pack(">cBHHIH", b"S", grupo, msg, n_msgs, bulk, run_id)


def parsear_reporte(r, q):
    est, run, t_hs, rtt_m, rtt_x = struct.unpack(">hHIII", r[1:17])
    run2, bulk_us, heap_usado, stack_libre, heap_libre = struct.unpack(">HIIII", q[1:19])
    return {"esp_estado": est, "esp_t_hs_us": t_hs, "esp_rtt_media_us": rtt_m, "esp_rtt_max_us": rtt_x,
            "esp_bulk_us": bulk_us, "esp_heap_usado_hs": heap_usado, "esp_stack_libre": stack_libre,
            "esp_heap_libre": heap_libre}


class SesionTLS:
    """Adapta SSLObject (MemoryBIO) al enlace."""

    def __init__(self, enlace, ctx):
        self.e = enlace
        self.inc, self.out = ssl.MemoryBIO(), ssl.MemoryBIO()
        self.obj = ctx.wrap_bio(self.inc, self.out, server_side=True)

    def _drenar(self):
        o = self.out.read()
        if o:
            self.e.enviar(o)
        return len(o)

    def _alimentar(self):
        if self.e.disponible():
            self.inc.write(self.e.leer())
            return True
        return False

    def handshake(self, timeout_s=30):
        e = self.e
        m = {"srv_cpu_ns": 0, "bytes_vuelo_srv": 0, "bytes_clienthello": 0}
        t_vuelo_listo = t_vuelo_enviado = None
        fin = time.monotonic() + timeout_s
        hecho = False
        while True:
            nuevo = self._alimentar()
            if nuevo or not hecho:
                if nuevo and t_vuelo_listo is None:
                    m["bytes_clienthello"] = e.stats.payload_rx
                t0 = time.monotonic_ns()
                try:
                    self.obj.do_handshake()
                    hecho = True
                except ssl.SSLWantReadError:
                    pass
                dt = time.monotonic_ns() - t0
                n = self._drenar()
                if n:
                    m["srv_cpu_ns"] += dt
                    if t_vuelo_listo is None:
                        t_vuelo_listo = time.monotonic_ns()
                        m["bytes_vuelo_srv"] = n
            if t_vuelo_listo and t_vuelo_enviado is None and e.tx_vacio():
                t_vuelo_enviado = time.monotonic_ns()
            if hecho:
                break
            if time.monotonic() > fin:
                raise TimeoutError("handshake: tiempo agotado")
            if not e.intercambio() and e.tx_vacio():
                time.sleep(0.0002)
        t_fin = time.monotonic_ns()
        t0 = e.t_primer_rx
        m.update({
            "t_hs_ini_ns": t0, "t_hs_fin_ns": t_fin,
            "srv_t_hs_us": (t_fin - t0) / 1e3,
            "etapa1_clienthello_y_proceso_srv_us": (t_vuelo_listo - t0) / 1e3,
            "etapa2_envio_vuelo_srv_us": ((t_vuelo_enviado or t_fin) - t_vuelo_listo) / 1e3,
            "etapa3_proceso_cliente_y_finished_us": (t_fin - (t_vuelo_enviado or t_fin)) / 1e3,
            "srv_cpu_us": m.pop("srv_cpu_ns") / 1e3,
            "tls_version": self.obj.version(), "tls_cifrado": self.obj.cipher()[0],
            # El ServerHello híbrido lleva la clave X25519 (32 B) + texto cifrado ML-KEM-768 (1088 B)
            "grupo_detectado": "hibrido" if m["bytes_vuelo_srv"] > 1100 else "clasico",
        })
        return m

    def leer_exacto(self, n, timeout_s=30):
        buf = bytearray()
        fin = time.monotonic() + timeout_s
        while len(buf) < n:
            self._alimentar()
            try:
                d = self.obj.read(n - len(buf))
                if not d:            # SSLObject devuelve b'' cuando llega close_notify
                    raise ConnectionError("el cliente cerró la sesión TLS")
                buf += d
                continue
            except ssl.SSLWantReadError:
                pass
            if time.monotonic() > fin:
                raise TimeoutError("lectura TLS: tiempo agotado")
            if not self.e.intercambio() and self.e.tx_vacio():
                time.sleep(0.0002)
        return bytes(buf)

    def escribir(self, data):
        self.obj.write(data)
        self._drenar()

    def esperar_cierre(self, timeout_s=10):
        fin = time.monotonic() + timeout_s
        while time.monotonic() < fin:
            self._alimentar()
            try:
                if self.obj.read(1024) == b"":   # close_notify recibido
                    return True
            except ssl.SSLZeroReturnError:
                return True
            except ssl.SSLWantReadError:
                pass
            if not self.e.intercambio():
                time.sleep(0.0005)
        return False


def esperar_reporte(enlace, timeout_s=20):
    r = q = None
    fin = time.monotonic() + timeout_s
    while (r is None or q is None) and time.monotonic() < fin:
        c = enlace.ctrl_pop()
        while c:
            if c[:1] == b"R": r = c
            elif c[:1] == b"Q": q = c
            c = enlace.ctrl_pop()
        if r is None or q is None:
            if not enlace.intercambio():
                time.sleep(0.001)
    return parsear_reporte(r, q) if r and q else {"esp_estado": "sin_reporte"}


def ejecutar_corrida(enlace, ctx, grupo, msg=64, n_msgs=10, bulk=4096, run_id=1):
    res = {"run_id": run_id, "grupo": NOMBRE_GRUPO[grupo], "msg_bytes": msg, "n_msgs": n_msgs,
           "bulk_bytes": bulk, "error": ""}
    if not enlace.reset():
        res["error"] = "reset_fallido"
        return res
    enlace.stats.reiniciar()
    res["t_corrida_ini_ns"] = time.monotonic_ns()
    enlace.enviar_ctrl(orden_start(grupo, msg, n_msgs, bulk, run_id))
    try:
        if grupo == GRUPOS["sin_tls"]:
            for _ in range(n_msgs):
                enlace.bombear(lambda: enlace.disponible() >= msg)
                enlace.enviar(enlace.leer(msg))
            enlace.bombear(lambda: enlace.tx_vacio())
        else:
            s = SesionTLS(enlace, ctx)
            res.update(s.handshake())
            for _ in range(n_msgs):
                s.escribir(s.leer_exacto(msg))
            if bulk:
                t_b0 = time.monotonic_ns()
                s.leer_exacto(1)
                t_b1 = time.monotonic_ns()
                s.leer_exacto(bulk - 1)
                t_b2 = time.monotonic_ns()
                s.escribir(b"OK")
                res["srv_bulk_us"] = (t_b2 - t_b1) / 1e3
                res["rend_util_kbps"] = (bulk - 1) * 8 / ((t_b2 - t_b1) / 1e9) / 1e3
            res["cierre_ok"] = s.esperar_cierre()
    except ssl.SSLError as ex:
        res["error"] = f"SSLError:{ex.reason or ex}"
    except (TimeoutError, ConnectionError) as ex:
        res["error"] = f"{type(ex).__name__}:{ex}"
    res.update(esperar_reporte(enlace))
    res["t_corrida_fin_ns"] = time.monotonic_ns()
    res.update(enlace.stats.como_dict())
    return res


def crear_enlace(args):
    if args.sim:
        bus = BusSimulado(puerto=args.puerto, frame_size=args.frame)
    else:
        bus = BusI2C(bus_num=args.bus, direccion=args.dir, pin_ready=args.ready)
    return EnlaceMaestro(bus, frame_size=args.frame)


def argumentos_comunes(p):
    p.add_argument("--sim", action="store_true", help="usar el esclavo simulado (sin hardware)")
    p.add_argument("--puerto", type=int, default=5555)
    p.add_argument("--bus", type=int, default=3, help="número de bus I2C del enlace")
    p.add_argument("--dir", type=lambda x: int(x, 0), default=0x28, help="dirección I2C del ESP32")
    p.add_argument("--ready", type=int, default=17, help="GPIO (BCM) de la línea READY")
    p.add_argument("--frame", type=int, default=128, help="tamaño de trama (igual que en el ESP32)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    argumentos_comunes(ap)
    ap.add_argument("--grupo", choices=GRUPOS, default="hibrido")
    ap.add_argument("--msg", type=int, default=64)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--bulk", type=int, default=4096)
    a = ap.parse_args()
    if "OPENSSL_CONF" not in os.environ:
        print("AVISO: OPENSSL_CONF no está definido; se usarán los grupos por defecto de OpenSSL")
    print("OpenSSL:", ssl.OPENSSL_VERSION)
    e = crear_enlace(a)
    r = ejecutar_corrida(e, crear_contexto(), GRUPOS[a.grupo], a.msg, a.n, a.bulk)
    print(json.dumps(r, indent=2, default=str))
