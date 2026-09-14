variable "aws_region" {
  description = "AWS region for the OpsPilot deployment."
  type        = string
  default     = "ap-southeast-2"
}

variable "project_name" {
  description = "Short name used to identify deployment resources."
  type        = string
  default     = "opspilot"
}

variable "backend_image_tag" {
  description = "Immutable Git commit SHA tag of the backend image already pushed to ECR."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{7,40}$", var.backend_image_tag))
    error_message = "backend_image_tag must be a 7-40 character lowercase Git commit SHA."
  }
}
