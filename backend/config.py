import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'default_cyber_sentinel_secret_2026')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    PORT = int(os.getenv('PORT', 5000))
    
    # Primary Gemini model
    DEFAULT_GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
