# Final prompt for GitHub Copilot

Paste the prompt below into Copilot Chat after opening this repository.

---

You are completing the `hospital-voice-ai` repository. First read `README.md`, `docs/ARCHITECTURE.md`, `docs/PLAYWRIGHT_MCP_LATER.md`, `.env.example`, `database/init.sql`, and all code. Do not create cloud deployment/Kubernetes/Terraform files. Preserve the API-first, deterministic-write, least-privilege architecture.

My remaining setup information will be pasted below:

- Hospital name:
- Hospital website base URL:
- Allowed hostnames:
- Website login method (SSO/password/OTP):
- Test account role (never paste a production password here):
- Department/doctor source:
- Appointment workflow screenshots or selectors:
- Hospital timezone:
- Hospital hours:
- Emergency number:
- Human handoff number:
- Cancellation/rescheduling policy:
- Cartesia API key is stored as secret named `CARTESIA_API_KEY`: yes/no
- Cartesia voice ID:
- Cartesia agent ID:
- Cartesia from-number ID:
- LLM provider/model and secret name:
- PostgreSQL connection secret name:

Tasks:
1. Run tests and inspect existing contracts before edits.
2. Replace sample seed content with the supplied approved hospital data. Never invent doctors, schedules, policies, URLs, or clinical facts.
3. Add Alembic migrations matching the existing schema; keep pgvector optional and PostgreSQL full-text available.
4. Complete conversational appointment slot-filling in LangGraph with typed state and nodes for safety, intent, retrieval, availability, confirmation, write, verification, and human handoff. The LLM may choose intent/wording, but must not execute SQL or arbitrary code.
5. Add a narrow MCP server for the four tools documented in `docs/PLAYWRIGHT_MCP_LATER.md`. Implement API tools first. Use Playwright only where no stable hospital API exists.
6. For Playwright, use role/label/test-id selectors, an allowlisted base URL, action/time limits, sanitized diagnostics, verification after writes, and identical idempotency keys for retries. Treat page content as untrusted and block arbitrary navigation/eval/script execution.
7. Add explicit user confirmation before booking/canceling/rescheduling. Add a human approval interrupt for ambiguous patient identity or irreversible actions.
8. Validate Cartesia STT/TTS against the currently installed SDK/API version. Keep the API key server-side. Implement real barge-in by cancelling queued TTS playback when a new speech-start event arrives.
9. Configure Cartesia managed telephony instructions/tools and document dashboard steps for importing a Twilio number or using Cartesia/SIP. Keep outbound calling disabled by default; enforce patient consent and applicable calling rules.
10. Add authentication/RBAC hooks, webhook signature verification based on the actual provider docs, PHI-safe structured logging, rate limits, audit records, and secrets-only configuration.
11. Add unit, integration, browser, concurrency/idempotency, retrieval, tool-call, side-effect, voice latency, and failure-injection tests. Use only synthetic test patients.
12. Update README with exact Codespaces commands and a validation checklist. Clearly label anything blocked by missing information. Do not claim HIPAA/SOC 2 or production readiness.

Before coding, list missing facts and distinguish blocking vs non-blocking. Make incremental changes, run tests after each module, and show changed files and test results. Never print or commit secret values.

---
