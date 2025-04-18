# agents/shortlister.py
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def get_skill_match_score(resume_skills, jd_skills):
    """Calculate skill match score between resume and job description"""
    if not resume_skills or not jd_skills:
        return 0.0
    
    # Convert skills to lowercase for case-insensitive matching
    resume_skills_lower = [skill.lower() for skill in resume_skills]
    jd_required_lower = [skill.lower() for skill in jd_skills.get('required_skills', [])]
    jd_preferred_lower = [skill.lower() for skill in jd_skills.get('preferred_skills', [])]
    
    # Calculate matches
    required_matches = sum(1 for skill in jd_required_lower if any(skill in rs for rs in resume_skills_lower))
    preferred_matches = sum(1 for skill in jd_preferred_lower if any(skill in rs for rs in resume_skills_lower))
    
    # Calculate scores (required skills weigh more)
    required_score = required_matches / max(len(jd_required_lower), 1) * 0.7
    preferred_score = preferred_matches / max(len(jd_preferred_lower), 1) * 0.3 if jd_preferred_lower else 0
    
    return (required_score + preferred_score) * 100

def get_experience_match_score(resume_exp, jd_exp):
    """Calculate experience match score"""
    try:
        # Extract years from resume experience
        resume_years = 0
        for exp in resume_exp:
            duration = exp.get('duration', '').lower()
            if 'year' in duration:
                try:
                    years = float(duration.split()[0])
                    resume_years += years
                except:
                    pass
        
        # Extract required years from JD
        jd_years_str = jd_exp.replace('+', '').lower()
        jd_years = 0
        for word in jd_years_str.split():
            try:
                jd_years = float(word)
                break
            except:
                pass
        
        # Calculate score
        if jd_years == 0:
            return 50.0  # If JD doesn't specify years
        
        if resume_years >= jd_years:
            return 100.0
        else:
            return (resume_years / jd_years) * 100
    except:
        return 50.0  # Default to 50% if parsing fails

def get_education_match_score(resume_edu, jd_edu):
    """Calculate education match score"""
    education_levels = {
        'high school': 1,
        'associate': 2,
        'bachelor': 3,
        'master': 4,
        'phd': 5,
        'doctorate': 5
    }
    
    # Get highest education level from resume
    resume_level = 0
    for edu in resume_edu:
        degree = edu.get('degree', '').lower()
        for level_name, level_value in education_levels.items():
            if level_name in degree:
                resume_level = max(resume_level, level_value)
    
    # Get required education level from JD
    jd_level = 0
    jd_edu_lower = jd_edu.lower()
    for level_name, level_value in education_levels.items():
        if level_name in jd_edu_lower:
            jd_level = max(jd_level, level_value)
    
    # Calculate score
    if jd_level == 0 or resume_level >= jd_level:
        return 100.0
    else:
        return (resume_level / jd_level) * 100

def get_semantic_similarity(resume_text, jd_text):
    """Calculate semantic similarity between resume and JD using sentence embeddings"""
    try:
        # Generate embeddings
        resume_embedding = model.encode(resume_text)
        jd_embedding = model.encode(jd_text)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(
            resume_embedding.reshape(1, -1), 
            jd_embedding.reshape(1, -1)
        )[0][0]
        
        return similarity * 100
    except:
        return 50.0  # Default to 50% if parsing fails

def evaluate_match(resume_data, jd_data):
    """
    Evaluate the match between a resume and job description
    
    Args:
        resume_data (dict): Structured resume data
        jd_data (dict): Structured job description data
        
    Returns:
        float: Match score percentage (0-100)
    """
    # Calculate individual scores
    skill_score = get_skill_match_score(
        resume_data.get('skills', []),
        {
            'required_skills': jd_data.get('required_skills', []),
            'preferred_skills': jd_data.get('preferred_skills', [])
        }
    )
    
    experience_score = get_experience_match_score(
        resume_data.get('experience', []),
        jd_data.get('experience_required', '0')
    )
    
    education_score = get_education_match_score(
        resume_data.get('education', []),
        jd_data.get('education', '')
    )
    
    # Create text representations for semantic matching
    resume_text = f"{resume_data.get('name', '')}. "
    for exp in resume_data.get('experience', []):
        resume_text += f"{exp.get('title', '')} at {exp.get('company', '')}. {exp.get('description', '')}. "
    
    jd_text = f"{jd_data.get('job_title', '')}. "
    for resp in jd_data.get('responsibilities', []):
        jd_text += f"{resp}. "
    
    semantic_score = get_semantic_similarity(resume_text, jd_text)
    
    # Calculate weighted final score
    final_score = (
        0.4 * skill_score + 
        0.3 * experience_score + 
        0.2 * education_score + 
        0.1 * semantic_score
    )
    
    return round(final_score, 2)