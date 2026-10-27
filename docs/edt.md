# ESTRUCTURA DE DESGLOSE DE TRABAJO (EDT / WBS)
## Sistema inteligente para la prevención de fatiga visual

## Jerarquía del EDT

- **1.0 Sistema inteligente para la prevención de fatiga visual**
  - **1.1 Proyecto planificado y controlado**
    - 1.1.1 Alcance, objetivos y restricciones definidos
      - 1.1.1.1 Acta de constitución del proyecto
    - 1.1.2 Historias de usuario realizadas
      - 1.1.2.1 Historias de usuario
    - 1.1.3 Cronograma, presupuesto y asignación de responsables
      - 1.1.3.1 Cronograma del proyecto y presupuesto
    - 1.1.4 Registro de riesgos
      - 1.1.4.1 Matriz de riesgos
    - 1.1.5 Reporte de avances y actas de reunión
      - 1.1.5.1 Reportes de seguimiento y control
  - **1.2 Nodo IoT ambiental (ESP32)**
    - 1.2.1 ESP32 configurado
      - 1.2.1.1 Dispositivo inicial configurado
      - 1.2.1.2 Entorno de ejecución preparado
    - 1.2.2 Nodo ESP32
      - 1.2.2.1 Nodo ESP32 montado
    - 1.2.3 Firmware del ESP32 (Lectura y MQTT)
      - 1.2.3.2 Librerías y dependencias instaladas
    - 1.2.4 Registro de lecturas verificado
      - 1.2.4.1 Prueba de funcionamiento de ESP32
  - **1.3 Módulo de detección y medición de parpadeos**
    - 1.3.1 Detector de parpadeos
      - 1.3.1.1 Módulo de captura de video
      - 1.3.1.2 Detector de rostro y ojos
      - 1.3.1.3 Algoritmo de EAR implementado
    - 1.3.2 Medición personalizada de parpadeo
      - 1.3.2.1 Métricas de parpadeo
      - 1.3.2.2 Sistema de calibración
  - **1.4 Módulo de seguimiento del tiempo frente a la pantalla**
    - 1.4.1 Seguimiento de la exposición
      - 1.4.1.1 Detector de presencia
      - 1.4.1.2 Contador de tiempo de exposición
    - 1.4.2 Gestión de pausas
      - 1.4.2.1 Parámetro de pausa mínima
      - 1.4.2.2 Registro de pausas
  - **1.5 Módulo de seguimiento y comunicación ambiental**
    - 1.5.1 Sensores BH1750 y SHT31 conectados
      - 1.5.1.1 Sensores integrado al ESP32
    - 1.5.2 Firmware de lectura ambiental
      - 1.5.2.1 Firmware de lectura de datos
    - 1.5.3 Broker MQTT y tópicos
      - 1.5.3.1 Broker MQTT configurado
    - 1.5.4 Canal de datos MQTT, ESP32-PC
      - 1.5.4.1 Firmware de publicación MQTT
  - **1.6 Motor integrado de evaluación del estado visual**
    - 1.6.1 Módulo de consolidación de métricas
      - 1.6.1.1 Módulo de integración de datos
    - 1.6.2 Reglas de decisión
      - 1.6.2.1 Motor de reglas
    - 1.6.3 Recomendaciones 20-20-20
      - 1.6.3.1 Módulo de generación de recomendaciones
    - 1.6.4 Alertas por frecuencia de parpadeo
      - 1.6.4.1 Módulo de alertas por parpadeo
    - 1.6.5 Recomendaciones de iluminación, ventilación y humidificación
      - 1.6.5.1 Catálogo de recomendaciones ambientales
    - 1.6.6 Tabla de umbrales predefinidos
      - 1.6.6.1 Archivos de parámetros de motor
  - **1.7 Interfaz funcional de seguimiento y recomendaciones**
    - 1.7.1 Prototipo de interfaz
      - 1.7.1.1 Prototipo de interfaz
    - 1.7.2 Panel de parpadeo y exposición
      - 1.7.2.1 Gráficos y métricas en tiempo real
    - 1.7.3 Panel ambiental
      - 1.7.3.1 Panel ambiental
    - 1.7.4 Avisos de descanso y recomendaciones
      - 1.7.4.1 Componente de alertas
  - **1.8 Sistema integrado, estable y respetuoso de la privacidad**
    - 1.8.1 Aplicación integrada
      - 1.8.1.1 Integración completa
    - 1.8.2 Informe de verificación de privacidad
      - 1.8.2.1 Informe de privacidad
    - 1.8.3 Informe de consumo de CPU y memoria
      - 1.8.3.1 Versión optimizada del sistema
    - 1.8.4 Informe de compatibilidad con hardware
      - 1.8.4.1 Informe de compatibilidad
  - **1.9 Sistema verificado con evidencia de pruebas**
    - 1.9.1 Casos de prueba
      - 1.9.1.1 Casos de prueba
    - 1.9.2 Informe de pruebas de detección de parpadeos vs. conteo manual
      - 1.9.2.1 Resultados de precisión
    - 1.9.3 Informe de pruebas con usuarios y distintas condiciones
      - 1.9.3.1 Informe de pruebas con usuarios
    - 1.9.4 Informe de pruebas de integración y MQTT
      - 1.9.4.1 Evidencia de integración MQTT
    - 1.9.5 Informe de pruebas de recuperación ante fallos
      - 1.9.5.1 Informe de pruebas de recuperación
    - 1.9.6 Informe de pruebas de rendimiento y privacidad
      - 1.9.6.1 Pruebas e informe de rendimiento
  - **1.10 Despliegue del sistema**
    - 1.10.1 Preparación del entorno de despliegue
      - 1.10.1.1 Configuración del entorno de ejecución
    - 1.10.2 Instalación y configuración del sistema integrado
      - 1.10.2.1 Preparación de servicios y recursos necesarios
      - 1.10.2.2 Instalación de los componentes integrados
    - 1.10.3 Verificación del funcionamiento desplegado
      - 1.10.3.1 Configuración de parámetros de ejecución
      - 1.10.3.2 Pruebas de funcionamiento en el entorno final
      - 1.10.3.3 Validación de la comunicación entre componentes
    - 1.10.4 Registro de evidencias del despliegue
      - 1.10.4.1 Informe de despliegue
  - **1.11 Documentación técnica y cierre del proyecto**
    - 1.11.1 Documentación de arquitectura y componentes
      - 1.11.1.1 Documentación técnica
    - 1.11.2 Manual de instalación, configuración y uso
      - 1.11.2.1 Manual de usuario
    - 1.11.3 Documentación de reglas, umbrales y MQTT
      - 1.11.3.1 Guía de reglas y MQTT
    - 1.11.4 Informe de resultados de pruebas y validación
      - 1.11.4.1 Informe final de pruebas
    - 1.11.5 Presentación y demostración del prototipo
      - 1.11.5.1 Presentación del prototipo
    - 1.11.6 Verificación final y cierre
      - 1.11.6.1 Acta de cierre

