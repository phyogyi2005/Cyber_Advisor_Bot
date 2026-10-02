# 🛡️ CyberSentinel AI - Cyber Security Chatbot & Link Threat Analyzer

**CyberSentinel AI** is a state-of-the-art Security Operations Center (SOC) Chatbot Assistant and Link Threat Intelligence System built with **Python Flask**, **Google Gen AI (Gemini 2.5)**, and **Chart.js**.

---

## 🌟 Key Features

### 1. 🛡️ SOC Security Assistant (Normal Mode)
- Powered by **Google Gemini 2.5 API**.
- Answers queries on Network Security, OWASP Top 10 Web Vulnerabilities, Malware Defense, Incident Response, Cryptography, and Security Frameworks (NIST, ISO 27001, SOC2).
- Formats code snippets, terminal commands, and SOC checklists in clean Markdown.

### 2. 🎓 Cyber Academy (Learning Mode)
- Interactive cybersecurity mentor with pre-structured tracks:
  - **Phishing & Social Engineering**
  - **OWASP Top 10 Web Security**
  - **Password Hashing & Authentication**
  - **Malware & Ransomware Defense**
- Generates interactive scenario walk-throughs and knowledge check quizzes!

### 3. 🔍 Link Threat Safety Checker & Heuristic Scanner
- Multi-layered URL security engine:
  - **Protocol & SSL Check**: Unencrypted HTTP warnings & non-standard port detection.
  - **Raw IP Hostname Detection**: Identifies hostnames using numeric IP addresses.
  - **High-Risk TLD & Domain Inspection**: Checks against TLD threat lists (`.xyz`, `.top`, `.click`, `.zip`).
  - **Typosquatting & Brand Spoofing Engine**: Detects impersonation of target brands (Google, PayPal, Microsoft, Apple, Binance, Steam, etc.).
  - **Path Entropy & Obfuscation**: Calculates Shannon entropy to measure parameter obfuscation.
- **Deep Gemini AI Threat Narrative**: Generates comprehensive threat reports and 0-100% risk ratings.

### 4. 📊 Dynamic Bar Chart Visualizer (Chart.js)
- Renders animated bar charts displaying risk scores across 5 security dimensions:
  - **Phishing Risk**
  - **Malware Risk**
  - **Domain Reputation Risk**
  - **Obfuscation Level**
  - **Connection Safety Risk**

### 5. 🛰️ Cyber Scanning Radar HUD Waiting Effect
- Live diagnostic telemetry and animated rotating cyber radar beam while scanning links or waiting for AI threat synthesis.

---

## 🚀 Quick Setup & Execution

### Step 1: Install Python Dependencies
Run the following command in your terminal:
```bash
pip install -r requirements.txt
```

### Step 2: Configure your Google Gemini API Key
Open `.env` (or copy `.env.example` to `.env`) and insert your API Key from [Google AI Studio](https://aistudio.google.com/):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Step 3: Run the Application
Start the Flask development server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 📂 Project Structure
```
Chat_bot/
├── app.py                     # Main Flask web application & Gemini API integration
├── link_checker.py            # Heuristic URL analyzer & prompt formatter
├── config.py                  # Environment configuration settings
├── requirements.txt           # Python dependency specifications
├── .env                       # Environment variables (GEMINI_API_KEY)
├── .env.example               # Example environment template
├── static/
│   ├── css/
│   │   └── style.css          # Cyberpunk SOC dark glassmorphism design & animations
│   └── js/
│       ├── charts.js          # Chart.js Bar Chart visualizer script
│       └── main.js            # Main frontend logic & radar HUD controller
└── templates/
    └── index.html             # Single-page SOC security dashboard template
```
