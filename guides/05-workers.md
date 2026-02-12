# 05 - Worker Service (`terraform/05_workers`)

## Goal

Run transcription worker on ECS Fargate using image from ECR.

## Runtime for MVP

- model: `openai/whisper-tiny`
- compute: CPU
- launch type: Fargate

## Commands

1. Create module tfvars:

```powershell
Copy-Item terraform/05_workers/terraform.tfvars.example terraform/05_workers/terraform.tfvars
```

2. Edit `terraform/05_workers/terraform.tfvars` with outputs from:

- `01_database` (`jobs_table_name`, `jobs_table_arn`)
- `02_queues` (`transcription_queue_*`, `notification_queue_*`)
- `03_storage` (`audio_bucket_*`, `transcript_bucket_*`)

For first run keep:

```hcl
desired_count    = 0
worker_image_uri = ""
```

3. First apply (creates ECR + ECS infra only):

```powershell
terraform -chdir=terraform/05_workers init
terraform -chdir=terraform/05_workers plan
terraform -chdir=terraform/05_workers apply
```

4. Get ECR URL:

```powershell
terraform -chdir=terraform/05_workers output -raw worker_ecr_repository_url
```

5. Update `.env` before image push:

```env
WHISPER_MODEL_ID="openai/whisper-tiny"
WORKER_ECR_REPOSITORY_URL="<terraform output worker_ecr_repository_url>"
WORKER_IMAGE_TAG="latest"
```

6. Build and push worker image:

```powershell
powershell -ExecutionPolicy Bypass -File backend/worker/docker_package.ps1
```

7. Edit `terraform/05_workers/terraform.tfvars` for second run:

```hcl
worker_image_uri = "<worker_ecr_repository_url>:latest"
desired_count    = 1
```

8. Second apply (starts worker tasks):

```powershell
terraform -chdir=terraform/05_workers plan
terraform -chdir=terraform/05_workers apply
```

## Quick Validation

```powershell
aws ecs describe-services --cluster <ecs_cluster_name> --services <ecs_service_name> --region us-east-1
```

Check `runningCount` is `1` or more.

Next: `guides/06-notifications.md`
