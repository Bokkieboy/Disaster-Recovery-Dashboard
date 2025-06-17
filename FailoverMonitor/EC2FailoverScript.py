import boto3
import time
import logging
from botocore.exceptions import ClientError

# --- Configuration ---
# Main EC2 Instance
MAIN_INSTANCE_ID = "i-072c32506d067a13a"  
MAIN_REGION = "eu-west-2"             

# Backup EC2 Instance
BACKUP_INSTANCE_ID = "i-0391db570934d58c5" 
BACKUP_REGION = "eu-west-1"          

# Script Configuration
CHECK_INTERVAL_SECONDS = 60  # How often to check (in seconds)
LOG_FILE = "failover_monitor.log"
MAIN_INSTANCE_STABLE_WAIT_SECONDS = 300 # 5 minutes

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also print to console
    ]
)

# Variable to track if we've recently confirmed the main instance is stable
main_instance_confirmed_stable_since = None

def get_instance_state(instance_id, region_name):
    """
    Gets the state of a given EC2 instance.
    Returns instance state string (e.g., 'pending', 'running', 'stopping', 'stopped', 'shutting-down', 'terminated')
    Returns None if an error occurs or instance not found.
    """
    try:
        ec2_client = boto3.client('ec2', region_name=region_name)
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        if not response['Reservations'] or not response['Reservations'][0]['Instances']:
            logging.warning(f"Instance {instance_id} not found in region {region_name}.")
            return None
        return response['Reservations'][0]['Instances'][0]['State']['Name']
    except ClientError as e:
        logging.error(f"AWS API Error checking instance {instance_id} in {region_name}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred checking instance {instance_id} in {region_name}: {e}")
        return None

def start_instance(instance_id, region_name):
    """
    Starts a given EC2 instance.
    Returns True if start command issued or already running, False otherwise.
    """
    try:
        ec2_client = boto3.client('ec2', region_name=region_name)
        current_state = get_instance_state(instance_id, region_name)

        if current_state == 'running':
            logging.info(f"Instance {instance_id} in {region_name} is already running.")
            return True
        elif current_state == 'pending':
            logging.info(f"Instance {instance_id} in {region_name} is already pending. Waiting for it to start.")
            return True
        elif current_state in ['stopped', 'stopping']:
            logging.info(f"Attempting to start instance {instance_id} in {region_name} (current state: {current_state})...")
            ec2_client.start_instances(InstanceIds=[instance_id])
            logging.info(f"Start command issued for instance {instance_id} in {region_name}.")
            return True
        elif current_state is None:
            logging.error(f"Cannot start instance {instance_id}: current state unknown or instance not found.")
            return False
        else:
            logging.warning(f"Instance {instance_id} in {region_name} is in state '{current_state}', not attempting to start.")
            return False

    except ClientError as e:
        logging.error(f"AWS API Error starting instance {instance_id} in {region_name}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred starting instance {instance_id} in {region_name}: {e}")
        return False

def stop_instance(instance_id, region_name):
    """
    Stops a given EC2 instance.
    Returns True if stop command issued or already stopped/stopping, False otherwise.
    """
    try:
        ec2_client = boto3.client('ec2', region_name=region_name)
        current_state = get_instance_state(instance_id, region_name)

        if current_state == 'stopped':
            logging.info(f"Instance {instance_id} in {region_name} is already stopped.")
            return True
        elif current_state == 'stopping':
            logging.info(f"Instance {instance_id} in {region_name} is already stopping.")
            return True
        elif current_state == 'running' or current_state == 'pending': # Or other states you want to stop from
            logging.info(f"Attempting to stop instance {instance_id} in {region_name} (current state: {current_state})...")
            ec2_client.stop_instances(InstanceIds=[instance_id])
            logging.info(f"Stop command issued for instance {instance_id} in {region_name}.")
            return True
        elif current_state is None:
            logging.error(f"Cannot stop instance {instance_id}: current state unknown or instance not found.")
            return False
        else:
            logging.warning(f"Instance {instance_id} in {region_name} is in state '{current_state}', not attempting to stop.")
            return False
    except ClientError as e:
        logging.error(f"AWS API Error stopping instance {instance_id} in {region_name}: {e}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred stopping instance {instance_id} in {region_name}: {e}")
        return False

