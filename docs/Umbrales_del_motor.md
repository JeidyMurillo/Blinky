# Umbrales del motor de decisión (SCRUM-32)

**Fuente única:** `app/config/settings.yaml`, sección `thresholds:`.

Los valores por defecto se replican en `app/src/fatiga_visual/core/config.py`
(`DEFAULTS["thresholds"]`) para que la aplicación y las pruebas funcionen aunque
no exista el archivo YAML. `core/config.py` y `settings.yaml` deben mantenerse
iguales; hay una prueba que lo verifica.

En `decision/rules.py`, `decision/engine.py` y la interfaz **no queda ningún
umbral numérico fijo**: todos reciben el mapping devuelto por
`Settings.section("thresholds")`. Si se omite el YAML, se usa el espejo de
`DEFAULTS`. Para cambiar un umbral se edita `settings.yaml`, no el código.

## Umbrales

| Umbral | Valor | Fuente o justificación |
|---|---:|---|
| `min_confidence` | `0.35` | Confianza mínima de landmarks. MediaPipe suele dar >0.5 con rostro visible; 0.35 tolera luz baja y gafas. Lo consumen visión y motor (antes estaba duplicado en `vision:`). |
| `blink_rate_low` | `15` bpm | Frecuencia normal frente a pantalla ≈15–20 bpm. Sustituye el `10` del primer prototipo, que avisaba demasiado tarde. |
| `blink_warmup_seconds` | `20` s | Gracia al arrancar: `BlinkMetrics` necesita 10 s de ventana mínima y los primeros valores son inestables. |
| `perclos_high` | `0.15` | 15 % del tiempo con ojos cerrados en la ventana de 60 s; referencia habitual de fatiga en estudios PERCLOS. |
| `perclos_min_observation_seconds` | `60` | Tiempo mínimo observado antes de avisar por PERCLOS. El denominador crece desde 0, así que en sesiones cortas un solo cierre parecía fatiga; los cierres largos sí pueden avisar antes. |
| `long_closures_per_minute` | `3` | Cierres de >1,5 s por minuto (ver `vision.long_closure_seconds`); 3 o más sugiere microsueño. |
| `continuous_minutes` | `20` min | Regla 20-20-20 de la American Academy of Ophthalmology. La alerta se emite una vez por periodo continuo y se rearma solo cuando `breaks_taken` aumenta (pausa válida). |
| `cooldown_seconds` | `300` s | 5 min sin repetir la misma recomendación. Antes era un literal en `DecisionEngine` y generaba avisos redundantes. |
| `lux_min` | `300` lux | Mínimo para lectura en interiores (guías de iluminación de oficina / EN 12464-1). |
| `lux_max` | `1000` lux | Máximo antes de considerar deslumbramiento sobre la pantalla. |
| `temperature_min` | `18` °C | Extremo inferior de confort de ASHRAE 55 / ISO 7730 para oficinas. |
| `temperature_max` | `26` °C | Extremo superior de confort de ASHRAE 55 / ISO 7730 para oficinas. |
| `humidity_min` | `30` %HR | Por debajo aumenta la sequedad ocular (ASHRAE recomienda 40–60 %; 30 da tolerancia en aulas). |
| `humidity_max` | `60` %HR | Por encima aparece bochorno y riesgo de moho (ASHRAE 55). |

## Consumidores

| Módulo | Umbrales que usa |
|---|---|
| `decision/rules.py` | Todos los anteriores salvo `cooldown_seconds` |
| `decision/engine.py` | `cooldown_seconds` + pasa el mapping completo a las reglas |
| `runtime/pipeline.py` | `continuous_minutes`, `min_confidence` (filtro de muestras de visión) |
| `runtime/simulated.py` | `continuous_minutes` |
| `ui/state.py`, `ui/panels/blink_panel.py` | `continuous_minutes`, `perclos_high`, `perclos_min_observation_seconds`, `long_closures_per_minute` (solo presentación) |

## Alcance

Este documento cubre los umbrales del **motor de decisión**. El umbral EAR de
detección (`vision.ear_threshold`) y los parámetros de calibración
(`calibration_ratio`, `calibration_floor`, `calibration_ceiling`) pertenecen a
**SCRUM-23** y se ajustan por usuario en `app/blinky_calibration.json`. Son una
capa anterior: producen la tasa de parpadeo que luego consume este motor.

## Verificación

```powershell
cd app
python -m unittest discover -s tests
```

Incluye pruebas que comprueban que el YAML y `DEFAULTS` coinciden, que cada
umbral del YAML tiene comentario de justificación, que no quedan `thresholds.get(..., número)`
en las reglas y que cambiar un valor de configuración cambia el comportamiento
de las reglas y del cooldown.
