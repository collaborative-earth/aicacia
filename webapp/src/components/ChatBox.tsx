import React, { useState } from 'react';
import '../styles/ChatBox.css';
import { chatApiCall, sendFeedbackApiCall } from '../utils/api'; // Add feedback API call here
import ReactMarkdown from 'react-markdown';

const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<{ sender: 'user' | 'bot', text: string, feedback?: 'up' | 'down', message_id?: string }[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState<string | undefined>(undefined);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const sender = 'user' as 'user' | 'bot';
    const userMessage = { sender, text: input };
    const messages_with_user_message = [...messages, userMessage];
    setMessages(messages_with_user_message);
    setInput('');

    setLoading(true);

    const res = await chatApiCall(userMessage.text, threadId);

    setThreadId(res.thread_id);
    setLoading(false);

    const botResponse = { 
      sender: 'bot' as 'user' | 'bot',
      text: res.chat_messages[res.chat_messages.length - 1].message,
      message_id: res.chat_messages[res.chat_messages.length - 1].message_id,
    };
    const messages_with_bot_response = [...messages_with_user_message, botResponse];
    setMessages(messages_with_bot_response);
  };

  const handleInputKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  const handleFeedback = async (index: number, feedback: 'up' | 'down') => {
    const updatedMessages = [...messages];
    updatedMessages[index].feedback = feedback; // Update feedback for the message
    setMessages(updatedMessages);

    // API call for feedback
    await sendFeedbackApiCall({
      message_id: messages[index].message_id!,
      thread_id: threadId!,
      feedback,
    });
  };

  return (
    <div className="chatbox">
      <h2>Restoration Projects Chat!</h2>
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message-bubble ${message.sender}`}>
            <ReactMarkdown>{message.text}</ReactMarkdown>
            {message.sender === 'bot' && (
              <div className="feedback-buttons">
                <button 
                  className={`thumb-button ${message.feedback === 'up' ? 'selected' : ''}`} 
                  onClick={() => handleFeedback(index, 'up')}
                >
                  👍
                </button>
                <button 
                  className={`thumb-button ${message.feedback === 'down' ? 'selected' : ''}`} 
                  onClick={() => handleFeedback(index, 'down')}
                >
                  👎
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      <div className="input-bar">
        <input
          type="text"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleInputKeyPress}
          className="input-field"
        />
      </div>
      <div className={`loader-container ${loading ? 'show' : ''}`}>
        <span className="loader-text">AI is thinking...</span>
      </div>
    </div>
  );
};

export default ChatBox;
