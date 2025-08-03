'use client'

import { useState } from 'react'
import { Upload, Send, FileText, X, Loader2, Database } from 'lucide-react'
import axios from 'axios'

interface Document {
  id: number
  filename: string
  upload_date: string
  status: string
}

interface QueryResponse {
  answer: string
  sources: Array<{
    document_name: string
    page_number: string | number
    Case_Name?: string
    Case_No?: string
    Judges?: string
    Order_Date?: string
    Adjudication_Deadline?: string
    Appellant?: string
    Appellant_Advocate?: string
    Respondents?: string
    Respondent_Advocates?: string
    content_preview?: string
    similarity_score?: number
  }>
  query: string
  total_sources: number
  timestamp: string
}

export default function SimpleRAGInterface() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState<QueryResponse | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isQuerying, setIsQuerying] = useState(false)
  const [error, setError] = useState('')

  // File upload handler
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    setUploadedFiles(prev => [...prev, ...files])
    setError('')
  }

  // Remove file from upload queue
  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  // Upload documents to backend
  const uploadDocuments = async () => {
    if (uploadedFiles.length === 0) {
      setError('Please select files to upload')
      return
    }

    setIsUploading(true)
    setError('')

    try {
      for (const file of uploadedFiles) {
        const formData = new FormData()
        formData.append('file', file)

        await axios.post('/api/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        })
      }

      // Refresh document list
      await fetchDocuments()
      setUploadedFiles([])
      
    } catch (error: any) {
      console.error('Upload error:', error)
      setError(error.response?.data?.detail || 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  // Fetch uploaded documents
  const fetchDocuments = async () => {
    try {
      const response = await axios.get('/api/documents')
      setDocuments(response.data.documents || [])
    } catch (error) {
      console.error('Failed to fetch documents:', error)
    }
  }

  // Submit query
  const submitQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a query')
      return
    }

    if (documents.length === 0) {
      setError('Please upload documents first')
      return
    }

    setIsQuerying(true)
    setError('')
    setResponse(null)

    try {
      const response = await axios.post('/api/query', {
        query: query.trim(),
        top_k: 5
      })

      setResponse(response.data)
    } catch (error: any) {
      console.error('Query error:', error)
      setError(error.response?.data?.detail || 'Query failed')
    } finally {
      setIsQuerying(false)
    }
  }

  // Load documents on component mount
  useState(() => {
    fetchDocuments()
  })

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    if (bytes === 0) return '0 Bytes'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">RAG Pipeline Interface</h1>
        <p className="text-gray-400">Upload documents, ask questions, get comprehensive answers with metadata</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Panel - Document Upload & Management */}
        <div className="space-y-6">
          {/* Upload Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Upload size={20} />
              Upload Documents
            </h2>
            
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-600 rounded-lg p-6 text-center">
                <input
                  type="file"
                  multiple
                  accept=".pdf,.doc,.docx,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <Upload size={32} className="text-gray-400" />
                  <span className="text-gray-300">Click to upload documents</span>
                  <span className="text-sm text-gray-500">PDF, DOC, DOCX, TXT files supported</span>
                </label>
              </div>

              {/* File Queue */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-gray-300">Files to upload:</h3>
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between bg-gray-700 p-3 rounded">
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-blue-400" />
                        <span className="text-sm text-white">{file.name}</span>
                        <span className="text-xs text-gray-400">({formatFileSize(file.size)})</span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-gray-400 hover:text-red-400"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ))}
                  
                  <button
                    onClick={uploadDocuments}
                    disabled={isUploading}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-2 px-4 rounded font-medium flex items-center justify-center gap-2"
                  >
                    {isUploading ? (
                      <>
                        <Loader2 size={16} className="animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload size={16} />
                        Upload {uploadedFiles.length} file{uploadedFiles.length !== 1 ? 's' : ''}
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Uploaded Documents */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Database size={20} />
              Uploaded Documents ({documents.length})
            </h2>
            
            {documents.length === 0 ? (
              <div className="text-center py-8">
                <FileText size={32} className="text-gray-400 mx-auto mb-2" />
                <p className="text-gray-400">No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between bg-gray-700 p-3 rounded">
                    <div className="flex items-center gap-2">
                      <FileText size={16} className="text-green-400" />
                      <span className="text-sm text-white">{doc.filename}</span>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      doc.status === 'processed' ? 'bg-green-600 text-white' : 
                      doc.status === 'processing' ? 'bg-yellow-600 text-white' : 
                      'bg-red-600 text-white'
                    }`}>
                      {doc.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - Query & Results */}
        <div className="space-y-6">
          {/* Query Section */}
          <div className="bg-gray-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Send size={20} />
              Ask a Question
            </h2>
            
            <div className="space-y-4">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your question about the uploaded documents..."
                className="w-full h-32 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
              
              <button
                onClick={submitQuery}
                disabled={isQuerying || documents.length === 0}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white py-3 px-4 rounded font-medium flex items-center justify-center gap-2"
              >
                {isQuerying ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Send size={16} />
                    Submit Query
                  </>
                )}
              </button>
              
              {documents.length === 0 && (
                <p className="text-sm text-gray-400 text-center">
                  Upload documents first to enable querying
                </p>
              )}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-900 border border-red-600 rounded-lg p-4">
              <p className="text-red-200">{error}</p>
            </div>
          )}

          {/* Response Section */}
          {response && (
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Answer</h2>
              
              {/* Answer */}
              <div className="bg-gray-700 rounded-lg p-4 mb-6">
                <h3 className="font-medium text-white mb-2">Response:</h3>
                <p className="text-gray-200 whitespace-pre-wrap">{response.answer}</p>
              </div>

              {/* Sources & Metadata */}
              {response.sources && response.sources.length > 0 && (
                <div className="space-y-4">
                  <h3 className="font-medium text-white">Sources & Metadata ({response.total_sources}):</h3>
                  
                  {response.sources.map((source, index) => (
                    <div key={index} className="bg-gray-700 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium text-blue-400">
                          {source.document_name} - Page {source.page_number}
                        </span>
                        {source.similarity_score && (
                          <span className="text-xs text-gray-400">
                            Relevance: {(source.similarity_score * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                      
                      {/* Case Metadata */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        {source.Case_Name && (
                          <div>
                            <span className="text-gray-400">Case Name:</span>
                            <span className="text-white ml-2">{source.Case_Name}</span>
                          </div>
                        )}
                        {source.Case_No && (
                          <div>
                            <span className="text-gray-400">Case No:</span>
                            <span className="text-white ml-2">{source.Case_No}</span>
                          </div>
                        )}
                        {source.Judges && (
                          <div>
                            <span className="text-gray-400">Judges:</span>
                            <span className="text-white ml-2">{source.Judges}</span>
                          </div>
                        )}
                        {source.Order_Date && (
                          <div>
                            <span className="text-gray-400">Order Date:</span>
                            <span className="text-white ml-2">{source.Order_Date}</span>
                          </div>
                        )}
                        {source.Adjudication_Deadline && (
                          <div>
                            <span className="text-gray-400">Adjudication Deadline:</span>
                            <span className="text-white ml-2">{source.Adjudication_Deadline}</span>
                          </div>
                        )}
                        {source.Appellant && (
                          <div>
                            <span className="text-gray-400">Appellant:</span>
                            <span className="text-white ml-2">{source.Appellant}</span>
                          </div>
                        )}
                        {source.Appellant_Advocate && (
                          <div>
                            <span className="text-gray-400">Appellant Advocate:</span>
                            <span className="text-white ml-2">{source.Appellant_Advocate}</span>
                          </div>
                        )}
                        {source.Respondents && (
                          <div>
                            <span className="text-gray-400">Respondents:</span>
                            <span className="text-white ml-2">{source.Respondents}</span>
                          </div>
                        )}
                        {source.Respondent_Advocates && (
                          <div>
                            <span className="text-gray-400">Respondent Advocates:</span>
                            <span className="text-white ml-2">{source.Respondent_Advocates}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Content Preview */}
                      {source.content_preview && (
                        <div className="mt-3 pt-3 border-t border-gray-600">
                          <span className="text-xs text-gray-400">Content Preview:</span>
                          <p className="text-xs text-gray-300 mt-1">{source.content_preview}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              <div className="mt-4 text-xs text-gray-400">
                Query processed at: {new Date(response.timestamp).toLocaleString()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
