/*
 * ==============================================================================
 * CameraWebServer_ESP32S3_OV5640.ino — FASE 1: Cámara OV5640 + Sensor IR (GPIO 1)
 * ==============================================================================
 * 
 * Hardware conectado y probado:
 * - ESP32-S3 N16R8 (PCB V1695) + Cámara OV5640 de 5 MP
 * - Sensor Infrarrojo (FC-51 / TCRT5000):
 *     - VCC: 3.3V (Alimentado por módulo MB102 a 3.21 V)
 *     - GND: Masa común (GND Protoboard unido a GND ESP32)
 *     - OUT: GPIO 1 del ESP32-S3
 * 
 * Ajustes obligatorios en Arduino IDE:
 * - Placa: ESP32S3 Dev Module
 * - USB CDC On Boot: DISABLED (Obligatorio usando puerto físico USB-UART)
 * - Flash Size: 16MB (128Mb)
 * - PSRAM: OPI PSRAM
 * - Partition Scheme: 16M Flash (3MB APP / ...)
 * - Monitor Serie: 115200 baudios
 */

#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "board_config.h"

// ==============================================================================
// CONFIGURACIÓN DE RED LOCAL Y SERVIDOR
// ==============================================================================
const char* ssid = "JAPON";
const char* password = "1a.2*3-GLPV";

// Dirección IP de tu PC anfitriona donde corre Docker en el puerto 8088
const char* backend_server = "http://192.168.1.95:8088";

// ==============================================================================
// CONFIGURACIÓN DEL SENSOR INFRARROJO EN GPIO 1
// ==============================================================================
const int IR_GPIO_PIN = 1;

// Lógica del módulo infrarrojo:
// - Objeto presente / haz interrumpido = LOW (0V)
// - Haz despejado / libre = HIGH (3.3V)
const int IR_ACTIVE_LEVEL = LOW;

// Tiempos para anti-rebote (debounce) no bloqueante
const unsigned long DEBOUNCE_DELAY_MS = 50;
const unsigned long REPEAT_WINDOW_MS = 250;

int lastRawReading = HIGH;
int stableIrState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long lastEventSentTime = 0;
unsigned long eventSequence = 0;

// Prototipos implementados en app_httpd.cpp del paquete oficial de cámara
void startCameraServer();
void setupLedFlash();

// ==============================================================================
// ENVÍO DE EVENTO AL BACKEND DOCKER
// ==============================================================================
void sendSensorEvent(const char* eventType) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("[AVISO LOCAL] Wi-Fi desconectado, evento no enviado: %s\n", eventType);
    return;
  }

  HTTPClient http;
  String endpoint = String(backend_server) + "/api/v1/devices/ESP32_S3/events";
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(2500);

  eventSequence++;
  String eventId = "ESP32_S3-" + String(millis()) + "-" + String(eventSequence);
  String payload = "{\"event_id\":\"" + eventId + "\","
                   "\"sensor_id\":\"IR_1\","
                   "\"sensor_type\":\"IR\","
                   "\"event_type\":\"" + String(eventType) + "\","
                   "\"occurred_at\":\"\","
                   "\"metadata\":{\"gpio\":1,\"simulated\":false}}";

  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    Serial.printf("  -> [HTTP %d] Evento '%s' recibido por el backend Docker.\n", httpCode, eventType);
  } else {
    Serial.printf("  -> [HTTP ERROR] %s al contactar %s\n", http.errorToString(httpCode).c_str(), backend_server);
  }
  http.end();
}

// ==============================================================================
// SETUP PRINCIPAL
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println();
  Serial.println("==================================================");
  Serial.println("  ESP32-S3 N16R8 + OV5640 + SENSOR IR (GPIO 1)");
  Serial.println("==================================================");

  Serial.printf("FLASH DETECTADA: %u MB\n", ESP.getFlashChipSize() / (1024 * 1024));
  Serial.printf("PSRAM DETECTADA: %u MB\n", ESP.getPsramSize() / (1024 * 1024));

  // 1. Configurar entrada digital del Sensor Infrarrojo
  pinMode(IR_GPIO_PIN, INPUT_PULLUP);
  stableIrState = digitalRead(IR_GPIO_PIN);
  lastRawReading = stableIrState;
  Serial.printf("SENSOR INFRARROJO INICIALIZADO EN GPIO %d (Estado actual: %s)\n",
                IR_GPIO_PIN, (stableIrState == IR_ACTIVE_LEVEL ? "DETECTADO" : "LIBRE"));

  // 2. Inicializar controlador de Cámara OV5640 (Mapeo intacto)
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

  Serial.println("Inicializando camara OV5640...");
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("ERROR AL INICIALIZAR CAMARA: 0x%x\n", err);
  } else {
    Serial.println("CAMARA OV5640 INICIALIZADA CORRECTAMENTE.");
    sensor_t *s = esp_camera_sensor_get();
    if (s != nullptr) {
      s->set_framesize(s, FRAMESIZE_VGA);
    }
  }

  // 3. Conexión Wi-Fi
  Serial.print("Conectando a red Wi-Fi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);

  unsigned long start_attempt = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start_attempt < 25000)) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("\nERROR: No se pudo conectar a la red Wi-Fi.");
    return;
  }

  Serial.println("\nWIFI CONECTADO EXITOSAMENTE");

  // Iniciar servidor HTTP embebido oficial (sirve /capture para Docker)
  startCameraServer();

  Serial.println();
  Serial.println("==================================================");
  Serial.println("  ESP32-S3 LISTO");
  Serial.print("  IP LOCAL CAMARA: http://");
  Serial.println(WiFi.localIP());
  Serial.printf("  DESTINO EVENTOS: %s\n", backend_server);
  Serial.println("  Pasa la mano frente al sensor IR en GPIO 1...");
  Serial.println("==================================================");
}

// ==============================================================================
// BUCLE PRINCIPAL NO BLOQUEANTE
// ==============================================================================
void loop() {
  unsigned long currentMillis = millis();
  int rawReading = digitalRead(IR_GPIO_PIN);

  // Detección de flanco con anti-rebote (debounce)
  if (rawReading != lastRawReading) {
    lastDebounceTime = currentMillis;
  }

  if ((currentMillis - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
    if (rawReading != stableIrState && (currentMillis - lastEventSentTime > REPEAT_WINDOW_MS)) {
      stableIrState = rawReading;
      lastEventSentTime = currentMillis;

      if (stableIrState == IR_ACTIVE_LEVEL) {
        Serial.println("\n[SENSOR IR] -> ¡OBJETO DETECTADO! (GPIO 1 = LOW)");
        sendSensorEvent("IR_INTERRUPTED");
      } else {
        Serial.println("\n[SENSOR IR] -> HAZ DESPEJADO / LIBRE (GPIO 1 = HIGH)");
        sendSensorEvent("IR_CLEARED");
      }
    }
  }

  lastRawReading = rawReading;
  delay(10); // Pausa cooperativa mínima para no saturar CPU ni bloquear la cámara
}
