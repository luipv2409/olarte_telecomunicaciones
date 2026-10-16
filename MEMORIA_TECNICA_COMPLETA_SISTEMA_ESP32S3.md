# MEMORIA TÉCNICA Y REPORTE COMPLETO DEL SISTEMA
## ESP32-S3 N16R8 + OV5640 + SENSOR IR + DOCKER (YOLO LOCAL & CONTROL DE ACCESO)

> **Documento:** Memoria técnica integral y registro histórico del sistema.  
> **Fecha de consolidación:** 16 de Octubre de 2026.  
> **Estado:** Fase 0, Fase 1, Fase 2 y Fase 3 (Buzzer Acústico) completadas, operativas y validadas en hardware real.

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
| **RFID RC522 (Fase 2)** | **GPIO 14 (SCK), 21 (MOSI), 47 (MISO), 2 (SDA/SS), 48 (RST)** | **VALIDADO Y OPERATIVO (FASE 2)** | Bus SPI a 3.3V estrictos. Lectura de tarjetas UID `73230E06` y `6C8D1B06` |
| **Buzzer Activo (Fase 3)** | **GPIO 42** | **ACTIVO (FASE 3)** | Driver NPN 2N2222A (Low-Side Switch) con $R_B = 1\text{ k}\Omega$ a 3.3V. Señalización acústica |
| **LEDs Estado (Fase 3)** | GPIO 19 (Verde), GPIO 20 (Rojo) | *Reservados (Fase 3)* | Señalización luminosa con resistencias limitadoras de $220\text{ }\Omega$ |
| **Servo Maqueta (Fase 4)**| GPIO por definir (PWM LEDC) | *Futuro (Fase 4)* | Actuador de barrera vehicular (alimentado por convertidor LM2596 a 5V) |

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

6. **Integración Completa del Lector RFID RC522 (Fase 2):**
   * Se incorporó el lector MFRC522 mediante bus SPI en GPIO 14 (SCK), 21 (MOSI), 47 (MISO), 2 (SDA/SS) y 48 (RST).
   * Se integró lectura no bloqueante de tarjetas y llaveros RFID (MIFARE 1KB / 13.56 MHz) sin interferir con el streaming de cámara ni con el sensor infrarrojo.

---

## 7. FASE 2: INTEGRACIÓN DEL CONTROL DE ACCESO RFID (RC522)

### A. Mapeo de Pines SPI en la Placa ESP32-S3 (PCB V1695)
| Pin del RC522 | Pin ESP32-S3 | Posición en Regleta | Nivel Eléctrico | Función |
| :--- | :--- | :--- | :--- | :--- |
| **VCC** | **3V3** | Riel 3.3V (MB102 o placa) | **3.3 V ESTRICTO** | ¡NUNCA 5V! Tolera máx 3.3V |
| **RST** | **GPIO 48** | Regleta derecha, pin 6 desde abajo | 3.3 V | Salida de Reset / Wake-up |
| **GND** | **GND** | Regleta derecha, pin 1 desde abajo | 0 V | **Masa común obligatoria** |
| **IRQ** | *(Libre)* | — | — | No utilizado |
| **MISO** | **GPIO 47** | Regleta derecha, pin 5 desde abajo | 3.3 V | SPI Master In (Datos hacia ESP32) |
| **MOSI** | **GPIO 21** | Regleta derecha, pin 4 desde abajo | 3.3 V | SPI Master Out (Datos hacia RC522) |
| **SCK** | **GPIO 14** | Regleta izquierda, pin 2 desde abajo | 3.3 V | SPI Reloj |
| **SDA (SS)**| **GPIO 2** | Regleta izquierda, pin 8 desde abajo | 3.3 V | SPI Slave Select / Chip Select |

### B. Hallazgos Críticos y Soluciones Técnicas durante la Fase 2
1. **La Regla de Masa Común (GND):**
   * Si el GND del ESP32 no se une con el GND de la protoboard, el bus SPI queda sin referencia de 0V, haciendo que las señales floten y se lean errores `0x00`, `0xFF` o ruidos. **Solución:** Conectar un cable dedicado desde el pin `GND` del ESP32 al riel `(-)` de la protoboard.
2. **Diagnóstico Dinámico del Registro de Versión (`VersionReg`):**
   * **`0x82`:** Identificador legítimo de chip clon MFRC522 100% funcional.
   * **`0xEE` (Loopback MOSI-MISO por Cortocircuito Físico):** La dirección de VersionReg es 0x37 (`(0x37 << 1) | 0x80 = 0xEE`). Si MISO recibe `0xEE`, significa que el comando transmitido por MOSI (GPIO 21) regresa de inmediato por MISO (GPIO 47) porque los dos pines contiguos se están tocando físicamente en la regleta o en la protoboard. **Solución:** Separar físicamente los pines/jumpers 21 y 47.
   * **`0x7F` / `0x21` / `0x0E`:** Ruido transitorio o línea MISO flotando debido a falso contacto o jumper flojo.
   * **`0x00` o `0xFF`:** Falta de alimentación 3.3V, módulo MB102 apagado o masa (GND) desconectada.
