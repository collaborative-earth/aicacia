import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/aicacia_logo.png';
import '../styles/TopBar.css';

interface TopBarProps {
  isLoggedIn: boolean;
  onLogout: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ isLoggedIn, onLogout }) => {
  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <Link to="/" className="top-bar-link">
          <img src={logo} alt="Aicacia Logo" className="logo" />
          <h1>Aicacia</h1>
        </Link>
      </div>
      {isLoggedIn && (
        <div className="top-bar-right">
          <button onClick={onLogout} className="logout-button">Logout</button>
        </div>
      )}
    </header>
  );
};

export default TopBar;
