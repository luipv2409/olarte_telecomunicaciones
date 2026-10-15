# MEMORIA TÉCNICA Y REPORTE COMPLETO DEL SISTEMA
## ESP32-S3 N16R8 + OV5640 + SENSOR IR + DOCKER (YOLO LOCAL & CONTROL DE ACCESO)

> **Documento:** Memoria técnica integral y registro histórico del sistema.  
> **Fecha de consolidación:** 15 de Octubre de 2026.  
> **Estado:** Fase 0 y Fase 1 completadas, operativas y validadas en hardware real.

---

## 1. RESUMEN EJECUTIVO Y OBJETIVO DEL SISTEMA

Se ha diseñado, construido y puesto en marcha un sistema distribuido e incremental para el **monitoreo visual y control de acceso a un recinto**.
El sistema integra:
1. **Controlador físico de borde (ESP32-S3 N16R8):** Captura fotogramas continuos mediante cámara **OV5640 de 5 MP** y lee en tiempo real un sensor infrarrojo de proximidad digital en **GPIO 1** de forma no bloqueante con filtro anti-rebote (*debounce*).
2. **Servidor y Backend en Docker (PC Windows):** Recibe las capturas JPEG mediante HTTP en red local, procesa detección de personas en tiempo real con **YOLOv8n (optimizado para CPU)**, registra eventos de paso e interrupción de haz con deduplicación estricta (idempotencia) y almacena registros en base de datos.
3. **Panel Web de Monitoreo:** Tablero interactivo en tiempo real con visor de cámara anotado, contador de aforo visible en encuadre, tarjeta de estado instantáneo del infrarrojo (🔴 **DETECTADO** / 🟢 **LIBRE**), contador de activaciones, hora de última detección e historial de auditoría.

---

## 2. CREDENCIALES, DIRECCIONES IP Y SECRETOS DEL SISTEMA

*(Guardado como memoria técnica para replicación y respaldo)*

### A. Conectividad Wi-Fi
* **SSID:** `JAPON`
* **Contraseña Wi-Fi:** `1a.2*3-GLPV`
* **Frecuencia:** 2.4 GHz (Requisito estricto del módem ESP32-S3).

### B. Direcciones IP y Puertos en la Red Local (Subred `192.168.1.0/24`)
* **Dispositivo ESP32-S3:**  
  * Dirección IP asignada por DHCP: `http://192.168.1.111`
  * Endpoint de capturas de cámara: `http://192.168.1.111/capture`
  * Streaming web: `http://192.168.1.111/`
* **Computadora Anfitriona (Host Windows / Docker):**  
  * Dirección IP en la interfaz Ethernet/Wi-Fi: `192.168.1.95`
  * Puerto de servicio en Docker: `8088` (Mapeo: `0.0.0.0:8088 -> 8000/tcp`)
  * URL del Panel Web en la PC: `http://localhost:8088` o `http://127.0.0.1:8088`
  * URL accesible desde el ESP32: `http://192.168.1.95:8088`
  * Endpoint de ingesta de eventos de sensores: `POST http://192.168.1.95:8088/api/v1/devices/ESP32_S3/events`
  * Endpoint de telemetría y salud: `GET http://192.168.1.95:8088/api/status`

### C. Tokens de Seguridad y Claves de API
* **Token de Dispositivo (Header `X-Device-Token`):** `esp32_device_secret_token_seguro_fase1`
* **DeepSeek API Key:** Integración lista en modo opcional desacoplado (`DEEPSEEK_VISION_ENABLED=false` por defecto para evitar consumo innecesario de tokens). Modelo compatible: `deepseek-flash`.

---

## 3. HARDWARE FÍSICO, ALIMENTACIÓN Y CONEXIONES ELÉCTRICAS

### A. Especificaciones del Microcontrolador
* **SoC:** ESP32-S3 (Dual-Core Xtensa LX7 a 240 MHz).
* **Serigrafía de PCB:** `V1695`, `127294G_Y1127_231016 CAMERA SD CARD PSRAM`.
* **Memoria Flash:** 16 MB NOR Flash (comprobado por software: 16 MB).
* **Memoria RAM externa:** 8 MB OPI PSRAM (comprobado por software: 8 MB).
* **Sensor de Imagen:** Omnivision OV5640 de 5 megapíxeles con interfaz FPC flexible de 24 pines.
* **Puertos USB físicos en la placa:**
  * `USB-UART` (Puerto CH340 / CP2102 utilizado para programación y monitor serie).
  * `USB-OTG` (Nativo USB CDC, no utilizado para consola principal).

