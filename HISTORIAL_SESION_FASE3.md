# Historial de sesión - Fase 3 (ESP32-S3 + IR + RFID + Buzzer + Cámara)

Fecha: 2026-11-01

## 1. Estado del entorno Docker
- Contenedor del proyecto: `esp32-vision-personas-vision-service-1` (imagen `esp32-vision-personas-vision-service`).
- Estado: Up (healthy). Puerto host `8088` → contenedor `8000`.
- Los demás contenedores (teleco, ventas_ia, consultorio, etc.) pertenecen a otros proyectos.

## 2. Revisión del firmware `Fase3_ESP32_IR_RFID_Buzzer_Camera`
- La cámara **no graba de forma continua** ni se activa con el IR.
- Solo responde a peticiones HTTP: `/capture` (foto) y `/stream` (MJPEG).
- El IR y el RFID solo envían eventos JSON al backend; no disparan captura.
- El firmware no guarda video ni fotos.

## 3. Evaluación frente al objetivo (control de acceso tipo estadio/universidad)
Cumple parcialmente: detecta y registra, pero no controla el acceso.
- Falta un actuador (servomotor) que abra/cierre la puerta.
- La cámara no está integrada al flujo (sin evidencia por evento).
- No hay verificación de identidad más allá de la tarjeta.
- IR y RFID no están correlacionados (sensor fusion).
- Los UIDs autorizados están fijos en el firmware (`6C8D1B06` GRANTED, `73230E06` DENIED).
- Wi-Fi y token por defecto están escritos en el `.ino` (mover a `secrets.h`).
- Ya existe documentación de Fase 4 (Servo + Sensor Fusion + IA en servidor).

## 4. Base de datos
- El ESP32 no guarda datos; actúa como sensor y envía eventos por HTTP.
- El backend (FastAPI, `esp32-vision-personas/app/main.py`) guarda en SQLite (`app/recinto_events.db`, tabla `ir_events`).
- Se guarda evento y UID, sin fotos ni lista de usuarios.
- La decisión de acceso se toma en el ESP32; el backend solo la registra.

## 5. Problema de conexión al backend y corrección
- Síntoma: `connection refused` al contactar `http://192.168.1.95:8088`.
- Causa: la IP del PC cambió a `192.168.1.13` (misma red que el ESP32 `192.168.1.24`).
- Corrección: en el `.ino`, `BACKEND_BASE_URL` pasó de `http://192.168.1.95:8088` a `http://192.168.1.13:8088`.
- Resultado: los eventos IR devuelven `HTTP 200`.
- Recomendación: reservar la IP del PC en el router (DHCP estático).

## 6. Diagnóstico del lector RFID RC522
| Pin RC522 | ESP32-S3 |
|---|---|
| SDA (SS) | GPIO 2 |
| SCK | GPIO 14 |
| MOSI | GPIO 21 |
| MISO | GPIO 47 |
| IRQ | No se conecta |
| GND | GND |
| RST | GPIO 48 |
| 3.3V | 3.3 V |

- `0x00/0xFF`: lector sin alimentación o cable suelto (se encontró un pin desconectado).
- `0xEE`: MOSI/MISO cruzados, unidos o MISO flotante.
- Valores correctos: `0x92`, `0x91` o `0x82`.

## 7. Cambios de código en esta sesión
- `recinto-control/firmware/Fase3_ESP32_IR_RFID_Buzzer_Camera/Fase3_ESP32_IR_RFID_Buzzer_Camera.ino`: IP del backend actualizada a `192.168.1.13`.

## 8. Pendientes sugeridos
- Integrar el servomotor (Fase 4) y la captura de cámara por evento.
- Mover la lista de tarjetas autorizadas al backend.
- Persistir `recinto_events.db` en un volumen Docker.
- Mover credenciales a `secrets.h`.

