# Firmware ESP32-S3 (N16R8) + Cámara OV5640 (V1695)

Este directorio contiene los archivos de firmware verificados para la placa ESP32-S3 con 16 MB Flash, 8 MB PSRAM OPI y cámara OV5640 de 5 MP conectada por cinta FPC.

## Archivos del firmware

1. **`CameraWebServer_ESP32S3_OV5640.ino`**: Sketch principal con inicialización del sensor OV5640, PSRAM y servidor HTTP.
2. **`board_config.h`**: Asigna el perfil funcional `#define CAMERA_MODEL_ESP32S3_EYE` que mapea los pines GPIO correctos.
3. **Archivos dependientes del núcleo ESP32**:
   - `camera_pins.h`
   - `app_httpd.cpp`
   
> **Nota técnica:** Para compilar, estos dos últimos archivos deben estar en la misma carpeta del sketch. La forma más sencilla de obtenerlos es abrir en Arduino IDE:  
> **Archivo → Ejemplos → ESP32 → Camera → CameraWebServer** y copiar los archivos o reemplazar el `.ino` y `board_config.h` con los suministrados en este repositorio.

---

## Ajustes obligatorios en Arduino IDE 2.x

Conecta el cable al puerto **USB-UART** de la placa ESP32:

* **Placa:** `ESP32S3 Dev Module`
* **USB CDC On Boot:** **`Disabled`** *(Si está en Enabled no verás ningún mensaje por USB-UART en el monitor serie)*
* **Flash Size:** `16MB (128Mb)`
* **PSRAM:** `OPI PSRAM`
* **Partition Scheme:** `16M Flash (3MB APP/9.9MB FATFS)` o similar con APP >= 3 MB
* **Upload Speed:** `921600` (o `115200` si hay errores de transmisión)
* **Monitor Serie:** `115200` baudios

---

## Instrucciones de carga manual

1. Abre `CameraWebServer_ESP32S3_OV5640.ino` en Arduino IDE.
2. Configura las variables `ssid` y `password` con el nombre y contraseña de tu red Wi-Fi (2.4 GHz).
3. Selecciona el puerto COM correspondiente a tu interfaz USB-UART.
4. Presiona el botón **Subir** (Upload) en Arduino IDE.
5. Al terminar la carga, abre el **Monitor Serie** a 115200 baudios.
6. Presiona una vez el botón físico **RESET** en la placa.
7. Observa la salida serie hasta ver:
   ```text
   CAMARA INICIALIZADA CORRECTAMENTE.
   WIFI CONECTADO EXITOSAMENTE
   IP LOCAL ASIGNADA: http://192.168.x.xxx
   ```
8. Copia esa dirección IP para colocarla en la variable `ESP32_BASE_URL` del archivo `.env` de la aplicación Docker.
