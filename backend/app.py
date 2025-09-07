# File: app.py (Flask Backend)
from flask import Flask, request, jsonify, g, send_from_directory
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
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

truststore.inject_into_ssl()

# Import agents
from agents.jd_summarizer import summarize_jd
from agents.resume_parser import parse_resume
from agents.shortlister import evaluate_match

app = Flask(__name__)
CORS(app)
from config import get_config
config = get_config()
config.init_app(app)

# Validate GROQ API key is set
try:
    config.validate_groq_key()
    print("✅ GROQ API key configured successfully")
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    print("💡 Please run: python setup_env.py")
    sys.exit(1)

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'] + 'resumes/', exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'] + 'jds/', exist_ok=True)
os.makedirs('db/', exist_ok=True)

# Set database path
app.config['DATABASE'] = app.config['DATABASE_PATH']

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
    
    # Convert Row objects to dictionaries and handle binary data
    result = []
    for row in rv:
        row_dict = {}
        for key in row.keys():
            value = row[key]
            # Handle binary data
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8')
                except:
                    value = str(value)
            # Handle datetime objects
            elif hasattr(value, 'isoformat'):
                value = value.isoformat()
            row_dict[key] = value
        result.append(row_dict)
    
    return (result[0] if result else None) if one else result

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
    try:
        jobs = query_db('''
            SELECT 
                id,
                title,
                description,
                datetime(posting_date) as posting_date,
                status
            FROM jobs 
            WHERE status = "open" 
            ORDER BY posting_date DESC
        ''')
        return jsonify(jobs)
    except Exception as e:
        print(f"Error in get_jobs: {str(e)}")
        return jsonify({'message': f'Error fetching jobs: {str(e)}'}), 500

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
def create_application(current_user):
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        resume_id = data.get('resume_id')
        if not job_id or not resume_id:
            return jsonify({"message": "job_id and resume_id are required"}), 400

        # Load resume record
        resume_rec = query_db('SELECT * FROM resumes WHERE id = ?', [resume_id], one=True)
        if not resume_rec:
            return jsonify({"message": "Resume not found"}), 404
        resume_path = resume_rec.get('file_path')

        # Load job
        job = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
        if not job:
            return jsonify({"message": "Job not found"}), 404

        # Parse resume (re-parse to get structured data if not stored)
        resume_data = parse_resume(resume_path)

        # Retrieve job description chunks from Chroma
        vectorstore = Chroma(
            persist_directory="db/vector_store/jobs",
            embedding_function=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )
        job_chunks = vectorstore.similarity_search(job.get('title', ''), k=3)
        job_description = "\n".join([chunk.page_content for chunk in job_chunks]) if job_chunks else job.get('description', '')

        # Evaluate match
        match_result = evaluate_match(resume_data, job_description)

        # Save application
        db = get_db()
        # Ensure applications table has match_analysis column (lightweight migration)
        try:
            get_db().execute("SELECT match_analysis FROM applications LIMIT 1")
        except Exception:
            try:
                get_db().execute("ALTER TABLE applications ADD COLUMN match_analysis TEXT")
                get_db().commit()
            except Exception:
                pass

        db.execute(
            """
            INSERT INTO applications (
                applicant_id,
                job_id,
                resume_id,
                application_date,
                status,
                match_score,
                match_analysis
            ) VALUES (?, ?, ?, datetime('now'), ?, ?, ?)
            """,
            [
                current_user['id'],
                job_id,
                resume_id,
                'pending',
                match_result['match_score'],
                json.dumps(match_result['analysis'])
            ],
        )
        db.commit()

        return jsonify({
            "message": "Application submitted successfully",
            "match_score": match_result['match_score'],
            "semantic_score": match_result['semantic_score'],
            "llm_score": match_result['llm_score'],
            "analysis": match_result['analysis'],
            "status": "pending"
        }), 201
    except Exception as e:
        print(f"Error creating application: {e}")
        return jsonify({"message": f"Failed to submit application: {e}"}), 500

