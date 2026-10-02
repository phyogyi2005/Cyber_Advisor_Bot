import re
import urllib.parse
import math
import json
import logging
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Known suspicious / high-risk TLDs commonly abused in phishing/malware campaigns
HIGH_RISK_TLDS = {
    'xyz', 'top', 'work', 'click', 'zip', 'gq', 'cf', 'tk', 'ml', 'ga', 
    'country', 'download', 'stream', 'bid', 'racing', 'review', 'space', 
    'icu', 'buzz', 'monster', 'rest', 'fit', 'cam', 'cn', 'ru', 'su'
}

# Major target brands frequently targeted by typosquatting and brand spoofing
TARGET_BRANDS = [
    'google', 'paypal', 'microsoft', 'apple', 'amazon', 'facebook', 'instagram',
    'netflix', 'bankofamerica', 'chase', 'wellsfargo', 'binance', 'coinbase',
    'steam', 'discord', 'linkedin', 'outlook', 'yahoo', 'proton', 'meta',
    'twitter', 'github', 'dropbox', 'adobe', 'spotify', 'roblox', 'uber'
]

# Known URL shorteners
URL_SHORTENERS = {
    'bit.ly', 'tinyurl.com', 't.co', 'is.gd', 'ow.ly', 'buff.ly', 
    'rb.gy', 'cutt.ly', 'shorturl.at', 'tiny.cc', 'v.gd', 'qr.ae'
}

def calculate_entropy(text: str) -> float:
    """Calculates Shannon entropy of a string to measure randomness/obfuscation."""
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    char_counts = {}
    for char in text:
        char_counts[char] = char_counts.get(char, 0) + 1
    for count in char_counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return round(entropy, 2)

def analyze_url_heuristics(raw_url: str) -> Dict[str, Any]:
    """
    Performs comprehensive heuristic security evaluation on a given URL.
    Returns structured metrics and flagged threat signals.
    """
    working_url = raw_url.strip()
    if not working_url.startswith(('http://', 'https://', 'ftp://')):
        working_url = 'http://' + working_url

    try:
        parsed = urllib.parse.urlparse(working_url)
    except Exception as e:
        return {
            'valid': False,
            'error': f"Invalid URL format: {str(e)}",
            'raw_url': raw_url
        }

    hostname = parsed.hostname or ''
    port = parsed.port
    path = parsed.path or ''
    query = parsed.query or ''
    scheme = parsed.scheme.lower()

    flags = []
    heuristic_score = 100

    # 1. Check Protocol Security
    is_https = (scheme == 'https')
    if not is_https:
        flags.append({
            'type': 'PROTOCOL_WARNING',
            'severity': 'MEDIUM',
            'message': 'Unencrypted HTTP protocol in use. Data in transit is susceptible to interception (Man-In-The-Middle).'
        })
        heuristic_score -= 15

    # 2. Check for Non-Standard Ports
    if port and port not in (80, 443):
        flags.append({
            'type': 'SUSPICIOUS_PORT',
            'severity': 'HIGH',
            'message': f'Non-standard port ({port}) detected. Malicious services often run on unusual ports.'
        })
        heuristic_score -= 20

    # 3. Check for IP Hostname
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
    is_ip_address = bool(ip_pattern.match(hostname))
    if is_ip_address:
        flags.append({
            'type': 'RAW_IP_HOSTNAME',
            'severity': 'HIGH',
            'message': 'Raw IP address used instead of a registered domain name. High correlation with phishing/C2 servers.'
        })
        heuristic_score -= 30

    # 4. Domain & TLD Inspection
    tld = hostname.split('.')[-1].lower() if '.' in hostname else ''
    if tld in HIGH_RISK_TLDS:
        flags.append({
            'type': 'HIGH_RISK_TLD',
            'severity': 'MEDIUM',
            'message': f'Top-Level Domain (.{tld}) is heavily associated with spam, phishing, or malware hosting.'
        })
        heuristic_score -= 25

    # 5. Check URL Shortener Usage
    is_shortener = hostname.lower() in URL_SHORTENERS
    if is_shortener:
        flags.append({
            'type': 'URL_SHORTENER',
            'severity': 'LOW',
            'message': 'URL shortener detected. The actual target domain is hidden from view.'
        })
        heuristic_score -= 10

    # 6. Typosquatting / Brand Spoofing Check
    subdomains_and_domain = hostname.lower().split('.')
    spoof_detected = []
    for brand in TARGET_BRANDS:
        for part in subdomains_and_domain:
            if brand in part and part != brand:
                spoof_detected.append((brand, part))
            leetspeak_part = part.replace('0', 'o').replace('1', 'l').replace('3', 'e').replace('@', 'a')
            if brand == leetspeak_part and part != brand:
                spoof_detected.append((brand, part))

    if spoof_detected:
        brands_str = ", ".join([f"{b} (found in '{p}')" for b, p in spoof_detected])
        flags.append({
            'type': 'BRAND_SPOOFING_TYPOSQUATTING',
            'severity': 'CRITICAL',
            'message': f'Possible Brand Impersonation / Typosquatting detected: {brands_str}.'
        })
        heuristic_score -= 35

    # 7. Check for Auth Credentials in URL
    if parsed.username or parsed.password or '@' in raw_url:
        flags.append({
            'type': 'EMBEDDED_CREDENTIALS',
            'severity': 'CRITICAL',
            'message': 'URL contains embedded authentication ("@") syntax, often used to obscure real host destination.'
        })
        heuristic_score -= 30

    # 8. Subdomain Depth & Hyphen Overuse
    subdomain_count = max(0, len(subdomains_and_domain) - 2)
    if subdomain_count >= 3:
        flags.append({
            'type': 'EXCESSIVE_SUBDOMAINS',
            'severity': 'MEDIUM',
            'message': f'Excessive subdomains count ({subdomain_count}). Phishers often create deep subdomains to mimic legitimate URLs.'
        })
        heuristic_score -= 15

    hyphen_count = hostname.count('-')
    if hyphen_count >= 3:
        flags.append({
            'type': 'EXCESSIVE_HYPHENS',
            'severity': 'MEDIUM',
            'message': f'High number of hyphens ({hyphen_count}) in domain name, common in deceptive phishing URLs.'
        })
        heuristic_score -= 10

    # 9. Path & Query Entropy
    full_path_query = path + ('?' + query if query else '')
    path_entropy = calculate_entropy(full_path_query)
    if len(full_path_query) > 30 and path_entropy > 4.5:
        flags.append({
            'type': 'HIGH_ENTROPY_OBFUSCATION',
            'severity': 'MEDIUM',
            'message': f'High randomness/entropy ({path_entropy}) in path parameters. Likely obfuscated or encrypted payload.'
        })
        heuristic_score -= 15

    final_score = max(0, min(100, heuristic_score))

    return {
        'valid': True,
        'raw_url': raw_url,
        'working_url': working_url,
        'hostname': hostname,
        'scheme': scheme,
        'is_https': is_https,
        'is_ip_address': is_ip_address,
        'tld': tld,
        'path_entropy': path_entropy,
        'heuristic_score': final_score,
        'flags': flags,
        'subdomain_count': subdomain_count
    }

