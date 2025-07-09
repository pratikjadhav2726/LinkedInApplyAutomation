# 🧠 LinkedIn Apply Bot with Offline AI Integration (Ollama)

## Project Overview

This project automates the job application process on LinkedIn Easy Apply and extends support to external platforms such as Greenhouse, Ashby, and more. It features AI-powered resume tailoring and intelligent question answering via offline LLMs (Ollama or any LLM provider through LiteLLM), delivering a personalized, end-to-end automation experience for job seekers.

---

## 🚦 Project Status

### ✅ Stable Features

- Automated login and job application for LinkedIn Easy Apply
- AI-driven question answering for application forms (text, numeric, multiple-choice)
- **RAG-powered resume context optimization** with semantic chunking and vector retrieval
- Resume tailoring and skill replacement to optimize ATS scores
- Support for both PDF and DOCX resumes
- Offline AI integration (Ollama + phi4-mini) for data privacy and speed
- Flexible backend—integrate any LLM via LiteLLM
- Modular codebase designed for extensibility and additional platforms
- **Semantic search** using lightweight embedding models for better context relevance

### 🧪 Experimental Features

- Support for external applications including Greenhouse and Ashby
- Resume tailoring and regeneration (DOCX to PDF)

### 🚧 In Development / On the Way

- ~~Improved resume tailoring using RAG with semantic chunking and vector retrieval~~ ✅ **COMPLETED**
- Lightweight LLM-powered rewriting of resume sections based on job descriptions
- ~~Resume context compression for small models to reduce hallucination~~ ✅ **COMPLETED**
- Confidence scoring and APPLY/SKIP justification for job fit evaluation
- Pluggable model backend (phi4-mini, Mistral, TinyLlama, etc.)
- Logging outcomes for feedback loop and model fine-tuning

## 🧠 RAG (Retrieval-Augmented Generation) Features

### Smart Context Building
The bot now uses advanced RAG techniques to optimize context for small LLMs:

- **Semantic Chunking**: Resume content is intelligently split into meaningful chunks by sections and context
- **Vector Embeddings**: Uses `all-MiniLM-L6-v2` (90MB) for fast, accurate semantic search
- **FAISS Index**: Lightning-fast similarity search for relevant resume sections
- **Query-Aware Retrieval**: Finds most relevant resume content based on job description and questions
- **Context Caching**: Avoids recomputation for better performance

### Benefits for Small LLMs
- **Reduced Token Usage**: Only sends relevant context instead of entire resume
- **Better Accuracy**: Focused information reduces hallucination
- **Faster Response**: Less context to process means quicker generation
- **Cost Effective**: Fewer tokens = lower API costs
- **Scalable**: Works efficiently with resumes of any length

### Technical Implementation
```python
# Semantic search for relevant resume sections
relevant_chunks = self._semantic_search(query + job_description, top_k=8)

# Context optimization for small models
context = self._build_context_rag(
    query=question_text, 
    job_description=jd, 
    max_tokens=1500  # Optimized for small LLMs
)
```

## 🧩 Technologies Used

- Python (Selenium, PDF, DOCX)
- Ollama for offline LLM chat
- `phi4-mini` model
- **Sentence Transformers** for semantic embeddings
- **FAISS** for vector similarity search
- **NumPy** for efficient vector operations
- PyAutoGUI (to prevent system sleep)
- Regex, JSON, CSV, and automation utilities

## 📦 Getting Started

1. Clone the repository
2. Install dependencies using UV (recommended) or pip
3. Configure `config.yaml` with your details (LinkedIn credentials, resume path, etc.)
4. Run the bot using your preferred driver (e.g., Chrome WebDriver)
5. Ensure Ollama and the `phi4-mini` model are running locally
6. Ensure you have Groq API Key in .env file.

## 🚀 Installation & Usage with UV (Recommended)

This project uses [UV](https://docs.astral.sh/uv/) for fast and reliable dependency management.

### Prerequisites
- Python 3.9 or higher
- UV package manager ([install UV](https://docs.astral.sh/uv/getting-started/installation/))

### Quick Setup
```bash
# Clone the repository
git clone https://github.com/pratikjadhav2726/LinkedInEasyApplyBot.git
cd LinkedInEasyApplyBot

# Install all dependencies (including RAG dependencies)
uv sync

# Install additional RAG dependencies if needed
uv add sentence-transformers faiss-cpu numpy

# Run the bot
uv run python main.py
```

### RAG-Specific Dependencies
```bash
# Core RAG dependencies
uv add sentence-transformers  # For embeddings
uv add faiss-cpu             # For vector search
uv add numpy                 # For vector operations
```

### Common UV Commands
```bash
# Install dependencies
uv sync

# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name

# Remove a dependency
uv remove package-name

# Run the project
uv run python main.py

# Run with script entry point
uv run linkedin-bot

# Update dependencies
uv lock --upgrade
```

### Key Files
- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Lock file with exact versions of all dependencies
- `requirements.txt.backup` - Backup of the original requirements.txt

### Benefits of UV
- **⚡ Fast**: Much faster than pip for dependency resolution and installation
- **🔒 Reliable**: Lockfile ensures reproducible builds across environments
- **📦 Modern**: Uses standard pyproject.toml configuration
- **🛠️ All-in-one**: Handles virtual environments, dependencies, and project management

## ⚙️ AI Capabilities

- Uses LLM with RAG to:
  - **Intelligently extract** relevant resume sections for each question
  - **Semantically match** skills and experience to job requirements
  - Extract job-specific skills
  - Replace outdated resume skills
  - Tailor and regenerate resume (DOCX to PDF) *(experimental)*
  - Answer custom LinkedIn application questions with **focused context**
  - Evaluate job fit with **relevant experience matching**
  - **Compress context** for optimal small LLM performance

## 🎯 RAG Performance Optimizations

### For Small LLMs (phi4-mini, TinyLlama, etc.)
- Context limited to 1500-2000 tokens for optimal performance
- Semantic relevance scoring ensures only pertinent information is included
- Section-aware chunking maintains context coherence
- Caching reduces repeated computations

### Debug Mode
Enable debug mode to see RAG in action:
```python
# Shows relevance scores and selected chunks
ai_generator = AIResponseGenerator(..., debug=True)
```

## 🔮 Future Work

- Expand support for more external job platforms
- Add a user-friendly GUI for configuration and monitoring
- Enhance error handling and reporting
- Community-driven plugin system for new features
- **Advanced RAG features**: Multi-modal embeddings, query expansion, hybrid search

## 📁 Repository Status

> This project is a **modified version** of a popular LinkedIn Easy Apply Bot with enhanced AI capabilities via offline models and advanced RAG implementation.
> 
> Original credit: https://github.com/NathanDuma/LinkedIn-Easy-Apply-Bot

## 📜 License

This project is for educational and personal use only. Do not use it to spam applications or violate LinkedIn's terms.

---

🔐 **Important:** Keep your `config.yaml` and credentials private. Do not upload them to any public repo.
