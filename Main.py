from gmail_auth import authenticate_gmail_as_User, authenticate_gmail_with_service_account
from pubsub_notifications import setup_watch, listen_for_notifications_with_service_account
from utils import extract_email, get_header_value, decode_message
from outmethods import write_json_data_to_json
from openai_integration import call_openai_with_retry

from Email_processing import format_and_display_emails_table, read_emails
from Email_send_to import send_html_email, create_markdown_email_body
from Email_labels import get_all_labels, change_email_label
import config
import utils

from google.cloud import pubsub_v1

#Dirbtinis intelektas
from openai import OpenAI

#HTML formatavimas
import ssl

print(ssl.OPENSSL_VERSION)
ssl_context = ssl.create_default_context()
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

def process_new_emails(service, history_id):
    print(f"Processing new emails starting with historyId: {history_id}")

    try:
        # Call the Gmail API to list history
        response = service.users().history().list(userId='me', startHistoryId=history_id).execute() # Gauna sarašąs pagal historyId

        if 'historyId' not in response:
            print("No history records found in the response.")
            return
        
        new_messages = []
        processed_message_ids = set()
        if 'history' in response: 
            for record in response['history']:
                if 'messagesAdded' in record:
                    for message in record['messagesAdded']:

                        # Skip already processed messages
                        if message['message']['id'] in processed_message_ids:
                            print(f"Skipping already processed message ID: {message['message']['id']}")
                            continue

                        #Check if the message is with LABEL DRAFT
                        labels = message['message']['labelIds']
                        if 'DRAFT' in labels:
                            print(f"Skipping draft message ID: {message['message']['id']}")
                            continue

                        #Check if the message is with LABEL SENT
                        labels = message['message']['labelIds']
                        if 'SENT' in labels:
                            print(f"Skipping sent message ID: {message['message']['id']}")
                            continue

                        #Check if the message contains INBOX and UNREAD labels
                        full_message = service.users().messages().get(userId='me', id=message['message']['id']).execute()
                        labels = full_message.get('labelIds', [])
                        
                        if 'INBOX' in labels and 'UNREAD' in labels:
                            processed_message_ids.add(message['message']['id'])
                            new_messages.append(full_message)
                            print(f"Formuojama nauja užklausa į OPENAI")
                            json_data = message_handler(full_message)
                            write_to_OPENAI(json_data)

        if new_messages:
            print("\nNew Emails Received:")
            format_and_display_emails_table(new_messages)

    except Exception as e:
        print(f"Error processing new emails: {e}")

def message_handler(msg):
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

    json_data = message_to_json_data(ID, From, Date, Subject, body) 

    #pirmiausiai pasirasem sau i |JSON| faila
    write_json_data_to_json(json_data)

    return json_data

def message_to_json_data(ID, From, Date, Subject, body):

    JSON_Body = {
        "ID": ID,
        "From": From,
        "Date": Date,
        "Subject": Subject,
        "Body": body
    }

    return JSON_Body

def write_to_OPENAI(Json_Data):
    ID = Json_Data["ID"]
    From = Json_Data["From"]
    Date = Json_Data["Date"]
    Subject = Json_Data["Subject"]
    body = Json_Data["Body"]

    # Skip emails sent by the bot
    if "***REMOVED***" in From:
        print(f"Skipping email sent by the bot: {From}")
        return
    
    try:
        result = call_openai_with_retry(prompt=body, max_retries=3, wait_time=5)
        total_tokens = result.usage.total_tokens
        approx_cost_usd = float(total_tokens / 1000) * 0.03  # Assuming a cost of $0.03 per 1000 tokens
        response = result.choices[0].message.content

        email_body = create_markdown_email_body(total_tokens, approx_cost_usd, response)
        print(f"Siunciame laiska i {extract_email(From)} tema: {Subject}, ")

        User = config.get_global_user()   
        send_html_email(service=User, sender="***REMOVED***", recipient=extract_email(From), subject=Subject, html_content=email_body)
        change_email_label(User, ID, ["UNREAD"], ["Label_7380834898592995778"])

    except OpenAI.error.Timeout as e:
        print("Request timed out.")
    except OpenAI.error.RateLimitError as e:
        print("Rate limit exceeded.")


if __name__ == '__main__':
    # Authenticate and read emails
    User = authenticate_gmail_as_User()
    config.set_a_global_user(User)

    #read_emails(User)
    
    #get_all_labels(User)
    
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
    