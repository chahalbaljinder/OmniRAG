import React, { useState, useEffect } from 'react';
import { FileText, Trash2, Eye, Download, Calendar, Database, RefreshCw } from 'lucide-react';
import apiService from '../services/api';
import toast from 'react-hot-toast';

const DocumentsPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showMetadata, setShowMetadata] = useState({});
  const [deleting, setDeleting] = useState({});

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const result = await apiService.listDocuments();
      if (result.success) {
        setDocuments(result.data.documents || []);
      } else {
        toast.error('Failed to load documents');
      }
    } catch (error) {
      toast.error('Failed to load documents');
    }
    setLoading(false);
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }

    setDeleting({ ...deleting, [docId]: true });
    
    try {
      const result = await apiService.deleteDocument(docId);
      if (result.success) {
        toast.success(`Deleted "${filename}" successfully`);
        setDocuments(documents.filter(doc => doc.id !== docId));
      } else {
        toast.error(`Failed to delete document: ${result.error}`);
      }
    } catch (error) {
      toast.error('Failed to delete document');
    }

    setDeleting({ ...deleting, [docId]: false });
  };

  const handleViewDetails = async (docId) => {
    try {
      const result = await apiService.getDocument(docId);
      if (result.success) {
        setSelectedDoc(result.data);
      } else {
        toast.error('Failed to load document details');
      }
    } catch (error) {
      toast.error('Failed to load document details');
    }
  };

  const handleViewMetadata = async (docId) => {
    if (showMetadata[docId]) {
      setShowMetadata({ ...showMetadata, [docId]: false });
      return;
    }

    try {
      const result = await apiService.getDocumentMetadata(docId);
      if (result.success) {
        setShowMetadata({ 
          ...showMetadata, 
          [docId]: result.data 
        });
      } else {
        toast.error('Failed to load document metadata');
      }
    } catch (error) {
      toast.error('Failed to load document metadata');
    }
  };

  const handleClearKnowledgeBase = async () => {
    if (!window.confirm('Are you sure you want to clear the entire knowledge base? This action cannot be undone.')) {
      return;
    }

    try {
      const result = await apiService.clearKnowledgeBase();
      if (result.success) {
        toast.success('Knowledge base cleared successfully');
        setDocuments([]);
      } else {
        toast.error(`Failed to clear knowledge base: ${result.error}`);
      }
    } catch (error) {
      toast.error('Failed to clear knowledge base');
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Document Management</h1>
          <p className="text-gray-600">Manage your uploaded documents and knowledge base</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={fetchDocuments}
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
          
          {documents.length > 0 && (
            <button
              onClick={handleClearKnowledgeBase}
              className="flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-lg hover:bg-red-700"
            >
              <Database className="h-4 w-4 mr-2" />
              Clear Knowledge Base
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <FileText className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Documents</p>
              <p className="text-2xl font-semibold text-gray-900">{documents.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Database className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Pages</p>
              <p className="text-2xl font-semibold text-gray-900">
                {documents.reduce((sum, doc) => sum + (doc.page_count || 0), 0)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Download className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Size</p>
              <p className="text-2xl font-semibold text-gray-900">
                {formatFileSize(documents.reduce((sum, doc) => sum + (doc.file_size || 0), 0))}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Documents List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Documents</h2>
        </div>
        
        {documents.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No documents</h3>
            <p className="mt-1 text-sm text-gray-500">
              Upload some documents to get started.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {documents.map((doc) => (
              <div key={doc.id} className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center">
                      <FileText className="h-5 w-5 text-red-500 mr-3 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {doc.filename}
                        </h3>
                        <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                          <span className="flex items-center">
                            <Calendar className="h-4 w-4 mr-1" />
                            {new Date(doc.upload_date).toLocaleDateString()}
                          </span>
                          <span>{doc.page_count} pages</span>
                          <span>{formatFileSize(doc.file_size || 0)}</span>
                          {doc.chunk_count && <span>{doc.chunk_count} chunks</span>}
                        </div>
                      </div>
                    </div>

                    {/* Metadata */}
                    {showMetadata[doc.id] && (
                      <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">Document Metadata</h4>
                        <div className="space-y-2">
                          {/* Law-specific metadata */}
                          {showMetadata[doc.id].law_metadata && (
                            <div className="grid grid-cols-2 gap-4">
                              {showMetadata[doc.id].law_metadata.document_type && (
                                <div>
                                  <span className="text-xs font-medium text-gray-600">Document Type:</span>
                                  <p className="text-sm text-gray-900">
                                    {showMetadata[doc.id].law_metadata.document_type}
                                  </p>
                                </div>
                              )}
                              {showMetadata[doc.id].law_metadata.case_numbers && 
                               showMetadata[doc.id].law_metadata.case_numbers.length > 0 && (
                                <div>
                                  <span className="text-xs font-medium text-gray-600">Case Numbers:</span>
                                  <p className="text-sm text-gray-900">
                                    {showMetadata[doc.id].law_metadata.case_numbers.join(', ')}
                                  </p>
                                </div>
                              )}
                              {showMetadata[doc.id].law_metadata.courts && 
                               showMetadata[doc.id].law_metadata.courts.length > 0 && (
                                <div>
                                  <span className="text-xs font-medium text-gray-600">Courts:</span>
                                  <p className="text-sm text-gray-900">
                                    {showMetadata[doc.id].law_metadata.courts.join(', ')}
                                  </p>
                                </div>
                              )}
                              {showMetadata[doc.id].law_metadata.judges && 
                               showMetadata[doc.id].law_metadata.judges.length > 0 && (
                                <div>
                                  <span className="text-xs font-medium text-gray-600">Judges:</span>
                                  <p className="text-sm text-gray-900">
                                    {showMetadata[doc.id].law_metadata.judges.join(', ')}
                                  </p>
                                </div>
                              )}
                              {showMetadata[doc.id].law_metadata.legal_sections && 
                               showMetadata[doc.id].law_metadata.legal_sections.length > 0 && (
                                <div>
                                  <span className="text-xs font-medium text-gray-600">Legal Sections:</span>
                                  <p className="text-sm text-gray-900">
                                    {showMetadata[doc.id].law_metadata.legal_sections.join(', ')}
                                  </p>
                                </div>
                              )}
                            </div>
                          )}
                          
                          {/* General metadata */}
                          <div className="text-xs text-gray-600">
                            <pre className="whitespace-pre-wrap">
                              {JSON.stringify(showMetadata[doc.id], null, 2)}
                            </pre>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => handleViewDetails(doc.id)}
                      className="text-gray-400 hover:text-blue-600"
                      title="View Details"
                    >
                      <Eye className="h-5 w-5" />
                    </button>
                    
                    <button
                      onClick={() => handleViewMetadata(doc.id)}
                      className={`text-gray-400 hover:text-green-600 ${
                        showMetadata[doc.id] ? 'text-green-600' : ''
                      }`}
                      title="View Metadata"
                    >
                      <Database className="h-5 w-5" />
                    </button>
                    
                    <button
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      disabled={deleting[doc.id]}
                      className="text-gray-400 hover:text-red-600 disabled:opacity-50"
                      title="Delete Document"
                    >
                      {deleting[doc.id] ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-600"></div>
                      ) : (
                        <Trash2 className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Document Details Modal */}
      {selectedDoc && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium text-gray-900">Document Details</h3>
                <button
                  onClick={() => setSelectedDoc(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">{selectedDoc.filename}</h4>
                  <div className="mt-2 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-600">Pages:</span> {selectedDoc.page_count}
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Size:</span> {formatFileSize(selectedDoc.file_size || 0)}
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Uploaded:</span> {new Date(selectedDoc.upload_date).toLocaleString()}
                    </div>
                    <div>
                      <span className="font-medium text-gray-600">Chunks:</span> {selectedDoc.chunk_count || 'N/A'}
                    </div>
                  </div>
                </div>
                
                {selectedDoc.metadata && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Metadata</h4>
                    <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">
                      {JSON.stringify(selectedDoc.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentsPage;
