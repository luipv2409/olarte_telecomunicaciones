/*
 * ==============================================================================
 * PROYECTO: Recinto Control - FASE 3
 * ARCHIVO: Fase3_ESP32_IR_RFID_Buzzer_Camera.ino
 * ==============================================================================
 * 
 * Hardware integrado:
 * - ESP32-S3 N16R8 (PCB V1695) con cámara OV5640 de 5 MP
 * - Sensor Infrarrojo digital en GPIO 1 (Fase 1)
 * - Lector RFID RC522 vía bus SPI a 3.3V (Fase 2):
 *     - SCK:  GPIO 14
 *     - MOSI: GPIO 21
 *     - MISO: GPIO 47
 *     - SDA:  GPIO 2  (SS / Chip Select)
 *     - RST:  GPIO 48 (Reset)
 *     - VCC:  3.3V estrictos (Riel MB102 a 3.3V)
 *     - GND:  GND Común
 * - Buzzer Activo 5V vía Transistor NPN 2N2222A (Fase 3):
 *     - Base: GPIO 42 a través de resistencia de 1 kΩ
 *     - Colector: Pata negativa (-) del Buzzer
 *     - Emisor: GND Común
 *     - Positivo (+): Riel 3.3V (MB102)
 * 
 * Monitoreo de Hardware en Vivo:
 * - Detección dinámica de cortocircuito MOSI/MISO (0xEE) o cable suelto (0x00/0xFF).
 * - Telemetría de salud de hardware enviada en Heartbeat hacia backend Docker.
 * 
 * Ajustes obligatorios en menú Herramientas de Arduino IDE:
 * - Placa: ESP32S3 Dev Module
 * - USB CDC On Boot: Disabled (Crítico con puerto físico USB-UART)
 * - Flash Size: 16MB (128Mb)
 * - PSRAM: OPI PSRAM
 * - Partition Scheme: 16M Flash (3MB APP / 9.9MB FATFS)
 * - Monitor Serie: 115200 baudios
 * ==============================================================================
 */

#include <Arduino.h>
#include <SPI.h>
#include <MFRC522.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "board_config.h"

// Intentar incluir secrets.h si existe; de lo contrario usar valores por defecto
#if __has_include("secrets.h")
  #include "secrets.h"
#else
  #define SECRET_WIFI_SSID     "JAPON"
  #define SECRET_WIFI_PASSWORD "1a.2*3-GLPV"
  #define SECRET_DEVICE_TOKEN  "esp32_device_secret_token_seguro_fase1"
  #define BACKEND_BASE_URL     "http://192.168.1.95:8088"
#endif

const char* ssid = SECRET_WIFI_SSID;
const char* password = SECRET_WIFI_PASSWORD;
const char* device_token = SECRET_DEVICE_TOKEN;
const char* backend_url = BACKEND_BASE_URL;

const String DEVICE_ID = "ESP32_S3";
const String FIRMWARE_VERSION = "3.0.0-fase3";

// ==============================================================================
// 1. CONFIGURACIÓN DEL SENSOR INFRARROJO #1 (GPIO 1)
// ==============================================================================
const int IR_GPIO_PIN = 1;
const int IR_ACTIVE_LEVEL = LOW; // LOW = objeto frente al sensor, HIGH = libre

const unsigned long DEBOUNCE_DELAY_MS = 50;
const unsigned long REPEAT_WINDOW_MS = 250;

int lastRawIrReading = HIGH;
int stableIrState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long lastIrEventTime = 0;
unsigned long eventSequence = 0;

// ==============================================================================
// 2. CONFIGURACIÓN DEL LECTOR RFID RC522 (BUS SPI EN GPIOs 2, 14, 21, 47, 48)
// ==============================================================================
#define RFID_SS_PIN    2   // SDA / Slave Select (Salida al RC522; parpadea LED IO2)
#define RFID_RST_PIN   48  // Reset (Salida activa HIGH; activa LED 48)
#define RFID_SCK_PIN   14  // SPI Clock
#define RFID_MOSI_PIN  21  // SPI MOSI
#define RFID_MISO_PIN  47  // SPI MISO

MFRC522 mfrc522(RFID_SS_PIN, RFID_RST_PIN);

