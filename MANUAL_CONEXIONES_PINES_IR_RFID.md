# GUÍA DEFINITIVA DE CONEXIÓN FÍSICA: SENSOR INFRARROJO + LECTOR RFID RC522
## Placa: ESP32-S3 N16R8 (PCB V1695) con Cámara OV5640 5MP

---

## ⚠️ REGLAS CRÍTICAS DE ELECTRICIDAD (LEER ANTES DE CABLEAR)

1. **ALIMENTACIÓN DEL RFID RC522: ESTRICTAMENTE 3.3V**
   * El pin **3.3V (VCC)** del lector RC522 debe conectarse **exclusivamente a 3.3V** (pin `3V3` del ESP32 o riel de 3.3V de la fuente MB102).
   * **¡JAMÁS conectes el RC522 a 5V!** El circuito integrado MFRC522 no tolera 5V y se quema de forma permanente e irreversible.

2. **MASA COMÚN OBLIGATORIA (GND)**
   * El riel **GND** de la protoboard, el pin **GND** del ESP32, el pin **GND** del RC522 y el pin **GND** del sensor IR deben estar **todos interconectados entre sí**.
   * Si las masas no están unidas, las señales del bus SPI flotan y el lector reporta error `0x00` o `0xFF`.

3. **PIN IRQ DEL RC522: NO SE CONECTA**
   * El pin `IRQ` del lector RC522 se deja **completamente libre / al aire**.

---

## 1. MAPA FÍSICO DE LA PLACA ESP32-S3 (PCB V1695)

Mirando la placa de frente, con la **cámara OV5640 arriba** y los **dos puertos USB Type-C abajo**:

```text
                  [ LENTE CÁMARA OV5640 ]
                 ┌───────────────────────┐
                 │                       │
      (3V3)  [ ] │                       │ [ ]  (3V3)
      (GND)  [ ] │                       │ [ ]  (RX - 44)
    (GPIO 1) [●]─┼── IR (OUT)            │ [ ]  (TX - 43)
       (4)   [ ] │                       │ [ ]  (1)
       (5)   [ ] │                       │ [ ]  (2)
       (6)   [ ] │                       │ [ ]  (42)
       (7)   [ ] │                       │ [ ]  (41)
      (15)   [ ] │      ESP32-S3         │ [ ]  (40)
      (16)   [ ] │       N16R8           │ [ ]  (39)
      (17)   [ ] │                       │ [ ]  (38)
      (18)   [ ] │                       │ [ ]  (37)
       (3)   [ ] │                       │ [ ]  (36)
      (46)   [ ] │                       │ [ ]  (35)
    (GPIO 2) [●]─┼── RC522 (SDA / SS)    │ [ ]  (0)
       (9)   [ ] │                       │ [ ]  (45)
      (10)   [ ] │                       │ [●]──(GPIO 48) ── RC522 (RST)
      (11)   [ ] │  LEDs: [IO2] [48]     │ [●]──(GPIO 47) ── RC522 (MISO)
      (12)   [ ] │  [EN]         [BOOT]  │ [●]──(GPIO 21) ── RC522 (MOSI)
      (13)   [ ] │                       │ [ ]  (20)
   (GPIO 14) [●]─┼── RC522 (SCK)         │ [ ]  (19)
      (5V)   [ ] │                       │ [●]──(GND) ────── MASA COMÚN
                 └───┬───────────────┬───┘
                     │  USB-UART     │  USB-OTG
                     └───────────────┘
```

---

## 2. TABLA PIN A PIN: LECTOR RFID RC522 (8 PINES)

| Pin en el Lector RC522 | Pin en el ESP32-S3 (Serigrafía PCB) | Posición física en la placa | Función |
| :--- | :--- | :--- | :--- |
| **VCC / 3.3V** | Pin **`3V3`** (o riel 3.3V MB102) | Regleta izquierda (arriba) o riel | Alimentación positiva (3.3V) |
| **RST** | Pin **`48`** (GPIO 48) | **Regleta derecha, 6to pin** contando desde abajo (junto al LED 48) | Línea de Reset |
| **GND** | Pin **`GND`** | **Regleta derecha, 1er pin** abajo del todo (esquina inferior derecha) | Masa eléctrica común |
| **IRQ** | *(NO CONECTAR)* | — | Queda libre |
| **MISO** | Pin **`47`** (GPIO 47) | **Regleta derecha, 5to pin** contando desde abajo (entre `21` y `48`) | SPI Master In (Datos al ESP32) |
| **MOSI** | Pin **`21`** (GPIO 21) | **Regleta derecha, 4to pin** contando desde abajo (sobre `20`) | SPI Master Out (Datos al RC522) |
| **SCK** | Pin **`14`** (GPIO 14) | **Regleta izquierda, 2do pin** contando desde abajo (sobre `5V`) | SPI Reloj |
| **SDA (SS)** | Pin **`2`** (GPIO 2) | **Regleta izquierda, 8vo pin** contando desde abajo (entre `9` y `46`) | SPI Slave Select (Chip Select) |

