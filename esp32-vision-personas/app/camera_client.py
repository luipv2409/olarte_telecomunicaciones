import asyncio
import logging
import time
from typing import Optional, Tuple
import httpx

logger = logging.getLogger("camera_client")


class ESP32CameraClient:
    """
    Cliente asíncrono para obtener fotogramas JPEG desde el endpoint /capture del ESP32-S3.
    Implementa timeouts, reconexión con backoff y validación de integridad JPEG.
    """

    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.timeout_seconds = timeout_seconds
        self.is_connected = False
        self.last_success_ts: Optional[float] = None
        self.last_error: Optional[str] = None
        self.consecutive_errors: int = 0
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout_seconds, connect=3.0)
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _is_valid_jpeg(self, data: bytes) -> bool:
        """
        Verifica los bytes mágicos iniciales y finales de un JPEG estándar.
        SOI: 0xFF, 0xD8
        EOI: 0xFF, 0xD9
        """
        if not data or len(data) < 4:
            return False
        return data[:2] == b"\xff\xd8" and data[-2:] == b"\xff\xd9"

    async def fetch_frame(self) -> Tuple[bool, Optional[bytes], Optional[str]]:
        """
        Realiza una petición GET al endpoint /capture del ESP32.
        Retorna (exito, bytes_jpeg, mensaje_error).
        """
        if not self.base_url:
            self.last_error = "ESP32_BASE_URL no está configurada en .env"
            self.is_connected = False
            return False, None, self.last_error

        capture_url = f"{self.base_url}/capture"
        client = await self.get_client()

        try:
            response = await client.get(capture_url)
            if response.status_code == 200:
                raw_bytes = response.content
                if self._is_valid_jpeg(raw_bytes):
                    self.is_connected = True
                    self.last_success_ts = time.time()
                    self.last_error = None
                    self.consecutive_errors = 0
                    return True, raw_bytes, None
                else:
                    err = f"Respuesta recibida pero no es un JPEG válido ({len(raw_bytes)} bytes)"
                    self._record_error(err)
                    return False, None, err
            else:
                err = f"ESP32 respondió con código HTTP {response.status_code}"
                self._record_error(err)
                return False, None, err

        except httpx.TimeoutException:
            err = f"Timeout al contactar ESP32 en {capture_url} tras {self.timeout_seconds}s"
            self._record_error(err)
            return False, None, err
        except httpx.ConnectError:
            err = f"No se pudo conectar al ESP32 en {self.base_url}. Verifica IP y conexión Wi-Fi."
            self._record_error(err)
            return False, None, err
        except Exception as e:
            err = f"Error inesperado al consultar cámara: {type(e).__name__}: {str(e)}"
            self._record_error(err)
            return False, None, err

    def _record_error(self, err_msg: str):
        self.is_connected = False
        self.last_error = err_msg
        self.consecutive_errors += 1
        logger.warning("Fallo en captura de ESP32 [%d]: %s", self.consecutive_errors, err_msg)

    def get_backoff_delay(self) -> float:
        """
        Calcula una espera adicional si hay errores consecutivos para no saturar la red ni la cámara.
        """
        if self.consecutive_errors <= 1:
            return 0.0
        # Espera exponencial acotada a máximo 10 segundos
        return min(10.0, 1.0 * (1.5 ** min(self.consecutive_errors, 6)))
