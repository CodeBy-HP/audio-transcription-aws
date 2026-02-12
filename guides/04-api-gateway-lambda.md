# 04 - API Gateway + API Lambda (`terraform/04_api`)

## Goal

Deploy FastAPI as Lambda behind API Gateway HTTP API.

## Commands

1. Ensure `.env` has:

```env
CLERK_JWKS_URL="https://<your-clerk-domain>/.well-known/jwks.json"
AWS_REGION="us-east-1"
PRESIGNED_EXPIRES_SECONDS="900"
MAX_FILE_SIZE_BYTES="104857600"
```

2. Build Lambda zip (Docker-based for Linux-compatible dependencies):

```powershell
python backend/api/package_docker.py
```

Expected file: `backend/api/api_lambda.zip`

3. Create module tfvars:

```powershell
Copy-Item terraform/04_api/terraform.tfvars.example terraform/04_api/terraform.tfvars
```

4. Edit `terraform/04_api/terraform.tfvars` and fill from previous outputs:

- `users_table_name`, `users_table_arn`
- `jobs_table_name`, `jobs_table_arn`
- `audio_bucket_name`, `audio_bucket_arn`
- `clerk_jwks_url`
- `lambda_zip_path = "../../backend/api/api_lambda.zip"`

Important: do not set reserved Lambda env keys (example: do not set `AWS_REGION` inside Lambda env map in tfvars).

5. Apply module:

```powershell
terraform -chdir=terraform/04_api init
terraform -chdir=terraform/04_api plan
terraform -chdir=terraform/04_api apply
```

6. Print outputs:

```powershell
terraform -chdir=terraform/04_api output
```

## Update `.env` After This Step

Set:

```env
API_BASE_URL="<terraform output api_endpoint>"
```

## Quick Validation

```powershell
curl "<api_endpoint>/health"
```

Next: `guides/05-workers.md`
