from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 
from google.oauth2 import service_account as sa_credentials
import os


# Scopes for reading Gmail messages
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail_as_User():
    """
    Authenticate the user and return a Gmail API service instance.
    
    Returns:
        service: An authorized Gmail API service instance.
    """
    creds = None
    # Check if token.json exists for stored credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for future runs
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Build the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    return service

def authenticate_gmail_with_service_account(key_path):
    """
    Authenticate using a service account and return a Gmail API service instance.
    
    Args:
        key_path: Path to the service account key file (JSON).
    
    Returns:
        service: An authorized Gmail API service instance.
    """
    credentials = sa_credentials.Credentials.from_service_account_file(
        key_path, scopes=['https://www.googleapis.com/auth/gmail.modify']
    )

    service = build('gmail', 'v1', credentials=credentials)
    return service
