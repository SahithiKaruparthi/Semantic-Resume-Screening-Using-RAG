// src/components/applicant/JobDetails.js

import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import Navbar from './Navbar';

const JobDetails = () => {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        // Fetch job details
        const jobResponse = await axios.get(`/api/jobs/${jobId}`);
        setJob(jobResponse.data);
        
        // Check if user has already applied
        const applicationsResponse = await axios.get('/api/applications');
        setApplications(applicationsResponse.data);
        
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch job details');
        setLoading(false);
      }
    };
    
    fetchJobDetails();
  }, [jobId]);
  
  const hasApplied = applications.some(app => app.job_id === parseInt(jobId));
  
  const formatJobDescription = (description) => {
    return description.split('\n').map((paragraph, index) => (
      <p key={index}>{paragraph}</p>
    ));
  };
  
  return (
    <div className="job-details-page">
      <Navbar />
      <div className="job-details-content">
        {loading ? (
          <div className="loading">Loading job details...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : job ? (
          <div className="job-details">
            <h1>{job.title}</h1>
            <p className="job-date">Posted on: {new Date(job.posting_date).toLocaleDateString()}</p>
            
            <div className="job-description-section">
              <h2>Job Description</h2>
              <div className="job-description-content">
                {formatJobDescription(job.description)}
              </div>
            </div>
            
            <div className="job-actions">
              {hasApplied ? (
                <div className="already-applied">
                  You have already applied for this position.
                  <Link to="/my-applications" className="view-applications">View your applications</Link>
                </div>
              ) : (
                <Link to={`/apply/${jobId}`} className="apply-button">Apply Now</Link>
              )}
              <Link to="/" className="back-button">Back to Jobs</Link>
            </div>
          </div>
        ) : (
          <div className="not-found">Job not found</div>
        )}
      </div>
    </div>
  );
};

export default JobDetails;