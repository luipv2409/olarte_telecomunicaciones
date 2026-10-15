# Manual de replicación: ESP32-S3 N16R8 + OV5640 + CameraWebServer

> **Estado:** configuración reportada como funcional por el usuario (15 de octubre de 2026).  
> **Destinatario:** agente de IA, desarrollador o técnico que deba reproducir la transmisión de video por Wi-Fi.

## 1. Objetivo y resultado comprobado

Configurar una placa **ESP32-S3 N16R8**, con cámara **OV5640** conectada mediante cinta flexible (FPC), para emitir video en tiempo real mediante el ejemplo **CameraWebServer** del paquete ESP32 para Arduino. El video se visualiza desde el navegador de una computadora conectada a la misma red Wi-Fi.

El usuario confirmó que el sistema **funciona correctamente** después de cargar el programa y la configuración descritos aquí. No se ha medido FPS, latencia ni estabilidad a largo plazo.

## 2. Hardware identificado

| Elemento | Dato |
|---|---|
| Microcontrolador | ESP32-S3 |
| Flash | 16 MB, comprobados mediante `ESP.getFlashChipSize()` |
| PSRAM | 8 MB, comprobados mediante `ESP.getPsramSize()` |
| Cámara | OV5640, 5 MP, conexión FPC (declarado por usuario) |
| Identificación de PCB | `V1695`, `127294G_Y1127_231016` |
| Inscripciones de PCB | `Camera`, `SD Card`, `PSRAM` |
| Conexiones USB visibles | `USB-UART` y `USB-OTG` |
| Puerto usado en la prueba | **USB-UART** |
| Puerto COM observado | COM6 (puede variar) |

**Nota crítica:** aunque la PCB no está identificada comercialmente como ESP32-S3-EYE, **el usuario confirmó que funcionó con `CAMERA_MODEL_ESP32S3_EYE`**. Mantener ese perfil para reproducir la configuración probada. No inferir otro pinout por el nombre de la placa.

## 3. Entorno y configuración de Arduino IDE

Se observó **Arduino IDE 2.3.10** en una captura del entorno Windows. La versión exacta del paquete de placas `esp32` de Espressif no quedó registrada; para reproducibilidad estricta, verificarla y anotarla en el nuevo entorno.

1. Instalar Arduino IDE y el paquete de placas **esp32 by Espressif Systems** desde el Gestor de placas.
2. Conectar el cable al puerto físico **USB-UART** de la PCB.
3. Seleccionar **Tools / Herramientas → Board → ESP32S3 Dev Module**.
4. Ajustar:

| Opción | Valor probado / recomendado |
|---|---|
| Board | `ESP32S3 Dev Module` |
| USB CDC On Boot | **Disabled** (crítico con USB-UART) |
| Flash Size | `16MB (128Mb)` |
| PSRAM | `OPI PSRAM` |
| Partition Scheme | Esquema de flash de 16 MB con **APP >= 3 MB** (en captura: `16M Flash (3MB APP/9.9MB FATFS)` o similar) |
| Serial Monitor | `115200` baudios |
| Puerto | COM del adaptador USB-UART, COM6 en la sesión original |
| Upload Mode | `UART0 / Hardware CDC`, si aparece esa opción |

Otras opciones pueden conservar sus valores por defecto. El usuario confirmó que **USB CDC On Boot = Disabled** hizo visibles los mensajes de la aplicación a través de USB-UART.

## 4. Archivos necesarios

Abrir **Archivo → Ejemplos → ESP32 → Camera → CameraWebServer**. Guardar una copia editable del ejemplo.

El proyecto debe contener, como mínimo, estos archivos del ejemplo:

```text
CameraWebServer/
├── CameraWebServer.ino   # reemplazar por el código de la sección 5
├── board_config.h       # reemplazar por el código de la sección 6
├── camera_pins.h        # conservar original del paquete ESP32
└── app_httpd.cpp        # conservar original del paquete ESP32
```

El archivo `app_httpd.cpp` implementa `startCameraServer()` y la interfaz web. **No basta con pegar el `.ino` en un proyecto vacío** si faltan estos archivos. Dependiendo de la versión del ejemplo, puede haber otros archivos auxiliares: conservarlos.

