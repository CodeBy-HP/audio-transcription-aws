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

variable "receive_wait_time_seconds" {
  description = "SQS long polling wait time in seconds."
  type        = number
  default     = 20
}

variable "main_queue_message_retention_seconds" {
  description = "Message retention for main queues."
  type        = number
  default     = 345600 # 4 days
}

variable "dlq_message_retention_seconds" {
  description = "Message retention for dead-letter queues."
  type        = number
  default     = 1209600 # 14 days
}

variable "transcription_visibility_timeout_seconds" {
  description = "Visibility timeout for transcription queue."
  type        = number
  default     = 900 # 15 minutes
}

variable "notification_visibility_timeout_seconds" {
  description = "Visibility timeout for notification queue."
  type        = number
  default     = 60
}

variable "transcription_max_receive_count" {
  description = "Max receive attempts before moving to transcription DLQ."
  type        = number
  default     = 3
}

variable "notification_max_receive_count" {
  description = "Max receive attempts before moving to notification DLQ."
  type        = number
  default     = 5
}
