# agents/jd_summarizer.py

import os
import json
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

load_dotenv()

# Initialize the embedding model
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)

# Initialize Groq LLM with llama3
llm = ChatGroq(
    temperature=0.3,
    groq_api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama3-8b-8192"
)

# Define the prompt template in chat format
system_msg = "You are an HR assistant that specializes in analyzing job descriptions."

human_msg = """
Please analyze the following job description and extract key information:

{job_description}

Please provide the following:
1. Required skills  
2. Experience level  
3. Educational requirements  
4. Key responsibilities  
5. Summary of ideal candidate  
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_msg),
    ("human", human_msg)
])

# Chain together the prompt and model
chain = prompt | llm

def summarize_jd(job_description):
    """
    Analyze job description using Groq's llama3 model and return structured information.
    """
    try:
        # Optionally use vectorstore if you plan to scale with multiple documents
        os.makedirs("temp_db", exist_ok=True)
        Chroma.from_texts([job_description], embeddings, persist_directory="temp_db")

        # Run the chain
        result = chain.invoke({"job_description": job_description})

        # Try parsing result as JSON (if returned in structured format)
        try:
            return json.loads(result.content)
        except json.JSONDecodeError:
            return {"summary": result.content}

    except Exception as e:
        return {"error": str(e)}
