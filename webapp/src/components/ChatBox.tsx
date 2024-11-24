import React, { useState } from 'react';
import '../styles/ChatBox.css';
import { chatApiCall } from '../utils/api';
import ReactMarkdown from 'react-markdown';

const ChatBox: React.FC = () => {
  const [messages, setMessages] = useState<{ sender: 'user' | 'bot', text: string }[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState<string | undefined>(undefined);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: { sender: 'user' | 'bot', text: string } = { sender: 'user', text: input };
    let messages_with_user_message = [...messages, userMessage];
    setMessages(messages_with_user_message);
    setInput('');

    setLoading(true);

    console.log(messages);

    const res = await chatApiCall(userMessage.text, threadId);

    setThreadId(res.thread_id);

    setLoading(false);

    const botResponse: { sender: 'user' | 'bot', text: string } = { 
      sender: 'bot', 
      text: res.chat_messages[res.chat_messages.length-1].message 
    };
    let messages_with_bot_response = [...messages_with_user_message, botResponse];
    setMessages(messages_with_bot_response);
  };

  const handleInputKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="chatbox">
      <h2> Restoration Projects Chat!</h2>
      <div className="chat-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message-bubble ${message.sender}`}>
             <ReactMarkdown>{message.text}</ReactMarkdown>
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
