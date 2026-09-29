# ADR 0001: TriageProvider as a Protocol, selected by environment variable

## Status
Accepted

## Context
Complaint triage is done by something we don't fully control: a hosted LLM
(Groq), an offline LLM (Ollama), or a keyword fallback. The reader must be
replaceable - today a rule, tomorrow a model, next year a fine-tuned
classifier - without the rest of the system caring which.

## Decision
Define `TriageProvider` as a `typing.Protocol` with a single method,
`async def triage(text, location) -> TriageResult`, where `TriageResult` is
a Pydantic model shared with the HTTP layer (`app/models/schemas.py`).
Four implementations exist (`llm`, `ollama`, `rules`, `simulated`), selected
at process start by the `TRIAGE_PROVIDER` environment variable via
`app/providers/triage/factory.py::get_active_provider()`. Orchestration
(timeout, retry, fallback, caching) lives one layer up in
`app/services/triage_service.py`, outside any individual provider, so every
provider gets the same safety net for free.

## Consequences
- Swapping providers is a one-line env var change, no code change.
- Every provider must satisfy the same Pydantic schema, so "the model
  returned something weird" is caught at the boundary (`app/providers/triage/llm.py`,
  `TriageResult.model_validate`) rather than propagating into the database.
- `SimulatedTriage` (`app/providers/triage/simulated.py`) gives CI a
  deterministic, network-free provider with configurable failure injection
  (`SIMULATED_TRIAGE_MODE=timeout|malformed|http_error`), which is what lets
  `TRIAGE_PROVIDER=llm`'s non-determinism stay out of the test suite
  entirely (`backend/tests/test_triage_fallback.py`).
