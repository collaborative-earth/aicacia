// src/components/Login.tsx
import React, { useState } from 'react';
import { setToken } from '../utils/tokens';
import { loginUser, registerUser } from '../utils/api';
import '../styles/Login.css';

interface LoginProps {
  onLoginSuccess: () => void;
}

const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const data = await loginUser(email, password);
      setToken(data.token);
      onLoginSuccess();
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
      <div className="auth-container">
        <h2>Sign In</h2>
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
            <button type="submit" className="button-primary">Login</button>
            {/* <button type="button" onClick={handleRegister} className="button-secondary">
              Register
            </button> */}
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;