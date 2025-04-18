// src/components/applicant/Dashboard.js

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import Navbar from './Navbar';

const Dashboard = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const response = await axios.get('/api/jobs');
        setJobs(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch job listings');
        setLoading(false);
      }
    };
    
    fetchJobs();
  }, []);
  
  return (
    <div className="dashboard">
      <Navbar />
      <div className="dashboard-content">
        <h1>Available Job Openings</h1>
        
        {loading ? (
          <div className="loading">Loading job listings...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : jobs.length === 0 ? (
          <div className="no-jobs">No job openings available at the moment.</div>
        ) : (
          <div className="job-list">
            {jobs.map((job) => (
              <div className="job-card" key={job.id}>
                <h2>{job.title}</h2>
                <p className="job-date">Posted on: {new Date(job.posting_date).toLocaleDateString()}</p>
                <p className="job-description">{job.description.substring(0, 150)}...</p>
                <div className="job-actions">
                  <Link to={`/jobs/${job.id}`} className="view-button">View Details</Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;