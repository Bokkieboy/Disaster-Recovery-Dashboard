from flask import Flask, jsonify
from flask_cors import CORS
import boto3
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app, origins=["http://13.42.64.118:5173", "http://localhost:5173"])
instance_id = 'i-0dc17676ee962edcd'

def get_latest_cpu_utilization():
    cloudwatch_client = boto3.client('cloudwatch')
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