# Conjunto de datos: TLS 1.3 híbrido poscuántico sobre I2C

**Título:** Mediciones de tiempo, tráfico, memoria y energía del establecimiento de sesiones TLS 1.3 con intercambio de claves clásico (X25519) e híbrido (X25519MLKEM768) sobre un bus I2C entre un ESP32 y una Raspberry Pi 4.
**Autores:** David Yela, Kevin Pérez — Escuela Superior Politécnica del Litoral (ESPOL), Materia Integradora de Telecomunicaciones.
**Tutora:** María Antonieta Álvarez Villanueva.
**Fecha de la campaña:** 27/10/2026 (bloque rápido) y 29/10/2026 (bloque estándar).
**Licencia de los datos:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).

## Montaje
- Nodo sensor: ESP32 (cliente TLS 1.3, esclavo I2C 0x28), alimentado por USB desde la Raspberry Pi.
- Unidad de borde: Raspberry Pi 4 (servidor TLS 1.3, maestro del bus 3: GPIO4/GPIO5, pull-ups de 4,7 kΩ a 3,3 V).
- Línea READY: GPIO4 del ESP32 → GPIO17 de la Raspberry Pi.
- Enlace: capa propia sobre I2C con tramas de 128 bytes (cabecera 6, carga útil ≤ 120, CRC-16/CCITT 2), ACK y retransmisión de parada y espera.
- Energía: INA219 (bus 1, 0x40, ADC de 12 bits) en serie con la alimentación de 5 V de todo el sistema; la energía es del sistema completo.

## Versiones
| Componente | Versión |
|---|---|
| OpenSSL (Raspberry Pi) | 3.5.7 (9 Jun 2026), grupos configurados con `pi/conf/openssl_grupos.cnf` |
| Python | 3.13.5 |
| wolfSSL (ESP32) | 5.9.4 |
| ESP-IDF | 5.5.5 |
| Firmware de la campaña | commit `3e0e0bf` |
| Código de medición | commit registrado en el campo `git` de cada `*_meta.json` |

## Diseño experimental
- Dos bloques: estándar (100 kbit/s) y rápido (400 kbit/s); orden de bloques y de corridas aleatorio (semilla 42).
- En cada bloque: 2 grupos (clásico, híbrido) × 3 tamaños de mensaje (32, 128 y 512 bytes) × 60 repeticiones = 360 corridas.
- Cada corrida: handshake, 10 mensajes de telemetría con eco cifrado y un bloque de 4 KiB para el rendimiento; 60 s de reposo al inicio y al final de cada bloque.

## Archivos
| Archivo | Contenido |
|---|---|
| `raw/campana_<bloque>_<fecha>_meta.json` | Configuración del bloque, versiones, ventanas de reposo y estado de la Raspberry Pi |
| `raw/campana_<bloque>_<fecha>_corridas.jsonl` | Una línea por corrida con las métricas del ESP32, del servidor y del enlace |
| `raw/campana_<bloque>_<fecha>_potencia.csv.gz` | Potencia continua: `t_ns`, `v_V`, `i_mA`, `p_mW` |
| `processed/corridas_con_energia.csv` | Cada corrida con su energía del handshake y la marca `valida` |
| `processed/resumen.csv` | n, media, desviación, IC 95 %, mediana y CV por bloque, grupo y tamaño |
| `processed/comparaciones.csv` | Híbrido vs. clásico: sobrecosto %, IC 95 % bootstrap, p de Welch, Mann-Whitney y Shapiro |
| `processed/reposo_por_bloque.csv` | Potencia de reposo, deriva y muestras por segundo de cada bloque |

El significado y las unidades de cada campo están en `docs/diccionario_datos.md`. Las corridas descartadas (arranques abortados, repeticiones y el bloque con un registrador duplicado) están en `pruebas/semana10_campana/`, con su justificación en `docs/decisiones.md`.

## Cómo reproducir el análisis
```bash
cd pi && pip install -r ../requirements.txt
python3 analisis.py ../data/raw/campana_estandar_*_meta.json ../data/raw/campana_rapido_*_meta.json
```
