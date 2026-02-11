variable "aws_region" {
  description = "AWS region for this module."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (for example: dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "enable_deletion_protection" {
  description = "Whether to enable DynamoDB deletion protection."
  type        = bool
  default     = false
}
