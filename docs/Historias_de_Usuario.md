# Historias de Usuario

**Proyecto integrador:** Sistema inteligente para la prevención de fatiga visual mediante detección de parpadeos, monitoreo del tiempo de exposición a pantallas y condiciones ambientales (iluminación, temperatura y humedad).

**Integrantes:** Sebastián Castro Rengifo · Karol Tatiana Burbano Nasner · Jeidy Nicol Murillo Murillo · Verónica Lorena Mujica Gavidia · Sofía Carolina Quenoran Ipujan

**Versión:** 1.0 · **Última actualización:** 15/11/2026

---

## 1. Introducción

Este documento recoge la elicitación de requisitos del proyecto: stakeholders, roles del equipo, entrevista al usuario final, historias de usuario con criterios de aceptación y Product Backlog priorizado. Está actualizado con los cambios del docente: el video se procesa con la cámara del PC y el nodo de sensores es un ESP32 con BH1750 y SHT31 (luz, temperatura y humedad).

Las historias están escritas desde el punto de vista de quien las usa y en su lenguaje. Los detalles técnicos (MediaPipe, EAR, MQTT, sensores) se registran aparte, en la línea **Nota técnica**, para el equipo de desarrollo.

Los criterios de aceptación usan el formato **Given/When/Then**, escrito en español como **Dado que** (Given), **cuando** (When), **entonces** (Then). Cada historia incluye al menos un **caso de error**.

### 1.1 Stakeholders

| Stakeholder | Rol | Lo que puede aportar |
|---|---|---|
| Usuario final | Trabajadores de oficina, estudiantes y personas con alta exposición a pantallas | Describe sus hábitos, molestias y expectativas; recibe las recomendaciones y decide si usa o abandona el sistema. |
| Gerente del proyecto | Coordina el proyecto y valida resultados | Gestiona el riesgo de baja precisión del motor de decisión, el cronograma y la comunicación con el docente. |
| Desarrollador principal | Visión artificial | Detección de parpadeos (OpenCV, MediaPipe, EAR) con la cámara del PC; viabilidad técnica de las historias de E1. |
| Desarrollador IoT | Nodo de sensores | ESP32 con BH1750 y SHT31, y comunicación MQTT hacia el PC. |
| Arquitecto de software | Integración y rendimiento | Integración de componentes y rendimiento del PC al ejecutar visión, panel y cliente MQTT. |
| Equipo de pruebas | Usuarios de prueba | Ayudan a calibrar y validar el detector de parpadeo y opinan sobre la utilidad de los avisos. |
| Docente evaluador | Revisor académico | Define el alcance y los criterios de evaluación, y solicitó los cambios de cámara y sensores. |

### 1.2 Roles del equipo

| Rol | Persona(s) | Responsabilidad principal en este proyecto |
|---|---|---|
| Project Manager | Karol Tatiana Burbano Nasner | Entrevistas, acta, cronograma |
| Product Owner | Verónica Lorena Mujica Gavidia | Backlog, priorización, aceptación |
| Scrum Master | Jeidy Nicol Murillo Murillo | Facilitar ceremonias, eliminar impedimentos |
| Development Team | Sebastián Castro Rengifo, Sofía Carolina Quenoran Ipujan | Estimar, desarrollar, probar |

### 1.3 Project Manager vs. Product Owner

|  | Project Manager (PM) | Product Owner (PO) |
|---|---|---|
| **Responsabilidades exclusivas** | 1. Planificar el cronograma y los hitos del proyecto.<br>2. Gestionar los riesgos del Acta de Constitución.<br>3. Conducir las entrevistas y redactar el acta de elicitación. | 1. Ser dueño del Product Backlog y ordenarlo por prioridad (MoSCoW).<br>2. Aceptar o rechazar cada historia en la Sprint Review según sus criterios.<br>3. Escribir y mantener las historias de usuario. |
| **Enfoque** | Que el proyecto se entregue a tiempo y dentro del alcance. | Que el producto entregue el mayor valor posible al usuario final. |
| **En la elicitación** | Prepara y conduce la entrevista, documenta el acta y la valida con el entrevistado. | Convierte el acta en historias, define sus criterios de aceptación y las prioriza. |

El Scrum Master facilita las ceremonias sin decidir el contenido, y el Development Team aporta la viabilidad técnica y las estimaciones.

## 2. Entrevista al usuario final

### 2.1 Guía de entrevista

**Entrevistado:** usuario final (trabajador de oficina o estudiante con alta exposición a pantallas). Es el stakeholder principal porque recibe las alertas y decide si el sistema se usa o se abandona.

**Duración:** 20 a 30 minutos.

**Apertura (2 min):** presentar el proyecto en una frase, aclarar que no hay respuestas «correctas» y pedir permiso para tomar notas.

#### Proceso actual (cómo funciona HOY)

1. Cuéntame cómo es un día normal frente a la pantalla: ¿cuántas horas seguidas pasas, qué haces y cuándo haces pausas?
2. ¿Qué haces hoy para cuidar tus ojos (descansos, gotas, lentes, aplicaciones, reglas como la 20-20-20)? ¿Cómo decides cuándo parar?

#### Puntos de dolor (qué problemas tiene HOY)

3. ¿Qué molestias sientes (ardor, sequedad, visión borrosa, dolor de cabeza) y en qué momento o en qué condiciones aparecen (poca luz, aire acondicionado, calor)?
4. ¿Qué te ha frustrado de los recordatorios o herramientas que has probado antes? ¿Por qué dejaste de usarlos?

#### Visión (qué espera que cambie)

