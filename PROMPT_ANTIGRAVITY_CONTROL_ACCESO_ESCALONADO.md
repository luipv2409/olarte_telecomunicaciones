# PROMPT MAESTRO PARA ANTIGRAVITY — Control de acceso y conteo de personas por etapas

> **Instrucción para el agente Antigravity:** actúa como arquitecto de software, desarrollador de backend, especialista en ESP32-S3/IoT y pruebas de integración. **Implementa el proyecto de manera incremental y entrega archivos completos listos para revisar; NO cargues firmware en la placa ni ejecutes cambios en el hardware.** No asumas que un componente está conectado o que un hito funciona hasta que el usuario lo confirme.

## 0. Contexto validado (no reinventar)

Se está construyendo un prototipo/MVP de **control de acceso de personas a un recinto**. La **ESP32-S3 N16R8** es el controlador local: lee sensores, decide estados seguros de actuadores bajo reglas definidas y se comunica por Wi-Fi con el backend. El backend aporta persistencia, autorizaciones, monitoreo, reportes y análisis de imágenes. Se requiere una evolución **escalonada: primero un sensor, después integrar los demás uno por uno**.

Datos comprobados previamente:

- Placa: ESP32-S3 N16R8, 16 MB Flash y 8 MB PSRAM **detectadas correctamente** en Arduino IDE.
- Cámara: OV5640 por cinta FPC, placa con inscripción `V1695 127294G_Y1127_231016 CAMERA SD CARD PSRAM`.
- Firmware de cámara funcional: ejemplo ESP32 `CameraWebServer`, con `board_config.h` seleccionando `CAMERA_MODEL_ESP32S3_EYE` y su archivo original `camera_pins.h`. **Esta selección fue probada en esta placa y funciona**, aunque no constituye identificación comercial del modelo.
- Comunicación serie validada por puerto físico **USB-UART**, monitor 115200; `ESP32S3 Dev Module`, `USB CDC On Boot = Disabled`, `PSRAM = OPI PSRAM`, `Flash Size = 16MB`. El número COM varía según el equipo.
- Red Wi-Fi de trabajo: SSID `JAPON`. **No incluir ni publicar la contraseña** en código, documentos ni repositorio: tomarla de configuración local del usuario.
- La cámara permite vista web y capturas JPEG. A resoluciones altas, como 3 MP, hubo pantalla negra: **no prometer streaming estable de 3/5 MP**; medir capturas individuales y limitar streaming a resoluciones estables.
- Ya se solicitó un proyecto con **Docker local, panel web, backend y conteo visual de personas**, con análisis local YOLO y posible integración con API de DeepSeek. El uso de DeepSeek es **opcional, bajo demanda y sujeto a verificar soporte actual del modelo de entrada de imágenes**; no enviar fotogramas externos sin consentimiento y configuración expresa.

## 1. Inventario del documento aportado

Respetar estas piezas como **lista de referencia**, sin presuponer que todas estén conectadas o compradas:

| Área | Componente | Cantidad del documento | Notas |
|---|---|---:|---|
| Alimentación | LM2596 reductor 3 A | 1 | Ajustable, previsto para 5 V |
| Alimentación | Adaptador de pared DC 9/12 V 2 A | 1 | Fuente comercial segura |
| Alimentación | Jack DC hembra a bornera | 1 | Entrada de alimentación |
| Alimentación | Condensador electrolítico 16/25 V | 1 | Ayuda ante transitorios; verificar capacidad y polaridad |
| Identificación | RFID RC522 + tarjeta/llavero | 1 | Señales a 3,3 V; UID no es autenticación robusta por sí sola |
| Barrera | Servo SG90 o MG90S 180° | 1 | Sólo para maqueta/torniquete de demostración |
| Detección | Infrarrojos FC-51 o TCRT5000 | **2 previstos, sólo 1 disponible ahora** | No simular que existen dos físicamente |
| Alerta | Buzzer activo 5 V | 1 | Requiere circuito de accionamiento adecuado |
| Alerta | 2N2222A + resistencia | 1 | Driver buzzer; revisar corriente y diodo si carga inductiva |
| Indicadores | LED rojo y LED verde + resistencias | 2 | Señalización |
| Montaje | Protoboard 830 puntos | 1 | Exclusivamente pruebas de baja potencia |
| Montaje | Cables jumper | 1 juego | Cableado y pruebas |

