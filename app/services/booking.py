from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Appointment, AppointmentStatus, Patient, Slot


class BookingError(Exception):
    pass


async def list_available_slots(
    session: AsyncSession, department: str | None = None, doctor: str | None = None, limit: int = 10
):
    q = (
        select(Slot)
        .join(Slot.doctor)
        .options(selectinload(Slot.doctor))
        .where(Slot.is_available.is_(True), Slot.starts_at > datetime.now().astimezone())
        .order_by(Slot.starts_at)
        .limit(min(limit, 50))
    )
    if department:
        from app.models import Department, Doctor

        q = q.join(Doctor.department).where(Department.name.ilike(f"%{department}%"))
    if doctor:
        q = q.where(Slot.doctor.has(name=doctor))
    return list((await session.scalars(q)).all())


async def book_appointment(
    session: AsyncSession, patient_id: UUID, slot_id: UUID, reason: str | None, idempotency_key: str
) -> Appointment:
    existing = await session.scalar(
        select(Appointment).where(Appointment.idempotency_key == idempotency_key)
    )
    if existing:
        return existing
    patient = await session.get(Patient, patient_id)
    if not patient:
        raise BookingError("Patient not found")
    slot = await session.scalar(select(Slot).where(Slot.id == slot_id).with_for_update())
    if not slot or not slot.is_available:
        raise BookingError("Slot is no longer available")
    slot.is_available = False
    appt = Appointment(
        patient_id=patient_id, slot_id=slot_id, reason=reason, idempotency_key=idempotency_key
    )
    session.add(appt)
    await session.commit()
    await session.refresh(appt)
    return appt


async def cancel_appointment(session: AsyncSession, appointment_id: UUID) -> Appointment:
    appt = await session.scalar(
        select(Appointment).where(Appointment.id == appointment_id).with_for_update()
    )
    if not appt:
        raise BookingError("Appointment not found")
    if appt.status == AppointmentStatus.CANCELLED:
        return appt
    appt.status = AppointmentStatus.CANCELLED
    slot = await session.get(Slot, appt.slot_id)
    slot.is_available = True
    await session.commit()
    await session.refresh(appt)
    return appt
