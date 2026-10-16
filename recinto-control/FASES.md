# FASES.md — Plan de Entregas Incrementales y Trazabilidad

Este documento registra el progreso real y auditable de cada fase del proyecto de control de acceso.

---

## Matriz de Estados de Fases

| Fase | Alcance Técnico | Estado del Software | Estado de Hardware | Criterio de Aprobación |
|---|---|---|---|---|
| **Fase 0** | Entorno Docker, PostgreSQL interno y API v1 | **OPERATIVO EN 8088** | N/A | Contenedores levantados en puerto aislado 8088 |
| **Fase 1** | MVP: Monitoreo de 1 sensor IR + Debounce + Idempotencia | **VALIDADO Y OPERATIVO** | **VALIDADO EN HARDWARE** | Evento IR genera registro único en DB sin duplicados ni bloqueos |
| **Fase 2** | Lector RFID RC522: Autorización lógica y auditoría | **VALIDADO Y OPERATIVO** | **VALIDADO EN HARDWARE** | Tarjetas `73230E06` y `6C8D1B06` evaluadas contra políticas de acceso |
| **Fase 3** | Señalización: Buzzer activo (2N2222A en GPIO 42) + LEDs | **OPERATIVO (BUZZER)** | **VALIDADO EN HARDWARE (BUZZER)** | Bip de arranque, éxito (150ms) y denegado (3x80ms) validados |
| **Fase 4** | Servomotor SG90/MG90S para maqueta | **EN PREPARACIÓN** | Pendiente (Step-Down LM2596) | Apertura/cierre controlado con alimentación externa regulada a 5V |
| **Fase 5** | Integración de Cámara OV5640 y Conteo Visual YOLO | **OPERATIVO EN 8088** | **VALIDADO EN HARDWARE** | Personas visibles en encuadre reflejadas en panel de acceso |
| **Fase 6** | Segundo Sensor IR (Cruces y Dirección) | **BLOQUEADA POR HW** | Hardware no disponible | Secuencia A→B / B→A para determinar entrada/salida confirmada |
| **Fase 7** | Endurecimiento, roles, backups y TLS | **PENDIENTE** | N/A | Pruebas de estrés, caída de red y retención de auditoría |

---

## Detalle de Fases Activas

### Fase 0: Línea Base
* **Entregables:** `compose.yaml` (FastAPI + PostgreSQL aislado), `Dockerfile`, `.env.example`, modelos SQLAlchemy, pruebas unitarias.
* **Seguridad:** El puerto `5432` de PostgreSQL no se publica al host; se comunica exclusivamente por la red interna `recinto_control_net`.

### Fase 1: MVP Sensor Infrarrojo
* **Entregables:**
  * Firmware [`Fase1_ESP32_IR_Camera.ino`](file:///c:/xampp/htdocs/OLARTE/recinto-control/firmware/Fase1_ESP32_IR_Camera/Fase1_ESP32_IR_Camera.ino) con lógica anti-rebote no bloqueante.
  * Endpoints REST versionados: `POST /api/v1/devices/{device_id}/events` con deduplicación por clave única `(device_id, event_id)`.
  * Simulador de pruebas sin hardware: [`scripts/simulate_events.py`](file:///c:/xampp/htdocs/OLARTE/recinto-control/scripts/simulate_events.py).
* **Restricción de precisión:** El sistema NO afirma que un disparo IR sea una persona que ingresó; reporta estrictamente `IR_INTERRUPTED` e `IR_CLEARED`.
