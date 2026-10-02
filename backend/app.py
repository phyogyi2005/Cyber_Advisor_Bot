import os
import json
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from link_checker import analyze_url_heuristics, format_gemini_link_prompt

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for cross-origin frontend-backend separation
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Try importing Google Gen AI SDK
GENAI_AVAILABLE = False
genai_client = None

try:
    import google.genai as genai
    from google.genai import types
    GENAI_SDK_VERSION = 'new_genai'
    GENAI_AVAILABLE = True
    logger.info("Successfully imported google.genai SDK.")
except ImportError:
    try:
        import google.generativeai as genai
        GENAI_SDK_VERSION = 'legacy_genai'
        GENAI_AVAILABLE = True
        logger.info("Successfully imported google.generativeai SDK.")
    except ImportError:
        GENAI_SDK_VERSION = None
        GENAI_AVAILABLE = False
        logger.warning("Google GenAI SDK not found. Will use smart heuristic fallback until installed.")

def get_gemini_response(prompt: str, system_instruction: str = "") -> str:
    """Generates AI response using configured Gemini API key with robust multi-model fallback."""
    api_key = Config.GEMINI_API_KEY or os.getenv('GEMINI_API_KEY', '')
    if not api_key or api_key == 'YOUR_GEMINI_API_KEY_HERE':
        raise ValueError("GEMINI_API_KEY is not configured in .env file.")

    if not GENAI_AVAILABLE:
        raise RuntimeError("Google GenAI Python package is not installed.")

    # Only try active stable models
    candidate_models = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']
    last_exception = None

    for model_name in candidate_models:
        try:
            logger.info(f"Attempting response generation with model: {model_name}")
            if GENAI_SDK_VERSION == 'new_genai':
                client = genai.Client(api_key=api_key)
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction if system_instruction else None,
                    temperature=0.3
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                return response.text
            else:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=system_instruction if system_instruction else None
                )
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            last_exception = e
            logger.warning(f"Model '{model_name}' encountered error ({str(e)}). Switching to next candidate model...")

    raise last_exception or RuntimeError("All Gemini model attempts failed.")


# System prompts for Cyber Advisor
NORMAL_SYSTEM_PROMPT = """You are Cyber Advisor, an elite AI Cyber Security Assistant and Security Operations Specialist.
Your primary role is to assist security analysts, IT administrators, developers, and students with cybersecurity queries.
Provide clear, authoritative, and actionable advice on topics including:
- Network Defense, Firewalls, IDS/IPS, Zero Trust
- OWASP Top 10 Web Vulnerabilities & Prevention
- Malware Analysis, Ransomware Defense, Incident Response
- Threat Intelligence & Vulnerability Assessment
- Cryptography, PKI, Hashing & Authentication
- Regulatory Frameworks (NIST, ISO 27001, SOC2, GDPR)

Always maintain a helpful, vigilant, and authoritative Cyber Advisor persona. Use clean Markdown formatting for code snippets and security checklists."""

LEARNING_SYSTEM_PROMPT = """You are Cyber Advisor Academy, an interactive Cybersecurity Mentor and Educator.
Your task is to teach cybersecurity concepts step-by-step to learners.
Structure your responses cleanly with:
1. 💡 Concept Overview & Plain-English Explanation
2. 🎯 Real-World Attack Scenario or Example
3. 🛡️ Defensive Controls & Best Practices
4. ❓ Knowledge Check / Practice Question!

Keep explanations engaging, clear, and educational."""


