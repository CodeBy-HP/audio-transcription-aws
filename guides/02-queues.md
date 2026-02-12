# 02 - Queues (`terraform/02_queues`)

## Goal

Create queue backbone:

- transcription queue + DLQ
- notification queue + DLQ

## Commands

1. Create module tfvars:

```powershell
Copy-Item terraform/02_queues/terraform.tfvars.example terraform/02_queues/terraform.tfvars
```

2. Apply module:

```powershell
terraform -chdir=terraform/02_queues init
terraform -chdir=terraform/02_queues plan
terraform -chdir=terraform/02_queues apply
```

3. Print outputs:

```powershell
terraform -chdir=terraform/02_queues output
```

## Update `.env` After This Step

Set:

```env
TRANSCRIPTION_QUEUE_URL="<terraform output transcription_queue_url>"
NOTIFICATION_QUEUE_URL="<terraform output notification_queue_url>"
```

## Keep These Outputs for Next Steps

- `transcription_queue_url`
- `transcription_queue_arn`
- `notification_queue_url`
- `notification_queue_arn`

## Quick Validation

```powershell
aws sqs get-queue-attributes --queue-url <transcription_queue_url> --attribute-names QueueArn --region us-east-1
aws sqs get-queue-attributes --queue-url <notification_queue_url> --attribute-names QueueArn --region us-east-1
```

Next: `guides/03-storage.md`
