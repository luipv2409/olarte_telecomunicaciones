import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import Device, SensorEvent
from app.schemas import EventIngestRequest, EventIngestResponse
from app.security import verify_device_token

logger = logging.getLogger("events_router")
router = APIRouter(prefix="/api/v1/devices", tags=["events"])


@router.post("/{device_id}/events", response_model=EventIngestResponse)
def ingest_event(
    device_id: str = Path(..., max_length=64),
    payload: EventIngestRequest = ...,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_device_token)
):
    now = datetime.now(timezone.utc)

    # Asegurar que el dispositivo exista
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if not device:
        device = Device(
            device_id=device_id,
            status="online",
            last_seen_at=now
        )
        db.add(device)
        db.flush()
    else:
        device.last_seen_at = now

    # Verificar si el evento ya existe para cumplir idempotencia antes de insertar
    existing = db.query(SensorEvent).filter(
        SensorEvent.device_id == device_id,
        SensorEvent.event_id == payload.event_id
    ).first()

    if existing:
        return EventIngestResponse(
            status="duplicate_ignored",
            event_id=payload.event_id,
            is_duplicate=True,
            message="Evento ya procesado previamente. Idempotencia garantizada."
        )

    is_simulated = bool(payload.metadata.get("simulated", False)) if payload.metadata else False

    new_event = SensorEvent(
        device_id=device_id,
        event_id=payload.event_id,
        sensor_id=payload.sensor_id,
        sensor_type=payload.sensor_type,
        event_type=payload.event_type,
        occurred_at=payload.occurred_at,
        received_at=now,
        is_simulated=is_simulated,
        metadata_json=payload.metadata
    )

    try:
        db.add(new_event)
        db.commit()
    except IntegrityError:
        db.rollback()
        return EventIngestResponse(
            status="duplicate_ignored",
            event_id=payload.event_id,
            is_duplicate=True,
            message="Colision de clave unica. Evento duplicado descartado de forma segura."
        )

    return EventIngestResponse(
        status="accepted",
        event_id=payload.event_id,
        is_duplicate=False,
        message="Evento registrado exitosamente en base de datos."
    )
