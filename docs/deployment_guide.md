# 🚢 Deployment & Operations Guide

This guide provides operational instructions for deploying the **LLM-Powered File System Assistant** locally, via Docker / Docker Compose, and to AWS ECS Fargate using Terraform.

---

## 1. Environment Variable Configuration Matrix

Configure the application using environment variables (defined in `.env` locally or injected via AWS Secrets Manager in production):

| Variable | Required | Default | Description |
| :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | Conditional | None | OpenAI API authentication key (`sk-...`) |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model identifier |
| `OPENAI_BASE_URL` | No | None | Custom OpenAI-compatible endpoint (e.g. Ollama `http://localhost:11434/v1`) |
| `ANTHROPIC_API_KEY` | Conditional | None | Anthropic API authentication key (`sk-ant-...`) |
| `ANTHROPIC_MODEL` | No | `claude-3-5-sonnet-latest` | Anthropic model identifier |
| `GROQ_API_KEY` | Conditional | None | Groq Cloud API authentication key (`gsk_...`) |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Groq model identifier |
| `ASSISTANT_HOST` | No | `127.0.0.1` | Bind host when running `--serve` HTTP mode |
| `PORT` | No | `8000` | Bind port when running `--serve` HTTP mode |

> **Offline Operation**: When no API keys are supplied, the assistant automatically routes queries through the deterministic `MockLLMEngine` so all CLI tools, demos, and HTTP endpoints continue operating offline.

---

## 2. Local Host Deployment (Bare Metal)

```bash
git clone https://github.com/Shubhankart101/LLM-PoweredFileSystemAssistant.git
cd LLM-PoweredFileSystemAssistant

# Create and activate virtual environment
python -m venv venv
# Windows PowerShell: .\venv\Scripts\Activate.ps1
# Linux / macOS:     source venv/bin/activate

# Install dependencies and verify test suite
pip install --upgrade pip
pip install -r requirements.txt
pytest
```

Run in any of the supported modes:
```bash
# Single query CLI
python llm_file_assistant.py "Find resumes mentioning Python experience"

# Interactive REPL
python llm_file_assistant.py --interactive

# Guided demo (for presentation/recording)
python demo.py

# HTTP API server
python llm_file_assistant.py --serve --port 8000
```

---

## 3. Containerized Deployment (Docker & Docker Compose)

### 3.1 Multi-Stage `Dockerfile` Overview
The repository's root `Dockerfile` implements:
- **Builder Stage (`python:3.12-slim`)**: Compiles packages into an isolated `/opt/venv`.
- **Runner Stage (`python:3.12-slim`)**: Copies `/opt/venv`, installs `ca-certificates` and `curl`, runs under non-root `appuser` (UID `10001`), exposes port `8000`, defines persistent volumes `/app/resumes` and `/app/summaries`, and configures a container `HEALTHCHECK`.

### 3.2 Running via `docker-compose.yml`

`docker-compose.yml` provides three ready-to-use service profiles:

```bash
# 1. Interactive assistant (default service)
docker compose run --rm assistant

# 2. Single CLI query inside container
docker compose run --rm assistant "Create a summary file for resume_john_doe.pdf"

# 3. Automated benchmark demo
docker compose --profile demo run --rm demo

# 4. HTTP API server on http://localhost:8000 (/health and /query)
docker compose --profile api up -d
```

Test the HTTP API service:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find resumes mentioning Python experience"}'
```

---

## 4. Cloud Production Deployment (AWS ECS Fargate via Terraform)

The modular Terraform configuration in `infra/terraform/` provisions VPC networking, S3 storage, Secrets Manager, ECS Fargate + ALB, and CloudWatch alarms.

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your image URI, environment, and region

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Populate production LLM API keys into AWS Secrets Manager after creation:
```bash
aws secretsmanager put-secret-value \
  --secret-id "llm-fs-assistant-dev-llm-api-keys" \
  --secret-string '{"OPENAI_API_KEY":"sk-...","ANTHROPIC_API_KEY":"sk-ant-...","GROQ_API_KEY":"gsk_..."}'
```

For full details on remote state locking and variable tuning, see [`infra/terraform/TERRAFORM_GUIDE.md`](../infra/terraform/TERRAFORM_GUIDE.md).

---

## 5. Troubleshooting Matrix

| Issue / Symptom | Root Cause | Diagnostic Step | Resolution |
| :--- | :--- | :--- | :--- |
| **"No OPENAI_API_KEY found. Falling back to Mock engine."** | API key not set in env or `.env` | Check `env` or `.env` file | Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GROQ_API_KEY` in `.env` / Secrets Manager. |
| **"pypdf is required to parse PDF files."** | Missing dependency | `python -c "import pypdf"` | Install via `pip install -r requirements.txt`. |
| **"Permission denied writing to 'summaries/...'"** | Host volume permissions mismatch with UID `10001` | Inspect permissions on `./summaries` | Ensure host `./summaries` is writable or run `chmod -R 775 summaries/`. |
| **"RateLimitError (429) from LLM provider"** | Provider quota exceeded | Inspect provider dashboard | Switch `--provider groq` / `--provider anthropic` / `--provider mock`. |
| **Encoding issues reading TXT files** | Legacy Windows/ISO-8859-1 file | Inspect file bytes | `fs_tools._read_txt` automatically retries `utf-8`, `utf-8-sig`, `latin-1`, and `cp1252`. |
