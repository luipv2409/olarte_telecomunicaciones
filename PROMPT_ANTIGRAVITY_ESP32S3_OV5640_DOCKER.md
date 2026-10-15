# PROMPT MAESTRO PARA ANTIGRAVITY
## ESP32-S3 N16R8 + OV5640 + conteo de personas con Docker local y DeepSeek

Actúa como ingeniero experto en ESP32-S3, visión por computadora, Python/FastAPI, Docker y redes locales. **Tu trabajo consiste en crear y entregar el proyecto COMPLETO, sin ponerlo en marcha.** No me entregues únicamente recomendaciones o pseudocódigo: entrega archivos terminados, documentación y pasos para que **yo mismo** despliegue el sistema y cargue el ESP32 manualmente.

### 1. Contexto real, ya verificado

- Placa ESP32-S3 N16R8, serigrafía V1695, cámara OV5640 de 5 MP conectada mediante cinta FPC, ranura microSD y puertos USB-UART y USB-OTG.
- Arduino IDE: placa **ESP32S3 Dev Module**, Flash **16 MB**, **OPI PSRAM 8 MB**, USB CDC On Boot **Disabled** usando USB-UART, monitor serie **115200**, partición con APP de al menos 3 MB.
- El monitor serie confirmó `FLASH: 16 MB`, `PSRAM: 8 MB` y funcionamiento correcto.
- Ya funcionó la captura y visualización Wi-Fi con el ejemplo oficial **CameraWebServer** y la selección `#define CAMERA_MODEL_ESP32S3_EYE` en `board_config.h`, incluida la correspondencia de pines desde `camera_pins.h`. **No cambiar ese mapeo GPIO funcional por suposiciones**; la placa física dice V1695, no ESP32S3-EYE.
- Wi-Fi: SSID `JAPON`. La contraseña real y la API key NO se deben incluir en el proyecto, el prompt, logs ni documentación. Configurarlas de forma local y segura.
- CameraWebServer entrega páginas/capturas accesibles desde la IP local del ESP32; probar endpoint `/capture`. El streaming MJPEG puede estar en `:81/stream` dependiendo de la implementación.
- Hay un fallo pendiente: al cambiar el video a **P 3MP (864×1564)**, la imagen se vuelve negra. No asumir que está solucionado. Favorecer video/vista previa a resolución estable y fotografías de alta resolución bajo demanda; el servidor no repara un fallo que ocurre antes de capturar el JPEG.

### 2. Meta del sistema

Implementa en una carpeta independiente una solución donde el ESP32 capture imágenes y una aplicación Python dentro de Docker en mi PC Windows las consulte **por la red local**. Un detector ligero tipo YOLO, ejecutado localmente, debe contar **personas visibles en cada fotograma** y dibujar recuadros con confianza. Una interfaz web mostrará la última imagen, conteo estimado, actualización y estado de cámara/servidor. Se podrá usar la API de DeepSeek, a pedido del usuario, para una descripción o segunda estimación visual **únicamente si su API y modelo oficiales admiten realmente entrada de imágenes**.

**No confundas conteo de personas presentes en el encuadre con conteo acumulado de ingresos/salidas.** No implementar reconocimiento facial ni identificar personas.

### 3. REGLAS ABSOLUTAS: no interferir con Docker ni los puertos existentes

1. **NO EJECUTAR** `docker run`, `docker compose up`, `docker stop`, `docker restart`, `docker rm`, `docker compose down`, `docker system prune` ni comandos que creen, inicien, detengan o modifiquen contenedores, redes, volúmenes, imágenes, proyectos o servicios existentes. **No hacer despliegue automático, ni siquiera de prueba.**
2. **NO abrir, reservar ni publicar puertos de mi PC.** Mi Docker ya aloja otros sistemas en funcionamiento. No suponer que los puertos 80, 443, 3000, 5000, 8000, 8080, etc., están libres.
3. Crear `compose.yaml` con puerto **obligatoriamente configurable**, sin valor de host por defecto: por ejemplo `${APP_BIND_IP:?debes_elegir_IP}:${APP_HOST_PORT:?debes_elegir_puerto}:8000`. Requerir al usuario que seleccione previamente un puerto libre en `.env`.
4. Para acceso solo desde la PC, documentar `APP_BIND_IP=127.0.0.1`. Para acceso desde dispositivos de la misma LAN, documentar uso de **la IP LAN de la PC**, escogida por el usuario, y reglas de firewall limitadas a la LAN. No exponer públicamente el servicio ni usar `network_mode: host` o `privileged: true`.
5. Aislar completamente el proyecto con nombre Compose propio y redes propias. Evitar nombres globales rígidos de contenedores que colisionen; no alterar recursos existentes. No utilizar el socket de Docker del host.
6. Únicamente se permiten comandos de **consulta/solo lectura** como `docker ps` y revisión de puertos, si son necesarios y están disponibles, **sin ningún cambio de estado**. Si no puedes inspeccionar mi máquina, explica cómo podré hacerlo yo.
7. **NO instalar/reconfigurar Docker Desktop, WSL, dependencias del host o firewall** de forma automática. Entregar instrucciones para ejecución manual futura.