## 5. Código completo: `CameraWebServer.ino`

```cpp
#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include "board_config.h"

// Credenciales: introducir localmente; NO publicar contraseñas en repositorios.
const char* ssid = "TU_SSID";
const char* password = "TU_PASSWORD";

// Implementadas por app_httpd.cpp del ejemplo oficial.
void startCameraServer();
void setupLedFlash();

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("============================");
  Serial.println("ESP32-S3 N16R8 + OV5640");
  Serial.println("============================");

  Serial.printf("FLASH: %u MB\n",
                ESP.getFlashChipSize() / 1048576);
  Serial.printf("PSRAM: %u MB\n",
                ESP.getPsramSize() / 1048576);

  camera_config_t config = {};

  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;

  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;

  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;

  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // Resolución inicial para streaming fluido.
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;

  if (psramFound()) {
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.fb_count = 2;
    config.grab_mode = CAMERA_GRAB_LATEST;
  } else {
    config.fb_location = CAMERA_FB_IN_DRAM;
    config.fb_count = 1;
    config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  }

  Serial.println("Inicializando camara...");

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("ERROR CAMARA: 0x%x\n", err);
    Serial.println("Revisar pines GPIO y conexion.");
    return;
  }

  Serial.println("CAMARA INICIALIZADA");

  sensor_t *s = esp_camera_sensor_get();
  if (s != nullptr) {
    Serial.printf("SENSOR PID: 0x%04X\n", s->id.PID);
    s->set_framesize(s, FRAMESIZE_VGA);
  }

  Serial.println("Probando captura...");
  camera_fb_t *fb = esp_camera_fb_get();
  if (fb == nullptr) {
    Serial.println("ERROR: No se pudo capturar imagen");
    return;
  }

  Serial.printf("CAPTURA CORRECTA: %u bytes\n",
                (unsigned int)fb->len);
  esp_camera_fb_return(fb);

  Serial.println("Conectando WiFi...");
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);

  unsigned long inicio = millis();
  while (WiFi.status() != WL_CONNECTED &&
         millis() - inicio < 20000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println();
    Serial.println("ERROR: No se pudo conectar al WiFi");
    return;
  }

  Serial.println();
  Serial.println("WIFI CONECTADO");

  startCameraServer();

  Serial.println();
  Serial.println("============================");
  Serial.println("CAMARA LISTA");
  Serial.print("ABRIR EN COMPUTADORA: http://");
  Serial.println(WiFi.localIP());
  Serial.println("============================");
}

void loop() {
  delay(1000);
}
```

**Credenciales usadas en la prueba:** SSID `JAPON`. La contraseña fue proporcionada en la conversación original y se **omite deliberadamente de este manual portable** por seguridad. El agente debe solicitarla o leerla desde una configuración local segura, sin imprimirla en logs ni subirla a Git.

## 6. Código completo: `board_config.h`

```cpp
#ifndef BOARD_CONFIG_H
#define BOARD_CONFIG_H

// Perfil que funcionó en la PCB V1695 con OV5640.
#define CAMERA_MODEL_ESP32S3_EYE

#include "camera_pins.h"

#endif
```

**No modificar `camera_pins.h` a ciegas.** Los valores GPIO provienen del perfil `CAMERA_MODEL_ESP32S3_EYE` incluido en la versión instalada del paquete ESP32. Para replicación exacta entre versiones, guardar una copia del archivo `camera_pins.h` del entorno que funcionó y registrar la versión del core. Si una actualización cambia el pinout, recuperar la versión que funcionaba.

## 7. Compilación, carga y prueba

1. Abrir `CameraWebServer.ino` en Arduino IDE.
2. Confirmar que los archivos auxiliares aparecen como pestañas del mismo proyecto.
3. Configurar el SSID y contraseña locales.
4. Seleccionar las opciones de la sección 3.
5. Pulsar **Subir** y esperar la verificación de escritura.
6. Abrir **Monitor serie**, a `115200` baudios.
7. Si hace falta, pulsar una vez el botón **RESET**.
8. Comprobar que aparecen `CAMARA INICIALIZADA`, `CAPTURA CORRECTA`, `WIFI CONECTADO` y una IP.
9. Conectar la PC a la misma red Wi-Fi, abrir `http://<IP_QUE_MUESTRA_EL_MONITOR>` en el navegador y pulsar **Start Stream**.