### B. Esquema de Alimentación y Masas
* **ESP32-S3:** Alimentado directamente mediante su cable USB-C conectado a la PC o fuente independiente de 5V.
* **Protoboard y Sensores:** Alimentados exclusivamente a través del módulo de protoboard **MB102** con fuente de pared DC 9V/12V.
* **Tensión de riel medida con multímetro:** **3.21 V** (comprobado seguro para las entradas del ESP32-S3).
* **Masa Común:** Cable jumper uniendo **GND del ESP32-S3** con el **GND del protoboard**.
* **Regla de oro respetada:** Positivos separados (nunca se unió 5V ni 3.3V entre fuentes distintas).

### C. Mapeo Completo de Pines GPIO (ESP32-S3 V1695)

| Periférico | Pin GPIO | Estado | Función / Explicación |
|---|---|---|---|
| **Cámara OV5640 (D0-D7)** | GPIO 11, 9, 8, 10, 12, 18, 17, 16 | **OCUPADO** | Bus paralelo DVP (Y2 a Y9) |
| **Cámara OV5640 (Clocks)** | GPIO 15 (XCLK), 13 (PCLK) | **OCUPADO** | Reloj principal de 20 MHz y pixel clock |
| **Cámara OV5640 (Sync)** | GPIO 6 (VSYNC), 7 (HREF) | **OCUPADO** | Señales de sincronismo de cuadros |
| **Cámara OV5640 (I2C/SCCB)**| GPIO 4 (SDA), GPIO 5 (SCL) | **OCUPADO** | Bus de configuración del sensor |
| **Memoria PSRAM Octal** | GPIO 33, 34, 35, 36, 37 | **OCUPADO** | Bus OPI de alta velocidad reservado |
| **Puerto Serie UART0** | GPIO 43 (U0TXD), GPIO 44 (U0RXD) | **OCUPADO** | Comunicación USB-UART a 115200 baud |
| **Sensor Infrarrojo #1** | **GPIO 1** | **ACTIVO (FASE 1)** | Entrada digital `INPUT_PULLUP`. (LOW = Detectado, HIGH = Libre) |
| **RFID RC522 (Fase 2)** | GPIO 14, 21, 47, 48 *(Candidatos SPI)* | *Futuro* | Niveles a 3.3V para lector de tarjetas |
| **LEDs / Buzzer (Fase 3)** | Por asignar | *Futuro* | Señalización luminosa y acústica |
| **Servo Maqueta (Fase 4)**| Por asignar (PWM LEDC) | *Futuro* | Actuador de barrera (alimentación 5V externa separada) |

---

## 4. CONFIGURACIÓN EXACTA EN ARDUINO IDE 2.x

Para reproducir la compilación y subida del firmware sin errores de memoria o puerto serie:

| Parámetro en Menú Herramientas | Valor Obligatorio | Motivo Técnico |
|---|---|---|
| **Placa (Board)** | `ESP32S3 Dev Module` | Definición de placa del paquete oficial Espressif |
| **USB CDC On Boot** | **`Disabled`** | **CRÍTICO:** Si está en *Enabled*, la salida UART0 se apaga y el monitor serie queda mudo en USB-UART |
| **Flash Size** | `16MB (128Mb)` | Capacidad física de la memoria flash |
| **PSRAM** | `OPI PSRAM` | Activa los 8 MB Octal RAM indispensables para el búfer de la cámara |
| **Partition Scheme** | `16M Flash (3MB APP/9.9MB FATFS)` | El binario con Wi-Fi, HTTPClient y Camera supera 1.5 MB; requiere partición >= 3 MB |
| **Upload Speed** | `921600` (o `115200`) | Velocidad de grabación del bootloader |
| **Monitor Serie** | `115200 baudios` | Velocidad de depuración de la consola serie |

---

