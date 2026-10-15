from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import httpx

from app.database import get_db
from app.models import Device, SensorEvent
from app.schemas import DashboardSummary, EventItem
from app.config import settings

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    threshold_online = now - timedelta(seconds=45)

    # Buscar el dispositivo principal más reciente
    device = db.query(Device).order_by(Device.last_seen_at.desc()).first()

    is_online = False
    device_id = None
    last_seen = None
    firmware_ver = None
    ip_addr = None
    rssi = None

    if device:
        device_id = device.device_id
        last_seen = device.last_seen_at
        firmware_ver = device.firmware_version
        ip_addr = device.ip_address
        rssi = device.wifi_rssi
        if device.last_seen_at and device.last_seen_at >= threshold_online:
            is_online = True

    # Métricas de eventos IR
    interrupted_count = db.query(func.count(SensorEvent.id)).filter(
        SensorEvent.event_type == "IR_INTERRUPTED"
    ).scalar() or 0

    cleared_count = db.query(func.count(SensorEvent.id)).filter(
        SensorEvent.event_type == "IR_CLEARED"
    ).scalar() or 0

    # Últimos 15 eventos
    recent_db_events = db.query(SensorEvent).order_by(
        SensorEvent.occurred_at.desc()
    ).limit(15).all()

    recent_items = [
        EventItem(
            event_id=ev.event_id,
            sensor_id=ev.sensor_id,
            event_type=ev.event_type,
            occurred_at=ev.occurred_at,
            is_simulated=ev.is_simulated
        ) for ev in recent_db_events
    ]

    # Consultar personas_visibles desde el microservicio de visión si está activo (en 8088 o local)
    personas_visibles = None
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get("http://127.0.0.1:8088/api/count")
            if resp.status_code == 200:
                data = resp.json()
                personas_visibles = data.get("persons_visible")
    except Exception:
        # Si el servicio de visión está apagado o en otra máquina, no bloquea
        personas_visibles = None

    return DashboardSummary(
        device_id=device_id,
        online=is_online,
        last_seen_at=last_seen,
        firmware_version=firmware_ver,
        ip_address=ip_addr,
        wifi_rssi=rssi,
        ir_interrupted_count=interrupted_count,
        ir_cleared_count=cleared_count,
        personas_visibles=personas_visibles,
        cruces_confirmados="no_disponible (requiere Fase 6 con segundo IR)",
        ocupacion_estimada="no_disponible (requiere flujo bidireccional validado)",
        recent_events=recent_items
    )
