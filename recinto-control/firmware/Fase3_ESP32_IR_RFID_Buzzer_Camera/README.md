# FASE 3: Integración de Señalización Acústica (Buzzer Activo 5V / 2N2222A en GPIO 42)

Este proyecto integra y unifica el sistema completo de control de acceso:
1. **Cámara OV5640 5MP:** Streaming de video y capturas JPEG locales para inferencia YOLOv8.
2. **Sensor Infrarrojo Digital (GPIO 1):** Detección de paso no bloqueante con filtro *debounce*.
3. **Lector RFID RC522 (Bus SPI):** Lectura instantánea de tarjetas y credenciales con validación de políticas.
4. **Buzzer Activo 5V (GPIO 42 con Driver NPN 2N2222A):** Confirmación acústica inmediata (bip de arranque, éxito de socio activo, alarma de tarjeta bloqueada).
5. **Telemetría de Hardware en Vivo:** Detección de cortocircuitos (`0xEE`), cables sueltos (`0x00`/`0xFF`) y reporte en Heartbeat hacia backend Docker.

---

## 1. Mapeo de Hardware y Conexiones (PCB V1695)

| Periférico | Pin GPIO | Estado | Nivel Eléctrico | Función |
|---|---|---|---|---|
| **Sensor IR #1** | **GPIO 1** | **ACTIVO** | 3.3 V | Entrada digital (`INPUT_PULLUP`). LOW = Detectado, HIGH = Libre |
| **RFID SCK** | **GPIO 14** | **ACTIVO** | 3.3 V | Reloj del bus SPI |
| **RFID MOSI** | **GPIO 21** | **ACTIVO** | 3.3 V | Salida de datos hacia el RC522 |
| **RFID MISO** | **GPIO 47** | **ACTIVO** | 3.3 V | Entrada de datos desde el RC522 (¡NUNCA usar para buzzer!) |
| **RFID SDA (SS)**| **GPIO 2** | **ACTIVO** | 3.3 V | Slave Select (hace parpadear LED `IO2` en lectura) |
| **RFID RST** | **GPIO 48** | **ACTIVO** | 3.3 V | Reset (mantiene encendido LED `48` en azul) |
| **Buzzer Activo** | **GPIO 42** | **ACTIVO** | 3.3 V (Base) | Driver NPN 2N2222A con $R_B = 1\text{ k}\Omega$. Conmuta masa a 3.3V |
| **Cámara OV5640**| GPIO 4 a 18 | **ACTIVO** | 3.3 V | Bus DVP, relojes y bus SCCB/I2C |
| **PSRAM Octal** | GPIO 33 a 37| **ACTIVO** | Interno | 8 MB OPI PSRAM de alta velocidad |
| **UART0 Serie** | GPIO 43 / 44 | **ACTIVO** | 3.3 V | Consola serie USB-UART a 115200 baudios |

---

## 2. Esquema del Driver del Buzzer (2N2222A)

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

**Patillaje del Transistor 2N2222A (TO-92, cara plana mirando de frente):**
* **Pin 1 (Izquierda):** Emisor $\rightarrow$ GND común.
* **Pin 2 (Centro):** Base $\rightarrow$ Resistencia de $1\text{ k}\Omega$ (Marrón-Negro-Rojo) $\rightarrow$ Pin 42 del ESP32-S3.
* **Pin 3 (Derecha):** Colector $\rightarrow$ Pata corta `(-)` del buzzer.
* **Pata larga `(+)` del Buzzer:** Riel de 3.3V de la protoboard.

---

## 3. Patrones Acústicos Implementados

| Evento | Función en Firmware | Patrón |
|---|---|---|
| **Arranque del Sistema** | `beepStartup()` | 1 pulso de 80 ms |
| **Socio Activo #2 (`6C8D1B06`)** | `beepSuccess()` | 1 pulso de bienvenida de 150 ms |
| **Socio Bloqueado #1 (`73230E06`)** | `beepDenied()` | 3 pulsos rápidos de alarma (80 ms c/u) |
| **Tarjeta Desconocida** | `beepDenied()` | 3 pulsos rápidos de alarma (80 ms c/u) |

---

## 4. Ajustes en Arduino IDE 2.x

* **Placa:** `ESP32S3 Dev Module`
* **USB CDC On Boot:** `Disabled`
* **Flash Size:** `16MB (128Mb)`
* **PSRAM:** `OPI PSRAM`
* **Partition Scheme:** `16M Flash (3MB APP / 9.9MB FATFS)`
* **Upload Speed:** `921600` (o `115200`)
* **Monitor Serie:** `115200 baudios`