### 4. REGLAS ABSOLUTAS: no tocar físicamente ni programar el ESP32

1. **NO cargar/flashear/compilar-y-subir firmware** a la placa. No usar `arduino-cli upload`, `esptool`, PlatformIO upload ni ejecutar scripts de flasheo.
2. **NO abrir puertos COM/USB, no resetear la placa, no detectar puertos seriales automáticamente**, no cambiar drivers o ajustes de Arduino IDE.
3. Entregar, si fuese necesario, un `.ino` **completo y listo para que YO lo copie y suba manualmente**. No sobrescribir el código que ya funciona; cualquier versión nueva debe estar separada y descrita como alternativa opcional.
4. **Preferir no modificar firmware:** obtener imágenes mediante `http://IP_DEL_ESP32/capture` desde el servidor Docker; probar dirección real solo cuando YO haga el despliegue.
5. Si creas firmware opcional, conservar la configuración funcional `CAMERA_MODEL_ESP32S3_EYE`, GPIO correspondientes, OPI PSRAM, XCLK de 20 MHz, y documentar las dependencias del ejemplo Arduino (`board_config.h`, `camera_pins.h`, `app_httpd.cpp` si se usa). Nunca entregar un `.ino` que invoque `startCameraServer()` sin disponer de su implementación.

### 5. Funciones de aplicación

- Backend **FastAPI** (o justificar alternativa), cliente de cámara con URL configurable `ESP32_BASE_URL`, timeouts, reconexión/backoff, mensajes claros y captura periódica de JPEG mediante `/capture`.
- Detección de objetos **local**, modelo ligero YOLO adecuado para CPU, filtrando clase `person`; configurable umbral de confianza y frecuencia (p. ej., cada 2 s). No acumular imágenes indefinidamente ni bloquear el servidor si la cámara se desconecta.
- Panel web local claro: imagen anotada, personas detectadas, fecha/hora de última captura, FPS/frecuencia aproximada, error actual y estado del detector/DeepSeek.
- API propia con endpoints documentados equivalentes a `/health`, `/api/status`, `/api/count`, `/api/snapshot`, `/api/analyze/deepseek`.
- Empezar con resoluciones estables de previsualización; ofrecer foto a 3 MP/5 MP solo cuando la captura individual esté validada. No cambiar resolución del firmware automáticamente durante streaming y no prometer 5 MP fluidos.
- Opcionalmente guardar resultados agregados (marca temporal y cantidad), pero **no guardar fotos permanentemente por defecto**.
- En todos los conteos, indicar que son estimaciones de las personas visibles en la imagen, no registros de identidad ni conteos únicos.

### 6. DeepSeek: integración realista, segura y opcional

- `DEEPSEEK_API_KEY` se lee exclusivamente de variable de entorno dentro del backend; jamás llevar la clave al frontend, repositorio, logs o firmware.
- **Verificar en documentación oficial ACTUAL** si la API de DeepSeek ofrece un modelo/endpoint que acepte imágenes y cuál es su formato real. **No inventar** el nombre de un modelo de visión, un endpoint ni afirmar compatibilidad sin comprobarla.
- Si la entrada de imágenes está soportada, implementar un adaptador para enviar **solo bajo acción explícita del usuario** una captura y pedir conteo/explicación; validar JSON y etiquetar el resultado como estimación de DeepSeek.
- Si no está soportada para la API/modelo disponible, dejar la integración deshabilitada claramente con mensaje honesto; mantener el conteo funcional con YOLO local. Diseñar el adaptador para que en el futuro pueda utilizarse un servicio visual compatible.
- No enviar imágenes automáticamente a servicios externos, ni consumir tokens en cada fotograma; agregar control de timeout, fallo y costos.
- Minimizar tratamiento de datos personales, no usar identificación facial y advertir cuándo se enviaría una imagen fuera de la LAN.

