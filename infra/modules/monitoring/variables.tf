variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "log_group_name" {
  description = "Name of the CloudWatch log group to monitor"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "ecs_service_name" {
  description = "Name of the ECS service"
  type        = string
}

variable "target_group_arn_suffix" {
  description = "ARN suffix of the target group"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ARN suffix of the ALB"
  type        = string
}

variable "alarm_cpu_threshold" {
  description = "CPU percentage threshold for CloudWatch alarm"
  type        = number
  default     = 80
}

variable "alarm_memory_threshold" {
  description = "Memory percentage threshold for CloudWatch alarm"
  type        = number
  default     = 80
}

variable "alarm_error_count_threshold" {
  description = "Application error count threshold per period"
  type        = number
  default     = 5
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
