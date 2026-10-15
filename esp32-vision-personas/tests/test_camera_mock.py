import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.camera_client import ESP32CameraClient


# Helper para generar bytes simulados de JPEG válido
def make_mock_jpeg():
    # Cabecera SOI \xff\xd8, cuerpo, cierre EOI \xff\xd9
    return b"\xff\xd8" + b"MOCK_JPEG_CONTENT" * 10 + b"\xff\xd9"


@pytest.mark.asyncio
async def test_camera_client_empty_url():
    """Verifica el comportamiento cuando no hay URL configurada"""
    client = ESP32CameraClient(base_url="")
    success, data, err = await client.fetch_frame()
    assert success is False
    assert data is None
    assert "no está configurada" in err


@pytest.mark.asyncio
async def test_camera_client_valid_jpeg():
    """Verifica la recepción exitosa de un fotograma JPEG válido"""
    client = ESP32CameraClient(base_url="http://192.168.1.50")
    valid_bytes = make_mock_jpeg()

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = valid_bytes

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        success, data, err = await client.fetch_frame()

        assert success is True
        assert data == valid_bytes
        assert err is None
        assert client.is_connected is True
        assert client.consecutive_errors == 0
    await client.close()


@pytest.mark.asyncio
async def test_camera_client_invalid_jpeg():
    """Verifica el rechazo de datos que no son un JPEG válido"""
    client = ESP32CameraClient(base_url="http://192.168.1.50")
    corrupt_bytes = b"ESTO NO ES UN JPEG"

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.content = corrupt_bytes

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        success, data, err = await client.fetch_frame()

        assert success is False
        assert data is None
        assert "no es un JPEG válido" in err
        assert client.is_connected is False
        assert client.consecutive_errors == 1
    await client.close()


@pytest.mark.asyncio
async def test_camera_client_timeout():
    """Verifica el manejo de timeout cuando la cámara no responde a tiempo"""
    client = ESP32CameraClient(base_url="http://192.168.1.50", timeout_seconds=2.0)

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        success, data, err = await client.fetch_frame()

        assert success is False
        assert data is None
        assert "Timeout al contactar ESP32" in err
        assert client.consecutive_errors == 1
        assert client.get_backoff_delay() == 0.0  # Primer error no tiene backoff
    await client.close()


@pytest.mark.asyncio
async def test_camera_client_wifi_disconnect():
    """Verifica el manejo de error de conexión (Wi-Fi caído o IP inalcanzable)"""
    client = ESP32CameraClient(base_url="http://192.168.1.50")

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        success, data, err = await client.fetch_frame()

        assert success is False
        assert data is None
        assert "No se pudo conectar al ESP32" in err
        assert client.consecutive_errors == 1
    await client.close()


@pytest.mark.asyncio
async def test_camera_client_http_500():
    """Verifica el manejo de errores HTTP 500 generados por la cámara"""
    client = ESP32CameraClient(base_url="http://192.168.1.50")

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 500

    with patch.object(httpx.AsyncClient, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        success, data, err = await client.fetch_frame()

        assert success is False
        assert "código HTTP 500" in err
        assert client.consecutive_errors == 1
    await client.close()


def test_camera_client_backoff_progression():
    """Verifica que el backoff aumente progresivamente con fallos reiterados"""
    client = ESP32CameraClient(base_url="http://192.168.1.50")
    assert client.get_backoff_delay() == 0.0

    client.consecutive_errors = 1
    assert client.get_backoff_delay() == 0.0

    client.consecutive_errors = 3
    delay_3 = client.get_backoff_delay()
    assert delay_3 > 0.0

    client.consecutive_errors = 10
    delay_max = client.get_backoff_delay()
    assert delay_max <= 10.0
