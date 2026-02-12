# 01 - Database (`terraform/01_database`)

## Goal

Create DynamoDB tables used by the whole app:

- `users` table (PK: `clerk_user_id`)
- `jobs` table (PK: `clerk_user_id`, SK: `job_id`)

## Commands

1. Create module tfvars:

```powershell
Copy-Item terraform/01_database/terraform.tfvars.example terraform/01_database/terraform.tfvars
```

2. Open `terraform/01_database/terraform.tfvars` and set:

```hcl
aws_region                 = "us-east-1"
environment                = "dev"
enable_deletion_protection = false
```

3. Apply module:

```powershell
terraform -chdir=terraform/01_database init
terraform -chdir=terraform/01_database plan
terraform -chdir=terraform/01_database apply
```

4. Print outputs:

```powershell
terraform -chdir=terraform/01_database output
```

## Update `.env` After This Step

Set:

```env
USERS_TABLE_NAME="<terraform output users_table_name>"
JOBS_TABLE_NAME="<terraform output jobs_table_name>"
```

## Keep These Outputs for Next Steps

- `users_table_name`
- `users_table_arn`
- `jobs_table_name`
- `jobs_table_arn`

## Quick Validation

```powershell
aws dynamodb describe-table --table-name <users_table_name> --region us-east-1
aws dynamodb describe-table --table-name <jobs_table_name> --region us-east-1
```

Next: `guides/02-queues.md`
