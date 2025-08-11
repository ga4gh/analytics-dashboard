terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }
  backend "s3" {
    bucket = "ga4gh-analytics-dashboard-terraform-state"
    key    = "staging/rds.tfstate"
    region = "us-east-2"
  }

  required_version = ">= 1.3.0"
}
