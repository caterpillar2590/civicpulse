# ADR 0002: Frontend runtime configuration via /config.js + nginx proxy

## Status
Accepted

## Context
A Vite build bakes `import.meta.env` values into static JavaScript at
build time. If the backend API URL were baked in this way, the resulting
image would be environment-specific, breaking build-once-deploy-many for
the frontend: the same image couldn't run unmodified in dev, staging and
prod.

## Decision
We do both of the two options the assignment allows, deliberately
redundant:

1. **nginx reverse proxy** (`frontend/nginx.conf`): requests to `/api/*`
   are proxied to `http://backend:8000/api/*` inside the container network.
   In this mode the frontend never needs to know an absolute backend URL
   at all - relative fetches to `/api/...` just work.
2. **Runtime-generated `/config.js`** (`frontend/docker-entrypoint.sh`,
   wired in as an nginx `/docker-entrypoint.d/` script): on every container
   start, `window.__CONFIG__.API_BASE_URL` is (re)written from the
   `API_BASE_URL` environment variable. `index.html` loads this script
   *before* the built bundle, so `src/api/client.ts` reads it at call time,
   not at build time.

`API_BASE_URL` is left empty by default, which makes the frontend rely on
option 1. Option 2 exists for the case where the frontend and backend are
not behind the same reverse proxy (e.g. different Ingress hosts).

## Consequences
- One built frontend image (`frontend/Dockerfile`) runs unmodified across
  every environment in `compose.yaml`, `compose.prod.yaml`, and both
  Kubernetes overlays.
- `/config.js` is served with `Cache-Control: no-store` (see
  `nginx.conf`) so a redeploy with a changed `API_BASE_URL` takes effect
  immediately, without a stale browser cache masking it.
- No secret or environment-specific value ever appears in the JS bundle
  itself - anything in a browser bundle is public, "it's minified" is not
  a defence.
