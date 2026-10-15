from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, JSON,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    device_id = Column(String(64), primary_key=True, index=True)
    firmware_version = Column(String(32), nullable=False, default="1.0.0")
    status = Column(String(32), nullable=False, default="online")
    ip_address = Column(String(64), nullable=True)
    wifi_rssi = Column(Integer, nullable=True)
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    events = relationship("SensorEvent", back_populates="device", cascade="all, delete-orphan")


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False)
    sensor_type = Column(String(32), nullable=False)  # "IR", "RFID", etc.
    label = Column(String(64), nullable=False)        # ej: "Paso_Principal_IR1"
    gpio_pin = Column(Integer, nullable=True)         # None si pendiente de validación
    is_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class SensorEvent(Base):
    __tablename__ = "sensor_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), ForeignKey("devices.device_id"), nullable=False, index=True)
    event_id = Column(String(64), nullable=False)     # UUID o hash generado en el firmware
    sensor_id = Column(String(32), nullable=False, default="IR_1")
    sensor_type = Column(String(32), nullable=False, default="IR")
    event_type = Column(String(64), nullable=False)   # "IR_INTERRUPTED", "IR_CLEARED"
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), default=utc_now)
    is_simulated = Column(Boolean, default=False)
    metadata_json = Column(JSON, nullable=True)

    device = relationship("Device", back_populates="events")

    # REGLA CRÍTICA: Restricción única para garantizar idempotencia estricta
    __table_args__ = (
        UniqueConstraint("device_id", "event_id", name="uq_device_event"),
        Index("idx_device_occurred", "device_id", "occurred_at"),
    )


class AccessAttempt(Base):
    __tablename__ = "access_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(64), nullable=False, index=True)
    credential_id = Column(String(64), nullable=False)
    decision = Column(String(32), nullable=False)      # "DENIED", "AUTHORIZED_WAITING_PASSAGE"
    reason = Column(String(128), nullable=False)
    attempted_at = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(64), nullable=False)
    actor = Column(String(64), nullable=False, default="system")
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
