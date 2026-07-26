import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import sys

# Primary URL – the page you saw the snippet on (likely the main PMD page)
URL = "https://ffd.pmd.gov.pk/"

def extract_alert():
    headers = {"User-Agent": "Mozilla/5.0 (compatible; FloodAlertBot/1.0)"}
    try:
        print(f"Fetching {URL}...")
        response = requests.get(URL, timeout=25, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for the paragraph with class 'update-snippet' (or 'font-weight-bold')
        alert_p = soup.find('p', class_='update-snippet')
        if not alert_p:
            alert_p = soup.find('p', class_='font-weight-bold')
        if not alert_p:
            # Try any p with dir="rtl" (right‑to‑left)
            alert_p = soup.find('p', attrs={'dir': 'rtl'})

        if alert_p:
            message = alert_p.get_text(strip=True)
            # Clean emoji
            message = message.replace('🔹', '').strip()
        else:
            message = ""

        if not message:
            # Fallback: try to grab the iframe's parent text or any visible alert
            body_text = soup.body.get_text(separator=' ', strip=True)
            if 'flood' in body_text.lower() or 'سیلاب' in body_text:
                # Take the first 200 chars
                message = body_text[:200] + '...'
            else:
                message = "No active flood alert found. Please check PMD website manually."

        # Determine level from keywords (English & Urdu)
        msg_lower = message.lower()
        if any(w in msg_lower for w in ['high flood', 'high', 'شدید', 'خطرناک', 'انتباہ']):
            level = 'high'
        elif any(w in msg_lower for w in ['medium', 'moderate', 'متوسط', 'درمیانہ']):
            level = 'medium'
        else:
            level = 'low'

        alert_data = {
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open("alert.json", "w", encoding="utf-8") as f:
            json.dump(alert_data, f, ensure_ascii=False, indent=2)

        print(f"Success: level={level}, message={message[:100]}...")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        # Write a fallback so the site still works
        fallback = {
            "level": "low",
            "message": "Unable to fetch latest alert. Please visit PMD website.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open("alert.json", "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    extract_alert()
