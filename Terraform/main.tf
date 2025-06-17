# --- Networking for Primary Region ---
data "aws_vpc" "primary_default" {
  provider = aws.primary # Specify provider
  default  = true
}

data "aws_subnets" "primary_default" {
  provider = aws.primary # Specify provider
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.primary_default.id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# --- Security Group for Main EC2 Instance (in Primary Region) ---
resource "aws_security_group" "main_ec2_sg" {
  provider    = aws.primary
  name        = "main-ec2-failover-sg"
  description = "Allow SSH and application traffic for main instance"
  vpc_id      = data.aws_vpc.primary_default.id

  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow HTTP traffic (Port 80)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow HTTPS traffic (Port 443)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow access on Port 3000 (e.g., Frontend Dev/App)"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow access on Port 5000 (e.g., Backend API)"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "Main EC2 SG (Primary Region)" }
}

# --- Main EC2 Instance (in Primary Region) ---
resource "aws_instance" "main" {
  provider               = aws.primary
  ami                    = var.main_instance_ami
  instance_type          = var.instance_type
  key_name               = var.main_instance_key_name != "" ? var.main_instance_key_name : null
  subnet_id              = element(data.aws_subnets.primary_default.ids, 0)
  vpc_security_group_ids = [aws_security_group.main_ec2_sg.id]

  tags = {
    Name        = "Main-EC2-Instance"
    Environment = "failover-pair"
    Region      = var.primary_aws_region
  }
}

# --- Networking for Secondary Region ---
data "aws_vpc" "secondary_default" {
  provider = aws.secondary
  default  = true
}

data "aws_subnets" "secondary_default" {
  provider = aws.secondary
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.secondary_default.id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

# --- Security Group for Backup EC2 Instance (in Secondary Region) ---
resource "aws_security_group" "backup_ec2_sg" {
  provider    = aws.secondary
  name        = "backup-ec2-failover-sg"
  description = "Allow SSH and application traffic for backup instance"
  vpc_id      = data.aws_vpc.secondary_default.id

  ingress {
    description = "SSH access"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow HTTP traffic (Port 80)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow HTTPS traffic (Port 443)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow access on Port 3000 (e.g., Frontend Dev/App)"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  ingress {
    description = "Allow access on Port 5000 (e.g., Backend API)"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # WARNING: Restrict this
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = { Name = "Backup EC2 SG (Secondary Region)" }
}

# --- Backup EC2 Instance (in Secondary Region) ---
resource "aws_instance" "backup" {
  provider               = aws.secondary
  ami                    = var.backup_instance_ami
  instance_type          = var.instance_type
  key_name               = var.backup_instance_key_name != "" ? var.backup_instance_key_name : null
  subnet_id              = element(data.aws_subnets.secondary_default.ids, 0)
  vpc_security_group_ids = [aws_security_group.backup_ec2_sg.id]

  tags = {
    Name        = "Backup-EC2-Instance"
    Environment = "failover-pair"
    Region      = var.secondary_aws_region
  }
}

# --- IAM Policy (Global) ---
resource "aws_iam_policy" "home_server_ec2_manager_policy" {
  provider    = aws.primary # IAM is global, but provider assignment is good practice
  name        = "HomeServerEC2ManagerPolicyMultiRegion"
  description = "Allows describing EC2/CloudWatch, starting/stopping EC2 for failover."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { # EC2 and CloudWatch read permissions
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "cloudwatch:DescribeAlarms",
          "cloudwatch:GetMetricStatistics"
        ]
        Resource = "*"
      },
      { # EC2 start/stop permissions
        Effect = "Allow"
        Action = [
          "ec2:StartInstances",
          "ec2:StopInstances"
        ]
        Resource = "*" # Scope down with conditions if possible.
      }
    ]
  })
  tags = { Purpose = "FailoverAutomation" }
}

# --- CloudWatch Alarm for Main Instance Health (in Primary Region) ---
resource "aws_cloudwatch_metric_alarm" "main_instance_unhealthy" {
  provider            = aws.primary
  alarm_name          = "MainInstanceUnhealthyAlarm"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "StatusCheckFailed_System"
  namespace           = "AWS/EC2"
  period              = "60" # seconds
  statistic           = "Minimum"
  threshold           = "1"
  alarm_description   = "Alarm when the main EC2 instance (primary region) fails system status checks"
  treat_missing_data  = "breaching" # Treat missing data as breaching (instance might be down)

  dimensions = {
    InstanceId = aws_instance.main.id
  }

  # NOTE: alarm_actions and ok_actions are now empty as SNS is removed.
  # If you need notifications, you'll need to re-add SNS or another notification method.
  alarm_actions = []
  ok_actions    = []
}


# --- Outputs ---
output "main_instance_id" {
  description = "ID of the Main EC2 instance"
  value       = aws_instance.main.id
}
output "main_instance_public_ip" {
  description = "Public IP of the Main EC2 instance"
  value       = aws_instance.main.public_ip
}
output "main_instance_region" {
  description = "AWS Region of the Main EC2 instance"
  value       = var.primary_aws_region
}

output "backup_instance_id" {
  description = "ID of the Backup EC2 instance"
  value       = aws_instance.backup.id
}
output "backup_instance_public_ip" {
  description = "Public IP of the Backup EC2 instance"
  value       = aws_instance.backup.public_ip
}
output "backup_instance_region" {
  description = "AWS Region of the Backup EC2 instance"
  value       = var.secondary_aws_region
}

output "home_server_iam_policy_arn" {
  description = "ARN of the IAM policy for the home server"
  value       = aws_iam_policy.home_server_ec2_manager_policy.arn
}