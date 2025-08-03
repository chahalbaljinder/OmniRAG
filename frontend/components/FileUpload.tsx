'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react'
import { useDocuments } from '@/hooks/useDocuments'

interface FileUploadProps {
  onUploadComplete?: () => void
}

export default function FileUpload({ onUploadComplete }: FileUploadProps) {
  const { uploadDocument } = useDocuments()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      try {
        await uploadDocument(file)
        onUploadComplete?.()
      } catch (error) {
        console.error('Upload failed:', error)
      }
    }
  }, [uploadDocument, onUploadComplete])

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
  })

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-300 mb-4">
        <h3 className="font-semibold mb-2">Upload Documents</h3>
        <p className="text-gray-400">
          Upload PDF, TXT, DOC, or DOCX files to analyze with the RAG pipeline.
          Legal documents will have enhanced metadata extraction.
        </p>
      </div>

      <div
        {...getRootProps()}
        className={`file-upload-area ${isDragActive ? 'dragover' : ''}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 bg-gray-700 rounded-full flex items-center justify-center">
            <Upload size={24} className="text-gray-400" />
          </div>
          
          {isDragActive ? (
            <div className="text-center">
              <p className="text-lg font-medium text-blue-400">Drop files here</p>
              <p className="text-sm text-gray-400">Release to upload</p>
            </div>
          ) : (
            <div className="text-center">
              <p className="text-lg font-medium">Drag & drop files here</p>
              <p className="text-sm text-gray-400 mb-2">or click to browse</p>
              <p className="text-xs text-gray-500">
                Supports PDF, TXT, DOC, DOCX files
              </p>
            </div>
          )}
        </div>
      </div>

      {acceptedFiles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-300">Recent Uploads</h4>
          {acceptedFiles.map((file, index) => (
            <div key={index} className="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
              <FileText size={16} className="text-blue-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{file.name}</p>
                <p className="text-xs text-gray-400">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
              <CheckCircle size={16} className="text-green-400" />
            </div>
          ))}
        </div>
      )}

      <div className="text-xs text-gray-500 bg-gray-800 p-3 rounded-lg">
        <div className="flex items-start gap-2">
          <AlertCircle size={14} className="text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-yellow-400 mb-1">Enhanced Legal Document Processing</p>
            <p>
              Legal documents will automatically extract case metadata including:
              Case Name, Case Number, Judges, Order Date, Parties, Advocates, and more.
              This enhanced metadata will be included in query responses for cross-referencing.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
