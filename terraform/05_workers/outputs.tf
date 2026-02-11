output "worker_ecr_repository_url" {
  description = "ECR repository URL for the transcription worker image."
  value       = aws_ecr_repository.transcription.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS transcription worker service name."
  value       = aws_ecs_service.transcription.name
}

output "worker_task_definition_arn" {
  description = "ECS task definition ARN for transcription worker."
  value       = aws_ecs_task_definition.transcription.arn
}

output "next_step_note" {
  description = "MVP next step after workers module is applied."
  value       = "Workers infra applied. Build/push backend/worker image to worker_ecr_repository_url, then set desired_count to 1+ and apply again. Next module: notifications."
}
