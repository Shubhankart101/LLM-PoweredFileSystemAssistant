# ==============================================================================
# Terraform Backend Configuration
# ==============================================================================
# This configuration configures remote state management for Terraform using
# an Amazon S3 bucket with state locking via Amazon DynamoDB to prevent
# concurrent state modifications during CI/CD or team deployments.
#
# Before running 'terraform init', ensure the S3 bucket and DynamoDB table exist.
# You can provision them via AWS CLI or an initial bootstrap module:
#
#   aws s3api create-bucket \
#     --bucket llm-fs-assistant-tfstate-<YOUR_ACCOUNT_ID> \
#     --region us-east-1
#
#   aws dynamodb create-table \
#     --table-name llm-fs-assistant-tflocks \
#     --attribute-definitions AttributeName=LockID,AttributeType=S \
#     --key-schema AttributeName=LockID,KeyType=HASH \
#     --billing-mode PAY_PER_REQUEST \
#     --region us-east-1
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"

  # Uncomment and configure the backend block below for production/remote state:
  # backend "s3" {
  #   bucket         = "llm-fs-assistant-tfstate-REPLACE_WITH_ACCOUNT_ID"
  #   key            = "environments/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "llm-fs-assistant-tflocks"
  # }
}
