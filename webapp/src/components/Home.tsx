import React from 'react';
import { useNavigate } from 'react-router-dom';
import { removeToken } from '../utils/tokens';
import TopBar from './TopBar';


const Home: React.FC = () => {
  const navigate = useNavigate();

  const handleButtonClick = () => {
    removeToken();
    navigate('/login');
  }

  return (
    <div className="home-page">
      <TopBar />
      <div className="content">
        <button onClick={handleButtonClick}>Logout</button>
      </div>
    </div>
  );
};

export default Home;