def format_gemini_link_prompt(url: str, heuristics: Dict[str, Any]) -> str:
    """Creates a structured prompt for Gemini AI to analyze the link and produce JSON output."""
    return f"""You are an elite Cyber Security Operations Center (SOC) Threat Intelligence AI.
Analyze the following URL and heuristic security signals for potential threats such as Phishing, Malware, C2 Servers, Social Engineering, and Obfuscation.

Target URL: {url}

Pre-Computed Heuristic Security Report:
- Valid URL: {heuristics.get('valid')}
- Hostname: {heuristics.get('hostname')}
- Scheme/Protocol: {heuristics.get('scheme')} (HTTPS: {heuristics.get('is_https')})
- Raw IP Address Hostname: {heuristics.get('is_ip_address')}
- Top-Level Domain (TLD): .{heuristics.get('tld')}
- Heuristic Safety Score: {heuristics.get('heuristic_score')}/100
- Path Entropy Score: {heuristics.get('path_entropy')}
- Security Threat Flags Raised: {json.dumps(heuristics.get('flags', []), indent=2)}

REQUIREMENT:
Evaluate the security risk of this URL thoroughly. Return ONLY a JSON object (no markdown surrounding ticks, strictly valid JSON) with the following exact keys:

{{
  "overall_risk_score": <number 0-100, where 0 is 100% safe and 100 is critical threat>,
  "safety_rating": "<SAFE | LOW_RISK | MODERATE_RISK | HIGH_RISK | CRITICAL_DANGER>",
  "verdict_title": "<Short 3-6 word summary verdict>",
  "summary": "<2-3 sentence executive summary explaining why this URL is safe or dangerous>",
  "threat_dimensions": {{
    "phishing_risk": <number 0-100>,
    "malware_risk": <number 0-100>,
    "reputation_risk": <number 0-100>,
    "obfuscation_risk": <number 0-100>,
    "connection_risk": <number 0-100>
  }},
  "risk_factors": [
    "<Bullet point 1 detailing specific vulnerability or threat signal>",
    "<Bullet point 2>",
    "<Bullet point 3>"
  ],
  "recommendations": [
    "<SOC Defensive Recommendation 1>",
    "<SOC Defensive Recommendation 2>",
    "<SOC Defensive Recommendation 3>"
  ],
  "chart_data": {{
    "labels": ["Phishing", "Malware", "Reputation", "Obfuscation", "Connection"],
    "scores": [<phishing_risk>, <malware_risk>, <reputation_risk>, <obfuscation_risk>, <connection_risk>]
  }}
}}
"""
