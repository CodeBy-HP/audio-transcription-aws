variable "aws_region" {
  description = "AWS region for frontend resources."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (for example: dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "frontend_bucket_name" {
  description = "Optional custom frontend bucket name. Leave empty to auto-generate."
  type        = string
  default     = ""
}
