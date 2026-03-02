# ── Stage 1: dependency builder ───────────────────────────────────────────────
# Use slim to keep image small. Pin Python version for reproducibility.
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system deps needed to compile some wheels (faiss, asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install with CPU-only torch index to save ~500MB vs default CUDA wheel
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt \
    --prefix=/install


# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system deps only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Pre-cache the embedding model in the image for Cloud Run cold starts.
ENV HF_HOME=/app/hf_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy application source
COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Gunicorn with Uvicorn workers.
# 1 worker on Render free tier (512MB RAM — model takes ~200MB).
CMD ["sh", "-c", "gunicorn main:app \\\n    --worker-class uvicorn.workers.UvicornWorker \\\n    --workers 1 \\\n    --bind 0.0.0.0:${PORT:-8000} \\\n    --timeout 180 \\\n    --keep-alive 5 \\\n    --access-logfile -"]
