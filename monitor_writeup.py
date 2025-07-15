import requests
import json
import os
from datetime import datetime

# Configuration
DOMAIN = "writeup.ai"

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
    print(f"🔍 Checking {DOMAIN} status at {datetime.now()}")
    
    # Check environment variables
    sender_email = os.getenv('SENDER_EMAIL')
    print(f"Email configured: {'Yes' if sender_email else 'No'}")
    
    # Load previous status
    previous = load_previous_status()
    
    # Check current status
    dropcatch_status = check_dropcatch_status(DOMAIN)
    
    current = {
        'timestamp': datetime.now().isoformat(),
        'dropcatch': dropcatch_status
    }
    
    # Check for changes
    if previous.get('dropcatch') != dropcatch_status:
        print(f"🚨 STATUS CHANGE: {previous.get('dropcatch', 'unknown')} → {dropcatch_status}")
        if dropcatch_status == "AVAILABLE_FOR_BACKORDER":
            print("🎯 DOMAIN IS AVAILABLE FOR BACKORDER!")
    else:
        print("ℹ️ No changes detected")
    
    # Save current status
    save_current_status(current)
    
    # Print current status
    print(f"📊 DropCatch Status: {dropcatch_status}")
    print(f"Direct link: https://www.dropcatch.com/domain/{DOMAIN}")

if __name__ == "__main__":
    main()
