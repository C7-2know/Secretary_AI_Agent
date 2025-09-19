import os
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional
from dateutil import parser as dateparser

from app.models import IntentRequest, IntentResponse, IntentEntities, EventCreate, LogEntry
from app.utils import gemini, calendar_client, timeutil, sendgrid_client
from zoneinfo import ZoneInfo

load_dotenv()

API_KEY = os.getenv("APP_API_KEY", "devkey")
DEFAULT_TZ = os.getenv("APP_TIMEZONE", "Africa/Addis_Ababa")
FOLLOWUP_TO = os.getenv("FOLLOWUP_DEFAULT_RECIPIENT", "me@example.com")
# DIGEST_TO = os.getenv("DIGEST_DEFAULT_RECIPIENT", "me@example.com")

app = FastAPI(title="Executive Secretary AI Agent")

LOGS = []  # simple in-memory log list for demo

def auth_or_403(x_api_key: Optional[str]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

@app.post("/intent", response_model=IntentResponse)
async def parse_intent(req: IntentRequest, x_api_key: Optional[str] = Header(None)):
    auth_or_403(x_api_key)
    ent = await gemini.extract_entities(req.text, actor_tz=DEFAULT_TZ)
    print(f"Extracted entities: {ent}") 
    # Compute freebusy and slots
    window = ent.get("window") or {}
    start_iso = window.get("start")
    end_iso = window.get("end")

    # Validate and normalize time zone
    try:
        if not start_iso or not end_iso:
            print("Missing start_iso or end_iso, using default 24-hour window")  # Debug
            now = datetime.now(tz=ZoneInfo(DEFAULT_TZ))  # e.g., Africa/Nairobi
            start_iso = now.isoformat()
            end_iso = (now + timedelta(days=1)).isoformat()
        else:
            # Parse and ensure time zone
            start_dt = dateparser.parse(start_iso, ignoretz=False)
            end_dt = dateparser.parse(end_iso, ignoretz=False)
            if not start_dt.tzinfo or not end_dt.tzinfo:
                # Append DEFAULT_TZ if no time zone is specified
                tz = ZoneInfo(DEFAULT_TZ)
                start_dt = start_dt.replace(tzinfo=tz) if not start_dt.tzinfo else start_dt
                end_dt = end_dt.replace(tzinfo=tz) if not end_dt.tzinfo else end_dt
            if start_dt >= end_dt:
                raise ValueError("start_iso must be earlier than end_iso")
            start_iso = start_dt.isoformat()
            end_iso = end_dt.isoformat()
    except ValueError as e:
        print(f"Invalid ISO 8601 format: {str(e)}")  # Debug
        raise HTTPException(status_code=400, detail=f"Invalid ISO 8601 format or range: {str(e)}")

    print(f"Normalized start_iso: {start_iso}, end_iso: {end_iso}")  # Debug
    try:
        freebusy = calendar_client.find_freebusy(start_iso, end_iso)
        slots = timeutil.pick_slots(freebusy, ent.get("duration_min", 30))
        entities = IntentEntities(
            participants=ent.get("participants", []),
            duration_min=ent.get("duration_min", 30),
            window=None,
            location=ent.get("location", "Google Meet"),
        )
        res = IntentResponse(entities=entities, proposed_slots=slots, status="slots_proposed")
        LOGS.append(LogEntry(timestamp=datetime.utcnow(), actor="agent", action="parse_intent", payload=req.model_dump(), status="ok"))
        return res
    except ValueError as e:
        print(f"ValueError in find_freebusy: {str(e)}")  # Debug
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")
    except Exception as e:
        print(f"Calendar API error: {str(e)}")  # Debug
        raise HTTPException(status_code=500, detail=f"Calendar API error: {str(e)}")

@app.post("/events")
def create_event(evt: EventCreate, x_api_key: Optional[str] = Header(None)):
    auth_or_403(x_api_key)
    created = calendar_client.create_event(
        title=evt.title,
        attendees=evt.attendees,
        start_iso=evt.start.isoformat(),
        end_iso=evt.end.isoformat(),
        location=evt.location or "Google Meet"
    )
    LOGS.append(LogEntry(timestamp=datetime.utcnow(), actor="agent", action="create_event", payload={"id": created.get("id")}, status="ok"))
    return JSONResponse({"status": "created", "eventId": created.get("id"), "hangoutLink": created.get("hangoutLink")})

@app.post("/followups/run")
def run_followups(hours: int = 4, x_api_key: Optional[str] = Header(None)):
    auth_or_403(x_api_key)
    # For demo: send a generic follow-up
    html = "<p>Thanks for the meeting today. Summary and next steps are attached.</p>"
    sendgrid_client.send_email(FOLLOWUP_TO, "Thanks for today – recap & next steps", html)
    LOGS.append(LogEntry(timestamp=datetime.utcnow(), actor="agent", action="followups", payload={"hours": hours}, status="ok"))
    return {"status": "sent"}

@app.get("/logs")
def get_logs(x_api_key: Optional[str] = Header(None)):
    auth_or_403(x_api_key)
    return [l.model_dump() for l in LOGS]
