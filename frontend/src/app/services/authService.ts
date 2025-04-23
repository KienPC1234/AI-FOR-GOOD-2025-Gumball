import axios from 'axios';
import { LoginCredentials, RegisterCredentials, User, AuthResponse } from '../types/auth';

const API_URL = 'http://localhost:8000/api';

// For development/debugging
const logApiCall = (method: string, endpoint: string, data?: any) => {
  console.log(`API ${method} ${endpoint}`, data || '');
};

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const loginUser = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    logApiCall('POST', '/auth/login-simple', { email: credentials.email });
    const response = await api.post<AuthResponse>('/auth/login-simple', credentials);
    console.log('Login successful:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Login failed:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
};

export const registerUser = async (credentials: RegisterCredentials): Promise<void> => {
  try {
    logApiCall('POST', '/auth/register', { email: credentials.email });
    const response = await api.post('/auth/register', credentials);
    console.log('Registration successful:', response.data);
  } catch (error: any) {
    console.error('Registration failed:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'Registration failed');
  }
};

export const getCurrentUser = async (token: string): Promise<User> => {
  try {
    logApiCall('POST', '/auth/test-token');
    const response = await api.post<User>(
      '/auth/test-token',
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    console.log('Got current user:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Failed to get user data:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'Failed to get user data');
  }
};
