'use client';

import React, { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';

interface AuthGuardProps {
  children: React.ReactNode;
}

const publicPaths = ['/', '/login', '/register'];
const protectedPaths = ['/dashboard', '/upload', '/patients', '/profile', '/settings'];
const doctorPaths = ['/doctor', '/doctor/patients', '/doctor/scans'];
const patientPaths = ['/patient', '/patient/scans', '/patient/profile'];

const AuthGuard: React.FC<AuthGuardProps> = ({ children }) => {
  const { isAuthenticated, isLoading, isDoctor, isPatient } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading) {
      // If not authenticated and trying to access a protected route
      if (!isAuthenticated && (
        protectedPaths.some(path => pathname.startsWith(path)) ||
        doctorPaths.some(path => pathname.startsWith(path)) ||
        patientPaths.some(path => pathname.startsWith(path))
      )) {
        router.push('/login');
        return;
      }

      // If authenticated and trying to access login/register
      if (isAuthenticated && ['/login', '/register'].includes(pathname)) {
        router.push('/dashboard');
        return;
      }

      // Role-based access control
      if (isAuthenticated) {
        // Doctor paths are only for doctors
        if (doctorPaths.some(path => pathname.startsWith(path)) && !isDoctor()) {
          router.push('/dashboard');
          return;
        }

        // Patient paths are only for patients
        if (patientPaths.some(path => pathname.startsWith(path)) && !isPatient()) {
          router.push('/dashboard');
          return;
        }
      }
    }
  }, [isAuthenticated, isLoading, pathname, router, isDoctor, isPatient]);

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
