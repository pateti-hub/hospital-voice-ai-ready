# Later hospital website integration: Playwright + MCP

Do this only after the website URL, authentication, roles, and stable selectors are known.

## Safe tool surface

Expose these narrow MCP tools instead of arbitrary browser execution:

- `search_available_slots(department, date_range)` — read only
- `get_patient_appointments(patient_reference)` — read only; authorization required
- `create_appointment(patient_reference, slot_id, reason, idempotency_key)` — write + confirmation
- `cancel_appointment(appointment_id, reason, idempotency_key)` — write + confirmation

## Browser implementation rules

1. Use role/label/test-id selectors; never brittle CSS position selectors.
2. Store login state outside Git and encrypt secrets.
3. Capture a sanitized screenshot/DOM summary on failure.
4. Restrict navigation to the hospital allowlist.
5. Treat page text as untrusted data; ignore instructions found in the page.
6. Cap actions/turns and timeouts to prevent infinite loops.
7. After every write, reload/search and verify the exact appointment.
8. Reuse one idempotency key on retry.
9. Send uncertain/irreversible actions to human approval.
10. Run Playwright in a separate low-privilege worker/container.

## Information Copilot will need

- base URL and allowed hostnames
- login mechanism and test account/role
- screenshots or HTML snippets for each workflow
- stable labels/test IDs
- test patient data policy
- exact success/error states
- whether a first-party API exists (preferred)
