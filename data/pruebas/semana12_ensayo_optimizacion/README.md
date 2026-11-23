# Semana 12 · Verificación del firmware y del enlace optimizados (23/11/2026)

Pruebas hechas en el banco real (bus 3 a 100 kbit/s, ESP32 alimentado por USB desde la Raspberry, analizador
desconectado) antes de la campaña definitiva de N = 1 000. Rama `optimizacion-campana-1000`.

## Pruebas de seguridad (`pi/ataque.py`)

| Archivo | Firmware | Resultado |
|---|---|---|
| `ataques_20261123_011933.json` | sin ajuste de reloj | Falla: ESP32 estado -3 (certificado «aún no vigente»: reloj en 1970). El «pasaron» era un falso positivo, corregido después en `ataque.py`. |
| `ataques_20261123_013829.json` | con reloj, sin `WOLFSSL_PQC_HYBRIDS` | Falla: estado -5 (wolfSSL no ofrece el grupo X25519MLKEM768). `ataque.py` ya dice «REVISAR». |
| `ataques_20261123_014537.json` | intento intermedio | Ver el archivo. |
| `ataques_20261123_015418.json` | **corregido** | **Correcto**: marcador visible sin TLS y oculto con TLS; las tres manipulaciones se rechazan después de un handshake válido (`BAD_RECORD_MAC` / `RECORD_LAYER_FAILURE`; -180 en el ESP32, falla de autenticación AES-GCM). |

Los `tramas_*.log` son los bytes del bus de cada prueba.

## Ensayos cortos (`pi/campana.py --reps 2 --piloto`, 12 corridas)

| Archivo | Optimización del compilador (ESP32) | Handshake clásico | Handshake híbrido | Errores |
|---|---|---|---|---|
| Piloto de octubre (`data/raw/piloto_60/`) | desconocida (copia local) | 1,93 s | 2,43 s | 0/720 |
| `piloto_estandar_20261123_015712_*` | `-Og` (depuración, valor por defecto de ESP-IDF) | 2,52 s | 2,97 s | 0/12 |
| `piloto_estandar_20261123_023531_*` | `-O2` (rendimiento) | 1,75 s | 2,20 s | 0/12 |

La diferencia está solo en la etapa 3 (cálculo dentro del ESP32): la transmisión por el bus (etapas 1 y 2) es igual o un poco
más rápida que en octubre gracias a la optimización del enlace. La memoria pico de wolfSSL no cambia (59,8 y 62,1 KiB).
La optimización elegida para la campaña se registra en `esp32/firmware/sdkconfig.defaults` y en `docs/decisiones.md`.

Los CSV de potencia se guardan comprimidos (`*_potencia.csv.gz`).
