'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Upload, FileText, Settings, User, MessageSquare, Plus, Trash2 } from 'lucide-react'
import MessageBubble from './MessageBubble'
import FileUpload from './FileUpload'
import DocumentManager from './DocumentManager'
import SettingsPanel from './SettingsPanel'
import { useChat } from '@/hooks/useChat'
import { useDocuments } from '@/hooks/useDocuments'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  sources?: Array<{
    document_name: string
    page_number: string | number
    chunk_index: number
    similarity_score: number
    content_preview: string
    Case_Name?: string
    Case_No?: string
    Judges?: string | string[]
    Order_Date?: string
    Adjudication_Deadline?: string
    Appellant?: string
    Appellant_Advocate?: string
    Respondents?: string | string[]
    Respondent_Advocates?: string | string[]
  }>
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
  timestamp: Date
}

export default function ChatInterface() {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [input, setInput] = useState('')
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'documents' | 'settings'>('chat')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { sendMessage, isLoading } = useChat()
  const { documents, refreshDocuments } = useDocuments()

  const currentSession = sessions.find(s => s.id === currentSessionId)
  const messages = currentSession?.messages || []

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (sessions.length === 0) {
      createNewSession()
    }
    refreshDocuments()
  }, [])

  const createNewSession = () => {
    const newSession: ChatSession = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      timestamp: new Date()
    }
    setSessions(prev => [newSession, ...prev])
    setCurrentSessionId(newSession.id)
  }

  const deleteSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId))
    if (currentSessionId === sessionId) {
      const remaining = sessions.filter(s => s.id !== sessionId)
      setCurrentSessionId(remaining[0]?.id || null)
    }
  }

  const updateSessionTitle = (sessionId: string, title: string) => {
    setSessions(prev => prev.map(s => 
      s.id === sessionId ? { ...s, title } : s
    ))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading || !currentSessionId) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    // Add user message immediately
    setSessions(prev => prev.map(s => 
      s.id === currentSessionId 
        ? { ...s, messages: [...s.messages, userMessage] }
        : s
    ))

    // Update session title if it's the first message
    if (messages.length === 0) {
      const title = input.trim().length > 30 
        ? input.trim().substring(0, 30) + '...'
        : input.trim()
      updateSessionTitle(currentSessionId, title)
    }

    setInput('')

    try {
      const response = await sendMessage(input.trim())
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        sources: response.sources
      }

      setSessions(prev => prev.map(s => 
        s.id === currentSessionId 
          ? { ...s, messages: [...s.messages, assistantMessage] }
          : s
      ))
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Sorry, I encountered an error while processing your request. Please try again.',
        timestamp: new Date()
      }

      setSessions(prev => prev.map(s => 
        s.id === currentSessionId 
          ? { ...s, messages: [...s.messages, errorMessage] }
          : s
      ))
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as any)
    }
  }

  return (
    <div className="flex h-screen bg-gray-900 text-white">
      {/* Sidebar */}
      {sidebarOpen && (
        <div className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center justify-between mb-4">
              <h1 className="text-xl font-bold">RAG Pipeline</h1>
              <button
                onClick={createNewSession}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                title="New Chat"
              >
                <Plus size={20} />
              </button>
            </div>
            
            {/* Tab Navigation */}
            <div className="flex gap-1 bg-gray-700 rounded-lg p-1">
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md transition-colors ${ 
                  activeTab === 'chat' ? 'bg-gray-600 text-white' : 'text-gray-300 hover:text-white'
                }`}
              >
                <MessageSquare size={16} />
                <span className="text-sm">Chat</span>
              </button>
              <button
                onClick={() => setActiveTab('upload')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md transition-colors ${
                  activeTab === 'upload' ? 'bg-gray-600 text-white' : 'text-gray-300 hover:text-white'
                }`}
              >
                <Upload size={16} />
                <span className="text-sm">Upload</span>
              </button>
              <button
                onClick={() => setActiveTab('documents')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md transition-colors ${
                  activeTab === 'documents' ? 'bg-gray-600 text-white' : 'text-gray-300 hover:text-white'
                }`}
              >
                <FileText size={16} />
                <span className="text-sm">Docs</span>
              </button>
              <button
                onClick={() => setActiveTab('settings')}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-md transition-colors ${
                  activeTab === 'settings' ? 'bg-gray-600 text-white' : 'text-gray-300 hover:text-white'
                }`}
              >
                <Settings size={16} />
                <span className="text-sm">Settings</span>
              </button>
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'chat' && (
              <div className="h-full overflow-y-auto p-4">
                <div className="space-y-2">
                  {sessions.map((session) => (
                    <div
                      key={session.id}
                      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                        currentSessionId === session.id 
                          ? 'bg-gray-700' 
                          : 'hover:bg-gray-700'
                      }`}
                      onClick={() => setCurrentSessionId(session.id)}
                    >
                      <MessageSquare size={16} className="text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{session.title}</p>
                        <p className="text-xs text-gray-400">
                          {session.messages.length} messages
                        </p>
                      </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          deleteSession(session.id)
                        }}
                        className="p-1 hover:bg-gray-600 rounded transition-colors"
                        title="Delete Session"
                      >
                        <Trash2 size={14} className="text-gray-400" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'upload' && (
              <div className="h-full p-4">
                <FileUpload onUploadComplete={refreshDocuments} />
              </div>
            )}

            {activeTab === 'documents' && (
              <div className="h-full p-4">
                <DocumentManager documents={documents} onUpdate={refreshDocuments} />
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="h-full p-4">
                <SettingsPanel />
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {!sidebarOpen && (
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <MessageSquare size={20} />
              </button>
            )}
            <h2 className="text-lg font-semibold">
              {currentSession?.title || 'Select a chat session'}
            </h2>
          </div>
          
          {sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <Settings size={20} />
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mb-4">
                <MessageSquare size={32} className="text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Start a conversation</h3>
              <p className="text-gray-400 max-w-md">
                Ask questions about your legal documents. I can help you find specific case information, 
                analyze legal content, and provide detailed answers with source references.
              </p>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-gray-700 rounded-lg p-4 max-w-3xl">
                    <div className="loading-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-gray-700">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask about your legal documents..."
                  className="w-full bg-gray-700 border border-gray-600 rounded-lg py-3 px-4 pr-12 text-white placeholder-gray-400 resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  rows={1}
                  style={{ minHeight: '44px', maxHeight: '120px' }}
                  disabled={isLoading || !currentSessionId}
                />
                <button
                  type="submit"
                  disabled={!input.trim() || isLoading || !currentSessionId}
                  className="absolute right-2 bottom-2 p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg transition-colors"
                >
                  <Send size={16} />
                </button>
              </div>
            </div>
          </form>
          <div className="mt-2 text-xs text-gray-400 text-center">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  )
}
