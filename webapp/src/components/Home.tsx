import React, { useState } from 'react';
import TopBar from './TopBar';
import QuestionSection from './QuestionSection';
import ChatBox from './ChatBox';
import '../styles/Home.css';

const Home: React.FC = () => {
  const [isChatMode, setIsChatMode] = useState(false);

  return (
    <div className="home-page">
      <TopBar />
      <div className="home-content">
        <button onClick={() => setIsChatMode(!isChatMode)}>
          {isChatMode ? 'Switch to Search' : 'Switch to Chat'}
        </button>

        {isChatMode ? <ChatBox /> : <QuestionSection />}
      </div>
    </div>
  );
};

export default Home;

