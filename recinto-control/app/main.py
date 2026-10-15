import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.routers import devices, events, dashboard, access

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("recinto_main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando servicio de control de acceso y telemetria...")
    init_db()
    yield
    logger.info("Servicio detenido limpiamente.")


app = FastAPI(
    title="Recinto Control API",
    description="Servicio backend para control de acceso escalonado y telemetría de sensores ESP32-S3",
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Incluir routers versionados v1
app.include_router(devices.router)
app.include_router(events.router)
app.include_router(dashboard.router)
app.include_router(access.router)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "recinto-control"}


@app.get("/ready")
def readiness_check():
    return {"status": "ready"}


@app.get("/", response_class=HTMLResponse)
def serve_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