Salida de referencia (ilustrativa; los números varían):

```text
ESP-ROM:esp32s3-20210327
...
ESP32-S3 N16R8 + OV5640
FLASH: 16 MB
PSRAM: 8 MB
Inicializando camara...
CAMARA INICIALIZADA
SENSOR PID: 0x5640
Probando captura...
CAPTURA CORRECTA: 35000 bytes
Conectando WiFi...
WIFI CONECTADO
CAMARA LISTA
ABRIR EN COMPUTADORA: http://192.168.1.100
```

La IP `192.168.1.100` es **solo un ejemplo**. El PID mostrado es el esperado para OV5640, no un registro de lectura aportado por el usuario.

## 8. Diagnóstico documentado: lo que pasó en la sesión

### 8.1 El monitor solo mostraba el ROM bootloader

```text
ESP-ROM:esp32s3-20210327
Build:Mar 27 2021
rst:0x1 (POWERON),boot:0x2b (SPI_FAST_FLASH_BOOT)
...
entry 0x403c88b8
```

Este mensaje **no significa por sí solo que la cámara esté dañada**. La aplicación puede ejecutarse pero sus mensajes `Serial` no llegar al puerto monitorizado. En el entorno original, el usuario conectaba mediante **USB-UART**, pero tenía **USB CDC On Boot = Enabled**.

**Solución comprobada:** cambiar `USB CDC On Boot` a **Disabled**, volver a cargar el programa y abrir el monitor a 115200. Después se vieron mensajes de aplicación correctamente.

### 8.2 Prueba mínima de puerto serie y memoria

Código diagnóstico que funcionó:

```cpp
#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  delay(2000);
  Serial.println("======================");
  Serial.println("ESP32-S3 CONECTADO");
  Serial.println("======================");
  Serial.printf("FLASH: %u MB\n", ESP.getFlashChipSize() / 1048576);
  Serial.printf("PSRAM: %u MB\n", ESP.getPsramSize() / 1048576);
}

void loop() {
  Serial.println("ESP32-S3 FUNCIONANDO CORRECTAMENTE");
  delay(2000);
}
```

**Salida efectivamente comunicada por el usuario:**

```text
ESP32-S3 CONECTADO
FLASH: 16 MB
PSRAM: 8 MB
ESP32-S3 FUNCIONANDO CORRECTAMENTE
ESP32-S3 FUNCIONANDO CORRECTAMENTE
ESP32-S3 FUNCIONANDO CORRECTAMENTE
```

### 8.3 `Hard resetting via RTS pin...`

No es error. La salida de subida mostró:

```text
Wrote 307200 bytes (174247 compressed) ...
Verifying written data...
Hash of data verified.
Hard resetting via RTS pin...
```

La grabación y la verificación finalizaron correctamente.

### 8.4 Otros errores posibles

| Síntoma | Causa probable | Acción |
|---|---|---|
| `Camera init failed` / `ERROR CAMARA: 0x...` | Pines, alimentación, cinta FPC o perfil equivocado | Confirmar `CAMERA_MODEL_ESP32S3_EYE`, asiento del flex, versión del core y alimentación |
| `PSRAM: 0 MB` | PSRAM deshabilitada o modo equivocado | Seleccionar `OPI PSRAM` y reiniciar |
| Captura falla | Sensor no entrega frames, alimentación o configuración | Verificar inicialización, reducir resolución, revisar cable FPC |
| Wi-Fi no conecta | SSID/clave, alcance, red incompatible | Verificar red de 2.4 GHz y credenciales; revisar que no haya aislamiento de clientes |
| IP inaccesible desde PC | Red distinta, aislamiento de clientes o firewall | Poner PC y placa en misma LAN y probar URL exacta |
| Solo aparece `ESP-ROM` | Puerto serie/USB CDC no coinciden | Con USB-UART, `USB CDC On Boot = Disabled` |
| Compilación: `startCameraServer` indefinido | Falta `app_httpd.cpp` | Restaurar el ejemplo completo CameraWebServer |
| Compilación: `Y2_GPIO_NUM` indefinido | Falta `camera_pins.h` o perfil incorrecto | Restaurar archivo original y revisar `board_config.h` |
| Video entrecortado | Wi-Fi, resolución o calidad demasiado exigentes | Empezar en VGA y JPEG quality 12; acercar placa al router |

