import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 
from google.oauth2 import service_account as sa_credentials
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
import os
import sys
import json

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# Scopes for reading Gmail messages
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def refresh_gmail_token():
    flow = InstalledAppFlow.from_client_secrets_file('Creds/credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    # Save the credentials to token.json
    with open('Creds/token.json', 'w') as token:
        token.write(creds.to_json())
    return creds

def authenticate_gmail_as_User():
    """
    Authenticate the user and return a Gmail API service instance.
    
    Returns:
        service: An authorized Gmail API service instance.
    """
    creds = None
    # Check if token.json exists for stored credentials
    if os.path.exists('Creds/token.json'):
        creds = Credentials.from_authorized_user_file('Creds/token.json', SCOPES)

    # If there are no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Initialize the flow using the client_secrets.json
            flow = InstalledAppFlow.from_client_secrets_file('Creds/credentials.json', SCOPES)

            # Explicitly set the redirect_uri
            flow.redirect_uri = 'http://localhost:8080'

            # Generate the authorization URL
            auth_url, _ = flow.authorization_url(prompt='consent')
            print(f"Please visit this URL to authorize the application: {auth_url}")

            # Ask the user to input the authorization code
            code = input("Enter the authorization code: ")

            # Fetch the token using the authorization code
            flow.fetch_token(code=code)
            creds = flow.credentials

        # Save the credentials for future runs
        with open('Creds/token.json', 'w') as token:
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


if __name__ == "__main__":
    User = authenticate_gmail_as_User()
    config.set_a_global_user(User)

    #refresh_gmail_token()

    # File to encode
    input_file = "Creds/token.json"
    output_file = "token_base64.txt"

    # Read the file in binary mode
    with open(input_file, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")

    # Save the Base64 string to a file
    with open(output_file, "w") as file:
        file.write(encoded)

    print("Base64 encoding saved to token_base64.txt")