**Regla crucial:** sólo hay **UN sensor infrarrojo disponible** hoy. No se puede inferir con fiabilidad **dirección de paso (entrada/salida)** usando únicamente ese sensor. Un disparo IR indica presencia/interrupción en un punto, **no prueba entrada ni salida, ni identifica individuos**. El conteo de ocupación con la cámara tampoco equivale a contar cruces de un umbral. Diferenciar siempre `personas_visibles`, `eventos_ir`, `accesos_autorizados`, `pasos_confirmados` y `ocupacion_estimada`.

## 2. Restricciones absolutas de ejecución y preservación

1. **NO** conectarse a los puertos COM, USB-UART o USB-OTG; **NO** compilar, flashear, reiniciar, actualizar OTA ni ejecutar `esptool`, `arduino-cli upload` o acciones equivalentes sobre el ESP32. **El usuario subirá manualmente cada sketch desde Arduino IDE.** Entregar código, guía, capturas esperadas y criterios de aprobación.
2. **NO** detener, reiniciar, borrar, reconfigurar ni modificar contenedores, imágenes, redes, volúmenes o bases de datos Docker de otros proyectos. **NO** ejecutar `docker compose down` sobre proyectos ajenos ni comandos de limpieza global (`docker system prune`, etc.).
3. **NO** ocupar o reasignar puertos existentes. Prever `HOST_HTTP_PORT` configurable y verificar disponibilidad antes de proponer cualquier arranque. Usar nombre de proyecto Compose explícito y único (p. ej., `recinto-control`) y nombres/volúmenes/redes aislados. **No iniciar contenedores ni reservar puertos automáticamente**: entrega instrucciones y espera autorización del usuario.
4. **NO** abrir o accionar automáticamente una puerta real en pruebas. El servo es **sólo actuador de maqueta**; para recinto real se requeriría evaluación de seguridad eléctrica, evacuación, apertura de emergencia y normas locales. Ante incertidumbre, fallo de red, reinicio, lectura inválida o comando caducado, no permitir un desbloqueo inesperado. Nunca bloquear vías de evacuación.
5. **NO** poner la clave de Wi-Fi o DeepSeek en Git, documentación, logs, UI ni firmware compartido. Proveer `.env.example` con valores ficticios y, si corresponde, `secrets.h.example` ignorado por Git. Nunca pedir que copien secretos en un prompt público.
6. **NO** asumir GPIO o pines de alimentación sin verificar el pinout específico de la ESP32-S3 V1695 y los GPIO ya ocupados por OV5640/PSRAM/flash/microSD. Presentar una **tabla de asignaciones GPIO propuesta con estado POR VALIDAR**, sin conectar actuadores potencialmente conflictivos hasta confirmación.
7. No entregar código parcial, botones falsos ni mocks como si fueran hardware probado. Etiquetar datos simulados y los datos reales. No automatizar acciones destructivas.

## 3. Objetivo funcional y arquitectura

Diseñar un sistema con estas responsabilidades:

- **ESP32-S3 (cerebro local):** firmware modular con máquinas de estados de presencia IR, RFID, solicitud de autorización, control seguro de servo (cuando llegue su etapa), indicadores y alarmas, adquisición de imágenes OV5640 y telemetría. Debe poder operar en modo degradado sin una respuesta insegura al perder Wi-Fi/backend.
- **API local robusta:** Python 3 / FastAPI, validación estricta, autenticación entre dispositivo-servidor, control de permisos, límite de tasa, idempotencia, trazabilidad de eventos, estados del equipo, health checks, comandos con expiración y auditoría.
- **Base de datos:** PostgreSQL en servicio Docker aislado (o almacenamiento temporal mínimo solo en las primeras pruebas). Usar migraciones Alembic, transacciones para impedir doble registro de una misma entrada, restricciones únicas y marcas de tiempo UTC. Definir claramente persistencia de conteos versus lecturas crudas.
- **Servicio de visión:** YOLO local para contar **personas actualmente visibles en un fotograma** con umbral de confianza configurable. Si en futuras etapas se requiere contar cruces/dirección, diseñar seguimiento temporal y región/línea virtual, con calibración específica de escena; no afirmar precisión sin evaluación.
- **DeepSeek:** adaptador desacoplado, opcional y apagado por defecto, para interpretación visual puntual si la API y el modelo elegido realmente admiten imágenes; manejar límites, latencias, coste, consentimiento y fallos de API. No usar una respuesta generativa como único factor para abrir una puerta.
- **Panel web:** estado del ESP32, último fotograma, conteo visible y timestamp, historial de autorizaciones/eventos, estado de sensor, alarmas, errores, conectividad, y distinción clara entre simulación y hardware confirmado. El panel nunca sustituye enclavamientos locales.
- **Red:** ESP32 y PC Docker en misma LAN, IP o nombre configurable (`ESP32_BASE_URL`); servir panel en una interfaz local elegida explícitamente. API autenticada; minimizar exposición; documentar firewall y separación LAN/internet. No confundir `localhost` del contenedor con la dirección de la ESP32.

