from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import AppointmentCreate, PatientCreate


def test_e164_phone():
    assert PatientCreate(full_name="Test User", phone="+919876543210").phone.startswith("+")


def test_short_idempotency_rejected():
    with pytest.raises(ValidationError):
        AppointmentCreate(patient_id=uuid4(), slot_id=uuid4(), idempotency_key="short")