5. Si este sistema funcionara perfecto, ¿qué sería distinto en tu jornada? ¿Cómo te gustaría recibir los avisos (sonido, notificación, pantalla completa, discretos)?
6. ¿Qué tendría que pasar para que confiaras en el sistema y qué te haría dejar de usarlo?

#### Casos borde (¿qué pasa cuando...?)

7. ¿Qué pasa cuando estás en una videollamada, un examen o una presentación y el sistema decide que debes descansar?
8. ¿Qué pasa cuando usas lentes, te mueves mucho, estás de lado, hay contraluz o tapas la cámara? ¿Qué esperarías que hiciera el sistema?
9. ¿Qué pasa si el sensor del ambiente se desconecta o el Wi-Fi falla? ¿Prefieres que el sistema siga con los datos que tenga o que te avise?

#### Pregunta de cierre

10. ¿Qué no te pregunté que debería haberte preguntado?

**Despedida (2 min):** resumir lo entendido, agradecer y preguntar si se puede volver a contactar al entrevistado para validar el prototipo.

### 2.2 Acta de elicitación

**Proyecto:** Sistema inteligente para la prevención de fatiga visual mediante detección de parpadeos y monitoreo ambiental.  
**Entrevistado:** Felipe Salcedo, usuario final (estudiante).  
**Fecha:** 06/10/2026

**PUNTOS DE DOLOR ACTUALES**

- Ardor y sequedad ocular tras 3-4 horas continuas frente a la pantalla.
- Se olvida de hacer pausas porque está concentrado; los recordatorios que ha usado son por tiempo fijo y los ignora o desactiva.
- No sabe si su entorno (poca luz, aire acondicionado, aire seco) empeora las molestias.

**VISIÓN DEL NEGOCIO**

- Recibir avisos oportunos y personalizados (según su parpadeo y su ambiente, no solo por tiempo), discretos y que no interrumpan su trabajo.
- Ver un resumen simple de su jornada (tiempo de exposición, parpadeos por minuto, luz, temperatura y humedad) y recomendaciones concretas.

**ACTORES IDENTIFICADOS**

- Usuario final (trabajador de oficina, estudiante).
- Equipo de pruebas: compañeros que calibran y validan el detector de parpadeo.
- Equipo de desarrollo (visión artificial, IoT, arquitectura) y gerente del proyecto.
- Docente evaluador. Posible: jefe o docente si se quisieran reportes (por confirmar).

**RESTRICCIONES EXPLÍCITAS**

- No quiere que se grabe ni se almacene video suyo (privacidad).
- El sistema no debe ralentizar su computador ni distraerlo en videollamadas o presentaciones.
- Debe funcionar con la cámara integrada del PC y con la red Wi-Fi existente.

**REQUISITOS LATENTES DESCUBIERTOS**

- Modo «No molestar» para videollamadas, exámenes o presentaciones.
- Calibración inicial por usuario (lentes, forma de parpadear diferente).
- Comportamiento ante fallos: si falla el sensor o el Wi-Fi, seguir con parpadeo y tiempo, y avisar de forma clara.
- Alertas configurables (frecuencia, tipo, horario) y bitácora de alertas para ver si las recomendaciones realmente ayudan.

**REQUISITOS IMPLÍCITOS (esperados aunque nadie los dijo)**

- Instalación y uso sencillos, con mensajes en español y sin términos técnicos.
- Que funcione sin conexión a internet, solo con la red local.
- Que los datos mostrados sean confiables: ante la duda, el sistema prefiere decir «sin datos» a mostrar un valor falso.

**VALIDACIÓN DEL ACTA (antes de escribir las historias)**

- [ ] Acta revisada y confirmada por el entrevistado. Fecha: ____ / ____ / ________

## 3. Épicas del proyecto

| ID | Épica | Objetivo del Acta |
|---|---|---|
| E1 | Detección de parpadeos (Visión artificial) | Objetivo 1 |
| E2 | Monitoreo del tiempo de exposición a pantalla | Objetivos 1 y 3 |
| E3 | Nodo IoT ambiental (luz, temperatura y humedad) | Objetivo 2 |
| E4 | Motor de decisión y recomendaciones | Objetivo 3 |
| E5 | Dashboard e interfaz de usuario | Objetivo 3 |
| E6 | Privacidad, rendimiento y validación | Todos los objetivos |

Cada épica corresponde a una épica del tablero Jira del proyecto: E1 → `SCRUM-3`, E2 → `SCRUM-4`, E3 → `SCRUM-2`, E4 → `SCRUM-5`, E5 → `SCRUM-6` y E6 → `SCRUM-8` y `SCRUM-9` (pruebas, despliegue y cierre). La épica `SCRUM-1` agrupa la gestión del proyecto.

## 4. Historias de usuario

### 4.1 E1. Detección de parpadeos (Visión artificial)

#### HU-01 — Activar la cámara de mi computador

**Historia:** Como **usuario final**, quiero que el sistema use la cámara de mi computador para observar mis ojos mientras trabajo, para que mis parpadeos se midan automáticamente, sin tener que hacer nada.

**Criterios de aceptación:**

- **Dado que** abrí la aplicación, **cuando** acepto el permiso de la cámara, **entonces** el sistema empieza a monitorearme y me muestra un indicador de que está activo.
- **Dado que** el monitoreo está activo, **cuando** trabajo con normalidad frente a la pantalla, **entonces** el sistema sigue funcionando sin que yo deba hacer nada más.
- **Caso de error:** **Dado que** la cámara está tapada, desconectada, en uso por otra aplicación o negué el permiso, **cuando** intento iniciar el monitoreo, **entonces** veo un mensaje claro que me explica qué debo hacer para solucionarlo.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Objetivo 1
- **Nota técnica (para el equipo):** Cámara integrada del PC; captura de video con OpenCV (cambio solicitado por el docente: ya no se usa una webcam USB externa).

