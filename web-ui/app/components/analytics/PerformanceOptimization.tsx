import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Treemap,
} from 'recharts';

interface Bottleneck {
  id: string;
  type: 'cpu' | 'memory' | 'disk' | 'network' | 'database' | 'api';
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  impact: {
    performance: number;
    throughput: number;
    latency: number;
  };
  affectedComponents: string[];
  recommendation: {
    priority: 'low' | 'medium' | 'high';
    action: string;
    expectedImprovement: string;
    effort: 'low' | 'medium' | 'high';
    estimatedTime: string;
  };
}

interface OptimizationRecommendation {
  id: string;
  category: string;
  title: string;
  description: string;
  currentState: string;
  targetState: string;
  benefits: string[];
  implementation: {
    steps: string[];
    complexity: 'low' | 'medium' | 'high';
    resources: string[];
    risks: string[];
  };
  metrics: {
    metric: string;
    current: number;
    target: number;
    unit: string;
  }[];
}

interface PerformanceOptimizationProps {
  bottlenecks: Bottleneck[];
  recommendations: OptimizationRecommendation[];
  performanceData?: any[];
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

export const PerformanceOptimization: React.FC<PerformanceOptimizationProps> = ({
  bottlenecks,
  recommendations,
  performanceData,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'bottlenecks' | 'recommendations'>('overview');
  const [selectedBottleneck, setSelectedBottleneck] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const categories = Array.from(new Set(recommendations.map((r) => r.category)));

  const filteredRecommendations = selectedCategory
    ? recommendations.filter((r) => r.category === selectedCategory)
    : recommendations;

  const bottlenecksByType = bottlenecks.reduce((acc, b) => {
    acc[b.type] = (acc[b.type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const bottlenecksBySeverity = bottlenecks.reduce((acc, b) => {
    acc[b.severity] = (acc[b.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const impactData = bottlenecks.map((b) => ({
    name: b.type,
    impact: b.impact.performance,
    throughput: b.impact.throughput,
    latency: b.impact.latency,
  }));

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-500';
      case 'high':
        return 'bg-orange-100 text-orange-800 border-orange-500';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800 border-yellow-500';
      case 'low':
        return 'bg-blue-100 text-blue-800 border-blue-500';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-500';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-600';
      case 'medium':
        return 'bg-yellow-500';
      case 'low':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Total Bottlenecks</div>
          <div className="text-3xl font-bold text-gray-800">{bottlenecks.length}</div>
          <div className="text-sm text-gray-500 mt-1">
            {bottlenecks.filter((b) => b.severity === 'critical' || b.severity === 'high').length} high priority
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Recommendations</div>
          <div className="text-3xl font-bold text-blue-600">{recommendations.length}</div>
          <div className="text-sm text-gray-500 mt-1">
            {recommendations.filter((r) => r.implementation.complexity === 'low').length} quick wins
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Avg Performance Impact</div>
          <div className="text-3xl font-bold text-orange-600">
            {bottlenecks.length > 0
              ? (
                  bottlenecks.reduce((sum, b) => sum + b.impact.performance, 0) / bottlenecks.length
                ).toFixed(1)
              : '0'}
            %
          </div>
          <div className="text-sm text-gray-500 mt-1">degradation</div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <div className="text-sm text-gray-600">Potential Savings</div>
          <div className="text-3xl font-bold text-green-600">~45%</div>
          <div className="text-sm text-gray-500 mt-1">if all optimized</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Bottlenecks by Type</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={Object.entries(bottlenecksByType).map(([name, value]) => ({ name, value }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {Object.entries(bottlenecksByType).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Bottlenecks by Severity</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={Object.entries(bottlenecksBySeverity)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="0" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="1" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white p-4 rounded-lg shadow">
        <h3 className="text-lg font-semibold mb-4">Performance Impact Analysis</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={impactData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="impact" fill="#ef4444" name="Performance Impact %" />
            <Bar dataKey="throughput" fill="#f59e0b" name="Throughput Impact %" />
            <Bar dataKey="latency" fill="#8b5cf6" name="Latency Impact %" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );

  const renderBottlenecks = () => (
    <div className="space-y-4">
      <div className="flex gap-2 mb-4">
        {['cpu', 'memory', 'disk', 'network', 'database', 'api'].map((type) => (
          <button
            key={type}
            className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 capitalize"
          >
            {type} ({bottlenecksByType[type] || 0})
          </button>
        ))}
      </div>

      <div className="space-y-3">
        {bottlenecks.map((bottleneck) => (
          <div
            key={bottleneck.id}
            className={`p-4 rounded-lg border-2 cursor-pointer transition ${
              selectedBottleneck === bottleneck.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
            onClick={() =>
              setSelectedBottleneck(selectedBottleneck === bottleneck.id ? null : bottleneck.id)
            }
          >
            <div className="flex justify-between items-start">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <h4 className="text-lg font-semibold capitalize">{bottleneck.type}</h4>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityColor(bottleneck.severity)}`}>
                    {bottleneck.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-gray-700 mb-2">{bottleneck.description}</p>
                <div className="flex gap-4 text-sm text-gray-600">
                  <span>Performance: {bottleneck.impact.performance.toFixed(1)}%</span>
                  <span>Throughput: {bottleneck.impact.throughput.toFixed(1)}%</span>
                  <span>Latency: {bottleneck.impact.latency.toFixed(1)}%</span>
                </div>
              </div>
              <div className="text-2xl">
                {bottleneck.type === 'cpu' && '🖥️'}
                {bottleneck.type === 'memory' && '💾'}
                {bottleneck.type === 'disk' && '💿'}
                {bottleneck.type === 'network' && '🌐'}
                {bottleneck.type === 'database' && '🗄️'}
                {bottleneck.type === 'api' && '🔌'}
              </div>
            </div>

            {selectedBottleneck === bottleneck.id && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h5 className="font-semibold mb-2">Affected Components:</h5>
                <div className="flex flex-wrap gap-2 mb-4">
                  {bottleneck.affectedComponents.map((component) => (
                    <span key={component} className="px-2 py-1 bg-gray-100 rounded text-sm">
                      {component}
                    </span>
                  ))}
                </div>

                <div className="bg-blue-50 p-4 rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <span
                      className={`w-3 h-3 rounded-full ${getPriorityColor(
                        bottleneck.recommendation.priority
                      )}`}
                    />
                    <h5 className="font-semibold">Recommendation</h5>
                    <span className="text-sm text-gray-600">
                      ({bottleneck.recommendation.priority} priority, {bottleneck.recommendation.effort} effort)
                    </span>
                  </div>
                  <p className="text-gray-700 mb-2">{bottleneck.recommendation.action}</p>
                  <div className="text-sm text-gray-600">
                    Expected improvement: {bottleneck.recommendation.expectedImprovement}
                  </div>
                  <div className="text-sm text-gray-600">
                    Estimated time: {bottleneck.recommendation.estimatedTime}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderRecommendations = () => (
    <div className="space-y-4">
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setSelectedCategory(null)}
          className={`px-3 py-1 rounded ${
            !selectedCategory ? 'bg-blue-600 text-white' : 'bg-gray-200'
          }`}
        >
          All
        </button>
        {categories.map((category) => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={`px-3 py-1 rounded ${
              selectedCategory === category ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            {category}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-4">
        {filteredRecommendations.map((rec) => (
          <div key={rec.id} className="bg-white p-6 rounded-lg shadow-lg border border-gray-200">
            <div className="flex justify-between items-start mb-4">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <h3 className="text-xl font-semibold">{rec.title}</h3>
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                    {rec.category}
                  </span>
                </div>
                <p className="text-gray-700">{rec.description}</p>
              </div>
              <span
                className={`px-3 py-1 rounded text-white text-sm ${getPriorityColor(
                  rec.implementation.complexity === 'low' ? 'high' : rec.implementation.complexity === 'medium' ? 'medium' : 'low'
                )}`}
              >
                {rec.implementation.complexity.toUpperCase()}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 p-3 rounded">
                <div className="text-sm text-gray-600 mb-1">Current State</div>
                <div className="text-gray-800">{rec.currentState}</div>
              </div>
              <div className="bg-green-50 p-3 rounded">
                <div className="text-sm text-green-600 mb-1">Target State</div>
                <div className="text-gray-800">{rec.targetState}</div>
              </div>
            </div>

            <div className="mb-4">
              <h4 className="font-semibold mb-2">Expected Benefits:</h4>
              <ul className="list-disc list-inside space-y-1">
                {rec.benefits.map((benefit, idx) => (
                  <li key={idx} className="text-gray-700 text-sm">
                    {benefit}
                  </li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              {rec.metrics.map((metric) => (
                <div key={metric.metric} className="bg-gray-50 p-3 rounded">
                  <div className="text-sm text-gray-600 mb-1">{metric.metric}</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xl font-bold text-gray-800">
                      {metric.current.toFixed(1)}
                    </span>
                    <span className="text-sm text-gray-600">{metric.unit}</span>
                    <span className="text-sm text-green-600">→ {metric.target.toFixed(1)}</span>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-blue-50 p-4 rounded">
              <h4 className="font-semibold mb-2">Implementation Steps:</h4>
              <ol className="list-decimal list-inside space-y-1">
                {rec.implementation.steps.map((step, idx) => (
                  <li key={idx} className="text-gray-700 text-sm">
                    {step}
                  </li>
                ))}
              </ol>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <h5 className="font-semibold text-gray-700 mb-1">Required Resources:</h5>
                <ul className="list-disc list-inside space-y-1">
                  {rec.implementation.resources.map((resource, idx) => (
                    <li key={idx} className="text-gray-600">
                      {resource}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h5 className="font-semibold text-gray-700 mb-1">Potential Risks:</h5>
                <ul className="list-disc list-inside space-y-1">
                  {rec.implementation.risks.map((risk, idx) => (
                    <li key={idx} className="text-gray-600">
                      {risk}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="mt-4 flex gap-2">
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                Implement
              </button>
              <button className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50">
                Schedule
              </button>
              <button className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50">
                View Details
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="border-b">
          <div className="flex gap-4 px-6 pt-4">
            <button
              onClick={() => setActiveTab('overview')}
              className={`pb-2 border-b-2 ${
                activeTab === 'overview'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600'
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('bottlenecks')}
              className={`pb-2 border-b-2 ${
                activeTab === 'bottlenecks'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600'
              }`}
            >
              Bottlenecks ({bottlenecks.length})
            </button>
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`pb-2 border-b-2 ${
                activeTab === 'recommendations'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600'
              }`}
            >
              Recommendations ({recommendations.length})
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'bottlenecks' && renderBottlenecks()}
          {activeTab === 'recommendations' && renderRecommendations()}
        </div>
      </div>
    </div>
  );
};

export default PerformanceOptimization;
