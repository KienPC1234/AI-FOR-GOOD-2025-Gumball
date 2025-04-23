'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';
import { toast } from 'react-toastify';
import { AuthState, LoginCredentials, RegisterCredentials, User } from '../types/auth';
import { loginUser, registerUser, getCurrentUser } from '../services/authService';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (credentials: RegisterCredentials) => Promise<void>;
  logout: () => void;
}

const initialState: AuthState = {
  user: null,
  token: null,
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
      const token = Cookies.get('token');
      if (token) {
        try {
          const user = await getCurrentUser(token);
          setState({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          Cookies.remove('token');
          setState({
            ...initialState,
            isLoading: false,
          });
        }
      } else {
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
      setState({ ...state, isLoading: true, error: null });
      const { access_token } = await loginUser(credentials);
      
      // Set token in cookie
      Cookies.set('token', access_token, { expires: 1 }); // 1 day expiry
      
      // Get user data
      const user = await getCurrentUser(access_token);
      
      setState({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      toast.success('Login successful!');
      router.push('/dashboard');
    } catch (error) {
      setState({
        ...state,
        isLoading: false,
        error: 'Invalid email or password',
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
