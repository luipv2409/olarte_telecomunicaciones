/*
 * ==============================================================================
 * PROYECTO: Recinto Control - FASE 1
 * ARCHIVO: Fase1_ESP32_IR_Camera.ino
 * ==============================================================================
 * 
 * Hardware:
 * - ESP32-S3 N16R8 (PCB V1695) + Cámara OV5640 5MP
 * - 1x Sensor Infrarrojo de proximidad (FC-51 / TCRT5000)
 * 
 * Ajustes obligatorios en Arduino IDE:
 * - Placa: ESP32S3 Dev Module
 * - USB CDC On Boot: DISABLED (Obligatorio en USB-UART)
 * - Flash Size: 16MB (128Mb)
 * - PSRAM: OPI PSRAM
 * - Partition Scheme: 16M Flash (3MB APP / ...)
 * - Monitor Serie: 115200 baudios
 * 
 * Archivos de apoyo requeridos en esta misma carpeta:
 * - board_config.h (provisto en este repo)
 * - camera_pins.h  (original de ejemplos de ESP32)
 * - app_httpd.cpp  (original de ejemplos de ESP32)
 */

#include <Arduino.h>
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
  #define BACKEND_BASE_URL     "http://192.168.1.50:8089"
#endif

const char* ssid = SECRET_WIFI_SSID;
const char* password = SECRET_WIFI_PASSWORD;
const char* device_token = SECRET_DEVICE_TOKEN;
const char* backend_url = BACKEND_BASE_URL;

const String DEVICE_ID = "ESP32_S3_RECINTO";
const String FIRMWARE_VERSION = "1.1.0-fase1";

// ==============================================================================
// CONFIGURACIÓN DEL SENSOR INFRARROJO #1 (FASE 1)
// ESTADO: PENDIENTE DE VALIDACIÓN FÍSICA DE GPIO
// ==============================================================================
// Por precaución para no colisionar con la cámara, IR_ENABLED está en 'false' por defecto.
// Cámbialo a 'true' únicamente tras verificar que el pin está libre y a 3.3V.
const bool IR_ENABLED = false;

// Pin candidato (PENDIENTE DE VALIDACIÓN FÍSICA EN PCB):
const int IR_GPIO_PIN = 1;

// Nivel activo del módulo FC-51 (LOW = objeto interrumpe el haz; HIGH = despejado)
const int IR_ACTIVE_LEVEL = LOW;

// Tiempos para anti-rebote no bloqueante
const unsigned long DEBOUNCE_DELAY_MS = 50;
const unsigned long REPEAT_WINDOW_MS = 300;

// Variables de estado del sensor IR
int lastRawIrReading = HIGH;
int stableIrState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long lastEventSentTime = 0;
unsigned long eventSequence = 0;

// Variables para Heartbeat hacia el backend
unsigned long lastHeartbeatTime = 0;
const unsigned long HEARTBEAT_INTERVAL_MS = 15000;

// Prototipos del servidor web de cámara oficial (app_httpd.cpp)
void startCameraServer();
void setupLedFlash();

// ==============================================================================
// FUNCIONES AUXILIARES DE RED Y EVENTOS
// ==============================================================================

void sendHeartbeat() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String endpoint = String(backend_url) + "/api/v1/devices/" + DEVICE_ID + "/heartbeat";
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", device_token);
  http.setTimeout(3000);

  String payload = "{\"firmware_version\":\"" + FIRMWARE_VERSION + "\","
                   "\"ip_address\":\"" + WiFi.localIP().toString() + "\","
                   "\"wifi_rssi\":" + String(WiFi.RSSI()) + "}";

  int httpCode = http.POST(payload);
  if (httpCode > 0) {
    Serial.printf("[HEARTBEAT] Respuesta servidor: %d\n", httpCode);
  } else {
    Serial.printf("[HEARTBEAT] Error al contactar backend: %s\n", http.errorToString(httpCode).c_str());
  }
  http.end();
}

