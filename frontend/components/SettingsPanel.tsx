'use client'

import { useState } from 'react'
import { Settings, User, Database, Zap, Globe, Bell, Shield } from 'lucide-react'

export default function SettingsPanel() {
  const [settings, setSettings] = useState({
    model: 'gpt-3.5-turbo',
    temperature: 0.7,
    maxTokens: 2048,
    topK: 5,
    hybridAlpha: 0.5,
    enableNotifications: true,
    autoSave: true,
    darkMode: true,
    language: 'en'
  })

  const handleSettingChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="space-y-6">
      <div className="text-sm text-gray-300 mb-4">
        <h3 className="font-semibold mb-2">Settings</h3>
        <p className="text-gray-400">
          Configure your RAG pipeline and chat preferences.
        </p>
      </div>

      {/* Model Configuration */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={18} className="text-blue-400" />
          <h4 className="font-medium text-white">Model Configuration</h4>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Language Model
            </label>
            <select
              value={settings.model}
              onChange={(e) => handleSettingChange('model', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
              <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              <option value="claude-3-opus">Claude 3 Opus</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Temperature: {settings.temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.temperature}
              onChange={(e) => handleSettingChange('temperature', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Precise</span>
              <span>Creative</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Max Tokens
            </label>
            <input
              type="number"
              min="256"
              max="4096"
              value={settings.maxTokens}
              onChange={(e) => handleSettingChange('maxTokens', parseInt(e.target.value))}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Search Configuration */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Database size={18} className="text-green-400" />
          <h4 className="font-medium text-white">Search Configuration</h4>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Top-K Results: {settings.topK}
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={settings.topK}
              onChange={(e) => handleSettingChange('topK', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>1</span>
              <span>20</span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Hybrid Search Alpha: {settings.hybridAlpha}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={settings.hybridAlpha}
              onChange={(e) => handleSettingChange('hybridAlpha', parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>Semantic</span>
              <span>Keyword</span>
            </div>
          </div>
        </div>
      </div>

      {/* User Preferences */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <User size={18} className="text-purple-400" />
          <h4 className="font-medium text-white">Preferences</h4>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-300">Notifications</label>
              <p className="text-xs text-gray-400">Get notified about processing status</p>
            </div>
            <button
              onClick={() => handleSettingChange('enableNotifications', !settings.enableNotifications)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.enableNotifications ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.enableNotifications ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <label className="text-sm font-medium text-gray-300">Auto-save Sessions</label>
              <p className="text-xs text-gray-400">Automatically save chat sessions</p>
            </div>
            <button
              onClick={() => handleSettingChange('autoSave', !settings.autoSave)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                settings.autoSave ? 'bg-blue-600' : 'bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.autoSave ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Language
            </label>
            <select
              value={settings.language}
              onChange={(e) => handleSettingChange('language', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
              <option value="zh">中文</option>
            </select>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={18} className="text-yellow-400" />
          <h4 className="font-medium text-white">System Information</h4>
        </div>
        
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-400">RAG Pipeline Version</span>
            <span className="text-white">v2.1.0</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Embedding Model</span>
            <span className="text-white">all-MiniLM-L6-v2</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Vector Database</span>
            <span className="text-white">FAISS</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Text Search</span>
            <span className="text-white">BM25</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Documents Indexed</span>
            <span className="text-white">0</span>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
          Save Settings
        </button>
        <button className="flex-1 bg-gray-700 hover:bg-gray-600 text-white py-2 px-4 rounded-lg font-medium transition-colors">
          Reset to Default
        </button>
      </div>

      <div className="text-xs text-gray-500 bg-gray-800 p-3 rounded-lg">
        <p>
          ⚙️ <strong>Configuration Tips:</strong> Higher temperature increases creativity but may reduce accuracy. 
          Hybrid search alpha balances semantic similarity (0.0) with keyword matching (1.0). 
          More top-K results provide broader context but may include less relevant information.
        </p>
      </div>
    </div>
  )
}
