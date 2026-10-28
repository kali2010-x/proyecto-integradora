# Bitácora del proyecto

**Proyecto:** INGE-3286 — Implementación de un modelo criptográfico híbrido poscuántico para dispositivos IoT de bajo costo  
**Integrantes:** Kevin Pérez, David Yela · **Tutora:** María Antonieta Álvarez Villanueva

Organizada por las semanas de la plataforma de Materia Integradora. Cada actividad indica las semanas del laboratorio que cubre y sus evidencias en el repositorio. El PDF de cada semana para adjuntar en la plataforma está en [`bitacora_semanal/`](bitacora_semanal/).

## Semana 1 (28/09/2026 – 02/10/2026)

### 1.1 Preparación del entorno de la Raspberry Pi 4 y pruebas preliminares de criptografía poscuántica

| Campo | Valor |
|---|---|
| Inicio | 28/09/2026 |
| Cumplimiento | 01/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_01.pdf` |

**Descripción:** Se creó el repositorio del proyecto en GitHub (27/09) y se preparó la Raspberry Pi 4 con Raspberry Pi OS Lite de 64 bits y acceso por SSH. Se compiló la biblioteca liboqs 0.16.0 para disponer de los algoritmos poscuánticos (28/09). Con el sensor INA219 se registraron 10 minutos de consumo de la Raspberry en reposo para conocer su línea base (29/09). Se ejecutó un piloto de rendimiento de Kyber (30/09) y un benchmark de ECDH P-256, con el que se registró la decisión sobre la curva clásica de referencia (01/10). Paralelamente se revisó la línea de investigación de la tutora y se elaboraron las propuestas iniciales del proyecto.

**Evidencias:** `legacy/docs/liboqs_build_log.txt`, `legacy/data/ina219_reposo_10min.csv`, `legacy/data/kyber_piloto.csv`, `legacy/data/ecdh_piloto.csv`, `legacy/docs/decision_curva.md`

## Semana 2 (05/10/2026 – 09/10/2026)

### 2.1 Definición y corrección de la propuesta: TLS 1.3 híbrido poscuántico sobre el bus I2C

| Campo | Valor |
|---|---|
| Inicio | 05/10/2026 |
| Cumplimiento | 09/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Documentación |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_02.pdf` |

**Descripción:** A pedido del cliente se redefinió el proyecto: establecer sesiones TLS 1.3 con intercambio de claves híbrido (X25519 + ML-KEM-768) entre un nodo sensor ESP32 y una Raspberry Pi 4 comunicados por el bus I2C, midiendo tiempo, tráfico, memoria y energía. Se elaboró el estado del arte con fuentes revisadas y se aplicaron las correcciones del Ing. Medina (título, citas en todas las afirmaciones, unidades en kbit/s, estado del arte en prosa y justificación de 30 repeticiones) y del cliente (alcance solo I2C, un único sensor INA219 en la Raspberry, OpenSSL 3.5 en el servidor y wolfSSL en el ESP32). Se planificó el trabajo práctico en 12 semanas con una guía de laboratorio por semana.

**Evidencias:** `docs/guias/00_Mapa_del_trabajo_practico.pdf`

## Semana 3 (12/10/2026 – 16/10/2026)

### 3.1 Semanas 1 y 2 del laboratorio: entorno criptográfico, wolfSSL en el ESP32 y simulación del enlace

| Campo | Valor |
|---|---|
| Inicio | 12/10/2026 |
| Cumplimiento | 13/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_03.pdf` |

**Descripción:** Se configuró el acceso SSH (12/10), se reorganizó el repositorio (código nuevo en pi/, esp32/, sim/ y herramientas/; versión anterior en legacy/) y se generó el certificado del servidor sin subir la clave privada. Se verificó OpenSSL 3.5.7 con ML-KEM y la negociación del grupo X25519MLKEM768. En el ESP32 se compiló wolfSSL y se midió el costo criptográfico: ML-KEM-768 tarda de 6 a 9 ms por operación, frente a unos 400 ms de X25519 y 700 ms de la verificación ECDSA. En el simulador se completaron sesiones clásicas e híbridas y las 5 pruebas de ataque. Se detectó que wolfSSL 5.8.2 falla en ~3 % de los handshakes híbridos contra OpenSSL 3.5; con wolfSSL 5.9.4 hubo 0 fallos en 1.000 pruebas, por lo que se adoptó esa versión.

**Evidencias:** `docs/evidencias/semana01-02_entorno_y_simulacion/`, `data/pruebas/semana02_simulacion/`, `docs/guias/Semana_01_Base_del_laboratorio.pdf`, `docs/guias/Semana_02_ESP32_wolfSSL_y_simulador.pdf`

### 3.2 Informe de avance y ajuste de la propuesta según la retroalimentación de la tutora

| Campo | Valor |
|---|---|
| Inicio | 13/10/2026 |
| Cumplimiento | 16/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Documentación |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_03.pdf` |

