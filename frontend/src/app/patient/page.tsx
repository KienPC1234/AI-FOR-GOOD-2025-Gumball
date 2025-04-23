'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { FiUpload, FiFileText, FiUser, FiAlertCircle } from 'react-icons/fi';
import Link from 'next/link';

const PatientDashboard: React.FC = () => {
  const { user, isAuthenticated, isPatient } = useAuth();
  const router = useRouter();
  const [scans, setScans] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const cards = [
    {
      title: 'Upload New Scan',
      description: 'Upload a new medical scan for analysis',
      icon: FiUpload,
      href: '/patient/upload',
      color: 'bg-blue-500',
    },
    {
      title: 'My Scans',
      description: 'View your scan history and results',
      icon: FiFileText,
      href: '/patient/scans',
      color: 'bg-green-500',
    },
    {
      title: 'My Profile',
      description: 'Update your personal information',
      icon: FiUser,
      href: '/patient/profile',
      color: 'bg-purple-500',
    },
  ];

  return (
    <Layout>
      <div className="py-6">
        <h1 className="text-2xl font-semibold text-gray-900">Patient Dashboard</h1>
        {isAuthenticated ? (
          <p className="mt-1 text-sm text-gray-500">
            Welcome back, {user?.full_name || user?.email}
          </p>
        ) : (
          <p className="mt-1 text-sm text-gray-500">
            Please log in to access your dashboard
          </p>
        )}
      </div>
      
      {!isAuthenticated ? (
        <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6 text-center">
            <FiAlertCircle className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">Authentication Required</h3>
            <p className="mt-1 text-sm text-gray-500">
              You need to be logged in to view your patient dashboard.
            </p>
            <div className="mt-6">
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Go to Login
              </button>
            </div>
          </div>
        </div>
      ) : !isPatient() ? (
        <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6 text-center">
            <FiAlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              You don't have permission to access the patient dashboard.
            </p>
            <div className="mt-6">
              <button
                type="button"
                onClick={() => router.push('/dashboard')}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {cards.map((card) => (
              <Link
                key={card.title}
                href={card.href}
                className="block hover:shadow-lg transition-shadow duration-300"
              >
                <div className="bg-white overflow-hidden shadow rounded-lg">
                  <div className={`p-5 ${card.color} bg-opacity-10`}>
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 rounded-md p-3 ${card.color} text-white`}>
                        <card.icon className="h-6 w-6" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">
                            {card.title}
                          </dt>
                          <dd>
                            <div className="text-lg font-medium text-gray-900">
                              {card.description}
                            </div>
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          <div className="mt-8 bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Recent Scans
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Your most recent medical scans
                </p>
              </div>
              <Link
                href="/patient/scans"
                className="text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                View all
              </Link>
            </div>
            <div className="border-t border-gray-200">
              {isLoading ? (
                <div className="px-4 py-5 sm:p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-500">Loading scans...</p>
                </div>
              ) : scans.length === 0 ? (
                <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
                  No scans found. Upload a new scan to get started.
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {scans.map((scan: any) => (
                    <li key={scan.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                      <div className="flex items-center">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-blue-600 truncate">
                            {scan.name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(scan.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div>
                          <Link
                            href={`/patient/scans/${scan.id}`}
                            className="inline-flex items-center px-3 py-1 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                          >
                            View
                          </Link>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </>
      )}
    </Layout>
  );
};

export default PatientDashboard;
