output "transcription_queue_name" {
  description = "Transcription queue name."
  value       = aws_sqs_queue.transcription.name
}

output "transcription_queue_url" {
  description = "Transcription queue URL."
  value       = aws_sqs_queue.transcription.id
}

output "transcription_queue_arn" {
  description = "Transcription queue ARN."
  value       = aws_sqs_queue.transcription.arn
}

output "transcription_dlq_name" {
  description = "Transcription dead-letter queue name."
  value       = aws_sqs_queue.transcription_dlq.name
}

output "transcription_dlq_arn" {
  description = "Transcription dead-letter queue ARN."
  value       = aws_sqs_queue.transcription_dlq.arn
}

output "notification_queue_name" {
  description = "Notification queue name."
  value       = aws_sqs_queue.notification.name
}

output "notification_queue_url" {
  description = "Notification queue URL."
  value       = aws_sqs_queue.notification.id
}

output "notification_queue_arn" {
  description = "Notification queue ARN."
  value       = aws_sqs_queue.notification.arn
}

output "notification_dlq_name" {
  description = "Notification dead-letter queue name."
  value       = aws_sqs_queue.notification_dlq.name
}

output "notification_dlq_arn" {
  description = "Notification dead-letter queue ARN."
  value       = aws_sqs_queue.notification_dlq.arn
}

output "next_step_note" {
  description = "MVP next step after queues module is applied."
  value       = "Queues module applied. Essential step: set TRANSCRIPTION_QUEUE_URL and NOTIFICATION_QUEUE_URL in .env from queue outputs. Then run terraform in terraform/03_storage and connect S3 ObjectCreated events to transcription_queue_arn."
}

output "env_update_note" {
  description = "Environment variables to update after queues apply."
  value       = "Add to .env -> TRANSCRIPTION_QUEUE_URL=<transcription_queue_url>, NOTIFICATION_QUEUE_URL=<notification_queue_url>"
}
