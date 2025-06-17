from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from datetime import datetime, timedelta, timezone
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from dotenv import load_dotenv # For loading .env file

# Loads .env file
load_dotenv()

app = Flask(__name__)

REGION = os.getenv("AWS_REGION", "eu-west-2") # Use environment variable, default to eu-west-2
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION) # Added for instance description and state

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://10.0.0.253:3000"]}})
instance_id = 'i-072c32506d067a13a' # EC2 instance ID

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],
)

INSTANCE_ID_PRIMARY = os.getenv('INSTANCE_ID_PRIMARY')
AWS_REGION_PRIMARY = os.getenv('AWS_REGION_PRIMARY')

INSTANCE_ID_SECONDARY = os.getenv('INSTANCE_ID_SECONDARY')
AWS_REGION_SECONDARY = os.getenv('AWS_REGION_SECONDARY') 

def get_instance_configs():
    """
    Builds a list of instance configurations from specific environment variables.
    """
    configs = []
    if INSTANCE_ID_PRIMARY and AWS_REGION_PRIMARY:
        configs.append({
            'id': INSTANCE_ID_PRIMARY,
            'region': AWS_REGION_PRIMARY,
            'name': 'Primary EC2' 
        })
        app.logger.info(f"Primary instance configured: {INSTANCE_ID_PRIMARY} in {AWS_REGION_PRIMARY}")
    else:
        app.logger.warning("Primary instance (INSTANCE_ID_PRIMARY, AWS_REGION_PRIMARY) not configured in .env")

    if INSTANCE_ID_SECONDARY and AWS_REGION_SECONDARY:
        configs.append({
            'id': INSTANCE_ID_SECONDARY,
            'region': AWS_REGION_SECONDARY,
            'name': 'Secondary EC2'
        })
        app.logger.info(f"Secondary instance configured: {INSTANCE_ID_SECONDARY} in {AWS_REGION_SECONDARY}")
    
    if not configs:
        app.logger.error("CRITICAL: No EC2 instances have been configured in the .env file. Backend API will not return EC2 data.")
    return configs

# --- Helper function to get Boto3 clients (cached) ---
# This is good for performance and managing clients for different regions.
boto_clients_cache = {}

def get_boto_client(service_name, region_name):
    """Gets a Boto3 client for a given service and region, caching it."""
    cache_key = f"{service_name}_{region_name}"
    if cache_key not in boto_clients_cache:
        try:
            boto_clients_cache[cache_key] = boto3.client(service_name, region_name=region_name)
            app.logger.info(f"Successfully created Boto3 client for {service_name} in region: {region_name}")
        except Exception as e:
            app.logger.error(f"Error creating Boto3 {service_name} client for region {region_name}: {e}")
            return None
    return boto_clients_cache[cache_key]



# --- API Endpoints ---

@app.route('/api/status_check', methods=['GET'])
def get_server_status_check():
    """A simple endpoint to check if the backend is running."""
    return jsonify({"message": "Backend is running", "timestamp": datetime.now(timezone.utc).isoformat()}), 200

@app.route('/api/cpu', methods=['GET'])
def get_cpu_utilization_all():
    instance_configs = get_instance_configs()
    if not instance_configs:
        return jsonify({"error": "No EC2 instances configured on the backend. Please check backend .env file and logs."}), 500

    all_cpu_data = []
    for config in instance_configs:
        instance_id = config['id']
        region = config['region']
        cloudwatch = get_boto_client('cloudwatch', region)

        if not cloudwatch:
            all_cpu_data.append({
                "instanceId": instance_id, "region": region, "cpu": None,
                "error": f"Could not initialize CloudWatch client for region {region}. AWS credentials/permissions issue?"
            })
            continue
        
        try:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/EC2', MetricName='CPUUtilization',
                Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                StartTime=datetime.now(timezone.utc) - timedelta(minutes=10), # From user's original code
                EndTime=datetime.now(timezone.utc),
                Period=60, # From user's original code
                Statistics=['Average']
            )
            if response['Datapoints']:
                latest_datapoint = sorted(response['Datapoints'], key=lambda x: x['Timestamp'], reverse=True)[0]
                all_cpu_data.append({
                    "instanceId": instance_id, "region": region, 
                    "cpu": round(latest_datapoint['Average'], 2)
                })
            else:
                all_cpu_data.append({
                    "instanceId": instance_id, "region": region, "cpu": None,
                    "message": "No CPU data points found for this instance in the last 10 minutes."
                })
        except Exception as e:
            app.logger.error(f"Error fetching CPU for {instance_id} in {region}: {e}")
            all_cpu_data.append({
                "instanceId": instance_id, "region": region, "cpu": None, "error": str(e)
            })
            
    return jsonify(all_cpu_data)


