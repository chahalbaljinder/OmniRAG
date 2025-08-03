import { useState } from 'react'
import api from '@/lib/api'

interface ChatResponse {
  answer: string
  sources: Array<{
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
  query: string
  total_sources: number
  documents_searched: number
  processing_time: number
  query_id: number
  timestamp: string
}

export function useChat() {
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async (query: string): Promise<ChatResponse> => {
    setIsLoading(true)
    try {
      const formData = new FormData()
      formData.append('query', query)
      formData.append('k', '5') // Number of sources to return

      const response = await api.post('/query', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      return response.data
    } catch (error) {
      console.error('Chat error:', error)
      throw new Error('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  return {
    sendMessage,
    isLoading,
  }
}
