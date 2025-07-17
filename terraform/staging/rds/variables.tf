variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-2"
}

variable "db_identifier" {
  description = "RDS identifier"
  type        = string
  default     = "analytics-staging"
}

variable "db_name" {
  description = "Initial database name to create"
  type        = string
  default     = "analytics"
}

variable "master_username" {
  description = "admin username"
  type        = string
  default     = "analytics_staging"
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "17.5"
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.medium"
}

variable "multi_az" {
  description = "Create a Multi‑AZ standby"
  type        = bool
  default     = false
}

variable "project_name" {
  description = "Main project name"
  type        = string
  default     = "analytics"
}

variable "vpc_cidr" {
  description = "Parent IPv4 CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}