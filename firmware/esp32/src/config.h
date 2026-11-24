// Configuración del ESP32.
// Copia este archivo a config.local.h para credenciales reales o usa build_flags.
//
// Contrato: contracts/topics.md
// - WIFI_SSID / WIFI_PASSWORD con los datos de tu red.
// - MQTT_HOST con la IP de la computadora que corre el broker.
// - Pines I2C compartidos por BH1750 y SHT31.

#pragma once

#if __has_include("config.local.h")
#include "config.local.h"
#endif

#ifndef WIFI_SSID
#define WIFI_SSID "TU_SSID"
#endif
#ifndef WIFI_PASSWORD
#define WIFI_PASSWORD "TU_PASSWORD"
#endif
#ifndef MQTT_HOST
#define MQTT_HOST "192.168.1.10"
#endif
#define MQTT_PORT 1883
#define MQTT_CLIENT_ID "blinky-esp32"
#define MQTT_KEEPALIVE_SECONDS 30
#define MQTT_RECONNECT_INTERVAL_MS 5000

// Telemetría ambiental: QoS 0, sin retain.
#define MQTT_TOPIC_AMBIENT "fatiga/ambient"
#define MQTT_QOS_AMBIENT 0
#define MQTT_RETAIN_AMBIENT false

// Estado online/offline y Last Will and Testament: QoS 1, con retain.
#define MQTT_TOPIC_STATUS "fatiga/ambient/status"
#define MQTT_QOS_STATUS 1
#define MQTT_RETAIN_STATUS true
#define MQTT_STATUS_ONLINE "online"
#define MQTT_STATUS_OFFLINE "offline"

// Bus I2C compartido: BH1750 (luz) + SHT31 (temperatura y humedad).
#define I2C_SDA 21
#define I2C_SCL 22
#define I2C_CLOCK_HZ 100000
#define BH1750_ADDR 0x23
#define SHT31_ADDR 0x44

// Frecuencia de publicación.
#define PUBLISH_INTERVAL_MS 2000
