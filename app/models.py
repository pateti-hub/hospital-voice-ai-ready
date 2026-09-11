from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AppointmentStatus(StrEnum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)


class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    department_id: Mapped[UUID] = mapped_column(ForeignKey("departments.id"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    department: Mapped[Department] = relationship()


class Slot(Base):
    __tablename__ = "slots"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    doctor_id: Mapped[UUID] = mapped_column(ForeignKey("doctors.id"), index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    doctor: Mapped[Doctor] = relationship()


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    consent_to_call: Mapped[bool] = mapped_column(Boolean, default=False)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_appointment_idempotency"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(ForeignKey("patients.id"), index=True)
    slot_id: Mapped[UUID] = mapped_column(ForeignKey("slots.id"), unique=True, index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default=AppointmentStatus.BOOKED)
    idempotency_key: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    slot: Mapped[Slot] = relationship()
    patient: Mapped[Patient] = relationship()


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    channel: Mapped[str] = mapped_column(String(30), default="web")
    external_call_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    state: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    turn_id: Mapped[str] = mapped_column(String(80), index=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(240))
    content: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    authority: Mapped[int] = mapped_column(Integer, default=1)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
