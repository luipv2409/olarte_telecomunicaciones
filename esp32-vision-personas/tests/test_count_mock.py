import io
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from PIL import Image
import httpx

from app.detector import PersonDetector
from app.deepseek_client import DeepSeekVisionClient


def create_solid_jpeg(width: int = 100, height: int = 100) -> bytes:
    """Crea una imagen JPEG válida en memoria para pruebas"""
    img = Image.new("RGB", (width, height), color=(50, 100, 150))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_detector_corrupt_image():
    """Verifica que el detector maneje grácilmente imágenes corruptas sin lanzar excepciones no controladas"""
    detector = PersonDetector(model_name="yolov8n.pt")
    detector.is_initialized = True
    detector._model = MagicMock()

    result = detector.detect(b"DATOS_CORRUPTOS_NO_IMAGEN")
    assert result["count"] == 0
    assert result["boxes"] == []
    assert result["error"] is not None
    assert "Fallo al procesar imagen" in result["error"]


def test_detector_zero_persons():
    """Verifica que devuelva conteo 0 cuando no hay detecciones en el encuadre"""
    detector = PersonDetector(model_name="yolov8n.pt", confidence_threshold=0.5)
    detector.is_initialized = True

    # Simular predicción sin cajas
    mock_result = MagicMock()
    mock_result.boxes = []
    mock_model = MagicMock()
    mock_model.predict.return_value = [mock_result]
    detector._model = mock_model

    jpeg_data = create_solid_jpeg()
    result = detector.detect(jpeg_data)

    assert result["count"] == 0
    assert len(result["boxes"]) == 0
    assert result["error"] is None
    assert isinstance(result["annotated_jpeg"], bytes)


def test_detector_multiple_persons_and_filter_other_classes():
    """
    Verifica que el detector cuente adecuadamente múltiples personas
    y descarte objetos que no pertenezcan a la clase 0 (person).
    """
    detector = PersonDetector(model_name="yolov8n.pt", confidence_threshold=0.4)
    detector.is_initialized = True

    # Cajas simuladas:
    # 1. Clase 0 (persona), confianza 0.85 -> Debe incluirse
    # 2. Clase 0 (persona), confianza 0.90 -> Debe incluirse
    # 3. Clase 1 (bicicleta), confianza 0.95 -> Debe descartarse
    # 4. Clase 0 (persona), confianza 0.20 -> Debe descartarse por baja confianza
    box1 = MagicMock()
    box1.cls = [MagicMock(item=lambda: 0)]
    box1.conf = [MagicMock(item=lambda: 0.85)]
    box1.xyxy = [[10, 10, 50, 80]]

    box2 = MagicMock()
    box2.cls = [MagicMock(item=lambda: 0)]
    box2.conf = [MagicMock(item=lambda: 0.90)]
    box2.xyxy = [[60, 10, 90, 80]]

    box3 = MagicMock()
    box3.cls = [MagicMock(item=lambda: 1)]  # no es persona
    box3.conf = [MagicMock(item=lambda: 0.95)]
    box3.xyxy = [[20, 40, 70, 90]]

    box4 = MagicMock()
    box4.cls = [MagicMock(item=lambda: 0)]
    box4.conf = [MagicMock(item=lambda: 0.20)]  # debajo del 0.40
    box4.xyxy = [[5, 5, 20, 40]]

    mock_result = MagicMock()
    mock_result.boxes = [box1, box2, box3, box4]
    mock_model = MagicMock()
    mock_model.predict.return_value = [mock_result]
    detector._model = mock_model

    jpeg_data = create_solid_jpeg()
    result = detector.detect(jpeg_data)

    assert result["count"] == 2
    assert len(result["boxes"]) == 2
    assert result["boxes"][0]["confidence"] == 0.85
    assert result["boxes"][1]["confidence"] == 0.90


@pytest.mark.asyncio
async def test_deepseek_client_disabled():
    """Verifica que el cliente DeepSeek devuelva aviso limpio si está deshabilitado"""
    client = DeepSeekVisionClient(api_key="sk-test", enabled=False)
    result = await client.analyze_image(create_solid_jpeg())

    assert result["success"] is False
    assert result["source"] == "deepseek-disabled"
    assert "deshabilitada" in result["error"]


@pytest.mark.asyncio
async def test_deepseek_client_missing_key():
    """Verifica que reporte adecuadamente la ausencia de clave de API"""
    client = DeepSeekVisionClient(api_key="", enabled=True)
    result = await client.analyze_image(create_solid_jpeg())

    assert result["success"] is False
    assert result["source"] == "deepseek-no-key"
    assert "DEEPSEEK_API_KEY" in result["error"]


@pytest.mark.asyncio
async def test_deepseek_client_empty_image():
    """Verifica que no intente enviar fotogramas vacíos"""
    client = DeepSeekVisionClient(api_key="sk-test", enabled=True)
    result = await client.analyze_image(b"")

    assert result["success"] is False
    assert result["source"] == "no-image"


@pytest.mark.asyncio
async def test_deepseek_client_success_mock():
    """Verifica el flujo exitoso de llamada a DeepSeek Vision con mock"""
    client = DeepSeekVisionClient(
        api_key="sk-test-valid",
        model="deepseek-flash",
        enabled=True
    )

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Personas estimadas: 2. Se aprecian dos individuos de pie en una sala bien iluminada."
                }
            }
        ]
    }

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.analyze_image(create_solid_jpeg())

        assert result["success"] is True
        assert result["source"] == "deepseek-api"
        assert "Personas estimadas: 2" in result["estimation"]
        assert "fuera de la LAN" in result["disclaimer"]


@pytest.mark.asyncio
async def test_deepseek_client_timeout():
    """Verifica manejo de timeout en llamadas a DeepSeek"""
    client = DeepSeekVisionClient(
        api_key="sk-test-valid",
        enabled=True,
        timeout_seconds=1.0
    )

    with patch.object(httpx.AsyncClient, "post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Timeout")
        result = await client.analyze_image(create_solid_jpeg())

        assert result["success"] is False
        assert result["source"] == "deepseek-timeout"
        assert "Timeout" in result["error"]
