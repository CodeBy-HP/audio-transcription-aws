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

data "aws_iam_policy_document" "api_lambda_access" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["arn:aws:logs:*:*:*"]
  }

  statement {
    sid    = "UsersJobsTableAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query"
    ]
    resources = [
      var.users_table_arn,
      var.jobs_table_arn
    ]
  }

  statement {
    sid    = "AudioBucketAccessForPresign"
    effect = "Allow"
    actions = [
      "s3:PutObject"
    ]
    resources = ["${var.audio_bucket_arn}/*"]
  }
}

locals {
  lambda_function_name = "audiotrans-${var.environment}-api"
  api_name             = "audiotrans-${var.environment}-http-api"

  common_tags = {
    Project     = "audio-transcription"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_iam_role" "api_lambda" {
  name               = "audiotrans-${var.environment}-api-lambda-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy" "api_lambda_access" {
  name   = "audiotrans-${var.environment}-api-lambda-access"
  role   = aws_iam_role.api_lambda.id
  policy = data.aws_iam_policy_document.api_lambda_access.json
}

resource "aws_lambda_function" "api" {
  function_name    = local.lambda_function_name
  role             = aws_iam_role.api_lambda.arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.11"
  filename         = var.lambda_zip_path
  source_code_hash = filebase64sha256(var.lambda_zip_path)
  timeout          = var.lambda_timeout_seconds
  memory_size      = var.lambda_memory_mb

  environment {
    variables = {
      USERS_TABLE_NAME          = var.users_table_name
      JOBS_TABLE_NAME           = var.jobs_table_name
      AUDIO_BUCKET_NAME         = var.audio_bucket_name
      CLERK_JWKS_URL            = var.clerk_jwks_url
      PRESIGNED_EXPIRES_SECONDS = tostring(var.presigned_expires_seconds)
      MAX_FILE_SIZE_BYTES       = tostring(var.max_file_size_bytes)
    }
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_api" "http" {
  name          = local.api_name
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.cors_allow_origins
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
    max_age       = 3600
  }

  tags = local.common_tags
}

resource "aws_apigatewayv2_integration" "lambda_proxy" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = aws_lambda_function.api.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_proxy.id}"
}

resource "aws_apigatewayv2_route" "root" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_proxy.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true

  tags = local.common_tags
}

resource "aws_lambda_permission" "allow_apigw_invoke" {
  statement_id  = "AllowHttpApiInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
