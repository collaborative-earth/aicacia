import React from 'react';
import '../styles/Home.css';

const Home: React.FC = () => {
  return (
    <div className="home-page">
      <div className="home-content">
        {/* The main content is now rendered directly in App.tsx */}
        <h1>Welcome to Aicacia</h1>
      </div>
    </div>
  );
};

export default Home;

