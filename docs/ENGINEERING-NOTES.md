# Engineering Notes

Answers with file-and-line references, per the assignment's requirement
that generic answers score zero. Questions 1, 2, 5, and 8 require the
team's own hands-on measurement/experience and are left as templates -
everything else is answered from the actual code in this repository.

## 1. Three things that differ between your laptop and a CI runner

_(Team to fill in from your own experience running `ci.yml`. Starting
points to investigate: filesystem case-sensitivity, available CPU cores
affecting the HPA load test, pre-installed tool versions, network access
to Groq from a GitHub-hosted runner vs. your home network, Docker layer
cache cold-starts on a fresh runner. For each, name the exact line that
freezes it - e.g. the pinned Python version in `ci.yml`'s
`actions/setup-python@v5 with: python-version: "3.12"`.)_

## 2. Where your pipeline sits on the CI/CD maturity ladder

_(Team to fill in, citing Lecture 03 slide 32. Starting observation: this
pipeline has automated test, build, scan, and deploy stages gated by
`needs:` (`.github/workflows/cd.yml` lines defining `build-push:
needs: [test]` and `deploy-k8s: needs: [build-push]`), and deploys to a
real (ephemeral) cluster on every merge to `main` - argue which rung that
represents and what the next rung would add, e.g. progressive
canary/blue-green delivery, which this pipeline does not yet do.)_

## 3. The exact line guaranteeing build-once-deploy-many, and what breaks without it

`frontend/index.html` loads `<script src="/config.js"></script>` before
the built bundle, and `frontend/src/api/client.ts::apiBase()` reads
`window.__CONFIG__.API_BASE_URL` at call time rather than
`import.meta.env` at build time. `frontend/docker-entrypoint.sh`
regenerates `/config.js` from the `API_BASE_URL` environment variable on
every container start.

Without this, the backend URL would be compiled into the static JS bundle
by Vite at `docker build` time. The resulting image would only work
against whichever backend URL was set at build time - a rebuild would be
required for every environment (dev/staging/prod), which is exactly what
build-once-deploy-many forbids. See ADR 0002 for the full reasoning.

## 4. With a live LLM provider your service is probabilistic. What does "correct" mean, and how did you keep CI deterministic?

"Correct" for `TRIAGE_PROVIDER=llm` cannot mean "produces the exact same
category every time" - it means (a) the output always validates against
`TriageResult` (`app/models/schemas.py`) regardless of what the model
returns, and (b) the system's *behavior* around the model is
deterministic even when the model's *output* isn't: a timeout always
retries once then falls back (`app/services/triage_service.py::
_call_with_retry`), malformed JSON always falls back
(`app/providers/triage/llm.py`'s `json.JSONDecodeError` ->
`TriageError` -> fallback), and the fallback always succeeds
(`RuleBasedTriage` has no failure path).

CI never exercises the non-deterministic path at all:
`backend/tests/conftest.py` pins `TRIAGE_PROVIDER=simulated`, and
`SimulatedTriage` (`app/providers/triage/simulated.py`) is a pure
function of a SHA-256 hash of the input text - same input, same output,
every run, forever. Failure-path tests
(`backend/tests/test_triage_fallback.py`) inject failure deterministically
via `SIMULATED_TRIAGE_MODE=timeout|malformed`, never `time.sleep()` or a
real network call.

## 5. Your HPA lag: seconds between offered load rising and replicas rising

_(Team to fill in with a real `k6`/`hey` load test against a real cluster
and `kubectl get hpa -w` output - see `k8s/base/hpa.yaml` for the
`scaleUp.stabilizationWindowSeconds: 0` / `scaleDown.stabilizationWindowSeconds: 300`
configuration this measures against. Report: time from load starting to
CPU utilisation crossing 60%, time from that crossing to a new pod
`Running`, and time from `Running` to that pod passing its readiness
probe and actually receiving traffic - each of these three intervals
contributes to total lag, and they have different causes worth separating.)_

## 6. Why VPA is in Off mode; the Auto+HPA failure mode

`k8s/base/vpa.yaml` sets `updatePolicy.updateMode: "Off"`. Both
autoscalers would otherwise act on the same signal: the HPA
(`k8s/base/hpa.yaml`) scales replica count on CPU utilisation, computed as
usage/request. If VPA in Auto mode were also adjusting
`resources.requests.cpu` on the same Deployment, raising the request
lowers computed utilisation (same usage, bigger denominator), which
signals the HPA to scale *in*, which raises per-pod load, which signals
VPA to raise the request again - a feedback loop with no stable
equilibrium. Recommender-only mode plus a human reviewing
`kubectl describe vpa backend-vpa` and manually updating
`backend.yaml`'s `resources.requests` (per the assignment's five-step
loop in §3.3) is the industrial-standard way to get VPA's benefit without
the fight.

## 7. Your `internal: true` network blocks outbound traffic - where does that leave the LLM-calling service?

`compose.yaml`'s `internal` network (backend<->database<->cache<->ollama)
has `internal: true` and therefore no route to the outside world. The
`backend` service is deliberately **also** joined to `edge`
(`networks: [edge, internal]` in `compose.yaml`), and `edge` is a normal
(non-internal) bridge network, which has outbound internet access by
default. This is what lets `LLMTriage` (`app/providers/triage/llm.py`)
reach `api.groq.com` while `database`, `cache`, and `ollama` remain fully
unreachable from outside the internal network. The trade-off: `backend`
now sits on both networks, so it is the single bridging point between
"can reach the internet" and "can reach the data plane" - which is
also, not coincidentally, why network segmentation matters most for
exactly this service (it's the one component an attacker reaching from
outside would most want to compromise first).

## 8. The failure

_(Team to fill in - the assignment specifically wants a real failure that
cost more than an hour: symptoms, what you wrongly believed first, and
the exact command or log line that told you the truth. One candidate
already surfaced during initial setup and is documented in the commit
history / conversation log for this handoff: an Alembic migration that
manually created a Postgres enum type with `checkfirst=True` and then hit
`asyncpg.exceptions.DuplicateObjectError: type "category_enum" already
exists`, because `op.create_table()` tried to create the same
SQLAlchemy-attached enum a second time internally. The fix was
`create_type=False` on the enum objects passed to the table's columns.
If you use this as your answer, describe it in your own words with your
own timestamps - a generic retelling scores zero per the assignment's own
rule.)_
