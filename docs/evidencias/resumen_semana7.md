# Resumen Semana 7: TLS 1.3 Híbrido sobre I2C

**Fecha:** 24/10/2026
**Configuración:** ESP32 `MODO_ECO 0`, `FRAME_SIZE 128`, bus I2C a 400 kHz.

## Resultados Clave
- **Sesión TLS Híbrida:** `grupo_detectado: "hibrido"`, `esp_estado: 0`, `cierre_ok: true`.
- **Estabilidad:** 30/30 corridas correctas (15 clásico, 15 híbrido). 0 errores de CRC, 0 timeouts, 0 errores I/O.
- **Comparación de medias:**
  - **Tiempo de handshake (`esp_t_hs_us`):** Clásico 1,962,331 µs vs Híbrido 3,013,438 µs (**+53.5%**).
  - **ClientHello:** Clásico 180 B vs Híbrido 1,364 B (**+657.7%**).
  - **Heap usado (`esp_heap_usado_hs`):** Clásico 10,976 B vs Híbrido 10,968 B (sin cambios significativos).
  - **Pila libre (`esp_stack_libre`):** Clásico 28,608 B vs Híbrido 28,623 B (sin problemas de memoria).
  - **Rendimiento (`rend_util_kbps`):** 19.8 kbps en ambos (el cuello de botella fue la presencia del analizador lógico en el bus).

**Conclusión:** El intercambio híbrido X25519MLKEM768 es viable en el ESP32 (suficiente memoria), pero incrementa el tamaño del ClientHello en 7.6 veces y el tiempo de handshake en un 53.5% en comparación con X25519.
