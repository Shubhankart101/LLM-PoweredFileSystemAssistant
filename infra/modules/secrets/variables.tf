variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "recovery_window_days" {
  description = "Number of days before deleted secrets are permanently removed"
  type        = number
  default     = 0
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
