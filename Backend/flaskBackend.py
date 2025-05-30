from flask import Flask, jsonify
from flask_cors import CORS
import boto3
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000"]}})
instance_id = 'i-0dc17676ee962edcd'

# Set up rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],  # Example: max 100 requests/minute per IP
)

def get_latest_cpu_utilization():
    cloudwatch_client = boto3.client('cloudwatch', region_name='eu-west-2')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)

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
        return None, None

    latest = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)[0]
    return latest['Average'], latest['Timestamp']

@app.route('/api/cpu')
def get_cpu():
    cpu_usage, timestamp = get_latest_cpu_utilization()
    if cpu_usage is not None:
        return jsonify({'cpu': round(cpu_usage, 2)})
    else:
        return jsonify({'error': 'No CPU data available'}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)