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

variable "notification_queue_url" {
  description = "Notification queue URL from terraform/02_queues."
  type        = string
}

variable "notification_queue_arn" {
  description = "Notification queue ARN from terraform/02_queues."
  type        = string
}

variable "users_table_name" {
  description = "Users table name from terraform/01_database."
  type        = string
}

variable "users_table_arn" {
  description = "Users table ARN from terraform/01_database."
  type        = string
}

variable "jobs_table_name" {
  description = "Jobs table name from terraform/01_database."
  type        = string
}

variable "jobs_table_arn" {
  description = "Jobs table ARN from terraform/01_database."
  type        = string
}

variable "transcript_bucket_name" {
  description = "Transcript bucket name from terraform/03_storage."
  type        = string
}

variable "transcript_bucket_arn" {
  description = "Transcript bucket ARN from terraform/03_storage."
  type        = string
}

variable "sender_email" {
  description = "Verified SES sender email identity."
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to packaged notification Lambda zip."
  type        = string
  default     = "../../backend/notify/notify_lambda.zip"
}

variable "lambda_timeout_seconds" {
  description = "Notification Lambda timeout in seconds."
  type        = number
  default     = 60
}

variable "lambda_memory_mb" {
  description = "Notification Lambda memory size in MB."
  type        = number
  default     = 256
}

variable "download_url_ttl_seconds" {
  description = "Presigned transcript download link TTL."
  type        = number
  default     = 86400
}

variable "batch_size" {
  description = "SQS batch size for Lambda event source mapping."
  type        = number
  default     = 10
}
