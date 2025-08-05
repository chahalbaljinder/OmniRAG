# RAG Pipeline React UI

A modern React-based user interface for the RAG (Retrieval-Augmented Generation) Pipeline system.

## Features

- **Dashboard**: Overview of system status and quick actions
- **Document Upload**: Drag-and-drop PDF upload with progress tracking
- **Intelligent Query**: Natural language search with law-specific metadata support
- **Document Management**: View, organize, and delete documents with metadata inspection
- **Statistics**: System performance monitoring and usage analytics
- **Real-time Health Monitoring**: API status and system health indicators

## Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start Development Server**
   ```bash
   npm start
   ```
   
   The app will open at `http://localhost:3000`

3. **Ensure Backend is Running**
   Make sure your RAG API is running on `http://localhost:8001`

## API Integration

The UI connects to the following endpoints:

- `GET /health` - System health check
- `GET /stats` - System statistics
- `POST /upload` - Document upload
- `POST /query` - Document search
- `GET /documents` - List documents
- `GET /document/{id}` - Get document details
- `GET /document/{id}/metadata` - Get document metadata (law-specific)
- `DELETE /documents/{id}` - Delete document
- `DELETE /knowledge-base` - Clear all documents

## Law Document Features

The UI includes special support for law documents:

- **Case Number Recognition**: Displays case numbers from legal documents
- **Court Information**: Shows court names and jurisdictions
- **Judge Details**: Lists presiding judges
- **Legal Section References**: Identifies relevant legal sections
- **Page-Specific References**: Maintains page number context for citations

## Build for Production

```bash
npm run build
```

This creates a `build` folder with optimized production files.

## Technology Stack

- **React 18** - Modern React with hooks
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client
- **React Hot Toast** - Toast notifications
- **Lucide React** - Beautiful icons
- **React Dropzone** - File upload interface
