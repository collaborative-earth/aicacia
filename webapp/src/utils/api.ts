import axios from 'axios';
import { getToken } from './tokens';

// Base URL for the API
const API_URL = 'http://localhost:8000';

// Axios instance with default settings
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = getToken();

    // Define routes that should not include the token
    const unprotectedRoutes = ['/user/login', '/user'];

    // Check if the request URL is not in the list of unprotected routes
    if (token && !unprotectedRoutes.includes(config.url || '')) {
      config.headers['aicacia-api-token'] = token;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);


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


export const askQuestion = async (question: string) => {
    try {
        const response = await api.post('/user_query', { question });
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to ask question');
    }
}


export const submitFeedback = async (
  feedback: { query_id: string; references_feedback: number[]; feedback: string }
) => {
    try {
        const response = await api.post('/feedback', feedback);
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to submit feedback');
    }
}

export const chatApiCall = async (message: string, thread_id?: string) => {
    try {
        const response = await api.post('/chat', { message, thread_id: thread_id });
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to send chat message');
    }
}