#### HU-02 — Reconocer cuándo estoy frente a la pantalla

**Historia:** Como **usuario final**, quiero que el sistema reconozca cuándo estoy frente a la pantalla y cuándo me levanté, para que solo cuente mis parpadeos cuando realmente estoy trabajando.

**Criterios de aceptación:**

- **Dado que** el monitoreo está activo, **cuando** estoy sentado frente a la pantalla a una distancia normal, **entonces** el sistema me muestra el estado «Usuario detectado»; si no ve mi rostro, muestra «Sin rostro».
- **Dado que** el monitoreo está activo, **cuando** me levanto o salgo del encuadre de la cámara, **entonces** el sistema deja de contar parpadeos y registra que estoy ausente.
- **Caso de error:** **Dado que** hay poca luz, uso lentes o me muevo mucho, **cuando** el sistema no logra ver mis ojos con claridad, **entonces** me muestra «Sin rostro» o «Calibrando» en lugar de contar datos incorrectos.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Objetivo 1
- **Nota técnica (para el equipo):** Detección de rostro y de los puntos de referencia (landmarks) de los ojos con MediaPipe.

#### HU-03 — Contar mis parpadeos con exactitud

**Historia:** Como **usuario final**, quiero que el sistema cuente cada vez que parpadeo, para saber con exactitud cuántas veces parpadeo mientras uso la pantalla.

**Criterios de aceptación:**

- **Dado que** el monitoreo está activo y el sistema me ve bien, **cuando** parpadeo, **entonces** el contador de parpadeos aumenta en uno.
- **Dado que** se hizo una prueba con varios usuarios, **cuando** se compara el conteo del sistema con un conteo manual, **entonces** el sistema acierta al menos en el 85 % de los parpadeos.
- **Caso de error:** **Dado que** tengo los ojos entrecerrados, miro hacia abajo o muevo la cabeza bruscamente, **cuando** no hubo un parpadeo real, **entonces** el sistema no lo cuenta como parpadeo.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Objetivo 1
- **Nota técnica (para el equipo):** Cálculo del Eye Aspect Ratio (EAR) por fotograma; el parpadeo se registra cuando el EAR baja del umbral durante un número mínimo de fotogramas.

#### HU-04 — Ver mi frecuencia de parpadeo

**Historia:** Como **usuario final**, quiero ver cuántas veces parpadeo por minuto y cuánto dura aproximadamente cada parpadeo, para darme cuenta si estoy parpadeando menos de lo normal.

**Criterios de aceptación:**

- **Dado que** el monitoreo está activo, **cuando** pasa un minuto de uso, **entonces** veo mi frecuencia de parpadeo por minuto actualizada.
- **Dado que** mi frecuencia está por debajo del nivel saludable, **cuando** miro el panel, **entonces** el valor aparece resaltado (por ejemplo, con otro color).
- **Caso de error:** **Dado que** acabo de iniciar y todavía no hay datos suficientes, **cuando** miro mi frecuencia de parpadeo, **entonces** veo «Calculando…» en lugar de un número engañoso.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Objetivo 1
- **Nota técnica (para el equipo):** Frecuencia calculada en ventana móvil (último minuto) y duración promedio del cierre ocular.

#### HU-05 — Ajustar el sistema a mi forma de parpadear

**Historia:** Como **usuario final**, quiero que el sistema se adapte a mis ojos (con o sin lentes, ojos más grandes o más pequeños), para que no cuente parpadeos falsos ni se le escapen los reales.

**Criterios de aceptación:**

- **Dado que** es la primera vez que uso el sistema, **cuando** lo inicio, **entonces** me guía en una calibración corta de unos segundos mirando la pantalla.
- **Dado que** cambié de lentes o de posición, **cuando** pido recalibrar desde el panel, **entonces** la calibración se repite y se guardan los nuevos ajustes.
- **Caso de error:** **Dado que** no pude completar la calibración (me moví o tapé la cámara), **cuando** termina el tiempo de calibración, **entonces** me pide repetirla y, mientras no esté lista, muestra «Calibrando» y no cuenta parpadeos con un umbral dudoso.

- **Tipo de requisito:** Latente
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Objetivo 1
- **Nota técnica (para el equipo):** Calibración del umbral de EAR por usuario; el umbral calibrado se usa durante toda la sesión.

#### HU-06 — Detectar parpadeos incompletos

**Historia:** Como **usuario final**, quiero que el sistema note cuando parpadeo a medias, sin cerrar del todo los ojos, para recibir avisos más precisos sobre mi nivel de cansancio.

**Criterios de aceptación:**

- **Dado que** el monitoreo está activo, **cuando** parpadeo sin cerrar completamente los ojos, **entonces** el sistema lo registra como parpadeo incompleto y lo cuenta aparte.
- **Dado que** terminé mi sesión, **cuando** consulto mi resumen, **entonces** veo cuántos parpadeos fueron completos y cuántos incompletos.
- **Caso de error:** **Dado que** el sistema no está seguro de si fue un parpadeo incompleto o un simple movimiento, **cuando** no puede clasificarlo con seguridad, **entonces** no lo cuenta, para no inflar los datos.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Could
- **Fase / Hito:** Backlog (no comprometida para la primera versión)
- **Objetivo relacionado:** Objetivo 1
- **Nota técnica (para el equipo):** Requiere un rango intermedio de EAR; si se implementa, la precisión se documenta en las pruebas.

