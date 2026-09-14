output "ecr_repository_url" {
  description = "Private ECR repository to receive the immutable backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "app_runner_service_url" {
  description = "App Runner HTTPS service URL; normally reached through CloudFront."
  value       = aws_apprunner_service.backend.service_url
}

output "frontend_bucket_name" {
  description = "Private S3 bucket for compiled frontend assets."
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID for frontend invalidations."
  value       = aws_cloudfront_distribution.application.id
}

output "cloudfront_domain_name" {
  description = "Generated public CloudFront domain name."
  value       = aws_cloudfront_distribution.application.domain_name
}

output "application_url" {
  description = "Generated public HTTPS application URL."
  value       = "https://${aws_cloudfront_distribution.application.domain_name}"
}
