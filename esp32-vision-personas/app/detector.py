import io
import time
import logging
from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np

logger = logging.getLogger("detector")


class PersonDetector:
    """
    Detector de personas local basado en YOLOv8 (optimizado para CPU).
    Filtra estrictamente la clase 'person' (ID 0 en COCO).
    NO realiza reconocimiento facial, identificación biométrica ni conteo acumulado de flujo.
    """

    COCO_PERSON_CLASS_ID = 0

    def __init__(self, model_name: str = "yolov8n.pt", confidence_threshold: float = 0.45):
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self._model = None
        self.is_initialized = False
        self.initialization_error: Optional[str] = None

    def initialize(self):
        """
        Carga diferida del modelo YOLO para evitar demoras en el arranque de FastAPI.
        """
        try:
            import torch
            # Compatibilidad con PyTorch 2.6+: restablecer weights_only=False para checkpoints de YOLO
            if hasattr(torch, "load"):
                _orig_load = torch.load
                def _patched_load(*args, **kwargs):
                    if "weights_only" not in kwargs:
                        kwargs["weights_only"] = False
                    return _orig_load(*args, **kwargs)
                torch.load = _patched_load

            from ultralytics import YOLO
            logger.info("Cargando modelo YOLO: %s", self.model_name)
            self._model = YOLO(self.model_name)
            self.is_initialized = True
            self.initialization_error = None
            logger.info("Modelo YOLO inicializado exitosamente.")
        except Exception as e:
            self.initialization_error = f"Error cargando YOLO ({self.model_name}): {str(e)}"
            logger.error(self.initialization_error)

    def detect(self, jpeg_bytes: bytes) -> Dict[str, Any]:
        """
        Ejecuta la inferencia sobre los bytes JPEG.
        Retorna diccionario con:
          - count: número de personas estimadas en el encuadre
          - boxes: lista de coordenadas y confianza de cada persona
          - annotated_jpeg: bytes JPEG con las cajas delimitadoras dibujadas
          - inference_ms: tiempo de cómputo en milisegundos
          - disclaimer: aviso de privacidad y alcance técnico
        """
        start_t = time.perf_counter()

        if not self.is_initialized:
            self.initialize()

        if not self.is_initialized or self._model is None:
            return {
                "count": 0,
                "boxes": [],
                "annotated_jpeg": jpeg_bytes,
                "inference_ms": 0.0,
                "error": self.initialization_error or "Detector no inicializado",
                "disclaimer": "Estimación visual local instantánea. No acumulativo ni biométrico."
            }

        try:
            # Cargar imagen con PIL
            image = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
            img_width, img_height = image.size

            # Inferencia YOLO restringida a clase 0 (person)
            results = self._model.predict(
                source=image,
                conf=self.confidence_threshold,
                classes=[self.COCO_PERSON_CLASS_ID],
                verbose=False,
                device="cpu"
            )

            detected_boxes: List[Dict[str, Any]] = []
            draw = ImageDraw.Draw(image)

            # Intentar cargar una fuente legible, o fuente por defecto
            try:
                font = ImageFont.load_default()
            except Exception:
                font = None

            for result in results:
                boxes = result.boxes
                if boxes is None or len(boxes) == 0:
                    continue

                for box in boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())

                    if cls_id == self.COCO_PERSON_CLASS_ID and conf >= self.confidence_threshold:
                        raw_coords = box.xyxy[0]
                        coords = raw_coords.tolist() if hasattr(raw_coords, "tolist") else list(raw_coords)
                        x1, y1, x2, y2 = [int(v) for v in coords]

                        detected_boxes.append({
                            "class": "person",
                            "confidence": round(conf, 3),
                            "box": [x1, y1, x2, y2]
                        })

                        # Dibujar rectángulo en color cian/esmeralda
                        draw.rectangle([x1, y1, x2, y2], outline="#00e5ff", width=3)

                        # Etiqueta con porcentaje
                        label = f"Persona {int(conf * 100)}%"
                        text_bbox = draw.textbbox((x1, max(0, y1 - 18)), label, font=font) if hasattr(draw, "textbbox") else (x1, y1 - 18, x1 + 80, y1)
                        draw.rectangle(text_bbox, fill="#00e5ff")
                        draw.text((x1 + 2, max(0, y1 - 16)), label, fill="#000000", font=font)

            # Banner informativo inferior discreto
            banner_text = f"Personas visibles: {len(detected_boxes)} | Confianza >= {int(self.confidence_threshold*100)}%"
            draw.rectangle([0, img_height - 22, img_width, img_height], fill="#111827")
            draw.text((8, img_height - 18), banner_text, fill="#38bdf8", font=font)

            # Re-codificar a JPEG en memoria
            output_buffer = io.BytesIO()
            image.save(output_buffer, format="JPEG", quality=85)
            annotated_bytes = output_buffer.getvalue()

            elapsed_ms = (time.perf_counter() - start_t) * 1000.0

            return {
                "count": len(detected_boxes),
                "boxes": detected_boxes,
                "annotated_jpeg": annotated_bytes,
                "inference_ms": round(elapsed_ms, 1),
                "error": None,
                "disclaimer": "Estimación de personas visibles en el fotograma actual. No realiza conteo acumulado ni identificación biométrica."
            }

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_t) * 1000.0
            logger.error("Error en detección YOLO: %s", str(e))
            return {
                "count": 0,
                "boxes": [],
                "annotated_jpeg": jpeg_bytes,
                "inference_ms": round(elapsed_ms, 1),
                "error": f"Fallo al procesar imagen: {str(e)}",
                "disclaimer": "Estimación no disponible por error de procesamiento."
            }
