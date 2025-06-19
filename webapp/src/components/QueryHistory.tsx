import React, { useEffect, useState } from 'react';
import { listQueries } from '../utils/api';
import '../styles/QueryHistory.css';

interface QueryHistoryProps {
  onQuerySelect: (queryId: string) => void;
}

interface QueryItem {
  query_id: string;
  question: string;
  created_at: string;
  summary: string;
}

const QueryHistory: React.FC<QueryHistoryProps> = ({ onQuerySelect }) => {
  const [queries, setQueries] = useState<QueryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(false);
  const pageSize = 20; // Increased page size for sidebar

  const loadQueries = async () => {
    try {
      setLoading(true);
      const response = await listQueries(currentPage * pageSize, pageSize);
      setQueries(response.queries);
      setTotalCount(response.total_count);
    } catch (error) {
      console.error('Failed to load queries:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQueries();
  }, [currentPage]);

  const totalPages = Math.ceil(totalCount / pageSize);

  return (
    <div className="history-sidebar">
      <h3>Previous Questions</h3>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <div className="query-list">
            {queries.map((query) => (
              <div
                key={query.query_id}
                className="history-item"
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

export default QueryHistory; 