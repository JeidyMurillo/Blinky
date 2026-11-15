// Conexión WiFi y publicación MQTT.
//
// Contrato: contracts/topics.md
// - fatiga/ambient: JSON cada 2 s, QoS 0, retain false.
// - fatiga/ambient/status: online/offline, QoS 1, retain true.
// - LWT: si el ESP32 se cae, el broker publica offline por él.
//
// networkBegin() inicia WiFi y configura el broker; networkLoop() mantiene la
// conexión sin bloquear el resto del firmware.

#pragma once

#include "sensors.h"

void networkBegin();
void networkLoop();

// Publica {"lux":..., "temperature":..., "humidity":..., "seq":...}
// en MQTT_TOPIC_AMBIENT.
bool publishAmbient(const SensorReading &reading);
