output "notification_lambda_name" {
  description = "Notification worker Lambda function name."
  value       = aws_lambda_function.notification_worker.function_name
}

output "notification_lambda_arn" {
  description = "Notification worker Lambda function ARN."
  value       = aws_lambda_function.notification_worker.arn
}

output "ses_sender_identity_arn" {
  description = "SES sender identity ARN."
  value       = aws_ses_email_identity.sender.arn
}

output "next_step_note" {
  description = "MVP next step after notifications module is applied."
  value       = "Notifications module applied. Verify SES sender email, then test by sending a message to notification_queue_url and checking Lambda CloudWatch logs."
}

output "env_update_note" {
  description = "Environment variables to keep in sync for local testing."
  value       = "Add/keep in .env -> SENDER_EMAIL=<verified email>, TRANSCRIPT_BUCKET_NAME=<transcript_bucket_name>"
}
