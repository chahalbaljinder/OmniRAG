import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { 
  Home, 
  Upload, 
  Search, 
  FileText, 
  BarChart3, 
  Settings,
  Activity
} from 'lucide-react';

// Import pages
import Dashboard from './pages/Dashboard';
import UploadPage from './pages/UploadPage';
import QueryPage from './pages/QueryPage';
import DocumentsPage from './pages/DocumentsPage';
import StatsPage from './pages/StatsPage';

import './index.css';

function App() {
  const [isHealthy, setIsHealthy] = useState(false);
  const [healthChecking, setHealthChecking] = useState(true);

  // Check API health on app load
  useEffect(() => {
    checkApiHealth();
  }, []);

  const checkApiHealth = async () => {
    setHealthChecking(true);
    try {
      const response = await fetch('http://localhost:8001/health');
      setIsHealthy(response.ok);
    } catch (error) {
      setIsHealthy(false);
    }
    setHealthChecking(false);
  };

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Home },
    { name: 'Upload', href: '/upload', icon: Upload },
    { name: 'Query', href: '/query', icon: Search },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Statistics', href: '/stats', icon: BarChart3 },
  ];

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Toaster position="top-right" />
        
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <h1 className="text-xl font-bold text-gray-900">
                    🔍 RAG Pipeline
                  </h1>
                </div>
              </div>
              
              {/* Health Status */}
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-2">
                  <Activity className="h-4 w-4" />
                  {healthChecking ? (
                    <span className="text-yellow-600">Checking...</span>
                  ) : isHealthy ? (
                    <span className="text-green-600">API Healthy</span>
                  ) : (
                    <span className="text-red-600">API Down</span>
                  )}
                </div>
                <button
                  onClick={checkApiHealth}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Refresh
                </button>
              </div>
            </div>
          </div>
        </header>

        <div className="flex">
          {/* Sidebar */}
          <nav className="w-64 bg-white shadow-sm min-h-screen">
            <div className="p-4">
              <div className="space-y-1">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className={({ isActive }) =>
                        `group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors ${
                          isActive
                            ? 'bg-blue-100 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        }`
                      }
                    >
                      <Icon className="mr-3 h-5 w-5" />
                      {item.name}
                    </NavLink>
                  );
                })}
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/query" element={<QueryPage />} />
              <Route path="/documents" element={<DocumentsPage />} />
              <Route path="/stats" element={<StatsPage />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;
