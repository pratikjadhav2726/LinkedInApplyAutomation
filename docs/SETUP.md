# Setup Guide

This guide will help you set up LinkedIn Easy Apply Bot on your system.

## Prerequisites

- **Python 3.9+** - Check with `python --version` or `python3 --version`
- **uv** - Fast Python package manager ([Installation Guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Chrome Browser** - Required for Selenium automation
- **ChromeDriver** - Automatically managed by webdriver-manager

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/pratikjadhav2726/LinkedInEasyApplyBot.git
cd LinkedInEasyApplyBot
```

### 2. Install uv (if not already installed)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Or with pip:**
```bash
pip install uv
```

### 3. Install Dependencies

```bash
# Install all dependencies including dev tools
uv sync --dev

# Or install only runtime dependencies
uv sync
```

### 4. Configure the Bot

```bash
# Copy the example config file
cp examples/config.yaml.example config.yaml

# Edit config.yaml with your details
# Use your preferred editor:
nano config.yaml
# or
vim config.yaml
# or
code config.yaml  # VS Code
```

**Important:** Never commit `config.yaml` with real credentials to version control!

### 5. Set Up Environment Variables (Optional)

If using AI features, you may need API keys:

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 6. Prepare Your Resume

1. Place your resume PDF in the `examples/` directory or update the path in `config.yaml`
2. Optionally, create a text version of your resume for better AI processing
3. Update the resume path in `config.yaml`:

```yaml
uploads:
  resume: path/to/your/resume.pdf
```

## Running the Bot

### Basic Usage

```bash
# Run the bot
uv run python src/main.py

# Or use the entry point (if configured)
uv run linkedin-bot
```

### First Run Checklist

- [ ] Chrome browser is installed
- [ ] `config.yaml` is configured with your credentials
- [ ] Resume file path is correct in `config.yaml`
- [ ] LinkedIn credentials are valid
- [ ] Internet connection is stable

## Configuration Guide

### Essential Settings

1. **LinkedIn Credentials**
   ```yaml
   email: your-email@example.com
   password: your-password
   ```

2. **Job Search Parameters**
   ```yaml
   positions:
     - Software Engineer
     - Data Scientist
   
   locations:
     - San Francisco, CA
     - Remote
   ```

3. **Resume Path**
   ```yaml
   uploads:
     resume: examples/sample_resume.pdf
   ```

### AI Features (Optional)

To enable AI-powered features:

1. **Get an API Key**
   - OpenAI: https://platform.openai.com/api-keys
   - Groq: https://console.groq.com/keys
   - Or use Ollama for local LLM

2. **Configure in config.yaml**
   ```yaml
   openaiApiKey: sk-proj-your-key-here
   modelName: groq/llama-3.3-70b-versatile
   evaluateJobFit: True
   tailorResume: True
   ```

## Troubleshooting

### Common Issues

**Issue: ChromeDriver not found**
- Solution: webdriver-manager handles this automatically. Ensure Chrome is installed.

**Issue: Config file not found**
- Solution: Ensure `config.yaml` exists in the project root. Copy from `examples/config.yaml.example`

**Issue: Import errors**
- Solution: Run `uv sync --dev` to ensure all dependencies are installed

**Issue: LinkedIn login fails**
- Solution: Check credentials, ensure 2FA is disabled or handle manually, check for security challenges

**Issue: Bot gets stuck**
- Solution: Check browser console, enable debug mode in config.yaml

### Debug Mode

Enable verbose logging:

```yaml
debug: True
```

This will print detailed information about the bot's operations.

## Next Steps

- Read the [README.md](../README.md) for feature overview
- Check [CONTRIBUTING.md](../CONTRIBUTING.md) if you want to contribute
- Review [examples/config.yaml.example](../examples/config.yaml.example) for all configuration options

## Getting Help

- Open an [Issue](https://github.com/pratikjadhav2726/LinkedInEasyApplyBot/issues) for bugs
- Start a [Discussion](https://github.com/pratikjadhav2726/LinkedInEasyApplyBot/discussions) for questions
- Check existing issues and discussions first