### 4.2 E2. Monitoreo del tiempo de exposición a pantalla

#### HU-07 — Medir mi tiempo continuo frente a la pantalla

**Historia:** Como **usuario final**, quiero que el sistema mida cuánto tiempo llevo frente a la pantalla sin descansar, para saber cuándo ya pasó un tiempo razonable y necesito una pausa.

**Criterios de aceptación:**

- **Dado que** estoy frente a la pantalla, **cuando** el sistema me detecta, **entonces** el contador de tiempo continuo empieza y se ve en el panel.
- **Dado que** el contador está corriendo, **cuando** sigo trabajando durante la sesión, **entonces** el tiempo se mantiene actualizado sin reiniciarse por sí solo.
- **Caso de error:** **Dado que** el sistema deja de verme unos segundos (por ejemplo, agacho la cabeza), **cuando** vuelve a detectarme enseguida, **entonces** el contador no se reinicia por esa interrupción corta.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Objetivos 1 y 3
- **Nota técnica (para el equipo):** El contador inicia con la detección del rostro y tolera pérdidas breves de detección.

#### HU-08 — Reiniciar el contador tras una pausa real

**Historia:** Como **usuario final**, quiero que el contador se reinicie cuando me alejo de la pantalla el tiempo suficiente, para que mis descansos reales sean reconocidos y no me lleguen avisos innecesarios.

**Criterios de aceptación:**

- **Dado que** me levanté y me alejé de la pantalla, **cuando** pasa el tiempo mínimo de descanso, **entonces** el sistema considera que tomé una pausa válida.
- **Dado que** tomé una pausa válida, **cuando** vuelvo a la pantalla, **entonces** el contador empieza otra vez desde cero y la pausa queda en mi historial.
- **Caso de error:** **Dado que** me alejé solo unos segundos, **cuando** regreso antes del tiempo mínimo, **entonces** el contador sigue corriendo, porque eso no cuenta como descanso.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivos 1 y 3
- **Nota técnica (para el equipo):** El tiempo mínimo de ausencia para validar una pausa es configurable.

### 4.3 E3. Nodo IoT ambiental (luz, temperatura y humedad)

#### HU-09 — Medir la luz de mi espacio de trabajo

**Historia:** Como **usuario final**, quiero que el sistema mida la luz de mi espacio de trabajo, para saber si la iluminación es adecuada para mi confort visual.

**Criterios de aceptación:**

- **Dado que** el sensor está colocado cerca de mi puesto de trabajo, **cuando** el sistema está funcionando, **entonces** veo en el panel el nivel de luz actual de mi espacio.
- **Dado que** cambio la iluminación (apago una lámpara o abro una cortina), **cuando** pasan unos segundos, **entonces** el valor de luz mostrado cambia de acuerdo con ese cambio.
- **Dado que** se compara con un luxómetro o medidor de referencia, **cuando** se hacen pruebas, **entonces** los valores son coherentes con la referencia.
- **Caso de error:** **Dado que** el sensor de luz no responde, **cuando** el sistema intenta leerlo, **entonces** el panel muestra «Sin datos de luz» en lugar de un valor falso.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 2
- **Objetivo relacionado:** Objetivo 2
- **Nota técnica (para el equipo):** ESP32 + BH1750 por I2C (dirección `0x23`); lectura cada 2 s según `contracts/topics.md`.

#### HU-10 — Medir la temperatura y la humedad de mi espacio

**Historia:** Como **usuario final**, quiero que el sistema mida la temperatura y la humedad de mi espacio de trabajo, para saber si el aire (muy seco, muy frío o muy caliente) está resecando mis ojos.

**Criterios de aceptación:**

- **Dado que** el sensor está colocado cerca de mi puesto de trabajo, **cuando** el sistema está funcionando, **entonces** veo en el panel la temperatura y la humedad actuales.
- **Dado que** enciendo o apago el aire acondicionado o un ventilador, **cuando** pasan unos minutos, **entonces** los valores mostrados se actualizan con el cambio.
- **Caso de error:** **Dado que** el sensor está desconectado o entrega una lectura imposible, **cuando** el sistema lo detecta, **entonces** muestra «Sin datos» para esa medida y no la usa en los avisos.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 2
- **Objetivo relacionado:** Objetivo 2
- **Nota técnica (para el equipo):** SHT31 conectado al ESP32 por I2C (dirección `0x44`). Sustituye al DHT22 del prototipo anterior. Nueva historia por cambio del docente.

#### HU-11 — Ver los datos de mi ambiente casi al instante

**Historia:** Como **usuario final**, quiero que la información de mi ambiente aparezca en mi pantalla casi al instante, para que los avisos reflejen cómo está mi entorno ahora y no hace varios minutos.

**Criterios de aceptación:**

- **Dado que** el sensor ambiental está encendido y conectado al Wi-Fi, **cuando** mide luz, temperatura y humedad, **entonces** los valores llegan a mi computador en menos de 2 segundos.
- **Dado que** los datos están llegando, **cuando** uso el sistema, **entonces** el panel muestra la hora de la última actualización.
- **Caso de error:** **Dado que** los datos dejan de llegar, **cuando** pasan 15 segundos sin recibir lecturas, **entonces** el panel marca esos valores como «desactualizados».

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 2
- **Objetivo relacionado:** Objetivo 2
- **Nota técnica (para el equipo):** El ESP32 publica por MQTT sobre Wi-Fi cada 2 s y el PC se suscribe; latencia < 2 s; el broker Mosquitto corre en el PC y los tópicos están en `contracts/topics.md`.

