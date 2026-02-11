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

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "worker_task_policy" {
  statement {
    sid    = "ReceiveTranscriptionQueue"
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]
    resources = [var.transcription_queue_arn]
  }

  statement {
    sid    = "SendNotificationQueue"
    effect = "Allow"
    actions = [
      "sqs:SendMessage"
    ]
    resources = [var.notification_queue_arn]
  }

  statement {
    sid    = "AudioReadAndTranscriptWrite"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]
    resources = [
      "${var.audio_bucket_arn}/*",
      "${var.transcript_bucket_arn}/*"
    ]
  }

  statement {
    sid    = "JobsTableReadWrite"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:UpdateItem"
    ]
    resources = [var.jobs_table_arn]
  }
}

locals {
  cluster_name            = "audiotrans-${var.environment}-cluster"
  service_name            = "audiotrans-${var.environment}-transcription-worker"
  task_family             = "audiotrans-${var.environment}-transcription-worker"
  repository_name         = "audiotrans-${var.environment}-transcription-worker"
  log_group_name          = "/ecs/audiotrans-${var.environment}-transcription-worker"
  effective_subnet_ids    = length(var.subnet_ids) > 0 ? var.subnet_ids : data.aws_subnets.default.ids
  effective_worker_image  = var.worker_image_uri != "" ? var.worker_image_uri : "${aws_ecr_repository.transcription.repository_url}:latest"
  effective_poll_wait_sec = tostring(var.poll_wait_seconds)

  common_tags = {
    Project     = "audio-transcription"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_ecr_repository" "transcription" {
  name                 = local.repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = local.common_tags
}

resource "aws_ecs_cluster" "main" {
  name = local.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = local.log_group_name
  retention_in_days = var.log_retention_days
  tags              = local.common_tags
}

resource "aws_iam_role" "ecs_execution" {
  name               = "audiotrans-${var.environment}-ecs-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ecs_execution_managed" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task" {
  name               = "audiotrans-${var.environment}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json
  tags               = local.common_tags
}

resource "aws_iam_role_policy" "ecs_task_worker" {
  name   = "audiotrans-${var.environment}-ecs-worker-policy"
  role   = aws_iam_role.ecs_task.id
  policy = data.aws_iam_policy_document.worker_task_policy.json
}

resource "aws_security_group" "worker" {
  name        = "audiotrans-${var.environment}-worker-sg"
  description = "Security group for transcription worker tasks"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.common_tags
}

resource "aws_ecs_task_definition" "transcription" {
  family                   = local.task_family
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.task_cpu)
  memory                   = tostring(var.task_memory)
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "transcription-worker"
      image     = local.effective_worker_image
      essential = true
      environment = [
        { name = "AWS_REGION", value = var.aws_region },
        { name = "TRANSCRIPTION_QUEUE_URL", value = var.transcription_queue_url },
        { name = "NOTIFICATION_QUEUE_URL", value = var.notification_queue_url },
        { name = "AUDIO_BUCKET_NAME", value = var.audio_bucket_name },
        { name = "TRANSCRIPT_BUCKET_NAME", value = var.transcript_bucket_name },
        { name = "JOBS_TABLE_NAME", value = var.jobs_table_name },
        { name = "WHISPER_MODEL_ID", value = var.whisper_model_id },
        { name = "POLL_WAIT_SECONDS", value = local.effective_poll_wait_sec }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = local.common_tags
}

resource "aws_ecs_service" "transcription" {
  name            = local.service_name
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.transcription.arn
  launch_type     = "FARGATE"
  desired_count   = var.desired_count

  network_configuration {
    subnets          = local.effective_subnet_ids
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = true
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  tags = local.common_tags
}
