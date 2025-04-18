// src/components/applicant/ApplicationForm.js

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Navbar from './Navbar';

const ApplicationForm = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  
  const [job, setJob] = useState(null);
  const [resumes, setResumes] = useState([]);
  const [selectedResume, setSelectedResume] = useState('');
  const [newResume, setNewResume] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jobResponse, resumesResponse] = await Promise.all([
          axios.get(`/api/jobs/${jobId}`),
          axios.get('/api/resumes')
        ]);
        
        setJob(jobResponse.data);
        setResumes(resumesResponse.data);
        
        if (resumesResponse.data.length > 0) {
          setSelectedResume(resumesResponse.data[0].id);
        }
        
        setLoading(false);
      } catch (err) {
        setError('Failed to load required data');
        setLoading(false);
      }
    };
    
    fetchData();
  }, [jobId]);
  
  const handleResumeChange = (e) => {
    setSelectedResume(e.target.value);
  };
  
  const handleFileChange = (e) => {
    setNewResume(e.target.files[0]);
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    
    try {
      let resumeId = selectedResume;
      
      // If new resume is uploaded, submit it first
      if (newResume) {
        const formData = new FormData();
        formData.append('resume', newResume);
        
        const resumeResponse = await axios.post('/api/resumes', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        resumeId = resumeResponse.data.resume_id;
      }
      
      // Submit application
      const applicationResponse = await axios.post('/api/applications', {
        job_id: jobId,
        resume_id: resumeId
      });
      
      // Redirect to application status page
      navigate('/my-applications', { 
        state: { 
          success: true,
          matchScore: applicationResponse.data.match_score,
          status: applicationResponse.data.status
        } 
      });
    } catch (err) {
      setError(err.response?.data?.message || 'Failed to submit application. Please try again.');
      setSubmitting(false);
    }
  };
  
  return (
    <div className="application-form-page">
      <Navbar />
      <div className="application-form-content">
        {loading ? (
          <div className="loading">Loading application form...</div>
        ) : error ? (
          <div className="error-message">{error}</div>
        ) : job ? (
          <>
            <h1>Apply for {job.title}</h1>
            
            <form onSubmit={handleSubmit} className="application-form">
              <div className="form-section">
                <h2>Resume Selection</h2>
                
                {resumes.length > 0 ? (
                  <div className="form-group">
                    <label>Select from your uploaded resumes:</label>
                    <select value={selectedResume} onChange={handleResumeChange}>
                      {resumes.map(resume => (
                        <option key={resume.id} value={resume.id}>
                          Uploaded on {new Date(resume.upload_date).toLocaleDateString()}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <p className="no-resumes">You don't have any resumes uploaded yet.</p>
                )}
                
                <div className="form-group">
                  <label>Or upload a new resume (PDF only):</label>
                  <input 
                    type="file" 
                    accept=".pdf" 
                    onChange={handleFileChange}
                    required={resumes.length === 0}
                  />
                </div>
              </div>
              
              <div className="form-actions">
                <button type="submit" className="submit-button" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Application'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="not-found">Job not found</div>
        )}
      </div>
    </div>
  );
};

export default ApplicationForm;