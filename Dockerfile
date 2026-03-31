# ==================== Stage 1: Builder ====================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install system dependencies for mysqlclient compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first (better layer caching)
COPY pyproject.toml .
COPY labelu/version.py labelu/version.py
COPY labelu/__init__.py labelu/__init__.py
COPY README.md .

# Install Python dependencies
RUN pip install --no-cache-dir --prefix=/install ".[mysql]"

# ==================== Stage 2: Runtime ====================
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for mysqlclient
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r labelu && useradd -r -g labelu -m labelu

# Copy application source code
COPY --chown=labelu:labelu . .

# Install the app itself (editable-like, using the already-installed deps)
RUN pip install --no-cache-dir --no-deps .

# Set data directory via XDG_DATA_HOME so appdirs uses /data/labelu
ENV XDG_DATA_HOME=/data

RUN mkdir -p /data/labelu/media && \
    chown -R labelu:labelu /data && \
    chmod -R u+rwX /data

# Switch to non-root user
# USER labelu

EXPOSE 8000

CMD ["uvicorn", "labelu.main:app", "--host", "0.0.0.0", "--port", "8000"]