Diagrama conceptual:

```text
[1 IR hoy] -> [ESP32-S3 + OV5640] --Wi-Fi/LAN--> [API FastAPI / Docker]
                     |                         |-- PostgreSQL
                     |                         |-- YOLO local (fotogramas)
                     |                         |-- DeepSeek opcional, bajo demanda
                     |                         `-- Panel web / auditoría
              [RFID / LED / buzzer / servo: fases posteriores]
```

## 4. Plan de entregas incrementales y puertas de aprobación

**Trabajar en una fase a la vez.** Entregar cada fase con firmware completo actualizado, backend/migraciones de esa fase, diagramas de conexiones verificados o expresamente pendientes, pruebas y checklist. **Detenerse y esperar aprobación del usuario antes de pasar físicamente a la siguiente.** Puede preparar esqueletos de fases futuras, pero sin activarlas ni afirmar que están probadas.

### Fase 0 — Línea base y entorno (sin sensores conectados)

- Inventariar estructura de proyecto y puertos Docker activos mediante **instrucciones de inspección no invasivas**, sin alterar nada; identificar un puerto libre sólo cuando el usuario lo confirme.
- Mantener documentación exacta del firmware CameraWebServer funcional, sus archivos originales y configuración Arduino. Preparar copia versionada, no sobrescribir sin permiso.
- Proveer `docker-compose.yml`, `.env.example`, `Dockerfile`, API mínima, `/health`, `/ready`, pruebas y README; **sin desplegar automáticamente**.
- Probar con datos sintéticos etiquetados. Documentar contratos `device_id`, `event_id`, `timestamp`, `sensor_type`, `event_type` y seguridad.
- **Criterio de aprobación:** API y panel se pueden levantar manualmente en puerto libre; ninguno de los contenedores existentes cambió; firmware base preservado.

### Fase 1 — MVP: conectar y probar el ÚNICO sensor infrarrojo

- Elegir mediante verificación física si el módulo adquirido es **FC-51 o TCRT5000**, su pinout, tensión de alimentación, lógica de salida y umbral ajustable. No conectar señales de 5 V directamente a un GPIO ESP32 de 3,3 V.
- Proponer un **GPIO libre confirmado** que no choque con la cámara, USB, flash, PSRAM, SD u otros periféricos. Si se desconoce, **pedir fotografía/serigrafía o pinout** antes del cableado.
- Entregar sketch Arduino completo que conserve las funcionalidades de cámara sólo si está comprobada la compatibilidad de GPIO/recursos. Lectura no bloqueante con filtrado de rebotes, detección de cambio de estado, ventana antirrepetición, marcas de tiempo y diagnóstico por Serial.
- Transmitir `IR_INTERRUPTED` / `IR_CLEARED` al backend con cola acotada y reintentos idempotentes. No registrar cientos de eventos por un objeto quieto. Soportar pruebas desconectado.
- Backend recibe, valida, almacena y visualiza eventos IR y salud del dispositivo. **No llamar a este evento una entrada confirmada.** Mostrar `cruces_confirmados = no disponible` con un solo IR.
- **Criterio de aprobación:** aproximar objeto -> un cambio válido; retirarlo -> otro cambio; API registra una vez por `event_id`; no afecta video/captura; reinicios y pérdida de Wi-Fi tratados.

### Fase 2 — RFID RC522: autorización lógica, SIN accionar puerta

- Integrar RC522 con asignación SPI validada contra cámara/SD y niveles 3,3 V. Preparar lista de credenciales de prueba desde backend.
- Firmware envía solicitud autenticada; backend emite decisión de permiso con motivo y caducidad. UID RFID es identificador demostrativo, **no credencial segura única**; prever credenciales más robustas en producción.
- Correlacionar lectura de tarjeta y activación IR durante ventana temporal parametrizable. Estados: `IDLE`, `CREDENTIAL_READ`, `AUTH_PENDING`, `AUTHORIZED_WAITING_PASSAGE`, `PASSAGE_CANDIDATE`, `EXPIRED`, `DENIED`, `FAULT`.
- Evitar duplicados por idempotencia y expiración; registrar denegaciones sin abrir nada.
- **Criterio:** tarjeta autorizada/denegada y evento IR muestran trazabilidad, sin servomotor.

### Fase 3 — Señalización: LED verde, LED rojo y buzzer

- Integrar cada periférico **uno por uno**, primero LEDs con resistencias apropiadas, luego buzzer con transistor/control de corriente. Confirmar polaridad, consumo y tensión.
- Patrones claros para autorizado, denegado, sensor activo y error; estados temporizados no bloqueantes (`millis()`), nunca `delay()` largos que impidan vigilancia.
- **Criterio:** señales correctas, sin resets por alimentación, sin alarmas infinitas o espurias.

### Fase 4 — Servo SG90/MG90S, sólo maqueta

- Preparar esquema de alimentación regulada, tierras comunes donde corresponda y **servo separado de la alimentación lógica crítica**; revisar si LM2596/fuente suministran corriente suficiente. No conectar servo a pin 3,3 V del ESP32. Verificar polaridad de capacitor y tensión con multímetro antes de energizar.
- Ejecutar pruebas sin carga mecánica, con topes y límites de movimiento, tiempo máximo de accionamiento y retorno a estado definido. **No conectar todavía a un mecanismo real de evacuación/seguridad.**
- Agregar estados `CLOSED`, `OPENING`, `OPEN_FOR_PASSAGE`, `CLOSING`, `FAULT` con watchdog y orden única vigente; no reabrir por reenvío de comando.
- **Criterio:** pruebas manuales de autorizado/denegado, servo repetible, sin reinicios ni activación espontánea tras reset/red caída.

### Fase 5 — Cámara y análisis visual de personas

- Incorporar capturas periódicas **sin romper el CameraWebServer ya funcional**. Mostrar conteo de personas visibles con timestamp/confianza; evitar confundir foto congelada con feed en vivo.
- Probar resoluciones por separado y registrar latencia/errores/FPS. Para 3 MP/5 MP, preferir captura individual de alta resolución si streaming falla; reducir calidad/resolución cuando sea necesario, sin prometer que Docker solucione fallos de captura del ESP32.
- Procesar en Docker con YOLO CPU en primera versión; permitir adaptador GPU opcional, no obligatorio. No bloquear la API ante inferencia lenta; limitar colas y frecuencia.
- Usar DeepSeek visual sólo tras confirmar compatibilidad de modelo/API, con secreto desde entorno y llamada manual/autorizada; nunca como fuente única de autorización. Respetar privacidad: evitar reconocimiento facial/identificación biométrica, retención limitada, acceso restringido a imágenes.
- **Criterio:** el panel distingue conteo en campo de visión, evento IR y accesos autorizados; mediciones reproducibles.

### Fase 6 — Segundo infrarrojo (futuro, NO disponible hoy)

- Dejar la interfaz de software preparada pero deshabilitada. Sólo cuando el usuario disponga del segundo IR: colocarlo en secuencia física validada para inferir dirección A→B / B→A, ventanas temporales, inversión de trayectoria y paso simultáneo.
- Evaluar falsos positivos, colas y solapamientos; mantener incertidumbre cuando la secuencia no sea inequívoca.
- **Criterio:** ensayos reales de entrada/salida y métricas de precisión; entonces habilitar `pasos_confirmados` y `ocupacion_estimada` bajo reglas validadas.

### Fase 7 — Endurecimiento y escalado

- Usuarios/roles, autenticación de dashboard, claves de dispositivo rotables, TLS vía proxy local si corresponde, auditoría, backups/restauración, límites por IP y por dispositivo, secretos fuera del repo, migraciones y pruebas automáticas.
- Observabilidad: logs estructurados sin credenciales, métricas, estado online/offline, último contacto, latencia de captura, consumo de memoria, tiempo de inferencia y alertas por fallos.
- Docker Compose reproducible con healthchecks, límites de recursos, volúmenes de datos propios, reinicios controlados y documentación de actualización sin afectar otros proyectos.
- Pruebas de reconexión, interrupciones de energía, datos repetidos/fuera de orden, timeouts, sensor permanentemente bloqueado, modelo de IA caído, backend desconectado y dispositivos no autorizados.

## 5. Modelo lógico mínimo solicitado

Diseñar y migrar entidades semejantes a:

- `devices`: identificador, firmware_version, estado, último contacto.
- `sensors`: device_id, tipo, etiqueta, gpio_verificado, habilitado.
- `sensor_events`: event_id único por dispositivo, tipo, estado, timestamp_dispositivo, timestamp_servidor, metadata validada.
- `credentials` / `access_policies`: credencial de prueba, permiso, caducidad; no guardar secretos en claro.
- `access_attempts`: solicitud, decisión, causa, correlación con eventos IR, expiración.
- `actuator_commands`: command_id único, expiración, estado, acuse, auditoría y reintentos seguros.
- `vision_observations`: momento de captura, personas_visibles, confianza, resolución, origen del modelo, retención configurable.
- `system_audit`: quién, qué, cuándo, resultado, sin credenciales.

Documentar reglas para evitar doble contabilización y para que la ausencia de confirmación física no se convierta en una entrada validada. No almacenar imágenes de forma permanente por defecto.

## 6. Contrato API sugerido (versionado y verificable)

Especificar OpenAPI y pruebas de integración para rutas como:

```text
GET  /health
GET  /ready
POST /api/v1/devices/{device_id}/heartbeat
POST /api/v1/devices/{device_id}/events
POST /api/v1/access/evaluate
GET  /api/v1/devices
GET  /api/v1/events
GET  /api/v1/dashboard/summary
GET  /api/v1/vision/latest
POST /api/v1/vision/analyze-on-demand
```

Requerir tokens de dispositivo, eventos idempotentes, validación de tamaño/tipos, paginación, códigos de error y permisos por rol. Comandos de actuador futuros deben caducar y verificarse localmente; no exponer control del servo a endpoints públicos sin autenticación.

## 7. Entregables obligatorios por fase

1. Árbol completo de archivos del proyecto, código real de backend, frontend, firmware `.ino`, configuración de ejemplo, migraciones y pruebas; **no seudocódigo**.
2. `README.md` con Windows + Docker Desktop, requisitos, ejecución MANUAL, configuración de IP de ESP32 y puerto libre, cómo consultar logs y cómo detener **sólo este** proyecto.
3. `HARDWARE.md`: conexiones verificadas, tabla de GPIO con conflictos y estado de validación, alimentación segura por módulos y precauciones.
4. `FASES.md`: fases con estados `PENDIENTE`, `LISTO PARA PRUEBA`, `VALIDADO POR USUARIO`, además de evidencias y riesgos.
5. `TESTING.md`: comandos de pruebas sin hardware, casos de aceptación con hardware e instrucciones del monitor serie; sin ejecutar cargas.
6. `.env.example`, `.gitignore` y plantillas de secretos; contraseñas y API key ausentes del repositorio.
7. `docker-compose.yml` con proyecto aislado, puertos parametrizables **sin valores que se den por libres**, sin `network_mode: host`, sin nombres que colisionen y sin afectar proyectos existentes.
8. `CHANGELOG.md` que especifique cambios por etapa, archivos afectados, resultados observados y pendientes.
9. Resumen final con **qué está implementado, qué está simulado, qué necesita cablearse y qué debe hacer manualmente el usuario**.

## 8. Orden de trabajo exigido al agente

1. Leer este prompt y la lista de componentes, identificar incompatibilidades y preguntas bloqueantes **sin inventar conexiones**.
2. Revisar de forma no invasiva la organización del proyecto y los puertos existentes; presentar estrategia para elegir un puerto libre sin tocar Docker actual.
3. Proponer árbol de carpetas y contrato de eventos; crear primero **Fase 0** y **Fase 1 (un IR)** en archivos separados y con integración progresiva.
4. Entregar el firmware de fase 1 para que **el usuario lo cargue manualmente** en Arduino IDE y facilitar procedimiento de prueba en monitor serie. No cargarlo tú.
5. Esperar resultado real del usuario. **No marcar fase 1 como validada antes de recibirlo.**
6. Tras autorización del usuario, implementar **Fase 2 (RC522)**, luego **Fase 3 (indicadores)**, **Fase 4 (servo de maqueta)**, **Fase 5 (visión/IA)**, **Fase 6 (segundo IR futuro)** y **Fase 7 (robustez)**, siempre con pruebas y evidencia por fase.
7. Nunca fusionar lógica de visión de personas con decisión de abrir el actuador de forma automática e incontrolada.

## 9. Primer mensaje esperado de Antigravity

Antes de escribir archivos, entrega una respuesta breve con: (a) alcance MVP con **un único IR**, (b) módulos disponibles vs. pendientes de validación, (c) propuesta de API y Docker aislado, (d) mapa GPIO **pendiente de validación**, (e) archivos a crear en Fase 0/Fase 1, y (f) cualquier confirmación indispensable, especialmente modelo exacto del IR, GPIO seguros y puerto Docker. Después comienza sólo el código que no requiera suposiciones eléctricas.

**PRIORIDAD ABSOLUTA:** preservar el ESP32 funcional, no interferir con Docker, no desplegar ni cargar nada automáticamente, entregar cada versión terminada y comprobable por el usuario, y avanzar de un solo sensor infrarrojo hasta el sistema integral por etapas.
