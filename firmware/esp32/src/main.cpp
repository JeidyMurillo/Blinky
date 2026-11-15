// Punto de entrada del firmware del ESP32.
//
// Contrato: contracts/topics.md
// Flujo:
//   1. Inicializar serial, sensores (BH1750 + SHT31) y red.
//   2. Cada PUBLISH_INTERVAL_MS leer y publicar en MQTT_TOPIC_AMBIENT.
//   3. Mantener WiFi/MQTT y el estado online/offline con LWT.
//
// Qué completar:
// - Añadir LED de estado y botón de reconfiguración si hace falta.
// - Firmar el mensaje o usar TLS si el prototipo lo requiere.

#include <Arduino.h>

#include "config.h"
#include "mqtt_wifi.h"
#include "sensors.h"

static unsigned long lastPublish = 0;

void setup() {
    Serial.begin(115200);
    delay(200);
    Serial.println("Blinky sensor ambiental");

    sensorsBegin();
    networkBegin();
}

void loop() {
    networkLoop();

    if (millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
        lastPublish = millis();
        SensorReading reading;
        if (readSensors(reading)) {
            publishAmbient(reading);
        } else {
            Serial.println("Lectura inválida, se omite");
        }
    }

    delay(10);
}
