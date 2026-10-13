"""
enlace.py - Capa de enlace confiable sobre I2C (lado MAESTRO: Raspberry Pi).

Trama de tamaño fijo FRAME_SIZE (debe coincidir con el ESP32):
  [0] MAGIC 0xA5
  [1] TIPO  (0x00 POLL, 0x01 DATOS, 0x02 CONTROL, 0x03 RESET)
  [2] SEQ   número de secuencia de la trama que se envía (1..255, 0 = ninguna)
  [3] ACK   última SEQ recibida correctamente del otro extremo
  [4..5] LEN longitud de la carga útil (big endian)
  [6..6+MAX_PAYLOAD-1] carga útil (rellenada con ceros)
  [-2..-1] CRC-16/CCITT-FALSE de los bytes 0..FRAME_SIZE-3

Protocolo: el maestro hace "intercambios": ESCRIBE una trama y luego LEE una
trama de respuesta (siempre exactamente una lectura por escritura exitosa).
ARQ de parada y espera en ambos sentidos (retransmite hasta recibir ACK).
"""
import collections
import struct
import time

MAGIC = 0xA5
T_POLL, T_DATOS, T_CTRL, T_RESET = 0x00, 0x01, 0x02, 0x03
HDR = 6
CRC_LEN = 2


def crc16_ccitt(data: bytes, crc: int = 0xFFFF) -> int:
    """CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF). '123456789' -> 0x29B1."""
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


class Trama:
    def __init__(self, frame_size: int):
        self.size = frame_size
        self.max_payload = frame_size - HDR - CRC_LEN

    def construir(self, tipo, seq, ack, payload=b""):
        assert len(payload) <= self.max_payload
        cuerpo = struct.pack(">BBBBH", MAGIC, tipo, seq, ack, len(payload)) + payload
        cuerpo += bytes(self.size - CRC_LEN - len(cuerpo))
        return cuerpo + struct.pack(">H", crc16_ccitt(cuerpo))

    def analizar(self, raw: bytes):
        """Devuelve (tipo, seq, ack, payload) o None si la trama es inválida."""
        if len(raw) != self.size or raw[0] != MAGIC:
            return None
        if struct.unpack(">H", raw[-2:])[0] != crc16_ccitt(raw[:-2]):
            return None
        _, tipo, seq, ack, n = struct.unpack(">BBBBH", raw[:HDR])
        if n > self.max_payload:
            return None
        return tipo, seq, ack, bytes(raw[HDR:HDR + n])


def _sig(seq):  # siguiente número de secuencia, 1..255
    return 1 if seq >= 255 else seq + 1


class EstadisticasEnlace:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.intercambios = 0
        self.bytes_bus = 0          # bytes físicos (escritos + leídos)
        self.payload_tx = 0         # bytes útiles nuevos enviados al esclavo
        self.payload_rx = 0         # bytes útiles nuevos recibidos del esclavo
        self.errores_crc = 0
        self.timeouts_ready = 0
        self.errores_io = 0
        self.retransmisiones = 0

    def como_dict(self, prefijo="enl_"):
        return {prefijo + k: v for k, v in self.__dict__.items()}


