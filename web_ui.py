#!/usr/bin/env python3

import os
import sys
import subprocess
import threading
import time
import json
import yaml
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import signal
import psutil

app = Flask(__name__)
app.secret_key = 'linkedin_bot_secret_key_change_this'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for automation control
automation_process = None
automation_status = {"running": False, "logs": [], "start_time": None}

class AutomationRunner:
    def __init__(self):
        self.process = None
        self.logs = []
        self.running = False
        
    def start_automation(self, config_path="config.yaml"):
        """Start the LinkedIn automation bot"""
        try:
            self.running = True
            automation_status["running"] = True
            automation_status["start_time"] = datetime.now().isoformat()
            automation_status["logs"] = []
            
            # Change to src directory and run main.py
            cmd = [sys.executable, "src/main.py"]
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.getcwd()
            )
            
            # Monitor output in a separate thread
            def monitor_output():
                for line in iter(self.process.stdout.readline, ''):
                    if line:
                        log_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "message": line.strip()
                        }
                        automation_status["logs"].append(log_entry)
                        logger.info(f"Bot: {line.strip()}")
                        
                self.process.wait()
                self.running = False
                automation_status["running"] = False
                
            thread = threading.Thread(target=monitor_output)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start automation: {e}")
            self.running = False
            automation_status["running"] = False
            return False
    
    def stop_automation(self):
        """Stop the running automation"""
        try:
            if self.process and self.process.poll() is None:
                # Terminate gracefully first
                self.process.terminate()
                time.sleep(2)
                
                # Force kill if still running
                if self.process.poll() is None:
                    self.process.kill()
                    
            self.running = False
            automation_status["running"] = False
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop automation: {e}")
            return False

automation_runner = AutomationRunner()

def install_dependencies():
    """Install project dependencies"""
    try:
        # Check if uv is available
        try:
            subprocess.run(['uv', '--version'], check=True, capture_output=True)
            # Use uv sync for faster installation
            result = subprocess.run(['uv', 'sync'], check=True, capture_output=True, text=True)
            logger.info("Dependencies installed successfully using uv")
            return True, "Dependencies installed successfully using uv"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to pip
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                                  check=True, capture_output=True, text=True)
            logger.info("Dependencies installed successfully using pip")
            return True, "Dependencies installed successfully using pip"
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to install dependencies: {e.stderr}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error installing dependencies: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return get_default_config()
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()