## 5. ESTRUCTURA DE LOS PROYECTOS IMPLEMENTADOS

El espacio de trabajo `c:\xampp\htdocs\OLARTE` contiene dos implementaciones perfectamente orquestadas:

### Proyecto 1: `esp32-vision-personas/` (Activo en Docker `0.0.0.0:8088`)
El microservicio actualmente en ejecución en la máquina, encargado del streaming en vivo, inferencia YOLO y monitoreo del sensor infrarrojo:

```text
esp32-vision-personas/
├── compose.yaml                         # Compose aislado (mapeado a 0.0.0.0:8088)
├── Dockerfile                           # Python 3.11-slim optimizado para CPU
├── requirements.txt                     # FastAPI, Ultralytics YOLOv8, OpenCV, httpx
├── .env                                 # Configuración activa con IP 0.0.0.0 y base URL del ESP32
├── .env.example                         # Plantilla sin secretos
├── .gitignore / .dockerignore           # Exclusiones de seguridad
├── README.md                            # Manual operativo del microservicio
├── app/
│   ├── main.py                          # FastAPI con worker de captura + endpoints IR y YOLO
│   ├── config.py                        # Pydantic Settings
│   ├── camera_client.py                 # Cliente asíncrono hacia /capture con backoff
│   ├── detector.py                      # YOLOv8n CPU (filtra clase 'person' con recuadros cian)
│   ├── deepseek_client.py               # Adaptador multimodal bajo demanda
│   ├── templates/index.html             # Dashboard con visualizador de cámara e indicador IR
│   └── static/
│       ├── style.css                    # Estilos oscuros, animaciones de pulso y estados
│       └── app.js                       # Polling dinámico a 1s para refresco instantáneo
├── firmware/
│   ├── CameraWebServer_ESP32S3_OV5640.ino  # Firmware FASE 1: OV5640 + Sensor IR en GPIO 1
│   ├── board_config.h                   # Perfil CAMERA_MODEL_ESP32S3_EYE comprobado
│   └── README.md                        # Documentación de carga manual
├── scripts/
│   └── simulate_ir.py                   # Simulador interactivo de paso de mano sin hardware
└── tests/
    ├── test_camera_mock.py              # Pruebas mock de desconexión, timeouts y JPEG corrupto
    └── test_count_mock.py               # Pruebas de filtrado YOLO y cliente DeepSeek
```

### Proyecto 2: `recinto-control/` (Arquitectura Escalonada con PostgreSQL)
Estructura lista para la evolución completa hacia control de acceso corporativo con base de datos relacional y migraciones:

```text
recinto-control/
├── compose.yaml                         # FastAPI + PostgreSQL 15 aislado (sin exponer puerto 5432)
├── Dockerfile                           # Backend Python 3.11
├── requirements.txt                     # FastAPI, SQLAlchemy, psycopg2, Alembic
├── .env.example                         # Plantilla de variables
├── README.md / HARDWARE.md / FASES.md   # Documentación de control por etapas y alimentación
├── TESTING.md / CHANGELOG.md            # Pruebas de idempotencia y registro de versiones
├── app/
│   ├── main.py                          # API v1
│   ├── database.py / models.py / schemas.py # Modelos ORM (devices, sensor_events con clave única)
│   ├── security.py                      # Verificación de X-Device-Token
│   └── routers/                         # Endpoints modulares (devices, events, dashboard, access)
├── firmware/Fase1_ESP32_IR_Camera/      # Firmware modular con heartbeat y cola de reintentos
└── scripts/simulate_events.py           # Simulador de secuencias de eventos y validación de idempotencia
```

---

## 6. HITOS TÉCNICOS RESUELTOS DURANTE LA SESIÓN

1. **Aislamiento absoluto de Docker y verificación de puertos:**
   * Se comprobó mediante inspección de solo lectura (`docker ps`) que los puertos `8000`, `8080`, `8082`, `8085`, `3000` y `3001` estaban ocupados por otros contenedores activos del usuario.
   * Se identificó y reservó el puerto **`8088`** para el microservicio de visión sin colisionar con ningún servicio preexistente.
   * Se evitó publicar el puerto de bases de datos al host para mantener el principio de mínimo privilegio.

