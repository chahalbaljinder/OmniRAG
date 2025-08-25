import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, CheckCircle, AlertCircle, File } from 'lucide-react';
import apiService from '../services/api';
import toast from 'react-hot-toast';

const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending'
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeFile = (id) => {
    setFiles(files.filter(f => f.id !== id));
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setUploading(true);
    setUploadResults(null);

    try {
      const fileList = files.map(f => f.file);
      const result = await apiService.uploadFiles(fileList);

      if (result.success) {
        setUploadResults(result.data);
        toast.success(`Successfully uploaded ${result.data.total_uploaded || files.length} files!`);
        setFiles([]);
      } else {
        toast.error(`Upload failed: ${result.error}`);
      }
    } catch (error) {
      toast.error('Upload failed');
    }

    setUploading(false);
  };

  const clearResults = () => {
    setUploadResults(null);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Documents</h1>
        <p className="text-gray-600">Add PDF documents to your knowledge base</p>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
              isDragActive
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            }`}
          >
            <input {...getInputProps()} />
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              {isDragActive
                ? 'Drop the files here...'
                : 'Drag & drop PDF files here, or click to select files'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Only PDF files are supported
            </p>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="mt-6">
              <h3 className="text-sm font-medium text-gray-900 mb-3">
                Selected Files ({files.length})
              </h3>
              <div className="space-y-2">
                {files.map((fileObj) => (
                  <div
                    key={fileObj.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center">
                      <File className="h-5 w-5 text-red-500 mr-3" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {fileObj.file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(fileObj.file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(fileObj.id)}
                      className="text-gray-400 hover:text-red-500"
                      disabled={uploading}
                    >
                      <X className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Upload Button */}
              <div className="mt-4 flex justify-end">
                <button
                  onClick={uploadFiles}
                  disabled={uploading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload Files
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Upload Results */}
      {uploadResults && (
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
            <h2 className="text-lg font-medium text-gray-900">Upload Results</h2>
            <button
              onClick={clearResults}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="p-6">
            {/* Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-900">Successful</p>
                <p className="text-2xl font-bold text-green-600">
                  {uploadResults.total_uploaded || 0}
                </p>
              </div>
              
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-900">Failed</p>
                <p className="text-2xl font-bold text-red-600">
                  {uploadResults.errors ? uploadResults.errors.length : 0}
                </p>
              </div>
              
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <File className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-900">Total Files</p>
                <p className="text-2xl font-bold text-blue-600">
                  {(uploadResults.total_uploaded || 0) + (uploadResults.errors ? uploadResults.errors.length : 0)}
                </p>
              </div>
            </div>

            {/* Successful Uploads */}
            {uploadResults.uploaded && uploadResults.uploaded.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Successfully Uploaded
                </h3>
                <div className="space-y-2">
                  {uploadResults.uploaded.map((doc, index) => (
                    <div key={index} className="flex items-center p-3 bg-green-50 rounded-lg">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {doc.filename}
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>{doc.pages} pages</span>
                          <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                          <span>{doc.chunks} chunks created</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Errors */}
            {uploadResults.errors && uploadResults.errors.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-3">
                  Upload Errors
                </h3>
                <div className="space-y-2">
                  {uploadResults.errors.map((error, index) => (
                    <div key={index} className="flex items-center p-3 bg-red-50 rounded-lg">
                      <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default UploadPage;
