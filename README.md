# Executive Secretary AI Agent (FastAPI + Gemini + Google Calendar + SendGrid)

Backend-focused automation that parses natural-language scheduling requests, proposes slots,
creates Google Calendar events, and sends follow-up emails.

## Features
- `POST /intent` — parse NL text to extract participants, duration, windows, and location.
- `POST /events` — create a calendar event (Google Calendar API).
- `POST /followups/run` — generate & send follow-up emails for recent meetings.
- `GET /logs` — view recent actions.

## Quick Start (Local)
1. **Python** 3.10+
2. Create and configure `.env` (see `.env.example`)
3. Enable **Google Calendar API** and obtain OAuth credentials:
   - Create OAuth Client ID (Desktop) in Google Cloud Console.
   - Put JSON as `credentials.json` in `./secrets/`.
   - First run will open a browser to authorize and create `token.json` under `./secrets/`.
4. Install deps and run:
   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
5. Test with curl/Postman:
   ```bash
   curl -X POST http://localhost:8000/intent -H "x-api-key: devkey" -H "Content-Type: application/json" -d '{"text":"Schedule 30m with john@co.com next tue morning on Google Meet"}'
   ```

## Folder Structure
```
app/
  main.py
  models.py
  utils/
    gemini.py
    calendar_client.py
    sendgrid_client.py
    timeutil.py
secrets/
  credentials.json (from Google Console)
  token.json (created on first OAuth flow)
.env (environment variables)
```

## Notes
- Gemini is used for *entity extraction* from free-form text 
- Google Calendar requires OAuth 2.0; place `credentials.json` in `./secrets/` and authorize once.
- SendGrid for emails; 

