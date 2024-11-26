import axios from 'axios';
import { getToken, removeToken } from './tokens';

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

    const unprotectedRoutes = ['/user/login', '/user'];

    if (token && !unprotectedRoutes.includes(config.url || '')) {
      config.headers['aicacia-api-token'] = token;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      removeToken();
    }

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
  feedback: { query_id: string; summary_feedback: number; references_feedback: number[]; feedback: string }
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

export const getUserInfo = async () => {
    try {
        const response = await api.get('/user_info/');
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to get user');
    }
}

export const sendFeedbackApiCall = async ({ message_id, feedback, thread_id }: { message_id: string, feedback: 'up' | 'down', thread_id: string }) => {

  try {
    const response = await api.post('/chat_feedback', { 
      thread_id,
      message_id,
      feedback: feedback === 'up' ? 1 : 0, 
      feedback_message: "" });
    return response.data;
  } catch (error) {
      console.log(error);
      throw new Error('Failed to send chat feedback');
  }
  
};