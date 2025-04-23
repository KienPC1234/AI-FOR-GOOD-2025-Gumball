'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '../components/layout/Layout';
import { useAuth } from '../context/AuthContext';
import { FiUsers, FiFileText, FiActivity, FiAlertCircle } from 'react-icons/fi';
import Link from 'next/link';
import axios from 'axios';
import { User } from '../types/auth';

const DoctorDashboard: React.FC = () => {
  const { user, isAuthenticated, isDoctor } = useAuth();
  const router = useRouter();
  const [patients, setPatients] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get('/api/patients', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        setPatients(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching patients:', err);
        setError('Failed to load patients');
      } finally {
        setIsLoading(false);
      }
    };

    if (isAuthenticated && isDoctor()) {
      fetchPatients();
    }
  }, [isAuthenticated, isDoctor]);

  const cards = [
    {
      title: 'Manage Patients',
      description: 'View and manage your patients',
      icon: FiUsers,
      href: '/doctor/patients',
      color: 'bg-blue-500',
    },
    {
      title: 'Review Scans',
      description: 'Review and analyze patient scans',
      icon: FiFileText,
      href: '/doctor/scans',
      color: 'bg-green-500',
    },
    {
      title: 'Recent Activity',
      description: 'View your recent activity',
      icon: FiActivity,
      href: '/doctor/activity',
      color: 'bg-purple-500',
    },
  ];

  return (
    <Layout>
      <div className="py-6">
        <h1 className="text-2xl font-semibold text-gray-900">Doctor Dashboard</h1>
        {isAuthenticated ? (
          <p className="mt-1 text-sm text-gray-500">
            Welcome back, Dr. {user?.full_name || user?.email}
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
              You need to be logged in to view your doctor dashboard.
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
      ) : !isDoctor() ? (
        <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6 text-center">
            <FiAlertCircle className="mx-auto h-12 w-12 text-red-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">Access Denied</h3>
            <p className="mt-1 text-sm text-gray-500">
              You don't have permission to access the doctor dashboard.
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
                  Recent Patients
                </h3>
                <p className="mt-1 max-w-2xl text-sm text-gray-500">
                  Your most recent patients
                </p>
              </div>
              <Link
                href="/doctor/patients"
                className="text-sm font-medium text-blue-600 hover:text-blue-500"
              >
                View all
              </Link>
            </div>
            <div className="border-t border-gray-200">
              {isLoading ? (
                <div className="px-4 py-5 sm:p-6 text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
                  <p className="mt-2 text-sm text-gray-500">Loading patients...</p>
                </div>
              ) : error ? (
                <div className="px-4 py-5 sm:p-6 text-center text-red-500">
                  {error}
                </div>
              ) : patients.length === 0 ? (
                <div className="px-4 py-5 sm:p-6 text-center text-gray-500">
                  No patients found.
                </div>
              ) : (
                <ul className="divide-y divide-gray-200">
                  {patients.slice(0, 5).map((patient) => (
                    <li key={patient.id} className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                      <div className="flex items-center">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-blue-600 truncate">
                            {patient.full_name || patient.email}
                          </p>
                          <p className="text-sm text-gray-500">
                            {patient.email}
                          </p>
                        </div>
                        <div>
                          <Link
                            href={`/doctor/patients/${patient.id}`}
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

export default DoctorDashboard;
