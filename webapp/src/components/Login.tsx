// src/components/Login.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { setToken } from '../utils/tokens';
import { loginUser, registerUser } from '../utils/api';
import TopBar from './TopBar';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const data = await loginUser(email, password);
      setToken(data.token);
      navigate('/');
    } catch (error) {
      alert((error as Error).message);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      await registerUser(email, password);
      alert('Registration successful. Please login.');
    } catch (error) {
      alert((error as Error).message);
    }
  };

  return (
    <div className="login-page">
      <TopBar />
      <div className="auth-container">
        <h2>Login</h2>
        <form onSubmit={handleLogin}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <div className="button-group">
            <button type="submit">Login</button>
            <button type="button" onClick={handleRegister}>
              Register
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;