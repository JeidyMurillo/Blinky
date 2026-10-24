# Cronograma del proyecto

## 1. Actividades y duración
s
Para estimar las duraciones se considera una jornada productiva de 6 horas por integrante al día:
duración (días) = esfuerzo (h) ÷ (integrantes asignados × 6 h).

| Código | Paquete de trabajo | Esfuerzo (h) | Integrantes asignados | Duración (días) | Predecesora |
|---|---|---:|---:|---:|---|
| 1.4.1.1 | Módulo de captura de la cámara del PC | 12 | 2 | 1 | — |
| 1.4.2.1 | Detector de rostro y puntos de los ojos | 18 | 2 | 1,5 | 1.4.1.1 |
| 1.4.3.1 | Algoritmo de EAR y detección de parpadeos | 24 | 2 | 2 | 1.4.2.1 |
| 1.4.3.3 | Métricas de parpadeo | 18 | 2 | 1,5 | 1.4.3.1 |
| 1.4.3.2 | Calibración del umbral de EAR | 12 | 1 | 2 | 1.4.3.3 |
| **Total** | | **84 h** | **5 integrantes disponibles** | | |

## 2. Dependencias de las actividades

Las actividades se organizan de manera secuencial, ya que cada una utiliza los resultados de la anterior. Primero se obtiene el módulo de captura de la cámara; después se detectan el rostro y los puntos de referencia de los ojos. Con esta información se calcula el EAR para detectar los parpadeos, se obtienen las métricas de frecuencia y, finalmente, se calibra el umbral individual para mejorar la exactitud del sistema.

## 3. Cronograma y ruta crítica

Se considera que las actividades se ejecutan de forma secuencial, que las duraciones corresponden a días hábiles (lunes a viernes) y que el proyecto inicia el 26 de octubre de 2026.

| Código | ES | EF | LS | LF | Holgura | Inicio | Fin |
|---|---:|---:|---:|---:|---:|---|---|
| 1.4.1.1 | 0 | 1 | 0 | 1 | 0 | 26 oct | 26 oct |
| 1.4.2.1 | 1 | 2,5 | 1 | 2,5 | 0 | 27 oct | 28 oct (mediodía) |
| 1.4.3.1 | 2,5 | 4,5 | 2,5 | 4,5 | 0 | 28 oct (tarde) | 30 oct (mediodía) |
| 1.4.3.3 | 4,5 | 6 | 4,5 | 6 | 0 | 30 oct (tarde) | 3 nov |
| 1.4.3.2 | 6 | 8 | 6 | 8 | 0 | 4 nov | 5 nov |

- **ES:** inicio temprano.
- **EF:** finalización temprana.
- **LS:** inicio tardío.
- **LF:** finalización tardía.
- **Holgura:** tiempo que puede retrasarse una actividad sin retrasar la fecha final del módulo.

La ruta crítica es **1.4.1.1 → 1.4.2.1 → 1.4.3.1 → 1.4.3.3 → 1.4.3.2**, con una duración total de **8 días hábiles**, que terminan el **5 de noviembre de 2026**. Todas las actividades tienen holgura cero, por lo que un retraso en cualquiera de ellas afectaría la fecha de finalización del módulo.