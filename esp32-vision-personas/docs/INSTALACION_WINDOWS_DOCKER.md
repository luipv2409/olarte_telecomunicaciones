# Guía de Instalación y Despliegue Manual en Windows (Docker)

Esta guía detalla los pasos manuales para configurar y levantar el contenedor de **`esp32-vision-personas`** en tu PC Windows utilizando **Docker Desktop**, asegurando aislamiento total y sin interferir con otros servicios o puertos en uso.

---

## 1. Reglas de Aislamiento y Seguridad

* Este proyecto utiliza el nombre de Compose `esp32-vision-personas` y su propia red interna tipo bridge (`esp32_vision_net`).
* **Nunca** sobrescribirá ni detendrá contenedores de otros proyectos.
* No utiliza `network_mode: host` ni monta el socket de Docker del sistema anfitrión.

---

## 2. Paso 1: Seleccionar un puerto libre en Windows

Dado que en tu PC ya corren otros contenedores o servicios (XAMPP, Apache, MySQL, etc.), **no asumas** que los puertos 80, 8000, 8080 o 3000 están disponibles.

Abre **PowerShell** en Windows y comprueba si un puerto (por ejemplo, el `8088`) está libre:

```powershell
Get-NetTCPConnection -LocalPort 8088 -ErrorAction SilentlyContinue
```

* **Si el comando no devuelve ninguna salida:** El puerto está libre y puedes utilizarlo.
* **Si el comando devuelve líneas con `Listen` o `Established`:** El puerto está ocupado; prueba con otro número (ej. `8089`, `8095`, `9000`).

---

## 3. Paso 2: Crear el archivo `.env`

Entra a la carpeta del proyecto en tu terminal:

```powershell
cd c:\xampp\htdocs\OLARTE\esp32-vision-personas
copy .env.example .env
```

Abre `.env` con tu editor preferido y edita las siguientes variables:

```dotenv
# 1. Dirección IP de enlace:
#    - Usa '127.0.0.1' si solo accederás desde el navegador de esta misma PC.
#    - Usa la IP local de tu PC en la red (ej. 192.168.1.50) si quieres ver el panel desde tu celular u otra PC en la misma red Wi-Fi.
APP_BIND_IP=127.0.0.1

# 2. Puerto verificado libre en el Paso 1:
APP_HOST_PORT=8088

# 3. Dirección IP del ESP32 (obtenida del monitor serie de Arduino IDE):
ESP32_BASE_URL=http://192.168.1.150

# 4. Intervalo entre capturas (segundos):
CAPTURE_INTERVAL_SECONDS=2.0

# 5. Umbral de confianza YOLO (0.10 a 0.95):
DETECTION_CONFIDENCE=0.45

# 6. DeepSeek (Opcional - dejar vacío si no se usa):
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-flash
DEEPSEEK_VISION_ENABLED=false
```

> **IMPORTANTE:** Nunca agregues el archivo `.env` a Git ni compartas tus contraseñas o API keys.

---

## 4. Paso 3: Construir la imagen Docker (Build aislado)

Ejecuta el comando de construcción especificando explícitamente el archivo compose y el nombre de proyecto:

```powershell
docker compose -f compose.yaml -p esp32-vision-personas build
```

Este proceso:
1. Instalará Python 3.11-slim y las dependencias de visión en un entorno no-root seguro.
2. Pre-descargará el modelo ligero `yolov8n.pt` para que la inferencia funcione sin depender de conexiones externas continuas.

---

## 5. Paso 4: Iniciar el servicio

Para iniciar **únicamente** este servicio en segundo plano:

```powershell
docker compose -f compose.yaml -p esp32-vision-personas up -d
```

Verifica que el contenedor esté corriendo y saludable:

```powershell
docker compose -f compose.yaml -p esp32-vision-personas ps
```

Deberás ver el estado `Up (healthy)`.

---

## 6. Paso 5: Acceder a la interfaz web

Abre tu navegador web e ingresa a:

* Si configuraste `APP_BIND_IP=127.0.0.1`:
  `http://127.0.0.1:8088` o `http://localhost:8088`
* Si configuraste la IP LAN de tu PC (ej. `192.168.1.50`):
  `http://192.168.1.50:8088`

---

## 7. Paso 6: Ver registros (Logs) en caso de incidencias

Para inspeccionar lo que sucede en tiempo real:

```powershell
docker compose -f compose.yaml -p esp32-vision-personas logs -f
```

*(Presiona `Ctrl + C` para salir de la visualización de logs).*

---

## 8. Paso 7: Detener el servicio limpiamente

Cuando desees apagar el servicio sin tocar ningún otro contenedor de tu máquina:

```powershell
docker compose -f compose.yaml -p esp32-vision-personas down
```
