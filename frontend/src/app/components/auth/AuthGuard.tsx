'use client';

import React, { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';

interface AuthGuardProps {
  children: React.ReactNode;
}

const publicPaths = ['/', '/login', '/register'];
const protectedPaths = ['/dashboard', '/upload', '/patients', '/profile', '/settings'];

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading) {
      // If not authenticated and trying to access a protected route
      if (!isAuthenticated && protectedPaths.some(path => pathname.startsWith(path))) {
        router.push('/login');
      }

      // If authenticated and trying to access login/register
      if (isAuthenticated && ['/login', '/register'].includes(pathname)) {
        router.push('/dashboard');
      }
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // For public routes or authenticated users on the correct routes
  return <>{children}</>;
};

export default AuthGuard;
