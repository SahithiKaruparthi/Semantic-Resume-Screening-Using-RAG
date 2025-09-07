# agents/shortlister.py
import os
import json
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize LLM (lazy initialization)
def get_llm():
    return ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="openai/gpt-oss-20b"
    )

# Create text splitter for resume
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# Create prompt template for match analysis
template = """
You are an expert HR analyst. Analyze the match between the candidate's profile and the job requirements.
Use the retrieved job description chunks and candidate profile to provide a detailed analysis.

Retrieved Job Description Chunks:
{job_chunks}

Candidate Profile:
{candidate_profile}

Provide a detailed analysis in JSON format:
{{
    "match_score": 0-100,
    "strengths": [
        {{
            "category": "skills/experience/education",
            "description": "detailed explanation",
            "relevance": "how this matches job requirements"
        }}
    ],
    "gaps": [
        {{
            "category": "skills/experience/education",
            "description": "what's missing",
            "importance": "how critical this is for the role"
        }}
    ],
    "detailed_analysis": "comprehensive analysis of the match",
    "recommendation": "whether to shortlist, interview, or reject"
}}
"""

prompt = PromptTemplate(
    input_variables=["job_chunks", "candidate_profile"],
    template=template
)

# Create chain (lazy initialization)
def get_chain():
    return LLMChain(llm=get_llm(), prompt=prompt)

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

def get_semantic_similarity(resume_text, job_id):
    """
    Calculate semantic similarity using RAG pipeline:
    1. Convert resume to embedding
    2. Retrieve relevant job chunks
    3. Calculate similarity
    """
    try:
        # Load the vector store
        vectorstore = Chroma(
            persist_directory="db/vector_store/jobs",
            embedding_function=embeddings
        )
        
        # Retrieve relevant chunks
        relevant_chunks = vectorstore.similarity_search(
            resume_text,
            k=3
        )
        
        # Calculate similarity scores safely
        similarities = []
        resume_vec = embeddings.embed_query(resume_text)
        for chunk in relevant_chunks:
            chunk_vec = embeddings.embed_query(chunk.page_content)
            # Cosine similarity
            dot = sum(a*b for a, b in zip(resume_vec, chunk_vec))
            norm_a = sum(a*a for a in resume_vec) ** 0.5
            norm_b = sum(b*b for b in chunk_vec) ** 0.5
            if norm_a == 0 or norm_b == 0:
                continue
            similarities.append(dot / (norm_a * norm_b))

        if not similarities:
            return 0.0

        # Return average similarity as percentage
        return float(min(100, max(0, (sum(similarities) / len(similarities)) * 100)))
        
    except Exception as e:
        print(f"Error in get_semantic_similarity: {str(e)}")
        return 0.0

def generate_matching_analysis(resume_data, jd_data, match_score):
    """
    Generate a human-readable analysis of the match between resume and job description
    
    Args:
        resume_data (dict): Structured resume data
        jd_data (dict): Structured job description data
        match_score (float): The semantic match score
        
    Returns:
        str: A friendly analysis of the match
    """
    try:
        # Extract key information
        candidate_name = resume_data.get('name', 'The candidate')
        job_title = jd_data.get('job_title', 'the position')
        
        # Generate strengths and areas for improvement
        strengths = []
        areas_for_improvement = []
        
        # Analyze skills
        resume_skills = set(skill.lower() for skill in resume_data.get('skills', []))
        required_skills = set(skill.lower() for skill in jd_data.get('required_skills', []))
        preferred_skills = set(skill.lower() for skill in jd_data.get('preferred_skills', []))
        
        matching_required = resume_skills.intersection(required_skills)
        matching_preferred = resume_skills.intersection(preferred_skills)
        
        if matching_required:
            strengths.append(f"Has {len(matching_required)} required skills: {', '.join(matching_required)}")
        if matching_preferred:
            strengths.append(f"Has {len(matching_preferred)} preferred skills: {', '.join(matching_preferred)}")
            
        missing_required = required_skills - resume_skills
        if missing_required:
            areas_for_improvement.append(f"Missing {len(missing_required)} required skills: {', '.join(missing_required)}")
            
        # Analyze experience
        resume_exp = resume_data.get('experience', [])
        jd_exp = jd_data.get('experience_required', '')
        
        if resume_exp:
            total_years = sum(
                float(exp.get('duration', '0').split()[0])
                for exp in resume_exp
                if 'year' in exp.get('duration', '').lower()
            )
            strengths.append(f"Has {total_years:.1f} years of relevant experience")
            
        # Generate the analysis text
        analysis = f"✨ Match Analysis for {candidate_name} ✨\n\n"
        analysis += f"Overall Match Score: {match_score:.1f}%\n\n"
        
        if strengths:
            analysis += "🌟 Strengths:\n"
            for strength in strengths:
                analysis += f"• {strength}\n"
            analysis += "\n"
            
        if areas_for_improvement:
            analysis += "📝 Areas for Improvement:\n"
            for area in areas_for_improvement:
                analysis += f"• {area}\n"
                
        if match_score >= 80:
            analysis += "\n🎯 Recommendation: Strong match! Consider shortlisting."
        elif match_score >= 60:
            analysis += "\n🤔 Recommendation: Moderate match. Review in detail."
        else:
            analysis += "\n⚠️ Recommendation: Low match. May not be suitable."
            
        return analysis
        
    except Exception as e:
        print(f"Error generating matching analysis: {str(e)}")
        return "Unable to generate detailed analysis."

