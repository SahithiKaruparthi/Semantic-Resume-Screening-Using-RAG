// src/App.js

import React from 'react';
import {Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Register from './components/Register';
import ApplicantDashboard from './components/Applicant/Dashboard';
import AdminDashboard from './components/Admin/Dashboard';
import JobForm from './components/Admin/JobForm';
import JobDetails from './components/Applicant/JobDetails';
import AdminJobDetails from './components/Admin/JobDetails';
import ApplicationForm from './components/Applicant/ApplicationForm';
import ApplicationsList from './components/Applicant/ApplicationsList';
import AdminApplicationsList from './components/Admin/ApplicationsList';
import { AuthProvider, useAuth } from './components/contexts/AuthContext';
import './App.css';

// Protected route component
const ProtectedRoute = ({ children, requiredRole }) => {
  const { user, isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to={user.role === 'admin' ? '/admin' : '/'} />;
  }
  
  return children;
};

function App() {
  return (
    <AuthProvider>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Applicant Routes */}
            <Route path="/" element={
              <ProtectedRoute requiredRole="applicant">
                <ApplicantDashboard />
              </ProtectedRoute>
            } />
            <Route path="/jobs/:jobId" element={<JobDetails />} />
            <Route path="/apply/:jobId" element={
              <ProtectedRoute requiredRole="applicant">
                <ApplicationForm />
              </ProtectedRoute>
            } />
            <Route path="/my-applications" element={
              <ProtectedRoute requiredRole="applicant">
                <ApplicationsList />
              </ProtectedRoute>
            } />
            
            {/* Admin Routes */}
            <Route path="/admin" element={
              <ProtectedRoute requiredRole="admin">
                <AdminDashboard />
              </ProtectedRoute>
            } />
            <Route path="/admin/jobs/new" element={
              <ProtectedRoute requiredRole="admin">
                <JobForm />
              </ProtectedRoute>
            } />
            <Route path="/admin/jobs/:jobId" element={
              <ProtectedRoute requiredRole="admin">
                <AdminJobDetails />
              </ProtectedRoute>
            } />
            <Route path="/admin/jobs/:jobId/edit" element={
              <ProtectedRoute requiredRole="admin">
                <JobForm />
              </ProtectedRoute>
            } />
            <Route path="/admin/applications" element={
              <ProtectedRoute requiredRole="admin">
                <AdminApplicationsList />
              </ProtectedRoute>
            } />
            
            {/* Default redirect */}
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </div>
    </AuthProvider>
  );
}

export default App;