terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Or your desired AWS provider version
    }
  }
}

# Provider for the primary region
provider "aws" {
  alias  = "primary"
  region = var.primary_aws_region
  profile = "primary"
}

# Provider for the secondary region
provider "aws" {
  alias  = "secondary"
  region = var.secondary_aws_regio
  profile = "secondary"
}