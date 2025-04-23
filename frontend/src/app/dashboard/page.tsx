'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { FiUpload, FiList, FiUser, FiActivity, FiLock } from 'react-icons/fi';
import Link from 'next/link';

const DashboardPage: React.FC = () => {
  const router = useRouter();
  const { user, isAuthenticated } = useAuth();

  const cards = [
    {
      title: 'Upload Medical Scan',
      description: 'Upload CT, MRI, or X-ray images for AI analysis',
      icon: FiUpload,
      href: '/upload',
      color: 'bg-blue-500',
    },
    {
      title: 'Patient Records',
      description: 'View and manage patient records and scan history',
      icon: FiList,
      href: '/patients',
      color: 'bg-green-500',
    },
    {
      title: 'Your Profile',
      description: 'Manage your account settings and preferences',
      icon: FiUser,
      href: '/profile',
      color: 'bg-purple-500',
    },
    {
      title: 'Recent Activity',
      description: 'View your recent scans and analysis results',
      icon: FiActivity,
      href: '/activity',
      color: 'bg-orange-500',
    },
  ];

  return (
    <Layout>
      <div className="py-6">
        <h1 className="text-2xl font-semibold text-gray-900">Dashboard</h1>
        {isAuthenticated ? (
          <p className="mt-1 text-sm text-gray-500">
            Welcome back, {user?.email}
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
            <FiLock className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">Authentication Required</h3>
            <p className="mt-1 text-sm text-gray-500">
              You need to be logged in to view your dashboard and access medical scan features.
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
      ) : (

      <div className="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
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
        <div className="px-4 py-5 sm:px-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Recent Scans
          </h3>
          <p className="mt-1 max-w-2xl text-sm text-gray-500">
            Your most recent medical scan analyses
          </p>
        </div>
        <div className="border-t border-gray-200">
          <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
            No recent scans found. Upload a new scan to get started.
          </div>
        </div>
      </div>
      )}
    </Layout>
  );
};

export default DashboardPage;
