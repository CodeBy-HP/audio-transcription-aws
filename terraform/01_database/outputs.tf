output "users_table_name" {
  description = "Users table name."
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "Users table ARN."
  value       = aws_dynamodb_table.users.arn
}

output "jobs_table_name" {
  description = "Jobs table name."
  value       = aws_dynamodb_table.jobs.name
}

output "jobs_table_arn" {
  description = "Jobs table ARN."
  value       = aws_dynamodb_table.jobs.arn
}

output "next_step_note" {
  description = "MVP next step after database module is applied."
  value       = "Database module applied. Essential next step: set USERS_TABLE_NAME and JOBS_TABLE_NAME in .env from terraform outputs. Then run terraform in terraform/02_queues to create transcription/notification queues and DLQs."
}