unsigned long lastRfidScanTime = 0;
const unsigned long RFID_COOLDOWN_MS = 1500; // Evita ráfagas repetidas de la misma tarjeta
String lastScannedUid = "";

// ==============================================================================
// 3. CONFIGURACIÓN DEL BUZZER ACTIVO 5V (GPIO 42 - TRANSISTOR 2N2222A)
// ==============================================================================
#define BUZZER_PIN 42

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
    if (i < 2) delay(80);
  }
}

// Variables para Heartbeat y Monitoreo de Hardware
unsigned long lastHeartbeatTime = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 15000;

// Prototipos de servidor de cámara (app_httpd.cpp oficial)
void startCameraServer();
void setupLedFlash();

// ==============================================================================
// 4. ENVÍO DE EVENTOS Y TELEMETRÍA AL BACKEND DOCKER
// ==============================================================================
void sendSensorEvent(const char* sensorId, const char* sensorType, const char* eventType, const String& extraMetadataJson) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("[OFFLINE] Wi-Fi desconectado. Evento no enviado: %s (%s)\n", eventType, sensorId);
    return;
  }

  HTTPClient http;
  String endpoint = String(backend_url) + "/api/v1/devices/" + DEVICE_ID + "/events";
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", device_token);
  http.setTimeout(2500);

  eventSequence++;
  String eventId = DEVICE_ID + "-" + String(millis()) + "-" + String(eventSequence);

  String payload = "{\"event_id\":\"" + eventId + "\","
                   "\"sensor_id\":\"" + String(sensorId) + "\","
                   "\"sensor_type\":\"" + String(sensorType) + "\","
                   "\"event_type\":\"" + String(eventType) + "\","
                   "\"occurred_at\":\"\","
                   "\"metadata\":" + extraMetadataJson + "}";

  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    Serial.printf("  -> [HTTP %d] Evento '%s' [%s] aceptado por el backend.\n", httpCode, eventType, sensorId);
  } else {
    Serial.printf("  -> [HTTP ERROR] %s al contactar %s\n", http.errorToString(httpCode).c_str(), backend_url);
  }
  http.end();
}

void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  // Autodiagnóstico en tiempo real del bus SPI del RFID RC522
  byte liveVer = mfrc522.PCD_ReadRegister(mfrc522.PCD_Register::VersionReg);
  String hwStatus = "OK";
  char verHexStr[8];
  snprintf(verHexStr, sizeof(verHexStr), "0x%02X", liveVer);

  if (liveVer == 0x82 || liveVer == 0x91 || liveVer == 0x92) {
    hwStatus = "OK";
  } else if (liveVer == 0xEE) {
    hwStatus = "SHORT_MOSI_MISO_PINS_21_47";
    Serial.println("[TELEMETRÍA] ⚠️ ALERTA: Corto entre GPIO 21 (MOSI) y GPIO 47 (MISO).");
  } else if (liveVer == 0x00 || liveVer == 0xFF) {
    hwStatus = "DISCONNECTED_OR_NO_POWER";
    Serial.println("[TELEMETRÍA] 🔴 ALERTA: Lector RC522 sin alimentación o desconectado.");
  } else {
    hwStatus = "UNSTABLE_BUS_NOISE";
  }

  HTTPClient http;
  String endpoint = String(backend_url) + "/api/v1/devices/" + DEVICE_ID + "/heartbeat";
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", device_token);
  http.setTimeout(2000);

  String payload = "{\"firmware_version\":\"" + FIRMWARE_VERSION + "\","
                   "\"ip_address\":\"" + WiFi.localIP().toString() + "\","
                   "\"wifi_rssi\":" + String(WiFi.RSSI()) + ","
                   "\"rc522_version\":\"" + String(verHexStr) + "\","
                   "\"rc522_hardware_status\":\"" + hwStatus + "\","
                   "\"buzzer_pin\":" + String(BUZZER_PIN) + "}";

  http.POST(payload);
  http.end();
}

