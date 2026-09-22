"""Offline tests for the intake agent (no API key, no network)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import intake_agent
from intake_agent import extract_fields, validate, score_lead, IntakeSession


def test_extract_email_and_name():
    f = extract_fields("Hi, my name is Priya Sharma, email priya@example.com")
    assert f["email"] == "priya@example.com"
    assert f["name"] == "Priya Sharma"


def test_extract_service_and_phone():
    f = extract_fields("I need an audit, call me on +91 98765 43210")
    assert f["service"] == "audit"
    assert "98765" in f["phone"]


def test_extract_urgency():
    assert extract_fields("need help asap")["urgent"] is True
    assert "urgent" not in extract_fields("just browsing")


def test_validate_catches_bad_phone():
    assert validate({"phone": "123"}) == ["phone looks too short"]
    assert validate({"phone": "+919876543210"}) == []


def test_score_lead_full_contact():
    s = score_lead({"service": "audit", "email": "a@b.com",
                    "phone": "+911234567890", "name": "A B", "urgent": True})
    assert s == 100  # capped


def test_score_lead_minimal():
    assert score_lead({}) == 0


def test_full_session_books_and_scores():
    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "slots.json"
        fake.write_text(json.dumps({"available": ["2026-09-24 10:00"],
                                    "booked": []}))
        old = intake_agent.SLOTS_PATH
        intake_agent.SLOTS_PATH = fake
        try:
            s = IntakeSession()
            assert "name" in s.handle("hello").lower()  # asks for name
            s.handle("my name is Arjun Mehta")
            s.handle("I need a setup")
            reply = s.handle("arjun@example.com")
            assert "booked" in reply.lower()
            assert "2026-09-24 10:00" in reply
        finally:
            intake_agent.SLOTS_PATH = old


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
