import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

interface SystemMetrics {
  timestamp: number;
  cpu: {
    overall: number;
    perCore: number[];
    processes: Array<{ name: string; usage: number }>;
  };
  memory: {
    total: number;
    used: number;
    free: number;
    swapTotal: number;
    swapUsed: number;
  };
  disk: {
    readSpeed: number;
    writeSpeed: number;
    ioTime: number;
  };
  network: {
    bytesIn: number;
    bytesOut: number;
    packetsIn: number;
    packetsOut: number;
  };
  gpu?: {
    utilization: number;
    memoryUsed: number;
    memoryTotal: number;
    temperature: number;
  };
  temperature?: {
    cpu: number;
    gpu?: number;
    disk?: number[];
  };
}

interface SystemPerformanceProps {
  data: SystemMetrics[];
  realTime?: boolean;
  refreshInterval?: number;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export const SystemPerformance: React.FC<SystemPerformanceProps> = ({
  data,
  realTime = false,
  refreshInterval = 1000,
}) => {
  const [currentMetrics, setCurrentMetrics] = useState<SystemMetrics | null>(
    data.length > 0 ? data[data.length - 1] : null
  );
  const [historicalData, setHistoricalData] = useState<SystemMetrics[]>(data);

  useEffect(() => {
    if (realTime && currentMetrics) {
      const interval = setInterval(() => {
        setCurrentMetrics((prev) => {
          if (!prev) return null;
          const newData = {
            ...prev,
            timestamp: Date.now(),
            cpu: {
              ...prev.cpu,
              overall: Math.random() * 100,
              perCore: prev.cpu.perCore.map(() => Math.random() * 100),
            },
            memory: {
              ...prev.memory,
              used: prev.memory.used + (Math.random() - 0.5) * 100,
            },
          };
          setHistoricalData((history) => {
            const updated = [...history, newData];
            return updated.slice(-3600);
          });
          return newData;
        });
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [realTime, refreshInterval, currentMetrics]);

  if (!currentMetrics) {
    return <div className="p-4 text-gray-500">No system metrics available</div>;
  }

  const cpuData = historicalData.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    cpu: d.cpu.overall,
  }));

  const memoryData = historicalData.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    used: d.memory.used,
    free: d.memory.free,
    swapUsed: d.memory.swapUsed,
  }));

  const diskData = historicalData.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    read: d.disk.readSpeed,
    write: d.disk.writeSpeed,
  }));

  const networkData = historicalData.map((d) => ({
    time: new Date(d.timestamp).toLocaleTimeString(),
    in: d.network.bytesIn,
    out: d.network.bytesOut,
  }));

  const perCoreData = currentMetrics.cpu.perCore.map((usage, idx) => ({
    core: `Core ${idx}`,
    usage,
  }));

  const gpuData = currentMetrics.gpu
    ? [
        {
          name: 'GPU Usage',
          value: currentMetrics.gpu.utilization,
          fill: '#8884d8',
        },
      ]
    : [];

  return (
    <div className="space-y-6 p-6">
      <h2 className="text-2xl font-bold text-gray-800">System Performance</h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">CPU Usage (Overall)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="cpu"
                stroke="#8884d8"
                fill="#8884d8"
                fillOpacity={0.6}
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-2 text-center text-3xl font-bold text-gray-700">
            {currentMetrics.cpu.overall.toFixed(1)}%
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Memory Usage</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={memoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip
                formatter={(value: number) => [
                  `${(value / 1024 / 1024 / 1024).toFixed(2)} GB`,
                  'Value',
                ]}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="used"
                stackId="1"
                stroke="#82ca9d"
                fill="#82ca9d"
                name="Used"
              />
              <Area
                type="monotone"
                dataKey="free"
                stackId="1"
                stroke="#ffc658"
                fill="#ffc658"
                name="Free"
              />
            </AreaChart>
          </ResponsiveContainer>
          <div className="mt-2 text-center text-sm text-gray-600">
            {((currentMetrics.memory.used / currentMetrics.memory.total) * 100).toFixed(1)}% used (
            {(currentMetrics.memory.used / 1024 / 1024 / 1024).toFixed(2)} GB /{' '}
            {(currentMetrics.memory.total / 1024 / 1024 / 1024).toFixed(2)} GB)
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">CPU Usage (Per Core)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={perCoreData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="core" />
              <YAxis domain={[0, 100]} />
              <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Usage']} />
              <Bar dataKey="usage" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Disk I/O</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={diskData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip formatter={(value: number) => [`${(value / 1024 / 1024).toFixed(2)} MB/s`, '']} />
              <Legend />
              <Line
                type="monotone"
                dataKey="read"
                stroke="#82ca9d"
                name="Read Speed"
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="write"
                stroke="#ffc658"
                name="Write Speed"
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div className="mt-2 text-center text-sm text-gray-600">
            Current: {(currentMetrics.disk.readSpeed / 1024 / 1024).toFixed(2)} MB/s read /{' '}
            {(currentMetrics.disk.writeSpeed / 1024 / 1024).toFixed(2)} MB/s write
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Network Throughput</h3>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={networkData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" hide />
              <YAxis />
              <Tooltip
                formatter={(value: number) => [
                  `${(value / 1024 / 1024).toFixed(2)} MB`,
                  'Data',
                ]}
              />
              <Legend />
              <Area
                type="monotone"
                dataKey="in"
                stackId="1"
                stroke="#8884d8"
                fill="#8884d8"
                name="Bytes In"
              />
              <Area
                type="monotone"
                dataKey="out"
                stackId="1"
                stroke="#82ca9d"
                fill="#82ca9d"
                name="Bytes Out"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {currentMetrics.gpu && (
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">GPU Utilization</h3>
            <ResponsiveContainer width="100%" height={250}>
              <RadialBarChart
                cx="50%"
                cy="50%"
                innerRadius="20%"
                outerRadius="90%"
                data={gpuData}
                startAngle={180}
                endAngle={0}
              >
                <RadialBar
                  minAngle={15}
                  label={{ position: 'insideStart', fill: '#fff' }}
                  background
                  clockWise
                  dataKey="value"
                />
                <Tooltip formatter={(value) => [`${value}%`, 'Usage']} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="mt-2 text-center">
              <div className="text-sm text-gray-600">
                Temperature: {currentMetrics.gpu.temperature}°C
              </div>
              <div className="text-sm text-gray-600">
                Memory: {(currentMetrics.gpu.memoryUsed / 1024 / 1024).toFixed(2)} MB /{' '}
                {(currentMetrics.gpu.memoryTotal / 1024 / 1024).toFixed(2)} MB
              </div>
            </div>
          </div>
        )}

        {currentMetrics.temperature && (
          <div className="bg-white p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-4">Temperature Monitoring</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">CPU Temperature</span>
                <span className="font-semibold text-lg">
                  {currentMetrics.temperature.cpu}°C
                </span>
              </div>
              {currentMetrics.temperature.gpu && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">GPU Temperature</span>
                  <span className="font-semibold text-lg">
                    {currentMetrics.temperature.gpu}°C
                  </span>
                </div>
              )}
              {currentMetrics.temperature.disk &&
                currentMetrics.temperature.disk.map((temp, idx) => (
                  <div key={idx} className="flex justify-between items-center">
                    <span className="text-gray-600">Disk {idx} Temperature</span>
                    <span className="font-semibold text-lg">{temp}°C</span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Top CPU Processes</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Process</th>
                <th className="text-right py-2">CPU Usage (%)</th>
              </tr>
            </thead>
            <tbody>
              {currentMetrics.cpu.processes
                .sort((a, b) => b.usage - a.usage)
                .slice(0, 10)
                .map((process, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="py-2">{process.name}</td>
                    <td className="text-right py-2">{process.usage.toFixed(1)}%</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default SystemPerformance;
