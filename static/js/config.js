/**
 * Cyber Advisor Configuration
 * 
 * If running Frontend and Backend separately (e.g. Flask backend on VPN at http://127.0.0.1:5000),
 * set API_BASE_URL to your backend host address, e.g.:
 * const API_BASE_URL = 'http://127.0.0.1:5000';
 */

const API_BASE_URL = window.location.origin.includes('5000') 
    ? '' 
    : 'http://127.0.0.1:5000';
