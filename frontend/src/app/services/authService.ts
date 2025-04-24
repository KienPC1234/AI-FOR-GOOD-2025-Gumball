import axios from 'axios';
import Cookies from 'js-cookie';
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
    const token = typeof window !== 'undefined' ? Cookies.get('token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const loginUser = async (credentials: LoginCredentials): Promise<AuthResponse> => {
  try {
    // Try the standard OAuth2 login endpoint first
    logApiCall('POST', '/auth/login', { email: credentials.email });

    // Create form data for OAuth2 password flow
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const response = await api.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    console.log('Login successful:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Login failed:', error.response?.data || error.message);

    // Try the simple login endpoint as fallback
    try {
      logApiCall('POST', '/auth/login-simple', { email: credentials.email });
      const simpleResponse = await api.post<AuthResponse>('/auth/login-simple', credentials);
      console.log('Simple login successful:', simpleResponse.data);
      return simpleResponse.data;
    } catch (fallbackError: any) {
      console.error('Simple login also failed:', fallbackError.response?.data || fallbackError.message);
      throw new Error(error.response?.data?.detail || fallbackError.response?.data?.detail || 'Login failed');
    }
  }
};

export const registerUser = async (credentials: RegisterCredentials): Promise<void> => {
  try {
    logApiCall('POST', '/auth/register', { email: credentials.email });
    const response = await api.post('/auth/register', {
      email: credentials.email,
      password: credentials.password,
      is_active: true,
      is_superuser: false
    });
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

    // Try to get user data from /auth/me endpoint as fallback
    try {
      logApiCall('GET', '/auth/me');
      const meResponse = await api.get<User>('/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      console.log('Got user from /me endpoint:', meResponse.data);
      return meResponse.data;
    } catch (fallbackError: any) {
      console.error('Failed to get user data from /me endpoint:', fallbackError.response?.data || fallbackError.message);
      throw new Error(error.response?.data?.detail || fallbackError.response?.data?.detail || 'Failed to get user data');
    }
  }
};

export const refreshToken = async (token: string, refToken: string): Promise<void> => {
  try {
    const response = await api.post<AuthResponse>('/api/auth/refresh-token', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          refreshToken: refToken,
        },
    });
    Cookies.set('token', response.data.access_token, { expires: 1 });
    Cookies.set('refresh_token', response.data.refresh_token, { expires: 7 });
  } catch (error: any) {
    const errmsg = error.response?.data || error.message;
    console.error('Failed to refresh token:', errmsg);
    throw new Error(errmsg || 'Failed to get user data');
  }
};