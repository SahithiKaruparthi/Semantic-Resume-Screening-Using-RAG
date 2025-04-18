// src/components/admin/ApplicationsList.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import AdminNavbar from './AdminNavbar';

const AdminApplicationsList = () => {
  const [applications, setApplications] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchApplications = async () => {
      try {
        const response = await axios.get('/api/admin/applications');
        setApplications(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch applications');
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
  
  const handleStatusChange = async (applicationId, newStatus) => {
    try {
      await axios.put(`/api/admin/applications/${applicationId}/status`, {
        status: newStatus
      });
      
      // Update local state
      setApplications(applications.map(app => 
        app.id === applicationId ? { ...app, status: newStatus } : app
      ));
    } catch (err) {
      alert('Failed to update application status');
    }
  };
  
  const handleViewResume = (resumeId) => {
    window.open(`/api/resumes/${resumeId}`, '_blank');
  };
  
  const filteredApplications = filter === 'all' 
    ? applications 
    : applications.filter(app => app.status === filter);
  
  return (
    <div className="admin-applications-page">
      <AdminNavbar />
      <div className="admin-applications-content">
        <h1>Applications Management</h1>
        
        <div className="filter-controls">
          <label>Filter by status:</label>
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="all">All Applications</option>
            <option value="pending">Pending</option>
            <option value="shortlisted">Shortlisted</option>
            <option value="interviewed">Interviewed</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        
        {loading ? (
          <div className="loading">Loading applications...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : filteredApplications.length === 0 ? (
          <div className="no-applications">
            No applications found matching the current filter.
          </div>
        ) : (
          <div className="admin-applications-list">
            {filteredApplications.map((app) => (
              <div className="admin-application-card" key={app.id}>
                <div className="application-header">
                  <h2>Application for {app.job_title}</h2>
                  <span className={getStatusBadgeClass(app.status)}>
                    {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                  </span>
                </div>
                
                <div className="application-details">
                  <div className="candidate-info">
                    <p><strong>Candidate:</strong> {app.applicant_name}</p>
                    <p><strong>Email:</strong> {app.applicant_email}</p>
                    <p><strong>Applied on:</strong> {new Date(app.application_date).toLocaleDateString()}</p>
                  </div>
                  
                  <div className="application-score">
                    <p><strong>Match Score:</strong> <span className="match-score">{app.match_score}%</span></p>
                  </div>
                </div>
                
                <div className="application-actions">
                  <button 
                    onClick={() => handleViewResume(app.resume_id)}
                    className="view-resume-button"
                  >
                    View Resume
                  </button>
                  
                  <div className="status-actions">
                    <select 
                      value={app.status}
                      onChange={(e) => handleStatusChange(app.id, e.target.value)}
                    >
                      <option value="pending">Pending</option>
                      <option value="shortlisted">Shortlist</option>
                      <option value="interviewed">Interviewed</option>
                      <option value="rejected">Reject</option>
                    </select>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminApplicationsList;