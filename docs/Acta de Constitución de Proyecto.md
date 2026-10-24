# Acta de Constitución del Proyecto

| Campo | Información |
| :--- | :--- |
| **Nombre del Proyecto:** | Sistema inteligente para la prevención de fatiga visual mediante detección de parpadeos, monitoreo del tiempo de exposición a pantallas y condiciones ambientales (iluminación, temperatura y humedad). |
| **Patrocinador:** | Equipo del Proyecto |
| **Gerente del proyecto:** | Karol Nasner |
| **Cliente:** | Nombre del usuario específico |
| **Responsable:** | Equipo de Desarrollo |
| **Fecha de Inicio esperada:** | 26 oct 26 |
| **Fecha de finalización esperada:** | 10 dic 26 |

---

## Definición del Problema
El uso prolongado de pantallas digitales puede estar asociado con fatiga visual y cambios negativos en el patrón de parpadeo de los usuarios. Adicionalmente, las condiciones ambientales desfavorables, como una iluminación inadecuada, afectan el confort visual. Asimismo, la temperatura elevada y la baja humedad relativa del ambiente favorecen la evaporación de la película lagrimal, lo que intensifica la sequedad y el cansancio ocular. La falta de herramientas preventivas automatizadas en tiempo real propicia la aparición de síntomas de cansancio ocular durante las jornadas prolongadas frente al computador.

---

## Definición de Objetivos
Al 3 de diciembre, entregar un prototipo que detecte parpadeos con $\ge85\%$ de exactitud, reciba luz, temperatura y humedad en menos de 2 s en el 95% de las transmisiones, y muestre la recomendación correcta en el dashboard.

| Objetivos | Criterios de evaluación de los objetivos |
| :--- | :--- |
| **1. Desarrollar un módulo de monitoreo en tiempo real del parpadeo mediante procesamiento de video en el PC con su cámara integrada.** | Detección exitosa del valor Eye Aspect Ratio (EAR) e identificación de parpadeos con una exactitud del 85% en pruebas con usuarios. |
| **2. Integrar un nodo IoT ambiental (ESP32 + BH1750 + SHT31) para la captura de iluminación, temperatura y humedad relativa.** | Latencia de recepción de datos de luxes, temperatura (°C) y humedad relativa (%) vía protocolo MQTT inferior a 2 segundos en el percentil 95 ($P_{95}$) de los casos durante una prueba continua de 10 minutos desde el ESP32 hacia el PC. |
| **3. Implementar un motor de decisión.** | Evaluación en tiempo real de las reglas lógicas unificadas (combinación de parpadeo, tiempo de pantalla, iluminación, temperatura y humedad) determinando la alerta correspondiente con un 95% de coherencia lógica de un conjunto de 20 casos de pruebas definidos. |
| **4. Implementar un dashboard en aplicación de alertas preventivas.** | Despliegue correcto y en tiempo real de recomendaciones específicas (regla 20-20-20, descanso, ajuste de luz, ventilación o humidificación del espacio) en la interfaz gráfica ante cada evento generado por el motor de decisión. La alerta deberá aparecer en menos de 1 segundo desde que el motor de decisión genere la recomendación, en al menos el 95 % de 20 pruebas. |

---

## Alcance

| Dentro del Alcance | Fuera del Alcance |
| :--- | :--- |
| Captura y procesamiento de video local en el PC mediante su cámara integrada. | Diagnóstico, tratamiento o detección de patologías oftálmicas o enfermedades oculares. |
| Detección de parpadeos (EAR) usando OpenCV y MediaPipe. | Almacenamiento o transmisión de video grabado del usuario (prioridad en privacidad). |
| Medición de variables ambientales (iluminación, temperatura y humedad relativa) con ESP32 + sensores BH1750 y SHT31. | Modelos de inteligencia artificial complejos en la nube o requerimientos de procesamiento externo. |
| Comunicación entre el PC y el ESP32 mediante MQTT/Wi-Fi. | Fabricación a escala industrial de un producto comercial o carcasa personalizada. |
| Interfaz gráfica local para métricas y recomendaciones. | Soporte para otros sistemas operativos (macOS, Linux, móviles). |

---

## Suposiciones
1. Suponemos que contamos con el ESP32, el BH1750 y el SHT31 durante todo el semestre.
2. Suponemos que la red Wi-Fi permite una comunicación MQTT estable entre el PC y el ESP32.
3. Suponemos que el PC cuenta con una cámara HD con capacidad para la captura de imagen en condiciones de baja iluminación y con el rendimiento computacional suficiente para ejecutar OpenCV y MediaPipe de forma fluida.
4. Suponemos que los sensores se ubicarán cerca del puesto de trabajo, para que las lecturas representen el ambiente real.
5. Suponemos que los usuarios de prueba colaborarán de forma objetiva en la validación.

---

## Restricciones
* **Disponibilidad de hardware:** Dependencia directa de los componentes físicos especificados (ESP32, BH1750 y SHT31).
* **Recursos técnicos y de procesamiento:** Dependencia del rendimiento y la calidad de la cámara del PC (resolución, ángulo, posición).
* **Cronograma académico:** El desarrollo y la validación del proyecto deben completarse estrictamente dentro de los plazos establecidos por la institución educativa para el proyecto integrador.

