import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/aicacia_logo.png';
import '../styles/TopBar.css';

interface TopBarProps {
  isLoggedIn: boolean;
  userInfo: {email: string, user_id: string, is_admin: boolean} | null;
  onLogout: () => void;
}

const TopBar: React.FC<TopBarProps> = ({ isLoggedIn, userInfo, onLogout }) => {
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
          <nav className="top-bar-nav">
            <Link to="/" className="nav-link">Home</Link>
            <Link to="/chat" className="nav-link">Chat</Link>
            {userInfo?.is_admin && (
              <Link to="/admin/feedbacks" className="nav-link admin-link">Admin Feedbacks</Link>
            )}
          </nav>
          <button onClick={onLogout} className="logout-button">Logout</button>
        </div>
      )}
    </header>
  );
};

export default TopBar;