def save_config(config_data):
    """Save configuration to config.yaml"""
    try:
        with open('config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config_data, file, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def get_default_config():
    """Return default configuration template"""
    return {
        'email': 'email@domain.com',
        'password': 'yourpassword',
        'openaiApiKey': 'sk-proj-your-openai-api-key',
        'disableAntiLock': False,
        'remote': False,
        'lessthanTenApplicants': False,
        'newestPostingsFirst': False,
        'experienceLevel': {
            'internship': False,
            'entry': True,
            'associate': True,
            'mid-senior level': True,
            'director': False,
            'executive': False
        },
        'jobTypes': {
            'full-time': True,
            'contract': True,
            'part-time': False,
            'temporary': True,
            'internship': False,
            'other': False,
            'volunteer': False
        },
        'date': {
            'all time': True,
            'month': False,
            'week': False,
            '24 hours': False
        },
        'positions': [],
        'locations': [],
        'residentStatus': False,
        'distance': 100,
        'outputFileDirectory': 'output/',
        'companyBlacklist': [],
        'titleBlacklist': [],
        'posterBlacklist': [],
        'uploads': {
            'resume': 'sample_resume.pdf'
        },
        'checkboxes': {
            'driversLicence': True,
            'requireVisa': False,
            'legallyAuthorized': False,
            'certifiedProfessional': True,
            'urgentFill': True,
            'commute': True,
            'remote': True,
            'drugTest': True,
            'assessment': True,
            'securityClearance': False,
            'degreeCompleted': ['High School Diploma', 'Bachelor\'s Degree'],
            'backgroundCheck': True
        },
        'universityGpa': 4.0,
        'salaryMinimum': 65000,
        'languages': {
            'english': 'Native or bilingual'
        },
        'noticePeriod': 2,
        'experience': {
            'default': 0
        },
        'personalInfo': {
            'Pronouns': 'Mr.',
            'First Name': 'FirstName',
            'Last Name': 'LastName',
            'Phone Country Code': 'Canada (+1)',
            'Mobile Phone Number': '1234567890',
            'Street address': '123 Fake Street',
            'City': 'Red Deer, Alberta',
            'State': 'YourState',
            'Zip': 'YourZip/Postal',
            'Linkedin': 'https://www.linkedin.com/in/my-linkedin-profile',
            'Website': 'https://www.my-website.com',
            'MessageToManager': 'Hi, I am interested to join your organization. Please have a look at my resume. Thank you.'
        },
        'eeo': {
            'gender': 'None',
            'race': 'None',
            'veteran': 'None',
            'disability': 'None',
            'citizenship': 'yes',
            'clearance': 'no'
        },
        'evaluateJobFit': False,
        'tailorResume': False,
        'textResume': 'sample_text_resume.txt',
        'docxResume': 'sample_docx_resume.docx',
        'debug': False,
        'modelName': 'groq/llama-3.3-70b-versatile'
    }

@app.route('/')
def index():
    """Main dashboard page"""
    config = load_config()
    return render_template('index.html', config=config, status=automation_status)

@app.route('/configure')
def configure():
    """Configuration page"""
    config = load_config()
    return render_template('configure.html', config=config)

@app.route('/save_config', methods=['POST'])
def save_config_route():
    """Save configuration from form"""
    try:
        form_data = request.form
        config = load_config()
        
        # Update config with form data
        config['email'] = form_data.get('email', '')
        config['password'] = form_data.get('password', '')
        config['openaiApiKey'] = form_data.get('openaiApiKey', '')
        
        # Boolean fields
        config['disableAntiLock'] = 'disableAntiLock' in form_data
        config['remote'] = 'remote' in form_data
        config['lessthanTenApplicants'] = 'lessthanTenApplicants' in form_data
        config['newestPostingsFirst'] = 'newestPostingsFirst' in form_data
        config['residentStatus'] = 'residentStatus' in form_data
        config['evaluateJobFit'] = 'evaluateJobFit' in form_data
        config['tailorResume'] = 'tailorResume' in form_data
        config['debug'] = 'debug' in form_data
        
        # Experience levels
        for level in config['experienceLevel'].keys():
            config['experienceLevel'][level] = f'exp_{level.replace(" ", "_").replace("-", "_")}' in form_data
            
        # Job types
        for job_type in config['jobTypes'].keys():
            config['jobTypes'][job_type] = f'job_{job_type.replace("-", "_")}' in form_data
            
        # Date filter (only one should be true)
        for date_option in config['date'].keys():
            config['date'][date_option] = f'date_{date_option.replace(" ", "_")}' in form_data
            
        # Lists
        positions_text = form_data.get('positions', '')
        config['positions'] = [p.strip() for p in positions_text.split('\n') if p.strip()]
        
        locations_text = form_data.get('locations', '')
        config['locations'] = [l.strip() for l in locations_text.split('\n') if l.strip()]
        
        blacklist_companies = form_data.get('companyBlacklist', '')
        config['companyBlacklist'] = [c.strip() for c in blacklist_companies.split('\n') if c.strip()]
        
        blacklist_titles = form_data.get('titleBlacklist', '')
        config['titleBlacklist'] = [t.strip() for t in blacklist_titles.split('\n') if t.strip()]
        
        # Numeric fields
        config['distance'] = int(form_data.get('distance', 100))
        config['universityGpa'] = float(form_data.get('universityGpa', 4.0))
        config['salaryMinimum'] = int(form_data.get('salaryMinimum', 65000))
        config['noticePeriod'] = int(form_data.get('noticePeriod', 2))
        
        # Personal info
        personal_fields = ['pronouns', 'firstName', 'lastName', 'phoneCountryCode', 
                          'mobilePhone', 'streetAddress', 'city', 'state', 'zip', 
                          'linkedin', 'website', 'messageToManager']
        
        for field in personal_fields:
            if field in form_data:
                # Map form field names to config field names
                field_mapping = {
                    'pronouns': 'Pronouns',
                    'firstName': 'First Name',
                    'lastName': 'Last Name',
                    'phoneCountryCode': 'Phone Country Code',
                    'mobilePhone': 'Mobile Phone Number',
                    'streetAddress': 'Street address',
                    'city': 'City',
                    'state': 'State',
                    'zip': 'Zip',
                    'linkedin': 'Linkedin',
                    'website': 'Website',
                    'messageToManager': 'MessageToManager'
                }
                config_key = field_mapping.get(field, field)
                config['personalInfo'][config_key] = form_data.get(field, '')
        
        # Resume file
        config['uploads']['resume'] = form_data.get('resume', 'sample_resume.pdf')
        config['textResume'] = form_data.get('textResume', 'sample_text_resume.txt')
        config['docxResume'] = form_data.get('docxResume', 'sample_docx_resume.docx')
        
        # Model name
        config['modelName'] = form_data.get('modelName', 'groq/llama-3.3-70b-versatile')
        
        if save_config(config):
            flash('Configuration saved successfully!', 'success')
        else:
            flash('Error saving configuration!', 'error')
            
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        flash(f'Error saving configuration: {str(e)}', 'error')
    
    return redirect(url_for('configure'))

@app.route('/install_deps')
def install_deps():
    """Install dependencies"""
    success, message = install_dependencies()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('index'))

@app.route('/start_automation')
def start_automation():
    """Start the LinkedIn automation"""
    if automation_runner.running:
        flash('Automation is already running!', 'warning')
    else:
        success = automation_runner.start_automation()
        if success:
            flash('Automation started successfully!', 'success')
        else:
            flash('Failed to start automation!', 'error')
    
    return redirect(url_for('monitor'))

@app.route('/stop_automation')
def stop_automation():
    """Stop the LinkedIn automation"""
    success = automation_runner.stop_automation()
    if success:
        flash('Automation stopped successfully!', 'success')
    else:
        flash('Failed to stop automation!', 'error')
    
    return redirect(url_for('monitor'))

@app.route('/monitor')
def monitor():
    """Monitor automation status and logs"""
    return render_template('monitor.html', status=automation_status)

@app.route('/api/status')
def api_status():
    """API endpoint for automation status"""
    return jsonify(automation_status)

@app.route('/api/logs')
def api_logs():
    """API endpoint for automation logs"""
    return jsonify({"logs": automation_status["logs"]})

if __name__ == '__main__':
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)
    
    print("🤖 LinkedIn Easy Apply Bot - Web UI")
    print("="*50)
    print("📋 Starting web interface...")
    print(f"🌐 Open your browser and go to: http://localhost:5000")
    print("📝 Configure your settings and start the automation!")
    print("="*50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)