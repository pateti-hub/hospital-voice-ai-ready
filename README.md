# Hospital Voice AI Assistant

A runnable, production-minded **development application** for hospital information and appointment workflows. It implements the project discussed in the supplied conversation, except cloud/production deployment. The current hospital website is deliberately not automated yet; a safe Playwright/MCP adapter is reserved for the later integration phase.

## Included

- FastAPI REST API, WebSocket voice gateway, OpenAPI docs
- PostgreSQL + pgvector schema, sample departments/doctors/slots/policies
- Idempotent appointment booking with row locking and cancellation
- Retrieval from an approved hospital knowledge base (PostgreSQL full-text; pgvector-ready)
- OpenAI-compatible LLM response generation with deterministic fallback
- Cartesia Ink 2 streaming STT and Sonic 3.6 streaming TTS
- Cartesia Managed Agents outbound telephony endpoint, patient consent gate, webhooks
- Emergency/medical-advice guardrails and human-handoff signaling
- Structured request IDs, JSON logs, Prometheus metrics, evaluation tests
- Small browser UI for text and microphone conversations
- Codespaces/devcontainer and local PostgreSQL setup

> **Important:** This is a portfolio/development system, not a certified clinical system. Do not claim HIPAA, SOC 2, clinical safety, or production readiness without legal, security, privacy, and clinical review.

## 1. Run in GitHub Codespaces

1. Upload this folder to a GitHub repository.
2. Open **Code → Codespaces → Create codespace**.
3. If the container does not initialize automatically, run:

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
docker compose up -d db
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open forwarded port 8000. API documentation is at `/docs`.

## 2. Add secrets

Put values in `.env` locally or Codespaces repository secrets. Never add real keys to Git.

Required for voice:
- `CARTESIA_API_KEY`: create in the Cartesia dashboard.
- `CARTESIA_VOICE_ID`: choose a voice ID; the example is only a public sample.

Required for generative answers:
- `OPENAI_API_KEY` and optionally `OPENAI_MODEL` / `OPENAI_BASE_URL`.

Required for managed telephony:
- `CARTESIA_AGENT_ID`
- `CARTESIA_FROM_NUMBER_ID`
- `ALLOW_OUTBOUND_CALLS=true` only after consent/compliance checks.

The server, not browser JavaScript, holds API keys.

## 3. Database data to replace

Edit `database/seed.sql` before first database creation, or use SQL/admin endpoints later. Replace:
- hospital hours and emergency number
- departments and doctor names
- real slot source (do not generate slots in production)
- appointment/cancellation policies
- approved source URLs and policy authority

Reset local sample data:

```bash
docker compose down -v
docker compose up -d db
```

## 4. Try the API

```bash
curl http://localhost:8000/api/v1/health
curl 'http://localhost:8000/api/v1/slots?department=Cardiology'
curl -X POST http://localhost:8000/api/v1/chat -H 'content-type: application/json'   -d '{"message":"What are the outpatient hours?","channel":"api"}'
```

Create a patient, copy patient/slot IDs, then book with a unique idempotency key:

```bash
curl -X POST http://localhost:8000/api/v1/patients -H 'content-type: application/json'   -d '{"full_name":"Demo Patient","phone":"+919876543210","consent_to_call":false}'
```

## 5. Voice protocol

Browser → `/api/v1/voice`:
- binary: mono PCM signed 16-bit little-endian at 16 kHz
- JSON `{"type":"end_turn"}`: finalize STT for one turn
- JSON `{"type":"close"}`: end session

Server → browser:
- JSON transcript/assistant/control events
- binary: PCM signed 16-bit little-endian at configured TTS sample rate (24 kHz default)

The UI uses echo cancellation/noise suppression and manual endpointing. Cartesia provides streaming STT/TTS; production barge-in needs cancellation IDs and more robust browser AudioWorklet buffering.

## 6. Telephony

Recommended path: create a Cartesia Managed Agent, configure its LLM/system prompt and approved tools, then attach a Cartesia number, imported Twilio number, or SIP trunk. Point agent tools at narrowly scoped endpoints in this API. Outbound calls use `POST /api/v1/telephony/outbound` and are disabled by default.

Do not place reminder/follow-up calls without documented consent and applicable telecom compliance. Add webhook signature verification once Cartesia supplies the signing configuration for your account.

## 7. Later Playwright + MCP integration

Follow `docs/PLAYWRIGHT_MCP_LATER.md` after the hospital website is stable. The correct order is API-first, browser-second. Do not give an LLM arbitrary Playwright code execution. Expose fixed, validated actions and verify every write by reading the resulting page.

## 8. Tests

```bash
pytest -q
ruff check .
python scripts/check.py
```

## Known boundaries before real use

- Authentication/RBAC is not yet connected to your hospital identity provider.
- PostgreSQL full-text retrieval works now; embedding ingestion is intentionally left configurable because an embedding provider/model was not specified.
- Browser automation is deferred until the website DOM and login flow exist.
- Telephony provisioning/agent creation happens in Cartesia; this repository uses configured IDs.
- Clinical, privacy, security, load, accessibility, and disaster-recovery reviews are still required.
- No production/cloud deployment files are included.
