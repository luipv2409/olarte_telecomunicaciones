# Guía de Diagnóstico y Solución de Problemas

Esta guía cubre los errores más frecuentes reportados durante la puesta en marcha del hardware ESP32-S3 con cámara OV5640 y el despliegue del contenedor Docker.

---

## 1. Problemas de Cámara y Hardware ESP32-S3

### A. Pantalla negra al cambiar resolución a 3 MP (864×1564) o superior
* **Causa técnica:** En el sensor OV5640, cambiar dinámicamente la resolución durante una transmisión activa de video puede desincronizar el reloj de píxeles (PCLK) y saturar los búferes DMA del controlador de cámara antes de que el conversor JPEG termine de empaquetar el frame.
* **Solución comprobada:** 
  1. Mantén la resolución base en **`FRAMESIZE_VGA` (640×480)** o **`FRAMESIZE_SVGA` (800×600)** para la previsualización y conteo en tiempo real.
  2. Si requieres capturas de 3 MP o 5 MP, realízalas como una toma fotográfica única estática, no durante una secuencia continua de streaming.

### B. El Monitor Serie solo muestra mensajes de ROM Bootloader
```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x2b (SPI_FAST_FLASH_BOOT)
```
* **Causa:** El cable USB está conectado al puerto físico **USB-UART**, pero la opción **USB CDC On Boot** en Arduino IDE está configurada en `Enabled`.
* **Solución:** Cambia **USB CDC On Boot** a **`Disabled`**, recompila y sube el firmware. Al reiniciar a 115200 baudios verás los mensajes de la aplicación.

### C. `Camera init failed` o `ERROR CAMARA: 0x...`
* **Causa 1:** El cable cinta FPC de la cámara está flojo o invertido.
  * *Acción:* Levanta con cuidado la pestaña plástica del conector en la PCB V1695, reasienta el flex asegurando que los contactos hagan contacto pleno, y cierra la pestaña.
* **Causa 2:** Perfil de pines incorrecto.
  * *Acción:* Asegúrate de tener `#define CAMERA_MODEL_ESP32S3_EYE` en `board_config.h`.

### D. `PSRAM: 0 MB` detectada
* **Causa:** El menú de Arduino IDE tiene seleccionada una opción distinta a `OPI PSRAM`.
* **Solución:** En **Herramientas → PSRAM**, selecciona estrictamente **`OPI PSRAM`**.

---

## 2. Problemas de Red y Conectividad Wi-Fi

### A. El ESP32 imprime puntos continuos y dice `ERROR: No se pudo conectar al WiFi`
* **Causa 1:** El ESP32 solo soporta redes Wi-Fi de **2.4 GHz**. No se conectará a redes exclusivas de 5 GHz.
* **Causa 2:** Credenciales incorrectas en `CameraWebServer_ESP32S3_OV5640.ino`.
* **Causa 3:** Aislamiento de clientes (AP Isolation) habilitado en el router Wi-Fi.

### B. El contenedor Docker no se conecta al ESP32 (`ConnectError` o `Timeout`)
* **Verificación:** Desde tu PC Windows, abre el navegador y escribe:
  ```text
  http://<IP_DEL_ESP32>/capture
  ```
* Si el navegador descarga una foto `.jpg`, la cámara funciona.
* Revisa que en el archivo `.env` la variable `ESP32_BASE_URL` tenga el prefijo `http://` completo (ej. `http://192.168.1.150`).
* Si Docker Desktop corre en WSL2, asegúrate de que el firewall de Windows no esté bloqueando las peticiones salientes entre la subred virtual de Docker y la LAN física.

---

## 3. Problemas en Docker Compose

### A. Error: `Variable not set. Defaulting to a blank string.` o error de variable obligatoria
```text
Error: Debes definir APP_BIND_IP en .env
```
* **Causa:** No creaste el archivo `.env` o dejaste variables vacías.
* **Solución:** Crea tu archivo `.env` copiando `.env.example` y asigna valores válidos (ej. `APP_BIND_IP=127.0.0.1` y `APP_HOST_PORT=8088`).

### B. Error: `bind: address already in use`
* **Causa:** El puerto seleccionado en `APP_HOST_PORT` está siendo utilizado por otro programa en tu PC (Apache de XAMPP, Node.js, etc.).
* **Solución:** Ejecuta en PowerShell:
  ```powershell
  Get-NetTCPConnection -LocalPort <puerto> -ErrorAction SilentlyContinue
  ```
  Elige un número de puerto que no arroje resultados y actualízalo en tu `.env`.
