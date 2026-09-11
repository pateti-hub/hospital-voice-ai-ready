import pytest

from app.services.agent import EMERGENCY_PATTERNS, MEDICAL_ADVICE_PATTERNS


@pytest.mark.parametrize(
    "text", ["I have chest pain", "I cannot breathe", "There is severe bleeding"]
)
def test_emergency_patterns(text):
    assert any(p in text.lower() for p in EMERGENCY_PATTERNS)


def test_medical_advice_boundary():
    assert any(p in "what medicine should i take" for p in MEDICAL_ADVICE_PATTERNS)
