-- schema.sql
-- Database schema for intelligent resume screening system

-- Users table with RBAC
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT CHECK(role IN ('admin', 'applicant')) NOT NULL
);

-- Jobs table 
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  summarized_data TEXT,  -- Stores LLM-processed JD data as JSON
  posting_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status TEXT CHECK(status IN ('open', 'closed')) DEFAULT 'open'
);

-- Resumes table
CREATE TABLE IF NOT EXISTS resumes (
  id INTEGER PRIMARY KEY,
  applicant_id INTEGER NOT NULL,
  file_path TEXT NOT NULL,
  parsed_data TEXT,  -- Stores LLM-parsed resume data as JSON
  upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (applicant_id) REFERENCES users(id)
);

-- Applications
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY,
  applicant_id INTEGER NOT NULL,
  job_id INTEGER NOT NULL,
  resume_id INTEGER NOT NULL,
  application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status TEXT CHECK(status IN ('pending', 'shortlisted', 'rejected', 'interviewed')) DEFAULT 'pending',
  match_score FLOAT,
  FOREIGN KEY (applicant_id) REFERENCES users(id),
  FOREIGN KEY (job_id) REFERENCES jobs(id),
  FOREIGN KEY (resume_id) REFERENCES resumes(id),
  UNIQUE(applicant_id, job_id) -- Prevents duplicate applications
);

-- Interview scheduling
CREATE TABLE IF NOT EXISTS interviews (
  id INTEGER PRIMARY KEY,
  application_id INTEGER NOT NULL,
  scheduled_date TIMESTAMP,
  status TEXT CHECK(status IN ('scheduled', 'completed', 'cancelled')) DEFAULT 'scheduled',
  notes TEXT,
  FOREIGN KEY (application_id) REFERENCES applications(id)
);