### 7. Archivos COMPLETOS que debes crear

Crear la carpeta **`esp32-vision-personas/`** aislada de mis otros proyectos:

```text
esp32-vision-personas/
├── README.md
├── compose.yaml
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
├── requirements.txt             # o pyproject.toml con versiones compatibles
├── app/
│   ├── main.py
│   ├── config.py
│   ├── camera_client.py
│   ├── detector.py
│   ├── deepseek_client.py
│   ├── templates/
│   └── static/
├── firmware/
│   ├── README.md
│   └── CameraWebServer_ESP32S3_OV5640.ino   # si se requiere, opcional
├── tests/
│   ├── test_camera_mock.py
│   └── test_count_mock.py
└── docs/
    ├── INSTALACION_WINDOWS_DOCKER.md
    ├── CONFIGURACION_ARDUINO_IDE.md
    ├── ARQUITECTURA.md
    └── SOLUCION_PROBLEMAS.md
```

Entregar archivos **reales y terminados**, no placeholders en las partes críticas. Configuración de ejemplo SIN secretos:

```dotenv
APP_BIND_IP=
APP_HOST_PORT=
ESP32_BASE_URL=
CAPTURE_INTERVAL_SECONDS=2
DETECTION_CONFIDENCE=0.45
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=
DEEPSEEK_VISION_ENABLED=false
```

No fijar puerto ni IP de la ESP32 sin conocerlos. `.env` real debe quedar fuera de Git.

### 8. Pruebas permitidas y prohibidas

- Puedes revisar el código, analizar sintaxis y preparar **pruebas unitarias con mocks** (sin conexión a cámara real y sin despliegue). Si existe entorno aislado y autorización para ejecutar pruebas locales que no abran puertos, puedes usarlas; en cualquier caso evita efectos sobre otros proyectos.
- **PROHIBIDO** iniciar el contenedor o servidor, ocupar un puerto, tocar proyectos ajenos, cambiar ajustes del sistema, consultar la cámara real sin permiso o subir firmware.
- Prepara pruebas que cubran: imagen JPEG correcta/incorrecta, timeout, Wi-Fi desconectado, conteo vacío, detección de varias personas, falta de API key, respuesta DeepSeek no disponible y errores HTTP.
- Incluye instrucciones para **mi validación manual** en Windows (Docker Desktop): elegir un puerto libre, configurar `.env`, construir y levantar únicamente este proyecto, abrir panel desde LAN y detener solo este proyecto cuando yo lo desee. Advertir antes de cualquier comando que pueda cambiar contenedores.

### 9. Resultado final que espero de Antigravity

Al finalizar, entrégame:

1. Ruta del proyecto completo y enumeración de archivos creados.
2. Resumen técnico del funcionamiento y de los endpoints HTTP.
3. Pasos manuales precisos para seleccionar un puerto que NO esté ocupado, configurar `.env` y levantar el Compose solo cuando **yo** lo autorice.
4. Instrucciones del `.ino` completo (si es necesario) para que **yo** lo cargue en Arduino IDE; si el firmware actual basta, indícalo y no inventes cambios.
5. Estado real y documentado de compatibilidad de imágenes con DeepSeek; si no es viable, entregar alternativa local completamente operativa.
6. Limitaciones de la cámara (especialmente 3 MP), rendimiento CPU, seguridad LAN y privacidad.
7. Confirmación verificable: **«No modifiqué contenedores ni servicios existentes, no abrí ni reservé puertos, no accedí al puerto COM y no cargué firmware al ESP32».** Solo declararlo si es verdad.

**Empieza creando el proyecto en una carpeta independiente. No intentes desplegarlo ni subir código al ESP32. Yo me encargo manualmente de esos pasos.**
