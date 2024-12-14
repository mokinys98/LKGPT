#Gmail API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request 
from google.oauth2 import service_account as sa_credentials
from google.cloud import pubsub_v1
#Bibliotekos
import os
import base64
import json
import time
import re
#Dirbtinis intelektas
from openai import OpenAI
#Lentele CLI
from tabulate import tabulate
#Dotenv API raktams
from dotenv import find_dotenv, load_dotenv
#HTML formatavimas
import markdown2
from email.mime.text import MIMEText
import base64


load_dotenv(find_dotenv())
# Replace with your OpenAI API key
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

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

def decode_message(encoded_data):
    decoded_bytes = base64.urlsafe_b64decode(encoded_data)
    return decoded_bytes.decode('utf-8')
def save_message_to_file(msg):
    headers = msg['payload']['headers']
    snippet = msg['snippet']
    body_encoded = msg['payload']['parts'][0]['body']['data']  # Base64-encoded body
    body = decode_message(body_encoded)  # Decode the body content

    # Prepare content to save
    content = f"Headers: {headers}\n\nSnippet: {snippet}\n\nBody (text/plain):\n{body}\n"

    # Save to file
    with open("email_message.txt", "w", encoding="utf-8") as file:
        file.write(content)
    print("Message saved to email_message.txt")
def save_message_to_file_as_json(msg):
    headers = msg['payload']['headers']
    snippet = msg['snippet']
    body_encoded = msg['payload']['parts'][0]['body']['data']  # Base64-encoded body
    body = decode_message(body_encoded)  # Decode the body content

    # Convert headers to JSON format
    headers_json = json.dumps(headers, indent=4)

    # Prepare content to save
    content = f"Headers (JSON):\n{headers_json}\n\nSnippet: {snippet}\n\nBody (text/plain):\n{body}\n"

    # Save to file
    with open("email_message.json", "w", encoding="utf-8") as file:
        file.write(content)
    print("Message saved to email_message.json")
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
def extract_domain(sender_email):
    """
    Extracts the domain from the sender's email address.
    Args:
        sender_email (str): The sender's email address.
    Returns:
        str: The domain of the email.
    """
    if "@" in sender_email:
        return sender_email.split("@")[1]
    return "N/A"
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

def setup_watch(service, topic_name):
    global last_history_id
    request = {
        "labelIds": ["INBOX"],  # Watch only the inbox
        "topicName": topic_name  # Pub/Sub topic name
    }
    response = service.users().watch(userId='me', body=request).execute()
    last_history_id = response.get('historyId')
    print("Watch setup successful:", response)
    return response
def create_callback(service):
    def callback(message):
        global last_history_id

        print(f"Received Pub/Sub message: {message.data.decode('utf-8')}")
        message.ack()  # Acknowledge the message

        notification = json.loads(message.data.decode('utf-8'))
        pubsub_history_id = int(notification['historyId'])

        if pubsub_history_id <= int(last_history_id):
            print(f"Ignoring older or already processed historyId: {pubsub_history_id}")
            return

        # Process new emails starting from the last_history_id
        process_new_emails(service, last_history_id)
    return callback

def listen_for_notifications_with_service_account(subscription_name, key_path, service):
    
    credentials = sa_credentials.Credentials.from_service_account_file(key_path)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    subscription_path = subscriber.subscription_path('skilful-mercury-444620-s6', subscription_name)

    # Pass the service object to the callback
    callback = create_callback(service)

    print(f"Listening for messages on {subscription_path}...")
    subscriber.subscribe(subscription_path, callback=callback)

    while True:
        time.sleep(5)
def process_new_emails(service, history_id):
    print(f"Processing new emails starting with historyId: {history_id}")

    try:
        # Call the Gmail API to list history
        response = service.users().history().list(userId='me', startHistoryId=history_id).execute() # Gauna sarašąs pagal historyId

        if 'historyId' not in response:
            print("No history records found in the response.")
            return
        
        new_messages = []
        if 'history' in response: # Jei response'je yra history
            for record in response['history']:
                if 'messages' in record:
                    for message in record['messages']:
                        full_message = service.users().messages().get(userId='me', id=message['id']).execute()
                        new_messages.append(full_message)
                        write_to_OPENAI(full_message)

        if new_messages:
            print("\nNew Emails Received:")
            format_and_display_emails_table(new_messages)
            update_last_history_id(response['historyId'])
        else:
            print("No new emails found in the history records.")
    except Exception as e:
        print(f"Error processing new emails: {e}")



