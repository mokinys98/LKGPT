import os
import base64
import json
from tabulate import tabulate
from Helpers.utils import decode_message, extract_domain, get_header_value

def read_emails(service):
    # Get the list of messages
    results = service.users().messages().list(userId='me', maxResults=10).execute()
    messages = []
    labels = results.get("labels", [])

    if not labels:
        print("No labels found.")
    else:
        print("Labels:")
        for label in labels:
            print(label["name"])

    # Fetch each message's details
    for msg in results.get('messages', []):
        full_message = service.users().messages().get(userId='me', id=msg['id']).execute()
        messages.append(full_message)

    # Display the messages in a table
    format_and_display_emails_table(messages)   


def format_and_display_emails_table(messages):
    """
    Formats and displays email details in a single-line table with an additional domain column: DATE, Sender, Subject, Domain.

    Args:
        messages (list): List of email message objects retrieved via the Gmail API.
    """
    # Prepare data for the table
    table_data = []
    for msg in messages:
        # Extract headers
        headers = msg['payload']['headers']
        
        # Initialize variables
        date = "N/A"
        sender = "N/A"
        subject = "N/A"
        domain = "N/A"
        
        # Find the required headers
        for header in headers:
            if header['name'] == 'Date':
                date = header['value']
            elif header['name'] == 'From':
                sender = header['value']
            elif header['name'] == 'Subject':
                subject = header['value']
        
        # Extract the domain from the sender's email
        if sender != "N/A" and "<" in sender:
            # Extract email from "Name <email@example.com>" format
            sender_email = sender.split("<")[1].strip(">")
        else:
            sender_email = sender
        domain = extract_domain(sender_email)
        
        # Add data as a single row
        table_data.append([date, sender, domain, subject])

    # Print the table with one message per line
    print(tabulate(table_data, headers=["DATE", "Sender", "Domain", "Subject"], tablefmt="grid"))
