# Registro de decisiones técnicas

Anotar aquí cada decisión con fecha, opciones consideradas, evidencia y responsable.

| Fecha | Decisión | Alternativas | Evidencia (archivo) |
|---|---|---|---|
| 2026-10-12 | Línea base clásica = X25519 (no P-256) | P-256 | El grupo híbrido combina X25519 + ML-KEM-768; así la diferencia medida es solo ML-KEM |
| 2026-10-12 | wolfSSL >= 5.9.4 en el ESP32 | 5.8.2 | Con 5.8.2, ~3 % de handshakes híbridos rechazados por OpenSSL 3.5 (BAD_ECPOINT); con 5.9.4, 0 de 1000 |
| 2026-10-21 | Tamaño de trama del enlace: FRAME_SIZE = 128 bytes | 32 / 64 | docs/evidencias/semana03_eco_i2c/ y semana04_modo_rapido_y_calibracion/: 0 errores en 10 000 tramas a 100 y 400 kbit/s; menor sobrecarga de cabecera (6,25 %) |
| 2026-10-26 | Gobernador de CPU = performance durante las mediciones | ondemand | Frecuencia fija (1,8 GHz) en todas las corridas; se vuelve a fijar después de cada reinicio (semana 9) |
| 2026-10-26 | N = 60 por configuración (campaña de octubre) | N = 30 / 45 | docs/evidencias/semana09_piloto_y_muestra/: Jain con r = ±5 % exigía 45 |
| 2026-11-17 | La campaña de 60 pasa a ser la **prueba piloto**; campaña definitiva con **N = 1 000** por configuración | Mantener N = 60 (±7 % en la energía) | data/raw/piloto_60/; cálculo en la sección «Semana 12» |
| 2026-11-17 | Ejecutar cada bloque en 10 tandas de 100 repeticiones (semilla 42 + t) | Un solo bloque de 6 000 corridas | herramientas/campana_tandas.sh: una interrupción solo obliga a repetir la tanda afectada |
| 2026-11-23 | Firmware del ESP32 compilado con `-O2` (CONFIG_COMPILER_OPTIMIZATION_PERF) | `-Og` (por defecto) / `-Os` | data/pruebas/semana12_ensayo_optimizacion/README.md: handshake clásico 1,75 s (-O2), 2,15 s (-Os), 2,52 s (-Og) |
| 2026-11-23 | Firmware y enlace optimizados (rama optimizacion-campana-1000) | Firmware de octubre | data/pruebas/semana12_ensayo_optimizacion/; herramientas/verificar_optimizaciones.py |

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

## Semana 5 — Capa de enlace confiable

- **Mecanismo:** Tramas con MAGIC (0xA5), TIPO, SEQ, ACK, LEN y CRC-16/CCITT sobre el bus I2C.
- **Recuperación:** ARQ de parada y espera (la Raspberry reintenta si no recibe confirmación).
- **Prueba de estabilidad:** 50/50 corridas exitosas sin TLS.
- **Contadores del enlace:** 0 errores CRC, 0 timeouts, 0 errores I/O, 0 retransmisiones.
- **Prueba de retransmisión:** Se desconectó el cable READY por ~2 segundos durante una corrida de 200 mensajes. El enlace registró timeouts (`enl_timeouts_ready` = 30 y 9) y se recuperó solo, terminando sin errores (`error: ""`, `esp_estado: 0`).
- **Eficiencia del enlace:** 23.36% (fórmula: `(enl_payload_tx + enl_payload_rx) / enl_bytes_bus`). El resto del ancho de banda se usa en cabeceras, CRC y sondeos.
## Semana 6. Hallazgo: validación de certificados en un nodo sin reloj de tiempo real

