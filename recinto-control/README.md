# Recinto Control — Sistema Escalonado de Control de Acceso y Sensores

Sistema de control de acceso para recintos basado en microcontrolador **ESP32-S3 N16R8 con cámara OV5640**, backend **FastAPI**, base de datos relacional **PostgreSQL**, panel de telemetría en tiempo real y arquitectura de sensores incrementales.

---

## 📁 Estructura del Proyecto (`recinto-control/`)

```text
recinto-control/
├── compose.yaml                      # Docker Compose aislado (PostgreSQL interno + FastAPI)
├── Dockerfile                        # Imagen backend Python 3.11-slim
├── requirements.txt                  # Dependencias FastAPI, SQLAlchemy, psycopg2, pytest
├── .env.example                      # Plantilla de variables sin secretos
├── .gitignore                        # Protección para credenciales y temporales
├── .dockerignore                     # Exclusiones de contexto de compilación
├── README.md                         # Esta documentación operativa
├── HARDWARE.md                       # Diagrama de alimentación, tierras y mapa GPIO
├── FASES.md                          # Trazabilidad de fases y estado de componentes
├── TESTING.md                        # Casos de prueba unitaria y con hardware
├── CHANGELOG.md                      # Historial de cambios
├── app/
│   ├── __init__.py
│   ├── main.py                       # Aplicación FastAPI y panel web
│   ├── config.py                     # Configuración tipada
│   ├── database.py                   # Conexión SQLAlchemy y motor PostgreSQL
│   ├── models.py                     # Tablas de DB (dispositivos, eventos idempotentes)
│   ├── schemas.py                    # Esquemas Pydantic v2
│   ├── security.py                   # Verificación de tokens de dispositivo
│   ├── routers/
│   │   ├── devices.py                # Heartbeat y registro de estado
│   │   ├── events.py                 # Ingesta idempotente de eventos de sensores
│   │   ├── dashboard.py              # Resumen de telemetría y eventos
│   │   └── access.py                 # Evaluación de acceso (preparado e inactivo en Fase 1)
│   ├── templates/
│   │   └── dashboard.html            # Dashboard en tema oscuro
│   └── static/
│       ├── style.css                 # Estilos modernos de alta legibilidad
│       └── app.js                    # Refresco automático de telemetría
├── firmware/
│   └── Fase1_ESP32_IR_Camera/
│       ├── Fase1_ESP32_IR_Camera.ino # Sketch Arduino con debounce no bloqueante y cámara
│       ├── board_config.h            # Perfil funcional CAMERA_MODEL_ESP32S3_EYE
│       └── secrets.h.example         # Plantilla de credenciales Wi-Fi locales
├── scripts/
│   └── simulate_events.py            # Simulador de eventos para pruebas sin hardware
└── tests/
    ├── __init__.py
    ├── test_api_heartbeat.py         # Pruebas de salud y autenticación
    └── test_api_events_idempotency.py# Pruebas de deduplicación estricta en base de datos
```

---

## 🚀 Despliegue y Ejecución Manual (Windows + Docker Desktop)

### Paso 1: Verificar un puerto libre en tu PC Windows
Para no interferir con el servicio de visión en el puerto `8088` ni con tus otros contenedores existentes, verifica un puerto libre (por ejemplo `8089`):
```powershell
Get-NetTCPConnection -LocalPort 8089 -ErrorAction SilentlyContinue
```
*Si no devuelve salida, el puerto está disponible.*

### Paso 2: Configurar el archivo `.env`
```powershell
cd c:\xampp\htdocs\OLARTE\recinto-control
copy .env.example .env
```
Edita `.env` con:
```dotenv
HOST_HTTP_PORT=8089
HOST_BIND_IP=127.0.0.1
POSTGRES_DB=recinto_control_db
POSTGRES_USER=recinto_admin
POSTGRES_PASSWORD=tu_clave_secreta_local
DEVICE_API_SECRET=esp32_device_secret_token_seguro_fase1
ESP32_BASE_URL=http://192.168.1.111
```

### Paso 3: Construir y Levantar el Contenedor (Aislado)
```powershell
# Construir imagen del backend
docker compose -f compose.yaml -p recinto-control build

# Levantar únicamente este proyecto en segundo plano
docker compose -f compose.yaml -p recinto-control up -d
```
Verifica el estado del servicio:
```powershell
docker compose -f compose.yaml -p recinto-control ps
```

### Paso 4: Abrir el Dashboard en el Navegador
Abre en tu navegador:  
👉 **`http://localhost:8089`**

---

## 🧪 Pruebas de Simulación sin Hardware Conectado

Para comprobar que la base de datos PostgreSQL, la API y el panel web están funcionando al 100% sin tener el sensor físico conectado:
```powershell
python scripts/simulate_events.py http://127.0.0.1:8089
```
Observarás en el dashboard cómo se incrementan los eventos y cómo se visualizan con la etiqueta `SIMULADO`.

---

## 🛑 Detener el Servicio Limpiamente

Cuando desees detener el servicio sin tocar ningún otro contenedor:
```powershell
docker compose -f compose.yaml -p recinto-control down
```
*(Tus datos en PostgreSQL se conservan intactos en el volumen persistente `recinto_postgres_data`).*
