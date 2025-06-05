# /failover/failover_handler.py

import os
import json
import time
import logging
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# --- Configuration from Environment Variables ---
# These must be set in the environment or a .env file
SQS_QUEUE_URL = os.getenv("FAILOVER_SQS_QUEUE_URL")
PRIMARY_ALARM_NAME = os.getenv("PRIMARY_ALARM_NAME", "MainInstanceUnhealthyAlarm") # Default is fine if it matches Terraform
BACKUP_INSTANCE_ID = os.getenv("BACKUP_INSTANCE_ID")
BACKUP_INSTANCE_REGION = os.getenv("BACKUP_INSTANCE_REGION") # e.g., "eu-west-1"
AWS_REGION_FOR_SCRIPT = os.getenv("AWS_REGION_FOR_SCRIPT") # Region for SQS client, e.g., "eu-west-2"

# Optional configurations with defaults
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "20"))
VISIBILITY_TIMEOUT_SECONDS = int(os.getenv("VISIBILITY_TIMEOUT_SECONDS", "60"))

# --- Logging Setup ---
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Validate Essential Configuration ---
REQUIRED_ENV_VARS = {
    "SQS_QUEUE_URL": SQS_QUEUE_URL,
    "BACKUP_INSTANCE_ID": BACKUP_INSTANCE_ID,
    "BACKUP_INSTANCE_REGION": BACKUP_INSTANCE_REGION,
    "AWS_REGION_FOR_SCRIPT": AWS_REGION_FOR_SCRIPT,
    "PRIMARY_ALARM_NAME": PRIMARY_ALARM_NAME
}

missing_vars = [key for key, value in REQUIRED_ENV_VARS.items() if value is None]
if missing_vars:
    logging.critical(f"Missing critical environment variables: {', '.join(missing_vars)}. Please set them and restart.")
    exit(1)

# --- Initialize AWS Boto3 Clients ---
try:
    logging.info(f"Initializing SQS client for region: {AWS_REGION_FOR_SCRIPT}")
    sqs_client = boto3.client("sqs", region_name=AWS_REGION_FOR_SCRIPT)
    
    logging.info(f"Initializing EC2 client for region: {BACKUP_INSTANCE_REGION}")
    ec2_client = boto3.client("ec2", region_name=BACKUP_INSTANCE_REGION)
    logging.info("AWS clients initialized successfully.")
except Exception as e:
    logging.critical(f"Fatal error: Failed to initialize AWS Boto3 clients: {e}")
    exit(1)


def get_instance_state(instance_id: str) -> str | None:
    """
    Retrieves the current state of the specified EC2 instance.
    Returns the state string (e.g., 'running', 'stopped') or None if an error occurs or instance not found.
    """
    if not instance_id:
        logging.error("get_instance_state called with no instance_id.")
        return None
    try:
        logging.debug(f"Describing instance: {instance_id}")
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        reservations = response.get("Reservations")
        if not reservations:
            logging.warning(f"No reservations found for instance {instance_id}. It might not exist or there was an issue.")
            return "not-found" # Or None, depending on how you want to handle "not found"
        
        instances = reservations[0].get("Instances")
        if not instances:
            logging.warning(f"No instances found in reservation for instance {instance_id}.")
            return "not-found" # Or None
            
        state_info = instances[0].get("State", {})
        instance_state = state_info.get("Name")
        logging.info(f"Instance {instance_id} current state: {instance_state}")
        return instance_state

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "InvalidInstanceID.NotFound":
            logging.warning(f"Instance {instance_id} not found.")
            return "not-found"
        logging.error(f"AWS ClientError checking instance state for {instance_id}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error checking instance state for {instance_id}: {e}")
    return None


def start_backup_instance(instance_id: str):
    """
    Initiates the start of the backup EC2 instance.
    """
    if not instance_id:
        logging.error("start_backup_instance called with no instance_id.")
        return
    try:
        logging.info(f"Attempting to start backup instance: {instance_id}")
        ec2_client.start_instances(InstanceIds=[instance_id])
        logging.info(f"Start command issued for instance {instance_id}. Monitor AWS console for progress.")
    except ClientError as e:
        logging.error(f"AWS ClientError starting instance {instance_id}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error starting instance {instance_id}: {e}")


