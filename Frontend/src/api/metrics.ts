export async function fetchCPU(): Promise<number> {
    const res = await fetch('http://localhost:3001/metrics');
    const data = await res.json();
    return data.cpu;
  }