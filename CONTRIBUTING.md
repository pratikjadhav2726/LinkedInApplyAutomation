# Contributing to LinkedIn Easy Apply Bot

Thank you for your interest in contributing to LinkedIn Easy Apply Bot! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/pratikjadhav2726/LinkedInEasyApplyBot/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Relevant logs or error messages

### Suggesting Features

1. Check existing issues and discussions
2. Create a new issue with:
   - Clear description of the feature
   - Use case and motivation
   - Proposed implementation (if you have ideas)

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install dependencies
   uv sync --dev
   ```

4. **Make your changes**
   - Follow the existing code style
   - Add tests for new features
   - Update documentation as needed
   - Ensure all tests pass: `uv run pytest`

5. **Commit your changes**
   ```bash
   git commit -m "feat: add your feature description"
   ```
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for tests
   - `refactor:` for code refactoring
   - `chore:` for maintenance tasks

6. **Push and create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a PR on GitHub with:
   - Clear description of changes
   - Reference related issues
   - Screenshots (if UI changes)

## Development Setup

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager
- Git

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/LinkedInEasyApplyBot.git
cd LinkedInEasyApplyBot

# Install dependencies
uv sync --dev

# Copy example config
cp examples/config.yaml.example config.yaml
# Edit config.yaml with your test credentials
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_ai_response_generator.py
```

### Code Style

We use:
- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Lint
uv run flake8 src tests

# Type check
uv run mypy src
```

## Project Structure

```
LinkedInEasyApplyBot/
├── src/                    # Source code
│   ├── ai/                 # AI/LLM integration
│   ├── bot/                # Bot logic
│   ├── external/           # External platform handlers
│   ├── utils/              # Utility functions
│   └── main.py             # Entry point
├── tests/                  # Test files
├── examples/               # Example configs and samples
├── docs/                   # Documentation
└── pyproject.toml          # Project configuration
```

## Guidelines

### Code Quality

- Write clear, readable code
- Add docstrings to functions and classes
- Follow PEP 8 style guide
- Keep functions focused and small
- Add type hints where appropriate

### Testing

- Write tests for new features
- Aim for good test coverage
- Test edge cases and error conditions
- Use descriptive test names

### Documentation

- Update README.md for user-facing changes
- Add docstrings to new functions/classes
- Update CHANGELOG.md for significant changes
- Keep comments clear and helpful

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion in GitHub Discussions
- Contact maintainers

Thank you for contributing! 🎉

