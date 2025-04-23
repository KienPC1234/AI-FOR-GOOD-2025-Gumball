'use client';

import axios from 'axios';
import Cookies from 'js-cookie';
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
    const token = typeof window !== 'undefined' ? Cookies.get('token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

const loginUser = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    console.log('Attempting login with credentials:', credentials);

    // Try the login-simple endpoint
    const response = await api.post<AuthResponse>('/auth/login-simple', {
      email: credentials.email,
      password: credentials.password
    });

    console.log('Login response:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Login failed:', error);
    console.error('Response data:', error.response?.data);
    console.error('Status code:', error.response?.status);

    let errorMessage = 'Invalid email or password';

    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    }

    throw new Error(errorMessage);
  }
};

const registerUser = async (credentials: RegisterCredentials): Promise<void> => {
  try {
    console.log('Attempting to register with credentials:', {
      email: credentials.email,
      role: credentials.role,
      full_name: credentials.full_name
    });

    await api.post('/auth/register', {
      email: credentials.email,
      password: credentials.password,
      role: credentials.role || 'patient',
      full_name: credentials.full_name || '',
      is_active: true,
      is_superuser: false
    });

    console.log('Registration successful');
  } catch (error: any) {
    console.error('Registration failed:', error);
    console.error('Response data:', error.response?.data);
    console.error('Status code:', error.response?.status);

    let errorMessage = 'Registration failed';
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail;
    }

    throw new Error(errorMessage);
  }
};

const getCurrentUser = async (token: string): Promise<User> => {
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
  } catch (error: any) {
    console.error('Failed to get user data:', error.response?.data || error.message);
    throw new Error(error.response?.data?.detail || 'Failed to get user data');
  }
};

export { loginUser, registerUser, getCurrentUser };