- **Problema:** El ESP32 no tiene una fuente de hora con batería ni NTP en el banco de pruebas. Al arrancar, su reloj marca 1970, y wolfSSL rechaza el certificado X.509 del servidor (válido desde octubre de 2026) por estar "aún no vigente". En el registro aparece como `esp_estado = -3`.
- **Solución en el laboratorio:** `main.c` fija el reloj a la fecha de compilación más 1 día de margen (`settimeofday()`) antes de cargar el certificado. Se mantiene la verificación de la firma y de las fechas.
- **Limitación:** La hora depende de la fecha de compilación; con un firmware antiguo, el nodo podría aceptar un certificado vencido.
- **Implicación:** Cualquier nodo IoT que valide certificados X.509 en TLS, sea con intercambio clásico o híbrido, necesita una fuente de hora confiable (NTP, RTC externo o la hora entregada por la unidad de borde). Se incluirá como recomendación de despliegue.

## Semana 7. TLS 1.3 Híbrido sobre I2C

- **Mecanismo:** Intercambio híbrido `X25519MLKEM768` (clásico + post-cuántico).
- **Memoria:** El ESP32 tiene suficiente RAM y pila para soportar ML-KEM sin reinicios (`esp_stack_libre` > 28 KB).
- **Costo:** El ClientHello híbrido es 7.6 veces más grande (1364 B vs 180 B) y el handshake tarda un 53.5% más (3.01 s vs 1.96 s), aunque esto último se vio afectado por la conexión del analizador lógico.
- **Conclusión:** La migración post-cuántica es viable en hardware de bajo costo como el ESP32.



## Semana 8. Confidencialidad e integridad (pruebas sin analizador)

- **Pruebas de manipulación:** La capa de enlace (CRC) no protege contra ataques maliciosos, pero TLS 1.3 (AEAD) rechaza las alteraciones y reinyecciones. Las 5 pruebas de `ataque.py` arrojaron "TODAS LAS PRUEBAS PASARON".
- **Confidencialidad:** Se comparó la telemetría en el bus buscando la palabra "TELEMETRIA" en los logs. Sin TLS apareció 6 veces; con TLS 0 veces. Esto demuestra que el cifrado híbrido protege los datos en el bus.
- **Pendiente:** Captura con analizador lógico (PulseView) para tener una evidencia independiente al hardware de la Raspberry.

### Interpretación para el Capítulo 3
El CRC de la capa de enlace protege contra errores accidentales del bus, pero un atacante puede recalcularlo. TLS 1.3 usa cifrado autenticado (AEAD) con un número de secuencia por registro, por lo que cualquier alteración o repetición invalida la etiqueta de autenticación y la sesión se aborta. Estas pruebas verifican el comportamiento de la implementación; no constituyen una prueba formal de seguridad, y la resistencia frente a una computadora cuántica proviene del diseño del estándar, no de este experimento.

## Semana 9 - Entorno de la campaña
- Fecha: 26/10/2026
- Commit congelado: 3e0e0bf (etiqueta v0.9-campana). FRAME_SIZE = 128.
- Gobernador de CPU: performance (se fija después de cada reinicio).
- Red: SSH por Wi-Fi; Wi-Fi y Bluetooth se mantienen igual en todas las mediciones.
- ESP32 alimentado por USB desde la Raspberry; analizador lógico desconectado.
- esp_heap_usado_hs = memoria pico de wolfSSL (definición nueva desde este commit).
   

- Red: Raspberry Pi conectada por cable Ethernet al router. Acceso remoto vía SSH desde laptop por Wi-Fi a la misma red. El chip Wi-Fi de la Raspberry permanece habilitado pero inactivo (no cursa tráfico), por lo que su consumo es despreciable.

## Semana 9 - Tamaño de muestra
- Pilotos: estandar (100 kbit/s) y rapido (400 kbit/s), 10 repeticiones x 6 configuraciones, 60/60 correctas en ambos.
- tamano_muestra.py (Jain 1991, r = 5 %, 95 %): n requerido maximo = 45, dado por energia_hs_mJ del clasico a 100 kbit/s
  (±6,1 % con n = 30). Los tiempos de handshake y el rendimiento tienen variacion < 0,1 %.
