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

output "alb_unhealthy_alarm_arn" {
  description = "ARN of the ALB unhealthy hosts alarm"
  value       = aws_cloudwatch_metric_alarm.alb_unhealthy_hosts.arn
}
