import React from 'react';
import { Link } from 'react-router-dom';
import logo from '../assets/aicacia_logo.png';

const TopBar: React.FC = () => {
  return (
    <header className="top-bar">
      <Link to="/" className="top-bar-link">
        <img src={logo} alt="Aicacia Logo" className="logo" />
        <h1>Aicacia</h1>
      </Link>
    </header>
  );
};

export default TopBar;