# Contrato MQTT - Blinky

Este documento es la fuente de verdad del enlace entre el ESP32, el broker y la
aplicación. Se escribe antes que el firmware y que el cliente Python: si algo no
coincide aquí, no se implementa.

- Versión del contrato: **1.0**
- Broker: Mosquitto 2.x, MQTT 3.1.1
- JSON ambiental: [`ambient.schema.json`](./ambient.schema.json)
- Eventos internos de exposición: [`exposure.schema.json`](./exposure.schema.json)
- Codificación: UTF-8
- Zona horaria: la app sella la hora de recepción. El ESP32 no necesita reloj.

## 1. Tópicos

| Tópico | Dirección | QoS | Retain | Frecuencia | Uso |
| --- | --- | --- | --- | --- | --- |
| `fatiga/ambient` | ESP32 -> app | 0 | `false` | cada 2 s | Lectura ambiental |
| `fatiga/ambient/status` | ESP32 -> app | 1 | `true` | al conectar / LWT | Estado del nodo |
| `fatiga/blink` | app -> ESP32 | 0 | `false` | reservado | Futuras órdenes a la app |
| `fatiga/test` | herramientas | 0 | `false` | a demanda | Latencia y diagnóstico |

Reglas:

1. **No se renombran tópicos existentes.** `fatiga/ambient` y `fatiga/blink` ya
   están en `settings.yaml` y en el firmware.
2. `fatiga/ambient` **no usa retain**. Un mensaje retenido haría parecer
   reciente una lectura vieja al reconectar la app.
3. `fatiga/ambient/status` **sí usa retain** para que la app conozca el último
   estado del nodo aunque el ESP32 esté apagado.
4. El QoS de telemetría es 0: una lectura perdida se recupera en el siguiente
   ciclo de 2 s. El estado usa QoS 1 porque interesa que llegue.
5. Cada dispositivo debe usar un `client_id` único. El prototipo usa
   `blinky-esp32`.

## 2. Payload ambiental

```json
{"lux": 420.5, "temperature": 23.4, "humidity": 48.0, "seq": 128}
```

Campos obligatorios:

| Campo | Tipo | Rango | Unidad |
| --- | --- | --- | --- |
| `lux` | número | 0 - 200000 | lux |
| `temperature` | número | -40 - 85 | °C |
| `humidity` | número | 0 - 100 | % HR |

Campos opcionales:

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `seq` | entero >= 0 | Contador del firmware; sirve para detectar pérdidas |
| `timestamp` | entero >= 0 | Época en milisegundos, solo si el nodo tiene hora |
| `firmware` | string | Versión del firmware, por ejemplo `"1.0.0"` |

El JSON es estricto: no se admiten campos desconocidos. La validación completa
está en `ambient.schema.json` y la replica `ambient/mqtt_client.py`.

## 3. Last Will and Testament (LWT)

Al conectarse, el ESP32 registra este testamento:

```text
topic:   fatiga/ambient/status
payload: offline
qos:     1
retain:  true
```

Después de un `CONNACK` correcto publica:

```text
topic:   fatiga/ambient/status
payload: online
qos:     1
retain:  true
```

Si el ESP32 pierde la conexión sin `DISCONNECT` limpio, el broker publica
`offline` por él. Así la app distingue "nodo apagado" de "nodo sin datos".

La app también considera desconectado el sensor si pasan **15 segundos** sin
una lectura en `fatiga/ambient`, aunque el último estado sea `online`.

## 4. Flujo completo

```text
BH1750 + SHT31
      |
      v
ESP32: JSON cada 2 s -> fatiga/ambient        (QoS 0, retain false)
ESP32: online/offline -> fatiga/ambient/status (QoS 1, retain true)
      |
      v
Mosquitto 1883
      |
      v
app: ambient/mqtt_client.py -> AmbientReading -> EventBus
      |                                          |
      v                                          v
decision/engine.py                          storage/repository.py
      |                                          |
      v                                          v
Recommendation -> UI                        SQLite (histórico)
```

## 5. Eventos internos (no son tópicos MQTT)

El `EventBus` de la aplicación usa nombres con puntos que **no viajan por el
broker**. Se llaman eventos para distinguirlos de los tópicos MQTT y no deben
publicarse ni suscribirse en Mosquitto.

| Evento | Productor | Consumidor | Contenido |
| --- | --- | --- | --- |
| `blink.metrics` | `vision/blink_metrics.py` | UI, decisión, storage | Tasa, PERCLOS, cierres largos y confianza |
| `blink.event` | `vision/blink_detector.py` | UI, decisión | Parpadeo individual o cierre prolongado |
| `vision.status` | `vision/` y `runtime/` | UI | Estado de cámara, rostro y calibración |
| `vision.landmarks` | `runtime/pipeline.py` | UI | `FaceOverlay` con puntos normalizados para dibujar sobre el video (sin frames) |
| `exposure.metrics` | `exposure/`, `runtime/` | UI, decisión, storage | Sesión, tiempo continuo, pausas y presencia (`exposure.schema.json`) |
| `exposure.break` | `exposure/breaks.py`, `runtime/` | UI, decisión | `BreakEvent` con `started` / `finished` y duración de la pausa válida (`exposure.schema.json`) |
| `exposure.presence` | `exposure/presence.py`, `runtime/` | UI, decisión, storage | Cambio presente/ausente con confianza (`exposure.schema.json`) |
| `ambient.reading` | `ambient/mqtt_client.py` | UI, decisión, storage | `AmbientReading` ya validado |
| `ambient.status` | `ambient/mqtt_client.py` | UI | Nodo online/offline o datos vencidos |
| `decision.recommendation` | `decision/engine.py` | UI, storage | Recomendación y su motivo |
| `decision.recommendation.resolved` | `decision/engine.py` | UI | `RecommendationResolved` con id y hora al normalizarse la condición |

Regla: si un dato debe cruzar de un proceso o equipo a otro, va por MQTT y se
documenta en la sección 1. Si solo circula dentro de la app, va por `EventBus`
y se documenta en esta tabla.

`exposure/bus.py` construye el payload de ambos eventos, lo valida contra
`exposure.schema.json` y solo entonces lo publica. Los nombres de los temas se
toman de `bus.topics` en `settings.yaml`; los valores por defecto son los de
esta tabla.

## 6. Compatibilidad y cambios

- Un campo nuevo obligatorio, un rango distinto o un tópico renombrado es un
  cambio **incompatible**: subir la versión del contrato y actualizar firmware,
  cliente Python y esquema en el mismo commit.
- Añadir un campo opcional también requiere actualizar el esquema y el parser.
- Las herramientas de prueba (`tools/nodo_simulado.py`,
  `tools/mqtt_latency_test.py`) deben respetar este contrato.
- Si un mensaje no valida, el cliente lo descarta y sigue escuchando. Nunca
  rompe la app.

## 7. Configuración de referencia

`app/config/settings.yaml`:

```yaml
mqtt:
  enabled: true
  host: 127.0.0.1
  port: 1883
  keepalive: 30
  qos: 0
  topics:
    ambient: fatiga/ambient
    status: fatiga/ambient/status
    blink: fatiga/blink
```

`firmware/esp32/src/config.h` debe contener exactamente los mismos tópicos.
