#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SHT31.h>
#include "config.h"
#include "mqtt_wifi.h"
#include "sensors.h"

#define PIN_SDA 8
#define PIN_SCL 9
#define BH1750_ADDR 0x23
#define SHT_ADDR 0x45

Adafruit_SHT31 sht = Adafruit_SHT31(&Wire);
bool shtOk = false;
bool bhOk = false;

void checkBusIdle() {
  pinMode(PIN_SDA, INPUT_PULLUP);
  pinMode(PIN_SCL, INPUT_PULLUP);
  delay(10);
  Serial.printf("Reposo: SDA=%d SCL=%d (ambos deben ser 1)\n",
                digitalRead(PIN_SDA), digitalRead(PIN_SCL));
}

void scanI2C() {
  Serial.println("Escaneando I2C...");
  int n = 0;
  for (uint8_t a = 1; a < 127; a++) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      Serial.printf("  Dispositivo en 0x%02X\n", a);
      n++;
    }
  }
  if (n == 0) Serial.println("  Ninguno encontrado");
}

bool bhInit() {
  Wire.beginTransmission(BH1750_ADDR);
  Wire.write(0x01);
  if (Wire.endTransmission() != 0) return false;
  delay(10);
  Wire.beginTransmission(BH1750_ADDR);
  Wire.write(0x10);
  if (Wire.endTransmission() != 0) return false;
  delay(180);
  return true;
}

bool bhRead(float &lux) {
  if (Wire.requestFrom((uint8_t)BH1750_ADDR, (uint8_t)2) != 2) return false;
  uint8_t hi = Wire.read();
  uint8_t lo = Wire.read();
  uint16_t raw = (hi << 8) | lo;
  if (raw == 0xFFFF) return false;
  lux = raw / 1.2;
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  checkBusIdle();
  Wire.begin(PIN_SDA, PIN_SCL);
  Wire.setClock(100000);
  scanI2C();
  bhOk = bhInit();
  shtOk = sht.begin(SHT_ADDR);

  Serial.println(bhOk ? "BH1750 OK" : "BH1750 NO responde");
  Serial.println(shtOk ? "SHT3x OK" : "SHT3x NO responde");

  networkBegin();
}

static unsigned long lastPublish = 0;

void loop() {
  networkLoop();

  if (millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    lastPublish = millis();

    float lux = 0;
    float t = 0;
    float h = 0;
    bool ok = false;

    if (bhOk && bhRead(lux)) {
      ok = true;
    }
    if (shtOk) {
      t = sht.readTemperature();
      h = sht.readHumidity();
      if (!isnan(t) && !isnan(h)) {
        ok = true;
      }
    }

    if (ok) {
      SensorReading reading;
      reading.lux = lux;
      reading.temperature = t;
      reading.humidity = h;
      reading.valid = true;
      publishAmbient(reading);
    } else {
      Serial.println("Lectura invalida, se omite");
    }
  }

  delay(10);
}
