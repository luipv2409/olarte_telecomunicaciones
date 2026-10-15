#!/usr/bin/env python3
"""
Simulador de eventos de sensor para pruebas de Fase 1 sin hardware.
Envía eventos IR_INTERRUPTED e IR_CLEARED al backend FastAPI para verificar
la persistencia en PostgreSQL, la idempotencia y el refresco del panel web.
"""

import sys
import time
import uuid
from datetime import datetime, timezone
import httpx

# Parámetros por defecto
DEFAULT_API_URL = "http://127.0.0.1:8089"
DEFAULT_DEVICE_ID = "ESP32_S3_SIMULADOR"
DEFAULT_TOKEN = "esp32_device_secret_token_seguro_fase1"


def run_simulation(base_url=DEFAULT_API_URL, count=3):
    headers = {
        "Content-Type": "application/json",
        "X-Device-Token": DEFAULT_TOKEN
    }

    print(f"\n=======================================================")
    print(f"  SIMULADOR DE EVENTOS DE SENSOR - RECINTO CONTROL")
    print(f"  Destino: {base_url}")
    print(f"  Dispositivo: {DEFAULT_DEVICE_ID}")
    print(f"=======================================================\n")

    # 1. Enviar Heartbeat
    print("[1/3] Enviando Heartbeat...")
    try:
        hb_payload = {
            "firmware_version": "1.1.0-simulador",
            "ip_address": "127.0.0.1",
            "wifi_rssi": -45,
            "sensor_states": {"IR_1": "READY"}
        }
        res = httpx.post(f"{base_url}/api/v1/devices/{DEFAULT_DEVICE_ID}/heartbeat", json=hb_payload, headers=headers, timeout=5.0)
        print(f"  -> Heartbeat respuesta [{res.status_code}]: {res.json()}")
    except Exception as e:
        print(f"  ❌ Error al enviar heartbeat (¿está corriendo el backend en {base_url}?): {e}")
        return

    # 2. Simular ciclos de paso IR
    print(f"\n[2/3] Simulando {count} secuencias de paso óptico (INTERRUPTED -> CLEARED)...")
    for i in range(1, count + 1):
        event_interrupted_id = f"sim-{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        # A) Interrupción
        payload_int = {
            "event_id": event_interrupted_id,
            "sensor_id": "IR_1",
            "sensor_type": "IR",
            "event_type": "IR_INTERRUPTED",
            "occurred_at": now_str,
            "metadata": {"simulated": True, "cycle": i}
        }
        res_int = httpx.post(f"{base_url}/api/v1/devices/{DEFAULT_DEVICE_ID}/events", json=payload_int, headers=headers, timeout=5.0)
        print(f"  [Ciclo {i}] Evento INTERRUPTED enviado -> Código {res_int.status_code}: {res_int.json().get('status')}")

        time.sleep(1.0)

        # B) Despeje
        event_cleared_id = f"sim-{uuid.uuid4().hex[:12]}"
        payload_clr = {
            "event_id": event_cleared_id,
            "sensor_id": "IR_1",
            "sensor_type": "IR",
            "event_type": "IR_CLEARED",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "metadata": {"simulated": True, "cycle": i}
        }
        res_clr = httpx.post(f"{base_url}/api/v1/devices/{DEFAULT_DEVICE_ID}/events", json=payload_clr, headers=headers, timeout=5.0)
        print(f"  [Ciclo {i}] Evento CLEARED enviado     -> Código {res_clr.status_code}: {res_clr.json().get('status')}")

        time.sleep(1.0)

    # 3. Demostración de Idempotencia (Re-enviar evento idéntico)
    print("\n[3/3] Demostrando Idempotencia (re-enviando el último evento con mismo event_id)...")
    res_dup = httpx.post(f"{base_url}/api/v1/devices/{DEFAULT_DEVICE_ID}/events", json=payload_clr, headers=headers, timeout=5.0)
    data_dup = res_dup.json()
    print(f"  -> Resultado duplicado [{res_dup.status_code}]:")
    print(f"     status: {data_dup.get('status')}")
    print(f"     is_duplicate: {data_dup.get('is_duplicate')}")
    print(f"     mensaje: {data_dup.get('message')}")

    print("\n✅ Simulación completada exitosamente. Abre el dashboard para ver los datos.")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API_URL
    run_simulation(base_url=target)
