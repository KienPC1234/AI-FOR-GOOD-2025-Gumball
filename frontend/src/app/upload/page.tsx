'use client';

import { toast } from 'react-toastify';
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Layout from '../components/layout/Layout';
import { FiUpload, FiFile, FiX, FiLock } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';

const UploadPage: React.FC = () => {
  const router = useRouter();
  const { isAuthenticated, user } = useAuth();
  const [files, setFiles] = useState<File[]>([]);
  const [patientInfo, setPatientInfo] = useState({
    name: '',
    age: '',
    gender: '',
    scanType: 'ct',
    notes: '',
  });
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const fileArray = Array.from(e.target.files);
      const validFiles = fileArray.filter(file => {
          if (file.size > 25 * 1024 * 1024) { // 25 MB limit
              toast.error(`${file.name} exceeds the size limit of 25MB.`);
              return false;
          }
          if (!['image/jpeg', 'image/png', 'application/dicom'].includes(file.type)) {
              toast.error(`${file.name} is not a valid file type.`);
              return false;
          }
          return true;
      });
      setFiles((prevFiles) => [...prevFiles, ...validFiles]);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      const fileArray = Array.from(e.dataTransfer.files);
      setFiles((prevFiles) => [...prevFiles, ...fileArray]);
    }
  };

  const removeFile = (index: number) => {
    setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setPatientInfo((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      // Insert uploading logic here
      // Simulate file upload
      await new Promise((resolve) => setTimeout(resolve, 2000));
      toast.success('Files uploaded successfully!');
      setFiles([]);
      setPatientInfo({
        name: '',
        age: '',
        gender: '',
        scanType: 'ct',
        notes: '',
      });
    } catch (error) {
      toast.error('Failed to upload files. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="py-6">
        <h1 className="text-2xl font-semibold text-gray-900">Upload Medical Scan</h1>
        <p className="mt-1 text-sm text-gray-500">
          Upload CT, MRI, or X-ray images for AI analysis
        </p>
      </div>

      {!isAuthenticated ? (
        <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:p-6 text-center">
            <FiLock className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-lg font-medium text-gray-900">Authentication Required</h3>
            <p className="mt-1 text-sm text-gray-500">
              You need to be logged in to upload and analyze medical scans.
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

      <div className="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
        <form onSubmit={handleSubmit}>
          <div className="px-4 py-5 sm:p-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Patient Name
                </label>
                <input
                  type="text"
                  name="name"
                  id="name"
                  value={patientInfo.name}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label htmlFor="age" className="block text-sm font-medium text-gray-700">
                  Age
                </label>
                <input
                  type="number"
                  name="age"
                  id="age"
                  value={patientInfo.age}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label htmlFor="gender" className="block text-sm font-medium text-gray-700">
                  Gender
                </label>
                <select
                  id="gender"
                  name="gender"
                  value={patientInfo.gender}
                  onChange={handleInputChange}
                  className="mt-1 block w-full bg-white border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  required
                >
                  <option value="">Select gender</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label htmlFor="scanType" className="block text-sm font-medium text-gray-700">
                  Scan Type
                </label>
                <select
                  id="scanType"
                  name="scanType"
                  value={patientInfo.scanType}
                  onChange={handleInputChange}
                  className="mt-1 block w-full bg-white border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  required
                >
                  <option value="ct">CT Scan</option>
                  <option value="mri">MRI</option>
                  <option value="xray">X-Ray</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
                  Clinical Notes (Optional)
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  rows={3}
                  value={patientInfo.notes}
                  onChange={handleInputChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">
                  Upload Scan Images
                </label>
                <div
                  className={`mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed rounded-md ${
                    isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
                  }`}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <div className="space-y-1 text-center">
                    <FiUpload className="mx-auto h-12 w-12 text-gray-400" />
                    <div className="flex text-sm text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-medium text-blue-600 hover:text-blue-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
                      >
                        <span>Upload files</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          multiple
                          accept="image/*,.dicom"
                          onChange={handleFileChange}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-gray-500">
                      PNG, JPG, DICOM up to 50MB
                    </p>
                  </div>
                </div>
              </div>

              {files.length > 0 && (
                <div className="sm:col-span-2">
                  <h3 className="text-sm font-medium text-gray-700">Selected Files</h3>
                  <ul className="mt-2 border border-gray-200 rounded-md divide-y divide-gray-200">
                    {files.map((file, index) => (
                      <li
                        key={index}
                        className="pl-3 pr-4 py-3 flex items-center justify-between text-sm"
                      >
                        <div className="w-0 flex-1 flex items-center">
                          <FiFile className="flex-shrink-0 h-5 w-5 text-gray-400" />
                          <span className="ml-2 flex-1 w-0 truncate">{file.name}</span>
                        </div>
                        <div className="ml-4 flex-shrink-0">
                          <button
                            type="button"
                            onClick={() => removeFile(index)}
                            className="font-medium text-red-600 hover:text-red-500"
                          >
                            <FiX className="h-5 w-5" />
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
          <div className="px-4 py-3 bg-gray-50 text-right sm:px-6">
          <button
            type="submit"
            disabled={files.length === 0 || isLoading}
            className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white"></div>
            ) : (
              'Upload and Analyze'
            )}
          </button>
          </div>
        </form>
      </div>
      )}
    </Layout>
  );
};

export default UploadPage;
