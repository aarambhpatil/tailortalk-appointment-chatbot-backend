import os
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from dateutil import parser
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar']
SERVICE_ACCOUNT_FILE = 'dev-lambda-465104-n1-91f9fc3b438c.json'
CALENDAR_ID = 'e90c1c573eefd74578635d756e513049550789b44b953f84b6012b8600f4e532@group.calendar.google.com'

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

def format_time_for_google_api(time_str: str) -> str:
    ist_timezone = pytz.timezone('Asia/Kolkata')
    dt = parser.parse(time_str)
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        dt_aware = ist_timezone.localize(dt)
    else:
        dt_aware = dt.astimezone(ist_timezone)
    return dt_aware.isoformat()

class CheckAvailabilityInput(BaseModel):
    start_time: str = Field(description="The start of the time range to check for availability, in ISO 8601 format.")
    end_time: str = Field(description="The end of the time range to check for availability, in ISO 8601 format.")

@tool("check_calendar_availability", args_schema=CheckAvailabilityInput)
def check_calendar_availability(start_time: str, end_time: str) -> str:
    """Checks for free slots in the Google Calendar within a given time range."""
    try:
        formatted_start_time = format_time_for_google_api(start_time)
        formatted_end_time = format_time_for_google_api(end_time)
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=formatted_start_time,
            timeMax=formatted_end_time,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return f"The calendar is completely free between {start_time} and {end_time}."
        busy_slots = [(e['start'].get('dateTime', e['start'].get('date')), e['end'].get('dateTime', e['end'].get('date'))) for e in events]
        return f"The following time slots are busy: {busy_slots}. All other times are free."
    except Exception as e:
        return f"An error occurred: {e}"

class CreateEventInput(BaseModel):
    summary: str = Field(description="The title or summary of the event.")
    start_time: str = Field(description="The start time of the event in ISO 8601 format.")
    end_time: str = Field(description="The end time of the event in ISO 8601 format.")
    description: str = Field(default="", description="A brief description of the event.")

@tool("create_calendar_event", args_schema=CreateEventInput)
def create_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> str:
    """Creates a new event in the Google Calendar"""
    formatted_start_time = format_time_for_google_api(start_time)
    formatted_end_time = format_time_for_google_api(end_time)
    event = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': formatted_start_time},
        'end': {'dateTime': formatted_end_time},
    }
    try:
        created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
        return f"Success! Event created. View it here: {created_event.get('htmlLink')}"
    except Exception as e:
        return f"An error occurred: {e}"