import os
import uvicorn
import ssl
import config

from gmail_auth import authenticate_gmail_as_User, authenticate_gmail_with_service_account
from pubsub_notifications import setup_watch, listen_for_notifications_with_service_account
from utils import extract_email, get_header_value, decode_message
from outmethods import write_json_data_to_json
from openai_integration import call_openai_with_retry

from Email_processing import format_and_display_emails_table, read_emails
from Email_send_to import send_html_email, create_markdown_email_body, create_greeting_email
from Email_labels import get_all_labels, change_email_label

from sqldb import update_sender_statistics, sender_exists, create_entry
from google.cloud import pubsub_v1

from fastapi import FastAPI, Request
from APIroutes import router
from fastapi.templating import Jinja2Templates
from openai import OpenAI

print(ssl.OPENSSL_VERSION)
ssl_context = ssl.create_default_context()
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

app = FastAPI(
    title="Email Processing API",
    description="API for processing and sending emails",
    version="1.0.0",
    openapi_url="/openapi.json",)


# Initialize templates directory
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "HTMLtemplates"))

app.include_router(router)

@app.get("/")
async def root(request: Request):
    # Render a placeholder homepage
    return templates.TemplateResponse("home.html", {"request": request})
    

def process_new_emails(service, history_id):
    print(f"Processing new emails starting with historyId: {history_id}")

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
        
        new_messages = []
        processed_message_ids = set()
        if 'history' in response: 
            for record in response['history']:
                if 'messagesAdded' in record:
                    for message in record['messagesAdded']:

                        # Skip already processed messages or messages with DRAFT or SENT labels
                        if message['message']['id'] in processed_message_ids or 'DRAFT' in message['message']['labelIds'] or 'SENT' in message['message']['labelIds']:
                            print(f"Skipping already processed, draft or sent message ID: {message['message']['id']}")
                            continue

                        #Check if the message contains INBOX and UNREAD labels
                        full_message = service.users().messages().get(userId='me', id=message['message']['id']).execute()
                        labels = full_message.get('labelIds', [])

                        # #Checks if Subject is Saskaita
                        # if 'Saskaita' in full_message['subject']:
                        #     send_bill_email(service, full_message)


                        headers = full_message['payload']['headers']
                        From = get_header_value(headers, "From")
                        sender_email = extract_email(From)
                        bool = sender_exists(sender_email)
                        if bool:
                            print(f"Sender exists in the database: {sender_email}")
                        else:
                            print(f"Sender does not exist in the database: {sender_email}")
                            email_body = create_greeting_email()
                            try:
                                User = config.get_global_user()   
                                send_html_email(service=User, sender="***REMOVED***", recipient=extract_email(sender_email), subject="Sveiki!", html_content=email_body)
                                create_entry(sender_email)
                                continue
                            except Exception as e:
                                print(f"Error sending email: {e}")
                                continue
                        
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
    ThreadId = msg['threadId']
    headers = msg['payload']['headers']

    # Dynamically fetch headers
    Date = get_header_value(headers, "Date")
    From = get_header_value(headers, "From")
    Subject = get_header_value(headers, "Subject")
    In_Reply_To = get_header_value(headers, "In-Reply-To")
    References = get_header_value(headers, "References")

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

    # Prepare JSON data from the message
    json_data = message_to_json_data(ID=ID, ThreadID=ThreadId, From=From, Date=Date, Subject=Subject, body=body, In_Reply_To=In_Reply_To, References=References) 

    #pirmiausiai pasirasem sau i |JSON| faila
    write_json_data_to_json(json_data)

    return json_data

def message_to_json_data(ID, From, Date, Subject, body, ThreadID = None, In_Reply_To=None, References=None):

    JSON_Body = {
        "ID": ID,
        "ThreadID": ThreadID,
        "In_Reply_To": In_Reply_To,
        "References": References,
        "From": From,
        "Date": Date,
        "Subject": Subject,
        "Body": body
    }

    return JSON_Body

