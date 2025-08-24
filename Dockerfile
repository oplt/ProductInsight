# Multi-stage Dockerfile for ProductInsights

# Base stage with common dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --create-home appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements/base.txt requirements/base.txt
RUN pip install --no-cache-dir -r requirements/base.txt

# Development stage
FROM base as development

# Install development dependencies
COPY requirements/dev.txt requirements/dev.txt
RUN pip install --no-cache-dir -r requirements/dev.txt

# Copy source code
COPY . .

# Change ownership to app user
RUN chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 5000

# Development command
CMD ["python", "run.py"]

# Production stage
FROM base as production

# Install production dependencies
COPY requirements/prod.txt requirements/prod.txt
RUN pip install --no-cache-dir -r requirements/prod.txt

# Install gunicorn for production
RUN pip install gunicorn

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p logs uploads && \
    chown -R appuser:appuser /app

# Switch to app user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "wsgi:app"]

# Worker stage for background tasks
FROM production as worker

# Worker command
CMD ["celery", "-A", "app.worker", "worker", "--loglevel=info"]

# Scheduler stage for periodic tasks
FROM production as scheduler

# Scheduler command
CMD ["celery", "-A", "app.worker", "beat", "--loglevel=info"]