class EnlaceMaestro:
    def __init__(self, bus, frame_size=128, timeout_ready_s=0.2, log_tramas=None):
        self.bus = bus
        self.t = Trama(frame_size)
        self.timeout_ready_s = timeout_ready_s
        self.stats = EstadisticasEnlace()
        self.log_tramas = log_tramas      # archivo opcional donde se vuelca cada trama (hex)
        self.manip_tx = None              # gancho de ataque: f(payload)->payload (maestro->esclavo)
        self.manip_rx = None              # gancho de ataque: f(payload)->payload (esclavo->maestro)
        self._estado_inicial()

    def _estado_inicial(self):
        self.cola_tx = collections.deque()   # (tipo, bytes) pendientes de enviar
        self.pendiente = None                # (tipo, seq, payload) enviado sin ACK
        self.seq_tx = 0
        self.ultima_seq_rx = 0
        self.buf_rx = bytearray()
        self.ctrl_rx = collections.deque()
        self.t_primer_rx = None              # instante del primer byte útil recibido

    # ---------------- API para la capa superior ----------------
    def enviar(self, datos: bytes, tipo=T_DATOS):
        mp = self.t.max_payload
        for i in range(0, len(datos), mp):
            self.cola_tx.append((tipo, bytes(datos[i:i + mp])))

    def enviar_ctrl(self, msg: bytes):
        assert len(msg) <= self.t.max_payload
        self.cola_tx.append((T_CTRL, msg))

    def leer(self, n=None) -> bytes:
        n = len(self.buf_rx) if n is None else min(n, len(self.buf_rx))
        out = bytes(self.buf_rx[:n])
        del self.buf_rx[:n]
        return out

    def disponible(self):
        return len(self.buf_rx)

    def tx_vacio(self):
        return not self.cola_tx and self.pendiente is None

    def ctrl_pop(self):
        return self.ctrl_rx.popleft() if self.ctrl_rx else None

    # ---------------- Núcleo del protocolo ----------------
    def _xfer(self, trama: bytes):
        """Escribe una trama y lee exactamente una respuesta. Devuelve bytes o None."""
        try:
            self.bus.escribir(trama)
        except OSError:
            self.stats.errores_io += 1
            return None
        if not self.bus.esperar_ready(self.timeout_ready_s):
            self.stats.timeouts_ready += 1     # igual se lee para mantener 1:1 escritura/lectura
        try:
            resp = self.bus.leer(self.t.size)
        except OSError:
            self.stats.errores_io += 1
            return None
        self.stats.intercambios += 1
        self.stats.bytes_bus += 2 * self.t.size
        if self.log_tramas:
            self.log_tramas.write(f"{time.monotonic_ns()} M>E {trama.hex()}\n"
                                  f"{time.monotonic_ns()} E>M {bytes(resp).hex()}\n")
        return bytes(resp)

    def intercambio(self) -> bool:
        """Un ciclo escritura+lectura. Devuelve True si hubo avance (datos nuevos o ACK)."""
        if self.pendiente is None and self.cola_tx:
            tipo, p = self.cola_tx.popleft()
            self.seq_tx = _sig(self.seq_tx)
            self.pendiente = (tipo, self.seq_tx, p)
            self.stats.payload_tx += len(p)
            nuevo = True
        else:
            nuevo = False
        if self.pendiente:
            tipo, seq, p = self.pendiente
            if not nuevo:
                self.stats.retransmisiones += 1
            if self.manip_tx and tipo == T_DATOS:
                p = self.manip_tx(p)
            trama = self.t.construir(tipo, seq, self.ultima_seq_rx, p)
        else:
            trama = self.t.construir(T_POLL, self.seq_tx, self.ultima_seq_rx)
        raw = self._xfer(trama)
        if raw is None:
            return False
        r = self.t.analizar(raw)
        if r is None:
            self.stats.errores_crc += 1
            return False
        tipo, seq, ack, payload = r
        avance = False
        if self.pendiente and ack == self.pendiente[1]:
            self.pendiente = None
            avance = True
        if tipo in (T_DATOS, T_CTRL) and seq == _sig(self.ultima_seq_rx):
            self.ultima_seq_rx = seq
            if tipo == T_DATOS:
                if self.manip_rx:
                    payload = self.manip_rx(payload)
                if self.t_primer_rx is None and payload:
                    self.t_primer_rx = time.monotonic_ns()
                self.buf_rx += payload
                self.stats.payload_rx += len(payload)
            else:
                self.ctrl_rx.append(payload)
            avance = True
        return avance

    def reset(self, intentos=20) -> bool:
        """Reinicia el estado del enlace en ambos extremos."""
        for _ in range(intentos):
            raw = self._xfer(self.t.construir(T_RESET, 0, 0))
            raw = self._xfer(self.t.construir(T_POLL, 0, 0)) if raw is not None else None
            if raw is not None:
                r = self.t.analizar(raw)
                if r is not None and r[0] in (T_POLL, T_RESET) and r[2] == 0:
                    self._estado_inicial()
                    return True
            time.sleep(0.01)
        return False

    def bombear(self, hasta=lambda: False, timeout_s=10.0, pausa_ocioso_s=0.0005):
        """Hace intercambios hasta que hasta() sea True o se agote el tiempo."""
        fin = time.monotonic() + timeout_s
        while not hasta():
            if time.monotonic() > fin:
                raise TimeoutError("enlace: tiempo agotado")
            if not self.intercambio() and self.tx_vacio():
                time.sleep(pausa_ocioso_s)


# ====================== Transportes ======================
class BusI2C:
    """Transporte real: Raspberry Pi como maestro (smbus2) + línea READY (libgpiod v2)."""

    def __init__(self, bus_num=3, direccion=0x28, pin_ready=17, chip="/dev/gpiochip0"):
        from smbus2 import SMBus, i2c_msg
        import gpiod
        from gpiod.line import Direction, Bias, Value
        self._i2c_msg = i2c_msg
        self._activo = Value.ACTIVE
        self.bus = SMBus(bus_num)
        self.dir = direccion
        self.pin = pin_ready
        self.req = gpiod.request_lines(
            chip, consumer="ready-esp32",
            config={pin_ready: gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_DOWN)})

    def escribir(self, data: bytes):
        self.bus.i2c_rdwr(self._i2c_msg.write(self.dir, data))

    def esperar_ready(self, timeout_s):
        fin = time.monotonic() + timeout_s
        while time.monotonic() < fin:
            if self.req.get_value(self.pin) == self._activo:
                return True
        return False

    def leer(self, n):
        m = self._i2c_msg.read(self.dir, n)
        self.bus.i2c_rdwr(m)
        return bytes(m)

    def cerrar(self):
        self.bus.close()
        self.req.release()


class BusSimulado:
    """Transporte de pruebas: emula el bus contra sim/esclavo_sim (TCP).
    'W'+trama = escritura del maestro; 'R' = lectura (bloquea hasta que el esclavo responde)."""

    def __init__(self, host="127.0.0.1", puerto=5555, frame_size=128):
        import socket
        self.s = socket.create_connection((host, puerto))
        self.s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.n = frame_size

    def escribir(self, data):
        self.s.sendall(b"W" + data)

    def esperar_ready(self, timeout_s):
        return True

    def leer(self, n):
        self.s.sendall(b"R")
        buf = b""
        while len(buf) < n:
            c = self.s.recv(n - len(buf))
            if not c:
                raise OSError("simulador cerrado")
            buf += c
        return buf

    def cerrar(self):
        self.s.close()
