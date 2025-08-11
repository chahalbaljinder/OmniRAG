import axios from 'axios';

// Use environment variable for API URL, fallback to localhost for development
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// API service class
class APIService {
  // Health check
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Get statistics
  async getStats() {
    try {
      const response = await api.get('/stats');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Upload files
  async uploadFiles(files) {
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });

      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message 
      };
    }
  }

  // Query documents
  async queryDocuments(query, options = {}) {
    try {
      const formData = new FormData();
      formData.append('query', query);
      formData.append('k', options.k || 3);
      formData.append('search_type', options.search_type || 'semantic');

      const response = await api.post('/query', formData);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message 
      };
    }
  }

  // List documents
  async listDocuments() {
    try {
      const response = await api.get('/documents');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Get document details
  async getDocument(documentId) {
    try {
      const response = await api.get(`/document/${documentId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Get document metadata
  async getDocumentMetadata(documentId) {
    try {
      const response = await api.get(`/document/${documentId}/metadata`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  // Delete document
  async deleteDocument(documentId) {
    try {
      const response = await api.delete(`/documents/${documentId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message 
      };
    }
  }

  // Clear knowledge base
  async clearKnowledgeBase() {
    try {
      const response = await api.delete('/knowledge-base');
      return { success: true, data: response.data };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message 
      };
    }
  }
}

export default new APIService();
