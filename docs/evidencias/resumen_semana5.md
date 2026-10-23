# Resumen Semana 5: Capa de Enlace Confiable (sin TLS)

**Fecha:** 23/10/2026
**Configuración:** ESP32 en `MODO_ECO 0`, `FRAME_SIZE 128`, bus I2C a 400 kHz.

## Resultados Clave
1. **Corrida inicial (20 msgs):** 0 errores. `enl_errores_crc` = 0.
2. **Prueba de resistencia (50 corridas):** 50/50 exitosas. 0 errores de CRC, 0 timeouts, 0 errores I/O.
3. **Prueba de retransmisión (corte de READY por 2s):** El enlace se recuperó solo. Registró `enl_timeouts_ready` > 0 (30 y 9) y `error: ""` en ambas pruebas.
4. **Eficiencia del enlace:** 23.36% (cálculo: (1292 + 1280) / 11008).

## Conclusión
El enlace I2C es 100% estable y confiable a 400 kHz. La capa de enlace detecta y recupera pérdidas de señal correctamente.
