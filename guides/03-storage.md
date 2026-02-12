# 03 - Storage (`terraform/03_storage`)

## Goal

Create:

- private S3 audio upload bucket
- private S3 transcript bucket
- S3 event notification from audio bucket to transcription SQS queue

## Commands

1. Create module tfvars:

```powershell
Copy-Item terraform/03_storage/terraform.tfvars.example terraform/03_storage/terraform.tfvars
```

2. Edit `terraform/03_storage/terraform.tfvars` and set:

- `transcription_queue_arn` from `02_queues`
- `transcription_queue_url` from `02_queues`

3. Apply module:

```powershell
terraform -chdir=terraform/03_storage init
terraform -chdir=terraform/03_storage plan
terraform -chdir=terraform/03_storage apply
```

4. Print outputs:

```powershell
terraform -chdir=terraform/03_storage output
```

## Update `.env` After This Step

Set:

```env
AUDIO_BUCKET_NAME="<terraform output audio_bucket_name>"
TRANSCRIPT_BUCKET_NAME="<terraform output transcript_bucket_name>"
```

## Keep These Outputs for Next Steps

- `audio_bucket_name`
- `audio_bucket_arn`
- `transcript_bucket_name`
- `transcript_bucket_arn`

## Quick Validation

```powershell
aws s3api head-bucket --bucket <audio_bucket_name>
aws s3api head-bucket --bucket <transcript_bucket_name>
```

Next: `guides/04-api-gateway-lambda.md`
