import subprocess
import requests
import time
import boto3
import logging

# Configuration
EC2_INSTANCE_ID = "i-0dc17676ee962edcd"
REGION = "eu-west-2"
CHECK_INTERVAL = 60  # in seconds
FRONTEND_CONTAINER = "dr_dashboard_frontend"
BACKEND_CONTAINER = "dr_dashboard_backend"

logging.basicConfig(filename='failover.log', level=logging.INFO)

def is_ec2_running():
    try:
        ec2 = boto3.client('ec2', region_name=REGION)
        response = ec2.describe_instance_status(InstanceIds=[EC2_INSTANCE_ID])
        statuses = response.get('InstanceStatuses', [])
        if not statuses:
            logging.info("No instance status available (likely stopped or terminated).")
            return False
        state = statuses[0]['InstanceState']['Name']
        logging.info(f"EC2 instance state: {state}")
        return state == 'running'
    except Exception as e:
        logging.error(f"Error checking EC2 status: {e}")
        return False

def start_local_services():
    try:
        # Start backend
        subprocess.run(["docker", "start", BACKEND_CONTAINER], check=True)
        logging.info("Backend started successfully.")
        # Start frontend
        subprocess.run(["docker", "start", FRONTEND_CONTAINER], check=True)
        logging.info("Frontend started successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error starting local services: {e}")

def main():
    while True:
        if not is_ec2_running():
            logging.warning("EC2 is down. Starting local services...")
            start_local_services()
        else:
            logging.info("EC2 is running normally.")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()