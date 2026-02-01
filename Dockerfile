# ==============================================================================
# Stage 1: Frontend Builder
# ==============================================================================
FROM oven/bun:1.3.8-alpine AS frontend-builder

WORKDIR /build

# Copy package files (Bun uses bun.lock instead of package-lock.json)
COPY frontend/package.json frontend/bun.lock ./

# Install dependencies
# --frozen-lockfile: Ensures reproducible builds (like npm ci)
RUN bun install --frozen-lockfile

# Copy frontend source
COPY frontend/ ./

# Build production bundle
# Bun runs Vite, which produces identical output to Node.js version
RUN bun run build

# Verify build output exists (fail fast if build failed)
RUN test -d dist && test -f dist/index.html

# ==============================================================================
# ROLLBACK OPTION: Uncomment below to revert to Node.js 24
# ==============================================================================
# FROM node:24-alpine AS frontend-builder
# WORKDIR /build
# COPY frontend/package*.json ./
# RUN npm ci --ignore-scripts
# COPY frontend/ ./
# RUN npm run build
# ==============================================================================

# ==============================================================================
# Stage 2: Backend Builder
# ==============================================================================
FROM python:3.14-slim AS backend-builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/pyproject.toml ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the package and dependencies
COPY backend/ ./
RUN pip install --no-cache-dir .

# ==============================================================================
# Stage 3: Production
# ==============================================================================
FROM python:3.14-slim AS production

# HTTP server metadata
LABEL http.server.name="granian"
LABEL http.server.version="2.6.1"
LABEL http.server.type="asgi"
LABEL org.opencontainers.image.frontend.builder="bun-1.3.5"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy backend code
COPY --from=backend-builder /build/app /app/app

# Copy frontend build
COPY --from=frontend-builder /build/dist /app/static

# Create data directory
RUN mkdir -p /data && chown -R appuser:appuser /data /app

# Switch to non-root user
USER appuser

# Environment variables
ENV DATABASE_PATH=/data/familycircle.db
ENV PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Run with Granian
CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "app.main:app"]
