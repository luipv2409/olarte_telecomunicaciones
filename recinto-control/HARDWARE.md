# HARDWARE.md — Mapa de Conexiones, Alimentación y Seguridad Eléctrica

> **ESTADO GENERAL:** Fase 0 y Fase 1 preparadas por software. Conexión de sensores físicos: **ESTRICTAMENTE PENDIENTE DE VALIDACIÓN**.

---

## 1. Arquitectura de Alimentación y Tierras

```text
[ Adaptador DC 9V/12V ] ───> [ Módulo MB102 ] ───> Riel Protoboard (3.3V) ───> VCC Sensor IR
                                     │
                                     ├───> GND Protoboard ──────────┐
                                                                    │ (GND Común)
[ PC / Cargador USB-C ] ───> [ Puerto USB-C ESP32-S3 ] ───> GND ESP32 ─────┘
```

### Reglas críticas de alimentación:
1. **NO utilizar el módulo LM2596 por ahora:** Se utiliza exclusivamente el módulo de protoboard **MB102** con fuente de pared DC 9/12 V para alimentar el protoboard.
2. **ESP32-S3 alimentado de forma independiente:** Se mantiene conectado por su cable USB para programación y telemetría UART.
3. **Masa Común (GND Obligatorio):** Conectar un cable jumper entre el pin **GND del ESP32-S3** y el riel **GND azul del protoboard**.
4. **NUNCA unir los positivos:** Jamás conectar el pin `5V` o `3V3` del ESP32 con las salidas de 5V o 3.3V del módulo MB102. Cada fuente entrega energía a sus propios rieles.
5. **Verificación con Multímetro:** Antes de insertar cualquier sensor, mide con multímetro la tensión entre el riel positivo y GND del MB102 asegurando que marque **3.3 V exactos** (jumper del MB102 en posición 3.3V).
6. **Advertencia del Servo SG90/MG90S (Fases futuras):** Los servomotores generan picos de corriente inductivos superiores a 600-800 mA. **Nunca** se alimentará el servo desde el pin 3.3V del ESP32 ni se conectará a la placa hasta que se evalúe su fuente en la Fase 4.

---

## 2. Mapa de Asignación GPIO en ESP32-S3 (PCB V1695)

> [!CAUTION]
> La cámara OV5640 y la memoria PSRAM OPI de 8 MB ocupan la inmensa mayoría de los GPIOs internos. Usar un pin reservado provocará reinicios en bucle (*panic core dump*) o fallos en el bus DMA de la cámara.

| Periférico | Pin GPIO | Estado | Nivel Lógico | Notas Técnicas |
|---|---|---|---|---|
| **Cámara OV5640 (D0-D7)** | GPIO 11, 9, 8, 10, 12, 18, 17, 16 | **OCUPADO** | 3.3 V | Bus de datos paralelo DVP de la cámara |
| **Cámara OV5640 (Control)** | GPIO 15 (XCLK), 13 (PCLK), 6 (VSYNC), 7 (HREF) | **OCUPADO** | 3.3 V | Relojes y sincronismo vertical/horizontal |
| **Cámara OV5640 (SCCB/I2C)** | GPIO 4 (SDA), GPIO 5 (SCL) | **OCUPADO** | 3.3 V | Bus I2C de configuración del sensor OV5640 |
| **Memoria PSRAM OPI 8MB** | GPIO 33, 34, 35, 36, 37 | **OCUPADO** | Interno | Bus de datos Octal SPI. No tocar |
| **Puerto USB-UART** | GPIO 43 (U0TXD), GPIO 44 (U0RXD) | **OCUPADO** | 3.3 V | Monitor serie a 115200 baudios |
| **Sensor IR #1 (Fase 1)** | **GPIO 1** *(Candidato A)* o **GPIO 2** *(Candidato B)* | **PENDIENTE DE VALIDACIÓN** | 3.3 V | Entrada digital. Requiere jumper de MB102 a 3.3V |
| **Lector RFID (Fase 2)** | GPIO 14, 21, 47, 48 *(Candidatos SPI)* | **FUTURO** | 3.3 V | SCK, MISO, MOSI, SDA. No conectar aún |
| **LED Verde / Rojo (Fase 3)** | Por definir | **FUTURO** | 3.3 V | Requiere resistencias de 220 Ω / 330 Ω |
| **Buzzer Activo 5V (Fase 3)** | Por definir | **FUTURO** | 3.3 V a base | Requiere transistor 2N2222A y diodo de protección |
| **Servo Maqueta (Fase 4)** | Por definir (PWM LEDC) | **FUTURO** | Señal 3.3 V | Alimentación motriz 5V externa separada |

---

## 3. Conexión del Sensor Infrarrojo #1 (Fase 1)

* **Pin VCC del IR:** Al riel **3.3V** del protoboard (alimentado por MB102).
* **Pin GND del IR:** Al riel **GND** del protoboard.
* **Pin OUT del IR:** Al GPIO seleccionado (ej. **GPIO 1**) una vez confirmada la serigrafía física.

### Lógica de disparo del módulo FC-51:
* **Sin obstáculo (despejado):** El LED indicador del sensor está apagado; el pin OUT entrega **HIGH (3.3V)**.
* **Con obstáculo (interrumpido):** El LED indicador del sensor se enciende; el pin OUT conmuta a **LOW (0V)**.
* Ajusta el potenciómetro azul del módulo para regular la distancia de detección a unos 5-10 cm.

---

## 4. PENDIENTE DE VALIDACIÓN FÍSICA

Antes de cambiar `IR_ENABLED = true` en el firmware:
1. **Modelo exacto de sensor:** Confirmar si el módulo es FC-51 (tres pines: VCC, GND, OUT) o TCRT5000 (cuatro pines con salida analógica y digital).
2. **Inspección de serigrafía en la PCB V1695:** Verificar qué etiquetas exactas tienen los pines accesibles en las regletas de la placa (por ejemplo: `G1`, `G2`, `G21`, `G47`, `G48`).
3. **Medición con voltímetro:** Confirmar que entre el pin OUT del sensor y GND nunca existan más de 3.3 V cuando el sensor se dispare.
