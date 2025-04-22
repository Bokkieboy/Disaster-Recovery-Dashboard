# Flask Backend - Control EC2 + Serve Device Info
from flaskBackend import Flask, request, jsonify
import boto3
from flask_cors import CORS
import datetime

app = Flask(__name__)
CORS(app)

ec2 = boto3.client('ec2', region_name='us-east-1')

# Mock in-memory DB for demo
devices = [
    {"id": "i-1234567890abcdef0", "name": "Amazon EC2", "status": "running"},
    {"id": "i-0987654321fedcba0", "name": "Amazon EC2", "status": "stopped"},
    {"id": "home-server-01", "name": "Home Server", "status": "running"}
]

@app.route('/devices')
def list_devices():
    return jsonify(devices)

@app.route('/uptime')
def get_uptime():
    now = datetime.datetime.utcnow().hour
    # Fake 24-hour binary uptime (1 = up, 0 = down)
    return jsonify([1 if i % 5 != 0 else 0 for i in range(24)])

@app.route('/control', methods=['POST'])
def control_device():
    data = request.get_json()
    id = data['id']
    action = data['action']

    for dev in devices:
        if dev['id'] == id:
            dev['status'] = 'stopped' if action == 'shutdown' else 'running'
            # For EC2:
            if id.startswith('i-'):
                if action == 'shutdown':
                    ec2.stop_instances(InstanceIds=[id])
                elif action == 'reboot':
                    ec2.reboot_instances(InstanceIds=[id])
            return jsonify({'result': 'success'})

    return jsonify({'error': 'Device not found'}), 404

@app.route('/add', methods=['POST'])
def add_device():
    data = request.get_json()
    new_id = data['id']
    devices.append({"id": new_id, "name": "Amazon EC2", "status": "pending"})
    return jsonify({'result': 'added'})

if __name__ == '__main__':
    app.run(debug=True)
