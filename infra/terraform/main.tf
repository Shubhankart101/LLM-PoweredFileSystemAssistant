terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.app_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# 1. VPC & Networking Module
module "vpc" {
  source = "../modules/vpc"

  app_name             = var.app_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  enable_nat_gateway   = var.enable_nat_gateway
}

# 2. S3 Storage Module
module "s3" {
  source = "../modules/s3"

  app_name      = var.app_name
  environment   = var.environment
  bucket_prefix = var.app_name
}

# 3. Secrets Management Module
module "secrets" {
  source = "../modules/secrets"

  app_name    = var.app_name
  environment = var.environment
}

# 4. ECS Fargate Compute & Load Balancing Module
module "ecs" {
  source = "../modules/ecs"

  app_name              = var.app_name
  environment           = var.environment
  aws_region            = var.aws_region
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.vpc.ecs_security_group_id
  alb_security_group_id = module.vpc.alb_security_group_id
  container_image       = var.container_image
  container_port        = var.container_port
  cpu                   = var.cpu
  memory                = var.memory
  desired_count         = var.desired_count
  s3_bucket_arn         = module.s3.bucket_arn
  secrets_arn           = module.secrets.secret_arn
  log_group_name        = "/ecs/${var.app_name}-${var.environment}"
}

# 5. Monitoring & Alarms Module
module "monitoring" {
  source = "../modules/monitoring"

  app_name                = var.app_name
  environment             = var.environment
  log_retention_days      = var.log_retention_days
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_service_name        = module.ecs.service_name
  target_group_arn_suffix = module.ecs.target_group_arn_suffix
  alb_arn_suffix          = module.ecs.alb_arn_suffix
}
