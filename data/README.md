# Datos

Cada ejecución deja tres archivos con el mismo sello de fecha y hora:
`*_meta.json` (configuración y ventanas de reposo), `*_corridas.jsonl` (una línea por corrida) y
`*_potencia.csv.gz` (lecturas del INA219, comprimidas). Los campos están descritos en
[`docs/diccionario_datos.md`](../docs/diccionario_datos.md).

## `raw/` — campaña oficial (semana 10)

Solo los bloques de la campaña final, con N = 60 repeticiones por configuración (360 corridas por bloque).

| Bloque | Archivos | Estado |
|---|---|---|
| rápido (400 kbit/s) | `campana_rapido_20261027_015155_*` | 360/360 correctas |
| estándar (100 kbit/s) | `campana_estandar_*` | pendiente |

`campana.py`, `ataque.py` y `resumen_rapido.py` siguen escribiendo y leyendo en `raw/`.

## `pruebas/` — pruebas y pilotos (semanas 2 a 9)

| Carpeta | Contenido |
|---|---|
| `semana02_simulacion/` | Pruebas de ataque en el simulador (13/10) |
| `semana05_capa_enlace/` | `campana_prueba_enlace_*`: 50 corridas sin TLS |
| `semana06_tls_clasico/` | `campana_prueba_clasico_*`: 30 corridas TLS clásico |
| `semana07_tls_hibrido/` | `campana_prueba_hibrido_*`: dos series de 30 corridas mezcladas (19:14 y 23:33 del 24/10) |
| `semana08_ataques/` | `ataques_*.json` (todas con TODAS LAS PRUEBAS PASARON) y registros de tramas sin y con TLS |
| `semana09_piloto/` | Pilotos usados: `piloto_estandar_20261027_003359_*` y `piloto_rapido_20261027_005041_*` |
| `semana09_piloto/descartado_repetido/` | `piloto_estandar_20261027_002249_*`: primera ejecución del piloto estándar, repetida; su reposo final quedó incompleto |

Para recalcular el tamaño de muestra solo con los pilotos válidos:

```bash
cd pi && python3 tamano_muestra.py ../data/pruebas/semana09_piloto/piloto_*_meta.json
```

## `processed/`

Salidas de `pi/analisis.py`. `ensayo_piloto_semana09/` guarda el ensayo general hecho con los pilotos;
el análisis final de la campaña se generará en `processed/`.
