# agents/jd_summarizer.py

import os
import json
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize LLM (lazy initialization)
def get_llm():
    return ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="openai/gpt-oss-20b"
    )

# Create text splitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)

# Create prompt template
template = """
Analyze the following job description and extract key information in a structured format.
Include:
1. Required skills
2. Preferred skills
3. Experience requirements
4. Education requirements
5. Key responsibilities
6. Job title
7. Company information (if available)

Job Description:
{job_description}

Provide the information in JSON format with the following structure if they exist. Otherwise leave them blank. Ensure the output is valid JSON. Do not include any explanation or commentary:
{
    "job_title": "",
    "required_skills": [],
    "preferred_skills": [],
    "experience_required": "",
    "education": "",
    "responsibilities": [],
    "company_info": ""
}
"""

prompt = PromptTemplate(
    input_variables=["job_description"],
    template=template
)

# Create chain (lazy initialization)
def get_chain():
    return LLMChain(llm=get_llm(), prompt=prompt)

def summarize_jd(job_description):
    """
    Process job description using RAG pipeline:
    1. Chunk the job description
    2. Store chunks in vector store
    3. Use LLM to generate structured summary
    """
    try:
        # Create chunks
        chunks = text_splitter.split_text(job_description)
        
        # Store in Chroma
        vectorstore = Chroma.from_texts(
            chunks,
            embeddings,
            persist_directory="db/vector_store/jobs"
        )
        
        # Retrieve relevant chunks for summarization
        relevant_chunks = vectorstore.similarity_search(
            "What are the key requirements and responsibilities for this job?",
            k=3
        )
        
        # Combine relevant chunks
        context = "\n".join([chunk.page_content for chunk in relevant_chunks])
        
        # Run the chain with retrieved context
        result = get_chain().invoke({"job_description": context})
        
        # Parse result as JSON
        try:
            return json.loads(result.content)
        except json.JSONDecodeError:
            return {"summary": result.content}
            
    except Exception as e:
        print(f"Error in summarize_jd: {str(e)}")
        return {"error": str(e)}
