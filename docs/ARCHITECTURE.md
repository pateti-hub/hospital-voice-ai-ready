# Architecture

```text
Web text / Web microphone / Phone
                |
        FastAPI REST + WS
                |
      safety and turn control
                |
      agent response service
       /        |         \
PostgreSQL   approved RAG   tools
(state/data) (FTS/pgvector) (booking)
                |
      Cartesia Ink / Sonic
                |
 Cartesia number / Twilio / SIP
```

## Boundaries

1. **LLM is not the database.** It proposes language; deterministic services validate writes.
2. **Read and write tools are separate.** Booking requires validated IDs and an idempotency key.
3. **API first, browser second.** Playwright is a later fallback for workflows with no stable API.
4. **Retrieval is authority-aware.** Only approved hospital content should be inserted.
5. **Voice is streaming.** Audio frames, partial/final transcripts, turn IDs, and cancellation are explicit.
6. **Safety is deterministic.** Emergency and medical-advice boundaries run before generation.
7. **No PHI in telemetry.** Current logs keep IDs/event types; production redaction still requires review.

## Production-oriented flows

### Information question
User → safety classifier → PostgreSQL retrieval → grounded LLM → citations → Cartesia TTS.

### Appointment write
User intent → collect required fields → availability read → explicit confirmation → transactional booking → read-back verification → confirmation. The current REST endpoint implements the transaction; the conversational slot-filling UI is the next application-specific refinement.

### Failure recovery
- Retry only transient network/provider failures.
- Never blindly retry side effects; repeat with the same idempotency key.
- If retrieval has no approved answer, request human help.
- If a slot is taken during booking, return conflict and fetch fresh availability.
