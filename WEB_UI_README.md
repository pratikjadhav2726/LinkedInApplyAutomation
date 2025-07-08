# 🌐 LinkedIn Easy Apply Bot - Web UI

A user-friendly web interface for the LinkedIn Easy Apply Bot that makes it easy for non-technical users to configure and run the automation.

## ✨ Features

- **🎛️ Easy Configuration**: Web form interface for all bot settings
- **⚡ Auto-Install Dependencies**: One-click dependency installation  
- **📊 Real-time Monitoring**: Live logs and automation status
- **🔒 Secure**: Credentials stored locally in config.yaml
- **📱 Responsive Design**: Works on desktop, tablet, and mobile
- **🚀 Zero Setup**: Just run one command to start

## 🚀 Quick Start

### Step 1: Install Dependencies

The web UI can automatically install dependencies, but you can also do it manually:

**Using UV (Recommended - Faster):**
```bash
uv sync
```

**Using Pip:**
```bash
pip install flask psutil
```

### Step 2: Start the Web UI

```bash
python web_ui.py
```

### Step 3: Open Your Browser

Navigate to: **http://localhost:5000**

That's it! 🎉

## 📋 Usage Guide

### 1. **Dashboard**
   - Overview of current configuration
   - Quick actions to start/stop automation
   - Recent activity and logs

### 2. **Configuration**
   - **Account Settings**: LinkedIn credentials and API keys
   - **Job Search**: Positions, locations, filters
   - **Personal Info**: Contact details and preferences  
   - **Resume Files**: Upload paths for PDF/text/DOCX files
   - **AI Features**: Enable smart features like job fit evaluation

### 3. **Monitor**
   - Real-time automation logs
   - Status indicators and uptime
   - Export logs and session statistics

## 🔧 Configuration Sections

### Essential Settings
- **LinkedIn Email & Password** (Required)
- **Target Positions** (Required)
- **Target Locations** (Required) 
- **Resume File Path** (Required)

### Optional Settings
- **OpenAI API Key** - For AI-powered responses
- **Experience Levels** - Entry, Mid-senior, etc.
- **Job Types** - Full-time, Contract, etc.
- **Filters** - Remote only, Under 10 applicants
- **Blacklists** - Companies/titles to avoid

## 🛡️ Security & Safety

- ✅ **Local Storage**: All credentials stored in local `config.yaml`
- ✅ **No Cloud**: Everything runs on your machine
- ✅ **HTTPS Ready**: Can be configured for SSL
- ⚠️ **Keep Private**: Never share your `config.yaml` file
- ⚠️ **Backup**: Save your configuration regularly

## 🔍 Troubleshooting

### Common Issues

**"Dependencies not found"**
- Click "Install Dependencies" in the web UI
- Or run: `uv sync` or `pip install -r requirements.txt`

**"Permission denied"**
- Make sure you have write permissions in the project directory
- Run as administrator on Windows if needed

**"Browser automation fails"**
- Ensure Chrome is installed and up to date
- Check if your LinkedIn credentials are correct
- Verify resume files exist at specified paths

**"Web UI won't start"**
- Check if port 5000 is available
- Make sure Flask is installed: `pip install flask`

### Getting Help

1. Check the console output for error messages
2. Look at the logs in the Monitor page
3. Ensure all required fields are filled in Configuration
4. Verify your resume files exist and are accessible

## 📁 File Structure

```
├── web_ui.py                 # Main Flask application
├── templates/                # HTML templates
│   ├── base.html            # Base layout
│   ├── index.html           # Dashboard
│   ├── configure.html       # Configuration form
│   └── monitor.html         # Monitoring page
├── config.yaml              # Bot configuration (auto-generated)
├── output/                  # Log files and outputs
└── src/                     # Original bot source code
```

## ⚙️ Advanced Configuration

### Custom Port
```bash
# Run on different port
export PORT=8080
python web_ui.py
```

### Production Deployment
```bash
# For production use
export FLASK_ENV=production
python web_ui.py
```

## 🔄 Updates

To update the bot:
1. Pull latest changes from repository
2. Restart the web UI
3. Your configuration will be preserved

## ⚠️ Important Notes

- **Educational Use**: This tool is for educational and personal use only
- **LinkedIn ToS**: Use responsibly and in accordance with LinkedIn's terms
- **Rate Limiting**: The bot includes delays to avoid being detected
- **Manual Review**: Always review applications before submission
- **Backup Config**: Save your configuration settings regularly

## 🆘 Support

If you encounter issues:

1. **Check Logs**: Look at the Monitor page for error messages
2. **Verify Config**: Ensure all required settings are configured
3. **Update Browser**: Make sure Chrome is up to date
4. **Check Files**: Verify resume files exist at specified paths

---

**⭐ Pro Tip**: Start with a small number of target positions and locations to test the setup before scaling up!

**🔒 Security Reminder**: Keep your `config.yaml` file private and never commit it to version control.