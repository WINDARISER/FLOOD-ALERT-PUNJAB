import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import re

# List of official flood alert pages to try
SOURCES = [
    {
        "name": "PDMA Punjab",
        "url": "https://pdma.gos.pk/flood-alert/",
        "selector": "div.alert-content, div.field--name-body, article, .flood-alert-text"  # common selectors
    },
    {
        "name": "PMD Flood Forecasting",
        "url": "http://www.pmd.gov.pk/FFD/cp/floodpage.asp",
        "selector": "body"  # fallback whole page text
    }
]

def extract_alert_from_page(url, selector, name):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; FloodAlertBot/1.0)"}
        response = requests.get(url, timeout=20, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find content with known selectors
        content_div = None
        for sel in selector.split(", "):
            content_div = soup.select_one(sel)
            if content_div:
                break

        if not content_div:
            # Fallback: get all text from body
            content_div = soup.body

        full_text = content_div.get_text(separator=" ", strip=True) if content_div else ""

        # Look for keywords like "flood warning", "high flood", "evacuate", etc.
        keywords = ["flood warning", "high flood", "evacuate", "low-lying", "flood alert",
                     "سیلاب", "انتباہ", "شدید سیلاب", "نشیبی", "خطرہ"]
        found = False
        message = ""
        level = "low"

        for line in full_text.split(". "):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                # Determine flood level
                if "high" in line_lower or "شدید" in line:
                    level = "high"
                elif "medium" in line_lower or "moderate" in line_lower:
                    level = "medium"
                else:
                    level = "low"
                # Clean up the line for message
                message = line.strip()
                if len(message) < 10:  # too short, maybe not the alert
                    continue
                found = True
                break

        if not found:
            # If no keyword found, take the first long line that looks like an alert
            lines = [l.strip() for l in full_text.split("\n") if len(l.strip()) > 30]
            if lines:
                message = lines[0]
                level = "low"
            else:
                message = f"No active alert found on {name}. Check directly."
                level = "low"

        return message, level, True
    except Exception as e:
        print(f"Error scraping {name}: {e}")
        return None, None, False

def main():
    alert_message = "No flood warning in effect. Stay alert."
    alert_level = "low"
    success = False

    # Try each source
    for source in SOURCES:
        msg, lvl, ok = extract_alert_from_page(source["url"], source["selector"], source["name"])
        if ok and msg:
            alert_message = msg
            alert_level = lvl
            success = True
            break

    if not success:
        # Fallback static message
        alert_message = "Unable to fetch latest alert. Please visit PDMA website."
        alert_level = "low"

    # Ensure message doesn't contain HTML
    alert_message = re.sub(r'<[^>]+>', '', alert_message)

    alert_data = {
        "level": alert_level,
        "message": alert_message,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    with open("alert.json", "w", encoding="utf-8") as f:
        json.dump(alert_data, f, ensure_ascii=False, indent=2)

    print(f"Alert updated: {alert_data['level']} - {alert_data['message'][:80]}...")

if __name__ == "__main__":
    main()
