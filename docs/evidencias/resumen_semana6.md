# Resumen Semana 6: TLS 1.3 Clásico sobre I2C (X25519)

**Fecha:** 23/10/2026
**Configuración:** ESP32 `MODO_ECO 0`, `FRAME_SIZE 128`, bus I2C a 400 kHz.

## Resultados Clave
- **Sesión TLS 1.3 completada:** `tls_version: "TLSv1.3"`, `cifrado: "TLS_AES_256_GCM_SHA384"`.
- **Grupo detectado:** `clasico` (X25519).
- **Estabilidad:** 30/30 corridas correctas. 0 errores de CRC, 0 timeouts, 0 errores I/O.
- **ClientHello:** 180 bytes.
- **Tiempo de handshake (ESP32):** 1,898,823 µs (~1.9 s).
- **Memoria usada:** Heap: 10,976 B. Stack libre: 28,522 B.
- **Rendimiento útil:** 92.3 kbps.

## Hallazgo
El ESP32 no tiene RTC, por lo que fue necesario fijar el reloj a la fecha de compilación para que pudiera validar el certificado X.509 del servidor. Documentado en `docs/decisiones.md`.
