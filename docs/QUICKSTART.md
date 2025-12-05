# Quick Start Guide

Get up and running with LinkedIn Easy Apply Bot in 5 minutes!

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager
- Chrome browser

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/pratikjadhav2726/LinkedInEasyApplyBot.git
cd LinkedInEasyApplyBot

# 2. Install dependencies
uv sync

# 3. Copy and configure
cp examples/config.yaml.example config.yaml
# Edit config.yaml with your details
```

## Minimal Configuration

Edit `config.yaml` with at minimum:

```yaml
email: your-email@example.com
password: your-password

positions:
  - Software Engineer

locations:
  - San Francisco, CA

uploads:
  resume: examples/sample_resume.pdf
```

## Run

```bash
uv run python src/main.py
```

That's it! The bot will:
1. Log into LinkedIn
2. Search for jobs matching your criteria
3. Automatically apply to Easy Apply positions

## Next Steps

- **Enable AI features**: Add API key and set `evaluateJobFit: True`
- **Customize search**: Add more positions, locations, filters
- **Read full docs**: Check [SETUP.md](SETUP.md) for detailed configuration

## Troubleshooting

**Config not found?**
- Ensure `config.yaml` is in the project root
- Copy from `examples/config.yaml.example`

**Import errors?**
- Run `uv sync --dev` to install all dependencies

**Login issues?**
- Check credentials in `config.yaml`
- Disable 2FA temporarily or handle security challenges manually

## Need Help?

- 📖 [Full Setup Guide](SETUP.md)
- 🏗️ [Architecture Overview](ARCHITECTURE.md)
- 🐛 [Report Issues](https://github.com/pratikjadhav2726/LinkedInEasyApplyBot/issues)
- 💬 [Start Discussion](https://github.com/pratikjadhav2726/LinkedInEasyApplyBot/discussions)

