# Audio Transcription AWS MVP - Step-by-Step Runbook

This folder is the exact replication guide for this repository.

Follow these files in this exact order:

1. `guides/01-database.md`
2. `guides/02-queues.md`
3. `guides/03-storage.md`
4. `guides/04-api-gateway-lambda.md`
5. `guides/05-workers.md`
6. `guides/06-notifications.md`
7. `guides/07-end-to-end-validation.md`
8. `guides/09-frontend.md`

## What You Deploy

- `terraform/01_database`: DynamoDB tables (`users`, `jobs`)
- `terraform/02_queues`: SQS queues + DLQs
- `terraform/03_storage`: S3 audio/transcript buckets + S3 -> SQS notification
- `terraform/04_api`: FastAPI Lambda + API Gateway HTTP API
- `terraform/05_workers`: ECS Fargate worker + ECR image repository
- `terraform/06_notifications`: SQS-triggered notification Lambda + SES
- `terraform/07_frontend`: S3 + CloudFront for static frontend hosting

## Before You Start

Install and verify:

```powershell
aws --version
terraform version
python --version
docker --version
uv --version
node --version
npm --version
```

Also ensure:

- AWS CLI is configured to the correct account.
- Docker Desktop is running.
- Clerk project exists (publishable key, secret key, issuer/JWKS URL).

Quick identity check:

```powershell
aws sts get-caller-identity
```

## Global Rules (Important)

- Never hardcode ARNs/URLs in code.
- Always copy Terraform outputs into next module `terraform.tfvars`.
- After each Terraform module, update `.env`.
- For Lambda packaging, always run:
  - `python backend/api/package_docker.py`
  - `python backend/notify/docker_package.py`
- Worker deployment is intentionally 2-pass:
  - pass 1 create infra with `desired_count = 0`
  - pass 2 push image and set `desired_count = 1`

## One-Time `.env` Baseline

Start from:

```powershell
Copy-Item .env.example .env
```

Then fill values step-by-step as each guide instructs.
