# Proyecto integrador: TLS 1.3 híbrido post-cuántico sobre bus I2C

Nodo sensor (ESP32, cliente TLS, esclavo I2C) ↔ unidad de borde (Raspberry Pi 4, servidor TLS, maestro I2C).
Intercambio de claves híbrido **X25519MLKEM768** frente a **X25519**. Energía del sistema con INA219.

| Carpeta | Contenido |
|---|---|
| `pi/` | Raspberry: capa de enlace (`enlace.py`), servidor TLS (`servidor_tls.py`), pruebas de eco y ataque, potencia, campaña, análisis |
| `esp32/firmware/` | Proyecto ESP-IDF v5.5: I2C esclavo + cliente TLS con wolfSSL ≥ 5.9.4 |
| `sim/` | Esclavo simulado (mismo código C del ESP32) para probar sin hardware |
| `herramientas/` | Verificación del entorno, certificado → header C |
| `certs/` | Certificado del servidor (la clave privada NO se sube) |
| `data/raw`, `data/processed` | Datos crudos y procesados |
| `docs/` | Evidencias, decisiones, diccionario de datos, figuras |
| `legacy/` | Scripts de la propuesta anterior (no se usan) |

Inicio rápido (Raspberry):
```bash
source ~/proyecto-kyber-rpi/src/venv/bin/activate      # o el venv que use el proyecto
export OPENSSL_CONF=~/proyecto-kyber-rpi/pi/conf/openssl_grupos.cnf
cd ~/proyecto-kyber-rpi/pi
python3 servidor_tls.py --grupo hibrido                  # una corrida con el ESP32 real
```
Las guías semanales en PDF describen cada paso.
