'use client'

import { User, Bot, Clock, FileText, ExternalLink } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { format } from 'date-fns'

interface MessageProps {
  message: {
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
}

export default function MessageBubble({ message }: MessageProps) {
  const isUser = message.type === 'user'
  
  const formatJudges = (judges: string | string[] | undefined) => {
    if (!judges) return 'N/A'
    if (Array.isArray(judges)) return judges.join(', ')
    return judges
  }

  const formatRespondents = (respondents: string | string[] | undefined) => {
    if (!respondents) return 'N/A'
    if (Array.isArray(respondents)) return respondents.join(', ')
    return respondents
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} message-appear`}>
      <div className={`max-w-3xl ${isUser ? 'ml-12' : 'mr-12'}`}>
        <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          {/* Avatar */}
          <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-blue-600' : 'bg-green-600'
          }`}>
            {isUser ? <User size={16} /> : <Bot size={16} />}
          </div>

          {/* Message Content */}
          <div className="flex-1">
            <div className={`rounded-lg p-4 ${
              isUser 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-700 text-white'
            }`}>
              {isUser ? (
                <p className="whitespace-pre-wrap">{message.content}</p>
              ) : (
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                      li: ({ children }) => <li className="mb-1">{children}</li>,
                      code: ({ children }) => (
                        <code className="bg-gray-800 px-1 py-0.5 rounded text-sm">{children}</code>
                      ),
                      pre: ({ children }) => (
                        <pre className="bg-gray-800 p-3 rounded-lg overflow-x-auto text-sm">{children}</pre>
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>

            {/* Sources - Only for assistant messages */}
            {!isUser && message.sources && message.sources.length > 0 && (
              <div className="mt-3 space-y-2">
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <FileText size={14} />
                  <span>Sources ({message.sources.length})</span>
                </div>
                
                <div className="space-y-2">
                  {message.sources.map((source, index) => (
                    <div key={index} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <FileText size={14} className="text-blue-400 flex-shrink-0" />
                          <span className="text-sm font-medium text-blue-400">
                            {source.document_name}
                          </span>
                        </div>
                        <span className="text-xs text-gray-400">
                          Score: {(source.similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>

                      {/* Enhanced Case Metadata */}
                      {(source.Case_Name || source.Case_No || source.Judges || source.Order_Date) && (
                        <div className="mb-3 p-2 bg-gray-900 rounded border border-gray-600">
                          <div className="text-xs font-semibold text-green-400 mb-2">📋 Case Metadata</div>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                            {source.Case_Name && (
                              <div>
                                <span className="text-gray-400">Case Name:</span>
                                <span className="ml-2 text-white">{source.Case_Name}</span>
                              </div>
                            )}
                            {source.Case_No && (
                              <div>
                                <span className="text-gray-400">Case No:</span>
                                <span className="ml-2 text-white">{source.Case_No}</span>
                              </div>
                            )}
                            {source.Judges && (
                              <div>
                                <span className="text-gray-400">Judges:</span>
                                <span className="ml-2 text-white">{formatJudges(source.Judges)}</span>
                              </div>
                            )}
                            {source.Order_Date && (
                              <div>
                                <span className="text-gray-400">Order Date:</span>
                                <span className="ml-2 text-white">{source.Order_Date}</span>
                              </div>
                            )}
                            {source.Adjudication_Deadline && (
                              <div>
                                <span className="text-gray-400">Adjudication Deadline:</span>
                                <span className="ml-2 text-white">{source.Adjudication_Deadline}</span>
                              </div>
                            )}
                            {source.Appellant && (
                              <div>
                                <span className="text-gray-400">Appellant:</span>
                                <span className="ml-2 text-white">{source.Appellant}</span>
                              </div>
                            )}
                            {source.Appellant_Advocate && (
                              <div>
                                <span className="text-gray-400">Appellant Advocate:</span>
                                <span className="ml-2 text-white">{source.Appellant_Advocate}</span>
                              </div>
                            )}
                            {source.Respondents && (
                              <div>
                                <span className="text-gray-400">Respondents:</span>
                                <span className="ml-2 text-white">{formatRespondents(source.Respondents)}</span>
                              </div>
                            )}
                            {source.Respondent_Advocates && (
                              <div>
                                <span className="text-gray-400">Respondent Advocates:</span>
                                <span className="ml-2 text-white">{formatRespondents(source.Respondent_Advocates)}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Document Info */}
                      <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                        <span>Page: {source.page_number !== 'N/A' ? source.page_number : 'Unknown'}</span>
                        <span>Chunk: {source.chunk_index}</span>
                      </div>

                      {/* Content Preview */}
                      <div className="text-sm text-gray-300 bg-gray-900 p-2 rounded border border-gray-600">
                        <div className="text-xs text-gray-400 mb-1">Content Preview:</div>
                        <p className="text-xs leading-relaxed">{source.content_preview}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Timestamp */}
            <div className={`flex items-center gap-1 mt-2 text-xs text-gray-400 ${
              isUser ? 'justify-end' : 'justify-start'
            }`}>
              <Clock size={12} />
              <span>{format(message.timestamp, 'HH:mm')}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
