variable "primary_aws_region" {
  description = "AWS region for the PRIMARY EC2 instance"
  type        = string
  default     = "eu-west-2" # Example: London
}

variable "secondary_aws_region" {
  description = "AWS region for the SECONDARY (backup) EC2 instance"
  type        = string
  default     = "eu-west-1" # Example: Ireland
}

variable "main_instance_ami" {
  description = "AMI ID for the main EC2 instance (e.g., Ubuntu, in primary_aws_region)"
  type        = string
  default     = "ami-044415bb13eee2391" # Example: Ubuntu Server 24.04 in London
}

variable "backup_instance_ami" {
  description = "AMI ID for the backup EC2 instance (e.g., Ubuntu, in secondary_aws_region)"
  type        = string
  default     = "ami-01f23391a59163da9" # Example: Ubuntu Server 24.04 in Ireland
}

variable "instance_type" {
  description = "EC2 instance type for both main and backup instances"
  type        = string
  default     = "t2.micro"
}

variable "main_instance_key_name" {
  description = "Name of the EC2 key pair in primary_aws_region for the MAIN instance (for SSH access)"
  type        = string
  default     = "" # If empty, instance launched without a key pair
}

variable "backup_instance_key_name" {
  description = "Name of the EC2 key pair in secondary_aws_region for the BACKUP instance (for SSH access)"
  type        = string
  default     = "" # If empty, instance launched without a key pair
}

variable "home_server_monitoring_entity_name" {
  description = "Name of the IAM user or role your home server uses (for IAM policy description)"
  type        = string
  default     = "HomeServerMonitoringUser"
}