def write_to_OPENAI(Json_Data):
    ID = Json_Data["ID"]
    ThreadID = Json_Data["ThreadID"]
    In_Reply_To = Json_Data["In_Reply_To"]
    References = Json_Data["References"]
    From = Json_Data["From"]
    Date = Json_Data["Date"]
    Subject = Json_Data["Subject"]
    body = Json_Data["Body"]
    
    
    try:
        result = call_openai_with_retry(prompt=body, max_retries=3, wait_time=5)
        total_tokens = result.usage.total_tokens
        approx_cost_usd = float(total_tokens / 1000) * 0.03  # Assuming a cost of $0.03 per 1000 tokens
        response = result.choices[0].message.content

        email_body = create_markdown_email_body(total_tokens, approx_cost_usd, response)
        print(f"Siunciame laiska i {extract_email(From)} tema: {Subject}, ")

        try:
            User = config.get_global_user()   
            send_html_email(service=User, sender="***REMOVED***", recipient=extract_email(From), subject=Subject, html_content=email_body,
                             thread_id=ThreadID, in_reply_to=In_Reply_To, references=References)
            change_email_label(User, ID, ["UNREAD"], ["Label_7380834898592995778"])
            update_sender_statistics(sender_email=extract_email(From), cost=approx_cost_usd)

            # ~~~~~~~~~~~ JSON ~~~~~~~~~~~
            # Prepare JSON data from the message
            json_data = message_to_json_data(ID=ID, ThreadID=ThreadID, From="***REMOVED***", Date=Date, Subject=Subject, body=email_body, In_Reply_To=In_Reply_To, References=References) 
            #pirmiausiai pasirasem sau i |JSON| faila
            write_json_data_to_json(json_data)

        except Exception as e:
            print(f"Error sending email: {e}")

    except OpenAI.error.Timeout as e:
        print("Request timed out.")
    except OpenAI.error.RateLimitError as e:
        print("Rate limit exceeded.")


def test(User):
    response = User.users().history().list(
            userId='me',
            startHistoryId=17893,
            historyTypes=['messageAdded']
            ).execute() # Gauna sarašąs pagal historyId
    Meg_arr = []
    for record in response['history']:
        for message in record['messagesAdded']:
            message['message']['id']
            #print(message['message']['id'])
            msg = User.users().messages().get(userId='me', id=message['message']['id']).execute()
            Meg_arr.append(msg)
            

    #Create a function to evaluate and compare the headers of all mesages
    def extract_headers(messages):
        headers_dict = {}
        for msg in messages:
            for header in msg['payload']['headers']:
                if header['name'] not in headers_dict:
                    headers_dict[header['name']] = []
                headers_dict[header['name']].append(header['value'])
    
        return headers_dict
    
    #check if the sender is aurimas.zvirblys@mil.lt
    def check_sender(messages, target_email="Aurimas.Zvirblys@mil.lt"):
        matching_messages = []
        for msg in messages:
            headers = msg['payload']['headers']
            From = get_header_value(headers, "From")
            sender_email = extract_email(From)
            if sender_email == target_email:
                matching_messages.append(msg)
        return matching_messages

    #matching_messages = check_sender(Meg_arr)
    #print(Meg_arr)

if __name__ == '__main__':
    #Runs uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # Authenticate and read emails
    User = authenticate_gmail_as_User()
    config.set_a_global_user(User)
    

    # Path to the service account key file
    service_account_key_path = os.path.join("Creds", "skilful-mercury-444620-s6-2526f9ed3422.json")
    # Authenticate Gmail API
    service_account = authenticate_gmail_with_service_account(service_account_key_path)

    # Example usage:
    setup_watch(User, "projects/skilful-mercury-444620-s6/topics/LK-DI")
    # Start listening for notifications
    listen_for_notifications_with_service_account(
         subscription_name="LK-DI-sub",
         key_path=service_account_key_path,
         Userservice=User
     )

    
    