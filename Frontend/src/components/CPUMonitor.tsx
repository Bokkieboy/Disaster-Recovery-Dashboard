import { useEffect, useState } from 'react';
import { fetchCPU } from '../api/metrics';

export default function CPUMonitor() {
  const [cpu, setCpu] = useState<number | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      const cpuValue = await fetchCPU();
      setCpu(cpuValue);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="text-center p-6 bg-white rounded-2xl shadow-xl">
      <h2 className="text-xl font-semibold">CPU Usage</h2>
      <p className="text-4xl text-blue-500 font-bold mt-4">{cpu ?? 'Loading...'}%</p>
    </div>
  );
}