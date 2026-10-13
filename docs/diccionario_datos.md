# Diccionario de datos

## data/raw/<tipo>_<bloque>_<fecha>_corridas.jsonl  (una línea por corrida)
| Campo | Unidad | Descripción |
|---|---|---|
| run_id, orden, rep | - | identificador, posición en el orden aleatorio, número de repetición |
| bloque | - | modo del bus: `estandar` (100 kbit/s) o `rapido` (400 kbit/s) |
| grupo | - | `clasico` (X25519) o `hibrido` (X25519MLKEM768) |
| msg_bytes, n_msgs, bulk_bytes | bytes / - / bytes | tamaño y número de mensajes de telemetría, tamaño del bloque de rendimiento |
| error | - | vacío si la corrida terminó bien; si no, causa (`SSLError:...`, `Timeout...`) |
| esp_estado | - | 0 = OK en el ESP32; negativo = código de error de wolfSSL |
| t_corrida_ini_ns, t_corrida_fin_ns | ns (reloj monotónico de la Raspberry) | ventana de toda la corrida |
| t_hs_ini_ns, t_hs_fin_ns | ns | ventana del handshake (primer byte del ClientHello -> handshake completo) |
| esp_t_hs_us | µs | duración del handshake medida en el ESP32 (SSL_connect) |
| srv_t_hs_us | µs | duración del handshake medida en el servidor |
| etapa1_clienthello_y_proceso_srv_us | µs | llegada del ClientHello + cómputo del servidor hasta tener su vuelo |
| etapa2_envio_vuelo_srv_us | µs | transmisión por el bus del vuelo del servidor (ServerHello...Finished) |
| etapa3_proceso_cliente_y_finished_us | µs | cómputo del cliente + llegada de su Finished |
| srv_cpu_us | µs | tiempo de CPU del servidor dentro de do_handshake |
| bytes_clienthello, bytes_vuelo_srv | bytes | tamaños medidos de los mensajes del handshake |
| grupo_detectado | - | grupo inferido del tamaño del ServerHello (control de consistencia) |
| tls_version, tls_cifrado | - | versión y suite negociadas |
| esp_rtt_media_us, esp_rtt_max_us | µs | latencia ida y vuelta de un mensaje de telemetría (media / máximo) |
| srv_bulk_us, rend_util_kbps | µs / kbit/s | tiempo y rendimiento útil del bloque cifrado |
| esp_bulk_us | µs | tiempo del bloque medido en el ESP32 |
| esp_heap_usado_hs | bytes | memoria dinámica ocupada por la sesión TLS tras el handshake |
| esp_stack_libre | bytes | mínimo de pila libre de la tarea TLS (desde el arranque) |
| esp_heap_libre | bytes | heap libre al final de la corrida |
| enl_intercambios | - | ciclos escritura+lectura en el bus |
| enl_bytes_bus | bytes | bytes físicos transmitidos por el bus (incluye sondeo y cabeceras) |
| enl_payload_tx, enl_payload_rx | bytes | bytes útiles enviados / recibidos |
| enl_errores_crc, enl_timeouts_ready, enl_errores_io, enl_retransmisiones | - | contadores de la capa de enlace |
| pre_temp_c, pre_throttled, pre_cpu_mhz, pre_i2c_hz, post_throttled | °C / - / MHz / Hz | estado de la Raspberry antes/después |

## data/raw/<tipo>_<bloque>_<fecha>_potencia.csv
| Campo | Unidad | Descripción |
|---|---|---|
| t_ns | ns | reloj monotónico de la Raspberry (el mismo de las corridas) |
| v_V | V | voltaje en el lado de la carga (VIN-) |
| i_mA | mA | corriente del sistema (Raspberry + ESP32) |
| p_mW | mW | potencia = v_V · i_mA |

## data/processed/corridas_con_energia.csv
Igual que las corridas, más: `p_reposo_mW` (potencia en reposo del bloque), `energia_hs_mJ`
(integral de P - P_reposo durante el handshake), `energia_corrida_mJ`, `muestras_en_hs`, `valida`.
