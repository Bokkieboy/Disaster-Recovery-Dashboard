import React from 'react';

export default function App() {
  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white hidden md:block">
        <div className="p-6 text-2xl font-bold border-b border-gray-700">
          DR Dashboard
        </div>
        <nav className="p-4">
          <ul className="space-y-4">
            <li><a href="#" className="hover:text-blue-400">Home</a></li>
            <li><a href="#" className="hover:text-blue-400">Backups</a></li>
            <li><a href="#" className="hover:text-blue-400">Recovery</a></li>
            <li><a href="#" className="hover:text-blue-400">Logs</a></li>
          </ul>
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 bg-gray-100 p-6">
        {/* Header */}
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">Welcome to the Disaster Recovery Dashboard</h1>
          <p className="text-gray-600 mt-2">Monitor and manage your recovery infrastructure.</p>
        </header>

        {/* Content Cards */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold text-gray-800">Last Backup</h2>
            <p className="mt-2 text-gray-600">April 21, 2025 at 02:13 AM</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold text-gray-800">Status</h2>
            <p className="mt-2 text-green-600 font-bold">All systems operational</p>
          </div>
          <div className="bg-white p-6 rounded-2xl shadow hover:shadow-lg transition">
            <h2 className="text-xl font-semibold text-gray-800">Recovery Points</h2>
            <p className="mt-2 text-gray-600">5 snapshots available</p>
          </div>
        </section>
      </main>
    </div>
  );
}