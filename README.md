# 🧠 LinkedIn Easy Apply Bot with Offline AI Integration (Ollama)

This project automates the LinkedIn Easy Apply job application process, enhanced with **AI-powered resume tailoring** and **application question answering** using **offline LLMs via Ollama**.

## 🚀 Features

- 🔁 Auto-login and apply to jobs using LinkedIn's Easy Apply
- 🧠 AI-powered question answering for job applications (text, numeric, choice)
- 📄 Resume tailoring using LLMs based on job description
- 📊 Skills replacement suggestions to optimize ATS score
- 🧾 Works with PDF and DOCX resumes
- 🛡️ Completely offline AI integration using **Ollama + phi4-mini**

## 🧩 Technologies Used

- Python (Selenium, PDF, DOCX)
- Ollama for offline LLM chat
- `phi4-mini` model
- PyAutoGUI (to prevent system sleep)
- Regex, JSON, CSV, and automation utilities

## 📦 Getting Started

1. Clone the repository
2. Configure `config.yaml` with your details (LinkedIn credentials, resume path, etc.)
3. Run the bot using your preferred driver (e.g., Chrome WebDriver)
4. Ensure Ollama and the `phi4-mini` model are running locally

## ⚙️ AI Capabilities

- Uses LLM to:
  - Extract job-specific skills
  - Replace outdated resume skills
  - Tailor and regenerate resume (DOCX to PDF)
  - Answer custom LinkedIn application questions
  - Evaluate job fit (optional)

## 📁 Repository Status

> This project is a **modified version** of a popular LinkedIn Easy Apply Bot with enhanced AI capabilities via offline models.  
Original credit: [Original GitHub Repo](https://github.com/originaluser/originalrepo)

## 📜 License

This project is for educational and personal use only. Do not use it to spam applications or violate LinkedIn's terms.

---

🔐 **Important:** Keep your `config.yaml` and credentials private. Do not upload them to any public repo.
