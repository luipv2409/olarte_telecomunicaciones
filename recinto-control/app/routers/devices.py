from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Device
from app.schemas import HeartbeatRequest, HeartbeatResponse
from app.security import verify_device_token

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.post("/{device_id}/heartbeat", response_model=HeartbeatResponse)
def device_heartbeat(
    device_id: str = Path(..., max_length=64),
    payload: HeartbeatRequest = ...,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_device_token)
):
    now = datetime.now(timezone.utc)
    device = db.query(Device).filter(Device.device_id == device_id).first()

    if not device:
        device = Device(
            device_id=device_id,
            firmware_version=payload.firmware_version,
            status="online",
            ip_address=payload.ip_address,
            wifi_rssi=payload.wifi_rssi,
            last_seen_at=now
        )
        db.add(device)
    else:
        device.firmware_version = payload.firmware_version
        device.status = "online"
        device.ip_address = payload.ip_address
        device.wifi_rssi = payload.wifi_rssi
        device.last_seen_at = now

    db.commit()

    return HeartbeatResponse(
        status="ok",
        server_time=now,
        acknowledged_device=device_id
    )
