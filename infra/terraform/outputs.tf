# VPC Outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

# Storage Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for candidate resumes and summaries"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 storage bucket"
  value       = module.s3.bucket_arn
}

# Secrets Outputs
output "secrets_manager_secret_name" {
  description = "Name of the Secrets Manager secret"
  value       = module.secrets.secret_name
}

output "secrets_manager_secret_arn" {
  description = "ARN of the Secrets Manager secret"
  value       = module.secrets.secret_arn
}

# Compute & Load Balancer Outputs
output "ecs_cluster_name" {
  description = "Name of the ECS Fargate cluster"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "Name of the ECS Fargate service"
  value       = module.ecs.service_name
}

output "alb_dns_name" {
  description = "DNS endpoint of the Application Load Balancer"
  value       = module.ecs.alb_dns_name
}

# Monitoring Outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.monitoring.log_group_name
}

output "cloudwatch_error_alarm_arn" {
  description = "ARN of the application error spike alarm"
  value       = module.monitoring.error_alarm_arn
}
