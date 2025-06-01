import React, { useState, useEffect } from "react";
// import CPUMonitor from './components/CPUMonitor'; // Assuming this might be used later or was part of a larger setup
import ConfirmationModal from './components/ConfirmationModal';

// Image URLs (replace with your own or static CDN if needed)
const EC2_ICON = "https://ugc.same-assets.com/8wU1D40_3LpE9jfPvDe3E9Bii0g185xi.jpeg"; // microchip icon
const SERVER_ICON = "https://cdn.hashnode.com/res/hashnode/image/upload/v1732626640426/fb3d271a-b153-4422-977d-5a4ebcdffa79.png"; // server banks isometric

const devicesInitial = [
  {
    id: 1,
    type: "Amazon EC2",
    icon: EC2_ICON,
    uptime: "Unknown", // changed from percentage to string
    cpuUsage: 0, // in percentage
    region: "eu-west-2",
  },
  {
    id: 2,
    type: "Amazon EC2",
    icon: EC2_ICON,
    uptime: "Unknown",
    cpuUsage: 30,
    region: "us-west-2",
  },
  {
    id: 3,
    type: "Home Server",
    icon: SERVER_ICON,
    uptime: "Unknown",
    cpuUsage: 20,
    region: "local",
  },
];

type Device = {
  id: number;
  type: string;
  icon: string;
  uptime: string;
  cpuUsage: number;
  region: string;
};

// --- Step 2: Remove onReboot from DeviceCardProps ---
type DeviceCardProps = {
  device: Device;
  onShutdown: () => void;
  // onReboot: () => void; // Removed
  onOn: () => void;
  onDelete: () => void;
};

// --- Step 3: Remove onReboot from DeviceCard parameters ---
function DeviceCard({ device, onShutdown, onOn, onDelete }: DeviceCardProps) {
  return (
    
    <div
      style={{ width: 200 }}
      className="flex flex-col items-center p-3 rounded-md bg-black/10 shadow-md mx-3 mt-6"
    >
      <div className="text-lg font-bold mb-1 text-white">Uptime: {device.uptime}</div>
      <img
        src={device.icon}
        alt={device.type}
        style={{ width: 72, height: 72, objectFit: "contain" }}
        className="mb-2 rounded-lg border"
      />
      <div className="font-semibold text-center text-sm mb-1 text-slate-400">
        {device.type}
      </div>
      <div className="text-sm text-gray-500 mb-2">Region: {device.region}</div>
      <div className="text-sm text-gray-500 mb-2">
        CPU: {device.cpuUsage}%
      </div>
      <button
        className="w-full bg-white text-black font-semibold rounded-sm border py-1 shadow mb-1 hover:bg-zinc-100"
        onClick={onShutdown}
      >
        Shutdown
      </button>
      {/* --- Step 1: Remove the Reboot button --- */}
      {/*
      <button
        className="w-full bg-white text-black font-semibold rounded-sm border py-1 shadow mb-1 hover:bg-zinc-100"
        onClick={onReboot} // This onClick would also be removed
      >
        Reboot
      </button>
      */}
      <button
        className="w-full bg-white text-black font-semibold rounded-sm border py-1 shadow hover:bg-zinc-100"
        onClick={onOn}
      >
        Switch on
      </button>
      <button
        className="w-full bg-red-500 text-white font-semibold rounded-sm border py-1 shadow hover:bg-red-600 mt-1" // Added mt-1 for spacing if needed
        onClick={onDelete}
      >
        Delete
      </button>
    </div>
  );
}

// UptimeBar component remains unchanged
function UptimeBar({ value = 90 }) {
  // value = percentage
  const totalSegments = 30;
  const filled = Math.round((value / 100) * totalSegments);
  return (
    <div className="w-full max-w-2xl mx-auto flex flex-col items-center mb-2">
      <div className="flex w-full justify-between">
        <span className="text-white text-xs">0%</span>
        <span className="text-white text-xs">Uptime</span>
        <span className="text-white text-xs">100%</span>
      </div>
      <div className="flex w-full space-x-1 mt-1">
        {Array.from({ length: totalSegments }).map((_, i) => (
          <div
            key={`uptime-bar-segment-${i}`}
            className={`h-6 flex-1 rounded-[2px] ${
              i < filled ? "bg-green-400" : "bg-zinc-700"
            }`}
          />
        ))}
      </div>
    </div>
  );
}


