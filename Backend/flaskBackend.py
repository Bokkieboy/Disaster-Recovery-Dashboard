from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

app = Flask(__name__)

REGION = os.getenv("AWS_REGION", "eu-west-2") # Use environment variable, default to eu-west-2
ec2 = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION) # Added for instance description and state

CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
instance_id = 'i-0dc17676ee962edcd' # EC2 instance ID

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],
)

def get_latest_cpu_utilization():
    cloudwatch_client = boto3.client('cloudwatch', region_name=REGION) # Use REGION here
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)

    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName='CPUUtilization',
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Average']
        )

        datapoints = response['Datapoints']
        if not datapoints:
            print(f"No CPU data points found for instance {instance_id}") # Added for debugging
            return None, None

        latest = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)[0]
        return latest['Average'], latest['Timestamp']
    except Exception as e:
        print(f"Error fetching CPU utilization: {e}") # Added for debugging
        return None, None

# --- NEW ENDPOINT: /api/uptime ---
@app.route('/api/uptime')
def get_uptime():
    try:
        instance = ec2_resource.Instance(instance_id) # Use ec2_resource
        
        # Get instance state (running, stopped, pending, etc.)
        instance_state = instance.state['Name']

        if instance_state != 'running':
            return jsonify({'uptime': instance_state.capitalize(), 'uptime_days': 0}) # Report current state

        # Get launch time, ensuring it's timezone-aware for comparison
        launch_time = instance.launch_time
        
        # Calculate uptime relative to current time (also timezone-aware)
        current_time = datetime.now(launch_time.tzinfo) 
        uptime_delta = current_time - launch_time
        
        days = uptime_delta.days
        hours = uptime_delta.seconds // 3600
        minutes = (uptime_delta.seconds % 3600) // 60

        uptime_str = f"{days}d {hours}h {minutes}m"
        return jsonify({'uptime': uptime_str, 'uptime_days': days})
    except Exception as e:
        print(f"Error fetching uptime for instance {instance_id}: {e}") # Added for debugging
        return jsonify({'error': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_instance():
    print(f"Attempting to start instance: {instance_id}") # Added for debugging
    try:
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Successfully sent start command for instance: {instance_id}") # Added for debugging
        return jsonify({"status": "starting"})
    except Exception as e:
        print(f"Error starting instance {instance_id}: {e}") # Added for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop', methods=['POST'])
def stop_instance():
    print(f"Attempting to stop instance: {instance_id}") # Added for debugging
    try:
        ec2.stop_instances(InstanceIds=[instance_id])
        print(f"Successfully sent stop command for instance: {instance_id}") # Added for debugging
        return jsonify({"status": "stopping"})
    except Exception as e:
        print(f"Error stopping instance {instance_id}: {e}") # Added for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/api/cpu')
def get_cpu():
    cpu_usage, timestamp = get_latest_cpu_utilization()
    if cpu_usage is not None:
        return jsonify({'cpu': round(cpu_usage, 2)})
    else:
        return jsonify({'error': 'No CPU data available'}), 503

if __name__ == '__main__':
    # Running in debug mode allows auto-reloading and better error messages
    app.run(host='0.0.0.0', port=5000, debug=True)