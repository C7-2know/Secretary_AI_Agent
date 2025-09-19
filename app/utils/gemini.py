import os, httpx, re
from datetime import datetime, timedelta
from dateutil import parser as dateparser

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Simple, resilient NL extraction that uses Gemini if key exists; otherwise a regex fallback.
async def extract_entities(text: str, actor_tz: str = "America/New_York"):
    if GEMINI_API_KEY:
        try:
            # Gemini JSON response extraction using the REST API
            model = "gemini-1.5-flash"
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            prompt = f"""You are an information extractor. From the user's text, extract:
- participants: list of emails (guess simple ones like john@company.com if present)
- duration_min: integer (default 30 if missing)
- window: start and end in ISO8601 if dates are present; otherwise pick the next business day 09:00-12:00 in {actor_tz}
- location: string; default 'Google Meet'
Return ONLY valid JSON with keys: participants, duration_min, window, location.
User text: {text}
"""
            payload = {
                "contents": [ { "parts": [ { "text": prompt } ] } ]
            }
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                print("gemini response: ", data)
                # Naive extraction of first JSON block from the model output
                cand = data["candidates"][0]["content"]["parts"][0]["text"]
                import json as _json
                obj = _json.loads(cand)
                # Coerce datetimes
                if obj.get("window"):
                    obj["window"]["start"] = dateparser.parse(obj["window"]["start"]).isoformat()
                    obj["window"]["end"] = dateparser.parse(obj["window"]["end"]).isoformat()
                return obj
        except Exception:
            pass

    # Fallback: very naive regex-based extraction
    emails = re.findall(r"[\w\.-]+@[\w\.-]+", text)
    duration = 30
    if m := re.search(r"(\d+)\s*(min|minutes|m)\b", text, re.I):
        duration = int(m.group(1))
    # Window: next weekday morning
    base = datetime.utcnow() + timedelta(days=1)
    start = base.replace(hour=6, minute=0, second=0, microsecond=0)  # 9am Addis is 6 UTC
    end = base.replace(hour=9, minute=0, second=0, microsecond=0)
    return {
        "participants": emails,
        "duration_min": duration,
        "window": { "start": start.isoformat(), "end": end.isoformat() },
        "location": "Google Meet"
    }
