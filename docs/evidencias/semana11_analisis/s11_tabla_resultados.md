# Semana 11 · Tabla de resultados principales

Fuente: `data/processed/resumen.csv` y `comparaciones.csv` (720/720 corridas válidas; N = 180 por grupo y bloque).
Formato: media ± semiamplitud del IC 95 %. Sobrecosto = 100·(híbrido − clásico)/clásico, con IC 95 % bootstrap.

## Bus estándar (100 kbit/s)

| Métrica | Clásico (X25519) | Híbrido (X25519MLKEM768) | Sobrecosto [IC 95 %] | p |
|---|---|---|---|---|
| Duración del handshake (ms) | 1933,10 ± 0,03 | 2425,8 ± 0,2 | +25,5 % [25,5; 25,5] | < 0,001 (Welch) |
| ClientHello (bytes) | 180 | 1364 | +657,8 % | constante |
| Respuesta del servidor (bytes) | 745 | 1823 | +144,7 % | < 0,001 |
| Memoria pico de wolfSSL (KiB) | 59,8 | 62,1 | +3,8 % | constante |
| Energía por handshake, mediana (mJ) | 310,7 | 333,8 | +7,4 % [7,0; 8,0] | < 0,001 (Mann-Whitney) |
| Rendimiento útil (kbit/s) | 43,39 | 43,38 | 0,0 % | sin diferencia práctica |

## Bus rápido (400 kbit/s)

| Métrica | Clásico (X25519) | Híbrido (X25519MLKEM768) | Sobrecosto [IC 95 %] | p |
|---|---|---|---|---|
| Duración del handshake (ms) | 1898,3 ± 0,5 | 2046,90 ± 0,05 | +7,8 % [7,8; 7,9] | < 0,001 (Welch) |
| ClientHello (bytes) | 180 | 1364 | +657,8 % | constante |
| Respuesta del servidor (bytes) | 745 | 1823 | +144,7 % | < 0,001 |
| Memoria pico de wolfSSL (KiB) | 59,8 | 62,1 | +3,8 % | constante |
| Energía por handshake, mediana (mJ) | 470,6 | 491,7 | +4,5 % [4,2; 4,8] | < 0,001 (Mann-Whitney) |
| Rendimiento útil (kbit/s) | 153,1 | 153,2 | +0,1 % | 0,34 (sin diferencia) |

## Notas para la interpretación

- **Energía: se reporta la mediana.** Shapiro rechaza la normalidad (p < 10⁻²⁴) y hay entre 7 y 11 % de handshakes atípicos
  (hasta ~1000 mJ) repartidos al azar en el orden y en los tres tamaños de mensaje: son actividad de fondo de la Raspberry,
  porque la potencia se mide en todo el sistema. Con medias el sobrecosto sale +3,4 % [−1,4; 8,1] (p Welch 0,15) a 100 kbit/s
  y +3,8 % [0,5; 7,2] a 400 kbit/s; la mediana y Mann-Whitney son la lectura robusta.
- **La energía no se compara entre bloques**, solo híbrido vs. clásico dentro de cada bloque: los bloques se midieron en días
  distintos, con potencia de reposo distinta (2574 vs. 2740 mW) y con distinta tasa de muestreo del INA219 (646 vs. 1991 muestras/s).
- **Tiempo: el bus explica la diferencia.** El procesamiento del cliente y el Finished (etapa 3) dura ~1,75–1,86 s en todos los
  casos; lo que crece con el híbrido son las etapas de transmisión: ClientHello + proceso del servidor (26 → 270 ms a 100 kbit/s;
  8 → 78 ms a 400 kbit/s) y envío de la respuesta del servidor (170 → 389 ms; 48 → 110 ms). El cómputo del servidor es ~1,5–1,8 ms.
  Por eso el sobrecosto del híbrido baja de +25,5 % a +7,8 % al pasar a 400 kbit/s.
- **Correlación tiempo-energía (Spearman, por grupo y bloque): ρ entre −0,04 y 0,21.** Dentro de un bloque, la variación de la
  energía no la explica el tiempo del handshake (el tiempo casi no varía: CV < 0,1 %).
- **Latencia de un mensaje** (RTT): diferencias < 3,2 % entre grupos; depende del tamaño del mensaje y del modo de bus, no del intercambio.
- Controles: 720/720 válidas, grupo detectado = pedido, ClientHello constante por grupo, ≥ 1246 muestras de potencia por
  handshake, temperatura 52,5–56,9 °C, throttling 0x0, deriva del reposo 7–11 mW (< 0,5 %).
