# Resumen Semana 8: Confidencialidad e Integridad (sin analizador)

**Fecha:** 24/10/2026
**Configuración:** ESP32 `MODO_ECO 0`, `FRAME_SIZE 128`, bus I2C a 400 kHz.

## Resultados Clave
- **Sesión TLS Híbrida:** `grupo_detectado: "hibrido"`, `esp_estado: 0`, `cierre_ok: true`.
- **Pruebas de ataque (`ataque.py`):** 5/5 ejecuciones exitosas. Todas arrojaron `"CONCLUSION": "TODAS LAS PRUEBAS PASARON"`.
- **Verificación de Confidencialidad (búsqueda en logs):**
  - En el log **sin TLS**, la palabra `TELEMETRIA` (hex `54454c454d4554524941`) se encontró **6 veces** (texto visible).
  - En el log **con TLS**, la palabra se encontró **0 veces** (texto cifrado).

## Nota sobre el analizador
Las capturas con analizador lógico quedan pendientes. La confidencialidad se verificó con el registro de tramas de la Raspberry (`ataque.py`) y se confirmará con una captura independiente.