@app.route('/api/uptime', methods=['GET'])
def get_instance_uptime_all():
    instance_configs = get_instance_configs()
    if not instance_configs:
        return jsonify({"error": "No EC2 instances configured on the backend. Please check backend .env file and logs."}), 500

    all_uptime_data = []
    for config in instance_configs:
        instance_id = config['id']
        region = config['region']
        # For uptime, EC2 resource is convenient for launch_time and state
        # We are not caching resource clients here for simplicity, but you could.
        try:
            ec2_resource_client = boto3.resource('ec2', region_name=region)
            instance = ec2_resource_client.Instance(instance_id)
            instance.load() # Make sure instance data is loaded
        except Exception as e:
            app.logger.error(f"Error creating EC2 resource or loading instance {instance_id} in {region}: {e}")
            all_uptime_data.append({
                "instanceId": instance_id, "region": region, "uptime": "Error",
                "uptime_days": 0, "status": "Error", 
                "error": f"Could not get EC2 instance details. AWS credentials/permissions or instance ID issue? Error: {str(e)}"
            })
            continue
            
        try:
            instance_state = instance.state['Name']
            launch_time = instance.launch_time # This is already timezone-aware (UTC)
            
            uptime_str = instance_state.capitalize()
            uptime_d = 0
            status = instance_state

            if instance_state == 'running' and launch_time:
                now_utc = datetime.now(timezone.utc)
                uptime_delta = now_utc - launch_time
                
                days = uptime_delta.days
                hours, remainder = divmod(uptime_delta.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                uptime_str = f"{days}d {hours}h {minutes}m"
                uptime_d = round(uptime_delta.total_seconds() / (24 * 3600), 2)
            elif not launch_time and instance_state == 'running':
                uptime_str = "Running (launch time unavailable)"


            all_uptime_data.append({
                "instanceId": instance_id, "region": region,
                "uptime": uptime_str, "uptime_days": uptime_d, "status": status,
                "launchTime": launch_time.isoformat() if launch_time else None
            })
        except Exception as e:
            app.logger.error(f"Error processing uptime for {instance_id} in {region}: {e}")
            all_uptime_data.append({
                "instanceId": instance_id, "region": region, "uptime": "Processing Error",
                "uptime_days": 0, "status": "Error", "error": str(e)
            })
            
    return jsonify(all_uptime_data)


@app.route('/api/start', methods=['POST'])
def start_instance_req():
    instance_id = request.args.get('instance_id')
    region = request.args.get('region')

    if not instance_id or not region:
        return jsonify({"error": "Missing 'instance_id' or 'region' query parameter"}), 400

    ec2_control_client = get_boto_client('ec2', region)
    if not ec2_control_client:
        return jsonify({"error": f"Could not get EC2 client for region {region}. AWS credentials/permissions issue?"}), 500
        
    try:
        response = ec2_control_client.start_instances(InstanceIds=[instance_id])
        app.logger.info(f"Start instance API call response for {instance_id} in {region}: {response}")
        return jsonify({
            "message": f"Start initiated for instance {instance_id} in {region}",
            "instanceId": instance_id, "region": region,
            "details": response.get('StartingInstances', [])
        }), 200
    except Exception as e:
        app.logger.error(f"Error starting instance {instance_id} in {region}: {e}")
        return jsonify({
            "error": f"Failed to start instance {instance_id}: {str(e)}",
            "instanceId": instance_id, "region": region
        }), 500
    
@app.route('/api/stop', methods=['POST'])
def stop_instance_req():
    instance_id = request.args.get('instance_id')
    region = request.args.get('region')

    if not instance_id or not region:
        return jsonify({"error": "Missing 'instance_id' or 'region' query parameter"}), 400

    ec2_control_client = get_boto_client('ec2', region)
    if not ec2_control_client:
        return jsonify({"error": f"Could not get EC2 client for region {region}. AWS credentials/permissions issue?"}), 500

    try:
        response = ec2_control_client.stop_instances(InstanceIds=[instance_id])
        app.logger.info(f"Stop instance API call response for {instance_id} in {region}: {response}")
        return jsonify({
            "message": f"Stop initiated for instance {instance_id} in {region}",
            "instanceId": instance_id, "region": region,
            "details": response.get('StoppingInstances', [])
        }), 200
    except Exception as e:
        app.logger.error(f"Error stopping instance {instance_id} in {region}: {e}")
        return jsonify({
            "error": f"Failed to stop instance {instance_id}: {str(e)}",
            "instanceId": instance_id, "region": region
        }), 500

if __name__ == '__main__':
    # Enable Flask's built-in logger to see messages in console
    app.logger.setLevel(os.getenv('FLASK_LOG_LEVEL', 'INFO').upper())
    app.logger.info("Flask application starting...")
    app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=5000)
