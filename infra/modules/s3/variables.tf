variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "bucket_prefix" {
  description = "Prefix for the S3 bucket name"
  type        = string
  default     = "llm-assistant"
}

variable "versioning_enabled" {
  description = "Enable S3 bucket object versioning"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default     = {}
}
