'use client'

import { FileText, Download, Trash2, Calendar, HardDrive, Clock } from 'lucide-react'
import { format } from 'date-fns'
import { useDocuments } from '@/hooks/useDocuments'

interface Document {
  id: number
  filename: string
  upload_date: string
  file_size: number
  status: string
  chunk_count?: number
  processing_time?: number
}

interface DocumentManagerProps {
  documents: Document[]
  onUpdate: () => void
}

export default function DocumentManager({ documents, onUpdate }: DocumentManagerProps) {
  const { deleteDocument } = useDocuments()

  const handleDelete = async (documentId: number) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await deleteDocument(documentId)
        onUpdate()
      } catch (error) {
        console.error('Failed to delete document:', error)
      }
    }
  }

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    if (bytes === 0) return '0 Bytes'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'processed':
      case 'completed':
        return 'text-green-400'
      case 'processing':
        return 'text-yellow-400'
      case 'failed':
      case 'error':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-300 mb-4">
        <h3 className="font-semibold mb-2">Document Library</h3>
        <p className="text-gray-400">
          Manage your uploaded documents. Documents are processed with enhanced metadata extraction.
        </p>
      </div>

      {documents.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText size={32} className="text-gray-400" />
          </div>
          <h4 className="text-lg font-medium text-gray-300 mb-2">No documents uploaded</h4>
          <p className="text-gray-400">
            Upload your first document to get started with the RAG pipeline.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {documents.map((document) => (
            <div key={document.id} className="card">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <FileText size={18} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium text-white truncate mb-1">
                      {document.filename}
                    </h4>
                    
                    <div className="flex items-center gap-4 text-xs text-gray-400">
                      <div className="flex items-center gap-1">
                        <Calendar size={12} />
                        <span>{format(new Date(document.upload_date), 'MMM dd, yyyy')}</span>
                      </div>
                      
                      <div className="flex items-center gap-1">
                        <HardDrive size={12} />
                        <span>{formatFileSize(document.file_size)}</span>
                      </div>
                      
                      {document.chunk_count && (
                        <div className="flex items-center gap-1">
                          <FileText size={12} />
                          <span>{document.chunk_count} chunks</span>
                        </div>
                      )}
                      
                      {document.processing_time && (
                        <div className="flex items-center gap-1">
                          <Clock size={12} />
                          <span>{document.processing_time.toFixed(2)}s</span>
                        </div>
                      )}
                    </div>
                    
                    <div className="mt-2">
                      <span className={`text-xs font-medium ${getStatusColor(document.status)}`}>
                        {document.status.charAt(0).toUpperCase() + document.status.slice(1)}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => {
                      // Download functionality would go here
                      console.log('Download document:', document.id)
                    }}
                    className="p-2 text-gray-400 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                    title="Download"
                  >
                    <Download size={16} />
                  </button>
                  
                  <button
                    onClick={() => handleDelete(document.id)}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-gray-700 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <div className="text-xs text-gray-500 bg-gray-800 p-3 rounded-lg">
        <p>
          📋 <strong>Enhanced Processing:</strong> Legal documents are automatically processed with 
          comprehensive case metadata extraction including case names, numbers, judges, dates, 
          parties, and advocates for precise cross-referencing in queries.
        </p>
      </div>
    </div>
  )
}
