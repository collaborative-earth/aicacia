import axios from 'axios';
import { getToken, removeToken } from './tokens';

// Base URL for the API - use environment variable with fallback
const API_URL = import.meta.env.VITE_API_URL || 'http://3.137.35.87:8000';

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
      window.location.href = '/login';
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

interface Reference {
  url: string;
  title: string;
  score: number;
  chunk: string;
}

interface ReferenceFeedback {
  feedback: number;
  feedback_reason: string;
}

interface QuestionResponse {
  query_id: string;
  references: Reference[];
  summary: string;
}

interface FeedbackRequest {
  query_id: string;
  references_feedback: ReferenceFeedback[];
  summary_feedback: number;
  feedback: string;
}

export async function askQuestion(query: string): Promise<QuestionResponse> {
  try {
    const response = await api.post('/user_query', { question: query });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch:', error);
    throw new Error('Failed to fetch');
  }
}

export async function submitFeedback(feedback: FeedbackRequest): Promise<void> {
  try {
    await api.post('/feedback', feedback);
  } catch (error) {
    console.error('Failed to submit feedback:', error);
    throw new Error('Failed to submit feedback');
  }
}

export interface ChatMessage {
  message: string;
  message_from: 'user' | 'agent';
  message_id?: string;
}

export interface ChatResponse {
  chat_messages: ChatMessage[];
  thread_id: string;
}

export interface ThreadSummary {
  thread_id: string;
  last_message: string;
  last_message_time: string;
  message_count: number;
}

export interface ThreadListResponse {
  threads: ThreadSummary[];
}

export const chatApiCall = async (message: string, thread_id?: string): Promise<ChatResponse> => {
    try {
        const response = await api.post('/chat', { message, thread_id: thread_id });
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to send chat message');
    }
}

export const getThreadsApiCall = async (): Promise<ThreadListResponse> => {
    try {
        const response = await api.get('/chat/threads');
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to fetch threads');
    }
}

export const getThreadMessagesApiCall = async (thread_id: string): Promise<ChatResponse> => {
    try {
        const response = await api.get(`/chat/threads/${thread_id}`);
        return response.data;
    } catch (error) {
        console.log(error);
        throw new Error('Failed to fetch thread messages');
    }
}

export const deleteThreadApiCall = async (thread_id: string): Promise<void> => {
    try {
        await api.delete(`/chat/threads/${thread_id}`);
    } catch (error) {
        console.log(error);
        throw new Error('Failed to delete thread');
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

// Admin API functions
export const listAllUsers = async () => {
    try {
        const response = await api.get('/admin/users');
        return response.data;
    } catch (error) {
        console.error('Failed to fetch users:', error);
        throw new Error('Failed to fetch users');
    }
};

export const listUserQueries = async (userId: string, skip: number = 0, limit: number = 10) => {
    try {
        const response = await api.get(`/admin/users/${userId}/queries`, {
            params: { skip, limit }
        });
        return response.data;
    } catch (error) {
        console.error('Failed to fetch user queries:', error);
        throw new Error('Failed to fetch user queries');
    }
};

export const getUserQueryWithFeedback = async (userId: string, queryId: string) => {
    try {
        const response = await api.get(`/admin/users/${userId}/queries/${queryId}`);
        return response.data;
    } catch (error) {
        console.error('Failed to fetch user query:', error);
        throw new Error('Failed to fetch user query');
    }
};

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

export const listQueries = async (skip: number = 0, limit: number = 10) => {
  try {
    const response = await api.get(`/user_query/list`, {
      params: { skip, limit }
    });
    return response.data;
  } catch (error) {
    console.error('Failed to fetch queries:', error);
    throw new Error('Failed to fetch queries');
  }
};

export const getQueryWithFeedback = async (queryId: string) => {
  try {
    const response = await api.get(`/user_query/${queryId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch query:', error);
    throw new Error('Failed to fetch query');
  }
};