@app.route('/api/applications', methods=['GET'])
@token_required
def get_my_applications(current_user):
    try:
        applications = query_db('''
            SELECT 
                a.id,
                a.applicant_id,
                a.job_id,
                a.resume_id,
                a.match_score,
                a.match_analysis,
                a.status,
                datetime(a.application_date) as application_date,
                j.title as job_title,
                j.description as job_description,
                r.file_path as resume_path
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            LEFT JOIN resumes r ON a.resume_id = r.id
            WHERE a.applicant_id = ?
            ORDER BY a.application_date DESC
        ''', [current_user['id']])
        
        # Convert file paths to relative paths for JSON serialization
        for app in applications:
            if app['resume_path']:
                try:
                    app['resume_path'] = os.path.relpath(app['resume_path'], app.config['UPLOAD_FOLDER'])
                except:
                    # If path conversion fails, just use the original path
                    pass
        
        return jsonify(applications)
    except Exception as e:
        print(f"Error in get_my_applications: {str(e)}")  # Add logging
        return jsonify({'message': f'Error fetching applications: {str(e)}'}), 500

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
    
    # Status updated successfully
    
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
    try:
        job = query_db('''
            SELECT 
                id,
                title,
                description,
                datetime(posting_date) as posting_date,
                status
            FROM jobs 
            WHERE id = ?
        ''', [job_id], one=True)
        
        if not job:
            return jsonify({'message': 'Job not found!'}), 404
        return jsonify(job)
    except Exception as e:
        print(f"Error in get_job: {str(e)}")
        return jsonify({'message': f'Error fetching job: {str(e)}'}), 500

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
@token_required
@admin_required
def update_job(current_user, job_id):
    data = request.get_json()
    
    # Check if job exists
    job = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
    if not job:
        return jsonify({'message': 'Job not found!'}), 404
    
    # Update job
    db = get_db()
    db.execute('UPDATE jobs SET title = ?, description = ? WHERE id = ?',
              [data['title'], data['description'], job_id])
    
    # Process updated job description with RAG
    updated_job = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
    summarized_jd = summarize_jd(updated_job['description'])
    
    # Store the summarized JD
    db.execute('UPDATE jobs SET summarized_data = ? WHERE id = ?',
              [json.dumps(summarized_jd), job_id])
    db.commit()
    
    return jsonify({'message': 'Job updated successfully!'})

@app.route('/api/jobs/<int:job_id>/applications', methods=['GET'])
@token_required
@admin_required
def get_job_applications(current_user, job_id):
    try:
        # First check if job exists
        job = query_db('SELECT * FROM jobs WHERE id = ?', [job_id], one=True)
        if not job:
            return jsonify({'message': 'Job not found!'}), 404

        applications = query_db('''
            SELECT 
                a.id,
                a.applicant_id,
                a.job_id,
                a.resume_id,
                a.match_score,
                a.match_analysis,
                a.status,
                datetime(a.application_date) as application_date,
                u.username,
                u.email,
                r.file_path as resume_path,
                j.title as job_title
            FROM applications a
            JOIN users u ON a.applicant_id = u.id
            LEFT JOIN resumes r ON a.resume_id = r.id
            JOIN jobs j ON a.job_id = j.id
            WHERE a.job_id = ?
            ORDER BY a.match_score DESC, a.application_date DESC
        ''', [job_id])
        
        # Convert file paths to relative paths for JSON serialization
        for app in applications:
            if app['resume_path']:
                try:
                    app['resume_path'] = os.path.relpath(app['resume_path'], app.config['UPLOAD_FOLDER'])
                except:
                    # If path conversion fails, just use the original path
                    pass
        
        return jsonify(applications)
    except Exception as e:
        print(f"Error in get_job_applications: {str(e)}")  # Add logging
        return jsonify({'message': f'Error fetching job applications: {str(e)}'}), 500

@app.route('/api/resumes/<path:filename>', methods=['GET'])
@token_required
def get_resume(current_user, filename):
    try:
        # Check if the user is admin or the resume belongs to them
        resume = query_db('''
            SELECT r.*, a.applicant_id 
            FROM resumes r
            LEFT JOIN applications a ON r.id = a.resume_id
            WHERE r.file_path LIKE ?
        ''', [f'%{filename}'], one=True)
        
        if not resume:
            return jsonify({'message': 'Resume not found'}), 404
            
        if current_user['role'] != 'admin' and resume['applicant_id'] != current_user['id']:
            return jsonify({'message': 'Unauthorized access'}), 403
        
        # Get the directory and filename
        resume_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes')
        try:
            return send_from_directory(resume_dir, filename, as_attachment=True)
        except Exception as e:
            print(f"Error sending file: {str(e)}")
            return jsonify({'message': 'Error serving resume file'}), 500
            
    except Exception as e:
        print(f"Error in get_resume: {str(e)}")
        return jsonify({'message': 'Error serving resume'}), 500

@app.route('/api/resumes', methods=['GET'])
@token_required
def get_user_resumes(current_user):
    resumes = query_db('''
        SELECT * FROM resumes 
        WHERE applicant_id = ? 
        ORDER BY upload_date DESC
    ''', [current_user['id']])
    
    return jsonify(resumes)

# Initialize database and create admin user
if not os.path.exists(app.config['DATABASE']):
    init_db()
    create_admin_if_not_exists()

if __name__ == '__main__':
    app.run(debug=True)