---

## Factores generales de riesgo

| Riesgo | Descripción | Responsable |
| :--- | :--- | :--- |
| **1. Falsos positivos o negativos en la detección de parpadeos por mala iluminación o posición frente a la cámara del PC** | Este factor puede degradar la precisión del sistema y provocar alertas inoportunas al usuario. | Desarrollador Principal (Visión Artificial) |
| **2. Inestabilidad en la conexión Wi-Fi o caída del broker MQTT** | Puede causar la interrupción en la recepción de los datos ambientales (iluminación, temperatura y humedad) enviados por el ESP32. | Desarrollador IoT |
| **3. El PC disponible no cuente con los recursos** | Este problema tiene como consecuencia un retardo (lag) o posible congelamiento en la interfaz y en el flujo de video de OpenCV. | Arquitecto de Software |
| **4. Baja precisión inicial del motor de decisión basado en reglas fijas** | Puede resultar en recomendaciones poco adaptadas al comportamiento real y subjetivo del usuario final. | Gerente del Proyecto |
| **5. Fallas físicas en el cableado, en el sensor BH1750 o SHT31** | Ocasiona la pérdida temporal o definitiva de la variable de iluminación o humedad ambiental dentro del motor de decisión. | Desarrollador IoT |

---

## Interesados

| Interesado | Poder | Interés | Criterio de éxito | Estrategia |
| :--- | :--- | :--- | :--- | :--- |
| **Usuario:** Oscar Eduardo Materon - Guardia de seguridad | Medio | Alto | No desactiva los avisos y los considera útiles. | Gestionar de cerca (entrevistas y pruebas) |
| **Gerente del proyecto** | Alto | Alto | Entrega a tiempo con los objetivos cumplidos. | Gestionar de cerca |
| **Desarrollador principal** | Medio | Alto | Detecta parpadeos con $\ge85\%$ de exactitud en las pruebas con usuarios. | Gestionar de cerca |
| **Desarrollador IoT** | Medio | Alto | Luz, temperatura y humedad llegan al PC con una latencia inferior a 2 s en el percentil 95 ($P_{95}$) durante una prueba continua de 10 minutos. | Gestionar de cerca |
| **Docente evaluador** | Alto | Medio | Alcance y plazos cumplidos. | Mantener satisfecho |
| **Equipo de pruebas** | Bajo | Medio | Completa las sesiones de calibración y validación. | Mantener informado |

---

## Hitos Principales

| Hito | Descripción |
| :--- | :--- |
| **Aprobación del Acta de Constitución** | Definición y validación del alcance de la propuesta. |
| **Prototipo de Visión Artificial (Fase 1)** | Detección de parpadeos (EAR) con la cámara del PC. |
| **Prototipo IoT (Fase 2)** | Envío de lecturas de luxes, temperatura y humedad desde el ESP32 mediante MQTT. |
| **Implementación del Motor de Decisión (Fase 3)** | Desarrollo de las reglas que combinan tiempo de exposición, parpadeo, iluminación, temperatura y humedad |
| **Implementación del dashboard de alertas preventivas (Fase 4)** | Desarrollo de la interfaz gráfica para mostrar métricas, recomendaciones y alertas; validación del tiempo de visualización establecido. |
| **Integración del Sistema** | Unificación completa de módulos de Visión Artificial, IoT, Motor de Decisión y Dashboard. |
| **Pruebas** | Evaluación empírica de métricas de desempeño, exactitud y usabilidad. |
| **Presupuesto** | Estimación de los costos asociados a hardware, infraestructura y desarrollo. |
| **Cierre del Proyecto y Presentación** | Entrega del informe final, código y demostración en vivo. |

---

## Presupuesto

| Rubro | Descripción | Cantidad | Costo unitario (COP) | Costo total (COP) |
| :--- | :--- | :---: | :---: | :---: |
| Hardware | ESP32 (microcontrolador con Wi-Fi) | 5 | $38.900 | $194.500 |
| Hardware | Sensor de luz BH1750 | 1 | $11.500 | $11.500 |
| Hardware | Sensor de temperatura y humedad SHT31 | 1 | $32.927 | $42.927 |
| Hardware | Cables, protoboard y fuente de alimentación USB | 1 |$20.000 | $20.000 |
| Hardware | Imprevistos | 1 |$50.000 | $50.000 |
| Infraestructura | Broker MQTT (Mosquitto, software libre) en el PC | 1 | 0 | 0 |
| Desarrollo | Software (Python, OpenCV, MediaPipe) – licencias libres | 1 | 0 | 0 |
| Desarrollo | Horas de trabajo del equipo | 84 h | $50.000 | $4.200.000|
| | **Total estimado (sin horas)** | | $163.327 | $318.927 |
| | **Total estimado (con horas)** | | $213.327 | $4.518.927 |

---

## Firmas

| Nombre | Rol | Fecha |
| :--- | :--- | :--- |
| | Gerente | |
| | Docente | |
