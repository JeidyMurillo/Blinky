# Pruebas de calibración EAR (SCRUM-23)

Objetivo: demostrar que el umbral aprendido **mejora la exactitud frente al
umbral fijo `0.21`**, usando la cámara del PC. No se necesita ESP32 ni broker.

## Herramientas

- `tools/record_ear.py`: graba EAR, etiqueta los cierres de ojos y calcula el
  umbral calibrado con la misma `EarCalibration` de la aplicación.
- `tools/blink_eval.py`: evalúa el CSV y compara fijo vs calibrado sobre la
  **misma señal** (fotogramas y eventos de parpadeo).

## Procedimiento

Desde la raíz del repositorio:

```powershell
cd "C:\Users\Karol\Documents\Proyecto Integrador\fatiga-visual"
python tools\record_ear.py --output tools\data\sesion1.csv
python tools\blink_eval.py tools\data\sesion1.csv
```

Durante la grabación (40 s por defecto):

1. **Calibración (4 s):** mirar al frente sin parpadear. La ventana muestra
   `CALIBRANDO`. Al terminar imprime el umbral aprendido, p. ej.
   `Umbral calibrado: 0.1873 (62 muestras)`.
2. **Etiquetado:** cada vez que cierres los ojos, pulsa **ESPACIO** en ese mismo
   momento. La tecla marca 0,3 s como `closed_real=1`. Repite 10 veces.
3. **Fin:** pulsa **ENTER** o **Q**. Se guarda el CSV en `tools\data\`.

Repite la sesión 3 veces, por ejemplo:

| Sesión | Condición |
|---|---|
| `sesion1.csv` | luz normal |
| `sesion2.csv` | luz baja / contraluz |
| `sesion3.csv` | gafas o distancia distinta a la cámara |

Los CSV quedan en `tools\data\`, ignorados por Git. Para la evidencia de Jira
se adjunta la salida del evaluador y el valor calibrado, no el JSON de
calibración (`app/blinky_calibration.json` también está ignorado).

## Cómo se mide

El evaluador descarta las filas de calibración y calcula, para cada umbral:

- **Fotograma:** exactitud, precisión y recall comparando `ear < umbral` contra
  `closed_real`.
- **Parpadeo:** empareja cada cierre real con el detectado dentro de 0,6 s y
 reporta TP/FP/FN y exactitud.

Al final imprime `MEJORA: SÍ` solo si el umbral calibrado es **≥** el fijo en
ambas medidas.

## Criterio para cerrar SCRUM-23

- El umbral aprendido se aplica automáticamente: el grabador lo usa en cuanto
  termina la calibración y el pipeline de la app hace lo mismo.
- `MEJORA: SÍ` en las 3 sesiones.
- Si además la exactitud calibrada es ≥85 %, sirve como evidencia para SCRUM-44.

Si aparece `AVISO: la calibración no terminó`, repite con el rostro bien visible
y sin taparte los ojos durante los primeros 4 segundos. Si la cámara está ocupada,
cierra la aplicación Blinky antes de grabar.
