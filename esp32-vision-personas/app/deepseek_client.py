import base64
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger("deepseek_client")


class DeepSeekVisionClient:
    """
    Adaptador para la API de DeepSeek con soporte multimodal de imágenes.
    
    Principios de seguridad y costos:
    1. La clave DEEPSEEK_API_KEY nunca se expone al frontend ni a los logs.
    2. NUNCA se invoca de forma automática por fotograma; solo por petición manual del usuario.
    3. Si DEEPSEEK_VISION_ENABLED es false o la clave está vacía, devuelve un aviso claro sin fallar.
    4. Las respuestas se etiquetan estrictamente como estimaciones secundarias externas.
    """

    API_URL = "https://api.deepseek.com/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-flash",
        enabled: bool = False,
        timeout_seconds: float = 20.0
    ):
        self.api_key = api_key.strip() if api_key else ""
        self.model = model
        self.enabled = enabled
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        return self.enabled and bool(self.api_key)

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "has_api_key": bool(self.api_key),
            "model": self.model,
            "ready": self.is_configured()
        }

    async def analyze_image(self, jpeg_bytes: bytes, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía un fotograma JPEG codificado en Base64 al endpoint de DeepSeek.
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "La integración con DeepSeek Vision está deshabilitada (DEEPSEEK_VISION_ENABLED=false en .env).",
                "estimation": None,
                "source": "deepseek-disabled"
            }

        if not self.api_key:
            return {
                "success": False,
                "error": "Falta configurar DEEPSEEK_API_KEY en el archivo .env.",
                "estimation": None,
                "source": "deepseek-no-key"
            }

        if not jpeg_bytes:
            return {
                "success": False,
                "error": "No hay imagen disponible para analizar.",
                "estimation": None,
                "source": "no-image"
            }

        prompt_text = (
            custom_prompt
            or "Analiza detenidamente esta imagen de cámara fija. "
               "Estima cuántas personas ves en el encuadre y describe brevemente la escena. "
               "Responde en formato conciso indicando: 'Personas estimadas: X' seguido de tu observación."
        )

        b64_img = base64.b64encode(jpeg_bytes).decode("utf-8")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_img}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 300,
            "temperature": 0.2
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.API_URL, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "error": None,
                        "estimation": content,
                        "model": self.model,
                        "disclaimer": "Estimación provista por la API externa de DeepSeek a solicitud del usuario. Esta imagen fue transmitida fuera de la LAN únicamente para esta consulta.",
                        "source": "deepseek-api"
                    }
                else:
                    err_msg = f"DeepSeek API respondió con error HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(err_msg)
                    return {
                        "success": False,
                        "error": err_msg,
                        "estimation": None,
                        "source": "deepseek-http-error"
                    }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": f"Timeout al esperar respuesta de DeepSeek tras {self.timeout_seconds}s.",
                "estimation": None,
                "source": "deepseek-timeout"
            }
        except Exception as e:
            logger.error("Error consultando DeepSeek: %s", str(e))
            return {
                "success": False,
                "error": f"Error al conectar con DeepSeek: {str(e)}",
                "estimation": None,
                "source": "deepseek-exception"
            }