def evaluate_match(resume_data, job_description):
    """
    Evaluate match using comprehensive RAG pipeline:
    1. Create structured candidate profile
    2. Retrieve relevant job description chunks
    3. Augment profile with job context
    4. Generate detailed analysis
    """
    try:
        # Create comprehensive candidate profile
        candidate_profile = f"""
        Candidate Profile:
        Name: {resume_data.get('name', 'N/A')}
        Email: {resume_data.get('email', 'N/A')}
        
        Skills:
        {', '.join(resume_data.get('skills', []))}
        
        Experience:
        {resume_data.get('experience', 'N/A')}
        
        Education:
        {resume_data.get('education', 'N/A')}
        
        Additional Information:
        {resume_data.get('additional_info', 'N/A')}
        """
        
        # Get semantic similarity score (with fallback if retrieval yields nothing)
        semantic_score = get_semantic_similarity(candidate_profile, job_description)
        
        # Load vector store and retrieve relevant job chunks
        vectorstore = Chroma(
            persist_directory="db/vector_store/jobs",
            embedding_function=embeddings
        )
        
        # Retrieve most relevant chunks
        job_chunks = vectorstore.similarity_search(candidate_profile, k=3)
        
        # Format retrieved chunks
        if job_chunks:
            formatted_chunks = "\n\n".join([
                f"Chunk {i+1}:\n{chunk.page_content}"
                for i, chunk in enumerate(job_chunks)
            ])
        else:
            # Fallback: use raw job description if retrieval returns nothing
            formatted_chunks = f"Full JD Fallback:\n{job_description}"
        
        # Generate detailed analysis using LLM
        result = get_chain().invoke({
            "job_chunks": formatted_chunks,
            "candidate_profile": candidate_profile
        })
        # Normalize LLM output to text
        if hasattr(result, 'content'):
            llm_text = result.content
        elif isinstance(result, dict) and 'text' in result:
            llm_text = result['text']
        elif isinstance(result, str):
            llm_text = result
        else:
            llm_text = str(result)

        try:
            analysis = json.loads(llm_text)
            # Combine semantic score with LLM analysis
            llm_match = float(analysis.get('match_score', 0))
            final_score = (semantic_score * 0.7 + llm_match * 0.3)
            
            return {
                "match_score": round(final_score, 2),
                "analysis": {
                    "strengths": analysis.get('strengths', []),
                    "gaps": analysis.get('gaps', []),
                    "detailed_analysis": analysis.get('detailed_analysis', ''),
                    "recommendation": analysis.get('recommendation', '')
                },
                "semantic_score": round(semantic_score, 2),
                "llm_score": analysis.get('match_score', 0)
            }
        except json.JSONDecodeError:
            return {
                "match_score": round(semantic_score, 2),
                "analysis": {
                    "detailed_analysis": llm_text,
                    "error": "Failed to parse LLM response as JSON"
                },
                "semantic_score": round(semantic_score, 2),
                "llm_score": 0
            }
            
    except Exception as e:
        print(f"Error in evaluate_match: {str(e)}")
        return {
            "match_score": 0.0,
            "analysis": {
                "error": str(e),
                "detailed_analysis": "Error in match evaluation"
            },
            "semantic_score": 0.0,
            "llm_score": 0
        }