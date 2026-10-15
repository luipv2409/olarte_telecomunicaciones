from fastapi import Header, HTTPException, status
from app.config import settings


def verify_device_token(x_device_token: str = Header(...)):
    """
    Verifica que las solicitudes del firmware contengan el token secreto configurado.
    """
    if x_device_token != settings.DEVICE_API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de dispositivo no valido o ausente"
        )
    return x_device_token
