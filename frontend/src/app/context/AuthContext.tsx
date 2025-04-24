'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { toast } from 'react-toastify';
import { AuthState, LoginCredentials, RegisterCredentials, User } from '../types/auth';
import { loginUser, registerUser, getCurrentUser, refreshToken } from '../services/authService';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
}

const initialState: AuthState = {
  user: null,
  token: null,
  refToken: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>(initialState);
  const router = useRouter();

  useEffect(() => {
    const initAuth = async () => {
      const token = Cookies.get('token'), refToken = Cookies.get('refreshToken');
      if (token) {
        try {
          const user = await getCurrentUser(token);
          setState({
            user,
            token,
            refToken,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          console.log('User authenticated:', user.email);
        } catch (error) {
          console.error('Authentication error:', error);
          Cookies.remove('token');
          setState({
            ...initialState,
            isLoading: false,
          });
        }
      } else {
        console.log('No token found, user not authenticated');
        setState({
          ...initialState,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      console.log('Login attempt with:', credentials.email);
      setState({ ...state, isLoading: true, error: null });
      const response = await loginUser(credentials);
      console.log('Full login response:', response);

      const access_token = response.access_token;
      if (!access_token) {
        throw new Error('No access token received');
      }

      const refresh_token = response.refresh_token;
      // Will be made non-mandatory in the future
      if (!refresh_token) {
        throw new Error('No refresh token received');
      }

      // Set token in cookie
      Cookies.set('token', access_token, { expires: 1 }); // 1 day expiry
      Cookies.set('refreshToken', refresh_token, { expires: 7}); // 7 day lifetime
      console.log('Tokens saved in cookie');

      // Get user data
      const user = await getCurrentUser(access_token);
      console.log('User data retrieved:', user);

      setState({
        user,
        token: access_token,
        refToken: refresh_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      useEffect(() => {
        const interval = setInterval(async () => {
            const token = Cookies.get('token'), refToken = Cookies.get('refreshToken');
            if (token && refToken) {
                const { exp } = JSON.parse(atob(token.split('.')[1]));
                const now = Math.floor(Date.now() / 1000);
                if (exp - now < 300) { // Refresh if less than 5 minutes remaining
                  refreshToken(token, refToken);
                }
            }
        }, 60000); // Check every minute
        return () => clearInterval(interval);
    }, []);

      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error: any) {
      console.error('Login error details:', error);
      let errorMessage = 'Invalid email or password';

      if (error.message) {
        errorMessage = error.message;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      setState({
        ...state,
        isLoading: false,
        error: errorMessage,
      });
      toast.error('Login failed. Please check your credentials.');
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    try {
      setState({ ...state, isLoading: true, error: null });
      await registerUser(credentials);

      setState({
        ...state,
        isLoading: false,
      });

      toast.success('Registration successful! Please login.');
      router.push('/login');
    } catch (error) {
      setState({
        ...state,
        isLoading: false,
        error: 'Registration failed',
      });
      toast.error('Registration failed. Please try again.');
    }
  };

  const logout = () => {
    Cookies.remove('token');
    setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    router.push('/login');
    toast.info('You have been logged out.');
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
