# 06 - Notifications (`terraform/06_notifications`)

## Goal

Deploy notification Lambda that consumes notification queue and emails user.

## Commands

1. Verify SES sender identity in `us-east-1`.

If SES account is in sandbox:

- sender must be verified
- recipient must also be verified

2. Build notification Lambda zip:

```powershell
python backend/notify/docker_package.py
```

Expected file: `backend/notify/notify_lambda.zip`

3. Create module tfvars:

```powershell
Copy-Item terraform/06_notifications/terraform.tfvars.example terraform/06_notifications/terraform.tfvars
```

4. Edit `terraform/06_notifications/terraform.tfvars` with outputs from:

- `01_database` (users/jobs table names + ARNs)
- `02_queues` (notification queue URL + ARN)
- `03_storage` (transcript bucket name + ARN)

Set:

```hcl
sender_email    = "<verified-email>"
lambda_zip_path = "../../backend/notify/notify_lambda.zip"
```

5. Apply module:

```powershell
terraform -chdir=terraform/06_notifications init
terraform -chdir=terraform/06_notifications plan
terraform -chdir=terraform/06_notifications apply
```

## Update `.env` After This Step

Set:

```env
SENDER_EMAIL="<verified-email>"
DOWNLOAD_URL_TTL_SECONDS="86400"
```

If using SendGrid fallback:

```env
SENDGRID_API_KEY="<sendgrid-api-key>"
```

## Quick Validation

```powershell
aws lambda get-function --function-name <notification_lambda_name> --region us-east-1
```

Next: `guides/07-end-to-end-validation.md`
