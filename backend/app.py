from flask import Flask, request, jsonify
from flask_cors import CORS
from agents.mas_controller import run_pipeline
from db.database import init_db, get_db
from utils.auth_utils import authenticate, generate_token
import os

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
init_db()

# Auth Endpoints
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = authenticate(data['username'], data['password'])
    if user:
        token = generate_token(user)
        return jsonify({'token': token, 'role': user['role']})
    return jsonify({'error': 'Invalid credentials'}), 401

# Admin Endpoints
@app.route('/api/jd/upload', methods=['POST'])
def upload_jd():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        # Process JD with RAG pipeline
        with open(filename, 'r') as f:
            jd_text = f.read()
        
        # Run MAS pipeline
        run_pipeline(jd_text, [])  # Resumes will be processed separately
        
        return jsonify({'message': 'JD processed successfully'})

# Applicant Endpoints
@app.route('/api/resume/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        
        # Process resume
        from agents.resume_parser import parse_resume
        parsed_resume = parse_resume(filename)
        
        return jsonify({'message': 'Resume processed successfully', 'data': parsed_resume})

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)