from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AccessAttempt
from app.schemas import AccessEvaluateRequest, AccessEvaluateResponse
from app.security import verify_device_token

router = APIRouter(prefix="/api/v1/access", tags=["access"])


@router.post("/evaluate", response_model=AccessEvaluateResponse)
def evaluate_access(
    payload: AccessEvaluateRequest,
    db: Session = Depends(get_db),
    _token: str = Depends(verify_device_token)
):
    """
    Contrato preparado para Fase 2 (RFID RC522).
    En Fase 1 este endpoint se encuentra EXPLÍCITAMENTE INACTIVO y rechaza cualquier intento
    para evitar accionamientos no autorizados de actuadores.
    """
    attempt = AccessAttempt(
        device_id="ESP32_S3_RECINTO",
        credential_id=payload.credential_id,
        decision="DENIED",
        reason="Fase 1 activa: Evaluacion logica de acceso inactiva hasta Fase 2"
    )
    db.add(attempt)
    db.commit()

    return AccessEvaluateResponse(
        decision="DENIED",
        reason="Modulo de acceso inactivo en Fase 1 (esperando autorizacion de Fase 2)",
        expires_in_seconds=0,
        can_actuate_servo=False
    )
