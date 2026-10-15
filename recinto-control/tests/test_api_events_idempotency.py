import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)
AUTH_HEADERS = {"X-Device-Token": "esp32_device_secret_token_seguro_fase1"}


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_event_ingestion_and_idempotency():
    device_id = "ESP32_UNIT_TEST"
    event_id = "evt-uuid-12345-abc"
    now_str = datetime.now(timezone.utc).isoformat()

    payload = {
        "event_id": event_id,
        "sensor_id": "IR_1",
        "sensor_type": "IR",
        "event_type": "IR_INTERRUPTED",
        "occurred_at": now_str,
        "metadata": {"simulated": True}
    }

    # 1. Primera inserción: debe ser aceptada
    resp1 = client.post(f"/api/v1/devices/{device_id}/events", json=payload, headers=AUTH_HEADERS)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "accepted"
    assert data1["is_duplicate"] is False
    assert data1["event_id"] == event_id

    # 2. Segunda inserción con IDÉNTICO event_id: debe ser ignorada por idempotencia
    resp2 = client.post(f"/api/v1/devices/{device_id}/events", json=payload, headers=AUTH_HEADERS)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "duplicate_ignored"
    assert data2["is_duplicate"] is True

    # 3. Consultar dashboard: debe reflejar únicamente 1 interrupción, no 2
    dash_resp = client.get("/api/v1/dashboard/summary")
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["ir_interrupted_count"] == 1
    assert dash_data["ir_cleared_count"] == 0
    assert "no_disponible" in dash_data["cruces_confirmados"]


def test_access_evaluate_inactive_in_phase_1():
    payload = {
        "credential_id": "RFID_CARD_A1B2C3",
        "reader_id": "RFID_1"
    }
    resp = client.post("/api/v1/access/evaluate", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["decision"] == "DENIED"
    assert data["can_actuate_servo"] is False
    assert "Fase 1" in data["reason"]
