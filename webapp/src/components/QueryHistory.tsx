import React, { useEffect, useState } from 'react';
import { listQueries } from '../utils/api';
import '../styles/QueryHistory.css';

interface QueryHistoryProps {
  onQuerySelect: (queryId: string) => void;
  refreshTrigger: number;
  onContentChange?: (hasContent: boolean) => void;
  onItemClick?: () => void;
}

interface QueryItem {
  query_id: string;
  question: string;
  created_at: string;
  summary: string;
}

const QueryHistory: React.FC<QueryHistoryProps> = ({ onQuerySelect, refreshTrigger, onContentChange, onItemClick }) => {
  const [queries, setQueries] = useState<QueryItem[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const pageSize = 20;

  useEffect(() => {
    const loadQueries = async () => {
      setLoading(true);
      try {
        const response = await listQueries(currentPage * pageSize, pageSize);
        setQueries(response.queries);
        setTotalCount(response.total_count);
        onContentChange?.(response.total_count > 0);
      } catch (error) {
        console.error('Failed to load queries:', error);
        setQueries([]);
        setTotalCount(0);
        onContentChange?.(false);
      } finally {
        setLoading(false);
      }
    };

    loadQueries();
  }, [currentPage, refreshTrigger]);

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleItemClick = (queryId: string) => {
    onQuerySelect(queryId);
    onItemClick?.();
  };

  return (
    <div className="query-history">
      <h3>Previous Questions</h3>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : queries.length === 0 ? (
        <div className="no-queries">No previous questions yet</div>
      ) : (
        <>
          <div className="query-list">
            {queries.map((query) => (
              <div
                key={query.query_id}
                className="history-item"
                onClick={() => handleItemClick(query.query_id)}
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