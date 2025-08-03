import { useState, useEffect } from 'react'
import api from '@/lib/api'

interface Document {
  id: number
  filename: string
  upload_date: string
  file_size: number
  status: string
  chunk_count?: number
  processing_time?: number
}

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const refreshDocuments = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/documents')
      setDocuments(response.data.documents || [])
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const uploadDocument = async (file: File): Promise<void> => {
    const formData = new FormData()
    formData.append('files', file)

    try {
      await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      await refreshDocuments()
    } catch (error) {
      console.error('Upload error:', error)
      throw new Error('Failed to upload document')
    }
  }

  const deleteDocument = async (documentId: number): Promise<void> => {
    try {
      await api.delete(`/documents/${documentId}`)
      await refreshDocuments()
    } catch (error) {
      console.error('Delete error:', error)
      throw new Error('Failed to delete document')
    }
  }

  useEffect(() => {
    refreshDocuments()
  }, [])

  return {
    documents,
    isLoading,
    refreshDocuments,
    uploadDocument,
    deleteDocument,
  }
}
