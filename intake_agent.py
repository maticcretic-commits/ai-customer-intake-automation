#!/usr/bin/env python3
"""
AI Customer Intake Automation — portfolio practice project.

Starter for the "AI chatbot + customer intake automation" gig pattern:
agencies white-label this as a flat-fee build (chatbot, lead capture,
booking assistant) for professional-service firms.

Pipeline:
  1. Chat turns -> extract fields (name, service, preferred time) with
     simple robust parsing (swap in an LLM extractor later).
  2. Validate fields (phone/email formats, known services, future dates).
  3. Score the lead (service value + contact completeness + urgency words).
  4. Book the earliest matching slot from data/slots.json.
  5. Push the qualified lead to a CRM webhook (CRM_WEBHOOK_URL or dry-run).

Usage:
    python intake_agent.py --demo            # runs a scripted conversation
    python intake_agent.py --chat            # interactive chat in terminal
    python tests/test_intake.py
"""

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
SLOTS_PATH = BASE / "data" / "slots.json"

SERVICES = {
    "consultation": 30,
    "audit": 50,
    "setup": 40,
    "support": 20,
}

# TODO(learn): replace the regex extractor with an LLM function-calling
# extractor and compare field accuracy on 20 sample messages.


def extract_fields(text):
    """Pull structured fields out of free text. Returns dict of found fields."""
    fields = {}
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text)
    if email:
        fields["email"] = email.group(0)
    phone = re.search(r"\+?\d[\d\s-]{7,}\d", text)
    if phone:
        fields["phone"] = re.sub(r"[\s-]", "", phone.group(0))
    name = re.search(r"(?:my name is|i'm|i am|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
                     text, re.IGNORECASE)
    if name:
        fields["name"] = name.group(1).strip().title()
    for service in SERVICES:
        if service in text.lower():
            fields["service"] = service
            break
    urgent = any(w in text.lower() for w in ("urgent", "asap", "immediately", "today"))
    if urgent:
        fields["urgent"] = True
    return fields


def validate(fields):
    errors = []
    if "email" in fields and not re.fullmatch(r"[\w.+-]+@[\w-]+\.[\w.]+", fields["email"]):
        errors.append("email looks invalid")
    if "phone" in fields and len(re.sub(r"\D", "", fields["phone"])) < 8:
        errors.append("phone looks too short")
    return errors


def score_lead(fields):
    """0-100. Service value + contact completeness + urgency."""
    score = 0
    if fields.get("service"):
        score += SERVICES[fields["service"]]
    if fields.get("email"):
        score += 15
    if fields.get("phone"):
        score += 15
    if fields.get("name"):
        score += 10
    if fields.get("urgent"):
        score += 10
    return min(score, 100)


def book_earliest_slot(service):
    slots = json.loads(SLOTS_PATH.read_text())
    available = slots.get("available", [])
    if not available:
        return None
    slot = available.pop(0)
    slots["available"] = available
    slots.setdefault("booked", []).append({"slot": slot, "service": service})
    SLOTS_PATH.write_text(json.dumps(slots, indent=2))
    return slot


def push_to_crm(lead):
    """POST the qualified lead to the CRM webhook. Dry-run if unset."""
    url = os.environ.get("CRM_WEBHOOK_URL")
    payload = json.dumps({"event": "new_qualified_lead", **lead}).encode()
    if not url:
        print("[dry-run] would POST to CRM webhook:", payload.decode())
        return {"dry_run": True}
    req = urllib.request.Request(url, data=payload,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return {"status": resp.status, "dry_run": False}


class IntakeSession:
    def __init__(self):
        self.fields = {}

    def handle(self, text):
        self.fields.update(extract_fields(text))
        errors = validate(self.fields)
        missing = [f for f in ("name", "service", "email")
                   if f not in self.fields]
        if errors:
            return "I couldn't quite read that: " + "; ".join(errors) + ". Could you repeat it?"
        if missing:
            prompts = {"name": "your name", "service": "which service you need (consultation, audit, setup, support)",
                       "email": "your email"}
            return f"Thanks! Could you share {prompts[missing[0]]}?"
        score = score_lead(self.fields)
        slot = book_earliest_slot(self.fields["service"])
        lead = {**self.fields, "score": score, "slot": slot,
                "at": datetime.utcnow().isoformat()}
        push_to_crm(lead)
        if slot:
            return (f"You're booked for {self.fields['service']} on {slot}. "
                    f"Confirmation sent to {self.fields['email']}. (lead score: {score}/100)")
        return ("Got it — our team will call you to schedule. "
                f"(lead score: {score}/100)")


def run_demo():
    session = IntakeSession()
    for msg in ["Hi, my name is Priya Sharma",
                "I need a consultation",
                "my email is priya@example.com, it's urgent"]:
        print("Visitor:", msg)
        print("Agent:", session.handle(msg))


def run_chat():
    session = IntakeSession()
    print("Intake agent. Type 'quit' to exit.")
    while True:
        try:
            text = input("You: ")
        except EOFError:
            break
        if text.strip().lower() == "quit":
            break
        print("Agent:", session.handle(text))


def main():
    p = argparse.ArgumentParser(description="AI customer intake agent")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo", action="store_true")
    g.add_argument("--chat", action="store_true")
    args = p.parse_args()
    (run_demo if args.demo else run_chat)()


if __name__ == "__main__":
    main()
