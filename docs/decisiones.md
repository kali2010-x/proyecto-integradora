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
## Semana 6 — Hallazgo: Validación de certificados en IoT sin RTC

- **Problema:** El ESP32 no tiene RTC con batería. Al arrancar, su reloj marca 1970, lo que hace que rechace el certificado X.509 del servidor (válido desde Oct 2026) con error `-3`.
- **Solución:** Se modificó `main.c` para fijar el reloj a la fecha de compilación + 1 día de margen usando `settimeofday()`.
- **Implicación para la tesis:** En un despliegue real, un nodo IoT sin RTC requiere NTP o un RTC externo para validar certificados X.509. Este es un requisito de hardware/software que debe considerarse en la migración post-cuántica.
