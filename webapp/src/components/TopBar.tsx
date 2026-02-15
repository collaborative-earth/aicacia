import React from 'react';
import { Link, NavLink } from 'react-router-dom';
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
            <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>Home</NavLink>
            <NavLink to="/chat" className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>Chat</NavLink>
            {userInfo?.is_admin && (
              <NavLink to="/admin/feedbacks" className={({ isActive }) => `nav-link${isActive ? ' nav-link--active' : ''}`}>Admin Feedbacks</NavLink>
            )}
          </nav>
          <button onClick={onLogout} className="logout-button">Logout</button>
        </div>
      )}
    </header>
  );
};

export default TopBar;
