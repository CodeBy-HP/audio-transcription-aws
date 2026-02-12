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

variable "users_table_name" {
  description = "Users table name from terraform/01_database output."
  type        = string
}

variable "jobs_table_name" {
  description = "Jobs table name from terraform/01_database output."
  type        = string
}

variable "users_table_arn" {
  description = "Users table ARN from terraform/01_database output."
  type        = string
}

variable "jobs_table_arn" {
  description = "Jobs table ARN from terraform/01_database output."
  type        = string
}

variable "audio_bucket_name" {
  description = "Audio bucket name from terraform/03_storage output."
  type        = string
}

variable "audio_bucket_arn" {
  description = "Audio bucket ARN from terraform/03_storage output."
  type        = string
}

variable "transcript_bucket_name" {
  description = "Transcript bucket name from terraform/03_storage output."
  type        = string
}

variable "transcript_bucket_arn" {
  description = "Transcript bucket ARN from terraform/03_storage output."
  type        = string
}

variable "clerk_jwks_url" {
  description = "Clerk JWKS URL used by API auth guard."
  type        = string
}

variable "lambda_zip_path" {
  description = "Path to packaged API Lambda zip file."
  type        = string
  default     = "../../backend/api/api_lambda.zip"
}

variable "lambda_timeout_seconds" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 30
}

variable "lambda_memory_mb" {
  description = "Lambda memory size in MB."
  type        = number
  default     = 512
}

variable "presigned_expires_seconds" {
  description = "Presigned upload expiration time in seconds."
  type        = number
  default     = 900
}

variable "max_file_size_bytes" {
  description = "Maximum upload size accepted by API."
  type        = number
  default     = 104857600
}

variable "cors_allow_origins" {
  description = "Allowed origins for HTTP API CORS."
  type        = list(string)
  default     = ["http://localhost:3000"]
}
