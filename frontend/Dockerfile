# syntax=docker/dockerfile:1

FROM node:20-alpine AS builder

WORKDIR /build

COPY package*.json ./
RUN npm ci --omit=dev

FROM node:20-alpine AS runtime

RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -s /bin/sh -D appuser

WORKDIR /app

COPY --from=builder /build/node_modules ./node_modules
COPY --chown=appuser:appgroup app.js package.json ./
COPY --chown=appuser:appgroup views/ ./views/

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/health', r => process.exit(r.statusCode === 200 ? 0 : 1)).on('error', () => process.exit(1))"

CMD ["node", "app.js"]
