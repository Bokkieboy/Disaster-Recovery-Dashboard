import React, { useState, useEffect, useCallback } from "react";
// import CPUMonitor from './components/CPUMonitor'; 
import ConfirmationModal from './components/ConfirmationModal';

// Image URLs
const EC2_ICON = "https://ugc.same-assets.com/8wU1D40_3LpE9jfPvDe3E9Bii0g185xi.jpeg";
const SERVER_ICON = "https://cdn.hashnode.com/res/hashnode/image/upload/v1732626640426/fb3d271a-b153-4422-977d-5a4ebcdffa79.png";

// --- Device Type Definition ---
type Device = {
  id: number; 
  type: string; 
  icon: string;
  uptime: string;
  cpuUsage: number | string; 
  region: string; 
  awsInstanceId: string | null; 
  awsRegion: string | null;    
  status: string;              
};

// --- Initial Device Configuration ---
// Ensure awsInstanceId and awsRegion match your backend .env configuration
const devicesInitial: Device[] = [
  {
    id: 1,
    type: "Primary EC2", 
    icon: EC2_ICON,
    uptime: "Unknown",
    cpuUsage: 0,
    region: "eu-west-2", 
    awsInstanceId: "i-086152cb766c949b7", 
    awsRegion: "eu-west-2",                         
    status: "Unknown",
  },
  {
    id: 2,
    type: "Secondary EC2",
    icon: EC2_ICON,
    uptime: "Unknown",
    cpuUsage: 0,
    region: "eu-west-1", 
    awsInstanceId: "i-0526477f636ebfeb5", // Removed leading space
    awsRegion: "eu-west-1",                         
    status: "Unknown",
  },
  {
    id: 3, 
    type: "Home Server",
    icon: SERVER_ICON,
    uptime: "Unknown",
    cpuUsage: 0, 
    region: "local",
    awsInstanceId: null, 
    awsRegion: null,
    status: "Unknown", 
  },
];

// --- DeviceCard Props ---
type DeviceCardProps = {
  device: Device;
  onShutdown: () => void; // These are called by DeviceCard, App.tsx provides the implementation
  onOn: () => void;
  onDelete: () => void;
};

// --- DeviceCard Component (Slightly Enhanced Styling) ---
function DeviceCard({ device, onShutdown, onOn, onDelete }: DeviceCardProps) {
  let statusColor = "text-yellow-400"; // Default for Unknown/Pending
  if (device.status === "running") statusColor = "text-green-400";
  else if (device.status === "stopped") statusColor = "text-red-500";
  else if (device.status === "Error" || device.status === "Fetch Err" || device.status === "Status Err") statusColor = "text-orange-400";

  return (
    <div
      style={{ width: 230 }} // Adjusted width
      className="flex flex-col items-center p-4 rounded-lg bg-gray-800/60 shadow-xl mx-2 my-3 text-gray-200 border border-gray-700/50"
    >
      <img
        src={device.icon}
        alt={device.type}
        style={{ width: 60, height: 60, objectFit: "contain" }}
        className="mb-3 rounded-md border-2 border-gray-600 p-0.5"
      />
      <div className="font-bold text-md mb-1 text-center truncate w-full px-1 text-white" title={device.type}>
        {device.type}
      </div>
      {device.awsInstanceId && (
        <div className="text-xs text-gray-400 mb-1 truncate w-full text-center px-1" title={device.awsInstanceId}>
          ID: {device.awsInstanceId}
        </div>
      )}
      <div className="text-xs text-gray-400 mb-2">Region: {device.region}</div>
      
      <div className="text-sm mb-1">Status: <span className={`font-semibold ${statusColor}`}>{device.status}</span></div>
      <div className="text-sm mb-1">Uptime: {device.uptime}</div>
      <div className="text-sm mb-3">
        CPU: {typeof device.cpuUsage === 'number' ? `${device.cpuUsage}%` : device.cpuUsage}
      </div>

      {/* EC2 Controls: Only show if it's an EC2 instance */}
      {device.awsInstanceId && device.awsRegion && (
        <>
          <button
            className={`w-full text-white font-semibold rounded-md py-1.5 shadow-md mb-2 transition-all duration-150 ease-in-out transform hover:scale-105
                        ${device.status !== 'running' ? 'bg-gray-600 cursor-not-allowed opacity-70' : 'bg-red-600 hover:bg-red-700'}`}
            onClick={onShutdown}
            disabled={device.status !== 'running'}
          >
            Shutdown
          </button>
          <button
            className={`w-full text-white font-semibold rounded-md py-1.5 shadow-md mb-2 transition-all duration-150 ease-in-out transform hover:scale-105
                        ${device.status === 'running' ? 'bg-gray-600 cursor-not-allowed opacity-70' : 'bg-green-500 hover:bg-green-600'}`}
            onClick={onOn}
            disabled={device.status === 'running'}
          >
            Switch On
          </button>
        </>
      )}
      {/* Local Delete Button */}
      <button
        className="w-full bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-md py-1.5 shadow-md mt-1 transition-colors duration-150"
        onClick={onDelete}
      >
        Remove (Local)
      </button>
    </div>
  );
}

