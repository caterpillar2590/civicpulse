#!/bin/sh
set -eu

CONFIG_PATH="/usr/share/nginx/html/config.js"

# Written on every container start, from whatever environment this specific
# container instance has - so the one built image works unmodified in dev,
# staging and prod. Leave API_BASE_URL empty to rely on the nginx /api proxy.
cat > "$CONFIG_PATH" <<EOF
window.__CONFIG__ = {
  API_BASE_URL: "${API_BASE_URL:-}"
};
EOF

exec "$@"
