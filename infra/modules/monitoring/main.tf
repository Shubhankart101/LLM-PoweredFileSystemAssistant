resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${var.app_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.app_name}-${var.environment}-logs"
  })
}

resource "aws_cloudwatch_log_metric_filter" "app_errors" {
  name           = "${var.app_name}-${var.environment}-app-errors"
  pattern        = "?ERROR ?CRITICAL ?Exception ?failed"
  log_group_name = aws_cloudwatch_log_group.this.name

  metric_transformation {
    name          = "ApplicationErrorCount"
    namespace     = "LLMAssistant/${var.environment}"
    value         = "1"
    default_value = 0
  }
}

resource "aws_cloudwatch_metric_alarm" "error_spike" {
  alarm_name          = "${var.app_name}-${var.environment}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApplicationErrorCount"
  namespace           = "LLMAssistant/${var.environment}"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Triggered when LLM File Assistant logs 5+ errors across 2 consecutive minutes."

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_high_cpu" {
  alarm_name          = "${var.app_name}-${var.environment}-ecs-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "Triggers when ECS CPU utilization exceeds 80% for 3 consecutive minutes."

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "ecs_high_memory" {
  alarm_name          = "${var.app_name}-${var.environment}-ecs-high-memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 85
  alarm_description   = "Triggers when ECS memory utilization exceeds 85% for 3 consecutive minutes."

  dimensions = {
    ClusterName = var.ecs_cluster_name
    ServiceName = var.ecs_service_name
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "alb_unhealthy_hosts" {
  alarm_name          = "${var.app_name}-${var.environment}-alb-unhealthy-hosts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "UnHealthyHostCount"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0
  alarm_description   = "Triggers if ALB detects any unhealthy container targets."

  dimensions = {
    TargetGroup  = var.target_group_arn_suffix
    LoadBalancer = var.alb_arn_suffix
  }

  tags = var.tags
}
