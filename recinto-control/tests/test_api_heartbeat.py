import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# Base de datos en memoria para pruebas unitarias sin dependencias externas
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


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_heartbeat_unauthorized():
    payload = {
        "firmware_version": "1.0.0",
        "ip_address": "192.168.1.50",
        "wifi_rssi": -55
    }
    # Sin cabecera de autenticación
    response = client.post("/api/v1/devices/ESP32_TEST/heartbeat", json=payload)
    assert response.status_code == 422 or response.status_code == 401

    # Con token erróneo
    response_bad_token = client.post(
        "/api/v1/devices/ESP32_TEST/heartbeat",
        json=payload,
        headers={"X-Device-Token": "token_falso"}
    )
    assert response_bad_token.status_code == 401


def test_heartbeat_success():
    payload = {
        "firmware_version": "1.1.0-fase1",
        "ip_address": "192.168.1.111",
        "wifi_rssi": -48,
        "sensor_states": {"IR_1": "DESPEJADO"}
    }
    headers = {"X-Device-Token": "esp32_device_secret_token_seguro_fase1"}
    response = client.post("/api/v1/devices/ESP32_TEST/heartbeat", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["acknowledged_device"] == "ESP32_TEST"
    assert "server_time" in data
