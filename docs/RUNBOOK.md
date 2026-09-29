# RUNBOOK

## Deploying

**Local (Compose):**
```bash
cp .env.example .env   # fill in GROQ_API_KEY if using TRIAGE_PROVIDER=llm
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python scripts/seed.py
```

**Kubernetes (local cluster):**
```bash
kind create cluster --name civicpulse   # or k3d cluster create civicpulse
kubectl apply -k k8s/overlays/dev
kubectl -n civicpulse rollout status deployment/backend
kubectl -n civicpulse exec deploy/backend -- alembic upgrade head
kubectl -n civicpulse exec deploy/backend -- python scripts/seed.py
```

**Production deploy** happens automatically via `cd.yml` on every push to
`main`: test -> build+push to GHCR tagged by commit SHA -> apply
`k8s/overlays/prod` with that SHA. See ADR 0003.

## Rolling back

**Fast, imperative (the 3 a.m. answer)** - reverts to the previous
ReplicaSet immediately, whatever image it happened to be running:
```bash
kubectl -n civicpulse rollout undo deployment/backend
kubectl -n civicpulse rollout undo deployment/frontend
```

**Declarative, auditable (the correct answer once the fire is out)** -
re-apply the specific previous commit's manifests, so the rollback is a
recorded, reviewable git action rather than an implicit "go back one":
```bash
git log --oneline -- k8s/overlays/prod
kustomize edit set image ghcr.io/OWNER/civicpulse-backend=ghcr.io/OWNER/civicpulse-backend:<previous-sha>
kubectl apply -k k8s/overlays/prod
```

Use the fast path first to stop the bleeding; follow up with the
declarative path so the git history reflects what's actually running.

## Reading logs

All services log structured JSON to stdout (never to a file - container
filesystems are ephemeral). Every line carries `request_id`, propagated
from the `X-Request-ID` header (generated if absent).

```bash
# Compose
docker compose logs -f backend

# Kubernetes
kubectl -n civicpulse logs -f deploy/backend
kubectl -n civicpulse logs -f deploy/backend --previous   # after a restart
```

To trace one request end to end, grep for its `request_id` (returned in
the `X-Request-ID` response header on every call):
```bash
kubectl -n civicpulse logs deploy/backend | grep '"request_id": "the-id-here"'
```

## When triage starts failing

1. Check `GET /api/meta/providers` - shows the active provider and the
   last 20 outcomes (provider, latency, whether it fell back).
2. If `triaged_by` is consistently `rules:fallback`, the active provider
   (Groq/Ollama) is down, rate-limited, or misconfigured. The system is
   still serving 201s correctly - this is the fallback working as
   designed, not an outage of CivicPulse itself.
3. Check the WARNING-level log lines (`triage fallback`) for the
   `error_class` field - distinguishes a timeout from a malformed-output
   rejection from a transport error.
4. If it's a Groq rate limit: confirm current limits at
   console.groq.com (they change) and consider switching
   `TRIAGE_PROVIDER=rules` or `=ollama` temporarily via ConfigMap/`.env`
   while the primary provider recovers - no code change needed (ADR 0001).
5. `/metrics` exposes `triage_fallback_total` and `triage_latency_seconds`
   for a Prometheus-based alert on sustained fallback rate.

## Health check reference

- `GET /health` - liveness. Never touches the database. A failing check
  here means Kubernetes restarts the pod.
- `GET /ready` - readiness. Checks Postgres and Redis. A failing check
  here means Kubernetes removes the pod from the Service, but does *not*
  restart it.
