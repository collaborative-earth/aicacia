import React, { useState } from 'react';
import UserList from './UserList';
import AdminFeedbacks from './AdminFeedbacks';
import AdminDocuments from './AdminDocuments';
import AdminQueryHistory from './AdminQueryHistory';
import AdminQuestionSection from './AdminQuestionSection';
import '../../styles/QueryHistory.css';

const AdminLayout: React.FC = () => {
  const [selectedUserEmail, setSelectedUserEmail] = useState<string | null>(null);
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'feedbacks' | 'documents'>('feedbacks');

  const handleUserSelect = (userEmail: string) => {
    setSelectedUserEmail(userEmail);
    setSelectedQueryId(null); // Clear selected query when user changes
  };

  const handleQuerySelect = (queryId: string) => {
    setSelectedQueryId(queryId);
  };

  return (
    <>
      <aside className="sidebar">
        <UserList 
          onUserSelect={handleUserSelect} 
          selectedUserEmail={selectedUserEmail}
        />
        
        {/* Tab Navigation */}
        <div className="admin-tabs" style={{ marginTop: '20px' }}>
          <button
            className={`tab-button ${activeTab === 'feedbacks' ? 'active' : ''}`}
            onClick={() => setActiveTab('feedbacks')}
          >
            Feedbacks
          </button>
          <button
            className={`tab-button ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            Documents
          </button>
        </div>

        {/* Query History for Feedbacks Tab */}
        {activeTab === 'feedbacks' && selectedUserEmail && (
          <div style={{ marginTop: '20px' }}>
            <AdminQueryHistory 
              userEmail={selectedUserEmail}
              onQuerySelect={handleQuerySelect}
              selectedQueryId={selectedQueryId}
            />
          </div>
        )}
      </aside>
      
      <main className="main-content">
        {activeTab === 'feedbacks' ? (
          <AdminQuestionSection 
            userEmail={selectedUserEmail}
            selectedQueryId={selectedQueryId}
          />
        ) : (
          <AdminDocuments 
            selectedUserEmail={selectedUserEmail}
          />
        )}
      </main>
    </>
  );
};

export default AdminLayout;
