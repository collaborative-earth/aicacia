import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link } from 'react-router-dom';
import logo from '../assets/aicacia_logo.png';
import { getToken, removeToken } from '../utils/tokens';
import '../styles/TopBar.css';

const TopBar: React.FC = () => {
  const navigate = useNavigate();
  const [loggedIn, setLoggedIn] = useState(false);

  const handleButtonClick = () => {
    removeToken();
    navigate('/login');
  };

  useEffect(() => {
    const token = getToken();
    if (token) {
      setLoggedIn(true);
    }
  }, []);

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <Link to="/" className="top-bar-link">
          <img src={logo} alt="Aicacia Logo" className="logo" />
          <h1>Aicacia</h1>
        </Link>
      </div>
      {loggedIn && (
        <div className="top-bar-right">
          <button onClick={handleButtonClick}>Logout</button>
        </div>
      )}
    </header>
  );
};

export default TopBar;