- Decision: N = 60 por configuracion (360 corridas por bloque). Con N = 60 la energia se estima con ±4,3 % o mejor
  en todas las configuraciones y queda margen para corridas excluidas. Duracion estimada: ~50 min (estandar), ~38 min (rapido).
- analisis.py corregido (solo analisis, no medicion) para tolerar un reposo final incompleto en un piloto.

## Semana 10 - Campaña
- Orden de bloques (semilla 42): rapido, estandar. N = 60 por configuracion (360 corridas por bloque).
- 29/10: la corrida del 29/10 08:12 (30 repeticiones, 180 corridas) se registró como «estandar», pero se ejecutó a 400 kbit/s:
  rendimiento útil 153 kbit/s (imposible en un bus de 100 kbit/s), handshake híbrido 2,05 s y 3,05 s por corrida, iguales al
  bloque rápido; el piloto a 100 kbit/s dio 43 kbit/s, 2,43 s y 4,9 s. Se guarda como repetición del bloque rápido en
  data/pruebas/semana10_campana/rapido_repetido_20261029/ y no entra al análisis. El bloque estándar queda pendiente
  (baudrate=100000, N = 60).
- 29/10 10:27: bloque estándar a 100 kbit/s, 360/360 corridas correctas (rendimiento 43 kbit/s, 4,9 s por corrida). A las 10:46
  arrancó un segundo registrador de potencia (archivo campana_estandar_20261029_104604_potencia.csv) que siguió corriendo
  después del bloque: la tasa de muestreo bajó de 645 a 310 muestras/s, la potencia de reposo final subió 40 mW (deriva del
  bloque rápido: 7 mW) y la energía por handshake de las 226 corridas posteriores subió 14-17 %. Tiempos, bytes y memoria no
  cambiaron. Se guarda en data/pruebas/semana10_campana/estandar_con_registrador_extra_20261029/ y el bloque estándar se repite.
  El registro sobrante va a descartado/; la copia del 081204 que había quedado en data/raw se elimina (ya está en rapido_repetido).
- 29/10 11:33: bloque estándar definitivo (100 kbit/s, N = 60): 360/360 correctas, 647 muestras/s constantes, deriva del reposo
  11 mW y energía por handshake estable entre la primera y la segunda mitad del bloque. El arranque abortado de las 11:31
  (30 s, sin corridas) se mueve a data/pruebas/semana10_campana/descartado/. Semana 10 cerrada: data/raw contiene solo los
  dos bloques oficiales (rapido 27/10 y estandar 29/10).

## Semana 11 - Análisis de la campaña de octubre (hoy, prueba piloto)
- Fecha: 29/10/2026. Se analizaron las 720 corridas (360 por bloque, 60 por configuración), todas válidas, con
  `pi/analisis.py`. Resultados en `data/processed/piloto_60/` y tabla en `docs/evidencias/semana11_analisis/s11_tabla_resultados.md`.
- **Decisión: la energía se reporta con la mediana y se compara con Mann-Whitney.** Shapiro-Wilk rechazó la normalidad
  (p < 10⁻²⁴) y entre 7 % y 11 % de los handshakes tuvo energía atípica (hasta ~1 000 mJ), repartida al azar en el orden y en
  los tres tamaños: es actividad de fondo de la Raspberry, porque el INA219 mide todo el sistema. El tiempo se compara con Welch.
- **Decisión: la energía no se compara entre bloques**, solo híbrido frente a clásico dentro de cada bloque: los bloques se
  midieron en días distintos, con reposo distinto (2 574 frente a 2 740 mW) y distinta tasa de muestreo (646 frente a 1 991 muestras/s).
- Hallazgo: el sobrecosto de tiempo del híbrido baja de +25,5 % (100 kbit/s) a +7,8 % (400 kbit/s) porque lo que crece es la
  transmisión (ClientHello de 1 364 B frente a 180 B); el procesamiento del ESP32 (etapa 3) es casi igual en ambos grupos.
