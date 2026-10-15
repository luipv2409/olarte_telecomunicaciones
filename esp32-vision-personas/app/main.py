import asyncio
import io
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Response, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.camera_client import ESP32CameraClient
from app.detector import PersonDetector
from app.deepseek_client import DeepSeekVisionClient

# Configuración de registro
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")


import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "recinto_events.db")

def init_sqlite():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ir_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    sensor_id TEXT,
                    event_type TEXT,
                    occurred_at TEXT,
                    received_at TEXT,
                    is_simulated BOOLEAN
                )
            """)
            conn.commit()
    except Exception as e:
        logger.error("Error al inicializar SQLite: %s", e)

def save_event_db(event_id, sensor_id, event_type, occurred_at, received_at, is_simulated):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO ir_events (event_id, sensor_id, event_type, occurred_at, received_at, is_simulated)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_id, sensor_id, event_type, occurred_at, received_at, is_simulated))
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        logger.error("Error al guardar evento en SQLite: %s", e)
        return True


class SystemState:
    """
    Almacenamiento seguro en memoria del estado más reciente del sistema.
    No persiste imágenes en disco para proteger la privacidad del usuario.
    """
    def __init__(self):
        self.latest_raw_jpeg: Optional[bytes] = None
        self.latest_annotated_jpeg: Optional[bytes] = None
        self.latest_count: int = 0
        self.latest_boxes: list = []
        self.latest_capture_ts: Optional[float] = None
        self.latest_inference_ms: float = 0.0
        self.camera_connected: bool = False
        self.camera_error: Optional[str] = None
        self.detector_error: Optional[str] = None
        self.total_frames_processed: int = 0
        self.fps_estimate: float = 0.0
        self.last_frame_ts: float = 0.0

        # Estado del sensor infrarrojo (Fase 1)
        self.ir_state: str = "LIBRE"  # "DETECTADO" o "LIBRE"
        self.ir_is_detected: bool = False
        self.ir_total_activations: int = 0
        self.ir_last_detection_time: Optional[str] = None
        self.ir_recent_events: list = []
        self.seen_event_ids: set = set()
        self.device_online: bool = False
        self.device_last_seen: Optional[float] = None


state = SystemState()
camera_client = ESP32CameraClient(base_url=settings.ESP32_BASE_URL)
detector = PersonDetector(
    model_name=settings.YOLO_MODEL_NAME,
    confidence_threshold=settings.DETECTION_CONFIDENCE
)
deepseek_client = DeepSeekVisionClient(
    api_key=settings.DEEPSEEK_API_KEY,
    model=settings.DEEPSEEK_MODEL,
    enabled=settings.DEEPSEEK_VISION_ENABLED
)


async def camera_worker():
    """
    Tarea de fondo periódica:
    1. Consulta /capture en el ESP32.
    2. Ejecuta la inferencia de personas con YOLO (CPU) en un hilo no bloqueante.
    3. Actualiza el estado en memoria.
    """
    logger.info("Iniciando tarea de captura periódica hacia: %s", settings.ESP32_BASE_URL or "[No configurado]")
    detector.initialize()

    while True:
        try:
            start_loop = time.perf_counter()
            success, jpeg_data, err_msg = await camera_client.fetch_frame()

            if success and jpeg_data:
                state.latest_raw_jpeg = jpeg_data
                state.camera_connected = True
                state.camera_error = None
                state.latest_capture_ts = time.time()

                # Ejecutar inferencia en executor para no bloquear el bucle de eventos
                detect_res = await asyncio.to_thread(detector.detect, jpeg_data)

                state.latest_annotated_jpeg = detect_res["annotated_jpeg"]
                state.latest_count = detect_res["count"]
                state.latest_boxes = detect_res["boxes"]
                state.latest_inference_ms = detect_res["inference_ms"]
                state.detector_error = detect_res["error"]
                state.total_frames_processed += 1

                # Calcular FPS aproximado
                now = time.time()
                if state.last_frame_ts > 0:
                    delta = now - state.last_frame_ts
                    if delta > 0:
                        state.fps_estimate = round(1.0 / delta, 2)
                state.last_frame_ts = now

            else:
                state.camera_connected = False
                state.camera_error = err_msg

            # Respetar el intervalo configurado más el backoff en caso de fallo
            backoff = camera_client.get_backoff_delay()
            sleep_time = max(0.2, settings.CAPTURE_INTERVAL_SECONDS + backoff)
            await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Tarea de captura cancelada.")
            break
        except Exception as e:
            logger.error("Error imprevisto en camera_worker: %s", str(e))
            state.camera_error = str(e)
            await asyncio.sleep(settings.CAPTURE_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio: inicializar base de datos SQLite y lanzar worker
    init_sqlite()
    worker_task = asyncio.create_task(camera_worker())
    yield
    # Cierre: cancelar worker y cerrar cliente HTTP
    worker_task.cancel()
    await camera_client.close()
    logger.info("Servidor detenido limpiamente.")


app = FastAPI(
    title="ESP32-S3 OV5640 Person Counter & Access Control",
    description="Sistema local de conteo de personas y monitoreo de sensores para ESP32-S3",
    version="1.1.0",
    lifespan=lifespan
)

# Montar estáticos y plantillas
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


# ==============================================================================
# ENDPOINTS PRINCIPALES
# ==============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Panel web principal con vista en vivo, métricas de detección, estado del sensor IR y controles.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "esp32_url": settings.ESP32_BASE_URL,
            "interval_seconds": settings.CAPTURE_INTERVAL_SECONDS,
            "confidence": settings.DETECTION_CONFIDENCE,
            "deepseek_configured": deepseek_client.is_configured(),
            "deepseek_model": settings.DEEPSEEK_MODEL
        }
    )


@app.get("/health")
async def health_check():
    """
    Endpoint de salud para Docker HEALTHCHECK y balanceadores.
    """
    return {
        "status": "healthy",
        "service": "esp32-vision-personas",
        "timestamp": time.time(),
        "camera_connected": state.camera_connected
    }


@app.get("/api/status")
async def get_status():
    """
    Estado detallado de los subsistemas: Cámara ESP32, Detector YOLO, Sensor IR y DeepSeek.
    """
    return {
        "camera": {
            "connected": state.camera_connected,
            "base_url": settings.ESP32_BASE_URL,
            "last_capture_ts": state.latest_capture_ts,
            "error": state.camera_error,
            "frames_processed": state.total_frames_processed
        },
        "detector": {
            "model": settings.YOLO_MODEL_NAME,
            "confidence_threshold": settings.DETECTION_CONFIDENCE,
            "persons_visible": state.latest_count,
            "inference_ms": state.latest_inference_ms,
            "error": state.detector_error,
            "boxes": state.latest_boxes
        },
        "ir_sensor": {
            "state": state.ir_state,
            "is_detected": state.ir_is_detected,
            "total_activations": state.ir_total_activations,
            "last_detection_time": state.ir_last_detection_time,
            "recent_events": state.ir_recent_events[:15]
        },
        "deepseek": deepseek_client.get_status_info(),
        "fps_estimate": state.fps_estimate,
        "disclaimer": "Estimación instantánea de personas presentes en el encuadre. No acumulativo ni biométrico."
    }


@app.post("/api/v1/devices/{device_id}/events")
async def receive_sensor_event(device_id: str, payload: Dict[str, Any]):
    """
    Recibe eventos de sensores (IR_INTERRUPTED / IR_CLEARED) con idempotencia y deduplicación.
    """
    event_id = payload.get("event_id")
    event_type = payload.get("event_type", "IR_INTERRUPTED")
    sensor_id = payload.get("sensor_id", "IR_1")
    occurred_at = payload.get("occurred_at") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    metadata = payload.get("metadata", {})
    is_simulated = bool(metadata.get("simulated", False))
    received_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Idempotencia: descartar eventos repetidos
    if event_id and event_id in state.seen_event_ids:
        return {
            "status": "duplicate_ignored",
            "is_duplicate": True,
            "event_id": event_id,
            "current_state": state.ir_state
        }

    if event_id:
        state.seen_event_ids.add(event_id)
        if len(state.seen_event_ids) > 2000:
            state.seen_event_ids.clear()

    # Persistencia en base de datos SQLite
    is_new = save_event_db(event_id, sensor_id, event_type, occurred_at, received_at, is_simulated)
    if not is_new and event_id:
        return {
            "status": "duplicate_ignored",
            "is_duplicate": True,
            "event_id": event_id,
            "current_state": state.ir_state
        }

    # Transición de estado del sensor IR
    if event_type == "IR_INTERRUPTED":
        state.ir_state = "DETECTADO"
        state.ir_is_detected = True
        state.ir_total_activations += 1
        state.ir_last_detection_time = time.strftime("%H:%M:%S")
        logger.info("[IR] -> OBJETO DETECTADO (Total: %d)", state.ir_total_activations)
    elif event_type == "IR_CLEARED":
        state.ir_state = "LIBRE"
        state.ir_is_detected = False
        logger.info("[IR] -> HAZ DESPEJADO (LIBRE)")

    # Historial reciente en memoria
    state.ir_recent_events.insert(0, {
        "event_id": event_id or f"evt-{int(time.time()*1000)}",
        "event_type": event_type,
        "sensor_id": sensor_id,
        "time": time.strftime("%H:%M:%S"),
        "is_simulated": is_simulated
    })
    if len(state.ir_recent_events) > 30:
        state.ir_recent_events = state.ir_recent_events[:30]

    return {
        "status": "accepted",
        "is_duplicate": False,
        "event_id": event_id,
        "current_state": state.ir_state,
        "total_activations": state.ir_total_activations
    }


@app.post("/api/v1/devices/{device_id}/heartbeat")
async def receive_device_heartbeat(device_id: str, payload: Optional[Dict[str, Any]] = None):
    """
    Latido periódico del ESP32 para verificar estado de conexión.
    """
    state.device_online = True
    state.device_last_seen = time.time()
    return {
        "status": "ok",
        "device_id": device_id,
        "server_time": time.time()
    }


@app.get("/api/v1/events")
async def get_events_history():
    """
    Retorna el estado actual del sensor y el historial de activaciones.
    """
    return {
        "current_state": state.ir_state,
        "is_detected": state.ir_is_detected,
        "total_activations": state.ir_total_activations,
        "last_detection_time": state.ir_last_detection_time,
        "events": state.ir_recent_events
    }


@app.get("/api/count")
async def get_count():
    """
    Consulta ligera de conteo de personas en el fotograma actual.
    """
    return {
        "persons_visible": state.latest_count,
        "timestamp": state.latest_capture_ts,
        "inference_ms": state.latest_inference_ms,
        "camera_connected": state.camera_connected,
        "disclaimer": "Estimación de personas visibles en el fotograma actual. No realiza conteo acumulado."
    }


@app.get("/api/snapshot")
async def get_snapshot(raw: bool = Query(False, description="Si es true entrega el JPEG original sin recuadros")):
    """
    Entrega el último fotograma JPEG disponible (anotado por defecto).
    """
    img_data = state.latest_raw_jpeg if raw else state.latest_annotated_jpeg

    if img_data is None:
        # Generar un placeholder SVG con mensaje claro
        msg = "Esperando captura del ESP32..." if not state.camera_error else f"Error camara: {state.camera_error}"
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
            <rect width="100%" height="100%" fill="#0f172a"/>
            <text x="50%" y="45%" text-anchor="middle" fill="#94a3b8" font-family="sans-serif" font-size="20">
                ESP32-S3 OV5640
            </text>
            <text x="50%" y="55%" text-anchor="middle" fill="#38bdf8" font-family="sans-serif" font-size="14">
                {msg}
            </text>
        </svg>"""
        return Response(content=svg_content, media_type="image/svg+xml")

    return Response(
        content=img_data,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.post("/api/analyze/deepseek")
async def analyze_with_deepseek(payload: Optional[Dict[str, Any]] = None):
    """
    Acción explícita solicitada por el usuario para consultar la API de DeepSeek Vision
    sobre el fotograma actual. NUNCA se ejecuta de forma automática.
    """
    if state.latest_raw_jpeg is None:
        raise HTTPException(
            status_code=400,
            detail="No hay ningún fotograma capturado para enviar a DeepSeek."
        )

    custom_prompt = payload.get("prompt") if payload else None
    result = await deepseek_client.analyze_image(
        jpeg_bytes=state.latest_raw_jpeg,
        custom_prompt=custom_prompt
    )
    return result