#### HU-12 — Seguir protegido aunque falle el sensor o el Wi-Fi

**Historia:** Como **usuario final**, quiero que el sistema siga avisándome por mis parpadeos y mi tiempo de pantalla aunque falle el sensor o el Wi-Fi, para no quedarme sin protección por una falla del ambiente.

**Criterios de aceptación:**

- **Caso de error:** **Dado que** se cae el Wi-Fi o se desconecta el sensor, **cuando** el sistema deja de recibir datos del ambiente, **entonces** sigue evaluando mis parpadeos y mi tiempo de pantalla sin interrumpirse.
- **Dado que** no hay datos del ambiente, **cuando** miro el panel, **entonces** veo un mensaje claro: «Sin datos del ambiente».
- **Dado que** se restablece la conexión, **cuando** vuelven a llegar lecturas, **entonces** el sistema retoma luz, temperatura y humedad sin que yo reinicie nada.

- **Tipo de requisito:** Latente
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 2
- **Objetivo relacionado:** Objetivo 2
- **Nota técnica (para el equipo):** Reconexión automática del ESP32 al Wi-Fi y al broker (LWT `offline` y reintento cada 5 s); el motor de decisión maneja datos faltantes.

### 4.4 E4. Motor de decisión y recomendaciones

#### HU-13 — Evaluar mi estado combinando todas las medidas

**Historia:** Como **usuario final**, quiero que el sistema combine mis parpadeos, mi tiempo de pantalla y las condiciones de mi ambiente (luz, temperatura y humedad), para recibir avisos basados en el conjunto de condiciones y no en una sola medida.

**Criterios de aceptación:**

- **Dado que** el sistema tiene datos de mis parpadeos, mi tiempo de pantalla y mi ambiente, **cuando** se evalúa mi estado, **entonces** el resultado tiene en cuenta todas esas medidas a la vez.
- **Dado que** mis parpadeos son pocos y además la luz es mala, **cuando** el sistema evalúa mi estado, **entonces** me recomienda una acción más específica que si solo se cumpliera una de las condiciones.
- **Caso de error:** **Dado que** falta alguna medida (por ejemplo, no hay datos de humedad), **cuando** se evalúa mi estado, **entonces** el sistema usa las medidas disponibles, no falla y no inventa valores.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Motor de reglas determinista con 5 variables (tiempo, parpadeo, luz, temperatura, humedad); reglas documentadas.

#### HU-14 — Recibir la recomendación 20-20-20

**Historia:** Como **usuario final**, quiero recibir la recomendación de mirar un objeto lejano (a unos 6 metros) durante 20 segundos cada 20 minutos, para relajar mi vista durante el trabajo prolongado.

**Criterios de aceptación:**

- **Dado que** llevo 20 minutos seguidos frente a la pantalla, **cuando** se cumple ese tiempo, **entonces** recibo la recomendación 20-20-20 con instrucciones claras de qué hacer.
- **Dado que** hice caso al aviso y descansé la vista, **cuando** termina mi descanso, **entonces** el contador empieza de nuevo.
- **Caso de error:** **Dado que** ignoré el aviso o lo pospuse, **cuando** pasa un tiempo, **entonces** el sistema no me lo repite de forma insistente; me lo vuelve a mostrar solo después de un tiempo razonable.

- **Nota de implementación:** `decision/rules.py:TwentyTwentyTwenty` guarda el estado de la alerta. El aviso se emite una sola vez y se rearma cuando `ExposureMetrics.breaks_taken` aumenta, es decir, cuando el pipeline valida una pausa.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3

#### HU-15 — Recibir un aviso cuando parpadeo poco

**Historia:** Como **usuario final**, quiero recibir una recomendación cuando parpadeo muy poco, para recordar parpadear y descansar antes de que aparezca la fatiga.

**Criterios de aceptación:**

- **Dado que** mi frecuencia de parpadeo está por debajo del mínimo saludable de forma sostenida, **cuando** pasan unos minutos así, **entonces** recibo un aviso para parpadear más y descansar la vista.
- **Dado que** mi frecuencia de parpadeo baja, **cuando** el sistema evalúa qué tan grave es, **entonces** el aviso es leve si bajó un poco y es una pausa recomendada si bajó mucho.
- **Caso de error:** **Dado que** mi frecuencia baja solo por unos segundos, **cuando** el sistema lo evalúa, **entonces** no recibo aviso, para evitar alertas falsas.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Umbral inicial de frecuencia mínima por validar en las pruebas con usuarios.

#### HU-16 — Recibir un aviso si la luz no es adecuada

**Historia:** Como **usuario final**, quiero que el sistema me avise si la luz de mi espacio es muy baja o excesiva, para corregir las condiciones que aumentan mi fatiga visual.

**Criterios de aceptación:**

- **Dado que** la luz está por debajo del rango adecuado para trabajar en pantalla, **cuando** el sistema lo detecta, **entonces** me recomienda aumentar la iluminación (por ejemplo, encender una lámpara).
- **Dado que** hay exceso de luz o reflejos en la pantalla, **cuando** el sistema lo detecta, **entonces** me recomienda reducirla (por ejemplo, cerrar una cortina).
- **Caso de error:** **Dado que** el sensor de luz no está disponible, **cuando** el sistema evalúa mi ambiente, **entonces** no me da recomendaciones de luz basadas en datos inexistentes.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Rangos de luxes adecuados para trabajo en pantalla por definir en las pruebas.

#### HU-17 — Recibir un consejo si el aire está seco o incómodo

