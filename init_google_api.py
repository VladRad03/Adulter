from google_auth_oauthlib.flow import InstalledAppFlow
"""
Setting Up Google Calendar Integration for Your Agent

Make sure you have these three credentials from your Google Cloud project:

Environment Variable	Description
GOOGLE_CLIENT_ID	Your OAuth client ID
GOOGLE_CLIENT_SECRET	Your OAuth client secret
GOOGLE_REFRESH_TOKEN	The refresh token obtained via OAuth flow

Save these in your system environment variables or a .env file for your project.

then pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dotenv

"""


# Scopes: full calendar access
SCOPES = ["https://www.googleapis.com/auth/calendar"]

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",  # JSON you downloaded from Google
    SCOPES
)
creds = flow.run_local_server(port=0)

print("Access Token:", creds.token)
print("Refresh Token:", creds.refresh_token)
