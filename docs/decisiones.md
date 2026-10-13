# Registro de decisiones técnicas

Anotar aquí cada decisión con fecha, opciones consideradas, evidencia y responsable.

| Fecha | Decisión | Alternativas | Evidencia (archivo) |
|---|---|---|---|
| 2026-10-12 | Línea base clásica = X25519 (no P-256) | P-256 | El grupo híbrido combina X25519 + ML-KEM-768; así la diferencia medida es solo ML-KEM |
| 2026-10-12 | wolfSSL >= 5.9.4 en el ESP32 | 5.8.2 | Con 5.8.2, ~3 % de handshakes híbridos rechazados por OpenSSL 3.5 (BAD_ECPOINT); con 5.9.4, 0 de 1000 |
| | Tamaño de trama del enlace (FRAME_SIZE) | 32 / 64 / 128 | docs/evidencias/eco_*.json (semanas 3-4) |
| | Gobernador de CPU durante la campaña | ondemand / performance | (semana 9) |
