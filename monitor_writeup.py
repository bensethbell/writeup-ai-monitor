#!/usr/bin/env python3
"""
Complete Domain Monitoring Script with Simple Email
Uses basic smtplib without emojis to avoid encoding issues
"""

import requests
import smtplib
import json
import os
from datetime import datetime

# Configuration
DOMAIN = "writeup.ai"

# Email settings from environment variables (GitHub Secrets)
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": os.getenv('SENDER_EMAIL'),
    "sender_password": os.getenv('SENDER_PASSWORD'),
    "recipient": os.getenv('RECIPIENT_EMAIL')
}

def check_dropcatch_status(domain):
    """Check if domain is available on DropCatch"""
    try:
        url = f"https://www.dropcatch.com/domain/{domain}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            if "backorder" in content and "place a backorder" in content:
                return "AVAILABLE_FOR_BACKORDER"
            elif "no results" in content or "not found" in content:
                return "NOT_AVAILABLE_YET"
            elif "auction" in content:
                return "IN_AUCTION"
            else:
                return "UNKNOWN_STATUS"
        else:
            return f"ERROR_{response.status_code}"
            
    except Exception as e:
        return f"ERROR: {str(e)}"

def check_whois_status(domain):
    """Check WHOIS status using whois.net"""
    try:
        url = f"https://www.whois.net/whois/{domain}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            content = response.text.lower()
            
            if "pendingdelete" in content or "pending delete" in content:
                status = "pendingDelete"
            elif "redemption" in content:
                status = "redemptionPeriod"
            elif "expired" in content:
                status = "expired"
            elif "active" in content:
                status = "active"
            else:
                status = "unknown"
                
            return {
                'status': status,
                'checked_at': datetime.now().isoformat(),
                'source': 'whois.net'
            }
        else:
            return {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        return {"error": str(e)}

def send_simple_email(subject, body):
    """Send email using simple SMTP without MIME imports"""
    try:
        if not all([EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'], EMAIL_CONFIG['recipient']]):
            print("Email configuration missing")
            return False
        
        # Create simple email message (ASCII safe)
        clean_subject = subject.encode('ascii', 'ignore').decode('ascii')
        clean_body = body.encode('ascii', 'ignore').decode('ascii')
        
        message = f"""From: {EMAIL_CONFIG['sender_email']}
To: {EMAIL_CONFIG['recipient']}
Subject: {clean_subject}

{clean_body}
"""
        
        # Connect and send
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        server.sendmail(
            EMAIL_CONFIG['sender_email'], 
            EMAIL_CONFIG['recipient'], 
            message
        )
        server.quit()
        
        print(f"Email sent: {clean_subject}")
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def load_previous_status():
    """Load previous check results"""
    try:
        with open('domain_status.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_current_status(status_data):
    """Save current check results"""
    with open('domain_status.json', 'w') as f:
        json.dump(status_data, f, indent=2)

def main():
    """Main monitoring function"""
    print(f"Checking {DOMAIN} status at {datetime.now()}")
    
    # Load previous status
    previous = load_previous_status()
    
    # Check current status
    dropcatch_status = check_dropcatch_status(DOMAIN)
    whois_status = check_whois_status(DOMAIN)
    
    current = {
        'timestamp': datetime.now().isoformat(),
        'dropcatch': dropcatch_status,
        'whois': whois_status
    }
    
    # Check for important changes
    changes = []
    critical_alert = False
    
    if previous.get('dropcatch') != dropcatch_status:
        changes.append(f"DropCatch: {previous.get('dropcatch', 'unknown')} -> {dropcatch_status}")
        if dropcatch_status == "AVAILABLE_FOR_BACKORDER":
            critical_alert = True
    
    if previous.get('whois', {}).get('status') != whois_status.get('status'):
        old_status = previous.get('whois', {}).get('status', 'unknown')
        new_status = whois_status.get('status', 'unknown')
        changes.append(f"WHOIS: {old_status} -> {new_status}")
        if new_status in ['pendingDelete', 'expired']:
            critical_alert = True
    
    # Send email if changes detected (or for testing)
    if changes or True:  # REMOVE "or True" after testing
        urgency = "URGENT" if critical_alert else "Update"
        subject = f"{urgency}: {DOMAIN} Status Change!"
        
        body = f"""Domain: {DOMAIN}
Time: {datetime.now()}
GitHub Action: https://github.com/bensethbell/writeup-ai-monitor/actions

CHANGES DETECTED:
{chr(10).join(changes)}

CURRENT STATUS:
- DropCatch: {dropcatch_status}
- WHOIS Status: {whois_status.get('status', 'error')}

ACTION NEEDED:
{f'DOMAIN IS AVAILABLE FOR BACKORDER ON DROPCATCH!' if dropcatch_status == 'AVAILABLE_FOR_BACKORDER' else 'Continue monitoring...'}

Direct DropCatch Link: https://www.dropcatch.com/domain/{DOMAIN}

Next check: Tomorrow at 9 AM UTC
        """
        
        send_simple_email(subject, body)
    else:
        print("No changes detected")
    
    # Save current status
    save_current_status(current)
    
    # Print current status
    print(f"Current Status:")
    print(f"   DropCatch: {dropcatch_status}")
    print(f"   WHOIS: {whois_status.get('status', 'error')}")
    print(f"Direct link: https://www.dropcatch.com/domain/{DOMAIN}")

if __name__ == "__main__":
    main()
