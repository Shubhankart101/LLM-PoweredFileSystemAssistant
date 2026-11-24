# ==============================================================================
# Variables Definition
# ==============================================================================
# Strongly-typed input variables for LLM File System Assistant infrastructure.
# ==============================================================================

variable "aws_region" {
  type        = string
  description = "Target AWS region for deploying infrastructure."
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, prod)."
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: 'dev', 'staging', 'prod'."
  }
}

variable "app_name" {
  type        = string
  description = "Application and resource naming prefix."
  default     = "llm-fs-assistant"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the dedicated application VPC."
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "List of public subnet CIDR blocks across multiple availability zones."
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "List of private subnet CIDR blocks across multiple availability zones."
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "enable_nat_gateway" {
  type        = bool
  description = "Whether to provision a NAT Gateway for private subnets. Set false for cost-effective dev."
  default     = false
}

variable "container_image" {
  type        = string
  description = "Docker container image URI for the LLM File System Assistant."
  default     = "ghcr.io/shubhankart101/llm-poweredfilesystemassistant:latest"
}

variable "container_port" {
  type        = number
  description = "Port exposed by the container application."
  default     = 8000
}

variable "cpu" {
  type        = number
  description = "Fargate task CPU units (256, 512, 1024, 2048, 4096)."
  default     = 512

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU units must be a valid Fargate allocation (256, 512, 1024, 2048, 4096)."
  }
}

variable "memory" {
  type        = number
  description = "Fargate task memory allocation in MB (e.g., 512, 1024, 2048, 4096)."
  default     = 1024
}

variable "desired_count" {
  type        = number
  description = "Desired number of ECS task instances running simultaneously."
  default     = 1
}

variable "health_check_path" {
  type        = string
  description = "HTTP health check endpoint path on the container."
  default     = "/health"
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention period in days."
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch retention value."
  }
}

variable "s3_versioning_enabled" {
  type        = bool
  description = "Enable S3 bucket object versioning for resume document history."
  default     = true
}

variable "secret_recovery_window_days" {
  type        = number
  description = "Number of days AWS Secrets Manager waits before deleting deleted secrets (0 for instant deletion in dev)."
  default     = 0
}

variable "alarm_cpu_threshold" {
  type        = number
  description = "Percentage CPU utilization threshold for CloudWatch high CPU alarm."
  default     = 80
}

variable "alarm_memory_threshold" {
  type        = number
  description = "Percentage Memory utilization threshold for CloudWatch high Memory alarm."
  default     = 80
}

variable "alarm_error_count_threshold" {
  type        = number
  description = "Threshold count of logged application errors in 5 minutes triggering an alarm."
  default     = 5
}

variable "tags" {
  type        = map(string)
  description = "Additional tags to apply to all provisioned infrastructure resources."
  default     = {}
}
