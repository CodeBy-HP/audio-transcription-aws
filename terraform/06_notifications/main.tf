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

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "notification_lambda_access" {
  statement {
    sid    = "NotificationQueueRead"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ChangeMessageVisibility"
    ]
    resources = [var.notification_queue_arn]
  }

  statement {
    sid    = "DynamoLookup"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem"
    ]
    resources = [var.users_table_arn, var.jobs_table_arn]
  }

  statement {
    sid    = "TranscriptReadForPresign"
    effect = "Allow"
    actions = [
      "s3:GetObject"
    ]
    resources = ["${var.transcript_bucket_arn}/*"]
  }

  statement {
    sid    = "SendEmailWithSES"
    effect = "Allow"
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]
    resources = ["*"]
  }
}

locals {
  function_name = "audiotrans-${var.environment}-notification-worker"
  sender_email  = var.sender_email

  common_tags = {
    Project     = "audio-transcription"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ses_email_identity" "sender" {
  email = local.sender_email
}

resource "aws_iam_role" "notification_lambda" {
  name               = "audiotrans-${var.environment}-notification-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "basic_execution" {
  role       = aws_iam_role.notification_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "notification_lambda_access" {
  name   = "audiotrans-${var.environment}-notification-lambda-access"
  role   = aws_iam_role.notification_lambda.id
  policy = data.aws_iam_policy_document.notification_lambda_access.json
}

resource "aws_lambda_function" "notification_worker" {
  function_name    = local.function_name
  role             = aws_iam_role.notification_lambda.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.11"
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb

  environment {
    variables = {
      NOTIFICATION_QUEUE_URL  = var.notification_queue_url
      USERS_TABLE_NAME        = var.users_table_name
      JOBS_TABLE_NAME         = var.jobs_table_name
      TRANSCRIPT_BUCKET_NAME  = var.transcript_bucket_name
      SENDER_EMAIL            = local.sender_email
      SENDGRID_API_KEY        = var.sendgrid_api_key
      DOWNLOAD_URL_TTL_SECONDS = tostring(var.download_url_ttl_seconds)
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_event_source_mapping" "notification_queue" {
  event_source_arn = var.notification_queue_arn
  function_name    = aws_lambda_function.notification_worker.arn
  batch_size       = var.batch_size
  enabled          = true
}
