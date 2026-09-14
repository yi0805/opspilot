data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

locals {
  name                      = var.project_name
  lambda_function_name      = "${var.project_name}-backend"
  openai_ssm_parameter_name = "/opspilot/prod/openai-api-key"
  openai_ssm_parameter_arn  = "arn:${data.aws_partition.current.partition}:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter${local.openai_ssm_parameter_name}"
  common_tags = {
    Project     = "OpsPilot"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

resource "aws_ecr_repository" "backend" {
  name                 = "${local.name}-backend"
  force_delete         = true
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

resource "aws_ecr_lifecycle_policy" "backend" {
  repository = aws_ecr_repository.backend.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Retain only the five most recent backend images."
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

data "aws_iam_policy_document" "lambda_ecr_pull" {
  statement {
    sid = "AllowLambdaImageRetrieval"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer",
    ]
    resources = [aws_ecr_repository.backend.arn]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "AWS:SourceArn"
      values   = ["arn:${data.aws_partition.current.partition}:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:${local.lambda_function_name}"]
    }
  }
}

resource "aws_ecr_repository_policy" "lambda_pull" {
  repository = aws_ecr_repository.backend.name
  policy     = data.aws_iam_policy_document.lambda_ecr_pull.json
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${local.name}-lambda-execution"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.common_tags
}

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/lambda/${local.lambda_function_name}"
  retention_in_days = 7
  tags              = local.common_tags
}

data "aws_iam_policy_document" "lambda_execution" {
  statement {
    sid = "WriteFunctionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.backend.arn}:*"]
  }

  statement {
    sid       = "ReadOpenAiParameter"
    actions   = ["ssm:GetParameter"]
    resources = [local.openai_ssm_parameter_arn]
  }
}

resource "aws_iam_role_policy" "lambda_execution" {
  name   = "${local.name}-lambda-execution"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_execution.json
}

resource "aws_lambda_function" "backend" {
  function_name                  = local.lambda_function_name
  package_type                   = "Image"
  image_uri                      = "${aws_ecr_repository.backend.repository_url}:${var.backend_image_tag}"
  role                           = aws_iam_role.lambda_execution.arn
  architectures                  = ["x86_64"]
  memory_size                    = 512
  timeout                        = 110
  reserved_concurrent_executions = 1

  environment {
    variables = {
      APP_ENV                   = "production"
      DATABASE_URL              = "sqlite:////tmp/opspilot.db"
      OPENAI_MODEL              = "gpt-5.6-luna"
      OPENAI_SSM_PARAMETER_NAME = local.openai_ssm_parameter_name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.backend,
    aws_ecr_repository_policy.lambda_pull,
    aws_iam_role_policy.lambda_execution,
  ]

  tags = local.common_tags
}

resource "aws_lambda_function_url" "backend" {
  function_name      = aws_lambda_function.backend.function_name
  authorization_type = "NONE"
  invoke_mode        = "BUFFERED"
}

resource "aws_lambda_permission" "public_function_url" {
  statement_id           = "AllowPublicFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.backend.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "public_function_url_invoke" {
  statement_id             = "AllowPublicInvocationThroughFunctionUrl"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.backend.function_name
  principal                = "*"
  invoked_via_function_url = true
}

resource "aws_s3_bucket" "frontend" {
  bucket_prefix = "${local.name}-frontend-"
  force_destroy = false

  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket                  = aws_s3_bucket.frontend.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name}-frontend-s3"
  description                       = "CloudFront access to the private OpsPilot frontend bucket."
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_cache_policy" "static" {
  name        = "${local.name}-static"
  comment     = "Normal caching for versioned Vite assets."
  default_ttl = 86400
  max_ttl     = 31536000
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config { cookie_behavior = "none" }
    headers_config { header_behavior = "none" }
    query_strings_config { query_string_behavior = "none" }
  }
}

resource "aws_cloudfront_cache_policy" "api" {
  name        = "${local.name}-api-no-cache"
  comment     = "Disable CloudFront caching for dynamic agent responses."
  default_ttl = 0
  max_ttl     = 0
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config { cookie_behavior = "none" }
    headers_config { header_behavior = "none" }
    query_strings_config { query_string_behavior = "none" }
  }
}

resource "aws_cloudfront_origin_request_policy" "api" {
  name    = "${local.name}-api-forward-without-host"
  comment = "Forward API request data without forwarding the viewer Host header to Lambda."

  cookies_config { cookie_behavior = "all" }

  headers_config {
    header_behavior = "allExcept"
    headers { items = ["host"] }
  }

  query_strings_config { query_string_behavior = "all" }
}

resource "aws_cloudfront_distribution" "application" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "OpsPilot frontend and API"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"

  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "frontend-s3"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  origin {
    domain_name = trimsuffix(
      trimprefix(aws_lambda_function_url.backend.function_url, "https://"),
      "/",
    )
    origin_id = "backend-lambda-url"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "https-only"
      origin_read_timeout      = 120
      origin_keepalive_timeout = 60
      origin_ssl_protocols     = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "frontend-s3"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.static.id
    compress               = true
  }

  ordered_cache_behavior {
    path_pattern             = "/api/*"
    target_origin_id         = "backend-lambda-url"
    viewer_protocol_policy   = "redirect-to-https"
    allowed_methods          = ["GET", "HEAD", "OPTIONS", "PUT", "PATCH", "POST", "DELETE"]
    cached_methods           = ["GET", "HEAD"]
    cache_policy_id          = aws_cloudfront_cache_policy.api.id
    origin_request_policy_id = aws_cloudfront_origin_request_policy.api.id
    compress                 = true
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate { cloudfront_default_certificate = true }

  tags = local.common_tags
}

data "aws_iam_policy_document" "frontend_bucket" {
  statement {
    sid       = "AllowCloudFrontReadOnly"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.application.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket.json
}