def update_last_history_id(new_value):
    global last_history_id
    last_history_id = new_value
def set_a_global_user(user):
    global global_user
    global_user = user

def create_OPENAI_User_message(text):
    return {
        "role": "user",
        "content": text
    }
def create_OPENAI_Assistant_message(text):
    return {
        "role": "assistant",
        "content": text
    }
def get_header_value(headers, target_name):
    """
    Fetch the value of a specific header by name.

    Args:
        headers (list): List of header objects from the email payload.
        target_name (str): The name of the header to fetch (e.g., "Date", "From").

    Returns:
        str: The value of the header if found, else "N/A".
    """
    for header in headers:
        if header['name'].lower() == target_name.lower():  # Case-insensitive match
            return header['value']
    return "N/A"  # Return a default value if the header is not found

def extract_email(recipient):
    """
    Extracts the email address from a recipient string.

    Args:
        recipient (str): The recipient string, e.g., "Name <email@example.com>" or "email@example.com".

    Returns:
        str: The extracted email address, or None if invalid.
    """
    email_regex = r"<([^>]+)>"  # Match email inside angle brackets
    if "<" in recipient and ">" in recipient:  # If name and email format
        match = re.search(email_regex, recipient)
        if match:
            return match.group(1).strip()  # Return the email inside angle brackets
    else:
        # Assume it's just the email if no angle brackets
        return recipient.strip()

    return None  # Return None if invalid

def write_to_OPENAI(msg):

    ID = msg['id']
    headers = msg['payload']['headers']

    # Dynamically fetch headers
    Date = get_header_value(headers, "Date")
    From = get_header_value(headers, "From")
    Subject = get_header_value(headers, "Subject")
 
    # Decode the body dynamically
    if 'parts' in msg['payload']:
        # Handle multipart emails
        for part in msg['payload']['parts']:
            if part['mimeType'] == 'text/html':  # Prioritize HTML
                body_encoded = part['body']['data']
                body = decode_message(body_encoded)
                break
            elif part['mimeType'] == 'text/plain':  # Fallback to plain text
                body_encoded = part['body']['data']
                body = decode_message(body_encoded)
    else:
        # Handle single-part emails
        if 'body' in msg['payload'] and 'data' in msg['payload']['body']:
            body_encoded = msg['payload']['body']['data']
            body = decode_message(body_encoded)

    # Default fallback if no body is found
    body = body if 'body' in locals() else "No content found"

    #pirmiausiai pasirasem sau i |JSON| faila
    write_to_json(ID, From, Date, Subject, body)


    # OpenAI API rašymas
    try:
        completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": body
        }
            ]
        )
       
        total_tokens = completion.usage.total_tokens
        approx_cost_usd = float(total_tokens / 1000) * 0.03  # Assuming a cost of $0.03 per 1000 tokens
        response = completion.choices[0].message.content

        email_body = create_markdown_email_body(total_tokens, approx_cost_usd, response)
        send_html_email(global_user, "***REMOVED***", From, Subject, email_body)
        change_email_label(global_user, ID, ["UNREAD"], ["Executed"])

    except Exception as e:
        print(f"Error sending email: {e}")


# Funkcija sukurti el. laiško turinį Markdown formatu ir konvertuoti į HTML
def create_markdown_email_body(total_tokens, approx_cost_usd, response):
    """
    Sukuria el. laiško turinį Markdown formatu, konvertuoja jį į HTML.
    Args:
        total_tokens (int): Naudotų tokenų skaičius.
        approx_cost_usd (float): Apskaičiuota kaina USD.
        response (str): API sugeneruotas atsakymas.

    Returns:
        str: HTML turinys paruoštas siuntimui.
    """
    # Markdown turinys
    markdown_body = f"""
# API Atsakymo Informacija

- **Naudoti tokenai**: {total_tokens}
- **Apskaičiuota kaina**: ${approx_cost_usd:.5f}

---

## Atsakymas

{response}
    """
    # Konvertuojame Markdown į HTML
    return markdown2.markdown(markdown_body)

