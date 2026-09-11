from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PatientCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    date_of_birth: date | None = None
    consent_to_call: bool = False


class SlotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    doctor_id: UUID
    starts_at: datetime
    duration_minutes: int
    is_available: bool


class AppointmentCreate(BaseModel):
    patient_id: UUID
    slot_id: UUID
    reason: str | None = Field(default=None, max_length=500)
    idempotency_key: str = Field(min_length=8, max_length=120)


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    patient_id: UUID
    slot_id: UUID
    status: str
    reason: str | None
    created_at: datetime


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: UUID | None = None
    channel: Literal["web", "phone", "api"] = "web"


class ChatResponse(BaseModel):
    conversation_id: UUID
    turn_id: str
    answer: str
    citations: list[dict[str, Any]] = []
    requires_human: bool = False
    emergency: bool = False
    latency_ms: int


class OutboundCallRequest(BaseModel):
    to_number: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    patient_id: UUID | None = None
    purpose: Literal["appointment_reminder", "follow_up", "manual"]

    @field_validator("purpose")
    @classmethod
    def accepted(cls, v: str) -> str:
        return v
