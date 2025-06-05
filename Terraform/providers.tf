terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Or your desired AWS provider version
    }
  }
}

# Provider for the primary region (e.g., where your main instance and SQS/SNS are)
provider "aws" {
  alias  = "primary"
  region = var.primary_aws_region
}

# Provider for the secondary region (e.g., where your backup instance will be)
provider "aws" {
  alias  = "secondary"
  region = var.secondary_aws_region
}
