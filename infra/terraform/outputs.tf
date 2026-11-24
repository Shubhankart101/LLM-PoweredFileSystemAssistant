# ==============================================================================
# Outputs Definition
# ==============================================================================
# Exported resource identifiers, ARNs, endpoints, and names for integration.
# ==============================================================================

# ------------------------------------------------------------------------------
# Storage Outputs (S3)
# ------------------------------------------------------------------------------
output "s3_bucket_name" {
  description = "Name of the S3 bucket created for resumes and generated summaries."
  value       = aws_s3_bucket.resumes.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket created for resumes and generated summaries."
  value       = aws_s3_bucket.resumes.arn
}

output "s3_bucket_domain_name" {
  description = "Regional domain name of the S3 bucket."
  value       = aws_s3_bucket.resumes.bucket_regional_domain_name
}

# ------------------------------------------------------------------------------
# Secrets Manager Outputs
# ------------------------------------------------------------------------------
output "secrets_manager_secret_arn" {
  description = "ARN of the Secrets Manager secret storing LLM API keys."
  value       = aws_secretsmanager_secret.llm_keys.arn
}

output "secrets_manager_secret_name" {
  description = "Name of the Secrets Manager secret storing LLM API keys."
  value       = aws_secretsmanager_secret.llm_keys.name
}

# ------------------------------------------------------------------------------
# Compute Outputs (ECS Fargate & ALB)
# ------------------------------------------------------------------------------
output "container_service_endpoint" {
  description = "Public HTTP endpoint URL of the Application Load Balancer."
  value       = "http://${aws_lb.main.dns_name}"
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer."
  value       = aws_lb.main.dns_name
}

output "alb_arn" {
  description = "ARN of the Application Load Balancer."
  value       = aws_lb.main.arn
}

output "ecs_cluster_name" {
  description = "Name of the ECS Cluster running the assistant container."
  value       = aws_ecs_cluster.main.name
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS Cluster."
  value       = aws_ecs_cluster.main.arn
}

output "ecs_service_name" {
  description = "Name of the ECS Service."
  value       = aws_ecs_service.main.name
}

output "ecs_service_arn" {
  description = "ARN of the ECS Service."
  value       = aws_ecs_service.main.id
}

output "ecs_task_definition_arn" {
  description = "Full ARN of the registered ECS Task Definition."
  value       = aws_ecs_task_definition.main.arn
}

# ------------------------------------------------------------------------------
# IAM Roles Outputs
# ------------------------------------------------------------------------------
output "ecs_execution_role_arn" {
  description = "ARN of the ECS Execution IAM Role."
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS Task IAM Role."
  value       = aws_iam_role.ecs_task.arn
}

# ------------------------------------------------------------------------------
# Logging & Monitoring Outputs
# ------------------------------------------------------------------------------
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Log Group for container logs."
  value       = aws_cloudwatch_log_group.ecs.name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch Log Group for container logs."
  value       = aws_cloudwatch_log_group.ecs.arn
}

output "cloudwatch_alarm_high_error_rate_arn" {
  description = "ARN of the CloudWatch Alarm monitoring application error logs."
  value       = aws_cloudwatch_metric_alarm.app_errors.arn
}

output "cloudwatch_alarm_cpu_high_arn" {
  description = "ARN of the CloudWatch Alarm monitoring ECS CPU utilization."
  value       = aws_cloudwatch_metric_alarm.cpu_high.arn
}

output "cloudwatch_alarm_memory_high_arn" {
  description = "ARN of the CloudWatch Alarm monitoring ECS Memory utilization."
  value       = aws_cloudwatch_metric_alarm.memory_high.arn
}

output "cloudwatch_alarm_unhealthy_hosts_arn" {
  description = "ARN of the CloudWatch Alarm monitoring ALB unhealthy host counts."
  value       = aws_cloudwatch_metric_alarm.unhealthy_hosts.arn
}

# ------------------------------------------------------------------------------
# Networking Outputs
# ------------------------------------------------------------------------------
output "vpc_id" {
  description = "ID of the dedicated application VPC."
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets."
  value       = aws_subnet.private[*].id
}
