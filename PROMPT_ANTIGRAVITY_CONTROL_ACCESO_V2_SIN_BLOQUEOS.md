# PROMPT OPERATIVO V2 — ANTIGRAVITY: MVP DE CONTROL DE ACCESO ESP32-S3 + OV5640

> **INSTRUCCIÓN PRIORITARIA:** No te limites a responder con arquitectura, preguntas o una propuesta. **CREA LOS ARCHIVOS DEL PROYECTO COMPLETOS Y ENTREGABLES DESDE AHORA**, sin desplegar ni manipular equipos. Avanza en la implementación de Fase 0 y Fase 1 por software. Las dudas de cableado quedan marcadas «PENDIENTE DE VALIDACIÓN» y **no bloquean** el desarrollo del backend, las pruebas automáticas, la documentación ni el firmware preparado. Solo pregunta cuando sea imposible producir software útil sin la respuesta.

## Contexto comprobado

- Equipo: ESP32-S3 N16R8, Flash 16 MB y PSRAM 8 MB, cámara OV5640 con cinta flexible, PCB rotulada `V1695 127294G_Y1127_231016 CAMERA SD CARD PSRAM`.
- Cámara web **ya funcional** con ejemplo oficial ESP32 CameraWebServer, `CAMERA_MODEL_ESP32S3_EYE`, `camera_pins.h` del ejemplo; no cambiar pines funcionales. Arduino IDE: `ESP32S3 Dev Module`, `USB CDC On Boot=Disabled` si USB-UART, `OPI PSRAM`, `Flash Size=16MB`, monitor 115200.
- Wi-Fi local de nombre `JAPON`. Contraseña en secreto local NO en repositorio ni mensajes; generar `secrets.h.example`.
- Cámara con problemas al cambiar a 3MP durante streaming: usar resolución estable para MVP, captura JPEG individual para pruebas, no prometer video 5 MP continuo.
- Existe un servicio Docker ajeno en host `8088` según la información disponible. Su estado actual puede cambiar: **jamás tocarlo**, ni ocupar otros puertos sin verificar.
- **Hardware disponible para Fase 1: un solo sensor infrarrojo** FC-51/TCRT5000 (tipo exacto pendiente de foto). RC522, SG90/MG90S, buzzer 5V con 2N2222, 2 LEDs con resistencias son fases siguientes; segundo IR no está disponible.
- **Alimentación actual**: ESP32-S3 alimentado de manera independiente por su puerto USB-C. Protoboard alimentado por módulo tipo MB102, rotulado `DC 7-12V`, con dos rieles seleccionables a 3.3V/5V. **NO utilizar LM2596 por ahora**. Unión de GND de la ESP32 con GND de protoboard cuando se interconecten señales; no unir positivos de alimentaciones distintas. Exigir verificar con multímetro tensiones/compatibilidad/corriente antes del cableado; servo no se alimentará automáticamente con MB102 hasta evaluar su corriente pico.
- El usuario quiere un **MVP real escalable** para control de entradas de un recinto; ESP32 es el controlador de sensores/actuadores, backend Docker realiza gestión, persistencia, panel y análisis visual. Para puerta real exigir mecanismos de emergencia y revisión de seguridad: servo SG90 solo para maqueta.

## ÓRDENES NO NEGOCIABLES

