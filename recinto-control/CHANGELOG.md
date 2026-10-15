# CHANGELOG.md — Registro de Cambios por Fase

Todas las modificaciones del sistema de control de acceso se registran en este archivo de manera cronológica y auditable.

---

## [1.1.0] - 2026-10-15 (Fase 1: MVP Sensor Infrarrojo y Persistencia)

### Añadido
* **Firmware:** Creación de `Fase1_ESP32_IR_Camera.ino` con lectura no bloqueante de sensor IR, anti-rebote (`debounce`), ventana antirrepetición y reporte de latidos (`heartbeat`).
* **Seguridad de Hardware:** Parámetro `IR_ENABLED = false` por defecto para prevenir daños antes de validar el pin físico del ESP32-S3.
* **Backend:** Endpoints REST v1:
  * `POST /api/v1/devices/{device_id}/heartbeat`: Actualización de estado en línea y señal Wi-Fi.
  * `POST /api/v1/devices/{device_id}/events`: Ingesta idempotente con clave única `(device_id, event_id)` para descartar duplicados de red.
  * `GET /api/v1/dashboard/summary`: Resumen de eventos, telemetría y conteo visual.
  * `POST /api/v1/access/evaluate`: Endpoint preparado e inactivo por seguridad hasta Fase 2.
* **Persistencia:** Base de datos PostgreSQL con tablas `devices`, `sensors`, `sensor_events`, `access_attempts` y `audit_logs`.
* **Simulación:** Script `scripts/simulate_events.py` para validar todo el flujo de software sin requerir hardware conectado.
* **Frontend:** Dashboard responsivo en tema oscuro con telemetría en tiempo real y diferenciación de eventos reales vs. simulados.

---

## [1.0.0] - 2026-10-15 (Fase 0: Línea Base y Entorno Docker Aislado)

### Añadido
* Creación de `compose.yaml` con red interna `recinto_control_net`.
* Configuración de PostgreSQL sin exponer el puerto 5432 al host.
* Configuración de FastAPI con variables de puerto obligatorias en `.env`.
* Especificación de pruebas unitarias automatizadas con `pytest`.
