// Implementación de los sensores (BH1750 + SHT31).
//
// Ambos comparten el bus I2C de config.h. El SHT31 sustituye al DHT22 del
// prototipo anterior: mismas variables de salida, distinto driver.

#include <Arduino.h>
#include <Wire.h>
#include <BH1750.h>
#include <Adafruit_SHT31.h>

#include "config.h"
#include "sensors.h"

static BH1750 lightMeter;
static Adafruit_SHT31 sht31;

void sensorsBegin() {
    Wire.begin(I2C_SDA, I2C_SCL);
    Wire.setClock(I2C_CLOCK_HZ);

    if (!lightMeter.begin(BH1750::CONTINUOUS_HIGH_RES_MODE, BH1750_ADDR)) {
        Serial.println("BH1750 no responde en el bus I2C");
    }
    if (!sht31.begin(SHT31_ADDR)) {
        Serial.println("SHT31 no responde en el bus I2C");
    }
}

bool readSensors(SensorReading &reading) {
    reading.valid = false;

    float lux = lightMeter.readLightLevel();
    float temperature = sht31.readTemperature();
    float humidity = sht31.readHumidity();

    if (isnan(lux) || isnan(temperature) || isnan(humidity)) {
        return false;
    }

    // Rangos del contrato: evita publicar valores fuera de rango.
    if (lux < 0.0f || lux > 200000.0f) {
        return false;
    }
    if (temperature < -40.0f || temperature > 85.0f) {
        return false;
    }
    if (humidity < 0.0f || humidity > 100.0f) {
        return false;
    }

    reading.lux = lux;
    reading.temperature = temperature;
    reading.humidity = humidity;
    reading.valid = true;
    return true;
}
