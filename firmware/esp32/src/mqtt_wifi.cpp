// Implementación WiFi + MQTT.
//
// El JSON debe coincidir con contracts/ambient.schema.json y con
// ambient/mqtt_client.py del proyecto Python:
//   {"lux": 420, "temperature": 23.4, "humidity": 48, "seq": 128}
//
// LWT registrado en el CONNECT:
//   fatiga/ambient/status -> "offline", QoS 1, retain true.

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

#include "config.h"
#include "mqtt_wifi.h"

static WiFiClient wifiClient;
static PubSubClient mqtt(wifiClient);
static uint32_t sequence = 0;
static unsigned long lastWifiAttempt = 0;
static unsigned long lastMqttAttempt = 0;

static void connectWifi() {
    if (WiFi.status() == WL_CONNECTED) {
        return;
    }
    unsigned long now = millis();
    if (now - lastWifiAttempt < MQTT_RECONNECT_INTERVAL_MS) {
        return;
    }
    lastWifiAttempt = now;
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.println("Conectando WiFi...");
}

static bool connectMqtt() {
    if (mqtt.connected()) {
        return true;
    }
    unsigned long now = millis();
    if (now - lastMqttAttempt < MQTT_RECONNECT_INTERVAL_MS) {
        return false;
    }
    lastMqttAttempt = now;

    Serial.print("Conectando MQTT...");
    bool connected = mqtt.connect(
        MQTT_CLIENT_ID,
        nullptr,
        nullptr,
        MQTT_TOPIC_STATUS,
        MQTT_QOS_STATUS,
        MQTT_RETAIN_STATUS,
        MQTT_STATUS_OFFLINE
    );

    if (!connected) {
        Serial.print("error ");
        Serial.println(mqtt.state());
        return false;
    }

    Serial.println("ok");
    mqtt.publish(MQTT_TOPIC_STATUS, MQTT_STATUS_ONLINE, MQTT_RETAIN_STATUS);
    return true;
}

void networkBegin() {
    // Permite el primer intento inmediato aunque millis() aún sea pequeño.
    lastWifiAttempt = millis() - MQTT_RECONNECT_INTERVAL_MS;
    lastMqttAttempt = millis() - MQTT_RECONNECT_INTERVAL_MS;
    connectWifi();
    mqtt.setServer(MQTT_HOST, MQTT_PORT);
    mqtt.setKeepAlive(MQTT_KEEPALIVE_SECONDS);
    mqtt.setBufferSize(256);
}

void networkLoop() {
    connectWifi();
    if (WiFi.status() == WL_CONNECTED) {
        connectMqtt();
    }
    mqtt.loop();
}

bool publishAmbient(const SensorReading &reading) {
    if (!reading.valid || !mqtt.connected()) {
        return false;
    }

    JsonDocument doc;
    doc["lux"] = reading.lux;
    doc["temperature"] = reading.temperature;
    doc["humidity"] = reading.humidity;
    doc["seq"] = sequence++;

    char payload[160];
    size_t length = serializeJson(doc, payload, sizeof(payload));
    return mqtt.publish(
        MQTT_TOPIC_AMBIENT,
        reinterpret_cast<const uint8_t *>(payload),
        length,
        MQTT_RETAIN_AMBIENT
    );
}