// ==============================================================================
// 5. SETUP PRINCIPAL
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("================================================================");
  Serial.println(" ESP32-S3 N16R8 - FASE 3: CAM + IR + RFID RC522 + BUZZER ACTIVO");
  Serial.println("================================================================");

  Serial.printf("Flash detectada: %u MB\n", ESP.getFlashChipSize() / (1024 * 1024));
  Serial.printf("PSRAM detectada: %u MB\n", ESP.getPsramSize() / (1024 * 1024));

  // 5.1 Configurar Buzzer Activo (GPIO 42)
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.printf("[OK] Buzzer Activo inicializado en GPIO %d (Driver 2N2222A)\n", BUZZER_PIN);
  beepStartup(); // Micro-bip de arranque de 80 ms

  // 5.2 Configurar Sensor Infrarrojo (GPIO 1)
  pinMode(IR_GPIO_PIN, INPUT_PULLUP);
  stableIrState = digitalRead(IR_GPIO_PIN);
  lastRawIrReading = stableIrState;
  Serial.printf("[OK] Sensor IR inicializado en GPIO %d (Estado inicial: %s)\n",
                IR_GPIO_PIN, (stableIrState == IR_ACTIVE_LEVEL ? "DETECTADO" : "LIBRE"));

  // 5.3 Inicializar Bus SPI y Lector RFID RC522
  Serial.println("Inicializando bus SPI para RFID RC522...");
  Serial.printf("  -> SCK: GPIO %d | MOSI: GPIO %d | MISO: GPIO %d | SDA(SS): GPIO %d | RST: GPIO %d\n",
                RFID_SCK_PIN, RFID_MOSI_PIN, RFID_MISO_PIN, RFID_SS_PIN, RFID_RST_PIN);

  SPI.begin(RFID_SCK_PIN, RFID_MISO_PIN, RFID_MOSI_PIN, RFID_SS_PIN);
  mfrc522.PCD_Init();
  delay(50);

  // Diagnóstico del chip RC522
  byte rfidVer = mfrc522.PCD_ReadRegister(mfrc522.PCD_Register::VersionReg);
  Serial.printf("  -> Registro VersionReg RC522: 0x%02X ", rfidVer);
  if (rfidVer == 0x82) {
    Serial.println("(MFRC522 Clon funcional - OK)");
  } else if (rfidVer == 0x92 || rfidVer == 0x91) {
    Serial.println("(MFRC522 Original - OK)");
  } else if (rfidVer == 0xEE) {
    Serial.println("--> ⚠️ ¡ALERTA! Cortocircuito entre MOSI (GPIO 21) y MISO (GPIO 47). Separa esos cables.");
  } else {
    Serial.println("--> 🔴 ERROR DE BUS. Revisa conexiones 3.3V, GND común y pines SPI.");
  }

  // 5.4 Inicializar Cámara OV5640
  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
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

  Serial.println("Inicializando cámara OV5640...");
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("[ERROR] Fallo al inicializar cámara OV5640: 0x%x\n", err);
  } else {
    Serial.println("[OK] Cámara OV5640 inicializada correctamente.");
    sensor_t *s = esp_camera_sensor_get();
    if (s != nullptr) {
      s->set_framesize(s, FRAMESIZE_VGA);
    }
  }

  // 5.5 Conexión Wi-Fi
  Serial.print("Conectando a red Wi-Fi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);

  unsigned long startAttempt = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - startAttempt < 25000)) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[OK] WIFI CONECTADO");
    Serial.printf("  IP Local Cámara: http://%s\n", WiFi.localIP().toString().c_str());
    startCameraServer();
  } else {
    Serial.println("\n[AVISO] Operando en modo local desconectado.");
  }

  Serial.println("================================================================");
  Serial.println("  SISTEMA FASE 3 LISTO: CAM + IR + RFID + BUZZER OPERATIVOS");
  Serial.println("================================================================");
}