// UptimeBar component (not actively used in App's return, but kept as per user's code)
// function UptimeBar({ value = 90 }) { ... } // Kept for completeness if needed later

// --- Main App Component ---
function App() {
  const [devices, setDevices] = useState<Device[]>(devicesInitial);
  const [greeting] = useState("Hello, User!"); // Can be dynamic
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deviceToDeleteId, setDeviceToDeleteId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true); // For initial load
  const [fetchError, setFetchError] = useState<string | null>(null); // For API errors

  // Use environment variable for API base URL if available (Vite specific)
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

  const fetchData = useCallback(async () => {
    // Don't set global isLoading for interval refreshes, only for initial
    // setFetchError(null); // Clear previous errors
    try {
      const [cpuResponse, uptimeResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/cpu`),
        fetch(`${API_BASE_URL}/uptime`)
      ]);

      let cpuData: any[] = [];
      let uptimeData: any[] = [];
      let currentFetchError = null;

      if (cpuResponse.ok) {
        cpuData = await cpuResponse.json();
      } else {
        console.error("CPU API Error:", cpuResponse.status, await cpuResponse.text());
        currentFetchError = `CPU API Error (${cpuResponse.status})`;
      }

      if (uptimeResponse.ok) {
        uptimeData = await uptimeResponse.json();
      } else {
        console.error("Uptime API Error:", uptimeResponse.status, await uptimeResponse.text());
        currentFetchError = `${currentFetchError ? currentFetchError + '; ' : ''}Uptime API Error (${uptimeResponse.status})`;
      }
      
      if (currentFetchError) {
          setFetchError(currentFetchError + ". Check backend logs.");
      } else {
          setFetchError(null); // Clear error if all fetches were okay this time
      }

      setDevices(prevDevices =>
        prevDevices.map(device => {
          if (device.awsInstanceId && device.awsRegion) {
            const deviceCpuData = cpuData.find(
              (d: any) => d.instanceId === device.awsInstanceId && d.region === device.awsRegion
            );
            const deviceUptimeData = uptimeData.find(
              (d: any) => d.instanceId === device.awsInstanceId && d.region === device.awsRegion
            );
            
            // Debugging log for the primary instance
            // if (device.awsInstanceId === "i-0dc17676ee962edcd") {
            //    console.log("Updating i-0dc17676ee962edcd:", { deviceCpuData, deviceUptimeData });
            // }

            return {
              ...device,
              cpuUsage: deviceCpuData ? (deviceCpuData.cpu !== null ? deviceCpuData.cpu : (deviceCpuData.error ? `CPU Err` : 'N/A')) : (currentFetchError && !cpuData.length ? 'API Err' : device.cpuUsage),
              uptime: deviceUptimeData ? (deviceUptimeData.uptime || (deviceUptimeData.error ? `Uptime Err` : 'N/A')) : (currentFetchError && !uptimeData.length ? 'API Err' : device.uptime),
              status: deviceUptimeData ? (deviceUptimeData.status || (deviceUptimeData.error ? `Status Err` : 'Unknown')) : (currentFetchError && !uptimeData.length ? 'API Err' : device.status),
            };
          }
          return device;
        })
      );

    } catch (e: any) {
      console.error("Critical error in fetchData:", e);
      setFetchError(e.message || "Failed to fetch data. Is the backend running?");
      setDevices(prevDevs => prevDevs.map(d => ({ // Fallback error state
        ...d,
        cpuUsage: d.awsInstanceId ? 'Fetch Fail' : d.cpuUsage,
        uptime: d.awsInstanceId ? 'Fetch Fail' : d.uptime,
        status: d.awsInstanceId ? 'Fetch Fail' : d.status,
      })));
    } finally {
      setIsLoading(false); // Initial loading is done
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    setIsLoading(true); // Set loading for the very first fetch
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  // --- Action Handlers ---
  const handleActionConfirm = (message: string, actionFn: () => void) => {
    // Replace with a proper modal in a real app
    if (window.confirm(message)) {
      actionFn();
    }
  };

  const handleOn = async (awsInstanceId: string | null, awsRegion: string | null) => {
    if (!awsInstanceId || !awsRegion) {
      alert("Action not available: AWS configuration missing for this device.");
      return;
    }
    handleActionConfirm(
      `Are you sure you want to START instance ${awsInstanceId} in ${awsRegion}?`,
      async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/start?instance_id=${awsInstanceId}&region=${awsRegion}`, { method: 'POST' });
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || `Failed to start ${awsInstanceId}`);
          alert(data.message || `Start initiated for ${awsInstanceId}.`);
          setTimeout(fetchData, 2000); // Refresh data sooner after action
        } catch (err: any) {
          alert(`Start Error: ${err.message}`);
        }
      }
    );
  };

  const handleShutdown = async (awsInstanceId: string | null, awsRegion: string | null) => {
    if (!awsInstanceId || !awsRegion) {
      alert("Action not available: AWS configuration missing for this device.");
      return;
    }
    handleActionConfirm(
      `Are you sure you want to SHUTDOWN instance ${awsInstanceId} in ${awsRegion}?`,
      async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/stop?instance_id=${awsInstanceId}&region=${awsRegion}`, { method: 'POST' });
          const data = await response.json();
          if (!response.ok) throw new Error(data.error || `Failed to shutdown ${awsInstanceId}`);
          alert(data.message || `Shutdown initiated for ${awsInstanceId}.`);
          setTimeout(fetchData, 2000); 
        } catch (err: any) {
          alert(`Shutdown Error: ${err.message}`);
        }
      }
    );
  };
  
  const handleDelete = (id: number) => {
    setDeviceToDeleteId(id);
    setIsModalOpen(true);
  };

  const confirmDelete = () => {
    if (deviceToDeleteId !== null) {
      setDevices(devices.filter((device) => device.id !== deviceToDeleteId));
    }
    setIsModalOpen(false);
    setDeviceToDeleteId(null);
  };

  const cancelDelete = () => {
    setIsModalOpen(false);
    setDeviceToDeleteId(null);
  };

  const handleAddAnotherDevice = () => {
    const nextId = devices.length > 0 ? Math.max(...devices.map((d) => d.id)) + 1 : 1;
    const newDevice: Device = {
      id: nextId,
      type: "New Local Server", 
      icon: SERVER_ICON,        
      uptime: "Unknown",
      cpuUsage: 0,
      region: "local",          
      awsInstanceId: null,      
      awsRegion: null,          
      status: "Unknown",        
    };
    setDevices(prevDevices => [...prevDevices, newDevice]);
  };

  // --- JSX Structure ---
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 text-gray-100 font-sans">
      <header className="bg-black/70 backdrop-blur-md w-full py-4 shadow-2xl sticky top-0 z-50 border-b border-purple-700/40">
        <div className="container mx-auto flex items-center justify-between px-4 sm:px-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">Cloud DR Dashboard</h1>
          <div className="bg-white/10 rounded-lg p-2 px-4 shadow text-xs sm:text-sm min-w-[120px] text-center">
            {greeting}
          </div>
        </div>
      </header>

      <main className="container mx-auto p-4 sm:p-6 mt-6">
        {isLoading && <div className="text-center text-xl py-10 text-purple-300">Initializing & Fetching Data... <span className="animate-ping">✨</span></div>}
        {fetchError && !isLoading && <div className="text-center text-red-300 bg-red-800/50 p-3 rounded-md mb-6 shadow-lg">{fetchError}</div>}
        
        {!isLoading && (
          <div className="flex flex-row flex-wrap justify-center items-start -mx-2">
            {devices.map((device) => (
              <DeviceCard
                key={device.id}
                device={device}
                onShutdown={() => handleShutdown(device.awsInstanceId, device.awsRegion)}
                onOn={() => handleOn(device.awsInstanceId, device.awsRegion)}
                onDelete={() => handleDelete(device.id)}
              />
            ))}
            <div 
                className="flex flex-col items-center justify-center p-4 rounded-lg bg-gray-800/60 shadow-xl mx-2 my-3 border border-dashed border-gray-700/50 hover:border-purple-500 transition-all" 
                style={{width: 230, minHeight: 380 }} // Match DeviceCard height roughly
            >
                 <button
                    className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-lg shadow-lg text-md font-semibold transition-colors duration-150 transform hover:scale-105"
                    onClick={handleAddAnotherDevice}
                >
                    + Add Device
                </button>
                <p className="text-xs text-gray-500 mt-3 text-center"> (Adds local placeholder) </p>
            </div>
          </div>
        )}
      </main>

      <ConfirmationModal
        isOpen={isModalOpen}
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
        message="Are you sure you want to remove this device from the dashboard? This is a local action and does not affect the actual server."
      />
      
      <footer className="text-center py-6 mt-8 text-xs sm:text-sm text-gray-500 border-t border-purple-700/20">
        Cloud Disaster Recovery Dashboard &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
} 

export default App;
