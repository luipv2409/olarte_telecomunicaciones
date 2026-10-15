#!/usr/bin/env python3
"""
Simulador interactivo de sensor infrarrojo para esp32-vision-personas.
Envía eventos IR_INTERRUPTED e IR_CLEARED al backend para probar el widget
del panel web en tiempo real sin requerir hardware conectado.
"""

import sys
import time
import uuid
import httpx

API_BASE_URL = "http://127.0.0.1:8088"
DEVICE_ID = "ESP32_S3"


def simulate_hand_pass(cycles=2):
    print("==================================================")
    print("  SIMULADOR DE PASO DE MANO FRENTE AL SENSOR IR")
    print(f"  Destino: {API_BASE_URL}")
    print("==================================================")

    for i in range(1, cycles + 1):
        # 1. Objeto detectado (Mano interrumpiendo el haz)
        event_id_int = f"sim-{uuid.uuid4().hex[:10]}"
        payload_int = {
            "event_id": event_id_int,
            "sensor_id": "IR_1",
            "event_type": "IR_INTERRUPTED",
            "metadata": {"simulated": True, "cycle": i}
        }
        try:
            r1 = httpx.post(f"{API_BASE_URL}/api/v1/devices/{DEVICE_ID}/events", json=payload_int, timeout=3.0)
            print(f"\n[Ciclo {i}] -> 🔴 MANO DETECTADA (IR_INTERRUPTED)")
            print(f"           Respuesta servidor: HTTP {r1.status_code} | Estado: {r1.json().get('current_state')}")
        except Exception as e:
            print(f"Error conectando al servidor: {e}")
            return

        print("           Esperando 2 segundos con la mano en el sensor...")
        time.sleep(2.0)

        # 2. Objeto retirado (Haz libre)
        event_id_clr = f"sim-{uuid.uuid4().hex[:10]}"
        payload_clr = {
            "event_id": event_id_clr,
            "sensor_id": "IR_1",
            "event_type": "IR_CLEARED",
            "metadata": {"simulated": True, "cycle": i}
        }
        r2 = httpx.post(f"{API_BASE_URL}/api/v1/devices/{DEVICE_ID}/events", json=payload_clr, timeout=3.0)
        print(f"[Ciclo {i}] -> 🟢 MANO RETIRADA (IR_CLEARED)")
        print(f"           Respuesta servidor: HTTP {r2.status_code} | Estado: {r2.json().get('current_state')}")

        time.sleep(1.0)

    print("\n✅ Simulación completada. Revisa http://localhost:8088 en tu navegador.")


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    simulate_hand_pass(cycles=count)
