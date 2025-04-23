'use client';

import React, { useState } from 'react';
import Layout from '../components/layout/Layout';
import { FiSearch, FiPlus, FiUser, FiCalendar, FiFileText } from 'react-icons/fi';
import Link from 'next/link';

// Mock data for patients
const mockPatients = [
  {
    id: 1,
    name: 'Jane Cooper',
    age: 47,
    gender: 'Female',
    lastScan: '2023-04-15',
    scanType: 'CT Scan',
    status: 'Completed',
  },
  {
    id: 2,
    name: 'John Smith',
    age: 35,
    gender: 'Male',
    lastScan: '2023-04-10',
    scanType: 'MRI',
    status: 'Pending',
  },
  {
    id: 3,
    name: 'Robert Johnson',
    age: 62,
    gender: 'Male',
    lastScan: '2023-03-28',
    scanType: 'X-Ray',
    status: 'Completed',
  },
  {
    id: 4,
    name: 'Emily Davis',
    age: 29,
    gender: 'Female',
    lastScan: '2023-04-05',
    scanType: 'CT Scan',
    status: 'Completed',
  },
  {
    id: 5,
    name: 'Michael Wilson',
    age: 54,
    gender: 'Male',
    lastScan: '2023-04-18',
    scanType: 'MRI',
    status: 'In Progress',
  },
];

const PatientsPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [patients] = useState(mockPatients);

  const filteredPatients = patients.filter((patient) =>
    patient.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Layout>
      <div className="py-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Patients</h1>
            <p className="mt-1 text-sm text-gray-500">
              Manage patient records and scan history
            </p>
          </div>
          <Link
            href="/upload"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <FiPlus className="mr-2 -ml-1 h-5 w-5" />
            New Scan
          </Link>
        </div>
      </div>

      <div className="mt-4">
        <div className="relative rounded-md shadow-sm max-w-lg">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <FiSearch className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 rounded-md"
            placeholder="Search patients..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredPatients.length > 0 ? (
            filteredPatients.map((patient) => (
              <li key={patient.id}>
                <Link href={`/patients/${patient.id}`} className="block hover:bg-gray-50">
                  <div className="px-4 py-4 sm:px-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                          <FiUser className="h-6 w-6 text-gray-600" />
                        </div>
                        <div className="ml-4">
                          <p className="text-sm font-medium text-blue-600 truncate">{patient.name}</p>
                          <p className="text-sm text-gray-500">
                            {patient.age} years • {patient.gender}
                          </p>
                        </div>
                      </div>
                      <div className="ml-2 flex-shrink-0 flex">
                        <p
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            patient.status === 'Completed'
                              ? 'bg-green-100 text-green-800'
                              : patient.status === 'In Progress'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {patient.status}
                        </p>
                      </div>
                    </div>
                    <div className="mt-2 sm:flex sm:justify-between">
                      <div className="sm:flex">
                        <p className="flex items-center text-sm text-gray-500">
                          <FiFileText className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                          {patient.scanType}
                        </p>
                      </div>
                      <div className="mt-2 flex items-center text-sm text-gray-500 sm:mt-0">
                        <FiCalendar className="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400" />
                        <p>
                          Last scan on{' '}
                          <time dateTime={patient.lastScan}>
                            {new Date(patient.lastScan).toLocaleDateString()}
                          </time>
                        </p>
                      </div>
                    </div>
                  </div>
                </Link>
              </li>
            ))
          ) : (
            <li className="px-4 py-5 text-center text-gray-500">
              No patients found matching your search.
            </li>
          )}
        </ul>
      </div>
    </Layout>
  );
};

export default PatientsPage;