**Historia:** Como **usuario final**, quiero recibir un consejo cuando el aire de mi espacio esté muy seco o la temperatura no sea confortable, para ventilar, hidratarme o ajustar el ambiente antes de que mis ojos se resequen.

**Criterios de aceptación:**

- **Dado que** la humedad está por debajo del rango recomendado, **cuando** el sistema lo detecta, **entonces** me sugiere una acción sencilla (por ejemplo, ventilar el espacio, tomar agua o alejarme del flujo directo del aire acondicionado).
- **Dado que** la temperatura está fuera del rango confortable, **cuando** el sistema lo detecta, **entonces** me sugiere ajustar el ambiente.
- **Caso de error:** **Dado que** el sensor de temperatura y humedad no está disponible, **cuando** el sistema evalúa mi ambiente, **entonces** no emite consejos ambientales y lo indica en el panel.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Nueva historia por cambio del docente (sensor de temperatura/humedad).

#### HU-18 — Ajustar los avisos a mi gusto

**Historia:** Como **usuario final**, quiero poder ajustar cada cuánto, cómo y en qué horarios recibo los avisos, para que se adapten a mi forma de trabajar y no los desactive por incomodidad.

**Criterios de aceptación:**

- **Dado que** abro la configuración, **cuando** cambio la frecuencia, el tipo de aviso (sonido o notificación discreta) o el horario, **entonces** los cambios se aplican y se conservan la próxima vez que abra la aplicación.
- **Dado que** no cambié ningún ajuste, **cuando** uso el sistema, **entonces** funciona con valores recomendados por defecto.
- **Caso de error:** **Dado que** ingreso un valor que no tiene sentido (por ejemplo, avisar cada 0 minutos), **cuando** intento guardarlo, **entonces** el sistema me explica el rango permitido y conserva el valor anterior.

- **Tipo de requisito:** Latente
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Umbrales (parpadeo, tiempo, luz, temperatura, humedad) en archivo de configuración con valores por defecto documentados; permite al gerente ajustar las reglas sin tocar el código.

#### HU-19 — Silenciar los avisos cuando no puedo interrumpirme

**Historia:** Como **usuario final**, quiero poder pausar los avisos cuando estoy en una videollamada, un examen o una presentación, para que el sistema no me interrumpa en momentos importantes.

**Criterios de aceptación:**

- **Dado que** voy a empezar una videollamada o presentación, **cuando** activo el modo «No molestar» por un tiempo, **entonces** no aparecen avisos emergentes mientras esté activo.
- **Dado que** terminó el tiempo de «No molestar», **cuando** el modo se desactiva, **entonces** veo un resumen de los avisos que quedaron pendientes.
- **Caso de error:** **Dado que** olvidé desactivar «No molestar», **cuando** pasa un tiempo máximo (por ejemplo, 2 horas), **entonces** el sistema lo desactiva solo para que no me quede sin protección.

- **Tipo de requisito:** Latente
- **Prioridad (MoSCoW):** Should
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Primera versión con activación manual; detección automática de videollamada o pantalla compartida queda como mejora si el tiempo lo permite.

### 4.5 E5. Dashboard e interfaz de usuario

#### HU-20 — Ver mis métricas en un panel

**Historia:** Como **usuario final**, quiero ver en un panel mis parpadeos por minuto, mi tiempo de pantalla, la luz, la temperatura y la humedad, para conocer mi estado visual y el de mi ambiente de un vistazo.

**Criterios de aceptación:**

- **Dado que** el sistema está funcionando, **cuando** abro el panel, **entonces** veo las cinco medidas con sus unidades y en un lenguaje claro, entendible para una persona sin conocimientos técnicos.
- **Dado que** mis datos cambian, **cuando** estoy mirando el panel, **entonces** los valores se actualizan solos, sin tener que recargar.
- **Caso de error:** **Dado que** falta alguno de los datos, **cuando** miro el panel, **entonces** esa medida aparece como «Sin datos» y las demás siguen visibles.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 4
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Interfaz gráfica local que corre en el PC.

#### HU-21 — Recibir el aviso «Descansa tus ojos»

**Historia:** Como **usuario final**, quiero recibir un aviso visible cuando el sistema determine que necesito una pausa, para tomar un descanso a tiempo y prevenir la fatiga.

**Criterios de aceptación:**

- **Dado que** el sistema determina que necesito una pausa, **cuando** se genera el aviso, **entonces** aparece un mensaje visible con la recomendación específica (20-20-20, descanso o ajuste del ambiente).
- **Dado que** aparece el aviso, **cuando** lo cierro o lo pospongo, **entonces** desaparece y me vuelve a avisar en el tiempo que elegí.
- **Caso de error:** **Dado que** estoy escribiendo o usando otra ventana, **cuando** aparece el aviso, **entonces** no me bloquea la pantalla ni borra lo que estoy haciendo.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 4
- **Objetivo relacionado:** Objetivo 3

#### HU-22 — Consultar el resumen de mi jornada

**Historia:** Como **usuario final**, quiero consultar un resumen de mi jornada con mi promedio de parpadeos, las pausas que hice y los avisos que recibí, para identificar mis hábitos y comprobar si las recomendaciones realmente me ayudan.

**Criterios de aceptación:**

- **Dado que** terminé mi sesión, **cuando** cierro el monitoreo, **entonces** veo el resumen: tiempo total, promedio de parpadeos por minuto, pausas tomadas y avisos recibidos.
- **Dado que** uso el sistema varios días, **cuando** consulto mi historial, **entonces** puedo ver cómo cambian mis datos de una sesión a otra.
- **Caso de error:** **Dado que** cierro la aplicación de forma inesperada (por ejemplo, se va la luz), **cuando** vuelvo a abrirla, **entonces** los datos de esa sesión no se pierden.

