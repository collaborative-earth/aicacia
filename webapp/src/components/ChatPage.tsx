import React, { useState, useEffect } from 'react';
import ThreadList from './ThreadList';
import ChatBox from './ChatBox';
import { ChatMessage, getThreadMessagesApiCall } from '../utils/api';
import '../styles/ChatPage.css';

const ChatPage: React.FC = () => {
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [refreshThreads, setRefreshThreads] = useState(0);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const loadThreadMessages = async () => {
      if (activeThreadId) {
        try {
          const response = await getThreadMessagesApiCall(activeThreadId);
          setMessages(response.chat_messages);
        } catch (error) {
          console.error('Failed to load thread messages:', error);
          setMessages([]);
        }
      } else {
        setMessages([]);
      }
    };

    loadThreadMessages();
  }, [activeThreadId]);

  const handleThreadSelect = (threadId: string | null) => {
    setActiveThreadId(threadId);
    setIsSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const handleNewMessage = (newMessages: ChatMessage[], newThreadId: string) => {
    setMessages(newMessages);

    // If this is a new thread (activeThreadId was null), update it
    if (!activeThreadId && newThreadId) {
      setActiveThreadId(newThreadId);
      // Trigger thread list refresh after a short delay to let the backend commit
      setTimeout(() => setRefreshThreads(prev => prev + 1), 500);
    }
  };

  return (
    <div className="chat-page">
      {/* Hamburger menu button for mobile */}
      <button 
        className="hamburger-menu" 
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        aria-label="Toggle menu"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div 
          className="sidebar-overlay" 
          role="button"
          tabIndex={0}
          onClick={() => setIsSidebarOpen(false)}
          onKeyDown={(event) => {
            if (event.key === 'Escape' || event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              setIsSidebarOpen(false);
            }
          }}
        />
      )}

      {/* Sidebar */}
      <div className={`sidebar-container ${isSidebarOpen ? 'open' : ''}`}>
        <ThreadList
          onThreadSelect={handleThreadSelect}
          activeThreadId={activeThreadId}
          refreshTrigger={refreshThreads}
        />
      </div>

      {/* Main chat area */}
      <div className="chat-main">
        <ChatBox
          threadId={activeThreadId}
          initialMessages={messages}
          onNewMessage={handleNewMessage}
        />
      </div>
    </div>
  );
};

export default ChatPage;
