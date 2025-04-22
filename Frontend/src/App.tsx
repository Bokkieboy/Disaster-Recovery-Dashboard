import React, { useState } from "react";

// Image URLs (replace with your own or static CDN if needed)
const EC2_ICON = "https://ugc.same-assets.com/8wU1D40_3LpE9jfPvDe3E9Bii0g185xi.jpeg"; // microchip icon
const SERVER_ICON = "https://cdn.hashnode.com/res/hashnode/image/upload/v1732626640426/fb3d271a-b153-4422-977d-5a4ebcdffa79.png"; // server banks isometric

const devicesInitial = [
  {
    id: 1,
    type: "Amazon EC2",
    icon: EC2_ICON,
    uptime: 95, // in percentage
    cpuUsage: 45, // in percentage
    ramUsage: 70, // in percentage
    diskUsage: 60, // in percentage
    region: "us-east-1",
  },
  {
    id: 2,
    type: "Amazon EC2",
    icon: EC2_ICON,
    uptime: 85,
    cpuUsage: 30,
    ramUsage: 50,
    diskUsage: 40,
    region: "us-west-2",
  },
  {
    id: 3,
    type: "Home Server",
    icon: SERVER_ICON,
    uptime: 99,
    cpuUsage: 20,
    ramUsage: 40,
    diskUsage: 30,
    region: "local",
  },
];

function DeviceCard({ device, onShutdown, onReboot, onAdd }) {
  return (
    <div
      style={{ width: 200 }}
      className="flex flex-col items-center p-3 rounded-md bg-black/10 shadow-md mx-3 mt-6"
    >
      <div className="text-lg font-bold mb-1 text-white">{device.uptime}% Uptime</div> {/* Added text-white */}
      <img
        src={device.icon}
        alt={device.type}
        style={{ width: 72, height: 72, objectFit: "contain" }}
        className="mb-2 rounded-lg border"
      />
      <div className="font-semibold text-center text-sm mb-1">
        {device.type}
      </div>
      <div className="text-sm text-gray-500 mb-2">Region: {device.region}</div>
      <div className="text-sm text-gray-500 mb-2">
        CPU: {device.cpuUsage}%, RAM: {device.ramUsage}%, Disk: {device.diskUsage}%
      </div>
      <button
        className="w-full bg-white text-black font-semibold rounded-sm border py-1 shadow mb-1 hover:bg-zinc-100"
        onClick={onShutdown}
      >
        Shutdown
      </button>
      <button
        className="w-full bg-white text-black font-semibold rounded-sm border py-1 shadow mb-1 hover:bg-zinc-100"
        onClick={onReboot}
      >
        Reboot
      </button>
      <button
        className="w-full bg-white text-black font-semibold rounded-sm border py-1 shadow hover:bg-zinc-100"
        onClick={onAdd}
      >
        Add
      </button>
    </div>
  );
}

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
  const globalUptime = Math.max(...devices.map((d) => d.uptime)); // demo

  // Simulated handlers
  const handleShutdown = (id) => {
    // TODO: Wire this to API to shutdown instance
    alert(`Shutdown triggered for device ID ${id}`);
  };
  const handleReboot = (id) => {
    // TODO: Wire this to API to reboot instance
    alert(`Reboot triggered for device ID ${id}`);
  };
  const handleAdd = (id) => {
    // TODO: Wire this to API to add/duplicate instance
    alert(`Add triggered for device ID ${id}`);
  };
  const handleAddAnotherDevice = () => {
    const nextId = Math.max(...devices.map((d) => d.id)) + 1;
    setDevices([
      ...devices,
      {
        id: nextId,
        type: "Amazon EC2",
        icon: EC2_ICON,
        uptime: 0,
        cpuUsage: 0,
        ramUsage: 0,
        diskUsage: 0,
        region: "us-east-1",
      },
    ]);
  };

  return (
    <div className="min-h-screen bg-[#111132]">
      {/* Top Bar */}
      <div className="bg-black w-full py-5 flex items-center justify-center relative">
        <h1 className="text-2xl font-semibold text-white">Disaster Recovery</h1>
        <div
          className="absolute right-8 top-1/2 -translate-y-1/2 bg-white rounded p-4 shadow text-black min-w-[140px] flex items-center justify-center"
          style={{ boxShadow: "0 2px 10px rgba(0,0,0,0.07)" }}
        >
          {greeting}
        </div>
      </div>

      {/* Uptime */}
      <div className="w-full flex flex-col items-center mt-10">
        <UptimeBar value={globalUptime} />
      </div>

      {/* Devices List */}
      <div className="flex flex-row justify-center flex-wrap w-full max-w-5xl mx-auto mt-12">
        {devices.map((device) => (
          <DeviceCard
            key={device.id}
            device={device}
            onShutdown={() => handleShutdown(device.id)}
            onReboot={() => handleReboot(device.id)}
            onAdd={() => handleAdd(device.id)}
          />
        ))}

        {/* Add another device button */}
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
    </div>
  );
}

export default App;
