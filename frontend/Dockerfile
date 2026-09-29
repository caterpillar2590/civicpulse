# syntax=docker/dockerfile:1
FROM node:22-alpine AS builder
WORKDIR /build

COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime

RUN addgroup -S civicpulse && adduser -S civicpulse -G civicpulse \
    && rm -rf /usr/share/nginx/html/* \
    && rm /etc/nginx/conf.d/default.conf

COPY --from=builder /build/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.d/40-config.sh

RUN chmod +x /docker-entrypoint.d/40-config.sh \
    && chown -R civicpulse:civicpulse /usr/share/nginx/html /var/cache/nginx /var/run \
    && touch /var/run/nginx.pid \
    && chown civicpulse:civicpulse /var/run/nginx.pid \
    && sed -i 's/^user  nginx;//' /etc/nginx/nginx.conf

USER civicpulse
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://localhost:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