---

## 3. TABLA PIN A PIN: SENSOR INFRARROJO DE PROXIMIDAD (3 PINES)

| Pin en el Módulo IR | Pin en el ESP32-S3 / Protoboard | Posición física | Función |
| :--- | :--- | :--- | :--- |
| **VCC** | Riel **`3.3V`** (o pin `3V3`) | Riel de alimentación de protoboard | Alimentación (3.3V) |
| **GND** | Riel **`GND`** | Riel de masa común | Referencia 0V |
| **OUT** | Pin **`1`** (GPIO 1) | **Regleta izquierda, penúltimo pin** arriba (debajo de `GND`) | Señal digital (LOW al detectar paso) |

---

## 4. CHECKLIST PASO A PASO PARA VERIFICAR CADA CABLE

1. **Comprobar la Protoboard**:
   * Asegúrate de que los cables Dupont no tengan juego o queden flojos en los orificios.
   * Si algún cable se sale con facilidad, cámbialo de ranura o usa otro cable jumper nuevo.

2. **Verificar Alimentación con Multímetro o LED**:
   * El lector RC522 suele tener un pequeño LED SMD rojo en su plaquita. Si está conectado correctamente a 3.3V y GND, ese LED rojo del RC522 debe estar **encendido**.
   * El sensor infrarrojo tiene un LED de Power (PWR) que también debe estar **encendido fijo**.

3. **Calibración del Sensor Infrarrojo**:
   * Gira levemente el potenciómetro azul del sensor IR con un destornillador plano pequeño hasta que su segundo LED (Detección) se apague cuando no hay obstáculos a 10 cm, y se encienda cuando pasas la mano a 5 cm.

---

## 5. CÓDIGO EN EL FIRMWARE (VERIFICACIÓN)

En el archivo `Fase2_ESP32_IR_RFID_Camera.ino`, la sección de pines debe estar configurada exactamente así:

```cpp
// Sensor IR
const int IR_GPIO_PIN = 1;

// Lector RFID RC522
#define RFID_SS_PIN    2   // SDA en RC522
#define RFID_RST_PIN   48  // RST en RC522
#define RFID_SCK_PIN   14  // SCK en RC522
#define RFID_MOSI_PIN  21  // MOSI en RC522
#define RFID_MISO_PIN  47  // MISO en RC522
```

---

## 6. QUÉ DEBES VER EN EL MONITOR SERIE AL ARRANCAR (115200 Baudios)

Al presionar el botón físico **EN/RST** del ESP32:

```text
==================================================
  ESP32-S3 N16R8 - FASE 2: CAM + IR + RFID RC522
==================================================
Flash detectada: 16 MB
PSRAM detectada: 8 MB
[OK] Sensor IR inicializado en GPIO 1 (Estado inicial: LIBRE)
Inicializando bus SPI para RFID RC522...
  -> SCK: GPIO 14 | MOSI: GPIO 21 | MISO: GPIO 47 | SDA(SS): GPIO 2 | RST: GPIO 48
  -> Registro VersionReg RC522: 0x82 (Version clon detectada - OK)
Inicializando camara OV5640...
[OK] Camara OV5640 inicializada correctamente.
```

### Diagnóstico según `VersionReg`:
* **`0x82` o `0x92` o `0x91`:** 🟢 **COMUNICACIÓN SPI PERFECTA.** El lector está conectado al 100% y listo para leer tarjetas. (Tu placa reporta legítimamente `0x82`).
* **`0xEE`:** ⚠️ **PUENTE / CORTO ENTRE MOSI Y MISO.** El código 0xEE es exactamente el comando que el ESP32 envía hacia MOSI. Si lo recibe de vuelta en MISO, significa que el cable de **GPIO 21 (MOSI)** y el cable de **GPIO 47 (MISO)** se están tocando o están en la misma fila de la protoboard. Sepáralos.
* **`0x00` o `0xFF`:** 🔴 **ERROR DE CABLEADO / ALIMENTACIÓN.** Significa que el bus SPI no recibe ninguna señal o MISO está flotando. Verifica alimentación 3.3V, masa GND común y el pin RST (GPIO 48).

---

## 7. POLÍTICA DE ACCESO DE LAS TARJETAS (CONFIGURADA EN EL SISTEMA)

| UID de Tarjeta | Titular Asignado | Política de Acceso | Resultado en Web / Serial |
| :--- | :--- | :--- | :--- |
| **`73230E06`** | Socio #1 | 🔴 **TARJETA BLOQUEADA** | **ACCESO DENEGADO** (Banner Rojo) |
| **`6C8D1B06`** | Socio Activo #2 | 🟢 **TARJETA AUTORIZADA** | **ACCESO CONCEDIDO** (Banner Verde) |
