// src/components/admin/Dashboard.js

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import AdminNavbar from './AdminNavbar';

const AdminDashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [stats, setStats] = useState({
    totalJobs: 0,
    totalApplications: 0,
    shortlistedCandidates: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [jobsResponse, statsResponse] = await Promise.all([
          axios.get('/api/jobs'),
          axios.get('/api/admin/stats')
        ]);
        
        setJobs(jobsResponse.data);
        setStats(statsResponse.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch dashboard data');
        setLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);
  
  return (
    <div className="admin-dashboard">
      <AdminNavbar />
      <div className="admin-dashboard-content">
        <div className="dashboard-header">
          <h1>Admin Dashboard</h1>
          <Link to="/admin/jobs/new" className="add-job-button">Add New Job</Link>
        </div>
        
        {loading ? (
          <div className="loading">Loading dashboard data...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : (
          <>
            <div className="stats-cards">
              <div className="stat-card">
                <h3>Total Jobs</h3>
                <p className="stat-value">{stats.totalJobs}</p>
              </div>
              <div className="stat-card">
                <h3>Applications</h3>
                <p className="stat-value">{stats.totalApplications}</p>
              </div>
              <div className="stat-card">
                <h3>Shortlisted</h3>
                <p className="stat-value">{stats.shortlistedCandidates}</p>
              </div>
            </div>
            
            <div className="jobs-section">
              <h2>Active Job Listings</h2>
              
              {jobs.length === 0 ? (
                <div className="no-jobs">No job listings found. Create your first job posting!</div>
              ) : (
                <div className="admin-job-list">
                  {jobs.map((job) => (
                    <div className="admin-job-card" key={job.id}>
                      <div className="job-info">
                        <h3>{job.title}</h3>
                        <p>Posted: {new Date(job.posting_date).toLocaleDateString()}</p>
                        <p>Applications: {job.application_count || 0}</p>
                      </div>
                      <div className="job-actions">
                        <Link to={`/admin/jobs/${job.id}`} className="view-button">View Details</Link>
                        <Link to={`/admin/jobs/${job.id}/edit`} className="edit-button">Edit</Link>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AdminDashboard;
