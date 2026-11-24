# ==============================================================================
# Stage 1: Build & Dependency Wheel Stage
# ==============================================================================
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install compilation prerequisites if native modules require C-extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment isolated from base Python system packages
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy dependency manifest and build wheels / install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ==============================================================================
# Stage 2: Minimal Production Runtime
# ==============================================================================
FROM python:3.12-slim AS runner

# OpenContainer Initiative (OCI) Metadata Labels
LABEL org.opencontainers.image.title="LLM-Powered File System Assistant" \
      org.opencontainers.image.description="Multi-model autonomous file system and resume screening assistant with tool calling" \
      org.opencontainers.image.authors="Shubhankar Thapliyal" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/Shubhankart101/LLM-PoweredFileSystemAssistant"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME="/app"

# Install minimal runtime dependencies and security utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create dedicated non-root application user and group with deterministic IDs
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m -d /home/appuser appuser

WORKDIR ${APP_HOME}

# Copy pre-built virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Pre-create standard storage directories and assign ownership
RUN mkdir -p ${APP_HOME}/resumes ${APP_HOME}/summaries && \
    chown -R appuser:appgroup ${APP_HOME} /home/appuser

# Copy application source code with non-root ownership
COPY --chown=appuser:appgroup . ${APP_HOME}

# Switch to unprivileged non-root user
USER appuser

# Healthcheck to verify Python runtime, dependencies, and core modules
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import fs_tools; import llm_file_assistant; print('healthy')" || exit 1

# Expose HTTP server port for --serve mode (used in cloud/ECS deployments)
EXPOSE 8000

# Expose document storage volumes for external persistence
VOLUME ["/app/resumes", "/app/summaries"]

# Default entrypoint executes the assistant CLI
ENTRYPOINT ["python", "llm_file_assistant.py"]

# Default command displays usage assistance (can be overridden with queries or flags)
CMD ["--help"]
