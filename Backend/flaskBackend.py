from flask import Flask, jsonify
import boto3
from datetime import datetime, timedelta

app = Flask(__name__)

import boto3
from datetime import datetime, timedelta

instance_id = 'i-0dc17676ee962edcd'

def get_latest_cpu_utilization():
    cloudwatch_client = boto3.client('cloudwatch')
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=10)

    response = cloudwatch_client.get_metric_statistics(
        Namespace='AWS/EC2',
        MetricName='CPUUtilization',
        Dimensions=[
            {
                'Name': 'InstanceId',
                'Value': instance_id
            },
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=60,  # 1 minute
        Statistics=['Average']
    )

    datapoints = response['Datapoints']
    if not datapoints:
        print("No data available.")
        return None

    # Sort datapoints by Timestamp to get the latest one
    latest_datapoint = sorted(datapoints, key=lambda x: x['Timestamp'], reverse=True)[0]
    return latest_datapoint['Average'], latest_datapoint['Timestamp']

# Get the most recent CPU utilization
cpu_usage, timestamp = get_latest_cpu_utilization()

if cpu_usage is not None:
    return jsonify({'cpu': f"{cpu_usage:.2f}"})

if __name__ == '__main__':
    app.run(debug=True, port=3001)