- **Tipo de requisito:** Latente
- **Prioridad (MoSCoW):** Could
- **Fase / Hito:** Fase 4
- **Objetivo relacionado:** Objetivo 3
- **Nota técnica (para el equipo):** Solo se guardan datos numéricos de forma local, nunca video.

### 4.6 E6. Privacidad, rendimiento y validación

#### HU-23 — Proteger mi privacidad

**Historia:** Como **usuario final**, quiero que mi video no se grabe ni se envíe a internet, para sentir confianza al usar una cámara durante mi jornada.

**Criterios de aceptación:**

- **Dado que** el monitoreo está activo, **cuando** reviso lo que se guarda en mi computador, **entonces** no existe ningún video ni foto mía; solo números (parpadeos, tiempos, luz, temperatura y humedad).
- **Dado que** estoy usando el sistema, **cuando** reviso su conexión a internet, **entonces** ninguna imagen sale de mi computador hacia internet ni hacia la nube.
- **Caso de error:** **Dado que** el sistema falla o se cierra inesperadamente, **cuando** reviso los archivos temporales, **entonces** tampoco quedan imágenes guardadas por el error.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 1
- **Objetivo relacionado:** Todos los objetivos
- **Nota técnica (para el equipo):** El video se procesa en memoria y no se almacena en disco; no se transmite a servidores externos.

#### HU-24 — Que el sistema no vuelva lento mi computador

**Historia:** Como **usuario final**, quiero que el sistema funcione sin volver lento mi computador ni congelar mi pantalla, para poder trabajar con normalidad mientras me monitorea.

**Criterios de aceptación:**

- **Dado que** tengo abiertas mis aplicaciones habituales (navegador, documentos, videollamada), **cuando** el sistema me monitorea durante 30 minutos, **entonces** mi computador responde con normalidad y el panel no se congela.
- **Dado que** se hacen las pruebas de rendimiento, **cuando** se mide el uso de procesador y memoria, **entonces** los valores quedan documentados en el informe.
- **Caso de error:** **Dado que** mi computador está muy exigido, **cuando** el uso de recursos del sistema sube demasiado, **entonces** el sistema reduce su frecuencia de análisis para no afectar mi trabajo y me lo indica.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Fase 3
- **Objetivo relacionado:** Todos los objetivos
- **Nota técnica (para el equipo):** En el PC se ejecutan la visión artificial, el panel y el cliente MQTT; el ESP32 solo lee los sensores y publica (cambio por el ajuste del docente).

#### HU-25 — Validar el sistema con usuarios de prueba

**Historia:** Como **integrante del equipo de pruebas**, quiero probar el sistema en distintas condiciones (con y sin lentes, con buena y poca luz) y comparar sus resultados con un conteo manual, para confirmar que cuenta bien mis parpadeos y que los avisos son realmente útiles.

**Criterios de aceptación:**

- **Dado que** participo en una sesión de prueba, **cuando** el sistema cuenta mis parpadeos mientras otra persona los cuenta a mano, **entonces** se registra la diferencia y se calcula la precisión.
- **Dado que** terminan las pruebas con varios usuarios, **cuando** se consolidan los resultados, **entonces** quedan en el informe final, incluyendo mi opinión sobre la utilidad de los avisos.
- **Caso de error:** **Dado que** la precisión queda por debajo del 85 %, **cuando** se analizan los resultados, **entonces** se identifican las causas (luz, lentes, posición) y se ajusta o recalibra el sistema antes de la entrega.

- **Tipo de requisito:** Explícito
- **Prioridad (MoSCoW):** Must
- **Fase / Hito:** Pruebas
- **Objetivo relacionado:** Todos los objetivos

## 5. Product Backlog priorizado (MoSCoW)

