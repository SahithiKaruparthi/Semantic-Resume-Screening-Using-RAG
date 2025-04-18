// src/components/applicant/Navbar.js

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">Job Portal</Link>
      </div>
      
      <div className="navbar-menu">
        <Link to="/" className="navbar-item">Jobs</Link>
        <Link to="/my-applications" className="navbar-item">My Applications</Link>
      </div>
      
      <div className="navbar-user">
        <span className="user-name">Welcome, {user?.username}</span>
        <button onClick={handleLogout} className="logout-button">Logout</button>
      </div>
    </nav>
  );
};

export default Navbar;
