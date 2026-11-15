# Blinky - Monitor de fatiga ocular

Aplicación de escritorio que mide la fatiga visual usando una webcam y un
sensor ambiental ESP32. Muestra tres interfaces: Monitoreo, Estadísticas y
Recomendaciones.

## Estructura

```text
fatiga-visual/
  contracts/                    contrato MQTT (se escribe primero)
    topics.md                   tópicos, QoS, retain, LWT y flujo
    ambient.schema.json         JSON Schema del payload del ESP32
  app/
    config/settings.yaml        umbrales, cámara, MQTT, runtime y storage
    requirements.txt
    blinky.db                   SQLite (se crea al arrancar; no se versiona)
    src/fatiga_visual/
      main.py                   arma el grafo y arranca
      core/                     modelos, EventBus, settings
      vision/                   cámara, EAR, landmarks, parpadeo
      exposure/                 presencia, tiempo de sesión, pausas
      ambient/                  MQTT -> AmbientReading
      decision/                 reglas + motor
      runtime/                  ← NUEVO: conecta todas las piezas
        pipeline.py             fuente real: cámara + visión + motor
        simulated.py            fuente demo: mismos eventos, sin hardware
      storage/                  ← NUEVO: históricos e informes
        database.py             SQLite, esquema y 2 vistas
        repository.py           guardar muestras / consultar series
      ui/
        theme.py                tokens, DPI, iconos
        state.py                estado compartido (thread-safe)
        main_window.py          barra y navegación
        views/                  las 3 interfaces
        widgets/                cámara, métricas, alertas
        panels/                 panel ocular y sensor ambiental
    tests/
  firmware/esp32/               PlatformIO: BH1750 + SHT31 + MQTT + LWT
  broker/                       configuración del broker MQTT
  docs/
    Acta_de_Constitución_de_Proyecto.md   objetivos, alcance, riesgos
    Historias_de_Usuario.md     épicas, 25 historias y backlog MoSCoW
    Cronograma del proyecto.md  actividades, duraciones y ruta crítica
    edt.md                      estructura de desglose del trabajo
    architecture.md             módulos, EventBus y flujo de datos
    design/                     referencia visual (PNG y React)
  tools/
    nodo_simulado.py            ← NUEVO: publica MQTT falso
    mqtt_latency_test.py        latencia corregida (paho 2.x)
    blink_eval.py               evaluación de EAR
```

## Ejecutar

```powershell
cd fatiga-visual\app
pip install -r requirements.txt
cd src
python -m fatiga_visual.main
```

La ventana mide 1512x1000 px físicos y se centra en el área de trabajo.
En Windows se ajusta el DPI al importar `ui/theme.py`.

## Cámara

- OpenCV abre el dispositivo `camera.index` (0 por defecto) con DirectShow.
- La captura corre en un hilo propio en `vision/camera.py`; la UI solo lee
  el último fotograma con `after()`, nunca bloquea el hilo de Tk.
- Al cerrar la ventana o apagar la cámara se libera el dispositivo.

## Datos y flujo

```text
Cámara -> vision -> BlinkMetrics --------\
Cámara -> presence -> ExposureMetrics ----> runtime/pipeline.py
ESP32  -> MQTT   -> AmbientReading -----/          |
                                                   v
                                        decision/engine.py -> Recommendation
                                                   |              |
                                                   v              v
                                             EventBus           UI (poll)
                                                   |
                                                   v
                                       storage/repository.py -> SQLite
```

- Los módulos publican en `EventBus` (`blink.metrics`, `blink.event`,
  `vision.status`, `exposure.metrics`, `ambient.reading`, `ambient.status`,
  `decision.recommendation`).
- `runtime/` conecta cámara, visión, exposición y motor. La UI solo consume.
- `ui/state.py` concentra el estado de las tres vistas y encola los eventos;
  `MainWindow` los consume en el hilo de Tk cada 100 ms.
- `storage/` guarda muestras y expone series diarias para estadísticas.

## Fuente de datos

Se elige en `app/config/settings.yaml`:

```yaml
runtime:
  source: real        # ui | simulated | real
```

- `ui`: simulación dentro de `AppState` (comportamiento anterior).
- `simulated`: `runtime/simulated.py` publica los mismos eventos sin hardware.
- `real`: `runtime/pipeline.py` usa la cámara compartida con la UI. Si
  MediaPipe o el modelo no están disponibles, cae automáticamente en
  simulación y avisa por consola.

Activa la cámara desde la interfaz de Monitoreo para que el pipeline real
reciba fotogramas. `runtime.auto_start_camera: true` permite que el pipeline
abra la cámara por su cuenta.

El contador de sesión arranca en cero en cada ejecución, sin importar la fuente
de datos (`session.initial_*`).

## Detección de parpadeos

El detector real vive en `app/src/fatiga_visual/vision/`:

| Archivo | Función |
| --- | --- |
| `camera.py` | Captura la webcam en un hilo y comparte el último frame RGB |
| `face_landmarks.py` | MediaPipe Face Landmarker + blendshapes `eyeBlink` |
| `ear.py` | EAR por ojo y EAR medio |
| `smoothing.py` | Filtro EMA para reducir el temblor del EAR |
| `calibration.py` | Umbral personalizado por usuario y luz |
| `blink_detector.py` | Histéresis, duración, parpadeo y cierre largo |
| `blink_metrics.py` | Tasa, intervalos, PERCLOS y cierres largos |

Flujo:

