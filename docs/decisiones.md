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
