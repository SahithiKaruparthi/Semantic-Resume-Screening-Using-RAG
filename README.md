
### Project Overview

This project is a sophisticated AI-powered recruitment agent that automates the analysis of the candidates' profiles against the specific Job Descriptions. It leverages a **Retrieval-Augmented Generation (RAG)** architecture to intelligently match resumes to job descriptions, providing a detailed analysis and a final recommendation. The system is divided into three main components: a JD summarizer, a resume parser, and a shortlisting agent.

-----

### How It Works

The system operates in a three-step pipeline:

1.  **Job Description Summarization (`jd_summarizer.py`):**

      * The job description is processed using a RAG pipeline.
      * It is split into chunks, embedded, and stored in a **ChromaDB** vector store.
      * An LLM retrieves the most relevant chunks to generate a structured JSON summary, extracting key details like required skills, experience, and responsibilities.

2.  **Resume Parsing (`resume_parser.py`):**

      * This agent extracts raw text from a PDF resume using **PyPDF2**.
      * It then creates a temporary vector store from the resume text.
      * Using an LLM, it queries the temporary vector store to extract and structure the candidate's skills, experience, and education into a usable format.

3.  **Candidate Shortlisting (`shortlister.py`):**

      * This is the core of the project, combining the outputs from the previous two steps.
      * It performs a **hybrid analysis** using both rule-based scoring and a RAG pipeline.
      * **Rule-Based Matching:** It calculates basic scores for skills, experience, and education based on direct keyword matching.
      * **Semantic Matching (RAG):** It queries the pre-built JD vector store (from the JD summarizer) with the candidate's profile to retrieve the most relevant job requirements.
      * **LLM Analysis:** An LLM receives the candidate's profile and the retrieved JD context to generate a detailed, comprehensive analysis in JSON format.
      * **Final Score:** A final match score is computed as a weighted average of the semantic score and the LLM's analysis score, leading to a final recommendation (shortlist, review, or reject).

-----

### Key Technologies

  * **LangChain:** Framework used to build the LLM-powered applications and orchestration chains.
  * **HuggingFace Embeddings:** Provides the embedding models for converting text into vectors.
  * **ChromaDB:** The vector store used to store and retrieve text embeddings for both the JD and the resume.
  * **Groq API:** Provides a fast, scalable LLM inference service for the analysis and summarization tasks.
  * **PyPDF2:** Used for extracting text from PDF resumes.

-----

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/SahithiKaruparthi/Semantic-Resume-Screening-Using-RAG.git
    cd Semantic-Resume-Screening-Using-RAG
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate   # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up API key:**

      * Get a Groq API key from [groq.com](https://groq.com).
      * Create a `.env` file in the project's root directory.
      * Add your API key to the file:
        ```
        GROQ_API_KEY="your_groq_api_key_here"
        ```

-----

### Usage

1.  **Summarize a Job Description:**

    ```python
    from agents.jd_summarizer import summarize_jd

    job_description = "..."  # Paste your job description here
    jd_summary = summarize_jd(job_description)
    print(jd_summary)
    ```

2.  **Parse a Resume:**

    ```python
    from agents.resume_parser import parse_resume

    resume_path = "path/to/your/resume.pdf"
    resume_data = parse_resume(resume_path)
    print(resume_data)
    ```

3.  **Evaluate Match:**

    ```python
    from agents.shortlister import evaluate_match

    # Assuming you have jd_summary and resume_data from the above steps
    jd_data = jd_summary
    resume_data = resume_data

    match_result = evaluate_match(resume_data, jd_data)
    print(match_result)
    ```
