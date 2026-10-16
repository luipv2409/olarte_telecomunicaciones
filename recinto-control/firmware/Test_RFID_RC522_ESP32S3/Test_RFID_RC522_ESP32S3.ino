/*
 * ==============================================================================
 * TEST EXCLUSIVO DE LECTOR RFID RC522 (BUS SPI) - ESP32-S3 (PCB V1695)
 * ==============================================================================
 *
 * Propósito:
 *   - Probar y aislar al 100% el funcionamiento del lector RFID RC522.
 *   - SIN cámara, SIN Wi-Fi, SIN backend, para diagnóstico directo y puro en
 *     el Monitor Serie de Arduino IDE.
 *
 * Mapeo de Pines (Validado para PCB V1695):
 *   - SDA (SS): GPIO 2   (Regleta Izquierda, pin 8 desde abajo)
 *   - SCK:      GPIO 14  (Regleta Izquierda, pin 2 desde abajo)
 *   - MOSI:     GPIO 21  (Regleta Derecha, pin 4 desde abajo)
 *   - MISO:     GPIO 47  (Regleta Derecha, pin 5 desde abajo)
 *   - RST:      GPIO 48  (Regleta Derecha, pin 6 desde abajo)
 *   - VCC:      3.3V     (¡NUNCA 5V!)
 *   - GND:      GND      (Masa común)
 *   - IRQ:      (Dejar libre)
 *
 * Monitor Serie: 115200 baudios
 * ==============================================================================
 */

#include <MFRC522.h>
#include <SPI.h>

// Definición estricta de pines SPI
#define RFID_SS_PIN 2    // SDA / Slave Select en RC522
#define RFID_RST_PIN 48  // RST en RC522
#define RFID_SCK_PIN 14  // SCK en RC522
#define RFID_MOSI_PIN 21 // MOSI en RC522
#define RFID_MISO_PIN 47 // MISO en RC522

// Pin del Buzzer Activo (controlado por Transistor 2N2222A con resistencia de 1kΩ)
#define BUZZER_PIN 42

// Instancia del lector MFRC522
MFRC522 mfrc522(RFID_SS_PIN, RFID_RST_PIN);

unsigned long lastStatusPrint = 0;
const unsigned long STATUS_INTERVAL_MS = 3000;
unsigned long totalScans = 0;

// Funciones de señalización acústica
void beepStartup() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(80);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepSuccess() {
  digitalWrite(BUZZER_PIN, HIGH);
  delay(150);
  digitalWrite(BUZZER_PIN, LOW);
}

void beepDenied() {
  for (int i = 0; i < 3; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(80);
    digitalWrite(BUZZER_PIN, LOW);
    delay(80);
  }
}

void setup() {
  Serial.begin(115200);
  delay(2000); // Pausa de 2s para abrir el Monitor Serie

  Serial.println();
  Serial.println(
      "==============================================================");
  Serial.println("   TEST EXCLUSIVO DE DIAGNÓSTICO RFID RC522 - ESP32-S3");
  Serial.println(
      "==============================================================");
  Serial.printf("Configuración de Pines SPI:\n");
  Serial.printf("  -> SDA (SS) : GPIO %d\n", RFID_SS_PIN);
  Serial.printf("  -> SCK      : GPIO %d\n", RFID_SCK_PIN);
  Serial.printf("  -> MOSI     : GPIO %d\n", RFID_MOSI_PIN);
  Serial.printf("  -> MISO     : GPIO %d\n", RFID_MISO_PIN);
  Serial.printf("  -> RST      : GPIO %d\n", RFID_RST_PIN);
  // 0. Inicializar Buzzer
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.printf("  -> BUZZER   : GPIO %d (Transistor 2N2222A)\n", BUZZER_PIN);
  beepStartup(); // Micro-bip de confirmación de arranque

  // 1. Inicializar bus SPI en los GPIOs designados
  Serial.println("[PASO 1] Inicializando bus SPI por hardware...");
  pinMode(RFID_SS_PIN, OUTPUT);
  digitalWrite(RFID_SS_PIN, HIGH);
  pinMode(RFID_RST_PIN, OUTPUT);
  digitalWrite(RFID_RST_PIN, HIGH);
  delay(10);

  SPI.begin(RFID_SCK_PIN, RFID_MISO_PIN, RFID_MOSI_PIN, RFID_SS_PIN);

  // 2. Inicializar chip MFRC522
  Serial.println("[PASO 2] Inicializando chip MFRC522 (PCD_Init)...");
  mfrc522.PCD_Init();
  delay(100);

  // 3. Diagnóstico de comunicación SPI
  Serial.println("[PASO 3] Leyendo registro de versión (VersionReg)...");
  byte ver = mfrc522.PCD_ReadRegister(mfrc522.PCD_Register::VersionReg);
  Serial.printf("  ===> VersionReg leído: 0x%02X <===\n", ver);

  if (ver == 0x92) {
    Serial.println("  [ESTADO: 🟢 OK] Chip NXP MFRC522 versión 2.0 detectado.");
  } else if (ver == 0x91) {
    Serial.println("  [ESTADO: 🟢 OK] Chip NXP MFRC522 versión 1.0 detectado.");
  } else if (ver == 0x82) {
    Serial.println("  [ESTADO: 🟢 OK] Chip RC522 Clon funcional detectado (¡Tu "
                   "chip legítimo!).");
  } else if (ver == 0xEE) {
    Serial.println(
        "  [ESTADO: ⚠️ ALERTA] Lectura 0xEE detectada (Loopback de bus SPI).");
    Serial.println(
        "  -> CAUSA: El cable MOSI (GPIO 21) y MISO (GPIO 47) están tocándose");
    Serial.println("            o en la misma fila de la protoboard.");
    Serial.println("  -> ACCIÓN: Separa esos dos cables en la protoboard.");
  } else if (ver == 0x00 || ver == 0xFF) {
    Serial.println("  [ESTADO: 🔴 ERROR] Sin comunicación en el bus SPI (Línea "
                   "en 0 o flotante).");
    Serial.println("  -> Revisa alimentación 3.3V y GND en el RC522.");
    Serial.println(
        "  -> Revisa que el pin RST esté en GPIO 48 y MISO en GPIO 47.");
  } else {
    Serial.printf("  [ESTADO: 🟡 AVISO] Registro 0x%02X detectado. Verifica "
                  "cableado si no lee.\n",
                  ver);
  }

  Serial.println(
      "--------------------------------------------------------------");
  Serial.println("  Lector listo para pruebas continuas.");
  Serial.println("  Acerca tu tarjeta o llavero RFID al lector...");
  Serial.println(
      "==============================================================");
  Serial.println();
}

