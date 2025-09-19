import os
from datetime import datetime, timedelta
from typing import List, Tuple
from dateutil import parser as dateparser

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

SECRETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), '..', 'secrets')
CREDENTIALS_FILE = os.path.join(SECRETS_DIR, 'credentials.json')
TOKEN_FILE = os.path.join(SECRETS_DIR, 'token.json')

def _get_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    service = build('calendar', 'v3', credentials=creds)
    return service

def find_freebusy(window_start_iso: str, window_end_iso: str, calendar_id: str = 'primary') -> List[Tuple[datetime, datetime]]:
    service = _get_service()
    body = {
        "timeMin": window_start_iso,
        "timeMax": window_end_iso,
        "items": [{"id": calendar_id}]
    }
    fb = service.freebusy().query(body=body).execute()
    busy = fb['calendars'][calendar_id].get('busy', [])
    ws = dateparser.parse(window_start_iso)
    we = dateparser.parse(window_end_iso)
    # Available intervals by subtracting busy blocks
    blocks = [(dateparser.parse(b['start']), dateparser.parse(b['end'])) for b in busy]
    blocks.sort()
    avail = []
    cur = ws
    for bstart, bend in blocks:
        if bstart > cur:
            avail.append((cur, bstart))
        cur = max(cur, bend)
    if cur < we:
        avail.append((cur, we))
    return avail

def create_event(title: str, attendees: List[str], start_iso: str, end_iso: str, location: str = "Google Meet", calendar_id: str = 'primary') -> dict:
    service = _get_service()
    event = {
        'summary': title,
        'location': location,
        'start': { 'dateTime': start_iso },
        'end': { 'dateTime': end_iso },
        'attendees': [ {'email': a} for a in attendees ],
        'conferenceData': { 'createRequest': { 'requestId': title.replace(' ', '-') } }
    }
    created = service.events().insert(calendarId=calendar_id, body=event, conferenceDataVersion=1).execute()
    return created
