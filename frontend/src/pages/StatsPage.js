import React, { useState, useEffect } from 'react';
import { BarChart3, Activity, Clock, Database, TrendingUp, Zap } from 'lucide-react';
import apiService from '../services/api';
import toast from 'react-hot-toast';

const StatsPage = () => {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const [statsResult, healthResult] = await Promise.all([
        apiService.getStats(),
        apiService.healthCheck()
      ]);

      if (statsResult.success) {
        setStats(statsResult.data);
      }

      if (healthResult.success) {
        setHealth(healthResult.data);
      }
    } catch (error) {
      toast.error('Failed to load statistics');
    }
    setLoading(false);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">System Statistics</h1>
          <p className="text-gray-600">Monitor your RAG pipeline performance and usage</p>
        </div>
        
        <button
          onClick={fetchStats}
          className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <Activity className="h-4 w-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* System Health */}
      {health && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              System Health
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="w-8 h-8 bg-green-500 rounded-full mx-auto mb-2"></div>
                <p className="text-sm font-medium text-gray-900">API Status</p>
                <p className="text-green-600 font-semibold">Healthy</p>
              </div>
              
              {health.uptime && (
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <Clock className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-900">Uptime</p>
                  <p className="text-blue-600 font-semibold">
                    {Math.floor(health.uptime / 3600)}h {Math.floor((health.uptime % 3600) / 60)}m
                  </p>
                </div>
              )}
              
              {health.version && (
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <TrendingUp className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                  <p className="text-sm font-medium text-gray-900">Version</p>
                  <p className="text-purple-600 font-semibold">{health.version}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Statistics */}
      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Document Statistics */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 flex items-center">
                <Database className="h-5 w-5 mr-2" />
                Document Statistics
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">Total Documents</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.total_documents || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">Total Pages</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.total_pages || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">Total Chunks</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.total_chunks || 0}
                  </span>
                </div>
                
                {stats.total_size && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Total Size</span>
                    <span className="text-lg font-semibold text-gray-900">
                      {(stats.total_size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Query Statistics */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 flex items-center">
                <BarChart3 className="h-5 w-5 mr-2" />
                Query Statistics
              </h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">Total Queries</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {stats.total_queries || 0}
                  </span>
                </div>
                
                {stats.average_processing_time && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Avg Processing Time</span>
                    <span className="text-lg font-semibold text-gray-900">
                      {stats.average_processing_time.toFixed(3)}s
                    </span>
                  </div>
                )}
                
                {stats.queries_today && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Queries Today</span>
                    <span className="text-lg font-semibold text-gray-900">
                      {stats.queries_today}
                    </span>
                  </div>
                )}
                
                {stats.successful_queries && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-600">Success Rate</span>
                    <span className="text-lg font-semibold text-green-600">
                      {((stats.successful_queries / stats.total_queries) * 100).toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      {stats && stats.performance && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900 flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              Performance Metrics
            </h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {Object.entries(stats.performance).map(([key, value]) => (
                <div key={key} className="border rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-900 mb-2 capitalize">
                    {key.replace(/_/g, ' ')}
                  </h3>
                  {typeof value === 'object' ? (
                    <div className="space-y-1 text-sm">
                      {value.count && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Count:</span>
                          <span className="font-medium">{value.count}</span>
                        </div>
                      )}
                      {value.average && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Average:</span>
                          <span className="font-medium">{value.average.toFixed(3)}s</span>
                        </div>
                      )}
                      {value.min && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Min:</span>
                          <span className="font-medium">{value.min.toFixed(3)}s</span>
                        </div>
                      )}
                      {value.max && (
                        <div className="flex justify-between">
                          <span className="text-gray-600">Max:</span>
                          <span className="font-medium">{value.max.toFixed(3)}s</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-lg font-semibold text-gray-900">{value}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* System Information */}
      {stats && stats.system && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">System Information</h2>
          </div>
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(stats.system).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                  <span className="text-sm font-medium text-gray-600 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-sm text-gray-900">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Raw Stats Display for debugging */}
      {stats && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Raw Statistics</h2>
          </div>
          <div className="p-6">
            <pre className="text-xs bg-gray-100 p-4 rounded overflow-x-auto">
              {JSON.stringify(stats, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* No Stats Available */}
      {!stats && !loading && (
        <div className="text-center py-12">
          <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No statistics available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Statistics will appear here as you use the system.
          </p>
        </div>
      )}
    </div>
  );
};

export default StatsPage;