def main_monitoring_loop():
    global main_instance_confirmed_stable_since
    logging.info("--- Starting EC2 Failover Monitor ---")
    logging.info(f"Main Instance: {MAIN_INSTANCE_ID} ({MAIN_REGION})")
    logging.info(f"Backup Instance: {BACKUP_INSTANCE_ID} ({BACKUP_REGION})")
    logging.info(f"Main instance stability period before stopping backup: {MAIN_INSTANCE_STABLE_WAIT_SECONDS} seconds")

    while True:
        try:
            logging.info(f"Checking status of main instance: {MAIN_INSTANCE_ID} ({MAIN_REGION})")
            main_instance_state = get_instance_state(MAIN_INSTANCE_ID, MAIN_REGION)
            logging.info(f"Main instance {MAIN_INSTANCE_ID} current state: {main_instance_state}")

            if main_instance_state == 'running':
                logging.info(f"Main instance {MAIN_INSTANCE_ID} is running.")
                if main_instance_confirmed_stable_since is None:
                    main_instance_confirmed_stable_since = time.time()
                    logging.info(f"Main instance {MAIN_INSTANCE_ID} confirmed running. Starting stability timer.")

                if time.time() - main_instance_confirmed_stable_since >= MAIN_INSTANCE_STABLE_WAIT_SECONDS:
                    logging.info(f"Main instance {MAIN_INSTANCE_ID} has been stable for over {MAIN_INSTANCE_STABLE_WAIT_SECONDS} seconds.")
                    backup_instance_state = get_instance_state(BACKUP_INSTANCE_ID, BACKUP_REGION)
                    logging.info(f"Checking backup instance {BACKUP_INSTANCE_ID} state: {backup_instance_state}")
                    if backup_instance_state == 'running':
                        logging.info(f"Main instance is stable and backup instance {BACKUP_INSTANCE_ID} is running. Attempting to stop backup instance.")
                        stop_instance(BACKUP_INSTANCE_ID, BACKUP_REGION)
                    elif backup_instance_state == 'stopped':
                        logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is already stopped. No action needed for backup.")
                    elif backup_instance_state is None:
                        logging.warning(f"Could not determine state of backup instance {BACKUP_INSTANCE_ID} while main is stable.")
                    else:
                         logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is in state '{backup_instance_state}'. No stop action needed.")
                else:
                    wait_remaining = MAIN_INSTANCE_STABLE_WAIT_SECONDS - (time.time() - main_instance_confirmed_stable_since)
                    logging.info(f"Main instance {MAIN_INSTANCE_ID} is running, waiting for {wait_remaining:.0f} more seconds to confirm stability before potentially stopping backup.")

            elif main_instance_state is None: # Error or instance not found
                logging.error(f"Could not determine state of main instance {MAIN_INSTANCE_ID}. Not taking failover action to be safe.")
                main_instance_confirmed_stable_since = None # Reset stability timer

            else: # Main instance is not running (e.g., 'stopped', 'stopping', 'terminated')
                logging.warning(f"Main instance {MAIN_INSTANCE_ID} is NOT RUNNING (state: {main_instance_state}). Initiating check for backup instance.")
                main_instance_confirmed_stable_since = None # Reset stability timer

                backup_instance_state = get_instance_state(BACKUP_INSTANCE_ID, BACKUP_REGION)
                logging.info(f"Backup instance {BACKUP_INSTANCE_ID} current state: {backup_instance_state}")

                if backup_instance_state == 'running':
                    logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is already running.")
                elif backup_instance_state == 'stopped':
                    logging.info(f"Backup instance {BACKUP_INSTANCE_ID} is stopped. Attempting to start it.")
                    start_instance(BACKUP_INSTANCE_ID, BACKUP_REGION)
                elif backup_instance_state is None:
                    logging.error(f"Could not determine state of backup instance {BACKUP_INSTANCE_ID}. Cannot start it.")
                else:
                    logging.warning(f"Backup instance {BACKUP_INSTANCE_ID} is in state '{backup_instance_state}'. Not attempting to start automatically.")

        except Exception as e:
            logging.critical(f"An unhandled exception occurred in the main loop: {e}", exc_info=True)
            main_instance_confirmed_stable_since = None # Reset stability timer on error
        
        logging.info(f"Waiting for {CHECK_INTERVAL_SECONDS} seconds before next check...")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    # Ensure your AWS credentials and region are configured where this script runs
    # e.g., via `aws configure` or environment variables.
    main_monitoring_loop()