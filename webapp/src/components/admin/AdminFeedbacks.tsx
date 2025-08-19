import React, { useState } from 'react';
import UserList from './UserList';
import AdminQueryHistory from './AdminQueryHistory';
import AdminQuestionSection from './AdminQuestionSection';

const AdminFeedbacks: React.FC = () => {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedQueryId, setSelectedQueryId] = useState<string | null>(null);

  const handleUserSelect = (userId: string) => {
    setSelectedUserId(userId);
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
          selectedUserId={selectedUserId}
        />
        <div style={{ marginTop: '20px' }}>
          <AdminQueryHistory 
            userId={selectedUserId}
            onQuerySelect={handleQuerySelect}
            selectedQueryId={selectedQueryId}
          />
        </div>
      </aside>
      <main className="main-content">
        <AdminQuestionSection 
          userId={selectedUserId}
          selectedQueryId={selectedQueryId}
        />
      </main>
    </>
  );
};

export default AdminFeedbacks;
