# Architecture Overview

This document provides an overview of the LinkedIn Easy Apply Bot architecture.

## Project Structure

```
LinkedInEasyApplyBot/
├── src/                      # Source code
│   ├── ai/                  # AI/LLM integration
│   │   └── ai_response_generator.py
│   ├── bot/                 # Core bot logic
│   │   └── linkedin_easy_apply.py
│   ├── external/            # External platform handlers
│   │   └── external_applications.py
│   ├── utils/               # Utility functions
│   │   ├── file_utils.py
│   │   └── utils.py
│   └── main.py              # Entry point
├── tests/                    # Test suite
│   └── test_ai_response_generator.py
├── examples/                 # Example files and configs
│   ├── config.yaml.example
│   └── sample_*.pdf/docx/txt
├── docs/                     # Documentation
│   ├── SETUP.md
│   └── ARCHITECTURE.md
├── .github/                  # GitHub templates and workflows
│   ├── ISSUE_TEMPLATE/
│   └── workflows/
├── pyproject.toml           # Project configuration
├── uv.lock                  # Dependency lock file
└── README.md                # Main documentation
```

## Core Components

### 1. Main Entry Point (`src/main.py`)

- Initializes browser with Selenium
- Loads and validates configuration
- Creates bot instance and starts application process

### 2. LinkedIn Bot (`src/bot/linkedin_easy_apply.py`)

**Key Responsibilities:**
- LinkedIn authentication and session management
- Job search and filtering
- Application form filling
- File uploads (resume, cover letter)
- Handling various form field types (text, dropdown, radio, checkbox)

**Main Classes:**
- `LinkedinEasyApply`: Main bot class handling LinkedIn-specific logic

### 3. AI Response Generator (`src/ai/ai_response_generator.py`)

**Key Features:**
- RAG (Retrieval-Augmented Generation) for context optimization
- Semantic search using sentence transformers and FAISS
- Resume content extraction and chunking
- AI-powered question answering
- Job fit evaluation
- Resume tailoring

**Main Classes:**
- `AIResponseGenerator`: Handles all AI/LLM interactions

### 4. External Applications (`src/external/external_applications.py`)

**Supported Platforms:**
- Greenhouse
- Ashby

**Functions:**
- `apply_to_greenhouse()`: Handles Greenhouse application forms
- `apply_to_ashby()`: Handles Ashby application forms

### 5. Utilities (`src/utils/`)

- `file_utils.py`: File I/O operations, CSV logging
- `utils.py`: Helper functions for form interactions

## Data Flow

```
User Config (config.yaml)
    ↓
Main Entry Point
    ↓
LinkedIn Bot
    ├──→ Job Search
    ├──→ Job Filtering
    └──→ Application Process
            ├──→ Form Filling
            ├──→ AI Response Generator (if enabled)
            │       ├──→ RAG Context Building
            │       ├──→ LLM API Calls
            │       └──→ Response Generation
            └──→ External Platform Handler (if redirected)
                    └──→ Platform-specific Form Filling
```

## Key Design Patterns

### 1. RAG (Retrieval-Augmented Generation)

The bot uses RAG to optimize context for small LLMs:

1. **Chunking**: Resume is split into semantic chunks
2. **Embedding**: Chunks are converted to vectors using sentence transformers
3. **Indexing**: FAISS index is built for fast similarity search
4. **Retrieval**: Relevant chunks are retrieved based on query
5. **Generation**: LLM generates response with focused context

### 2. Modular Platform Support

External platforms are handled through separate functions, making it easy to add new platforms.

### 3. Configuration-Driven

All behavior is controlled through `config.yaml`, making it easy to customize without code changes.

## Dependencies

### Core Dependencies
- **selenium**: Browser automation
- **pyautogui**: System interaction (anti-sleep)
- **PyYAML**: Configuration parsing
- **webdriver_manager**: ChromeDriver management

### AI Dependencies
- **litellm**: Unified LLM interface
- **sentence-transformers**: Semantic embeddings
- **faiss-cpu**: Vector similarity search
- **numpy**: Numerical operations

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

## Extension Points

### Adding New Platforms

1. Create handler function in `src/external/external_applications.py`
2. Add detection logic in `src/bot/linkedin_easy_apply.py`
3. Call handler when platform is detected

### Adding New AI Features

1. Extend `AIResponseGenerator` class
2. Add configuration options to `config.yaml`
3. Integrate into bot workflow

### Customizing Form Filling

1. Extend field pattern matching in `src/utils/utils.py`
2. Add custom handlers in `LinkedinEasyApply.additional_questions()`

## Security Considerations

- Credentials stored in `config.yaml` (never committed)
- Session persistence via Chrome user data directory
- No sensitive data in logs (when debug=False)
- API keys loaded from environment variables when possible

## Performance Optimizations

- Lazy loading of AI models
- Caching of resume chunks and embeddings
- Semantic search for relevant context only
- Batch processing of form fields

## Future Improvements

- Plugin system for extensibility
- GUI for configuration
- Better error recovery
- Multi-threaded job processing
- Advanced RAG features (query expansion, hybrid search)