void loop() {
  unsigned long currentMillis = millis();

  // 1. Comprobar si hay una tarjeta presente y leer su número de serie
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    totalScans++;

    // Convertir el UID a String Hexadecimal limpio
    String uidHex = "";
    for (byte i = 0; i < mfrc522.uid.size; i++) {
      if (mfrc522.uid.uidByte[i] < 0x10)
        uidHex += "0";
      uidHex += String(mfrc522.uid.uidByte[i], HEX);
    }
    uidHex.toUpperCase();

    // Tipo de tarjeta PICC
    MFRC522::PICC_Type piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    String piccName = String(mfrc522.PICC_GetTypeName(piccType));

    // Impresión inmediata en el Monitor Serie
    Serial.println("**************************************************");
    Serial.printf("  ¡TARJETA DETECTADA! (Lectura #%lu)\n", totalScans);
    Serial.printf("  UID HEX     : %s\n", uidHex.c_str());
    Serial.printf("  Bytes UID   : %d bytes\n", mfrc522.uid.size);
    Serial.printf("  Tipo PICC   : %s\n", piccName.c_str());
    Serial.println("  ----------------------------------------------");

    // Evaluación local de reglas de acceso
    if (uidHex == "73230E06") {
      Serial.println("  POLÍTICA    : 🔴 [ACCESO DENEGADO]");
      Serial.println("  ESTADO      : CREDENCIAL BLOQUEADA");
      Serial.println("  TITULAR     : Socio #1");
      beepDenied();
    } else if (uidHex == "6C8D1B06") {
      Serial.println("  POLÍTICA    : 🟢 [ACCESO CONCEDIDO]");
      Serial.println("  ESTADO      : CREDENCIAL AUTORIZADA");
      Serial.println("  TITULAR     : Socio Activo #2");
      beepSuccess();
    } else {
      Serial.println("  POLÍTICA    : ⚪ [CREDENCIAL NO REGISTRADA]");
      Serial.println("  ESTADO      : TARJETA DESCONOCIDA");
      beepDenied();
    }
    Serial.println("**************************************************");
    Serial.println();

    // Poner la tarjeta en reposo y detener encriptación
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();

    // Pequeño delay de cortesía para evitar lecturas continuas de la misma
    // tarjeta
    delay(1000);
  }

  // 2. Mensaje periódico de latido/diagnóstico cada 3 segundos
  if (currentMillis - lastStatusPrint > STATUS_INTERVAL_MS) {
    lastStatusPrint = currentMillis;

    // Verificar en tiempo real si el bus SPI sigue respondiendo
    byte liveVer = mfrc522.PCD_ReadRegister(mfrc522.PCD_Register::VersionReg);
    if (liveVer == 0x82 || liveVer == 0x91 || liveVer == 0x92) {
      Serial.printf("[ESTADO VIVO] Lector OK (0x%02X) | Esperando tarjeta...\n",
                    liveVer);
    } else if (liveVer == 0xEE) {
      Serial.println("[ESTADO VIVO] ⚠️ Corto MOSI/MISO detectado (0xEE) | "
                     "Separa cables 21 y 47.");
    } else {
      Serial.printf("[ESTADO VIVO] 🔴 Falla de bus (0x%02X) | Revisa cables en "
                    "protoboard.\n",
                    liveVer);
    }
  }

  delay(20); // Pausa de 20ms para estabilidad
}
