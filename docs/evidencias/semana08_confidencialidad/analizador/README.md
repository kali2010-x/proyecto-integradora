# Capturas del analizador lógico (bus I²C)

Analizador lógico USB, PulseView, 1 MHz. SDA = D0, SCL = D1, decodificador I²C. Dirección del ESP32: 0x28.

| Imagen | Captura | Qué demuestra |
|---|---|---|
| `Evidencia_analizador_1_sin_TLS.png` | `captura_sin_tls.sr` | Sin TLS la telemetría viaja en claro: `54 45 4C 45 4D 45 54 52 49 41` = «TELEMETRIA» (t = +2 296 817 µs). |
| `Evidencia_analizador_2_TLS_clasico.png` | `captura_clasico.sr` | TLS 1.3 con X25519: ClientHello de 175 B (180 B con la cabecera del registro), en 2 tramas (t = +2 859 602 µs). |
| `Evidencia_analizador_3_TLS_hibrido.png` | `captura_hibrido.sr` | TLS 1.3 con X25519MLKEM768: ClientHello de 1359 B (1364 B), en 12 tramas (t = +2 282 346 µs). |

Los archivos `.pvs` guardan la configuración de PulseView (canales y decodificador). Los recuadros y las notas de las imágenes se añadieron sobre las capturas de pantalla; los bytes se verificaron contra los `.sr`.

Formato de la trama de enlace: `A5` | tipo (`00` sondeo, `01` datos, `02` control, `03` reinicio) | secuencia | ACK | longitud (2 B) | carga útil | CRC-16.