// ==============================================================================
// 6. BUCLE PRINCIPAL NO BLOQUEANTE
// ==============================================================================
void loop() {
  unsigned long currentMillis = millis();

  // ----------------------------------------------------------------------------
  // A. SONDEO NO BLOQUEANTE DEL SENSOR INFRARROJO
  // ----------------------------------------------------------------------------
  int rawReading = digitalRead(IR_GPIO_PIN);
  if (rawReading != lastRawIrReading) {
    lastDebounceTime = currentMillis;
  }

  if ((currentMillis - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
    if (rawReading != stableIrState && (currentMillis - lastIrEventTime > REPEAT_WINDOW_MS)) {
      stableIrState = rawReading;
      lastIrEventTime = currentMillis;

      if (stableIrState == IR_ACTIVE_LEVEL) {
        Serial.println("\n[IR] -> ¡OBJETO DETECTADO! (GPIO 1 = LOW)");
        sendSensorEvent("IR_1", "IR", "IR_INTERRUPTED", "{\"gpio\":1,\"simulated\":false}");
      } else {
        Serial.println("\n[IR] -> HAZ DESPEJADO (GPIO 1 = HIGH)");
        sendSensorEvent("IR_1", "IR", "IR_CLEARED", "{\"gpio\":1,\"simulated\":false}");
      }
    }
  }
  lastRawIrReading = rawReading;

  // ----------------------------------------------------------------------------
  // B. SONDEO NO BLOQUEANTE DEL LECTOR RFID RC522 CON SEÑALIZACIÓN ACÚSTICA
  // ----------------------------------------------------------------------------
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    if (currentMillis - lastRfidScanTime > RFID_COOLDOWN_MS) {
      lastRfidScanTime = currentMillis;

      // Obtener UID en Hexadecimal limpio
      String uidStr = "";
      for (byte i = 0; i < mfrc522.uid.size; i++) {
        if (mfrc522.uid.uidByte[i] < 0x10) uidStr += "0";
        uidStr += String(mfrc522.uid.uidByte[i], HEX);
      }
      uidStr.toUpperCase();
      lastScannedUid = uidStr;

      MFRC522::PICC_Type piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
      String piccTypeName = String(mfrc522.PICC_GetTypeName(piccType));

      Serial.println();
      Serial.println("**************************************************");
      Serial.printf("[RFID] -> ¡TARJETA DETECTADA!\n");
      Serial.printf("  UID HEX   : %s (Tamano: %d bytes)\n", uidStr.c_str(), mfrc522.uid.size);
      Serial.printf("  Tipo PICC : %s\n", piccTypeName.c_str());

      String decision = "DENIED";
      String cardHolder = "Desconocido";

      // Evaluación local de reglas y activación sonora
      if (uidStr == "6C8D1B06") {
        decision = "GRANTED";
        cardHolder = "Socio Activo #2";
        Serial.println("  POLÍTICA  : 🟢 [ACCESO CONCEDIDO]");
        Serial.printf("  TITULAR   : %s\n", cardHolder.c_str());
        beepSuccess(); // 1 bip de 150 ms
      } else if (uidStr == "73230E06") {
        decision = "DENIED";
        cardHolder = "Socio #1 (Bloqueado)";
        Serial.println("  POLÍTICA  : 🔴 [ACCESO DENEGADO]");
        Serial.printf("  TITULAR   : %s\n", cardHolder.c_str());
        beepDenied(); // 3 bips rápidos de alarma
      } else {
        decision = "DENIED";
        cardHolder = "Tarjeta no registrada";
        Serial.println("  POLÍTICA  : ⚪ [CREDENCIAL NO REGISTRADA]");
        Serial.printf("  TITULAR   : %s\n", cardHolder.c_str());
        beepDenied(); // 3 bips rápidos de alarma
      }
      Serial.println("**************************************************");

      // Construir metadata y enviar a Docker
      String meta = "{\"uid\":\"" + uidStr + "\","
                    "\"picc_type\":\"" + piccTypeName + "\","
                    "\"reader_id\":\"RFID_1\","
                    "\"access_decision\":\"" + decision + "\","
                    "\"card_holder\":\"" + cardHolder + "\","
                    "\"simulated\":false}";

      sendSensorEvent("RFID_1", "RFID", "CARD_SCANNED", meta);

      // Detener encriptación y poner tarjeta en reposo
      mfrc522.PICC_HaltA();
      mfrc522.PCD_StopCrypto1();
    }
  }

  // ----------------------------------------------------------------------------
  // C. HEARTBEAT PERIÓDICO HACIA EL BACKEND CON TELEMETRÍA DE HARDWARE
  // ----------------------------------------------------------------------------
  if (currentMillis - lastHeartbeatTime > HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatTime = currentMillis;
    sendHeartbeat();
  }

  delay(10); // Pausa cooperativa para multitarea del RTOS y servidor web de cámara
}