void sendSensorEvent(const char* eventType) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.printf("[EVENTO LOCAL] Wi-Fi desconectado, evento retenido: %s\n", eventType);
    return;
  }

  HTTPClient http;
  String endpoint = String(backend_url) + "/api/v1/devices/" + DEVICE_ID + "/events";
  http.begin(endpoint);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Token", device_token);
  http.setTimeout(3000);

  // Generar ID único para idempotencia
  eventSequence++;
  String eventId = DEVICE_ID + "-" + String(millis()) + "-" + String(eventSequence);

  // Formatear fecha aproximada o delegar al backend
  String payload = "{\"event_id\":\"" + eventId + "\","
                   "\"sensor_id\":\"IR_1\","
                   "\"sensor_type\":\"IR\","
                   "\"event_type\":\"" + String(eventType) + "\","
                   "\"occurred_at\":\"2026-10-15T12:00:00Z\","
                   "\"metadata\":{\"gpio\":" + String(IR_GPIO_PIN) + ",\"simulated\":false}}";

  int httpCode = http.POST(payload);
  Serial.printf("[EVENTO %s] Enviado ID: %s | HTTP: %d\n", eventType, eventId.c_str(), httpCode);
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
  Serial.println("  RECINTO CONTROL - FASE 1: ESP32-S3 + IR + OV5640");
  Serial.println("==================================================");

  // Configuración de la entrada del sensor IR
  if (IR_ENABLED) {
    pinMode(IR_GPIO_PIN, INPUT_PULLUP);
    stableIrState = digitalRead(IR_GPIO_PIN);
    Serial.printf("Sensor IR HABILITADO en GPIO %d (Estado inicial: %s)\n",
                  IR_GPIO_PIN, (stableIrState == IR_ACTIVE_LEVEL ? "INTERRUMPIDO" : "DESPEJADO"));
  } else {
    Serial.println("AVISO: Sensor IR DESHABILITADO por seguridad (IR_ENABLED=false).");
    Serial.println("       Valida el pin libre con multimetro antes de activarlo.");
  }

  // Inicialización de la Cámara OV5640
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

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Error al iniciar camara: 0x%x\n", err);
  } else {
    Serial.println("Camara OV5640 inicializada correctamente.");
  }

  // Conexión Wi-Fi
  Serial.print("Conectando a Wi-Fi: ");
  Serial.println(ssid);
  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  WiFi.begin(ssid, password);

  unsigned long startWifi = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - startWifi < 20000)) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWIFI CONECTADO");
    Serial.print("IP ESP32: http://");
    Serial.println(WiFi.localIP());
    startCameraServer();
    sendHeartbeat();
  } else {
    Serial.println("\nError de conexion Wi-Fi. Operando en modo degradado local.");
  }
}

// ==============================================================================
// BUCLE PRINCIPAL NO BLOQUEANTE
// ==============================================================================

void loop() {
  unsigned long currentMillis = millis();

  // 1. Tarea de fondo de Heartbeat (cada 15s)
  if (currentMillis - lastHeartbeatTime >= HEARTBEAT_INTERVAL_MS) {
    lastHeartbeatTime = currentMillis;
    sendHeartbeat();
  }

  // 2. Lectura y debounce del sensor IR (solo si está habilitado)
  if (IR_ENABLED) {
    int reading = digitalRead(IR_GPIO_PIN);

    if (reading != lastRawIrReading) {
      lastDebounceTime = currentMillis;
    }

    if ((currentMillis - lastDebounceTime) > DEBOUNCE_DELAY_MS) {
      if (reading != stableIrState && (currentMillis - lastEventSentTime > REPEAT_WINDOW_MS)) {
        stableIrState = reading;
        lastEventSentTime = currentMillis;

        if (stableIrState == IR_ACTIVE_LEVEL) {
          sendSensorEvent("IR_INTERRUPTED");
        } else {
          sendSensorEvent("IR_CLEARED");
        }
      }
    }

    lastRawIrReading = reading;
  }

  // Pequeña pausa cooperativa para no saturar la CPU
  delay(10);
}
