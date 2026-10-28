# Calibración INA219 — Semana 4

| Condición | INA219 (mA) | Multímetro V_shunt/0.1Ω (mA) | Error (%) | INA219 (V) | Multímetro (V) |
|---|---|---|---|---|---|
| Reposo | 468.1 | 508.0 | −7.85% | 5.260 | 5.30 |
| stress-ng 2 núcleos | 829.4 | 842.0 | −1.50% | 5.116 | 5.19 |
| stress-ng 4 núcleos | 1110.7 | 1179.5 | −5.83% | 5.027 | 5.12 |

## Análisis

- **Error sistemático:** el INA219 subestima la corriente en ~5% en promedio.
- **Error en reposo:** −7.85% (ligeramente superior al 5% recomendado).
- **Error en carga media:** −1.50% (aceptable).
- **Error en carga máxima:** −5.83% (cerca del límite).

## Conclusión

El error es **sistemático** (el INA219 siempre subestima), por lo que **afecta igual al clásico y al híbrido**. La comparación entre ambos sigue siendo válida.

Posibles causas:
- Tolerancia de la resistencia shunt (±1-5%).
- Precisión del multímetro (±1-2%).
- Caída de voltaje en cables.

## Recomendación

Aceptar el error y continuar. Si se requiere mayor precisión, calibrar el INA219 por software con un factor de corrección de ~1.05 (multiplicar las lecturas por 1.05).
