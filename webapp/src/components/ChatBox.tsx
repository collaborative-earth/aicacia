import React, { useState, useEffect, useRef } from 'react';
import '../styles/ChatBox.css';
import { chatApiCall, sendFeedbackApiCall, ChatMessage } from '../utils/api';
import ReactMarkdown from 'react-markdown';

interface ChatBoxProps {
  threadId: string | null;
  initialMessages: ChatMessage[];
  onNewMessage: (messages: ChatMessage[], threadId: string) => void;
}

const ChatBox: React.FC<ChatBoxProps> = ({ threadId, initialMessages, onNewMessage }) => {
  const [messages, setMessages] = useState<{ sender: 'user' | 'agent', text: string, feedback?: 'up' | 'down', message_id?: string }[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Convert API messages to internal format
  useEffect(() => {
    const convertedMessages = initialMessages.map(msg => ({
      sender: msg.message_from as 'user' | 'agent',
      text: msg.message,
      message_id: msg.message_id,
    }));
    setMessages(convertedMessages);
  }, [initialMessages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messages.length > 0) {
      // Use setTimeout to ensure DOM is updated
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { sender: 'user' as 'user' | 'agent', text: input };
    const messagesWithUserMessage = [...messages, userMessage];
    setMessages(messagesWithUserMessage);
    setInput('');
    setLoading(true);

    try {
      const res = await chatApiCall(input, threadId || undefined);
      setLoading(false);

      // Convert all messages from API response
      const allMessages = res.chat_messages.map(msg => ({
        sender: msg.message_from as 'user' | 'agent',
        text: msg.message,
        message_id: msg.message_id,
      }));

      setMessages(allMessages);
      onNewMessage(res.chat_messages, res.thread_id);
    } catch (error) {
      console.error('Failed to send message:', error);
      setLoading(false);
      // Revert to previous messages on error
      setMessages(messages);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFeedback = async (index: number, feedback: 'up' | 'down') => {
    const updatedMessages = [...messages];
    updatedMessages[index].feedback = feedback;
    setMessages(updatedMessages);

    if (messages[index].message_id && threadId) {
      try {
        await sendFeedbackApiCall({
          message_id: messages[index].message_id!,
          thread_id: threadId,
          feedback,
        });
      } catch (error) {
        console.error('Failed to send feedback:', error);
      }
    }
  };

  return (
    <div className="chatbox">
      {messages.length === 0 ? (
        <div className="chat-welcome">
          <h1>Aicacia Chat</h1>
          <p>Ask me anything about environmental restoration projects!</p>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((message, index) => (
            <div key={index} className={`message-container ${message.sender}`}>
              <div className="message-content">
                <div className="message-bubble">
                  <ReactMarkdown>{message.text}</ReactMarkdown>
                </div>
                {message.sender === 'agent' && message.message_id && (
                  <div className="feedback-buttons">
                    <button
                      className={`thumb-button ${message.feedback === 'up' ? 'selected' : ''}`}
                      onClick={() => handleFeedback(index, 'up')}
                      title="Good response"
                    >
                      👍
                    </button>
                    <button
                      className={`thumb-button ${message.feedback === 'down' ? 'selected' : ''}`}
                      onClick={() => handleFeedback(index, 'down')}
                      title="Bad response"
                    >
                      👎
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="message-container agent">
              <div className="message-content">
                <div className="message-bubble loading">
                  <span className="loader-text">Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      <div className="input-container">
        <div className={`input-wrapper ${input.trim() ? 'has-text' : ''}`}>
          <textarea
            placeholder="Message Aicacia..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleInputKeyDown}
            className="input-field"
            rows={1}
            disabled={loading}
          />
          <button
            onClick={handleSendMessage}
            className="send-button"
            disabled={loading || !input.trim()}
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatBox;