def process_sqs_message(message: dict):
    """
    Processes a single SQS message, expecting it to be an SNS notification
    wrapping a CloudWatch alarm message.
    """
    message_id = message.get("MessageId", "N/A")
    receipt_handle_short = message.get("ReceiptHandle", "N/A")[:20] # For concise logging
    logging.info(f"Processing SQS Message ID: {message_id}, ReceiptHandle (short): {receipt_handle_short}...")

    try:
        sqs_message_body_str = message["Body"]
        sns_notification = json.loads(sqs_message_body_str)

        # If RawMessageDelivery is false (default) for the SNS->SQS subscription,
        # the CloudWatch alarm JSON is a string within the 'Message' field of the SNS notification.
        # If RawMessageDelivery is true, sns_notification would BE the CloudWatch alarm JSON directly.
        if "Message" not in sns_notification:
            logging.warning(f"SNS 'Message' field missing in SQS message body. Assuming raw delivery or incorrect format. Body: {sqs_message_body_str}")
            # If you expect raw delivery, you'd parse sns_notification as the CloudWatch alarm directly.
            # For now, this path will skip processing if "Message" is missing.
            return 

        cloudwatch_alarm_str = sns_notification["Message"]
        cloudwatch_alarm = json.loads(cloudwatch_alarm_str)
        
        logging.debug(f"Parsed CloudWatch Alarm content: {json.dumps(cloudwatch_alarm, indent=2)}")

        alarm_name_from_msg = cloudwatch_alarm.get("AlarmName")
        new_state_value = cloudwatch_alarm.get("NewStateValue")

        if alarm_name_from_msg == PRIMARY_ALARM_NAME and new_state_value == "ALARM":
            logging.warning(f"FAILOVER TRIGGERED: Primary instance alarm '{alarm_name_from_msg}' is in ALARM state.")
            
            current_backup_state = get_instance_state(BACKUP_INSTANCE_ID)
            
            if current_backup_state == "stopped":
                logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is currently stopped. Initiating start sequence.")
                start_backup_instance(BACKUP_INSTANCE_ID)
            elif current_backup_state == "running":
                logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is already running. No action needed.")
            elif current_backup_state == "pending" or current_backup_state == "stopping":
                 logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is in a transitional state: '{current_backup_state}'. No action needed.")
            elif current_backup_state == "not-found":
                logging.error(f"Backup instance {BACKUP_INSTANCE_ID} was not found. Cannot start.")
            else: # Includes None (error) or other states
                logging.warning(f"Backup instance {BACKUP_INSTANCE_ID} is in state '{current_backup_state}'. Manual intervention might be required if it's not 'stopped' or 'running'.")
        
        elif alarm_name_from_msg == PRIMARY_ALARM_NAME and new_state_value == "OK":
            logging.info(f"RECOVERY: Primary instance alarm '{alarm_name_from_msg}' has returned to OK state.")
            # Consider adding logic here if you want to automate failback (e.g., stop the backup instance).
            # This requires careful planning to avoid flapping.
        else:
            logging.info(f"Received notification for alarm '{alarm_name_from_msg}' (state: '{new_state_value}'). Ignoring as it's not the primary failover alarm in ALARM state.")

    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error for SQS Message ID {message_id}: {e}. Body: {message.get('Body', 'N/A')}")
    except KeyError as e:
        logging.error(f"Missing expected key in message structure for SQS Message ID {message_id}: {e}. Body: {message.get('Body', 'N/A')}")
    except Exception as e:
        logging.error(f"Unexpected error processing SQS Message ID {message_id}: {e}")


def main_loop():
    """
    Main loop to continuously poll the SQS queue for messages and process them.
    """
    logging.info(f"Starting EC2 failover handler. Polling SQS queue: {SQS_QUEUE_URL}")
    logging.info(f"Monitoring for alarm: {PRIMARY_ALARM_NAME}")
    logging.info(f"Backup instance: {BACKUP_INSTANCE_ID} in region {BACKUP_INSTANCE_REGION}")

    while True:
        try:
            logging.debug(f"Receiving messages from SQS (WaitTimeSeconds={POLL_INTERVAL_SECONDS})...")
            response = sqs_client.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                AttributeNames=["All"], # Not strictly needed if not using them, but harmless
                MaxNumberOfMessages=5,  # Can process up to 5 messages per poll
                MessageAttributeNames=["All"], # Not strictly needed if not using them
                WaitTimeSeconds=POLL_INTERVAL_SECONDS, # Enables long polling
                VisibilityTimeout=VISIBILITY_TIMEOUT_SECONDS,
            )

            messages_received = response.get("Messages", [])
            if messages_received:
                logging.info(f"Received {len(messages_received)} message(s) from SQS.")
                for msg in messages_received:
                    process_sqs_message(msg)
                    # Delete message from queue only after successful processing attempt
                    try:
                        receipt_handle = msg["ReceiptHandle"]
                        logging.debug(f"Attempting to delete message with ReceiptHandle (short): {receipt_handle[:20]}...")
                        sqs_client.delete_message(
                            QueueUrl=SQS_QUEUE_URL,
                            ReceiptHandle=receipt_handle
                        )
                        logging.info(f"Successfully deleted message (ReceiptHandle short: {receipt_handle[:20]}).")
                    except ClientError as e:
                        logging.error(f"AWS ClientError deleting message (ReceiptHandle short: {receipt_handle[:20]}): {e}")
                    except Exception as e:
                        logging.error(f"Unexpected error deleting message (ReceiptHandle short: {receipt_handle[:20]}): {e}")
            else:
                logging.debug("No messages in queue this poll.")

        except ClientError as e:
            logging.error(f"AWS ClientError during SQS polling: {e}. Will retry after a delay.")
            time.sleep(60) # Longer backoff for client errors (e.g., network, throttling)
        except Exception as e:
            logging.error(f"An unexpected error occurred in the main polling loop: {e}. Will retry after a delay.")
            time.sleep(30) # Shorter backoff for other unexpected errors
        # No explicit sleep here if WaitTimeSeconds is effective,
        # as it dictates the poll duration.

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logging.info("Shutdown signal received (KeyboardInterrupt). Exiting gracefully.")
    except Exception as e:
        # This catches errors that might occur outside the main_loop, e.g., during initial setup if not caught earlier.
        logging.critical(f"A fatal unhandled error occurred: {e}", exc_info=True)
    finally:
        logging.info("Failover handler script has stopped.")
