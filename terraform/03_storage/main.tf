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

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "transcription_queue_from_s3" {
  statement {
    sid    = "AllowS3SendMessage"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions   = ["sqs:SendMessage"]
    resources = [var.transcription_queue_arn]

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = [aws_s3_bucket.audio.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

locals {
  audio_bucket_name      = "audiotrans-${var.environment}-audio-${data.aws_caller_identity.current.account_id}"
  transcript_bucket_name = "audiotrans-${var.environment}-transcripts-${data.aws_caller_identity.current.account_id}"

  common_tags = {
    Project     = "audio-transcription"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket" "audio" {
  bucket = local.audio_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket" "transcripts" {
  bucket = local.transcript_bucket_name
  tags   = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "audio" {
  bucket = aws_s3_bucket.audio.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "transcripts" {
  bucket = aws_s3_bucket.transcripts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["POST", "GET", "HEAD"]
    allowed_origins = var.cors_allow_origins
    expose_headers  = ["ETag", "x-amz-request-id", "x-amz-id-2"]
    max_age_seconds = 3600
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "transcripts" {
  bucket = aws_s3_bucket.transcripts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "audio" {
  bucket = aws_s3_bucket.audio.id

  rule {
    id     = "expire-audio-after-30-days"
    status = "Enabled"

    filter {}

    expiration {
      days = var.audio_expiration_days
    }
  }
}

resource "aws_sqs_queue_policy" "transcription_from_s3" {
  queue_url = var.transcription_queue_url
  policy    = data.aws_iam_policy_document.transcription_queue_from_s3.json
}

resource "aws_s3_bucket_notification" "audio_to_transcription_queue" {
  bucket = aws_s3_bucket.audio.id

  queue {
    id            = "audio-object-created"
    queue_arn     = var.transcription_queue_arn
    events        = ["s3:ObjectCreated:*"]
    filter_prefix = "audio/"
  }

  depends_on = [aws_sqs_queue_policy.transcription_from_s3]
}
