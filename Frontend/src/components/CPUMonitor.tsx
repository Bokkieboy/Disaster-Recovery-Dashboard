import { useEffect, useState } from 'react';
import { fetchCPU } from '../api/metrics';

export default function CPUMonitor() {
  const [cpu, setCpu] = useState<number | null>(null);

  useEffect(() => {
    const fetchCPU = async () => {
      try {
        const res = await fetch('http://localhost:3001/metrics'); // Backend API endpoint
        const data = await res.json();
        setCpu(data.cpu);
      } catch (error) {
        console.error('Error fetching CPU metrics:', error);
      }
    };

    // Fetch immediately and then every 30 seconds
    fetchCPU();
    const interval = setInterval(fetchCPU, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-center p-6 bg-white rounded-2xl shadow-xl">
      <h2 className="text-xl font-semibold">CPU Usage</h2>
      <p className="text-4xl text-blue-500 font-bold mt-4">{cpu !== null ? `${cpu.toFixed(2)}%` : 'Loading...'}</p>
    </div>
  );
}