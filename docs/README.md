# Documentación

| Archivo / carpeta | Contenido |
|---|---|
| `bitacora.md` | Bitácora del laboratorio |
| `decisiones.md` | Decisiones técnicas y del diseño experimental, con su justificación (entorno, N, orden de bloques…) |
| `diagramas/` | Diagrama de bloques (figura 1) y diagramas de flujo de los programas (figuras 2–8); fuentes en `diagramas/fuentes/` (`python3 fig_bloques.py`, `dot -Tpng -Gdpi=200 f2_firmware.dot -o ../f2_firmware.png`) |
| `diccionario_datos.md` | Significado y unidades de cada campo de los datos |
| `entregables/` | Documentos entregados en la materia (diagrama de bloques, descripción y diagramas de flujo) |
| `evidencias/` | Salidas y registros de cada semana, en orden cronológico ([índice](evidencias/README.md)) |
| `figuras/` | Figuras generadas por `pi/analisis.py` (`ensayo_piloto_semana09/` = ensayo con los pilotos) |
| `guias/` | Guías de laboratorio en PDF: mapa general, semanas 1–12 y versiones detalladas de 7–8 y 9–10 |
| `propuesta/` | Propuesta final, objetivos y justificación, y correspondencia objetivos ↔ capítulos |

Los scripts siguen escribiendo sus salidas nuevas en `docs/evidencias/` y `docs/figuras/`;
al cerrar cada semana se mueven a la subcarpeta que corresponde.
