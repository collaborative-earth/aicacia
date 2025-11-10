import React, { useEffect, useState } from 'react';
import { getThreadsApiCall, deleteThreadApiCall, ThreadSummary } from '../utils/api';
import '../styles/ThreadList.css';

interface ThreadListProps {
  onThreadSelect: (threadId: string | null) => void;
  activeThreadId: string | null;
  refreshTrigger: number;
}

const ThreadList: React.FC<ThreadListProps> = ({ onThreadSelect, activeThreadId, refreshTrigger }) => {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingThreadId, setDeletingThreadId] = useState<string | null>(null);

  const loadThreads = async () => {
    setLoading(true);
    try {
      const response = await getThreadsApiCall();
      setThreads(response.threads);
    } catch (error) {
      console.error('Failed to load threads:', error);
      setThreads([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadThreads();
  }, [refreshTrigger]);

  const handleNewChat = () => {
    onThreadSelect(null);
  };

  const handleDeleteThread = async (threadId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    if (!window.confirm('Are you sure you want to delete this conversation?')) {
      return;
    }

    setDeletingThreadId(threadId);
    try {
      await deleteThreadApiCall(threadId);
      setThreads(threads.filter(t => t.thread_id !== threadId));

      // If we deleted the active thread, start a new chat
      if (activeThreadId === threadId) {
        onThreadSelect(null);
      }
    } catch (error) {
      console.error('Failed to delete thread:', error);
      alert('Failed to delete conversation');
    } finally {
      setDeletingThreadId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMs = now.getTime() - date.getTime();
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    // Handle negative or zero cases (future dates or same day)
    if (diffInDays <= 0) {
      return 'Today';
    } else if (diffInDays === 1) {
      return 'Yesterday';
    } else if (diffInDays < 7) {
      return `${diffInDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  return (
    <div className="thread-list-sidebar">
      <button className="new-chat-btn" onClick={handleNewChat}>
        <span className="new-chat-icon">+</span>
        New chat
      </button>

      {loading ? (
        <div className="thread-loading">Loading conversations...</div>
      ) : (
        <div className="thread-list">
          {threads.length === 0 ? (
            <div className="no-threads">
              No conversations yet. Start a new chat!
            </div>
          ) : (
            threads.map((thread) => (
              <div
                key={thread.thread_id}
                className={`thread-item ${activeThreadId === thread.thread_id ? 'active' : ''} ${deletingThreadId === thread.thread_id ? 'deleting' : ''}`}
                onClick={() => onThreadSelect(thread.thread_id)}
              >
                <div className="thread-content">
                  <div className="thread-message">{thread.last_message}</div>
                  <div className="thread-meta">
                    <span className="thread-date">{formatDate(thread.last_message_time)}</span>
                    <span className="thread-count">{thread.message_count} messages</span>
                  </div>
                </div>
                <button
                  className="delete-thread-btn"
                  onClick={(e) => handleDeleteThread(thread.thread_id, e)}
                  disabled={deletingThreadId === thread.thread_id}
                  title="Delete conversation"
                >
                  🗑️
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default ThreadList;
