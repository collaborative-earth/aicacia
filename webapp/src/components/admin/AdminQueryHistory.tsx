import React, { useEffect, useState } from 'react';
import { listUserQueries } from '../../utils/api';
import '../../styles/QueryHistory.css';

interface AdminQueryHistoryProps {
  userId: string | null;
  onQuerySelect: (queryId: string) => void;
  selectedQueryId: string | null;
}

interface QueryItem {
  query_id: string;
  question: string;
  created_at: string;
  summary: string;
}

const AdminQueryHistory: React.FC<AdminQueryHistoryProps> = ({ 
  userId, 
  onQuerySelect, 
  selectedQueryId 
}) => {
  const [queries, setQueries] = useState<QueryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    if (!userId) {
      setQueries([]);
      setTotalCount(0);
      setCurrentPage(0);
      return;
    }

    const loadQueries = async () => {
      setLoading(true);
      try {
        const response = await listUserQueries(userId, currentPage * pageSize, pageSize);
        setQueries(response.queries);
        setTotalCount(response.total_count);
      } catch (error) {
        console.error('Failed to load user queries:', error);
        setQueries([]);
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    loadQueries();
  }, [userId, currentPage]);

  // Reset page when user changes
  useEffect(() => {
    setCurrentPage(0);
  }, [userId]);

  const totalPages = Math.ceil(totalCount / pageSize);

  if (!userId) {
    return (
      <div className="history-sidebar">
        <h3>User Questions</h3>
        <div className="loading">Select a user to view their questions</div>
      </div>
    );
  }

  return (
    <div className="history-sidebar">
      <h3>User Questions ({totalCount})</h3>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <div className="query-list">
            {queries.map((query) => (
              <div
                key={query.query_id}
                className={`history-item ${selectedQueryId === query.query_id ? 'selected' : ''}`}
                onClick={() => onQuerySelect(query.query_id)}
              >
                <div className="history-date">
                  {new Date(query.created_at).toLocaleDateString()}
                </div>
                <div className="history-question">{query.question}</div>
              </div>
            ))}
          </div>
          {totalPages > 1 && (
            <div className="history-pagination">
              <button
                onClick={() => setCurrentPage(p => p - 1)}
                disabled={currentPage === 0}
              >
                Previous
              </button>
              <span className="page-info">
                Page {currentPage + 1} of {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(p => p + 1)}
                disabled={currentPage >= totalPages - 1}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default AdminQueryHistory;
