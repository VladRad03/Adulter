import os
from typing import Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env
def send_event_to_google_calendar(
    summary: str,
    description: str,  # <-- new field
    location: str,
    start: dict,
    end: dict
):

    """
    Creates a Google Calendar event using OAuth credentials and refresh token.

    Parameters:
    - summary: str → Event title
    - description: str → Event description
    - location: str → Event location
    - start: dict → {"dateTime": "YYYY-MM-DDTHH:MM:SS", "timeZone": "Your/Timezone"}
    - end: dict → Same format as start

    Returns:
    - Success/failure message with Google Calendar event link
    """
    # print(os.getenv("GOOGLE_REFRESH_TOKEN"))
    # print(os.getenv("GOOGLE_CLIENT_ID"))
    # print(os.getenv("GOOGLE_CLIENT_SECRET"))
    # print("https://oauth2.googleapis.com/token")
    creds = Credentials(
        None,  # access token is automatically refreshed
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    try:
        service = build("calendar", "v3", credentials=creds)

        event_body = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": start,
            "end": end
        }

        event_result = service.events().insert(
            calendarId="primary",
            body=event_body
        ).execute()

        return f"✅ Success! Event created: {event_result.get('htmlLink')}"

    except Exception as e:
        return f"❌ Failed to create Google Calendar event: {str(e)}"

def get_calendar_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,       # RFC3339 timestamp, e.g. "2025-09-20T00:00:00-07:00"
    time_max: Optional[str] = None,       # RFC3339 timestamp
    query: Optional[str] = None,          # Keyword to search in summary/description
    max_results: int = 10 
):
    """
    Lists events from a Google Calendar with optional filters.

    Parameters:
    - calendar_id: str → the calendar to query (default "primary")
    - time_min: str → RFC3339 timestamp, e.g., "2025-09-20T00:00:00-07:00"
    - time_max: str → RFC3339 timestamp
    - query: str → keyword to search in summary/description
    - max_results: int → maximum number of events to return

    Returns:
    - List of matching events
    """
    
    creds = Credentials(
        None,
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    service = build("calendar", "v3", credentials=creds)

    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        q=query,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get("items", [])
    return events

def delete_event_from_google_calendar(event_id: str, calendar_id :str = "primary"):
    """
    Deletes a Google Calendar event by event ID.

    Parameters:
    - event_id: str → The unique ID of the event to delete
    - calendar_id: str → The calendar ID (default is 'primary')

    Returns:
    - Success/failure message
    """

    creds = Credentials(
        None,  # access token auto-refreshed
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token"
    )

    try:
        service = build("calendar", "v3", credentials=creds)
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return f"✅ Success! Event {event_id} deleted."

    except Exception as e:
        return f"❌ Failed to delete event {event_id}: {str(e)}"