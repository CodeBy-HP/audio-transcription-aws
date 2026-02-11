output "api_id" {
  description = "HTTP API ID."
  value       = aws_apigatewayv2_api.http.id
}

output "api_endpoint" {
  description = "HTTP API invoke URL."
  value       = aws_apigatewayv2_api.http.api_endpoint
}

output "api_lambda_name" {
  description = "API Lambda function name."
  value       = aws_lambda_function.api.function_name
}

output "api_lambda_arn" {
  description = "API Lambda function ARN."
  value       = aws_lambda_function.api.arn
}

output "next_step_note" {
  description = "MVP next step after API module is applied."
  value       = "Before API apply, run `python backend/api/package_docker.py` to create api_lambda.zip. After apply, set API endpoint for clients and proceed to terraform/05_workers."
}