- Se agregaron figuras para la tesis, `data/README_dataset.md`, la forma de reproducir sin la clave privada (`certs/README.md`)
  y las capturas del analizador lógico (sin TLS, clásico e híbrido) en `docs/evidencias/semana08_confidencialidad/analizador/`.

## Semana 12 - Tamaño de muestra definitivo (N = 1 000) y preparación de la campaña
### Por qué se aumentó N
- La tutora pidió reducir el error de las medias. Con N = 60, la semiamplitud del IC 95 % de la energía por handshake era de
  ±3,2 % a ±7,4 % según la configuración, porque la energía es la métrica más variable (el tiempo, los bytes y el rendimiento
  tienen coeficiente de variación menor que 1,5 % y ya eran precisos).
- Criterio de Jain (1991), ecuación (1.7): n = (z · CV / r)², con z = 1,96 (95 %) y r = error relativo buscado. Con los CV medidos
  en el piloto (energía: 12,5 % a 29,1 %), r = ±1 % exige n ≈ 1 000 cuando CV ≈ 16 %, el valor típico del piloto.
- **Decisión: N = 1 000 por configuración** (6 000 corridas por bloque, 12 000 en total; ≈ 13,5 h a 100 kbit/s y ≈ 10,5 h a
  400 kbit/s). Error esperado con r = 1,96 · CV / √N: energía ±0,8 % a ±1,1 % en 8 de las 12 configuraciones y hasta ±1,8 % en
  el clásico a 100 kbit/s (CV 24-29 %), que para ±1 % necesitaría de 2 200 a 3 300 corridas; ese margen se acepta para que la
  campaña dure un día. Tiempo, bytes y rendimiento: error menor que ±0,1 %.
- «±1 %» significa que, con 95 % de confianza, la media medida está a menos de 1 % de la media real; no es una «eficacia del 99 %».
- Las 720 corridas de octubre se conservan sin cambios como **prueba piloto** en `data/raw/piloto_60/` y
  `data/processed/piloto_60/` (movidas con `git mv`, con su historia). Archivos viejos sin versionar: `data/raw/antiguos/`.

### Optimización del código (rama `optimizacion-campana-1000`)
- CRC-16 por tabla (ESP32) y con `binascii.crc_hqx` (Raspberry), búfer circular por bloques y espera de READY por flanco en
  vez de sondeo. `herramientas/verificar_optimizaciones.py`: resultados idénticos al código original (CRC en 20 000 y 200 000
  tramas; búfer en 300 000 operaciones).
- Al compilar el firmware desde el repositorio aparecieron tres ajustes que solo existían en la copia local con la que se grabó
  el firmware de octubre y ahora quedan versionados: dos líneas sueltas en `user_settings.h` que impedían compilar;
  el ajuste del reloj con `settimeofday()` descrito en la semana 6 (sin él, estado -3: certificado «aún no vigente»), y
  `WOLFSSL_PQC_HYBRIDS` (sin él, estado -5: wolfSSL 5.9.4 no ofrece el grupo X25519MLKEM768).
- `ataque.py` daba «TODAS LAS PRUEBAS PASARON» aunque el handshake no empezara (los tiempos agotados contaban como rechazo);
  ahora exige que la corrida con TLS termine sin error.
- `prueba_eco.py` requiere el firmware de eco (MODO_ECO = 1); con el firmware TLS todas las tramas salen «distintas» y no indica
  falla. El cableado se verificó con `i2cdetect` (0x28 en el bus 3 y 0x40 en el bus 1) y con las corridas.

### Verificación antes de la campaña (23/11/2026)
- `ataque.py`: sin TLS el marcador «TELEMETRIA» es visible y con TLS no; las tres manipulaciones se rechazan después de un
  handshake correcto (`BAD_RECORD_MAC` / `RECORD_LAYER_FAILURE` en la Raspberry; -180, falla de autenticación AES-GCM, en el ESP32).
