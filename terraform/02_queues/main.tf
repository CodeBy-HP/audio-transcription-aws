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
  transcription_dlq_name = "audiotrans-${var.environment}-transcription-dlq"
  transcription_name     = "audiotrans-${var.environment}-transcription-queue"
  notification_dlq_name  = "audiotrans-${var.environment}-notification-dlq"
  notification_name      = "audiotrans-${var.environment}-notification-queue"

  common_tags = {
    Project     = "audio-transcription"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_sqs_queue" "transcription_dlq" {
  name                      = local.transcription_dlq_name
  message_retention_seconds = var.dlq_message_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = local.common_tags
}

resource "aws_sqs_queue" "transcription" {
  name                       = local.transcription_name
  visibility_timeout_seconds = var.transcription_visibility_timeout_seconds
  message_retention_seconds  = var.main_queue_message_retention_seconds
  receive_wait_time_seconds  = var.receive_wait_time_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.transcription_dlq.arn
    maxReceiveCount     = var.transcription_max_receive_count
  })

  tags = local.common_tags
}

resource "aws_sqs_queue_redrive_allow_policy" "transcription_dlq_allow" {
  queue_url = aws_sqs_queue.transcription_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.transcription.arn]
  })
}

resource "aws_sqs_queue" "notification_dlq" {
  name                      = local.notification_dlq_name
  message_retention_seconds = var.dlq_message_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = local.common_tags
}

resource "aws_sqs_queue" "notification" {
  name                       = local.notification_name
  visibility_timeout_seconds = var.notification_visibility_timeout_seconds
  message_retention_seconds  = var.main_queue_message_retention_seconds
  receive_wait_time_seconds  = var.receive_wait_time_seconds
  sqs_managed_sse_enabled    = true

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.notification_dlq.arn
    maxReceiveCount     = var.notification_max_receive_count
  })

  tags = local.common_tags
}

resource "aws_sqs_queue_redrive_allow_policy" "notification_dlq_allow" {
  queue_url = aws_sqs_queue.notification_dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.notification.arn]
  })
}
