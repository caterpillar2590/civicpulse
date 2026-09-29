# ADR 0003: Deploy by immutable commit SHA, never `:latest`

## Status
Accepted

## Context
`:latest` is a mutable pointer, not a version. If a Deployment references
`:latest`, "what is production running?" has no fixed answer - it depends
on whatever was most recently pushed, which may not even correspond to a
commit that passed CI (a base image `docker pull` could resolve to a
different digest days apart, too). This makes rollback, incident response,
and the viva question "show me exactly what's deployed" impossible to
answer with confidence.

## Decision
`cd.yml` builds and pushes every image tagged with **both** `${{ github.sha }}`
and `latest` (the `latest` tag is still published for convenience/browsing,
per the assignment's explicit allowance - "`:latest` may be pushed; it may
never be deployed"). The `deploy-k8s` job then runs
`kustomize edit set image ...=ghcr.io/OWNER/civicpulse-backend:${{ github.sha }}`
against `k8s/overlays/prod` **before** `kubectl apply -k`, so the manifest
that actually reaches the cluster always pins the exact commit SHA. The
same pattern is intended for `compose.prod.yaml`, via `${IMAGE_TAG}` set to
a SHA at deploy time - never left at its `latest` default outside local
testing.

## Consequences
- `kubectl -n civicpulse get deployment backend -o jsonpath='{.spec.template.spec.containers[0].image}'`
  or `git show` on the SHA gives a one-word, unambiguous answer to "what is
  production running?"
- Rollback is `kubectl rollout undo` (fast, imperative) or re-applying the
  previous overlay with the previous SHA (declarative, auditable) - both
  documented in `docs/RUNBOOK.md`. Neither is possible if the running image
  is a moving target.
- The bonus path (digest-pinning with Cosign) is a strict tightening of
  this same decision: a tag can, in principle, be repointed at the
  registry; a digest cannot.
