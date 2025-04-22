// server.js
const express = require('express');
const AWS = require('aws-sdk');
const cors = require('cors');

const app = express();
app.use(cors());

AWS.config.update({ region: 'eu-west-2b' }); 

const cloudwatch = new AWS.CloudWatch();

app.get('/metrics', async (req, res) => {
  const params = {
    MetricName: 'CPUUtilization',
    Namespace: 'AWS/EC2',
    Dimensions: [{
      Name: 'React-Web',
      Value: 'i-0dc17676ee962edcd'
    }],
    StartTime: new Date(Date.now() - 5 * 60 * 1000),
    EndTime: new Date(),
    Period: 60,
    Statistics: ['Average'],
  };

  try {
    const data = await cloudwatch.getMetricStatistics(params).promise();
    const latest = data.Datapoints.sort((a, b) => b.Timestamp - a.Timestamp)[0];
    res.json({ cpu: latest?.Average || 0 });
  } catch (err) {
    console.error(err);
    res.status(500).send('Failed to fetch metrics');
  }
});

app.listen(3001, () => console.log('Server running on http://localhost:3001'));