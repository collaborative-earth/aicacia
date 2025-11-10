import React, { useState, useEffect } from 'react';
import { 
  uploadUserDocuments, 
  listUserDocuments, 
  deleteUserDocument, 
  getUserDocumentQuota,
  UserDocumentInfo,
  UserDocumentQuota 
} from '../../utils/api';
import '../../styles/QueryHistory.css';
import '../../styles/AdminDocuments.css';

interface AdminDocumentsProps {
  selectedUserEmail: string | null;
}

const AdminDocuments: React.FC<AdminDocumentsProps> = ({ selectedUserEmail }) => {
  const [documents, setDocuments] = useState<UserDocumentInfo[]>([]);
  const [quota, setQuota] = useState<UserDocumentQuota | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  // Load documents and quota when user changes
  useEffect(() => {
    if (selectedUserEmail) {
      loadUserData();
    } else {
      setDocuments([]);
      setQuota(null);
    }
  }, [selectedUserEmail]);

  const loadUserData = async () => {
    if (!selectedUserEmail) return;
    
    setLoading(true);
    try {
      const [documentsResponse, quotaResponse] = await Promise.all([
        listUserDocuments(selectedUserEmail),
        getUserDocumentQuota(selectedUserEmail)
      ]);
      setDocuments(documentsResponse.documents);
      setQuota(quotaResponse);
    } catch (error) {
      console.error('Failed to load user data:', error);
      setMessage({ type: 'error', text: 'Failed to load user data' });
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      // Validate file count
      if (files.length > 5) {
        setMessage({ type: 'error', text: 'Maximum 5 files allowed per upload' });
        return;
      }
      
      // Validate file types
      const invalidFiles = Array.from(files).filter(file => !file.name.toLowerCase().endsWith('.pdf'));
      if (invalidFiles.length > 0) {
        setMessage({ type: 'error', text: 'Only PDF files are allowed' });
        return;
      }
      
      setSelectedFiles(files);
      setMessage(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedUserEmail || !selectedFiles) return;
    
    setUploading(true);
    setMessage(null);
    
    try {
      const response = await uploadUserDocuments(selectedUserEmail, selectedFiles);
      setDocuments(response.uploaded_documents);
      setQuota(prev => prev ? {
        ...prev,
        current_document_count: response.user_document_count,
        remaining_quota: response.remaining_quota
      } : null);
      
      setMessage({ 
        type: 'success', 
        text: `Successfully uploaded ${response.total_uploaded} document(s)` 
      });
      
      // Clear file input
      setSelectedFiles(null);
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Upload failed:', error);
      setMessage({ type: 'error', text: 'Upload failed. Please try again.' });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!selectedUserEmail) return;
    
    if (!window.confirm(`Are you sure you want to delete "${filename}"?`)) {
      return;
    }
    
    try {
      await deleteUserDocument(selectedUserEmail, docId);
      setMessage({ type: 'success', text: `Deleted "${filename}"` });
      loadUserData(); // Reload data
    } catch (error) {
      console.error('Delete failed:', error);
      setMessage({ type: 'error', text: 'Failed to delete document' });
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!selectedUserEmail) {
    return (
      <div className="main-content">
        <div className="no-selection">
          <h2>Document Management</h2>
          <p>Select a user to manage their documents</p>
        </div>
      </div>
    );
  }

  return (
    <div className="main-content">
      <div className="document-management">
        <div className="document-header">
          <h2>Document Management</h2>
          <p className="user-email">User: {selectedUserEmail}</p>
        </div>

        {/* Quota Information */}
        {quota && (
          <div className="quota-info">
            <div className="quota-stats">
              <span className="quota-current">{quota.current_document_count}</span>
              <span className="quota-separator">/</span>
              <span className="quota-max">{quota.max_documents}</span>
              <span className="quota-label">documents</span>
            </div>
            <div className="quota-remaining">
              {quota.remaining_quota} remaining
            </div>
          </div>
        )}

        {/* Upload Section */}
        <div className="upload-section">
          <h3>Upload Documents</h3>
          <div className="upload-controls">
            <input
              id="file-input"
              type="file"
              multiple
              accept=".pdf"
              onChange={handleFileSelect}
              className="file-input"
            />
            <button
              onClick={handleUpload}
              disabled={!selectedFiles || uploading || quota?.remaining_quota === 0}
              className="upload-button"
            >
              {uploading ? 'Uploading...' : 'Upload PDFs'}
            </button>
          </div>
          {selectedFiles && (
            <div className="selected-files">
              <p>Selected files:</p>
              <ul>
                {Array.from(selectedFiles).map((file, index) => (
                  <li key={index}>{file.name} ({formatFileSize(file.size)})</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Message Display */}
        {message && (
          <div className={`message ${message.type}`}>
            {message.text}
          </div>
        )}

        {/* Documents List */}
        <div className="documents-section">
          <h3>User Documents ({documents.length})</h3>
          {loading ? (
            <div className="loading">Loading documents...</div>
          ) : documents.length === 0 ? (
            <div className="no-documents">
              <p>No documents uploaded yet</p>
            </div>
          ) : (
            <div className="documents-list">
              {documents.map((doc) => (
                <div key={doc.doc_id} className="document-item">
                  <div className="document-info">
                    <div className="document-name">{doc.filename}</div>
                    <div className="document-details">
                      <span className="file-size">{formatFileSize(doc.file_size)}</span>
                      <span className="separator">•</span>
                      <span className="upload-date">{formatDate(doc.created_at)}</span>
                      <span className="separator">•</span>
                      <span className={`status status-${doc.processing_status}`}>
                        {doc.processing_status}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(doc.doc_id, doc.filename)}
                    className="delete-button"
                    title="Delete document"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminDocuments;