## 9. Ajustes del streaming y precauciones

- Resolución inicial: `FRAMESIZE_VGA` (640×480), adecuada para primera prueba.
- `jpeg_quality = 12`: en este driver, números menores suelen representar más calidad y mayor tamaño de imagen.
- `fb_count = 2` con PSRAM para captura continua; `CAMERA_GRAB_LATEST` prioriza cuadros recientes.
- `xclk_freq_hz = 20000000`: reloj externo de 20 MHz, según código que funcionó.
- El sensor OV5640 puede soportar mayor resolución, pero **no está validado que el streaming a 5 MP sea fluido** en este montaje. Aumentar resolución gradualmente y medir.
- El ejemplo ofrece interfaz de control web. Las opciones disponibles pueden variar según versión del paquete y sensor.
- La URL del servidor debe usarse **solo en una red local de confianza**. El ejemplo CameraWebServer normalmente no incluye autenticación de usuarios ni cifrado HTTPS. No exponer el puerto al Internet público ni reenviarlo desde el router.
- Evitar subir credenciales Wi-Fi a repositorios o compartir capturas donde aparezcan.

## 10. Instrucciones explícitas para otro agente de IA

**Contexto inmutable:** El usuario ya obtuvo video funcionando con ESP32-S3 N16R8, PCB V1695, cámara OV5640, PSRAM OPI 8 MB, flash 16 MB, USB-UART y `CAMERA_MODEL_ESP32S3_EYE`. No reiniciar la investigación de pinout sin evidencia de falla.

**Plan del agente:**

1. Reproducir el entorno de Arduino IDE y el ejemplo CameraWebServer completo.
2. Mantener `USB CDC On Boot = Disabled` mientras se utilice USB-UART.
3. Mantener `CAMERA_MODEL_ESP32S3_EYE` y los archivos auxiliares del ejemplo.
4. Sustituir las credenciales Wi-Fi mediante configuración local, sin registrarlas en respuestas ni repositorios.
5. Compilar, cargar, verificar mensajes por UART y obtener la IP asignada.
6. Probar captura y transmisión MJPEG desde el navegador.
7. Si falla, recopilar **mensaje exacto**, versión del core ESP32, configuración del IDE y contenido de `camera_pins.h` antes de modificar hardware o GPIO.
8. Para integrar la cámara en otra aplicación, conservar primero un respaldo de este firmware funcional. Evitar alterar la configuración validada hasta contar con una prueba de regresión.

### Criterios de aceptación

- [ ] Carga del firmware verificada (`Hash of data verified`).
- [ ] Mensajes `Serial` visibles a 115200 en USB-UART.
- [ ] Flash detectada: 16 MB.
- [ ] PSRAM detectada: 8 MB.
- [ ] Cámara inicializa sin error.
- [ ] Se obtiene un framebuffer JPEG válido.
- [ ] Wi-Fi se conecta y entrega IP local.
- [ ] El navegador de la PC muestra video con **Start Stream**.

### Datos pendientes para reproducibilidad estricta

- Versión exacta del paquete `esp32 by Espressif Systems`.
- Copia exacta del `camera_pins.h` del core que funcionó.
- Revisión/versión del firmware del sensor, si aplica.
- Métricas de FPS, latencia y duración de prueba (no medidas).

---

**Conclusión:** Esta es una receta funcional **confirmada por el usuario** para video local mediante CameraWebServer. La diferencia decisiva durante el diagnóstico fue corregir la salida serie por USB-UART; el perfil `CAMERA_MODEL_ESP32S3_EYE` y el programa de captura/servidor resultaron funcionales en esta unidad concreta.
