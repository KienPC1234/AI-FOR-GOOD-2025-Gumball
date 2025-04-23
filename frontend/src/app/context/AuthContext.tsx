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
  isDoctor: () => boolean;
  isPatient: () => boolean;
  isAdmin: () => boolean;
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

      // Call the login service
      const response = await loginUser(credentials);
      console.log('Full login response:', response);

      // Validate the token
      const access_token = response.access_token;
      if (!access_token) {
        throw new Error('No access token received');
      }

      // Set token in cookie
      Cookies.set('token', access_token, { expires: 1 }); // 1 day expiry
      console.log('Token saved in cookie');

      try {
        // Get user data
        const user = await getCurrentUser(access_token);
        console.log('User data retrieved:', user);

        setState({
          user,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });

        toast.success('Login successful!');
        router.push('/dashboard');
      } catch (userError) {
        console.error('Error getting user data:', userError);
        // Even if we can't get user data, we're still logged in with a token
        setState({
          user: null,
          token: access_token,
          isAuthenticated: true,
          isLoading: false,
          error: null,
        });
        toast.warning('Logged in but could not retrieve user profile');
        router.push('/dashboard');
      }
    } catch (error: any) {
      console.error('Login error details:', error);
      let errorMessage = 'Invalid email or password';

      // More comprehensive error handling
      if (error.message) {
        errorMessage = error.message;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.data) {
        // If response.data exists but not detail
        const dataError = error.response.data;
        if (typeof dataError === 'string') {
          errorMessage = dataError;
        } else if (dataError.message) {
          errorMessage = dataError.message;
        } else if (typeof dataError === 'object') {
          // Try to extract a meaningful message from the object
          const errorValues = Object.values(dataError).filter(v => !!v);
          if (errorValues.length > 0) {
            errorMessage = errorValues.join('. ');
          }
        }
      }

      setState({
        ...state,
        isLoading: false,
        error: errorMessage,
      });
      toast.error('Login failed: ' + errorMessage);
    }
  };

  const register = async (credentials: RegisterCredentials) => {
    try {
      console.log('Starting registration process with:', credentials.email);
      setState({ ...state, isLoading: true, error: null });

      await registerUser(credentials);
      console.log('Registration API call successful');

      setState({
        ...state,
        isLoading: false,
        error: null
      });

      toast.success('Registration successful! Please login.');
      router.push('/login');
    } catch (error: any) {
      console.error('Registration error details:', error);

      let errorMessage = 'Registration failed';

      // More comprehensive error handling
      if (error.message) {
        errorMessage = error.message;
      }

      setState({
        ...state,
        isLoading: false,
        error: errorMessage,
      });

      toast.error(`Registration failed: ${errorMessage}`);
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

  const isDoctor = () => {
    return state.user?.role === 'doctor' || state.user?.is_superuser;
  };

  const isPatient = () => {
    return state.user?.role === 'patient' || state.user?.is_superuser;
  };

  const isAdmin = () => {
    return state.user?.is_superuser || state.user?.role === 'admin';
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        register,
        logout,
        isDoctor,
        isPatient,
        isAdmin,
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
