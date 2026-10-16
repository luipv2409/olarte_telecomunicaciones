# FASE 2: Integración de Lector RFID RC522 en ESP32-S3 (PCB V1695)

Este manual documenta la integración física y lógica del lector **RFID RC522** junto a la cámara **OV5640** y el sensor **Infrarrojo digital**, sin interferir con los periféricos de la placa ni accionar compuertas físicas.

---

## 1. Análisis de Seguridad y Compatibilidad de Pines (PCB V1695)

Se han analizado exhaustivamente los 5 pines candidatos propuestos: **GPIO 2, 14, 21, 47 y 48**:

| GPIO | Función asignada (RC522) | Dirección | Estado en la PCB V1695 | Conclusiones técnicas |
|---|---|---|---|---|
| **GPIO 14** | **SCK (Clock SPI)** | Salida ESP32 | Expuesto en regleta izquierda (junto a `5V` y `0`). | Pin SPI nativo de alta velocidad. Libre de conflictos. |
| **GPIO 21** | **MOSI (Master Out)** | Salida ESP32 | Expuesto en regleta derecha (sobre `20` y `19`). | Señal digital limpia. No interfiere con microSD sin tarjeta. |
| **GPIO 47** | **MISO (Master In)** | Entrada ESP32 | Expuesto en regleta derecha (entre `21` y `48`). | Línea limpia de alta impedancia, sin cargas parásitas. |
| **GPIO 2** | **SDA (SS / Chip Select)** | Salida ESP32 | Conectado al LED SMD **`IO2`** en la PCB. | Al ser salida *push-pull*, maneja el SS sin problemas y hace parpadear el LED `IO2` al leer tarjetas. |
| **GPIO 48** | **RST (Reset)** | Salida ESP32 | Conectado al LED SMD **`48`** en la PCB. | Nivel ALTO permanente durante operación; mantiene encendido el LED `48` como indicador de lector activo. |

### Periféricos preservados:
* **Cámara OV5640:** Utiliza GPIO 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17 y 18. **Intactos.**
* **Sensor IR #1:** Utiliza GPIO 1. **Intacto.**
* **Memoria PSRAM Octal 8MB:** Utiliza GPIO 33, 34, 35, 36 y 37. **Intactos.**
* **Consola USB-UART:** Utiliza GPIO 43 y 44. **Intactos.**
* **Ranura MicroSD:** Las líneas SDMMC (GPIO 38, 39, 40) quedan reservadas y sin colisión.

---

## 2. Diagrama de Cableado Pin a Pin (RC522)

> [!CAUTION]
> **REGLA DE ORO DE ALIMENTACIÓN:**
> El pin **VCC del RC522 se alimenta EXCLUSIVAMENTE a 3.3 V** (desde el riel regulado del MB102 a 3.3V o pin 3V3). Conectar el módulo RC522 a 5V quema irreversiblemente el integrado MFRC522.

| Pin del Lector RC522 | Conexión en Protoboard / ESP32-S3 | Nivel eléctrico | Notas |
|---|---|---|---|
| **VCC** | **Riel 3.3V** del MB102 (o pin `3V3` de la placa) | **3.3 V** | Mide con multímetro antes de conectar |
| **RST** | Pin **GPIO 48** del ESP32-S3 | 3.3 V | Línea de Reset |
| **GND** | **Riel GND** común (unido al GND del ESP32) | 0 V | Masa de referencia obligatoria |
| **IRQ** | *NO CONECTAR* | — | No se utiliza en este diseño |
| **MISO** | Pin **GPIO 47** del ESP32-S3 | 3.3 V | Master In Slave Out |
| **MOSI** | Pin **GPIO 21** del ESP32-S3 | 3.3 V | Master Out Slave In |
| **SCK** | Pin **GPIO 14** del ESP32-S3 | 3.3 V | Reloj del bus SPI |
| **SDA (SS)** | Pin **GPIO 2** del ESP32-S3 | 3.3 V | Chip Select del bus SPI |

---

## 3. Preparación del Entorno en Arduino IDE

1. Abre Arduino IDE.
2. Ve a **Herramientas → Administrador de Bibliotecas** (o `Ctrl + Shift + I`).
3. Busca **`MFRC522`** de **GithubCommunity / Miguel Balboa**.
4. Haz clic en **Instalar**.
5. Abre el sketch [`Fase2_ESP32_IR_RFID_Camera.ino`](file:///c:/xampp/htdocs/OLARTE/recinto-control/firmware/Fase2_ESP32_IR_RFID_Camera/Fase2_ESP32_IR_RFID_Camera.ino).
6. Si tienes `secrets.h`, confirma tus credenciales Wi-Fi; de lo contrario usa los valores por defecto en el sketch.
7. Verifica los ajustes de placa:
   * **Placa:** `ESP32S3 Dev Module`
   * **USB CDC On Boot:** `Disabled`
   * **Flash Size:** `16MB (128Mb)`
   * **PSRAM:** `OPI PSRAM`
   * **Partition Scheme:** `16M Flash (3MB APP/9.9MB FATFS)`
   * **Monitor Serie:** `115200 baudios`
8. Compila y sube el firmware.

---

## 4. Criterios de Aceptación y Diagnóstico por Monitor Serie

Al reiniciar el ESP32, el monitor serie debe reportar:

```text
==================================================
  ESP32-S3 N16R8 - FASE 2: CAM + IR + RFID RC522
==================================================
Flash detectada: 16 MB
PSRAM detectada: 8 MB
[OK] Sensor IR inicializado en GPIO 1 (Estado inicial: LIBRE)
Inicializando bus SPI para RFID RC522...
  -> SCK: GPIO 14 | MOSI: GPIO 21 | MISO: GPIO 47 | SDA(SS): GPIO 2 | RST: GPIO 48
  -> Registro VersionReg RC522: 0x92 (MFRC522 v2.0 - OK)
Inicializando camara OV5640...
[OK] Camara OV5640 inicializada correctamente.
Conectando a red Wi-Fi: JAPON
[OK] WIFI CONECTADO
  IP Local Camara: http://192.168.1.111
```

### Diagnóstico del valor `VersionReg`:
* **`0x92` o `0x91`:** Comunicación SPI perfecta con el chip MFRC522.
* **`0x00` o `0xFF`:** Fallo de comunicación. Apaga el sistema y verifica cables en `GPIO 14, 21, 47, 2, 48` y los 3.3V/GND.

### Prueba con tarjeta:
Al acercar una tarjeta o llavero al lector, el monitor serie imprimirá:
```text
----------------------------------------
[RFID] -> ¡TARJETA DETECTADA!
  UID HEX: 3A 8B 1F 0C (Tamano: 4 bytes)
  Tipo PICC: MIFARE 1KB
----------------------------------------
  -> [HTTP 200] Evento 'CARD_SCANNED' [RFID_1] aceptado por el backend.
```
