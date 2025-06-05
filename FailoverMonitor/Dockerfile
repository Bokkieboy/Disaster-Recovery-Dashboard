FROM python:3.11-slim

WORKDIR /app

# Assuming you'll create a requirements.txt for this script in FailoverMonitor/
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY EC2FailoverScript.py .

CMD ["python", "-u", "EC2FailoverScript.py"]