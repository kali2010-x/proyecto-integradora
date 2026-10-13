#!/usr/bin/env bash
# verificar_entorno.sh - Semana 1: deja evidencia del entorno de la Raspberry en docs/evidencias/
# Uso:  bash herramientas/verificar_entorno.sh
set -u
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$RAIZ/docs/evidencias/entorno_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p "$RAIZ/docs/evidencias"
PY="${PYTHON:-python3}"
{
echo "== Fecha"; date
echo "== Sistema"; uname -a; grep PRETTY_NAME /etc/os-release
echo "== Python y OpenSSL de Python"; $PY --version; $PY -c "import ssl; print(ssl.OPENSSL_VERSION)"
echo "== OpenSSL (línea de comandos)"; openssl version
echo "== ML-KEM disponible en OpenSSL"; openssl list -kem-algorithms | grep -i "ml-kem" || echo "NO SE ENCONTRÓ ML-KEM (se necesita OpenSSL >= 3.5)"
echo "== Handshake TLS 1.3 local con cada grupo"
for G in X25519MLKEM768 X25519; do
  openssl s_server -accept 4433 -cert "$RAIZ/certs/servidor.pem" -key "$RAIZ/certs/servidor.key" \
          -tls1_3 -groups "$G" -naccept 1 -quiet >/dev/null 2>&1 &
  sleep 1
  echo "-- grupo pedido: $G"
  echo Q | openssl s_client -connect 127.0.0.1:4433 -tls1_3 -groups "$G" 2>&1 \
       | grep -E "Negotiated TLS1.3 group|Temp Key|Protocol|Cipher is" | sort -u
  wait
done
echo "== Python ssl + OPENSSL_CONF del proyecto (tamaño del ClientHello por grupo)"
for G in X25519MLKEM768 X25519; do
  sed "s/^Groups = .*/Groups = $G/" "$RAIZ/pi/conf/openssl_grupos.cnf" > /tmp/grp_$G.cnf
  OPENSSL_CONF=/tmp/grp_$G.cnf $PY - "$RAIZ" "$G" <<'PYEOF'
import ssl, sys
raiz, g = sys.argv[1], sys.argv[2]
s = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); s.load_cert_chain(f"{raiz}/certs/servidor.pem", f"{raiz}/certs/servidor.key")
c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); c.check_hostname = False; c.verify_mode = ssl.CERT_NONE
si, so, ci, co = (ssl.MemoryBIO() for _ in range(4))
S = s.wrap_bio(si, so, server_side=True); C = c.wrap_bio(ci, co)
hecho, ch = set(), None
for _ in range(10):
    for n, o in (("c", C), ("s", S)):
        if n not in hecho:
            try: o.do_handshake(); hecho.add(n)
            except ssl.SSLWantReadError: pass
    d = co.read(); ch = ch or len(d); si.write(d); ci.write(so.read())
print(f"   {g}: ClientHello = {ch} bytes, {C.version()}  (esperado: híbrido > 1200 B, clásico < 600 B)")
PYEOF
done
echo "== Buses I2C"; ls /dev/i2c-* 2>/dev/null; command -v i2cdetect >/dev/null && i2cdetect -y 1
echo "== Estado"; vcgencmd measure_temp 2>/dev/null; vcgencmd get_throttled 2>/dev/null
echo "== Paquetes Python del venv"; $PY -m pip list 2>/dev/null | grep -i -E "smbus2|gpiod|adafruit|numpy|pandas|scipy|matplotlib|psutil"
} 2>&1 | tee "$OUT"
echo; echo "Evidencia guardada en: $OUT"
