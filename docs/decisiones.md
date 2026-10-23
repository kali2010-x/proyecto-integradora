# Registro de decisiones técnicas

Anotar aquí cada decisión con fecha, opciones consideradas, evidencia y responsable.

| Fecha | Decisión | Alternativas | Evidencia (archivo) |
|---|---|---|---|
| 2026-10-12 | Línea base clásica = X25519 (no P-256) | P-256 | El grupo híbrido combina X25519 + ML-KEM-768; así la diferencia medida es solo ML-KEM |
| 2026-10-12 | wolfSSL >= 5.9.4 en el ESP32 | 5.8.2 | Con 5.8.2, ~3 % de handshakes híbridos rechazados por OpenSSL 3.5 (BAD_ECPOINT); con 5.9.4, 0 de 1000 |
| | Tamaño de trama del enlace (FRAME_SIZE) | 32 / 64 / 128 | docs/evidencias/eco_*.json (semanas 3-4) |
| | Gobernador de CPU durante la campaña | ondemand / performance | (semana 9) |
## Semana 3 — Enlace I2C dedicado

- **Bus 3** (GPIO4/GPIO5, pines 7/29) dedicado al ESP32 a **100 kHz**.
- **Bus 1** (pines 3/5) para INA219 a **400 kHz**.
- **ESP32** en dirección I2C **0x28**.
- **Tramas** probadas: 32, 64 y 128 bytes con 10.000 tramas cada una.
- **Resultado**: 0 errores en todos los casos.
- **Tasa bus observada**: ~35 kbps (por debajo del límite de 100 kbps).
- **Nota**: no fue necesario cambiar a I2C por software (clock stretching no fue problema).

## Semana 4 — Decisión de FRAME_SIZE

- **FRAME_SIZE definitivo:** 128 bytes
- **Justificación:** Es el mayor tamaño con 0 errores en ambos modos (100 y 400 kHz). Las tramas grandes desperdician menos ancho de banda en cabeceras (8 B por trama).
- **Datos a 400 kHz:**
  - 32 B: 170.95 kbps, 0 errores
  - 64 B: 150.04 kbps, 0 errores
  - 128 B: 144.57 kbps, 0 errores

### Tasa de muestreo del INA219
- **1424 muestras/s** (mínimo requerido: 200).

## Semana 5 — Capa de enlace confiable

- **Mecanismo:** Tramas con MAGIC (0xA5), TIPO, SEQ, ACK, LEN y CRC-16/CCITT sobre el bus I2C.
- **Recuperación:** ARQ de parada y espera (la Raspberry reintenta si no recibe confirmación).
- **Prueba de estabilidad:** 50/50 corridas exitosas sin TLS.
- **Contadores del enlace:** 0 errores CRC, 0 timeouts, 0 errores I/O, 0 retransmisiones.
- **Prueba de retransmisión:** Se desconectó el cable READY por ~2 segundos durante una corrida de 200 mensajes. El enlace registró timeouts (`enl_timeouts_ready` = 30 y 9) y se recuperó solo, terminando sin errores (`error: ""`, `esp_estado: 0`).
- **Eficiencia del enlace:** 23.36% (fórmula: `(enl_payload_tx + enl_payload_rx) / enl_bytes_bus`). El resto del ancho de banda se usa en cabeceras, CRC y sondeos.
## Semana 6. Hallazgo: validación de certificados en un nodo sin reloj de tiempo real

- **Problema:** El ESP32 no tiene una fuente de hora con batería ni NTP en el banco de pruebas. Al arrancar, su reloj marca 1970, y wolfSSL rechaza el certificado X.509 del servidor (válido desde octubre de 2026) por estar "aún no vigente". En el registro aparece como `esp_estado = -3`.
- **Solución en el laboratorio:** `main.c` fija el reloj a la fecha de compilación más 1 día de margen (`settimeofday()`) antes de cargar el certificado. Se mantiene la verificación de la firma y de las fechas.
- **Limitación:** La hora depende de la fecha de compilación; con un firmware antiguo, el nodo podría aceptar un certificado vencido.
- **Implicación:** Cualquier nodo IoT que valide certificados X.509 en TLS, sea con intercambio clásico o híbrido, necesita una fuente de hora confiable (NTP, RTC externo o la hora entregada por la unidad de borde). Se incluirá como recomendación de despliegue.
