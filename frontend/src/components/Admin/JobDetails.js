import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import AdminNavbar from './AdminNavbar';

const JobDetails = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchJobDetails = async () => {
      try {
        const token = localStorage.getItem('token');
        const headers = { 'Authorization': `Bearer ${token}` };
        
        const [jobResponse, applicationsResponse] = await Promise.all([
          axios.get(`/api/jobs/${jobId}`, { headers }),
          axios.get(`/api/jobs/${jobId}/applications`, { headers })
        ]);
        
        setJob(jobResponse.data);
        setApplications(applicationsResponse.data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching job details:', err);
        setError(err.response?.data?.message || 'Failed to fetch job details');
        setLoading(false);
      }
    };
    
    fetchJobDetails();
  }, [jobId]);
  
  const formatJobDescription = (description) => {
    return description.split('\n').map((paragraph, index) => (
      <p key={index}>{paragraph}</p>
    ));
  };
  
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
      const token = localStorage.getItem('token');
      await axios.put(`/api/admin/applications/${applicationId}/status`, 
        { status: newStatus },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      // Update local state
      setApplications(applications.map(app => 
        app.id === applicationId ? { ...app, status: newStatus } : app
      ));
    } catch (err) {
      console.error('Error updating status:', err);
      alert(err.response?.data?.message || 'Failed to update application status');
    }
  };
  
  const handleViewResume = (resumePath) => {
    if (!resumePath) {
      alert('Resume not available');
      return;
    }
    try {
      const token = localStorage.getItem('token');
      // Extract just the filename from the path
      const filename = resumePath.split('/').pop();
      window.open(`/api/resumes/${filename}?token=${token}`, '_blank');
    } catch (err) {
      console.error('Error viewing resume:', err);
      alert('Error viewing resume. Please try again.');
    }
  };
  
  const formatMatchScore = (score) => {
    try {
      const numScore = parseFloat(score);
      if (isNaN(numScore)) return '0%';
      return `${Math.round(numScore)}%`;
    } catch (err) {
      console.error('Error formatting match score:', err);
      return '0%';
    }
  };
  
  const formatDate = (date) => {
    const formattedDate = new Date(date).toLocaleDateString();
    return formattedDate.split(',').join(' at ');
  };
  
  return (
    <div className="job-details-page">
      <AdminNavbar />
      <div className="job-details-content">
        {loading ? (
          <div className="loading">Loading job details...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : job ? (
          <>
            <div className="job-details">
              <div className="job-header">
                <h1>{job.title}</h1>
                <div className="job-actions">
                  <Link to={`/admin/jobs/${jobId}/edit`} className="edit-button">Edit Job</Link>
                  <Link to="/admin" className="back-button">Back to Dashboard</Link>
                </div>
              </div>
              
              <div className="job-description-section">
                <h2>Job Description</h2>
                <div className="job-description-content">
                  {formatJobDescription(job.description)}
                </div>
              </div>
            </div>
            
            <div className="applications-section">
              <h2>Applications ({applications.length})</h2>
              
              {applications.length === 0 ? (
                <div className="no-applications">No applications received yet.</div>
              ) : (
                <div className="applications-list">
                  {applications.map((app) => (
                    <div className="admin-application-card" key={app.id}>
                      <div className="application-header">
                        <h3>Application from {app.username}</h3>
                        <span className={getStatusBadgeClass(app.status)}>
                          {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                        </span>
                      </div>
                      
                      <div className="application-details">
                        <div className="candidate-info">
                          <p><strong>Email:</strong> {app.email}</p>
                          <p><strong>Applied on:</strong> {formatDate(app.application_date)}</p>
                          <p><strong>Match Score:</strong> <span className="match-score">{formatMatchScore(app.match_score)}</span></p>
                        </div>
                      </div>
                      
                      <div className="application-actions">
                        <button 
                          onClick={() => handleViewResume(app.resume_path)}
                          className="view-resume-button"
                          disabled={!app.resume_path}
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
          </>
        ) : (
          <div className="not-found">Job not found</div>
        )}
      </div>
    </div>
  );
};

export default JobDetails; 