**Descripción:** Se presentó al cliente el informe de avance de las semanas 1 y 2 (13/10). Con la retroalimentación de la tutora se reestructuró la propuesta: título más general sin nombres de dispositivos, definición del problema de lo general a lo específico con datos estadísticos (crecimiento del IoT, probabilidad de una computadora cuántica relevante, plazos del NIST para 2030 y 2035) y un estado del arte y una solución centrados en el problema específico. Se preparó el borrador del Capítulo 1 en el formato de la materia y un resumen del proyecto para el profesor guía (16/10).

**Evidencias:** `docs/propuesta/`

## Semana 4 (19/10/2026 – 23/10/2026)

### 4.1 Semanas 3 y 4 del laboratorio: bus I2C dedicado, prueba de eco, modo rápido y calibración del INA219

| Campo | Valor |
|---|---|
| Inicio | 21/10/2026 |
| Cumplimiento | 23/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_04.pdf` |

**Descripción:** Se cableó el ESP32 a un bus I2C dedicado de la Raspberry (bus 3, pines 7 y 29, pull-ups de 4,7 kΩ) separado del bus del INA219 (bus 1). Se corrigió el cableado del sensor y se resolvió una conexión errónea del pin 3V3 del ESP32. La prueba de eco con 10.000 tramas de 32, 64 y 128 bytes dio 0 errores (21/10). En modo rápido (400 kbit/s) también hubo 0 errores y se fijó el tamaño de trama en 128 bytes. Se calibró el INA219 contra el multímetro: subestima la corriente de forma sistemática (≈5 %), lo que afecta por igual a ambos esquemas (23/10).

**Evidencias:** `docs/evidencias/semana03_eco_i2c/`, `docs/evidencias/semana04_modo_rapido_y_calibracion/`

### 4.2 Semanas 5 y 6 del laboratorio: capa de enlace confiable y TLS 1.3 clásico sobre I2C

| Campo | Valor |
|---|---|
| Inicio | 23/10/2026 |
| Cumplimiento | 23/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_04.pdf` |

**Descripción:** Se puso en marcha la capa de enlace (tramas con CRC-16, numeración y retransmisión): 50 de 50 corridas sin errores y recuperación automática al cortar la línea READY durante 2 s. Luego se establecieron sesiones TLS 1.3 clásicas (X25519, TLS_AES_256_GCM_SHA384) entre el ESP32 y la Raspberry: 30 de 30 corridas correctas, ClientHello de 180 bytes y handshake de ≈1,9 s. Hallazgo: el ESP32 arranca con el reloj en 1970 y rechazaba el certificado del servidor por no estar vigente; se corrigió fijando el reloj a la fecha de compilación y se registró como recomendación de despliegue (un nodo sin reloj necesita NTP o RTC).

**Evidencias:** `docs/evidencias/semana05_capa_enlace/`, `docs/evidencias/semana06_tls_clasico/`, `data/pruebas/semana05_capa_enlace/`, `data/pruebas/semana06_tls_clasico/`

### 4.3 Propuesta final: título, objetivos, justificación y registro del proyecto en la plataforma

| Campo | Valor |
|---|---|
| Inicio | 22/10/2026 |
| Cumplimiento | 23/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Documentación |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_04.pdf` |

**Descripción:** Con las observaciones del profesor guía y de la tutora se eligió el título «Implementación de un modelo criptográfico híbrido poscuántico para dispositivos IoT de bajo costo». Se redactó un objetivo general con un solo verbo (qué, cómo y para qué) y tres objetivos específicos alineados con los capítulos del informe, y se reescribió la justificación en tres razones: plazos de migración, evidencia limitada a otros enlaces y aporte práctico. Se prepararon los textos para registrar el proyecto en la plataforma (problema, resultados esperados, ODS e indicadores de impacto).

**Evidencias:** `docs/propuesta/Propuesta_integradora_final.pdf`, `docs/propuesta/Propuesta_integradora_final_Objetivos_y_Justificacion.pdf`

### 4.4 Semanas 7 y 8 del laboratorio: TLS 1.3 híbrido sobre I2C y pruebas de confidencialidad e integridad

| Campo | Valor |
|---|---|
| Inicio | 24/10/2026 |
| Cumplimiento | 24/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_04.pdf` |

**Descripción:** Se activó el intercambio híbrido X25519MLKEM768 en el ESP32. Hallazgo: en ESP-IDF, wolfSSL necesita la opción WOLFSSL_PQC_HYBRIDS para ofrecer el grupo híbrido; sin ella el nodo lo rechazaba. Con la corrección, 30 de 30 corridas mezcladas (clásico e híbrido) fueron correctas: el ClientHello híbrido ocupa 1.364 bytes frente a 180 del clásico (7,6 veces más). Las pruebas de ataque (alterar un bit en ambos sentidos y reinyectar tramas, recalculando el CRC) se aprobaron en todas las ejecuciones: TLS rechazó toda manipulación. En el registro de tramas, la palabra «TELEMETRIA» aparece 6 veces sin TLS y 0 veces con TLS. La captura independiente con el analizador lógico quedó pendiente porque su conexión altera el bus.

**Evidencias:** `docs/evidencias/semana07_tls_hibrido/`, `docs/evidencias/semana08_confidencialidad/`, `data/pruebas/semana07_tls_hibrido/`, `data/pruebas/semana08_ataques/`

## Semana 5 (26/10/2026 – 30/10/2026)

### 5.1 Semana 9 del laboratorio: firmware final, entorno congelado, pruebas piloto y tamaño de muestra

| Campo | Valor |
|---|---|
| Inicio | 26/10/2026 |
| Cumplimiento | 27/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_05.pdf` |

**Descripción:** Antes de congelar el entorno se corrigió la medición de memoria del ESP32 para registrar el pico de memoria de wolfSSL durante el handshake (etiqueta v0.9-campana). Se documentó el entorno (gobernador de CPU en performance, red y commit congelado). Se ejecutaron dos pilotos de 60 corridas, a 100 y a 400 kbit/s, ambos sin fallas. Resultados del piloto: el handshake híbrido tarda 25,5 % más que el clásico a 100 kbit/s y 7,9 % más a 400 kbit/s, y la memoria pico aumenta 3,8 %. Con el criterio de Jain (±5 %, 95 % de confianza) se fijó N = 60 repeticiones por configuración.

**Evidencias:** `docs/evidencias/semana09_piloto_y_muestra/`, `data/pruebas/semana09_piloto/`

### 5.2 Semana 10 del laboratorio: campaña de mediciones, bloque a 400 kbit/s

| Campo | Valor |
|---|---|
| Inicio | 27/10/2026 |
| Cumplimiento | 27/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Laboratorio |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_05.pdf` |

**Descripción:** Se sorteó el orden de los bloques (semilla 42: primero 400 kbit/s, luego 100 kbit/s) y se ejecutó el bloque a 400 kbit/s con 360 corridas en orden aleatorio: 360 de 360 correctas, sin retransmisiones. Medias: handshake clásico 1,90 s frente a 2,05 s del híbrido (+7,8 %); ClientHello 180 frente a 1.364 bytes; memoria pico 61.279 frente a 63.583 bytes. La potencia de reposo varió solo 7,3 mW entre el inicio y el final del bloque. Los datos se comprimieron y respaldaron en GitHub.

**Evidencias:** `docs/evidencias/semana10_campana/`, `data/raw/`

### 5.3 Reporte al cliente y organización del repositorio del proyecto

| Campo | Valor |
|---|---|
| Inicio | 27/10/2026 |
| Cumplimiento | 28/10/2026 |
| Responsable | Kevin Pérez |
| Tipo de actividad | Documentación |
| Adjunto | `docs/bitacora_semanal/Bitacora_Semana_05.pdf` |

**Descripción:** Se envió al cliente un resumen de avance con los resultados preliminares y la descripción del problema con el analizador lógico (al conectarlo al bus a 400 kbit/s aumentan los errores del enlace), junto con alternativas para la captura independiente. Se reorganizó el repositorio en orden cronológico: evidencias y datos por semana, guías y propuesta en docs/, y un README con la estructura y la cronología del trabajo.

**Evidencias:** `README.md`, `docs/evidencias/README.md`, `data/README.md`

## Compromisos de las próximas semanas

Actividades planificadas; se registran como cumplidas solo cuando se realicen.

| Semana | Fechas | Compromiso |
|---|---|---|
| 6 | 02/11/2026 – 06/11/2026 | Completar la campaña con el bloque a 100 kbit/s (360 corridas) y realizar las capturas con el analizador lógico (sin TLS y con TLS híbrido). |
| 7 | 09/11/2026 – 13/11/2026 | Análisis estadístico de la campaña: medias, intervalos de confianza, comparaciones híbrido vs. clásico y figuras (semana 11 del laboratorio). |
| 8 | 16/11/2026 – 20/11/2026 | Cierre técnico (semana 12 del laboratorio) y redacción del Capítulo 2 (metodología y desarrollo). |
| 9 | 23/11/2026 – 27/11/2026 | Redacción del Capítulo 3 (resultados y análisis) y revisión con el profesor guía y la tutora. |
