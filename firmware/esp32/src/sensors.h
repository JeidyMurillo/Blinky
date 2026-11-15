// Lectura de sensores ambientales (BH1750 + SHT31).
//
// Contrato: contratos/topics.md, campos lux/temperature/humidity.
// - BH1750 por I2C entrega lux.
// - SHT31 por I2C entrega temperatura y humedad.
//
// Devuelve false si algún valor es inválido para no publicar basura.

#pragma once

struct SensorReading {
    float lux;
    float temperature;
    float humidity;
    bool valid;
};

void sensorsBegin();

bool readSensors(SensorReading &reading);
