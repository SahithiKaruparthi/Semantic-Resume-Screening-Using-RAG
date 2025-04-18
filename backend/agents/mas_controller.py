# agents/mas_controller.py

from .jd_summarizer import summarize_jd
from .resume_parser import parse_resume
from .shortlister import evaluate_match
from .scheduler import send_invite

def run_pipeline(job_data, resume_file):
    """
    Run the full multi-agent system pipeline
    """
    # Step 1: Process the job description
    job_summary = summarize_jd(job_data['description'])
    
    # Step 2: Parse the resume
    parsed_resume = parse_resume(resume_file)
    
    # Step 3: Evaluate the match
    match_score = evaluate_match(parsed_resume, job_summary)
    
    # Step 4: If score is high enough, schedule interview
    if match_score >= 80:
        success = send_invite(job_data['applicant_email'], job_data['title'])
        interview_scheduled = success
    else:
        interview_scheduled = False
    
    # Return the pipeline results
    return {
        'job_summary': job_summary,
        'parsed_resume': parsed_resume,
        'match_score': match_score,
        'interview_scheduled': interview_scheduled
    }