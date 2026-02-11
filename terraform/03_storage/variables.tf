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

variable "transcription_queue_arn" {
  description = "ARN of the transcription queue from terraform/02_queues output."
  type        = string
}

variable "transcription_queue_url" {
  description = "URL of the transcription queue from terraform/02_queues output."
  type        = string
}

variable "audio_expiration_days" {
  description = "Days to retain uploaded audio objects before expiration."
  type        = number
  default     = 30
}
