# Configuración y Flasheo Manual en Arduino IDE

Esta guía detalla la configuración exacta y comprobada para compilar y cargar el firmware en la placa **ESP32-S3 N16R8 (serigrafía V1695)** equipada con cámara **OV5640**.

---

## 1. Conexión de Hardware

* La placa cuenta con dos puertos USB: `USB-UART` y `USB-OTG`.
* Conecta el cable USB al puerto rotulado **USB-UART**.
* Asegúrate de que el cable flex FPC de la cámara OV5640 esté firmemente asentado y con el seguro del conector cerrado.

---

## 2. Ajustes en Arduino IDE 2.x

Ve al menú **Herramientas (Tools)** y configura estrictamente los siguientes parámetros:

| Parámetro | Valor Exacto | Explicación Técnica |
|---|---|---|
| **Placa (Board)** | `ESP32S3 Dev Module` | Perfil genérico para el SoC ESP32-S3 |
| **USB CDC On Boot** | **`Disabled`** | **CRÍTICO:** Si se deja en *Enabled*, la salida por hardware UART0 se redirige al puerto CDC nativo y no verás nada en el Monitor Serie a través del puerto USB-UART |
| **Flash Size** | `16MB (128Mb)` | Capacidad física de la memoria NOR Flash instalada |
| **PSRAM** | `OPI PSRAM` | Habilita los 8 MB de memoria octal externa requeridos para framebuffers de alta resolución |
| **Partition Scheme** | `16M Flash (3MB APP/9.9MB FATFS)` | El servidor web y la pila de cámara superan 1.5 MB; requiere partición de aplicación de al menos 3 MB |
| **Upload Speed** | `921600` | Velocidad de programación (bajar a 115200 si hay ruido en el cable) |
| **USB DFU On Boot** | `Disabled` | Mantener por defecto |
| **Upload Mode** | `UART0 / Hardware CDC` | Según aparezca en tu versión de core |
| **Puerto (Port)** | Seleccionar el puerto COM asignado (ej. `COM6`) | Asignado por el controlador USB-Serial |

---

## 3. Estructura del Proyecto en Arduino IDE

Para compilar sin errores de cabeceras faltantes, el sketch debe tener estos cuatro archivos en su pestaña:

```text
CameraWebServer_ESP32S3_OV5640/
├── CameraWebServer_ESP32S3_OV5640.ino
├── board_config.h
├── camera_pins.h
└── app_httpd.cpp
```

* Los archivos `camera_pins.h` y `app_httpd.cpp` provienen directamente del paquete ESP32 oficial (**Archivo → Ejemplos → ESP32 → Camera → CameraWebServer**).
* En `board_config.h` debe estar activo:
  ```cpp
  #define CAMERA_MODEL_ESP32S3_EYE
  ```
  *(Este perfil mapea exactamente los pines GPIO de la PCB V1695)*.

---

## 4. Pasos de Compilación y Verificación

1. Abre `CameraWebServer_ESP32S3_OV5640.ino`.
2. Edita las variables de red local:
   ```cpp
   const char* ssid = "TU_NOMBRE_WIFI";
   const char* password = "TU_CLAVE_WIFI";
   ```
3. Presiona el botón **Subir** (Flecha hacia la derecha).
4. Espera a que la barra de progreso complete el 100% y veas:
   ```text
   Hash of data verified.
   Leaving...
   Hard resetting via RTS pin...
   ```
5. Abre el **Monitor Serie** (**Herramientas → Monitor Serie**).
6. Ajusta la velocidad a **115200 baudios**.
7. Si el monitor está en blanco, presiona una vez el pulsador físico **RESET** (o RST) en la placa.
8. La salida esperada debe ser:
   ```text
   ==========================================
     ESP32-S3 N16R8 + OV5640 - Servidor Camara
   ==========================================
   FLASH DETECTADA: 16 MB
   PSRAM DETECTADA: 8 MB
   Inicializando controlador de camara...
   CAMARA INICIALIZADA CORRECTAMENTE.
   SENSOR PID DETECTADO: 0x5640
   Captura de prueba exitosa (35210 bytes).
   Conectando a red Wi-Fi: JAPON
   ......
   WIFI CONECTADO EXITOSAMENTE
   ==========================================
     ESP32-S3 LISTO PARA TRANSMITIR
     IP LOCAL ASIGNADA: http://192.168.1.150
     Endpoint para capturas: /capture
   ==========================================
   ```
9. Anota la IP asignada (ejemplo: `http://192.168.1.150`) para ingresarla en el `.env` de Docker.
