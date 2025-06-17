# Multi-Region Disaster Recovery Dashboard & Failover System

This project provides a comprehensive, multi-region disaster recovery (DR) solution featuring a web-based dashboard for monitoring, controlling and automating a failover mechanism for AWS EC2 instances. The infrastructure is defined using Terraform, the dashboard is built with React and Flask, and the automated failover is handled by a reactive Python script on a home server or management node.

---

## Architecture

The system is composed of four main parts:

1.  **Infrastructure (Terraform):** Manages all AWS resources, including a primary EC2 instance, a backup EC2 instance in a separate region, security groups, a CloudWatch alarm for health monitoring, an SNS topic for notifications, and an SQS queue for reactive event handling.
2.  **Dashboard (React Frontend & Flask Backend):** A Dockerized web application that provides a real-time view of your instances' status, CPU usage, and uptime across different regions. It allows for manual start/stop actions.
3.  **Monitoring & Alerting (AWS CloudWatch & SNS):** A CloudWatch alarm continuously monitors the health of the primary EC2 instance. Upon failure, it triggers an SNS notification.
4.  **Failover Handler (Python & SQS):** A Python script, designed to run on a separate management node (like a home server), polls an SQS queue. When an SNS failure notification is received in the queue, this script automatically starts the backup EC2 instance.

---

## 🚀 Features

* **Multi-Region DR:** Primary and backup EC2 instances provisioned in separate AWS regions for high availability.
* **Infrastructure as Code (IaC):** All AWS resources are managed declaratively using **Terraform**.
* **Automated Failover:** A **Python script** listens to an **SQS queue** and automatically starts the backup instance when the primary instance fails (as detected by CloudWatch Alarms).
* **Real-time Monitoring Dashboard:** A **React** frontend displays status, uptime, and CPU usage for all managed instances.
* **API Layer:** A **Flask** backend provides a clean API for the frontend to interact with AWS resources.
* **Containerized Application:** The dashboard frontend and backend are Dockerized for easy and consistent deployment via **Docker Compose**.

---

## 📁 Project Structure

```
DisasterRecoveryDashboard/
├── Terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── providers.tf
│   └── terraform.tfvars.example
├── Backend/
│   ├── flaskBackend.py
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── Frontend/
│   ├── src/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── Failover/
│   └── failover_handler.py
└── docker-compose.yml
```

---

## 🛠️ Setup & Deployment Guide

Follow these steps in order to provision the infrastructure and run the applications.

### **Part 1: Provision AWS Infrastructure with Terraform**

This step creates all the necessary AWS resources (EC2, SQS, SNS, etc.).

