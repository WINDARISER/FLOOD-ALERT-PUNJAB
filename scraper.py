import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone

# URL of the PDMA or PMD page with the flood forecast
URL = "https://ffd.pmd.gov.pk/"   # or the exact page you were on

def fetch_alert():
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FloodAlertBot/1.0)"}
        response = requests.get(URL, timeout=20, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the paragraph with the flood forecast
        alert_p = soup.find('p', class_='update-snippet')
        if not alert_p:
            # Fallback: try any p with font-weight-bold
            alert_p = soup.find('p', class_='font-weight-bold')

        message = ""
        level = "low"

        if alert_p:
            message = alert_p.get_text(strip=True)
            # Determine level from keywords
            msg_lower = message.lower()
            if any(w in msg_lower for w in ['high flood', 'high', 'شدید', 'خطرناک', 'انتباہ']):
                level = 'high'
            elif any(w in msg_lower for w in ['medium', 'moderate', 'متوسط']):
                level = 'medium'
            else:
                level = 'low'
        else:
            message = "No active flood alert found on PMD website. Please check manually."
            level = "low"

        # Clean message – remove HTML entities and trim
        message = message.replace('🔹', '').strip()

        alert_data = {
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open("alert.json", "w", encoding="utf-8") as f:
            json.dump(alert_data, f, ensure_ascii=False, indent=2)

        print(f"Alert updated: {level} - {message[:80]}...")

    except Exception as e:
        print(f"Error fetching alert: {e}")
        # Fallback: keep the last alert, or write a default
        fallback = {
            "level": "low",
            "message": "Unable to fetch latest alert. Please visit PMD website.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open("alert.json", "w", encoding="utf-8") as f:
            json.dump(fallback, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_alert()
