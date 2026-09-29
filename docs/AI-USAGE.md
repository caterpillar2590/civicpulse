# AI Usage Disclosure

Per course policy: specific disclosure carries no penalty. This document
should be edited by the team to reflect what actually happened - the
template below reflects the state of the repository as handed off by an AI
assistant (Claude) and needs the team's own additions once you extend it.

## What the AI wrote (starting point, to be extended/reviewed by the team)

- Backend: full FastAPI application (`backend/app/`) - four-layer
  architecture, all ten endpoints, the four `TriageProvider`
  implementations, the state machine, Redis cache/rate-limiter, structured
  logging, SIGTERM handling.
- Frontend: React/Vite/TS application (`frontend/src/`) - Submit,
  Dashboard, Stats views, typed API client, error boundary, runtime config.
- Data layer: the Alembic migration and idempotent seed script.
- Docker: both multi-stage Dockerfiles, `compose.yaml`, `compose.prod.yaml`.
- Kubernetes: all manifests under `k8s/`, both Kustomize overlays.
- CI/CD: `ci.yml`, `cd.yml`, `release.yml`.
- Tests: the backend pytest suite (11 tests) and frontend Vitest suite
  (8 tests), including the fallback test and the injection-guardrail test
  named explicitly in the assignment.
- This document, the RUNBOOK, and the four ADRs (drafts - see note below).

## What was actually verified by running it (not just generated)

- Backend: installed into a real virtualenv, run against a real local
  Postgres 16 and Redis 7 (not mocks), with the full pytest suite passing
  (11/11, 82% coverage) and a live `curl` walkthrough of every endpoint.
  Two real bugs were found and fixed this way: a `setuptools` package
  discovery failure, a missing `greenlet` dependency, a `pool_size` kwarg
  incompatible with SQLite, a Postgres-only `char_length()` in a CHECK
  constraint, an event-loop-scoping bug in the Redis test fixture, and an
  Alembic migration that tried to create the same Postgres enum type
  twice.
- Frontend: `npm install`, `npm run build`, and `npm test` all run for
  real; 8/8 tests passing.
- `compose.yaml` / `compose.prod.yaml`: validated with a real
  `docker compose config` (schema + variable interpolation), and
  programmatically confirmed the database/cache have zero published ports
  in prod. NOT verified end-to-end with a real `docker compose up`,
  because the sandbox used to build this could not reach Docker Hub.
- `k8s/`: rendered with a real `kustomize build` and schema-validated with
  a real `kubeconform -strict`, for both overlays. NOT applied to a real
  cluster, deployed, or load-tested - the sandbox had no cluster to test
  against.

## What still needs a human

- Running `docker compose up` and Kubernetes deployment end-to-end on a
  real machine/cluster.
- Testing `TRIAGE_PROVIDER=llm` against a real Groq API key, and reporting
  a measured triage-cache hit rate (F layer, §5.2 Q4).
- Everything in §5.2's eight engineering-notes questions that requires
  first-hand measurement (HPA lag, the "one failure that cost an hour",
  etc.) - `docs/ENGINEERING-NOTES.md` is a template with placeholders, not
  a filled-in answer.
- The four ADRs in `docs/adr/` are genuine engineering decisions with
  real trade-offs recorded, but the team should review and adjust them to
  reflect any changes made after this handoff, and should treat them as a
  starting draft rather than a final, unreviewed submission.
- The entire collaboration workflow (§Rubric A): actual PRs, actual
  review comments from a partner, an actual merge conflict, actual commit
  history - none of this can be generated after the fact.
- The demo video and the viva.

## Team's own additions

_(Fill in here: what you personally changed, extended, or wrote from
scratch after this starting point, and why.)_