3. **Prueba de Laboratorio y Validación de 14 Lecturas Consecutivas (16 de Octubre de 2026):**
   * Se comprobó en tiempo real cómo el bucle de autodiagnóstico no bloqueante identificó en vivo el cortocircuito transitorio `0xEE` entre los pines 21 y 47 al conectar el buzzer. Tras separar los cables, el bus se estabilizó en `0x82` permanente.
   * Se ejecutaron con éxito rotundo **14 lecturas consecutivas de tarjetas RFID** con respuesta acústica inmediata y diferenciada en el buzzer:
     - `6C8D1B06`: 🟢 **ACCESO CONCEDIDO** (Socio Activo #2) $\rightarrow$ 1 bip largo (150 ms).
     - `73230E06`: 🔴 **ACCESO DENEGADO** (Socio #1) $\rightarrow$ 3 bips rápidos de alarma (80 ms).
4. **Innovación Arquitectónica: Telemetría de Salud de Hardware hacia Docker:**
   * **Objetivo:** No depender del Monitor Serie de Arduino IDE en producción para saber si un cable se aflojó.
   * **Implementación:** El ESP32 incluirá el estado en tiempo real del bus SPI (`spi_status: "OK"` / `"SHORT_MOSI_MISO_0xEE"` / `"DISCONNECTED"`) dentro del paquete JSON de Heartbeat enviado periódicamente a Docker (`POST /api/v1/devices/{device_id}/events` o telemetría). Así, el panel web alertará al operador exactamente qué cable o pin requiere atención.
5. **Peligro de Saturación por Ganancia Forzada (`RxGain_max`):**
   * En chips clones `0x82`, forzar ganancia máxima (48dB) con `PCD_SetAntennaGain` satura el mezclador analógico de RF y ciega el lector. **Solución:** Mantener la ganancia estándar de fábrica tras `PCD_Init()`.
6. **Comportamiento del LED 48 (WS2812 NeoPixel):**
   * El LED SMD serigrafiado como `48` en la placa es un LED inteligente direccionable. Al inicializar el pin RST del RC522 con pulsos rápidos, el LED decodifica colores transitorios (verde, blanco) y queda fijo en **Azul**. Esto es normal y confirma que GPIO 48 está en nivel ALTO (3.3V) manteniendo activo al lector.

### C. Políticas de Acceso Implementadas y Validadas en Hardware
| UID Hexadecimal | Titular Registrado | Política de Acceso | Resultado en Sistema |
| :--- | :--- | :--- | :--- |
| **`73230E06`** | Socio #1 | 🔴 **BLOQUEADA** | **ACCESO DENEGADO** (Banner Rojo en Web / Alerta en Consola) |
| **`6C8D1B06`** | Socio Activo #2 | 🟢 **AUTORIZADA** | **ACCESO CONCEDIDO** (Banner Verde en Web / Ingreso Permitido) |

### D. Actualización del Backend Docker y Panel Web
* **Base de datos SQLite (`recinto_events.db`):** Migrada con las columnas `uid` y `card_holder` para auditoría permanente.
* **Interfaz Web (`http://192.168.1.95:8088/`):** Incorporación de tarjeta de Control de Acceso RFID con animación de pulso, display de credenciales registradas, contador de usos y registro cronológico en vivo.
* **Firmware de Diagnóstico Aislado:** Creación del sketch de prueba [Test_RFID_RC522_ESP32S3.ino](file:///c:/xampp/htdocs/OLARTE/recinto-control/firmware/Test_RFID_RC522_ESP32S3/Test_RFID_RC522_ESP32S3.ino) para verificación pura en monitor serie.

---

## 8. FASE 3: SEÑALIZACIÓN ACÚSTICA (BUZZER ACTIVO) CON DRIVER NPN 2N2222A

### A. Especificaciones del Componente y Principio de Operación
* **Componente:** Buzzer electromagnético activo de 5V CC con oscilador interno (etiqueta superior `⊕ REMOVE AFTER WASHING`).
* **Frecuencia del Oscilador:** ~2700 Hz (tono acústico agudo predeterminado de fábrica).
* **Control Digital:** Solo requiere nivel lógico continuo DC (`HIGH` = 3.3V activa sonido, `LOW` = 0V silencio). No requiere modulación PWM ni librerías de generación de tonos (`tone()` / `ledcWrite`).
* **Consumo Eléctrico:** ~18 mA a 25 mA alimentado a 3.3V (~30 mA a 5V).

### B. Análisis de Ingeniería Eléctrica: ¿Por qué Driver NPN y no Resistencia Serie?
1. **Fallo del Método de Resistencia en Serie ($220\text{ }\Omega$):**
   * La bobina interna del zumbador presenta una impedancia equivalente de aproximadamente $R_{buzzer} \approx 160\text{ }\Omega$.
   * Si se conecta el buzzer en serie con una resistencia limitadora de $220\text{ }\Omega$ directamente a un pin de 3.3V del ESP32-S3, se forma un divisor de tensión:
     $$V_{buzzer} = 3.3\text{ V} \times \frac{160\text{ }\Omega}{220\text{ }\Omega + 160\text{ }\Omega} = 3.3\text{ V} \times \frac{160}{380} \approx 1.38\text{ V}$$
   * Con solo $1.38\text{ V}$, el oscilador interno queda por debajo del umbral mínimo de operación; el buzzer no vibra o produce un zumbido imperceptible.
   * Por otro lado, si se conectase directo al pin sin resistencia, el consumo de $\sim 30\text{ mA}$ excede los límites seguros continuos del ESP32-S3 y la fuerza contraelectromotriz (inductancia) de la bobina daña el microcontrolador.

2. **Solución Implementada: Conmutador en Lado Bajo (*Low-Side Switch*) con Transistor 2N2222A:**
   * Se utiliza un transistor NPN de conmutación rápida **2N2222A** con una resistencia de base de **$1\text{ k}\Omega$** conectada al **GPIO 42**.
   * **Cálculo de Corriente de Base ($I_B$):**
     $$I_B = \frac{V_{GPIO} - V_{BE}}{R_B} = \frac{3.3\text{ V} - 0.7\text{ V}}{1000\text{ }\Omega} = \frac{2.6\text{ V}}{1000\text{ }\Omega} = 2.6\text{ mA}$$
   * **Protección del ESP32:** El pin GPIO 42 solo suministra un consumo insignificante de **$2.6\text{ mA}$**, perfectamente seguro para el chip.
   * **Saturación Completa del Transistor:** Con una ganancia en saturación forzada $\beta_{sat} \approx 10$, se garantiza una corriente de colector disponible de $I_{C(sat)} = \beta_{sat} \times I_B = 10 \times 2.6\text{ mA} = 26\text{ mA}$, suficiente para la demanda del buzzer. La caída colector-emisor en saturación es mínima ($V_{CE(sat)} \approx 0.1\text{ V}$), entregando $3.2\text{ V}$ íntegros a la bobina del buzzer.

### C. Justificación de Asignación de Pines: ¿Por qué GPIO 42 y NUNCA GPIO 47?
* ⚠️ **PROHIBICIÓN ESTRICTA DE GPIO 47:** En algunas guías genéricas se sugiere el pin 47 para actuadores. En este diseño, **GPIO 47 está asignado de forma inamovible como MISO (Master In Slave Out) del bus SPI del RFID RC522**. Conectar el buzzer en el pin 47 anularía por completo la lectura de tarjetas.
* 🟢 **SELECCIÓN DE GPIO 42:**
  - Pin libre en la regleta derecha de la placa (PCB V1695).
  - No colisiona con el bus de la cámara OV5640 (pines 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18).
  - No interfiere con el bus Octal SPI de la memoria PSRAM de 8 MB (pines 33 al 37).
  - No interfiere con la consola USB-UART (pines 43 y 44).
  - No es pin de strapping de arranque crítico.

### D. Esquema del Circuito y Conexión Física (TO-92)
```text
               +3.3V (Riel Protoboard MB102)
                     │
                     ▲
                 ┌───────┐
                 │  (+)  │
                 │ BUZZER│ (Zumbador Activo 5V)
                 │  (-)  │
                 └───────┘
                     │
                     ▼
                 Colector (Pin 3)
                   ┌───┐
  GPIO 42 ──[1kΩ]──┤ B │  Transistor NPN 2N2222A
                   └───┘
                 Emisor (Pin 1)
                     │
                     ▼
               GND (Masa Común con ESP32)
```

**Patillaje físico del Transistor 2N2222A (Encapsulado TO-92, cara plana mirando de frente):**
* **Pin 1 (Izquierda) — Emisor:** Conectado directamente al riel azul de masa común (`GND`).
* **Pin 2 (Centro) — Base:** Conectado a la resistencia de $1\text{ k}\Omega$ (Marrón-Negro-Rojo), la cual va al pin **GPIO 42** del ESP32-S3.
* **Pin 3 (Derecha) — Colector:** Conectado a la pata corta / negativa `(-)` del buzzer.
* **Pata larga / positiva `(+)` del Buzzer:** Conectada directamente al riel rojo de **3.3V** de la protoboard.

### E. Patrones Acústicos Implementados en Firmware
| Patrón Acústico | Función en Firmware | Duración y Frecuencia | Evento Asociado |
| :--- | :--- | :--- | :--- |
| **Bip de Arranque** | `beepStartup()` | 1 pulso de 80 ms | Inicialización correcta del sistema y autodiagnóstico de periféricos |
| **Acceso Autorizado** | `beepSuccess()` | 1 pulso de 150 ms | Tarjeta válida registrada (`6C8D1B06` - Socio Activo #2) |
| **Acceso Denegado** | `beepDenied()` | 3 pulsos de 80 ms (intervalos de 80 ms) | Tarjeta bloqueada (`73230E06`) o credencial no registrada |

---

## 9. PROTOCOLO DE OPERACIÓN Y VALIDACIÓN RÁPIDA

### Cómo iniciar o reiniciar el sistema completo:
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
   ==============================================================
      TEST EXCLUSIVO DE DIAGNÓSTICO RFID RC522 - ESP32-S3
   ==============================================================
   Configuración de Pines SPI:
     -> SDA (SS) : GPIO 2
     -> SCK      : GPIO 14
     -> MOSI     : GPIO 21
     -> MISO     : GPIO 47
     -> RST      : GPIO 48
     -> BUZZER   : GPIO 42 (Transistor 2N2222A)
   [PASO 1] Inicializando bus SPI por hardware...
   [PASO 2] Inicializando chip MFRC522 (PCD_Init)...
   [OK] Lector detectado: 0x82 (Version clon funcional - OK)
   [ESTADO] Listo. Acerca una tarjeta al lector...
   ```
5. **Pruebas en tiempo real:**
   * **Arranque:** Al encender o resetear, el buzzer emite un micro-bip de 80 ms confirmando que el GPIO 42 y el transistor operan correctamente.
   * **RFID Denegado:** Al pasar la tarjeta `73230E06`, el monitor serie marca `🔴 [ACCESO DENEGADO]` y el buzzer emite **3 bips rápidos de advertencia**.
   * **RFID Concedido:** Al pasar la tarjeta `6C8D1B06`, el monitor serie marca `🟢 [ACCESO CONCEDIDO]` y el buzzer emite **1 bip largo de bienvenida (150 ms)**.
   * **Paso IR:** Al pasar la mano a 5 cm del sensor IR, el panel web conmuta a 🔴 **DETECTADO** y suma +1 activación.
   * **Cámara OV5640 + YOLO:** Video en vivo continuo con conteo instantáneo de personas presentes.

---

## 10. REGLAS PARA LAS PRÓXIMAS FASES (HOJA DE RUTA Y ACTUADORES)

* **Fase 3 (Finalización de Señalización):**
  * Conexión de **LED Verde (GPIO 19)** con resistencia de $220\text{ }\Omega$ para indicador visual de acceso concedido.
  * Conexión de **LED Rojo (GPIO 20)** con resistencia de $220\text{ }\Omega$ para indicador visual de acceso denegado.
* **Fase 4 (Servomotor de Barrera - Arquitectura de Potencia):**
  * **Problema del MB102:** El regulador lineal AMS1117-5.0 del módulo MB102 se sobrecalentaría críticamente si intenta bajar de 12V a 5V los 600-800 mA que consume un servomotor en movimiento ($P = 7\text{ V} \times 0.6\text{ A} \approx 4.2\text{ W}$, lo que causaría corte térmico y reinicio del ESP32).
  * **Solución de Potencia:** Se utilizará la fuente externa de pared **12V 2A** conectada a un convertidor conmutado **Step-Down LM2596** calibrado con multímetro exactamente a **$5.0\text{ V}$**.
  * **Regla de Conexión del Servo:**
    - Cable Rojo (VCC) del Servo -> Salida +5V del LM2596.
    - Cable Marrón/Negro (GND) del Servo -> Salida GND del LM2596 e interconectado a la masa común (GND) de todo el sistema.
    - Cable Naranja/Amarillo (PWM) del Servo -> Pin GPIO designado del ESP32-S3 (señal de 3.3V compatible con entradas lógicas del servomotor).
* **Fase 6 (Segundo Sensor IR):**
  * Se reservará un GPIO adicional para implementar la discriminación direccional de paso (Entrada vs. Salida) y el balance acumulativo de aforo.