| ID | Historia de usuario | Épica | MoSCoW | Justificación | Fase |
|---|---|---|---|---|---|
| HU-01 | Activar la cámara de mi computador | E1 | Must | Sin cámara no hay detección; es la base de todo el sistema. | Fase 1 |
| HU-02 | Reconocer cuándo estoy frente a la pantalla | E1 | Must | Evita contar parpadeos cuando no hay nadie o no se ven los ojos. | Fase 1 |
| HU-03 | Contar mis parpadeos con exactitud | E1 | Must | Es el objetivo central del proyecto (precisión ≥ 85 %). | Fase 1 |
| HU-04 | Ver mi frecuencia de parpadeo | E1 | Must | Es la métrica principal que usa el motor para detectar fatiga. | Fase 1 |
| HU-05 | Ajustar el sistema a mi forma de parpadear | E1 | Should | Mejora mucho la precisión y es un requisito latente, pero el sistema funciona con un umbral por defecto. | Fase 1 |
| HU-06 | Detectar parpadeos incompletos | E1 | Could | Enriquece el análisis, pero no es necesaria para cumplir los objetivos. | Backlog |
| HU-07 | Medir mi tiempo continuo frente a la pantalla | E2 | Must | Necesaria para la regla 20-20-20 y los avisos por tiempo. | Fase 1 |
| HU-08 | Reiniciar el contador tras una pausa real | E2 | Should | Evita avisos innecesarios tras un descanso real; sin ella el sistema aún funciona. | Fase 3 |
| HU-09 | Medir la luz de mi espacio de trabajo | E3 | Must | Objetivo 2 del Acta; variable básica del motor de decisión. | Fase 2 |
| HU-10 | Medir la temperatura y la humedad de mi espacio | E3 | Must | Cambio solicitado por el docente; completa las condiciones ambientales. | Fase 2 |
| HU-11 | Ver los datos de mi ambiente casi al instante | E3 | Must | Sin datos casi instantáneos el motor no puede usar el ambiente (latencia < 2 s). | Fase 2 |
| HU-12 | Seguir protegido aunque falle el sensor o el Wi-Fi | E3 | Should | Requisito latente; evita que una falla deje al usuario sin avisos (riesgos 2 y 5). | Fase 2 |
| HU-13 | Evaluar mi estado combinando todas las medidas | E4 | Must | Es el núcleo del Objetivo 3: avisos basados en varias variables. | Fase 3 |
| HU-14 | Recibir la recomendación 20-20-20 | E4 | Must | Es la recomendación principal y explícita del Acta. | Fase 3 |
| HU-15 | Recibir un aviso cuando parpadeo poco | E4 | Must | Es la prevención basada en parpadeo, que diferencia al proyecto de un simple temporizador. | Fase 3 |
| HU-16 | Recibir un aviso si la luz no es adecuada | E4 | Should | Recomendación del Acta; no bloquea el funcionamiento básico. | Fase 3 |
| HU-17 | Recibir un consejo si el aire está seco o incómodo | E4 | Should | Aprovecha los nuevos sensores; valiosa, pero secundaria frente a parpadeo y tiempo. | Fase 3 |
| HU-18 | Ajustar los avisos a mi gusto | E4 | Should | Requisito latente clave para que el usuario no abandone el sistema; hay valores por defecto. | Fase 3 |
| HU-19 | Silenciar los avisos cuando no puedo interrumpirme | E4 | Should | Requisito latente que evita interrupciones; la versión inicial puede ser manual. | Fase 3 |
| HU-20 | Ver mis métricas en un panel | E5 | Must | Es la forma en que el usuario ve y usa todo lo demás (Objetivo 3). | Fase 4 |
| HU-21 | Recibir el aviso «Descansa tus ojos» | E5 | Must | Es la entrega de la alerta preventiva; sin ella el sistema no genera valor. | Fase 4 |
| HU-22 | Consultar el resumen de mi jornada | E5 | Could | Ayuda a validar mejoras, pero no es esencial para la primera versión. | Fase 4 |
| HU-23 | Proteger mi privacidad | E6 | Must | Restricción explícita del cliente y del Acta (privacidad). | Fase 1 |
| HU-24 | Que el sistema no vuelva lento mi computador | E6 | Must | Restricción explícita; un sistema lento sería abandonado por el usuario. | Fase 3 |
| HU-25 | Validar el sistema con usuarios de prueba | E6 | Must | Necesaria para demostrar los criterios de evaluación y entregar el informe final. | Pruebas |

**Resumen:** Must: 16 · Should: 7 · Could: 2 · Won't: 4.

**Won't have (fuera de esta versión, según el Acta):**

- Diagnóstico, tratamiento o detección de enfermedades oculares.
- Grabación, almacenamiento o transmisión del video del usuario.
- Modelos de inteligencia artificial complejos en la nube o con procesamiento externo.
- Fabricación industrial de un producto comercial o carcasa personalizada.

## 6. Uso de las historias en Scrum

| Ceremonia | Cómo el equipo usa las historias | Quién participa |
|---|---|---|
| **Refinement** | El PO presenta las historias candidatas del backlog; el equipo pregunta, ajusta los criterios Dado/Cuando/Entonces, divide las historias grandes y las estima. El PO reajusta la prioridad MoSCoW con lo aprendido. | PO, Development Team, SM |
| **Sprint Planning** | El equipo toma del tope del backlog las historias Must que caben en el sprint (por ejemplo, HU-01 a HU-04 en la Fase 1), define el objetivo del sprint y las divide en tareas. | PO, Development Team, SM |
| **Sprint Review** | El equipo demuestra las historias terminadas (por ejemplo, contar parpadeos en vivo para HU-03). El PO verifica cada criterio de aceptación, incluido el caso de error, y **acepta o rechaza** la historia. Los comentarios de usuarios de prueba y docente entran al backlog. | PO, Development Team, usuarios de prueba, docente |

## 7. Trazabilidad con los riesgos del Acta

La numeración coincide con la matriz de riesgos del Acta de Constitución. La columna **P / I** replica la probabilidad e impacto registrados allí.

| Riesgo del Acta | P / I | Historias relacionadas | Responsable |
|---|---|---|---|
| **1.** Falsos positivos o negativos en la detección de parpadeos por mala iluminación o posición frente a la cámara del PC | Media / Alto | HU-02, HU-03, HU-05, HU-25 | Desarrollador Principal (Visión Artificial) |
| **2.** Caída o mala configuración del broker MQTT en el PC | Media / Alto | HU-11, HU-12 | Desarrollador IoT |
| **3.** Aumento de la latencia al integrar todos los módulos | Media / Medio | HU-11, HU-12, HU-24 | Arquitecto de Software |
| **4.** Baja precisión inicial del motor de decisión basado en reglas fijas | Media / Medio | HU-13, HU-15, HU-18 | Gerente del Proyecto |
| **5.** Fallas físicas en el cableado, en el sensor BH1750 o SHT31 | Baja / Medio | HU-09, HU-10, HU-12 | Desarrollador IoT |

**Nota sobre los umbrales:** los valores de umbral (parpadeos por minuto, tiempo de exposición, rango de luxes, temperatura y humedad) se definirán y ajustarán durante las pruebas con usuarios, de acuerdo con las reglas del motor de decisión y la regla 20-20-20.