- Ensayo de 12 corridas a 100 kbit/s: 12/12 sin error; INA219 a 646 muestras/s.
- Evidencia: `data/pruebas/semana12_ensayo_optimizacion/`.
- Optimización del compilador del ESP32: el firmware de octubre se había compilado con una configuración local que no quedó
  versionada. Se probaron las tres opciones con 12 corridas cada una (handshake clásico / híbrido): `-Og` 2,52 / 2,97 s;
  `-Os` 2,15 / 2,62 s; `-O2` 1,75 / 2,20 s; piloto de octubre 1,93 / 2,43 s. Ninguna reproduce el piloto. **Decisión: `-O2`**
  (rendimiento), fijado en `esp32/firmware/sdkconfig.defaults` para que cualquier compilación desde el repositorio sea igual.
  La diferencia está solo en el cálculo dentro del ESP32 (etapa 3); la transmisión y la memoria no cambian. Por eso los tiempos
  absolutos de la campaña definitiva no se comparan con el piloto: el piloto solo se usó para estimar la variabilidad y fijar N.

### Campaña definitiva: bloque estándar (100 kbit/s)
- 23/11/2026 08:01 a 24/11/2026: 10 tandas de 600 corridas (semillas 42 a 51), firmware `-O2`.
- 23/11/2026, ~21:00: corte de luz durante la tanda 10 (464 de 600 corridas). La tanda incompleta se apartó en
  `data/descartados/` y se repitió completa con la misma semilla (51) el 24/11 (`campana_estandar_20261124_075236_*`).
  Las tandas 1 a 9 no se afectaron. Después del corte se volvió a fijar el gobernador en performance y se lanzó dentro de tmux.
- Resultado: 6 000/6 000 corridas correctas, 0 retransmisiones, 3 errores de CRC recuperados por el enlace.

### Campaña definitiva: bloque rápido (400 kbit/s) y análisis
- 24/11/2026 21:26 a 25/11/2026: 10 tandas de 600 corridas (semillas 42 a 51), firmware `-O2`. Ensayo previo de 12 corridas
  a 400 kbit/s sin error (handshake 1,70 / 1,83 s).
- Hallazgo: en la tanda 7 (semilla 48, `campana_rapido_20261125_031431`) el registrador del INA219 terminó a los 1 147 s por
  un error de E/S del bus I²C 1; 406 corridas quedaron sin potencia y el análisis les asignaba ≈ -5 mJ como válidas.
  **Decisión:** apartar la tanda en `data/descartados/` y repetirla con la misma semilla (26/11, `campana_rapido_20261126_055154`,
  0 lecturas fallidas); y corregir el código para que no vuelva a pasar inadvertido: `potencia.py` reintenta lecturas,
  `campana.py` se detiene si el registrador muere, `campana_tandas.sh` exige potencia hasta el final del reposo y
  `analisis.py` deja vacía la energía sin registro.
- Resultado final (etiqueta `v1.1-campana-1000`): 12 000/12 000 corridas válidas, 0 retransmisiones, 4 errores de CRC
  recuperados.
- **Error alcanzado (semiamplitud del IC 95 % / media):** tiempo del handshake, bytes y rendimiento < ±0,01 %. Energía por
  handshake: ±0,9 % a ±1,2 % por grupo y bloque (n = 3 000) y ±1,5 % a ±2,3 % por configuración (n = 1 000). La energía
  varió más que en el piloto (CV 24-37 % frente a 12-29 %), sobre todo entre tandas, por la actividad de fondo de la
  Raspberry a lo largo de las horas; como el orden es aleatorio dentro de cada tanda, la comparación híbrido-clásico no se
  sesga. El objetivo de ±1 % se cumple en el tiempo y los bytes y, para la energía, a nivel de grupo y bloque.
