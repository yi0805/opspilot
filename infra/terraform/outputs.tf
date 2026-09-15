output "ecr_repository_url" {
  description = "Private ECR repository to receive the immutable backend image."
  value       = aws_ecr_repository.backend.repository_url
}

output "lambda_function_name" {
  description = "Lambda function name for operational verification."
  value       = aws_lambda_function.backend.function_name
}

output "lambda_function_url" {
  description = "Public Lambda Function URL; CloudFront is the intended application entry point."
  value       = aws_lambda_function_url.backend.function_url
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
  description = "Generated CloudFront HTTPS application URL."
  value       = "https://${aws_cloudfront_distribution.application.domain_name}"
}
