# Disaster Recovery Dashboard

A comprehensive cloud-based Disaster Recovery (DR) dashboard for managing and monitoring EC2 instances and home servers. This project includes a **React** frontend and a **Flask** backend, with metrics fetched from AWS CloudWatch. It is designed to be deployed on a home server or EC2 instance for high availability.

---

## 🚀 Features

* Real-time CPU and uptime monitoring for EC2 and local servers
* Automated failover and recovery triggers
* Easy-to-use React dashboard
* Dockerized for simple deployment
* CORS-enabled Flask API for secure cross-origin communication

---

## 📁 Project Structure

```
DisasterRecoveryDashboard/
├── Backend/
│   ├── flaskBackend.py
│   ├── requirements.txt
│   └── Dockerfile
├── Frontend/
│   ├── dist/
│   ├── node_modules/
│   ├── vite.config.ts
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

---

## 🛠️ Setup Instructions

### Prerequisites

* Docker & Docker Compose
* Node.js (v20 or later)
* Python 3.11
* AWS credentials configured (`~/.aws/credentials`)

### Clone the Repository

```bash
git clone [https://github.com/your-username/DisasterRecoveryDashboard.git](https://github.com/your-username/DisasterRecoveryDashboard.git)
cd DisasterRecoveryDashboard
```

### Build and Run the Docker Containers

For routine updates and initial setup:
```bash
docker-compose up -d --build
```
This command will build the images if they don't exist or if their Dockerfiles/contexts have changed, and then start the services in detached mode.

If you need a complete teardown (e.g., to remove old volumes):
```bash
docker-compose down -v
docker-compose up -d --build
```

### Access the Dashboard

* **Frontend**: [http://localhost:3000](http://localhost:3000)
* **Backend**: [http://localhost:5000](http://localhost:5000)

---

## 📦 Frontend

Located in the `Frontend/` directory. Built with Vite + React + Tailwind.

### Build Commands

```bash
cd Frontend
npm install
npm run build
```

### Development Server

```bash
npm run dev
```

---

## 🐍 Backend

Located in the `Backend/` directory. Built with Flask and Flask-CORS.

### Install Dependencies

```bash
cd Backend
pip3 install -r requirements.txt
```

### Run the Server

```bash
python flaskBackend.py
```

---

## 🔗 Environment Variables

Create a `.env` file in the **Backend** directory to store your AWS credentials and instance ID:

```env
INSTANCE_ID=i-0123456789abcdef0
AWS_REGION=eu-west-2
```

---

## 📊 API Endpoints

* **GET** `/api/cpu`: Returns the current CPU utilization for the EC2 instance.

    Example Response:
    ```json
    {
      "cpu": 27.5
    }
    ```

* **GET** `/api/uptime`: Returns the uptime for the EC2 instance.

    Example Response (actual structure may vary based on your implementation):
    ```json
    {
      "uptime": "7 days, 2 hours, 30 minutes",
      "uptime_days": 7.1,
      "status": "Running"
    }
    ```

---

## 🛠️ Troubleshooting

* **CORS Errors**: Make sure your frontend is pointing to the correct backend URL.
* **Docker Daemon Issues**: Ensure Docker is running and you have sufficient permissions.
* **AWS Permissions**: Ensure your AWS IAM user has sufficient permissions to access CloudWatch metrics.

---

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for more details.
