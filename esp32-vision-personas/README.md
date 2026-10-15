# ESP32-S3 OV5640 + Conteo de Personas Local con Docker

Sistema completo de adquisición de video y fotogramas mediante **ESP32-S3 N16R8 con cámara OV5640**, procesamiento de visión artificial local con **YOLOv8n (CPU)** en contenedor Docker aislado, panel web de visualización en tiempo real y adaptador multimodal opcional para la API de **DeepSeek**.

---

## 📁 Estructura del Proyecto

```text
esp32-vision-personas/
├── compose.yaml                      # Configuración Docker Compose con puertos aislados
├── Dockerfile                        # Imagen Python 3.11-slim optimizada para CPU
├── requirements.txt                  # Dependencias FastAPI, Ultralytics y OpenCV
├── .env.example                      # Plantilla de variables sin secretos
├── .dockerignore                     # Filtro de contexto de compilación
├── .gitignore                        # Protección para no subir credenciales ni .env
├── README.md                         # Esta documentación general
├── app/
│   ├── __init__.py
│   ├── main.py                       # Servidor FastAPI, endpoints REST y worker asíncrono
│   ├── config.py                     # Configuración tipada con Pydantic Settings
│   ├── camera_client.py              # Cliente HTTP asíncrono hacia /capture del ESP32
│   ├── detector.py                   # Detector YOLOv8 filtrando clase 'person' en CPU
│   ├── deepseek_client.py            # Adaptador seguro para DeepSeek Vision (bajo demanda)
│   ├── templates/
│   │   └── index.html                # Panel web interactivo con diseño oscuro
│   └── static/
│       ├── style.css                 # Estilos CSS modernos y responsivos
│       └── app.js                    # Telemetría en tiempo real y refresco de imagen
├── firmware/
│   ├── README.md                     # Instrucciones detalladas de carga en Arduino IDE
│   ├── CameraWebServer_ESP32S3_OV5640.ino  # Sketch funcional verificado
│   └── board_config.h                # Perfil CAMERA_MODEL_ESP32S3_EYE para PCB V1695
├── tests/
│   ├── __init__.py
│   ├── test_camera_mock.py           # Pruebas unitarias de cliente HTTP, timeouts y JPEG
│   └── test_count_mock.py            # Pruebas de inferencia, clases YOLO y DeepSeek
└── docs/
    ├── INSTALACION_WINDOWS_DOCKER.md # Pasos manuales de despliegue en Windows
    ├── CONFIGURACION_ARDUINO_IDE.md  # Ajustes de placa, flash, PSRAM y UART
    ├── ARQUITECTURA.md               # Diagramas de flujo, endpoints y privacidad
    └── SOLUCION_PROBLEMAS.md         # Diagnóstico de fallo 3MP, COM port y Wi-Fi
```

---

## 🚀 Puesta en Marcha Rápida (Manual)

### 1. Cargar el Firmware en el ESP32-S3
1. Abre [firmware/CameraWebServer_ESP32S3_OV5640.ino](file:///c:/xampp/htdocs/OLARTE/esp32-vision-personas/firmware/CameraWebServer_ESP32S3_OV5640.ino) en Arduino IDE.
2. Introduce tu SSID y clave Wi-Fi local.
3. Asegura los parámetros: Placa `ESP32S3 Dev Module`, `USB CDC On Boot = Disabled`, `PSRAM = OPI PSRAM`, `Flash = 16MB`.
4. Sube el código mediante el puerto USB-UART y anota la dirección IP que imprima el Monitor Serie a 115200 (ej. `http://192.168.1.150`).

### 2. Configurar el Entorno Docker
1. En la carpeta `esp32-vision-personas`, copia `.env.example` a `.env`:
   ```powershell
   copy .env.example .env
   ```
2. Edita `.env` seleccionando un puerto libre verificado en tu PC (ej. `APP_HOST_PORT=8088`) y la IP de tu ESP32:
   ```dotenv
   APP_BIND_IP=127.0.0.1
   APP_HOST_PORT=8088
   ESP32_BASE_URL=http://192.168.1.150
   ```

### 3. Construir e Iniciar el Contenedor
```powershell
docker compose -f compose.yaml -p esp32-vision-personas build
docker compose -f compose.yaml -p esp32-vision-personas up -d
```

### 4. Abrir el Panel Web
Navega a `http://localhost:8088` (o el puerto que configuraste).

---

## 🔒 Privacidad y Alcance Técnico

* **Conteo instantáneo:** El sistema estima cuántas personas están presentes en cada cuadro fotográfico. No realiza conteo acumulado de flujo de personas ni actúa como torniquete.
* **Sin almacenamiento de imágenes:** Los fotogramas se procesan en la memoria RAM y se descartan; no se almacenan fotos en disco.
* **Sin identificación:** No se aplica reconocimiento facial ni seguimiento individual de identidades.
