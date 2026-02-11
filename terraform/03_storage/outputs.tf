output "audio_bucket_name" {
  description = "Audio upload bucket name."
  value       = aws_s3_bucket.audio.id
}

output "audio_bucket_arn" {
  description = "Audio upload bucket ARN."
  value       = aws_s3_bucket.audio.arn
}

output "transcript_bucket_name" {
  description = "Transcript output bucket name."
  value       = aws_s3_bucket.transcripts.id
}

output "transcript_bucket_arn" {
  description = "Transcript output bucket ARN."
  value       = aws_s3_bucket.transcripts.arn
}

output "next_step_note" {
  description = "MVP next step after storage module is applied."
  value       = "Storage module applied. Essential step: set AUDIO_BUCKET_NAME in .env from audio_bucket_name output. Then implement/apply terraform/04_api."
}

output "env_update_note" {
  description = "Environment variables to update after storage apply."
  value       = "Add to .env -> AUDIO_BUCKET_NAME=<audio_bucket_name>"
}
