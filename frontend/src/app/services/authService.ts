import axios from 'axios';
import { LoginCredentials, RegisterCredentials, User, AuthResponse } from '../types/auth';

const API_URL = 'http://localhost:8000/api';

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
    const response = await api.post<AuthResponse>('/auth/login-simple', credentials);
    return response.data;
  } catch (error) {
    throw new Error('Login failed');
  }
};

export const registerUser = async (credentials: RegisterCredentials): Promise<void> => {
  try {
    await api.post('/auth/register', credentials);
  } catch (error) {
    throw new Error('Registration failed');
  }
};

export const getCurrentUser = async (token: string): Promise<User> => {
  try {
    const response = await api.post<User>(
      '/auth/test-token',
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error('Failed to get user data');
  }
};
