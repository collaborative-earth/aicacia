import axios from 'axios';

// Base URL for the API
const API_URL = 'http://localhost:8000';

// Axios instance with default settings
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});


export const loginUser = async (email: string, password: string) => {
  try {
    const response = await api.post('/user/login', { email, password });
    return response.data;
  } catch (error) {
    console.log(error);
    throw new Error('Invalid email or password');
  }
};


export const registerUser = async (email: string, password: string) => {
    try {
        const response = await api.post('/user', { email, password });
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Registration failed');
    }
}