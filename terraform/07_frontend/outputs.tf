output "frontend_bucket_name" {
  description = "S3 bucket used for static frontend files."
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_domain_name" {
  description = "CloudFront domain for frontend access."
  value       = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID."
  value       = aws_cloudfront_distribution.frontend.id
}

output "next_step_note" {
  description = "Manual steps to build and upload static frontend, then align CORS."
  value       = "Build frontend with NEXT_PUBLIC_* envs, upload frontend/out/* to S3 bucket, invalidate CloudFront, then add CloudFront URL to cors_allow_origins in terraform/03_storage and terraform/04_api."
}
