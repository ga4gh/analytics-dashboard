provider "aws" {
  region = var.region
}

data "aws_availability_zones" "available" {}

locals {
  vpc_cidr      = var.vpc_cidr            # e.g. 10.0.0.0/16
  subnet_bits   = 4                       # /16 + 4 = /20
  public_count  = 3
  private_count = 3

  public_subnets = [
    for i in range(local.public_count) :
      cidrsubnet(local.vpc_cidr, local.subnet_bits, i)
  ]

  private_subnets = [
    for i in range(local.private_count) :
      cidrsubnet(local.vpc_cidr, local.subnet_bits, local.public_count + i)
  ]
}

resource "random_password" "master" {
  length  = 20
  special = true
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "6.0.0"

  name                 = var.project_name
  cidr                 = var.vpc_cidr
  azs                  = slice(data.aws_availability_zones.available.names, 0, 3)
  public_subnets       = local.public_subnets
  private_subnets      = local.private_subnets
  enable_dns_hostnames = true
  enable_dns_support   = true
}


resource "aws_security_group" "postgres" {
  name        = "${var.db_identifier}-sg"
  description = "Ingress for Postgres"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Postgres from VPC"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "postgres" {
  name       = "${var.db_identifier}-subnet-group"
  subnet_ids = module.vpc.public_subnets
  tags = {
    Name = "${var.db_identifier}-subnet-group"
  }
}

resource "aws_db_instance" "postgres" {
  identifier              = var.db_identifier
  allocated_storage       = 20                # GiB
  max_allocated_storage   = 100               # autoscaling
  storage_type            = "gp3"

  engine                  = "postgres"
  engine_version          = var.engine_version
  instance_class          = var.instance_class

  db_name                 = var.db_name
  username                = var.master_username
  password                = random_password.master.result

  db_subnet_group_name    = aws_db_subnet_group.postgres.name
  vpc_security_group_ids  = [aws_security_group.postgres.id]

  multi_az                = var.multi_az
  publicly_accessible     = true # set to false in production!
  storage_encrypted       = true
  auto_minor_version_upgrade = true
  backup_retention_period = 7

  skip_final_snapshot     = true  # set to false in production!

  tags = {
    Name = var.db_identifier
    Terraform = "true"
  }
}