2. **Resolución de incompatibilidad en PyTorch 2.6+ (Pesos YOLO):**
   * En versiones recientes de PyTorch (2.6+), `torch.load` cambió el valor por defecto de `weights_only` de `False` a `True`, lo cual provocaba un fallo de deserialización (`WeightsUnpickler error`) al cargar checkpoints de YOLOv8.
   * Se implementó un parche dinámico seguro en [app/detector.py](file:///c:/xampp/htdocs/OLARTE/esp32-vision-personas/app/detector.py) que restablece la carga de modelos de visión sin alterar el sistema operativo ni requerir recompilación de dependencias.

3. **Mapeo de Coordenadas de Inferencia:**
   * Se corrigió la conversión de cajas delimitadoras en `PersonDetector` para admitir tanto tensores nativos de PyTorch como listas y arrays de NumPy mediante `hasattr(coords, "tolist")`, logrando un 100% de aprobación en la suite de 15 pruebas unitarias automatizadas (`15 passed in 0.87s`).

4. **Transición a Red Externa (`0.0.0.0`):**
   * Inicialmente el contenedor estaba enlazado a `127.0.0.1` (solo accesible internamente en la PC).
   * Para permitir que el ESP32 físico (`192.168.1.111`) enviara peticiones HTTP POST al backend en la PC (`192.168.1.95:8088`), se actualizó la vinculación a `0.0.0.0:8088`, garantizando la comunicación bidireccional entre el microcontrolador y el servidor.

5. **Lectura No Bloqueante del Sensor IR en GPIO 1:**
   * Se integró en el bucle principal `loop()` del ESP32 una rutina de sondeo digital no bloqueante basada en `millis()` con 50 ms de tiempo anti-rebote (*debounce*) y una ventana de 250 ms anti-repetición.
   * Esto garantiza que la cámara OV5640 **nunca sufra congelamiento de fotogramas ni pérdida de conexión Wi-Fi** mientras se detectan objetos o personas frente al sensor.

---

## 7. PROTOCOLO DE OPERACIÓN Y VALIDACIÓN RÁPIDA

### Cómo iniciar o reiniciar el sistema:
1. En tu terminal PowerShell:
   ```powershell
   cd c:\xampp\htdocs\OLARTE\esp32-vision-personas
   docker compose up -d
   ```
2. Abre en tu navegador:
   👉 **`http://localhost:8088`**
3. Enciende el ESP32 y el módulo MB102 (3.3V).
4. El monitor serie del ESP32 (115200 baudios) confirmará:
   ```text
   SENSOR INFRARROJO INICIALIZADO EN GPIO 1 (Estado actual: LIBRE)
   CAMARA OV5640 INICIALIZADA CORRECTAMENTE.
   WIFI CONECTADO EXITOSAMENTE
   IP LOCAL CAMARA: http://192.168.1.111
   DESTINO EVENTOS: http://192.168.1.95:8088
   ```
5. **Prueba de paso:**
   * Al colocar la mano a 5 cm del sensor: La tarjeta del panel web conmuta a 🔴 **DETECTADO**, suma +1 en activaciones y registra la hora.
   * Al retirar la mano: La tarjeta del panel web conmuta a 🟢 **LIBRE**.
   * Simultáneamente, la cámara OV5640 transmite el video en vivo y YOLO dibuja recuadros cian sobre cualquier persona visible en el encuadre.

---

## 8. REGLAS PARA LAS PRÓXIMAS FASES (HOJA DE RUTA)

* **Fase 2 (RFID RC522):** Conexión por bus SPI (3.3V). La lectura de tarjetas evaluará políticas en el backend sin accionar compuertas físicas hasta contar con mecanismos de seguridad.
* **Fase 3 (Señalización):** Integración secuencial de LED verde (autorizado), LED rojo (denegado) y buzzer con transistor 2N2222A.
* **Fase 4 (Servomotor Maqueta):** El servo SG90 solo se utilizará como demostración a escala; se alimentará de forma externa con GND común para proteger al microcontrolador de caídas de tensión.
* **Fase 6 (Segundo Sensor IR):** Solo cuando se disponga físicamente del segundo sensor se habilitará la lógica de dirección de paso (entrada vs. salida) y aforo acumulado del recinto.
