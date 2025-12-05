# Project Structure

This document describes the organization of the LinkedIn Easy Apply Bot repository.

## Directory Layout

```
LinkedInEasyApplyBot/
│
├── src/                          # Source code
│   ├── __init__.py
│   ├── main.py                   # Entry point
│   ├── ai/                       # AI/LLM integration
│   │   ├── __init__.py
│   │   └── ai_response_generator.py
│   ├── bot/                      # Core bot logic
│   │   ├── __init__.py
│   │   └── linkedin_easy_apply.py
│   ├── external/                 # External platform handlers
│   │   ├── __init__.py
│   │   └── external_applications.py
│   └── utils/                    # Utility functions
│       ├── __init__.py
│       ├── file_utils.py
│       └── utils.py
│
├── tests/                        # Test suite
│   ├── __init__.py
│   └── test_ai_response_generator.py
│
├── examples/                     # Example files and templates
│   ├── config.yaml.example       # Configuration template
│   ├── config.prod.yaml.example  # Production config template
│   ├── sample_resume.pdf         # Sample resume (PDF)
│   ├── sample_docx_resume.docx   # Sample resume (DOCX)
│   └── sample_text_resume.txt   # Sample resume (text)
│
├── docs/                         # Documentation
│   ├── SETUP.md                  # Detailed setup guide
│   ├── QUICKSTART.md             # Quick start guide
│   ├── ARCHITECTURE.md           # Architecture overview
│   └── PROJECT_STRUCTURE.md      # This file
│
├── .github/                      # GitHub configuration
│   ├── ISSUE_TEMPLATE/           # Issue templates
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── config.yml
│   └── workflows/                # GitHub Actions
│       └── ci.yml                # CI/CD pipeline
│
├── chrome_bot/                   # Chrome user data (gitignored)
│   └── ...                       # Browser session data
│
├── output/                       # Output files (gitignored)
│   └── ...                       # CSV logs, etc.
│
├── .gitignore                    # Git ignore rules
├── LICENSE                       # License file
├── README.md                     # Main documentation
├── CONTRIBUTING.md               # Contribution guidelines
├── CHANGELOG.md                  # Version history
├── CODE_OF_CONDUCT.md           # Code of conduct
├── pyproject.toml                # Project configuration
├── uv.lock                       # Dependency lock file
└── requirements.txt              # Legacy requirements (uv-managed)
```

## Key Files

### Configuration Files

- **`pyproject.toml`**: Project metadata, dependencies, and tool configurations
- **`uv.lock`**: Locked dependency versions for reproducible builds
- **`requirements.txt`**: Legacy requirements file (managed by uv)
- **`examples/config.yaml.example`**: Template configuration file

### Source Code

- **`src/main.py`**: Application entry point
- **`src/bot/linkedin_easy_apply.py`**: Core LinkedIn automation logic
- **`src/ai/ai_response_generator.py`**: AI/LLM integration with RAG
- **`src/external/external_applications.py`**: External platform handlers

### Documentation

- **`README.md`**: Main project documentation
- **`docs/SETUP.md`**: Detailed setup instructions
- **`docs/QUICKSTART.md`**: Quick start guide
- **`docs/ARCHITECTURE.md`**: Technical architecture overview
- **`CONTRIBUTING.md`**: Contribution guidelines
- **`CHANGELOG.md`**: Version history

### GitHub

- **`.github/ISSUE_TEMPLATE/`**: Issue templates for bug reports and feature requests
- **`.github/workflows/ci.yml`**: Continuous integration workflow

## File Naming Conventions

- **Python files**: `snake_case.py`
- **Config files**: `kebab-case.yaml` or `snake_case.yaml`
- **Documentation**: `UPPERCASE.md` (e.g., `README.md`, `SETUP.md`)
- **Test files**: `test_*.py`

## Ignored Files

The following are ignored by git (see `.gitignore`):

- `config.yaml` - User configuration (never commit!)
- `config.prod.yaml` - Production configuration
- `*.csv` - Output logs (except examples)
- `chrome_bot/` - Browser session data
- `output/` - Output directory
- `__pycache__/` - Python cache
- `.env` - Environment variables
- Virtual environments

## Adding New Files

### Adding a New Module

1. Create directory under `src/` if needed
2. Add `__init__.py` file
3. Update imports in dependent modules
4. Add tests in `tests/`

### Adding Documentation

1. Add markdown file to `docs/`
2. Update `README.md` with link if needed
3. Follow existing documentation style

### Adding Examples

1. Place example files in `examples/`
2. Update `.gitignore` if needed to allow specific files
3. Reference in documentation

## Best Practices

1. **Keep source code in `src/`**: All application code goes here
2. **Tests mirror source structure**: Tests in `tests/` mirror `src/` structure
3. **Examples are templates**: Use `.example` suffix for config templates
4. **Documentation in `docs/`**: Keep all docs organized here
5. **Never commit secrets**: Config files with real credentials are gitignored

