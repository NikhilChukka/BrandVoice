# ---------- builder ----------
FROM python:3.11-slim AS builder
WORKDIR /backend

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt && \
    apt-get purge -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# ---------- final ----------
FROM python:3.11-slim
WORKDIR /backend

# copy site-packages from builder layer
COPY --from=builder /install /usr/local

# copy source
COPY . .

# curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

ENV PORT=8080 HOST=0.0.0.0 PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
