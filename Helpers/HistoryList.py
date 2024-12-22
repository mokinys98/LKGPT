from utils import extract_email, get_header_value, decode_message

import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Emails.Email_processing import format_and_display_emails_table, read_emails
from Emails.Email_send_to import send_html_email, create_markdown_email_body, create_greeting_email
from Emails.Email_labels import get_all_labels, change_email_label
from Emails.Gmail_auth import authenticate_gmail_as_User
from sql.sqldb import send_email_info
from googleapiclient.errors import HttpError

import config
from Main import message_handler, decode_parts, message_to_json_data

#Gets a History list of emails from Gmail, from specific history id
def get_history_list(service, history_id):
    try:
        # Call the Gmail API to list history
        response = service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded']
            ).execute() # Gauna sarašąs pagal historyId

        if 'historyId' not in response:
            print("No history records found in the response.")
            return
                    
        for record in response['history']:
                if 'messagesAdded' in record:
                    for message in record['messagesAdded']:

                        history_id = record['id']
                        try:
                            full_message = service.users().messages().get(userId='me', id=message['message']['id']).execute()
                            json_data = message_handler(full_message)
                            send_email_info(history_id, json_data)
                        except HttpError as e:
                            if e.reason == 'Requested entity was not found.':
                                print(f"Email with History_ID: {history_id} not found")
                                # Handle the duplicate key case (e.g., skip, update, or log)
                            else:
                                # Re-raise the exception if it's a different APIError
                                raise

    except Exception as e:
        print(f"An error occurred: {e}")
        return

def One_Email_Data(history, message):
    # Fetch full message data using Gmail API
    payload = message.get('payload', {})

    ID = message['id']
    ThreadId = message['threadId']
    headers = payload.get('headers', [])

    # Dynamically fetch headers
    Date = get_header_value(headers, "Date")
    From = get_header_value(headers, "From")
    Subject = get_header_value(headers, "Subject")
    In_Reply_To = get_header_value(headers, "In-Reply-To")
    References = get_header_value(headers, "References")

    # Outlook conversion headers
    Message_ID = get_header_value(headers, "Message-ID")
    Thread_Index = get_header_value(headers, "Thread-Index")
    Thread_Topic = get_header_value(headers, "Thread-Topic")

    # Decode the body and attachments dynamically
    body, attachments = decode_parts(payload, decode_message)

    # Default fallback if no body is found
    body = body if body else "No content found"

    # Default fallback if no body is found
    body = body if 'body' in locals() else "No content found"
    
    # Prepare JSON data from the message
    json_data = message_to_json_data(ID=ID, ThreadID=ThreadId, From=From, Date=Date, Subject=Subject, body=body, In_Reply_To=In_Reply_To, References=References, 
                                     Message_ID=Message_ID, Thread_Index=Thread_Index, Thread_Topic=Thread_Topic)

    # Output attachments if needed
    if attachments:
        json_data['attachments'] = attachments 

    if history:
        json_data['historyId'] = history

    return json_data


if __name__ == '__main__':
    
    User = authenticate_gmail_as_User()
    config.set_a_global_user(User)

    get_history_list(User, 25909)