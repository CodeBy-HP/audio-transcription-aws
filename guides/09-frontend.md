# 09 - Frontend (Static Next.js + S3 + CloudFront)

Run this only after backend E2E is passing.

## Goal

Deploy static frontend and connect it to API securely with CORS.

## Step 1 - Build-time frontend env

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL="https://<api-id>.execute-api.us-east-1.amazonaws.com"
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY="pk_test_..."
```

Note:

- `NEXT_PUBLIC_*` values are public by design.
- never put secrets (`CLERK_SECRET_KEY`, `SENDGRID_API_KEY`) in frontend env.

## Step 2 - Build static site

```powershell
Set-Location frontend
npm install
npm run build
```

Expected output: `frontend/out`

## Step 3 - Deploy frontend infra

```powershell
Set-Location ../terraform/07_frontend
Copy-Item terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

Capture outputs:

```powershell
terraform output
```

Required values:

- `frontend_bucket_name`
- `cloudfront_distribution_id`
- `cloudfront_domain_name`

## Step 4 - Update CORS allowlists with CloudFront URL

1. Add `https://<cloudfront_domain_name>` to:

- `terraform/03_storage/terraform.tfvars` -> `cors_allow_origins`
- `terraform/04_api/terraform.tfvars` -> `cors_allow_origins`

2. Re-apply both modules:

```powershell
terraform -chdir=../03_storage plan
terraform -chdir=../03_storage apply
terraform -chdir=../04_api plan
terraform -chdir=../04_api apply
```

## Step 5 - Upload static files and invalidate CDN cache

```powershell
Set-Location ../../frontend
aws s3 sync out/ s3://<frontend_bucket_name> --delete
aws cloudfront create-invalidation --distribution-id <cloudfront_distribution_id> --paths "/*"
```

## Step 6 - Validate production frontend

Open:

`https://<cloudfront_domain_name>`

Validate:

- Clerk login works
- dashboard loads jobs
- upload to S3 works
- polling updates status
- transcript appears when job is completed

## Redeploy UI Changes Later

After any frontend code change:

```powershell
Set-Location frontend
npm run build
aws s3 sync out/ s3://<frontend_bucket_name> --delete
aws cloudfront create-invalidation --distribution-id <cloudfront_distribution_id> --paths "/*"
```
