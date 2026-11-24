resource "aws_secretsmanager_secret" "this" {
  name                    = "${var.app_name}-${var.environment}-llm-api-keys"
  description             = "LLM API keys for OpenAI, Anthropic, and Groq"
  recovery_window_in_days = var.environment == "prod" ? 30 : 0

  tags = merge(var.tags, {
    Name = "${var.app_name}-${var.environment}-secrets"
  })
}

resource "aws_secretsmanager_secret_version" "this" {
  secret_id = aws_secretsmanager_secret.this.id
  secret_string = jsonencode({
    OPENAI_API_KEY    = "sk-placeholder"
    ANTHROPIC_API_KEY = "sk-ant-placeholder"
    GROQ_API_KEY      = "gsk-placeholder"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
