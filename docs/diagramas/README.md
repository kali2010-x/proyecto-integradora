# Diagramas

| Archivo | Contenido |
|---|---|
| `bloques_v5.png` | Diagrama de bloques general por fases (figura 1 del entregable) |
| `flujo_firmware.png` | Firmware del ESP32: `main.c` y `cliente_tls.c` |
| `flujo_enlace.png` | Capa de enlace: `enlace.py` (maestro) y `enlace.c` (esclavo) |
| `flujo_servidor.png` | Una corrida en `servidor_tls.py` |
| `flujo_campana.png` | Orquestador `campana.py` |
| `flujo_potencia.png` | Registrador `potencia.py` |
| `flujo_ataque.png` | Pruebas de seguridad `ataque.py` |
| `flujo_analisis.png` | `analisis.py` y `tamano_muestra.py` |

Para regenerar una figura (desde `fuentes/`): `python3 f_campana.py && node render.js flujo_campana.html flujo_campana.png`
(el diagrama de bloques: `python3 bloques_v5.py && node render.js bloques_v5.html bloques_v5.png`). Requiere Python con Pillow, Node con Playwright y la fuente Liberation Sans.
