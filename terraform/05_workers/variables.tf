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

variable "transcription_queue_url" {
  description = "Transcription queue URL from terraform/02_queues."
  type        = string
}

variable "transcription_queue_arn" {
  description = "Transcription queue ARN from terraform/02_queues."
  type        = string
}

variable "notification_queue_url" {
  description = "Notification queue URL from terraform/02_queues."
  type        = string
}

variable "notification_queue_arn" {
  description = "Notification queue ARN from terraform/02_queues."
  type        = string
}

variable "audio_bucket_name" {
  description = "Audio bucket name from terraform/03_storage."
  type        = string
}

variable "audio_bucket_arn" {
  description = "Audio bucket ARN from terraform/03_storage."
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

variable "jobs_table_name" {
  description = "Jobs table name from terraform/01_database."
  type        = string
}

variable "jobs_table_arn" {
  description = "Jobs table ARN from terraform/01_database."
  type        = string
}

variable "worker_image_uri" {
  description = "Optional full worker image URI. If empty, repository_url:latest is used."
  type        = string
  default     = ""
}

variable "whisper_model_id" {
  description = "Hugging Face Whisper model ID."
  type        = string
  default     = "openai/whisper-tiny"
}

variable "poll_wait_seconds" {
  description = "SQS long polling wait time for the worker."
  type        = number
  default     = 20
}

variable "desired_count" {
  description = "ECS service desired task count."
  type        = number
  default     = 0
}

variable "task_cpu" {
  description = "Task CPU units (1024 = 1 vCPU)."
  type        = number
  default     = 2048
}

variable "task_memory" {
  description = "Task memory in MiB."
  type        = number
  default     = 4096
}

variable "log_retention_days" {
  description = "CloudWatch log retention period for worker logs."
  type        = number
  default     = 7
}

variable "subnet_ids" {
  description = "Optional subnet IDs for ECS service. If empty, default VPC subnets are used."
  type        = list(string)
  default     = []
}
