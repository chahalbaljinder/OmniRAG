import React, { useState } from 'react';
import { Search, Clock, FileText, Hash, Scale } from 'lucide-react';
import apiService from '../services/api';
import toast from 'react-hot-toast';

const QueryPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState({
    k: 3,
    search_type: 'semantic'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setLoading(true);
    setResults(null);

    try {
      const result = await apiService.queryDocuments(query, options);
      
      if (result.success) {
        setResults(result.data);
        toast.success('Query completed successfully!');
      } else {
        toast.error(`Query failed: ${result.error}`);
      }
    } catch (error) {
      toast.error('Query failed');
    }

    setLoading(false);
  };

  const formatPageReferences = (sources) => {
    if (!sources || sources.length === 0) return 'No sources';
    
    return sources.map(source => {
      if (source.page_number) {
        return `Page ${source.page_number}`;
      }
      return source.filename || 'Unknown source';
    }).join(', ');
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Query Documents</h1>
        <p className="text-gray-600">Ask questions about your uploaded documents</p>
      </div>

      {/* Query Form */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
                Your Question
              </label>
              <textarea
                id="query"
                rows={4}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="What are the main findings in the research papers? What legal precedents are mentioned? Summarize the key points..."
              />
            </div>

            {/* Query Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="k" className="block text-sm font-medium text-gray-700 mb-1">
                  Number of Results
                </label>
                <select
                  id="k"
                  value={options.k}
                  onChange={(e) => setOptions({...options, k: parseInt(e.target.value)})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value={1}>1</option>
                  <option value={3}>3</option>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                </select>
              </div>

              <div>
                <label htmlFor="search_type" className="block text-sm font-medium text-gray-700 mb-1">
                  Search Type
                </label>
                <select
                  id="search_type"
                  value={options.search_type}
                  onChange={(e) => setOptions({...options, search_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="semantic">Semantic Search</option>
                  <option value="keyword">Keyword Search</option>
                  <option value="hybrid">Hybrid Search</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={loading}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Ask Question
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div className="space-y-6">
          {/* Answer */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 flex items-center">
                <FileText className="h-5 w-5 mr-2" />
                Answer
              </h2>
            </div>
            <div className="p-6">
              <div className="prose max-w-none">
                <div className="text-gray-900 whitespace-pre-wrap">
                  {results.answer}
                </div>
              </div>

              {/* Metadata */}
              <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center">
                  <Clock className="h-4 w-4 text-gray-500 mr-2" />
                  <div>
                    <p className="text-xs text-gray-500">Processing Time</p>
                    <p className="text-sm font-medium">
                      {results.processing_time ? `${results.processing_time.toFixed(3)}s` : 'N/A'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center">
                  <FileText className="h-4 w-4 text-gray-500 mr-2" />
                  <div>
                    <p className="text-xs text-gray-500">Documents Found</p>
                    <p className="text-sm font-medium">
                      {results.sources ? results.sources.length : 0}
                    </p>
                  </div>
                </div>

                <div className="flex items-center">
                  <Hash className="h-4 w-4 text-gray-500 mr-2" />
                  <div>
                    <p className="text-xs text-gray-500">Search Type</p>
                    <p className="text-sm font-medium capitalize">
                      {results.search_type || options.search_type}
                    </p>
                  </div>
                </div>

                <div className="flex items-center">
                  <Scale className="h-4 w-4 text-gray-500 mr-2" />
                  <div>
                    <p className="text-xs text-gray-500">Confidence</p>
                    <p className="text-sm font-medium">
                      {results.confidence ? `${(results.confidence * 100).toFixed(1)}%` : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sources */}
          {results.sources && results.sources.length > 0 && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">
                  Sources ({results.sources.length})
                </h2>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  {results.sources.map((source, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h3 className="text-sm font-medium text-gray-900">
                            {source.filename || `Source ${index + 1}`}
                          </h3>
                          {source.page_number && (
                            <p className="text-xs text-gray-500">Page {source.page_number}</p>
                          )}
                          {source.relevance_score && (
                            <p className="text-xs text-green-600">
                              Relevance: {(source.relevance_score * 100).toFixed(1)}%
                            </p>
                          )}
                        </div>
                      </div>

                      {source.content && (
                        <div className="mt-3">
                          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded border-l-4 border-blue-200">
                            {source.content.length > 300 
                              ? `${source.content.substring(0, 300)}...` 
                              : source.content
                            }
                          </p>
                        </div>
                      )}

                      {/* Law-specific metadata */}
                      {source.law_metadata && (
                        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2">
                          {source.law_metadata.case_number && (
                            <div className="text-xs">
                              <span className="font-medium text-gray-600">Case:</span>
                              <br />
                              <span className="text-gray-800">{source.law_metadata.case_number}</span>
                            </div>
                          )}
                          {source.law_metadata.court && (
                            <div className="text-xs">
                              <span className="font-medium text-gray-600">Court:</span>
                              <br />
                              <span className="text-gray-800">{source.law_metadata.court}</span>
                            </div>
                          )}
                          {source.law_metadata.judge && (
                            <div className="text-xs">
                              <span className="font-medium text-gray-600">Judge:</span>
                              <br />
                              <span className="text-gray-800">{source.law_metadata.judge}</span>
                            </div>
                          )}
                          {source.law_metadata.legal_sections && source.law_metadata.legal_sections.length > 0 && (
                            <div className="text-xs">
                              <span className="font-medium text-gray-600">Sections:</span>
                              <br />
                              <span className="text-gray-800">
                                {source.law_metadata.legal_sections.join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Page References Summary */}
          {results.page_references && results.page_references.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-800 mb-1">Page References</h3>
              <p className="text-sm text-blue-700">
                This information was found on: {results.page_references.join(', ')}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!results && !loading && (
        <div className="text-center py-12">
          <Search className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">Ready to search</h3>
          <p className="mt-1 text-sm text-gray-500">
            Enter your question above to search through your documents.
          </p>
        </div>
      )}
    </div>
  );
};

export default QueryPage;