# Funkcija siųsti HTML el. laišką
def send_html_email(service, sender, recipient, subject, html_content):
    """
    Siunčia HTML formatu paruoštą el. laišką per Gmail API.

    Args:
        service: Autorizuotas Gmail API paslaugų objektas.
        sender (str): Siuntėjo el. pašto adresas.
        recipient (str): Gavėjo el. pašto adresas.
        subject (str): Laiško tema.
        html_content (str): Laiško turinys HTML formatu.

    Returns:
        dict: Gmail API atsakymas.
    """
    # Sukurkite MIMEText objektą su HTML turiniu
    message = MIMEText(html_content, "html")
    message["to"] = extract_email(recipient)
    message["from"] = sender
    message["subject"] = subject

    # Kodavimas į Base64, kaip reikalauja Gmail API
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    body = {"raw": raw_message}

    try:
        # Siųskite el. laišką
        sent_message = service.users().messages().send(userId="me", body=body).execute()
        print(f"El. laiškas sėkmingai išsiųstas! Žinutės ID: {sent_message['id']}")
        return sent_message
    except Exception as e:
        print(f"Klaida siunčiant el. laišką: {e}")
        return None


def create_message(sender, to, subject, body_text):
    message = f"From: {sender}\nTo: {to}\nSubject: {subject}\n\n{body_text}"
    raw_message = base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')
    return {'raw': raw_message}

def send_email(service, sender, to, subject, body_text):
    #Sukurs laisko turini
    message = create_message(sender, to, subject, body_text)
    #issiunia laiska
    sent_message = service.users().messages().send(userId='me', body=message).execute()
    print(f"Message sent: {sent_message['id']}")

def write_to_json(ID, From, Date, Subject, body):

    JSON_Body = {
        "ID": ID,
        "From": From,
        "Date": Date,
        "Subject": Subject,
        "Body": body
    }

    # Folder and file paths
    folder_name = "emails"
    file_name = Subject +".json"
    file_path = os.path.join(folder_name, file_name)

    # Ensure the folder exists
    os.makedirs(folder_name, exist_ok=True)

    # Step 1: Check if the file exists and load its content
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = []  # Default to an empty list if the file is empty or invalid JSON
    else:
        existing_data = []

    # Step 2: Ensure existing data is a list (for appending purposes)
    if not isinstance(existing_data, list):
        raise ValueError("The existing JSON content must be a list to append new items.")

    # Step 3: Append the new data
    existing_data.append(JSON_Body)

    # Step 4: Write the updated data back to the file
    with open(file_path, 'w') as file:
        json.dump(existing_data, file, indent=4)
               

def get_label_id(service, label_name):
    """
    Fetches the label ID for the given label name.

    Args:
        service: Authorized Gmail API service instance.
        label_name (str): The name of the label to fetch.

    Returns:
        str: The label ID, or None if not found.
    """
    try:
        labels = service.users().labels().list(userId="me").execute().get("labels", [])
        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]
    except Exception as e:
        print(f"Error fetching label ID: {e}")
    return None

def change_email_label(service, message_id, remove_labels, add_labels):
    """
    Modifies the labels of an email.

    Args:
        service: Authorized Gmail API service instance.
        message_id (str): The ID of the email to modify.
        remove_labels (list): Labels to remove from the email.
        add_labels (list): Labels to add to the email.

    Returns:
        dict: The Gmail API response.
    """
    try:
        body = {
            "removeLabelIds": remove_labels,
            "addLabelIds": add_labels,
        }
        result = service.users().messages().modify(userId="me", id=message_id, body=body).execute()
        print(f"Labels updated for message ID: {message_id}")
        return result
    except Exception as e:
        print(f"Error modifying email labels: {e}")
        return None

if __name__ == '__main__':
    # Authenticate and read emails
    User = authenticate_gmail_as_User()
    set_a_global_user(User)

    '''
    read_emails(User)
    '''
    
    # Path to the service account key file
    service_account_key_path = "C:/Users/Auris/Python/LKGPT/skilful-mercury-444620-s6-2526f9ed3422.json"
    # Authenticate Gmail API
    service_account = authenticate_gmail_with_service_account(service_account_key_path)

    # Example usage:
    setup_watch(User, "projects/skilful-mercury-444620-s6/topics/LK-DI")
    # Start listening for notifications
    listen_for_notifications_with_service_account(
        subscription_name="LK-DI-sub",
        key_path=service_account_key_path,
        service=User
    )
    