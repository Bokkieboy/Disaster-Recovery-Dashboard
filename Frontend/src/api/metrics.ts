export async function fetchCPU(): Promise<number> {
    const res = await fetch('http://localhost:5000/api/cpu');
    const data = await res.json();
    return data.cpu;
  }