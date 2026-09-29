# ADR 0004: PII and data governance in the triage pipeline

## Status
Accepted

## Context
Citizen complaints routinely contain names, phone numbers, and precise
addresses (`reporter_contact` is a free-text field by design; `text` and
`location` are not sanitized before triage). When `TRIAGE_PROVIDER=llm`,
this content is sent to a third-party hosted model (Groq). Some free-tier
providers (notably Google AI Studio / Gemini, an alternative documented in
the assignment) may use free-tier inputs to improve their models. Groq's
published terms for its free developer tier do not claim this, but the
underlying question - what leaves the machine, to whom, and under what
terms - applies to any hosted provider and needs an explicit answer, not
an assumption.

## Decision
We accept and document the exposure, scoped as narrowly as we can, rather
than attempting redaction:

1. **Only `text` and `location` are sent to the provider**
   (`app/providers/triage/llm.py::triage`) - `reporter_contact` is never
   included in the prompt sent to Groq or Ollama. It is stored, but only
   used for the operator to follow up with the citizen, never for triage.
2. **`TRIAGE_PROVIDER=ollama` is offered as a zero-exposure alternative**
   for any deployment where this trade-off is unacceptable: complaint text
   never leaves the machine, at the cost of slower and less accurate
   classification (the buy-vs-host trade-off, ours to make per deployment).
3. **We do not attempt automated PII redaction on `text` before sending
   it to `llm`**, because a naive redaction pass (regex for phone numbers,
   names) is unreliable, would degrade triage quality on exactly the
   complaints where a name or number matters for classification (e.g. "call
   me at ... it's urgent"), and would give a false sense of protection.
4. **The Redis triage cache is content-hash-keyed and TTL-bound** (24h,
   `app/providers/cache.py`), which limits how long a text blob's derived
   cache entry persists on our own infrastructure, though the *provider's*
   retention policy is outside our control regardless.

## Consequences
- A production deployment with `TRIAGE_PROVIDER=llm` is knowingly sending
  citizen-submitted free text (potentially including names or numbers a
  citizen chose to include) to Groq's API. This is disclosed here, not
  hidden.
- Anyone deploying this system for a real municipality should re-evaluate
  this decision against their own jurisdiction's data protection
  requirements before choosing `llm` over `ollama` in production - this
  ADR documents our default, not a universal answer.
- If requirements tighten, the fix is a one-line environment variable
  change (`TRIAGE_PROVIDER=ollama`), because of the abstraction described
  in ADR 0001 - the governance decision and the code decision are
  deliberately decoupled.
