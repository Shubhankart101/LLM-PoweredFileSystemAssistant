# 🚢 Deployment & Operations Guide

This guide provides step-by-step operational instructions for deploying the **LLM-Powered File System Assistant** across local workstations, containerized environments, staging clusters, and production cloud infrastructure.

---

## 1. Environment Variable Configuration Matrix

Configure the application using the following environment variables (defined in `.env` locally or injected via AWS Secrets Manager / Kubernetes Secrets in production):

| Variable | Required | Default | Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | Conditional | None | `sk-...` | OpenAI API authentication key |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | `gpt-4o-mini`, `gpt-4o`, `o1` | OpenAI model identifier |
| `OPENAI_BASE_URL` | No | None | URL string | Custom OpenAI-compatible endpoint (e.g. Ollama `http://localhost:11434/v1`) |
| `ANTHROPIC_API_KEY`| Conditional | None | `sk-ant-...` | Anthropic API authentication key |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-latest` | Claude model names | Anthropic model identifier |
| `GROQ_API_KEY` | Conditional | None | `gsk_...` | Groq Cloud API authentication key |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | LLaMA model names | Groq high-speed model identifier |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING` | Application logging verbosity |

> **Note on Offline Operation**: If no API keys are configured, the system automatically runs in deterministic **Mock Engine** mode.

---

## 2. Local Host Deployment (Bare Metal)

### Step 1: Clone Repository & Create Virtual Environment
```bash
git clone <repository-url>
cd LLM-PoweredFileSystemAssistant

# Create isolated Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run Automated Test Verification
```bash
pytest
```
*Expected: 24 passed in under 1 second.*

### Step 4: Run the Assistant
```bash
# Execute a single natural language query
python llm_file_assistant.py "Find resumes mentioning Python experience"

# Or launch the interactive terminal session
python llm_file_assistant.py --interactive
```

---

## 3. Containerized Deployment (Docker)

### 3.1 Production Multi-Stage `Dockerfile`
Create or use the following production-hardened `Dockerfile`:

```dockerfile
# ==============================================================================
# Stage 1: Build & Dependency Resolution
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Stage 2: Minimal Distroless / Hardened Runtime
# ==============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/.local/bin:${PATH}"

# Create unprivileged application user
RUN useradd --create-home --shell /bin/bash appuser

# Copy installed Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appuser fs_tools.py .
COPY --chown=appuser:appuser llm_file_assistant.py .
COPY --chown=appuser:appuser demo.py .
COPY --chown=appuser:appuser resumes/ ./resumes/

# Create destination summaries folder with proper ownership
RUN mkdir -p /app/summaries && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import fs_tools; exit(0)" || exit 1

ENTRYPOINT ["python", "llm_file_assistant.py"]
CMD ["--interactive"]
```

### 3.2 `docker-compose.yml` for Local Orchestration
```yaml
version: '3.8'

services:
  file-assistant:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: llm_file_assistant
    restart: unless-stopped
    stdin_open: true # Enables interactive terminal mode
    tty: true
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./resumes:/app/resumes:ro     # Mount inbound resumes as read-only
      - ./summaries:/app/summaries    # Persist generated summaries to host
```

### 3.3 Building and Running with Docker
```bash
# Build the container image
docker build -t llm-file-assistant:latest .

# Run single query inside container
docker run --rm \
  -e OPENAI_API_KEY="sk-..." \
  -v "$(pwd)/summaries:/app/summaries" \
  llm-file-assistant:latest "Create a summary file for resume_john_doe.pdf"

# Run interactive REPL session with Docker Compose
docker compose run --rm file-assistant
```

---

## 4. Cloud Production Deployment (AWS ECS Fargate)

### 4.1 ECS Task Definition (`task-definition.json`)
```json
{
  "family": "llm-fs-assistant-prod",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::123456789012:role/llm-fs-assistant-task-role-prod",
  "containerDefinitions": [
    {
      "name": "assistant",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-fs-assistant:latest",
      "essential": true,
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:llm-fs-assistant/llm-keys-prod:OPENAI_API_KEY::"
        }
      ],
      "environment": [
        {"name": "OPENAI_MODEL", "value": "gpt-4o-mini"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/llm-fs-assistant-prod",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### 4.2 Rolling Update Deployment Procedure
```bash
# Register new task definition revision
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Update ECS Service with zero-downtime rolling update
aws ecs update-service \
  --cluster prod-cluster \
  --service llm-assistant-service \
  --task-definition llm-fs-assistant-prod \
  --force-new-deployment
```

---

## 5. Troubleshooting Guide

| Issue / Symptom | Root Cause | Diagnostic Step | Resolution |
| :--- | :--- | :--- | :--- |
| **"No OPENAI_API_KEY found. Falling back to Mock engine."** | Environment variable missing or `.env` not present | Run `python -c "import os; print(os.getenv('OPENAI_API_KEY'))"` | Export key in shell or create `.env` file with `OPENAI_API_KEY=sk-...`. |
| **"pypdf is required to parse PDF files."** | `pypdf` dependency is not installed | Run `python -c "import pypdf"` | Run `pip install pypdf>=5.0.0` or `pip install -r requirements.txt`. |
| **"Permission denied writing to 'summaries/...' "** | Process lacks write permissions on destination directory | Inspect filesystem permissions: `ls -ld summaries/` | Adjust write permissions (`chmod -R 775 summaries/`) or run container as non-root user with write ownership. |
| **"RateLimitError (429) from LLM provider"** | API quota exceeded or concurrency limit hit | Inspect API usage dashboard | Switch to fallback provider (`--provider groq` or `--provider mock`) or set up backoff retries. |
| **"Tool iteration limit reached"** | Model looped without producing terminal natural language response | Run with `--verbose` to inspect `[Tool Call]` traces | Refine user query to be more specific or increase `max_iterations` in `assistant.run()`. |
| **Encoding errors reading legacy TXT files** | Character encoding incompatible with standard UTF-8 | Check file encoding | `fs_tools._read_txt` automatically falls back through `utf-8`, `utf-8-sig`, `latin-1`, and `cp1252`. |
