// src/components/admin/JobForm.js

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import AdminNavbar from './AdminNavbar';

const JobForm = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const isEditMode = !!jobId;
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(isEditMode);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  useEffect(() => {
    if (isEditMode) {
      const fetchJobDetails = async () => {
        try {
          const response = await axios.get(`/api/jobs/${jobId}`);
          const { title, description } = response.data;
          
          setTitle(title);
          setDescription(description);
          setLoading(false);
        } catch (err) {
          setError('Failed to fetch job details');
          setLoading(false);
        }
      };
      
      fetchJobDetails();
    }
  }, [jobId, isEditMode]);
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    
    try {
      if (isEditMode) {
        await axios.put(`/api/jobs/${jobId}`, { title, description });
      } else {
        await axios.post('/api/jobs', { title, description });
      }
      
      navigate('/admin');
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to save job');
      setSubmitting(false);
    }
  };
  
  return (
    <div className="job-form-page">
      <AdminNavbar />
      <div className="job-form-content">
        <h1>{isEditMode ? 'Edit Job Listing' : 'Create New Job Listing'}</h1>
        
        {loading ? (
          <div className="loading">Loading job details...</div>
        ) : (
          <form onSubmit={handleSubmit} className="job-form">
            {error && <div className="error-message">{error}</div>}
            
            <div className="form-group">
              <label>Job Title</label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>
            
            <div className="form-group">
              <label>Job Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                rows="10"
                placeholder="Enter detailed job description, requirements, and qualifications..."
              ></textarea>
            </div>
            
            <div className="form-actions">
              <button type="button" onClick={() => navigate('/admin')} className="cancel-button">
                Cancel
              </button>
              <button type="submit" className="submit-button" disabled={submitting}>
                {submitting ? 'Saving...' : isEditMode ? 'Update Job' : 'Create Job'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default JobForm;