1. **PROHIBIDO conectar, detectar, flashear, compilar y subir al ESP32 automáticamente**, abrir COM, reiniciar placa, hacer OTA o utilizar esptool/arduino-cli para modificar el dispositivo. Solo entregar ficheros `.ino`, `.h` y manual para **carga manual del usuario en Arduino IDE**. Compilación local estática, si es posible sin hardware, requiere permiso antes de ejecutar programas externos; por defecto solo escribir archivos.
2. **PROHIBIDO ejecutar Docker o alterar cualquier contenedor/imagen/red/volumen/puerto existente**, y prohibido `docker compose up/down`, `docker prune`, reinicios, instalaciones o cambios de firewall sin aprobación explícita. Puede crear `compose.yaml` y scripts/manuales para ejecutar por el usuario. No afirmar despliegue realizado.
3. No asumir que `8089` está libre. El puerto del backend se declara **mediante variable `HOST_HTTP_PORT`**, sin valor fijo que obligue a ocuparlo; `8089` puede ser un EJEMPLO sujeto a comprobación y aprobación manual. PostgreSQL **sin publicar `5432` al host** (solo red interna Compose). No integrar ni cambiar el servicio de `8088` a menos que el usuario lo solicite posteriormente. Proyecto Compose propio `recinto-control`, volúmenes con prefijo e interfaz de red aislada.
4. No inventar GPIO. Extraer primero el mapeo de `camera_pins.h` del proyecto realmente usado si está disponible. Documentar ocupados, reservados de placa y **candidatos sin cablear**. Si falta el pinout exacto, dejar `IR_GPIO` en plantilla sin asignación habilitada y dar instrucciones de validación; **igual entregar backend y firmware base completo parametrizable**.
5. No almacenar contraseñas Wi-Fi, DeepSeek API key ni tokens en Git. Entregar `.env.example`, `.gitignore`, `secrets.h.example`; no imprimir secretos en logs.
6. No contar detección IR como ingreso confirmado. Con 1 IR solo registrar `IR_INTERRUPTED` / `IR_CLEARED` y métricas de presencia; no inferir dirección, identidad ni ocupación real. YOLO cuenta `personas_visibles` del fotograma, NO personas que cruzaron ni aforo total. Separar estos indicadores en API, DB y panel.
7. DeepSeek es **opcional y desactivado por defecto**; antes de activar verificar que el endpoint/modelo contratado realmente acepte imagen y que el usuario autorice enviar la imagen a un proveedor externo. Detección local YOLO para conteo y API externa nunca como único criterio para desbloquear puerta.
8. No esperar otras respuestas para generar software de Fase 0/1. Entregar un trabajo tangible y etiquetar lo que requerirá intervención física. No sustituir una implementación por más preguntas.

## Arquitectura exigida

- Firmware modular ESP32 con `CameraWebServer` funcional, tarea o sondeo no bloqueante IR, debounce por tiempo, detector de flancos, heartbeat hacia backend, envío de eventos de forma idempotente con IDs únicos, timeout HTTP, reintentos limitados y cola acotada. No bloquear servicio de cámara. Prever seguridad ante pérdidas de Wi-Fi.
- FastAPI con OpenAPI y versión `/api/v1`; PostgreSQL, SQLAlchemy, Alembic, validación Pydantic, seguridad de dispositivo por token rotatorio configurable, consultas parametrizadas, índices, timestamps UTC, restricciones únicas por `(device_id,event_id)`, gestión de duplicados y logs de auditoría. Endpoint health.
- Dashboard LAN con estado de cámara, IR, eventos y fecha, estado dispositivo, errores y `personas_visibles` cuando visión esté habilitada. No fingir hardware conectado.
- Contenedor backend Docker Compose aislado; base de datos solo interna; configuración por `.env`; healthchecks y volúmenes persistentes; manual de backup/restauración; arranque solo por usuario.
- Componentes futuros desacoplados: módulo RFID RC522, LED/buzzer, servo maqueta, visión YOLO y DeepSeek bajo demanda, segundo infrarrojo; ninguno activado sin aprobación del usuario.

## Fases y aceptación — avanzar por artefactos, no por respuestas

### FASE 0: Generar estructura y backend listo para levantar MANUALMENTE

Crear carpeta `recinto-control/` con `compose.yaml`, Dockerfile, requirements con versiones compatibles, `.env.example`, `.gitignore`, README, HARDWARE.md, FASES.md, TESTING.md, CHANGELOG.md, servicios FastAPI y PostgreSQL, modelos, migraciones y pruebas. API mínima: `GET /health`, `POST /api/v1/devices/{id}/heartbeat`, `POST /api/v1/devices/{id}/events`, `GET /api/v1/dashboard/summary`. Autenticación, idempotencia y validación real. Preparar pruebas de API/DB que el usuario podrá ejecutar manualmente. No publicar puerto de DB ni tocar Docker.

### FASE 1: Firmware y simulador software de un único sensor infrarrojo

Crear sketch completo `firmware/Fase1_ESP32_IR_Camera/Fase1_ESP32_IR_Camera.ino`, configuración y archivos auxiliares NECESARIOS. Conservar mapa real de cámara y streaming funcional. Gestionar `IR_INTERRUPTED` y `IR_CLEARED`, rebote, pérdida de conectividad y registro autenticado. Como el pin físico del sensor no está validado, diseñar parámetro explícito `IR_GPIO` y modo `IR_ENABLED=false` por defecto; documentar qué se debe validar antes de activarlo, sin GPIO arbitrario. Añadir simulador de eventos desde PC para poder ensayar API, DB y dashboard **sin ESP32 conectado**; datos claramente identificados como simulados. No pretender que el hardware real esté validado.

### FASES SIGUIENTES — solo preparar interfaces, NO activar sin confirmación

2. RC522 RFID y autorización auditada con reglas de expiración y antirrepetición; UID no basta como autenticación segura.
3. LED rojo/verde + buzzer, drivers y comportamiento de errores.
4. Servo para maqueta, alimentación 5V adecuada (MB102 pendiente de verificación), control de tiempos y bloqueo seguro; puerta real requiere hardware apropiado, salida de emergencia sin depender de red ni IA.
5. YOLO local para conteo de personas visibles; DeepSeek opcional para descripción/verificación puntual y con consentimiento.
6. Segundo IR si se adquiere, secuencia A/B para dirección con calibración y antifalsos positivos.
7. Escalabilidad: supervisión, trazas, monitorización, colas, backups, pruebas de carga y pruebas de desconexión.

## Contrato API mínimo

- `POST /api/v1/devices/{device_id}/heartbeat`: identidad autenticada, firmware, timestamp, señal Wi-Fi, estado sensores.
- `POST /api/v1/devices/{device_id}/events`: cuerpo `event_id`, `type` enum, `occurred_at`, `sensor_id`, `metadata`; clave única `(device_id,event_id)`; duplicados no alteran métricas.
- `GET /api/v1/dashboard/summary`: `last_seen`, `online`, `ir_interrupted_count`, `ir_cleared_count`, `personas_visibles` (nullable), `cruces_confirmados` (null), `ocupacion_estimada` (null), y alertas.
- `POST /api/v1/access/evaluate`: contrato preparado, sin autorización efectiva al servo hasta fase aprobada; explícitamente marcado no implementado/inactivo.

## Entregables y modo de responder

1. **Crear archivos reales en el workspace, no solo enumerarlos.** Entregar árbol de archivos y descripción de cada módulo.
2. Escribir todo el firmware como archivo completo listo para abrir en Arduino IDE. Incluir `board_config.h` y la dependencia de `camera_pins.h` / `app_httpd.cpp` que deban conservarse del ejemplo probado. Nunca afirmar que compiló o fue probado en placa sin evidencia.
3. Incluir manual de pruebas de Fase 0/1, expectativas de salida del monitor serie, conexión física **solo después de validar módulo y GPIO** y guía de rollback.
4. Añadir sección `PENDIENTE DE VALIDACIÓN FÍSICA` con preguntas breves acerca de a) tipo exacto de IR y nivel lógico de salida; b) serigrafía de GPIO/pinout real de placa V1695; c) medida de tensiones del MB102 y corriente del servo futuro. Estas preguntas NO impiden entregar software funcional y un simulador.
5. NO hacer peticiones reiteradas de aprobación por elecciones que pueden hacerse seguras por defecto. NO desplegar, cargar firmware, borrar ni reemplazar proyectos existentes.
6. En respuesta final indicar: archivos creados, cómo ejecutarlos **manualmente**, cómo probar con simulador, qué está implementado y qué queda pendiente de conexión/validación física.

**COMIENZA AHORA CREANDO LOS ARCHIVOS DE FASE 0 Y FASE 1. NO RESPONDAS ÚNICAMENTE CON PLANES NI TRES PREGUNTAS.**
