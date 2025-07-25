# Study4Me Backend Dockerfile
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create application directory
WORKDIR /app

# Create directories for persistent data with proper permissions
RUN mkdir -p /app/data/rag_storage \
    /app/data/uploaded_docs \
    /app/logs \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create .env file with default values (override with volume mount or env vars)
RUN echo "# Docker default configuration" > /app/.env && \
    echo "RAG_DIR=/app/data/rag_storage" >> /app/.env && \
    echo "UPLOAD_DIR=/app/data/uploaded_docs" >> /app/.env && \
    echo "DB_PATH=/app/data/rag_tasks.db" >> /app/.env && \
    echo "GRAPHML_FILENAME=graph_chunk_entity_relation.graphml" >> /app/.env && \
    chown appuser:appuser /app/.env

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/readyz || exit 1

# Expose port
EXPOSE 8000

# Volume mount points for persistent data
VOLUME ["/app/data"]

# Default command with production-ready settings
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--log-level", "info", \
     "--access-log", \
     "--loop", "uvloop"]