## Diagrama del EDT

![EDT](images/Image.png)
Link para ver mejor: https://www.mindomo.com/mindmap/e885309891254d5a9b609da6db271776

## Diccionario del EDT

| Código | Paquete de trabajo | Descripción |
| :--- | :--- | :--- |
| 1.1.1.1 | Acta de constitución del proyecto | Documento aprobado con objetivos, alcance, interesados, riesgos, hitos, presupuesto y firmas. |
| 1.1.2.1 | Historias de usuario | Conjunto de historias que describen lo que el usuario espera del sistema, con su prioridad. |
| 1.1.3.1 | Cronograma del proyecto y presupuesto | Calendario de entregables con responsables, y estimación de costos de hardware, infraestructura y horas. |
| 1.1.4.1 | Matriz de riesgos | Lista de riesgos del proyecto con su descripción, responsable y respuesta prevista. |
| 1.1.5.1 | Reportes de seguimiento y control | Informes periódicos de avance y actas de las reuniones del equipo y con el docente. |
| 1.2.1.1 | Dispositivo inicial configurado | ESP32 con su configuración básica y conexión a la red Wi-Fi lista para programarse. |
| 1.2.1.2 | Entorno de ejecución preparado | Entorno de desarrollo del ESP32 listo para compilar y cargar el firmware. |
| 1.2.2.1 | Nodo ESP32 montado | ESP32 con los sensores BH1750 y SHT31 cableados por I2C y alimentado por USB. |
| 1.2.3.2 | Librerías y dependencias instaladas | Librerías de los sensores, Wi-Fi y MQTT instaladas y disponibles en el entorno del ESP32. |
| 1.2.4.1 | Prueba de funcionamiento de ESP32 | Evidencia de que el ESP32 entrega lecturas coherentes de luz, temperatura y humedad. |
| 1.3.1.1 | Módulo de captura de video | Componente que obtiene los cuadros de la cámara integrada y los procesa solo en memoria. |
| 1.3.1.2 | Detector de rostro y ojos | Detector basado en MediaPipe que ubica el rostro y los puntos de referencia de los ojos. |
| 1.3.1.3 | Algoritmo de EAR implementado | Cálculo del Eye Aspect Ratio por cuadro y detección de cada parpadeo según el umbral. |
| 1.3.2.1 | Métricas de parpadeo | Frecuencia de parpadeos por minuto entregada al motor de decisión. |
| 1.3.2.2 | Sistema de calibración | Procedimiento y valor de umbral de EAR ajustado a cada usuario. |
| 1.4.1.1 | Detector de presencia | Componente que determina si el usuario está frente a la pantalla a partir de la detección de rostro. |
| 1.4.1.2 | Contador de tiempo de exposición | Contador que acumula el tiempo continuo frente a la pantalla mientras se detecta al usuario. |
| 1.4.2.1 | Parámetro de pausa mínima | Valor configurable del tiempo de ausencia necesario para considerar una pausa válida. |
| 1.4.2.2 | Registro de pausas | Registro de cada pausa válida y reinicio del contador de exposición. |
| 1.5.1.1 | Sensores integrado al ESP32 | Sensores de luz, temperatura y humedad reconocidos y leídos desde el ESP32. |
| 1.5.2.1 | Firmware de lectura de datos | Programa del ESP32 que lee luxes, temperatura (°C) y humedad relativa (%) de forma periódica. |
| 1.5.3.1 | Broker MQTT configurado | Mosquitto instalado en el PC, con los tópicos de luz, temperatura y humedad definidos. |
| 1.5.4.1 | Firmware de publicación MQTT | Programa del ESP32 que publica las lecturas en los tópicos MQTT y un receptor en el PC que las recibe. |
| 1.6.1.1 | Módulo de integración de datos | Componente que reúne parpadeo, tiempo de exposición y variables ambientales en un solo estado. |
| 1.6.2.1 | Motor de reglas | Componente que evalúa las reglas en tiempo real y emite el evento de alerta correspondiente. |
| 1.6.3.1 | Módulo de generación de recomendaciones | Componente que produce la recomendación de la regla 20-20-20 y de descanso cuando corresponde. |
| 1.6.4.1 | Módulo de alertas por parpadeo | Componente que genera la alerta cuando la frecuencia de parpadeo cae bajo el umbral. |
| 1.6.5.1 | Catálogo de recomendaciones ambientales | Mensajes de ajuste de luz, ventilación y humidificación asociados a cada regla. |
| 1.6.6.1 | Archivos de parámetros de motor | Archivo con los valores de umbral predeterminados que usa el motor de reglas. |
| 1.7.1.1 | Prototipo de interfaz | Boceto de las pantallas del dashboard antes de su implementación. |
| 1.7.2.1 | Gráficos y métricas en tiempo real | Gráficos y valores en tiempo real de la frecuencia de parpadeo y del tiempo frente a la pantalla. |
| 1.7.3.1 | Panel ambiental | Visualización en tiempo real de luxes, temperatura y humedad relativa. |
| 1.7.4.1 | Componente de alertas | Elemento de la interfaz que muestra la recomendación generada por el motor de decisión. |
| 1.8.1.1 | Integración completa | Aplicación única que une visión artificial, receptor MQTT, motor de decisión y dashboard en el PC. |
| 1.8.2.1 | Informe de privacidad | Verificación de que el video se procesa en memoria y no se almacena ni se transmite. |
| 1.8.3.1 | Versión optimizada del sistema | Versión del sistema con ajustes que reducen el consumo de CPU y memoria y evitan retardos. |
| 1.8.4.1 | Informe de compatibilidad | Resultado de ejecutar el sistema en el PC y el ESP32 disponibles. |
| 1.9.1.1 | Casos de prueba | Casos definidos para cada criterio del Acta, incluidos los 20 del motor y los 20 del dashboard. |
| 1.9.2.1 | Resultados de precisión | Resultados de exactitud frente al conteo manual en pruebas con usuarios (meta ≥ 85 %). |
| 1.9.3.1 | Informe de pruebas con usuarios | Observaciones del usuario final sobre utilidad de los avisos en distintas condiciones de luz y posición. |
| 1.9.4.1 | Evidencia de integración MQTT | Resultados de la prueba continua de 10 minutos (meta: latencia < 2 s en el percentil 95). |
| 1.9.5.1 | Informe de pruebas de recuperación | Resultados de simular caídas de Wi-Fi, del broker o de un sensor y verificar la recuperación. |
| 1.9.6.1 | Pruebas e informe de rendimiento | Medición de CPU, memoria y tiempo de despliegue de alertas (meta: < 1 s en el 95 %). |
| 1.10.1.1 | Configuración del entorno de ejecución | Entorno final del PC con Python, OpenCV, MediaPipe y las dependencias instaladas. |
| 1.10.2.1 | Preparación de servicios y recursos necesarios | Servicios como el broker MQTT y permisos de cámara listos en el PC. |
| 1.10.2.2 | Instalación de los componentes integrados | Módulos del sistema instalados en el PC y firmware cargado en el ESP32. |
| 1.10.3.1 | Configuración de parámetros de ejecución | Umbrales, tópicos y direcciones de red ajustados para el entorno final. |
| 1.10.3.2 | Pruebas de funcionamiento en el entorno final | Evidencia de que el sistema completo funciona en el PC definitivo. |
| 1.10.3.3 | Validación de la comunicación entre componentes | Evidencia de que el ESP32, el broker, el motor y el dashboard se comunican correctamente. |
| 1.10.4.1 | Informe de despliegue | Documento con capturas y resultados del despliegue realizado. |
| 1.11.1.1 | Documentación técnica | Descripción de la arquitectura, los módulos y sus interfaces. |
| 1.11.2.1 | Manual de usuario | Instrucciones para instalar, configurar y usar el sistema. |
| 1.11.3.1 | Guía de reglas y MQTT | Descripción de las reglas de decisión, los umbrales y los tópicos MQTT. |
| 1.11.4.1 | Informe final de pruebas | Documento que consolida los resultados de los informes de la rama 1.9. |
| 1.11.5.1 | Presentación del prototipo | Presentación y demostración en vivo del prototipo funcionando ante el docente. |
| 1.11.6.1 | Acta de cierre | Documento firmado que confirma la entrega y la aceptación del proyecto. |
