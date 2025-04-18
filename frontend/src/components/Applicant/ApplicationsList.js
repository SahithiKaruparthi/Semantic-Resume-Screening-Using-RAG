// src/components/applicant/ApplicationsList.js

import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import axios from 'axios';
import Navbar from './Navbar';

const ApplicationsList = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const location = useLocation();
  const successMessage = location.state?.success && (
    <div className="success-message">
      Application submitted successfully! Your match score: {location.state.matchScore}%
      {location.state.status === 'shortlisted' && (
        <div className="shortlisted-message">
          Congratulations! You've been shortlisted for an interview. Check your email for details.
        </div>
      )}
    </div>
  );
  
  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const response = await axios.get('/api/applications');
        setApplications(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch your applications');
        setLoading(false);
      }
    };
    
    fetchApplications();
  }, []);
  
  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'shortlisted':
        return 'status-badge shortlisted';
      case 'rejected':
        return 'status-badge rejected';
      case 'interviewed':
        return 'status-badge interviewed';
      default:
        return 'status-badge pending';
    }
  };
  
  return (
    <div className="applications-list-page">
      <Navbar />
      <div className="applications-list-content">
        <h1>My Applications</h1>
        
        {successMessage}
        
        {loading ? (
          <div className="loading">Loading your applications...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : applications.length === 0 ? (
          <div className="no-applications">
            You haven't applied for any jobs yet.
          </div>
        ) : (
          <div className="applications-list">
            {applications.map((app) => (
              <div className="application-card" key={app.id}>
                <div className="application-header">
                  <h2>{app.job_title}</h2>
                  <span className={getStatusBadgeClass(app.status)}>
                    {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                  </span>
                </div>
                
                <div className="application-details">
                  <p>Applied on: {new Date(app.application_date).toLocaleDateString()}</p>
                  <p>Match Score: <span className="match-score">{app.match_score}%</span></p>
                </div>
                
                {app.status === 'shortlisted' && (
                  <div className="interview-info">
                    <p className="interview-notice">
                      You've been shortlisted! Check your email for interview details.
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApplicationsList;