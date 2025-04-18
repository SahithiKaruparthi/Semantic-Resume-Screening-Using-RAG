# File: app.py (Flask Backend)
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import os
import json
import hashlib
import uuid
from datetime import datetime
import jwt
from werkzeug.utils import secure_filename
from functools import wraps
import truststore

truststore.inject_into_ssl()

# Import agents
from agents.jd_summarizer import summarize_jd
from agents.resume_parser import parse_resume
from agents.shortlister import evaluate_match
from agents.scheduler import send_invite
from agents.mas_controller import run_pipeline

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['DATABASE'] = 'db/resume_screening.db'

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'] + 'resumes/', exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'] + 'jds/', exist_ok=True)
os.makedirs('db/', exist_ok=True)

# Database connection helper
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Initialize database
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# JWT token verification
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = query_db('SELECT * FROM users WHERE id = ?', 
                                   [data['user_id']], one=True)
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# Admin role verification
def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user['role'] != 'admin':
            return jsonify({'message': 'Admin privileges required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# Database query helper
def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (dict(rv[0]) if rv else None) if one else [dict(r) for r in rv]

# User authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Check if user already exists
    if query_db('SELECT * FROM users WHERE username = ? OR email = ?', 
               [data['username'], data['email']], one=True):
        return jsonify({'message': 'User already exists!'}), 409
    
    # Hash password
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    
    # Insert new user
    db = get_db()
    db.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)', 
              [data['username'], data['email'], password_hash, 'applicant'])
    db.commit()
    
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # Check if user exists
    password_hash = hashlib.sha256(data['password'].encode()).hexdigest()
    user = query_db('SELECT * FROM users WHERE username = ? AND password_hash = ?', 
                   [data['username'], password_hash], one=True)
    
    if not user:
        return jsonify({'message': 'Invalid credentials!'}), 401
    
    # Generate JWT token
    token = jwt.encode({
        'user_id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'token': token,
        'user_id': user['id'],
        'username': user['username'],
        'role': user['role']
    })

# Job posting routes
@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = query_db('SELECT * FROM jobs WHERE status = "open" ORDER BY posting_date DESC')
    return jsonify(jobs)

@app.route('/api/jobs', methods=['POST'])
@token_required
@admin_required
def add_job(current_user):
    data = request.get_json()
    
    # Insert new job
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO jobs (title, description) VALUES (?, ?)', 
                  [data['title'], data['description']])
    job_id = cursor.lastrowid
    db.commit()
    
    # Process job description with RAG
    job_data = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
    summarized_jd = summarize_jd(job_data['description'])
    
    # Store the summarized JD (optional - could also store in vector DB)
    db.execute('UPDATE jobs SET summarized_data = ? WHERE id = ?', 
              [json.dumps(summarized_jd), job_id])
    db.commit()
    
    return jsonify({'message': 'Job added successfully!', 'job_id': job_id}), 201

# Resume and application routes
@app.route('/api/resumes', methods=['POST'])
@token_required
def upload_resume(current_user):
    # Check if resume file is included
    if 'resume' not in request.files:
        return jsonify({'message': 'No resume file!'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'message': 'No selected file!'}), 400
    
    # Save resume file
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', filename)
    file.save(filepath)
    
    # Parse resume with LLM
    parsed_data = parse_resume(filepath)
    
    # Save resume to database
    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO resumes (applicant_id, file_path, parsed_data) VALUES (?, ?, ?)', 
                  [current_user['id'], filepath, json.dumps(parsed_data)])
    resume_id = cursor.lastrowid
    db.commit()
    
    return jsonify({
        'message': 'Resume uploaded successfully!',
        'resume_id': resume_id
    }), 201

@app.route('/api/applications', methods=['POST'])
@token_required
def apply_for_job(current_user):
    data = request.get_json()
    job_id = data['job_id']
    resume_id = data['resume_id']
    
    # Check if already applied
    if query_db('SELECT * FROM applications WHERE applicant_id = ? AND job_id = ?', 
               [current_user['id'], job_id], one=True):
        return jsonify({'message': 'Already applied for this job!'}), 409
    
    # Get job and resume data
    job = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
    resume = query_db('SELECT * FROM resumes WHERE id = ?', [resume_id], one=True)
    
    if not job or not resume:
        return jsonify({'message': 'Invalid job or resume ID!'}), 400
    
    if resume['applicant_id'] != current_user['id']:
        return jsonify({'message': 'Cannot use someone else\'s resume!'}), 403
    
    # Evaluate match score
    parsed_resume = json.loads(resume['parsed_data'])
    summarized_jd = json.loads(job['summarized_data']) if job.get('summarized_data') else summarize_jd(job['description'])
    match_score = evaluate_match(parsed_resume, summarized_jd)
    
    # Save application
    db = get_db()
    db.execute('INSERT INTO applications (applicant_id, job_id, resume_id, match_score) VALUES (?, ?, ?, ?)', 
              [current_user['id'], job_id, resume_id, match_score])
    db.commit()
    
    # Run full pipeline (could also be done asynchronously)
    application = query_db('SELECT * FROM applications WHERE applicant_id = ? AND job_id = ?', 
                         [current_user['id'], job_id], one=True)
    
    # If match score is above threshold, shortlist
    if match_score >= 80:
        db.execute('UPDATE applications SET status = "shortlisted" WHERE id = ?', [application['id']])
        db.commit()
        
        # Schedule interview (async in production)
        send_invite(current_user['email'], job['title'])
    
    return jsonify({
        'message': 'Application submitted successfully!',
        'match_score': match_score,
        'status': 'shortlisted' if match_score >= 80 else 'pending'
    })

@app.route('/api/applications', methods=['GET'])
@token_required
def get_my_applications(current_user):
    applications = query_db('''
        SELECT a.*, j.title as job_title, j.description as job_description 
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.applicant_id = ?
        ORDER BY a.application_date DESC
    ''', [current_user['id']])
    
    return jsonify(applications)

# Admin routes
@app.route('/api/admin/applications', methods=['GET'])
@token_required
@admin_required
def get_all_applications(current_user):
    applications = query_db('''
        SELECT a.*, u.username, u.email, j.title as job_title
        FROM applications a
        JOIN users u ON a.applicant_id = u.id
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.match_score DESC, a.application_date DESC
    ''')
    
    return jsonify(applications)

@app.route('/api/admin/applications/<int:application_id>/status', methods=['PUT'])
@token_required
@admin_required
def update_application_status(current_user, application_id):
    data = request.get_json()
    new_status = data['status']
    
    if new_status not in ['pending', 'shortlisted', 'rejected', 'interviewed']:
        return jsonify({'message': 'Invalid status!'}), 400
    
    db = get_db()
    db.execute('UPDATE applications SET status = ? WHERE id = ?', [new_status, application_id])
    db.commit()
    
    # If shortlisted, schedule interview
    if new_status == 'shortlisted':
        application = query_db('SELECT a.*, u.email, j.title FROM applications a JOIN users u ON a.applicant_id = u.id JOIN jobs j ON a.job_id = j.id WHERE a.id = ?', 
                             [application_id], one=True)
        send_invite(application['email'], application['title'])
    
    return jsonify({'message': f'Application status updated to {new_status}!'})

# Create admin user if doesn't exist
def create_admin_if_not_exists():
    with app.app_context():
        admin = query_db('SELECT * FROM users WHERE role = "admin"', one=True)
        if not admin:
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            db = get_db()
            db.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)', 
                      ['admin', 'admin@example.com', password_hash, 'admin'])
            db.commit()
            print("Admin user created! Username: admin, Password: admin123")

@app.route('/api/admin/stats', methods=['GET'])

def admin_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'applicant'")
        total_applicants = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_jobs = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM resumes')
        total_resumes = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM applications')
        total_applications = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'total_users': total_users,
            'total_applicants': total_applicants,
            'total_jobs': total_jobs,
            'total_resumes': total_resumes,
            'total_applications': total_applications
        }), 200

    except Exception as e:
        return jsonify({'message': 'Failed to fetch admin stats', 'error': str(e)}), 500
    
@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    job = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
    if not job:
        return jsonify({'message': 'Job not found!'}), 404
    return jsonify(job)


# Initialize database and create admin user
if not os.path.exists(app.config['DATABASE']):
    init_db()
    create_admin_if_not_exists()

if __name__ == '__main__':
    app.run(debug=True)