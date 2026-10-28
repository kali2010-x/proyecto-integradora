# Proyecto integrador: TLS 1.3 híbrido poscuántico sobre bus I2C

**Implementación de un modelo criptográfico híbrido poscuántico para dispositivos IoT de bajo costo**
David Yela · Kevin Pérez — Materia Integradora de Telecomunicaciones, ESPOL

Nodo sensor (ESP32, cliente TLS, esclavo I2C) ↔ unidad de borde (Raspberry Pi 4, servidor TLS, maestro I2C).
Se compara el intercambio de claves híbrido **X25519MLKEM768** con el clásico **X25519** sobre el bus I2C,
midiendo tiempo, tráfico, memoria y energía (INA219), y se prueba la protección frente a un atacante en el bus.

## Estructura del repositorio

| Carpeta | Contenido |
|---|---|
| `pi/` | Código de la Raspberry: capa de enlace, servidor TLS, pruebas de eco y ataque, potencia, campaña y análisis |
| `esp32/firmware/` | Firmware ESP-IDF v5.5 del nodo: I2C esclavo + cliente TLS con wolfSSL 5.9.4 |
| `sim/` | Esclavo simulado (mismo código C del ESP32) para probar sin hardware |
| `herramientas/` | Verificación del entorno, certificado → header C, búsqueda del texto en capturas del analizador |
| `certs/` | Certificado público del servidor (la clave privada **no** se sube) |
| `data/raw/` | **Datos oficiales de la campaña** (semana 10) |
| `data/pruebas/` | Datos de pruebas y pilotos, por semana (semanas 2 a 9) |
| `data/processed/` | Resultados del análisis (`ensayo_piloto_semana09/` = ensayo general con los pilotos) |
| `docs/` | Bitácora, decisiones, diccionario de datos, evidencias por semana, figuras, guías y propuesta |
| `legacy/` | Scripts y datos de la propuesta anterior (no se usan) |
| `src/` | En la Raspberry contiene el entorno virtual `venv/` (no se sube) |

Índices detallados: [`docs/README.md`](docs/README.md) · [`docs/evidencias/README.md`](docs/evidencias/README.md) · [`data/README.md`](data/README.md)

## Cronología del trabajo práctico

| Semana | Qué se hizo | Evidencias | Datos |
|---|---|---|---|
| 1–2 | Entorno (OpenSSL 3.5.7, wolfSSL 5.9.4 en el ESP32), benchmark y simulador | `docs/evidencias/semana01-02_entorno_y_simulacion/` | `data/pruebas/semana02_simulacion/` |
| 3 | Cableado del bus I2C dedicado (bus 3) y prueba de eco | `docs/evidencias/semana03_eco_i2c/` | — |
| 4 | Modo rápido (400 kbit/s), tamaño de trama 128 y calibración del INA219 | `docs/evidencias/semana04_modo_rapido_y_calibracion/` | — |
| 5 | Capa de enlace (tramas, CRC, retransmisión) | `docs/evidencias/semana05_capa_enlace/` | `data/pruebas/semana05_capa_enlace/` |
| 6 | TLS 1.3 clásico sobre I2C; hallazgo del reloj del ESP32 | `docs/evidencias/semana06_tls_clasico/` | `data/pruebas/semana06_tls_clasico/` |
| 7 | TLS 1.3 híbrido; hallazgo `WOLFSSL_PQC_HYBRIDS` (etiqueta `v0.7-hibrido`) | `docs/evidencias/semana07_tls_hibrido/` | `data/pruebas/semana07_tls_hibrido/` |
| 8 | Confidencialidad e integridad: pruebas de ataque 7/7 aprobadas (captura con analizador pendiente) | `docs/evidencias/semana08_confidencialidad/` | `data/pruebas/semana08_ataques/` |
| 9 | Firmware congelado con memoria pico (`v0.9-campana`), pilotos y tamaño de muestra (N = 60) | `docs/evidencias/semana09_piloto_y_muestra/` | `data/pruebas/semana09_piloto/` |
| 10 | Campaña: bloque rápido (400 kbit/s) 360/360 ✔ · bloque estándar (100 kbit/s) pendiente | `docs/evidencias/semana10_campana/` | `data/raw/` |
| 11 | Análisis estadístico | — | — |
| 12 | Cierre técnico | — | — |

## Inicio rápido (Raspberry)

En la Raspberry el repositorio está clonado en `~/proyecto-kyber-rpi`.

```bash
cd ~/proyecto-kyber-rpi/pi && source ../src/venv/bin/activate   # activa el venv y OPENSSL_CONF
python3 servidor_tls.py --grupo hibrido --frame 128               # una corrida con el ESP32 real
python3 resumen_rapido.py                                         # resumen del último archivo de corridas en data/raw/
```

Las guías de cada semana están en [`docs/guias/`](docs/guias/).
