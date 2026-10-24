# Cronograma del proyecto

## 1. Actividades y duración

| Código | Paquete de trabajo | Esfuerzo (h) | Integrantes asignados | Duración (días) | Predecesora |
|---|---|---:|---:|---:|---|
| 1.2.1 | Captura de video mediante webcam | 12 | 2 | 1 | — |
| 1.2.2 | Detección del rostro y landmarks de los ojos | 18 | 2 | 1 día y 5 horas | 1.2.1 |
| 1.2.3 | Cálculo del EAR y detección de parpadeos | 24 | 2 | 2 | 1.2.2 |
| 1.2.4 | Cálculo de frecuencia y duración del parpadeo | 18 | 2 | 1 día y 5 horas | 1.2.3 |
| 1.2.5 | Calibración del umbral individual de EAR | 12 | 1 | 2 | 1.2.4 |
| **Total** | | **84 h** | **5 integrantes disponibles** | | |

## 2. Dependencias de las actividades

Las actividades se organizan de manera secuencial, ya que cada una utiliza los resultados de la anterior. Primero se captura el video mediante la webcam; después se detectan el rostro y los puntos de referencia de los ojos. Con esta información se calcula el EAR para detectar los parpadeos, se mide su frecuencia y duración y, finalmente, se calibra el umbral individual para mejorar la precisión del sistema.

## 3. Cronograma y ruta crítica

Se considera que las actividades se ejecutan de forma secuencial y que las duraciones registradas corresponden a tiempo transcurrido.

| Código | ES | EF | LS | LF | Holgura |
|---|---:|---:|---:|---:|---:|
| 1.2.1 | 0 | 1 | 0 | 1 | 0 |
| 1.2.2 | 1 | 2,625 | 1 | 2,625 | 0 |
| 1.2.3 | 2,625 | 4,625 | 2,625 | 4,625 | 0 |
| 1.2.4 | 4,625 | 6,25 | 4,625 | 6,25 | 0 |
| 1.2.5 | 6,25 | 8,25 | 6,25 | 8,25 | 0 |

- **ES:** inicio temprano.
- **EF:** finalización temprana.
- **LS:** inicio tardío.
- **LF:** finalización tardía.
- **Holgura:** tiempo que puede retrasarse una actividad sin retrasar la fecha final del proyecto.

La ruta crítica es **1.2.1 → 1.2.2 → 1.2.3 → 1.2.4 → 1.2.5**, con una duración total estimada de **8,25 días**, bajo el supuesto de ejecución secuencial. Todas las actividades tienen holgura cero, por lo que un retraso en cualquiera de ellas afectaría la fecha de finalización del proyecto.
