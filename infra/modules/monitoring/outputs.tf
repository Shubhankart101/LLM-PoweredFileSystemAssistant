output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.this.name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.this.arn
}

output "error_alarm_arn" {
  description = "ARN of the error spike alarm"
  value       = aws_cloudwatch_metric_alarm.error_spike.arn
}

output "cpu_alarm_arn" {
  description = "ARN of the CPU alarm"
  value       = aws_cloudwatch_metric_alarm.ecs_high_cpu.arn
}

output "memory_alarm_arn" {
  description = "ARN of the Memory alarm"
  value       = aws_cloudwatch_metric_alarm.ecs_high_memory.arn
}