```text
webcam -> MediaPipe -> 478 landmarks -> EAR -> EMA -> calibración
       -> BlinkDetector -> BlinkMetrics -> EventBus/UI/SQLite -> DecisionEngine
```

`BlinkDetector` no cuenta cualquier bajada del EAR:

- exige `min_closed_frames` frames cerrados;
- usa histéresis (`ear_threshold` para cerrar, `+ reopen_margin` para abrir);
- mide la duración del cierre;
- si supera `max_blink_duration_ms` lo emite como `long_closure` (fatiga);
- opcionalmente combina el EAR con la blendshape `eyeBlink` de MediaPipe.

La calibración es perezosa: empieza con el primer fotograma que contiene un
rostro, no al abrir la aplicación. Dura `calibration_seconds`, pide mirar al
frente y usa el percentil 75 del EAR con los ojos abiertos, descartando la cola
de parpadeos. El umbral queda en `p75 * calibration_ratio` (0.60 por defecto),
con `calibration_floor` y `calibration_ceiling` como límites de seguridad. Mientras
calibra no se cuentan parpadeos ni PERCLOS, para que el arranque no infle las
métricas. El resultado se guarda en `app/blinky_calibration.json` (ignorado por
Git) y se recalcula al inicio de cada sesión para adaptarse a la iluminación.
Las lecturas de EAR imposibles (>0.5, típicas de un rostro cortado o girado) se
descartan para que no inflen el umbral ni generen falsos parpadeos.

### Instalación de MediaPipe

MediaPipe 1.2 usa la API *Tasks* y un modelo `.task`. El modelo se descarga
automáticamente la primera vez en la caché del usuario:

```text
%LOCALAPPDATA%\Blinky\models\face_landmarker.task
```

Para instalar sin duplicar OpenCV en Windows:

```powershell
pip install --no-deps mediapipe==1.2.3
pip install absl-py flatbuffers matplotlib sounddevice
```

También puedes indicar otro modelo con `vision.model_path` o con la variable
`BLINKY_FACE_MODEL`.

### Métricas de fatiga

`BlinkMetrics` incluye:

- `blink_rate`: parpadeos por minuto en la ventana móvil.
- `mean_blink_duration_ms` y `last_blink_duration_ms`.
- `inter_blink_seconds`: intervalo medio entre parpadeos.
- `perclos`: fracción del tiempo con los ojos cerrados.
- `long_closures`: cierres prolongados dentro de la ventana.
- `calibration_progress` y `confidence`.

La regla `prolonged_eye_closure` alerta cuando `perclos` o los cierres largos
superan los umbrales de `settings.yaml`.

## MQTT

El contrato completo está en [`contracts/topics.md`](contracts/topics.md) y el
JSON se valida con [`contracts/ambient.schema.json`](contracts/ambient.schema.json).
El firmware publica cada 2 s:

```json
{"lux": 420.5, "temperature": 23.4, "humidity": 48.0, "seq": 128}
```

Tópicos:

| Tópico | QoS | Retain | Uso |
| --- | --- | --- | --- |
| `fatiga/ambient` | 0 | false | telemetría |
| `fatiga/ambient/status` | 1 | true | online/offline + LWT |

Activa la conexión en `app/config/settings.yaml`:

```yaml
mqtt:
  enabled: true
  host: 127.0.0.1
  port: 1883
  qos: 0
  topics:
    ambient: fatiga/ambient
    status: fatiga/ambient/status
```

Para probar sin ESP32:

```powershell
python tools\nodo_simulado.py --scenario normal --interval 2
python tools\mqtt_latency_test.py --topic fatiga/test --count 20
```

## Base de datos

`storage/database.py` crea `app/blinky.db` con las tablas `sessions`,
`blink_samples`, `ambient_samples`, `exposure_samples` y `recommendations`.
Incluye dos vistas para informes: `v_daily_blinks` y `v_daily_ambient`.
Se puede desactivar o cambiar la ruta con:

```yaml
storage:
  enabled: true
  path: ""            # vacío = app/blinky.db
  retention_days: 90
```

## Pruebas

```powershell
cd fatiga-visual\app
python -m unittest discover -s tests
```

Las pruebas cubren EAR por ojo, histéresis y duración de parpadeos, calibración,
PERCLOS, cierres largos, pipeline real con detector simulado, backend de
MediaPipe, reglas, bus de eventos, configuración, contrato ambiental,
almacenamiento y runtime simulado.

## Documentación

| Documento | Contenido |
| --- | --- |
| [`docs/Acta_de_Constitución_de_Proyecto.md`](docs/Acta_de_Constitución_de_Proyecto.md) | Objetivos, criterios de éxito, alcance, interesados y matriz de riesgos con mitigación y contingencia. |
| [`docs/Historias_de_Usuario.md`](docs/Historias_de_Usuario.md) | Stakeholders, entrevista, 6 épicas, 25 historias con criterios Dado/Cuando/Entonces y backlog MoSCoW. |
| [`docs/Cronograma del proyecto.md`](docs/Cronograma%20del%20proyecto.md) | Actividades con códigos de la EDT, duraciones, dependencias y ruta crítica. |
| [`docs/edt.md`](docs/edt.md) | Estructura de desglose del trabajo y numeración canónica de los paquetes. |
| [`docs/architecture.md`](docs/architecture.md) | Módulos, responsabilidades, eventos internos y flujo de datos. |
| [`contracts/topics.md`](contracts/topics.md) | Contrato MQTT: tópicos, QoS, retain, LWT y esquema del payload. |
