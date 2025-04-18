// src/components/admin/AdminNavbar.js

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext'

const AdminNavbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <nav className="admin-navbar">
      <div className="navbar-brand">
        <Link to="/admin">Admin Portal</Link>
      </div>
      
      <div className="navbar-menu">
        <Link to="/admin" className="navbar-item">Dashboard</Link>
        <Link to="/admin/jobs/new" className="navbar-item">Add Job</Link>
        <Link to="/admin/applications" className="navbar-item">Applications</Link>
      </div>
      
      <div className="navbar-user">
        <span className="user-name">Admin: {user?.username}</span>
        <button onClick={handleLogout} className="logout-button">Logout</button>
      </div>
    </nav>
  );
};

export default AdminNavbar;