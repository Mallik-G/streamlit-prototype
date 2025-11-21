# Multi-stage Docker build for Cortex AI

# Stage 1: Base image with dependencies
FROM python:3.10-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development image
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-cov \
    pytest-mock \
    ruff \
    black \
    isort \
    mypy \
    pre-commit

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=true

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Stage 3: Production image (minimal)
FROM base as production

# Copy only necessary application files
COPY app.py .
COPY ui.py .
COPY chat.py .
COPY config.py .
COPY agent_builder.py .
COPY agent_templates.py .
COPY workflow_builder.py .
COPY styles.css .
COPY pages/ ./pages/
COPY utils/ ./utils/
COPY components/ ./components/

# Create directories for runtime data
RUN mkdir -p agents workflows vector_stores logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=false
ENV LOG_LEVEL=INFO
ENV STRUCTURED_LOGGING=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

EXPOSE 8501

# Run as non-root user
RUN useradd -m -u 1000 streamlit && \
    chown -R streamlit:streamlit /app
USER streamlit

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=true"]