**Prerequisites:**
* [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) installed.
* [AWS CLI](https://aws.amazon.com/cli/) installed and configured with your AWS credentials (`aws configure`). The credentials need permissions to create EC2, VPC, IAM, SNS, SQS, and CloudWatch resources.

**Steps:**
1.  Navigate to the Terraform directory: `cd DisasterRecoveryDashboard/Terraform`
2.  Create a `terraform.tfvars` file by copying the example: `cp terraform.tfvars.example terraform.tfvars`
3.  **Edit `terraform.tfvars`** and provide values for your setup:
    * `primary_aws_region` & `secondary_aws_region`
    * `main_instance_ami` & `backup_instance_ami` (ensure these AMIs are valid for their respective regions).
    * `main_instance_key_name` & `backup_instance_key_name` (these EC2 key pairs must already exist in their respective regions).
    * `sns_notification_email` (optional, for email alerts).
4.  Initialize Terraform:
    ```bash
    terraform init
    ```
5.  Review the execution plan:
    ```bash
    terraform plan -out=tfplan
    ```
6.  Apply the configuration to create the resources:
    ```bash
    terraform apply tfplan
    ```
7.  **Take note of the output values**, especially the instance IDs, region names, and the `failover_sqs_queue_url`. You will need these for the next steps.
8.  **Attach IAM Policy (Manual Step):**
    * The `home_server_iam_policy_arn` from the Terraform output needs to be attached to the IAM User or Role that your Home Server / Failover Handler script will use.

### **Part 2: Run the Monitoring Dashboard (Docker)**

This runs the React frontend and Flask backend.

**Prerequisites:**
* [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/) installed.

**Steps:**
1.  Navigate to the `Backend/` directory: `cd ../Backend`
2.  Create a `.env` file for the backend: `cp .env.example .env`
3.  **Edit `Backend/.env`** and fill in the instance IDs and regions using the output from your `terraform apply` command.
4.  Navigate back to the project root: `cd ..`
5.  Build and run the Docker containers:
    ```bash
    docker-compose up -d --build
    ```
6.  **Access the Dashboard:**
    * **Frontend**: [http://localhost:3000](http://localhost:3000) (or your configured frontend port)
    * **Backend API**: [http://localhost:5000/api](http://localhost:5000/api)

### **Part 3: Run the Failover Handler Script**

This script runs on your separate management node (e.g., a Home Server, Raspberry Pi, etc.) and performs the automated failover.

**Prerequisites:**
* Python 3 installed.
* AWS Credentials configured on the machine (via `aws configure`), attached to the IAM policy created by Terraform.

**Steps:**
1.  Navigate to the Failover directory: `cd Failover/`
2.  Install required Python packages:
    ```bash
    pip install boto3 python-dotenv
    ```
3.  **Set Environment Variables:** Before running the script, set the following environment variables in your terminal. Use the output values from your `terraform apply` command.
    ```bash
    # For Linux/macOS
    export FAILOVER_SQS_QUEUE_URL="<your_sqs_queue_url_from_terraform_output>"
    export BACKUP_INSTANCE_ID="<your_backup_instance_id_from_terraform_output>"
    export BACKUP_INSTANCE_REGION="<your_backup_instance_region_from_terraform_output>"
    export AWS_REGION_FOR_SCRIPT="<your_primary_aws_region_from_terraform>"
    export PRIMARY_ALARM_NAME="MainInstanceUnhealthyAlarm"
    ```
4.  Run the handler script. For continuous operation, it's best to run it as a background service (e.g., using `systemd` or `screen`).
    ```bash
    python failover_handler.py
    ```

---

## 📊 API Endpoints (Multi-Instance)

* **GET** `/api/cpu`: Returns CPU utilization for all managed EC2 instances.
* **GET** `/api/uptime`: Returns uptime and status for all managed EC2 instances.
* **POST** `/api/start?instance_id=<ID>&region=<REGION>`: Starts a specific EC2 instance.
* **POST** `/api/stop?instance_id=<ID>&region=<REGION>`: Stops a specific EC2 instance.

**Example Response from `/api/uptime`:**
```json
[
  {
    "instanceId": "i-0b2abb73b6dc5937f",
    "launchTime": "2025-06-02T19:50:56+00:00",
    "region": "eu-west-2",
    "status": "running",
    "uptime": "0d 2h 29m",
    "uptime_days": 0.1
  },
  {
    "instanceId": "i-0412b55a14275a1ed",
    "launchTime": "2025-06-02T22:12:07+00:00",
    "region": "eu-west-1",
    "status": "stopped",
    "uptime": "Stopped",
    "uptime_days": 0
  }
]
```

---

## 🛠️ Troubleshooting

* **Dashboard Not Showing Data:**
    * Verify the instance IDs and regions in `Backend/.env` exactly match the output from Terraform.
    * Check for leading/trailing spaces in your `.env` files.
    * Ensure the IAM policy created by Terraform is attached to the user/role whose credentials the backend is using.
* **Failover Script Errors:**
    * Ensure all required environment variables are set correctly before running the script.
    * Confirm the IAM policy is attached to the user/role whose credentials the script is using.
* **Terraform Errors:**
    * `InvalidAMIID.NotFound`: The AMI ID you provided in `terraform.tfvars` does not exist in the specified region. Find a valid one.
    * `Error deleting security group`: A resource (like an EC2 instance) is still using the security group. Find and disassociate the dependent resource in the AWS console.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.
