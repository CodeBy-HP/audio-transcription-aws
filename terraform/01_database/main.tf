terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  users_table_name = "audiotrans-${var.environment}-users"
  jobs_table_name  = "audiotrans-${var.environment}-jobs"

  common_tags = {
    Project     = "audio-transcription"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_dynamodb_table" "users" {
  name                        = local.users_table_name
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "clerk_user_id"
  deletion_protection_enabled = var.enable_deletion_protection

  attribute {
    name = "clerk_user_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}

resource "aws_dynamodb_table" "jobs" {
  name                        = local.jobs_table_name
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "clerk_user_id"
  range_key                   = "job_id"
  deletion_protection_enabled = var.enable_deletion_protection

  attribute {
    name = "clerk_user_id"
    type = "S"
  }

  attribute {
    name = "job_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = local.common_tags
}
