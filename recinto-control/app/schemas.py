from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    firmware_version: str = Field(..., max_length=32)
    ip_address: Optional[str] = Field(None, max_length=64)
    wifi_rssi: Optional[int] = Field(None, ge=-120, le=0)
    sensor_states: Optional[Dict[str, Any]] = Field(default_factory=dict)


class HeartbeatResponse(BaseModel):
    status: str = "ok"
    server_time: datetime
    acknowledged_device: str


class EventIngestRequest(BaseModel):
    event_id: str = Field(..., max_length=64, description="ID único para evitar duplicación")
    sensor_id: str = Field(default="IR_1", max_length=32)
    sensor_type: str = Field(default="IR", max_length=32)
    event_type: str = Field(..., description="IR_INTERRUPTED o IR_CLEARED")
    occurred_at: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EventIngestResponse(BaseModel):
    status: str
    event_id: str
    is_duplicate: bool
    message: str


class EventItem(BaseModel):
    event_id: str
    sensor_id: str
    event_type: str
    occurred_at: datetime
    is_simulated: bool


class DashboardSummary(BaseModel):
    device_id: Optional[str] = None
    online: bool = False
    last_seen_at: Optional[datetime] = None
    firmware_version: Optional[str] = None
    ip_address: Optional[str] = None
    wifi_rssi: Optional[int] = None
    ir_interrupted_count: int = 0
    ir_cleared_count: int = 0
    # Reglas críticas de precisión y honestidad técnica:
    personas_visibles: Optional[int] = None
    cruces_confirmados: Optional[str] = "no_disponible (requiere Fase 6 con segundo IR)"
    ocupacion_estimada: Optional[str] = "no_disponible (requiere flujo bidireccional validado)"
    recent_events: List[EventItem] = Field(default_factory=list)


class AccessEvaluateRequest(BaseModel):
    credential_id: str = Field(..., max_length=64)
    reader_id: str = Field(default="RFID_1", max_length=32)


class AccessEvaluateResponse(BaseModel):
    decision: str = "DENIED"
    reason: str = "Modulo de acceso inactivo en Fase 1 (esperando autorizacion de Fase 2)"
    expires_in_seconds: int = 0
    can_actuate_servo: bool = False
