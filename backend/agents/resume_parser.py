
# agents/resume_parser.py

import os
import PyPDF2
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

def parse_resume(file_path):
    """
    Parse resume PDF and extract structured information
    """
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)
    
    # Initialize embedding model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )
    
    # Create a temporary document for the resume
    os.makedirs("temp_db_resume", exist_ok=True)
    
    # Store the text in vector db
    db = Chroma.from_texts(
        [text], 
        embeddings, 
        persist_directory="temp_db_resume"
    )
    
    # Define the prompt template
    system = "You are an HR assistant that specializes in analyzing resumes."

    human = """
    Please analyze the following resume and extract key information:

    {resume_text}

    Please provide:
    1. Skills  
    2. Work experience (with years)  
    3. Education  
    4. Certifications  
    5. Projects  
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    
    # Initialize the language model
    llm = ChatGroq(
        temperature=0.3,
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama3-8b-8192",  # Or "llama3-70b-8192"
    )
    
    # Create a retrieval chain
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(),
    )
    
    # Query for each aspect of the resume
    skills_query = "What are the skills mentioned in this resume?"
    experience_query = "What is the work experience mentioned in this resume?"
    education_query = "What is the educational background mentioned in this resume?"
    certifications_query = "What certifications are mentioned in this resume?"
    
    # Get responses
    skills = qa.run(skills_query)
    experience = qa.run(experience_query)
    education = qa.run(education_query)
    certifications = qa.run(certifications_query)
    
    # For simplicity, create parsed data structure
    parsed_data = {
        "skills": skills,
        "experience": experience,
        "education": education,
        "certifications": certifications
    }
    
    return parsed_data

def extract_text_from_pdf(file_path):
    """
    Extract text from PDF file
    """
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text