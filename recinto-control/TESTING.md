# TESTING.md — Protocolo de Pruebas Unitarias, Simulación y Validación con Hardware

Este manual detalla los procedimientos de verificación para la **Fase 0** y la **Fase 1**, permitiendo ensayar el sistema completo por software antes de conectar físicamente ningún componente.

---

## 1. Pruebas Automáticas sin Hardware (Pytest)

Las pruebas unitarias validan la lógica de autenticación, la idempotencia estricta ante eventos repetidos y la integridad de los modelos de base de datos.

### Ejecución manual:
Desde tu terminal o dentro del contenedor:
```powershell
pytest -v tests/
```

### Casos de prueba cubiertos:
1. `test_health_check`: Verifica respuesta 200 y salud del microservicio.
2. `test_heartbeat_unauthorized`: Rechaza peticiones sin token o con token inválido (`401 Unauthorized`).
3. `test_heartbeat_success`: Registra y actualiza la marca de tiempo y versión de firmware del ESP32.
4. `test_event_ingestion_and_idempotency`:
   * Primer envío de un `event_id`: Devuelve `accepted` e incrementa el contador.
   * Segundo envío del **mismo** `event_id`: Devuelve `duplicate_ignored` y **no** duplica el conteo en la base de datos.
5. `test_access_evaluate_inactive_in_phase_1`: Confirma que la evaluación de acceso se mantenga denegada por seguridad en la Fase 1.

---

## 2. Simulación de Flujo Completo sin ESP32 (Simulador de Eventos)

El script `simulate_events.py` simula un dispositivo emitiendo latidos y ráfagas de interrupciones y despejes de infrarrojo:

```powershell
python scripts/simulate_events.py http://127.0.0.1:8089
```

### Salida esperada:
```text
=======================================================
  SIMULADOR DE EVENTOS DE SENSOR - RECINTO CONTROL
  Destino: http://127.0.0.1:8089
  Dispositivo: ESP32_S3_SIMULADOR
=======================================================

[1/3] Enviando Heartbeat...
  -> Heartbeat respuesta [200]: {'status': 'ok', 'server_time': '...', 'acknowledged_device': 'ESP32_S3_SIMULADOR'}

[2/3] Simulando 3 secuencias de paso óptico (INTERRUPTED -> CLEARED)...
  [Ciclo 1] Evento INTERRUPTED enviado -> Código 200: accepted
  [Ciclo 1] Evento CLEARED enviado     -> Código 200: accepted
  ...

[3/3] Demostrando Idempotencia (re-enviando el último evento con mismo event_id)...
  -> Resultado duplicado [200]:
     status: duplicate_ignored
     is_duplicate: True
     mensaje: Evento ya procesado previamente. Idempotencia garantizada.

✅ Simulación completada exitosamente. Abre el dashboard para ver los datos.
```

---

## 3. Pruebas con Hardware Real (Monitor Serie a 115200 baudios)

Una vez que se valide el pin físico y se active `IR_ENABLED = true` en el sketch:

1. **Al arrancar:**
   ```text
   ==================================================
     RECINTO CONTROL - FASE 1: ESP32-S3 + IR + OV5640
   ==================================================
   Sensor IR HABILITADO en GPIO 1 (Estado inicial: DESPEJADO)
   Camara OV5640 inicializada correctamente.
   WIFI CONECTADO
   IP ESP32: http://192.168.1.111
   [HEARTBEAT] Respuesta servidor: 200
   ```
2. **Al acercar la mano al sensor IR:**
   ```text
   [EVENTO IR_INTERRUPTED] Enviado ID: ESP32_S3_RECINTO-15200-1 | HTTP: 200
   ```
3. **Al retirar la mano:**
   ```text
   [EVENTO IR_CLEARED] Enviado ID: ESP32_S3_RECINTO-17100-2 | HTTP: 200
   ```

---

## 4. Guía de Rollback (Reversión de Emergencia)

Si al flashear el nuevo firmware la cámara presenta inestabilidad:
1. Abre Arduino IDE y vuelve a cargar el firmware de respaldo original probado:  
   [`esp32-vision-personas/firmware/CameraWebServer_ESP32S3_OV5640.ino`](file:///c:/xampp/htdocs/OLARTE/esp32-vision-personas/firmware/CameraWebServer_ESP32S3_OV5640.ino).
2. Verifica que el monitor serie restablezca la transmisión en `http://192.168.1.111`.