function App() {
  const [devices, setDevices] = useState(devicesInitial);
  const [greeting] = useState("Hello, User!");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deviceToDelete, setDeviceToDelete] = useState<number | null>(null);

  useEffect(() => {
    const fetchUptime = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/uptime');
        const data = await res.json();
        setDevices((prevDevices) =>
          prevDevices.map((device) =>
            device.id === 1
              ? {
                  ...device,
                  uptime: data.uptime,
                  // uptimeDays: data.uptime_days // Assuming uptimeDays might still be useful for other logic
                }
              : device
          )
        );
      } catch (error) {
        console.error("Error fetching uptime:", error);
        // Optionally update UI to show uptime is unavailable for device.id === 1
        setDevices((prevDevices) =>
          prevDevices.map((device) =>
            device.id === 1 ? { ...device, uptime: "Error" } : device
          )
        );
      }
    };

    const fetchCPU = async () => {
      try {
        const res = await fetch('http://localhost:5000/api/cpu');
        const data = await res.json();
        setDevices((prevDevices) =>
          prevDevices.map((device) =>
            device.id === 1 ? { ...device, cpuUsage: data.cpu } : device
          )
        );
      } catch (error) {
        console.error("Error fetching CPU metrics:", error);
         // Optionally update UI to show CPU usage is unavailable for device.id === 1
         setDevices((prevDevices) =>
          prevDevices.map((device) =>
            device.id === 1 ? { ...device, cpuUsage: NaN } : device // Or some other indicator
          )
        );
      }
    };

    fetchUptime();
    const upTimeInterval = setInterval(fetchUptime, 30000);

    fetchCPU();
    const cpuInterval = setInterval(fetchCPU, 30000);

    return () => {
      clearInterval(upTimeInterval);
      clearInterval(cpuInterval);
    };
  }, []);

  const handleShutdown = async (id: number) => {
    try {
      if (id === 1) {
        await fetch('http://localhost:5000/api/stop', { method: 'POST' });
        alert(`Shutdown initiated for EC2 instance (ID: ${id}).`);
      } else {
        alert(`Shutdown action for device ID ${id} (not EC2 id:1) - no API call configured.`);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      alert("Failed to shutdown: " + errorMessage);
    }
  };
  
  
  const handleAdd = async (id: number) => {
    try {
      // Assuming you only want to start the specific EC2 instance (id: 1) for now
      if (id === 1) {
        await fetch('http://localhost:5000/api/start', { method: 'POST' });
        alert(`Start initiated for EC2 instance (ID: ${id}).`);
      } else {
        alert(`Start action for device ID ${id} (not EC2 id:1) - no API call configured.`);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      alert("Failed to start: " + errorMessage);
    }
  };
  
  const handleDelete = (id: number) => {
    setIsModalOpen(true);
    setDeviceToDelete(id);
  };

  const confirmDelete = () => {
    if (deviceToDelete !== null) {
      setDevices(devices.filter((device) => device.id !== deviceToDelete));
    }
    setIsModalOpen(false);
    setDeviceToDelete(null);
  };

  const cancelDelete = () => {
    setIsModalOpen(false);
    setDeviceToDelete(null);
  };

  const handleAddAnotherDevice = () => {
    console.log("Add another device button clicked");
    const nextId = devices.length > 0 ? Math.max(...devices.map((d) => d.id)) + 1 : 1;
    setDevices([
      ...devices,
      {
        id: nextId,
        type: "Amazon EC2", // Default new device type
        icon: EC2_ICON,
        uptime: "Unknown",
        cpuUsage: 0,
        region: "eu-west-2", // Default region
      },
    ]);
  };

  return (
    <div className="min-h-screen bg-[#111132]">
      <div className="bg-black w-full py-5 flex items-center justify-center relative">
        <h1 className="text-2xl font-semibold text-white">Disaster Recovery</h1>
        <div
          className="absolute right-8 top-1/2 -translate-y-1/2 bg-white rounded p-4 shadow text-black min-w-[140px] flex items-center justify-center"
          style={{ boxShadow: "0 2px 10px rgba(0,0,0,0.07)" }}
        >
          {greeting}
        </div>
      </div>

      <div className="flex flex-row justify-center flex-wrap w-full max-w-5xl mx-auto mt-12">
        {devices.map((device) => (
          <DeviceCard
            key={device.id}
            device={device}
            onShutdown={() => handleShutdown(device.id)}
            // --- Step 4: Remove onReboot prop passed to DeviceCard ---
            // onReboot={() => handleReboot(device.id)} // Removed
            onOn={() => handleAdd(device.id)}
            onDelete={() => handleDelete(device.id)}
          />
        ))}

        <div className="flex flex-col items-center justify-center ml-8 mt-12">
          <button
            className="bg-indigo-400 text-white px-8 py-5 rounded-lg shadow-lg hover:bg-indigo-500 text-lg font-semibold"
            onClick={handleAddAnotherDevice}
            style={{ minWidth: 190 }}
          >
            Add another device
          </button>
        </div>
      </div>
      <ConfirmationModal
        isOpen={isModalOpen}
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
        message="Are you sure you want to delete this instance?"
      />
    </div>
  );
}

export default App;