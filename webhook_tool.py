import os
import requests
def send_event_to_webhook(
    summary: str,
    description: str,  # <-- new field
    location: str,
    start: dict,
    end: dict
) -> str:
    """
    Sends a calendar event JSON to the webhook endpoint and returns the server's response.

    Parameters:
    ----------
    event : dict
        A structured calendar event containing:
            - summary: str — title of the event
            - description: str — optional details
            - location: str — optional event location
            - start: dict — {dateTime: str, timeZone: str}
            - end: dict — {dateTime: str, timeZone: str}
    
    Returns:
    -------
    str
        A message indicating whether the event was successfully sent,
        including the response text from the webhook or an error description.
        If successful, include 'Success!' in the message.
    """
    event = {
        "summary": summary,
        "description": description,
        "location": location,
        "start": start,
        "end": end
    }
    
    try:
        API_URL = os.getenv("WEBHOOK_API_URL")
    except Exception as e:
        return f"Failed to retrieve webhook from environment variables: {str(e)}"
    if not API_URL:
        return "Webhook API URL not set in environment variables."
    try:
        response = requests.post(API_URL, json=event, timeout=5)
        return f"Success! Webhook responded with: {response.text}"
    except requests.RequestException as e:
        return f"Failed to send event: {str(e)}"