@app.route('/')
def home():
    return jsonify({
        'service': 'Cyber Advisor API Backend',
        'status': 'online',
        'api_endpoints': {
            'status': '/api/status',
            'chat': '/api/chat',
            'check_link': '/api/check_link'
        }
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    api_key = Config.GEMINI_API_KEY or os.getenv('GEMINI_API_KEY', '')
    has_valid_key = bool(api_key and api_key != 'YOUR_GEMINI_API_KEY_HERE')
    
    return jsonify({
        'status': 'online',
        'api_key_configured': has_valid_key,
        'genai_sdk_available': GENAI_AVAILABLE,
        'default_model': Config.DEFAULT_GEMINI_MODEL
    })


@app.route('/api/chat', methods=['POST'])
def handle_chat():
    data = request.json or {}
    user_message = data.get('message', '').strip()
    mode = data.get('mode', 'normal').lower()

    if not user_message:
        return jsonify({'error': 'Message cannot be empty.'}), 400

    system_prompt = LEARNING_SYSTEM_PROMPT if mode == 'learning' else NORMAL_SYSTEM_PROMPT

    try:
        reply = get_gemini_response(user_message, system_instruction=system_prompt)
        return jsonify({
            'reply': reply,
            'mode': mode,
            'status': 'success'
        })
    except ValueError as ve:
        return jsonify({
            'error': str(ve),
            'reply': f"⚠️ **API Key Missing**: Please add your Google Gemini API key to the `.env` file (`GEMINI_API_KEY=...`) to enable live AI responses."
        }), 200
    except Exception as e:
        logger.error(f"Chat execution error: {str(e)}")
        return jsonify({
            'error': str(e),
            'reply': f"⚠️ **Server Demand Notice**: Google Gemini API is experiencing temporary high demand for model capacity.\n*Details: {str(e)}*"
        }), 200


@app.route('/api/check_link', methods=['POST'])
def check_link():
    data = request.json or {}
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': 'Please provide a URL to scan.'}), 400

    heuristics = analyze_url_heuristics(url)

    if not heuristics.get('valid'):
        return jsonify({
            'error': heuristics.get('error', 'Invalid URL provided.')
        }), 400

    prompt = format_gemini_link_prompt(url, heuristics)
    
    ai_result = None
    try:
        ai_response_text = get_gemini_response(prompt)
        clean_json_str = ai_response_text.strip()
        if clean_json_str.startswith('```'):
            clean_json_str = clean_json_str.split('```')[1]
            if clean_json_str.startswith('json'):
                clean_json_str = clean_json_str[4:]
        clean_json_str = clean_json_str.strip()
        
        ai_result = json.loads(clean_json_str)
    except Exception as e:
        logger.warning(f"Gemini API link analysis fallback due to: {str(e)}")
        h_score = heuristics['heuristic_score']
        risk_score = 100 - h_score
        
        if risk_score > 70:
            rating = "CRITICAL_DANGER"
            verdict = "High Risk Threat Detected (Heuristic Warning)"
        elif risk_score > 40:
            rating = "HIGH_RISK"
            verdict = "Suspicious Link Signals Detected"
        elif risk_score > 20:
            rating = "MODERATE_RISK"
            verdict = "Caution Required - Non-Standard Link"
        else:
            rating = "SAFE"
            verdict = "No Major Heuristic Threats Detected"

        ai_result = {
            "overall_risk_score": risk_score,
            "safety_rating": rating,
            "verdict_title": verdict,
            "summary": f"Analyzed '{heuristics['hostname']}' using multi-layered heuristic threat signals. Safety score is {h_score}/100.",
            "threat_dimensions": {
                "phishing_risk": min(100, risk_score + 10 if heuristics['flags'] else risk_score),
                "malware_risk": risk_score if not heuristics['is_ip_address'] else min(100, risk_score + 25),
                "reputation_risk": 75 if heuristics['tld'] in ['xyz', 'top', 'click'] else risk_score,
                "obfuscation_risk": min(100, int(heuristics['path_entropy'] * 15)),
                "connection_risk": 80 if not heuristics['is_https'] else 10
            },
            "risk_factors": [flag['message'] for flag in heuristics['flags']] or ["No high-severity heuristic flags raised."],
            "recommendations": [
                "Verify the domain ownership before entering sensitive credentials.",
                "Ensure SSL HTTPS encryption is enabled and valid.",
                "Do not download or execute unverified files from unknown links."
            ],
            "chart_data": {
                "labels": ["Phishing", "Malware", "Reputation", "Obfuscation", "Connection"],
                "scores": [
                    min(100, risk_score + 10 if heuristics['flags'] else risk_score),
                    risk_score if not heuristics['is_ip_address'] else min(100, risk_score + 25),
                    75 if heuristics['tld'] in ['xyz', 'top', 'click'] else risk_score,
                    min(100, int(heuristics['path_entropy'] * 15)),
                    80 if not heuristics['is_https'] else 10
                ]
            }
        }

    return jsonify({
        'url': url,
        'heuristics': heuristics,
        'analysis': ai_result,
        'status': 'success'
    })


if __name__ == '__main__':
    port = Config.PORT
    logger.info(f"Starting Cyber Advisor Backend API on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=(Config.FLASK_ENV == 'development'))
