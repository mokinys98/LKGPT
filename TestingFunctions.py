from utils import extract_email, get_header_value, decode_message
from sqldb import initialize_database, update_sender_statistics, sender_exists, create_entry
from Email_processing import format_and_display_emails_table, read_emails
from Email_send_to import send_html_email, create_markdown_email_body, create_greeting_email
from Email_labels import get_all_labels, change_email_label
#Dirbtinis intelektas
from openai import OpenAI
import config

def process_specific_email(service, history_id, specific_email):
    print(f"Processing specific email with historyId: {history_id}")

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
            if 'id' in record:
                check = int(record['id'])
                if check == specific_email:
                    print(f"Found the specific email with historyId: {specific_email}")
                else:
                    #removes an whole object from responce
                    response['history'].remove(record)
                    
        new_messages = []
        processed_message_ids = set()
        if 'history' in response: 
            for record in response['history']:
                check = int(record['id'])
                if check == specific_email:
                    for message in record['messagesAdded']:
                        print(f"Found the specific email with historyId: {specific_email}")
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


                        # headers = full_message['payload']['headers']
                        # From = get_header_value(headers, "From")
                        # sender_email = extract_email(From)
                        # bool = sender_exists(sender_email)
                        # if bool:
                        #     print(f"Sender exists in the database: {sender_email}")
                        # else:
                        #     print(f"Sender does not exist in the database: {sender_email}")
                        #     email_body = create_greeting_email()
                        #     try:
                        #         User = config.get_global_user()   
                        #         send_html_email(service=User, sender="***REMOVED***", recipient=extract_email(sender_email), subject="Sveiki!", html_content=email_body)
                        #         create_entry(sender_email)
                        #         continue
                        #     except Exception as e:
                        #         print(f"Error sending email: {e}")
                        #         continue
                        

                        #BIG CHANGE TO LET ALL EMAILS GO TO OPENAI
                        if 'INBOX' in labels or 'UNREAD' in labels:
                            processed_message_ids.add(message['message']['id'])
                            new_messages.append(full_message)
                            print(f"Formuojama nauja užklausa į OPENAI")
                            json_data = test_message_handler(full_message)
                            test_write_to_OPENAI(json_data)

        if new_messages:
            print("\nNew Emails Received:")
            format_and_display_emails_table(new_messages)

    except Exception as e:
        print(f"Error processing new emails: {e}")


def test_write_to_OPENAI(Json_Data):
    ID = Json_Data["ID"]
    ThreadID = Json_Data["ThreadID"]
    In_Reply_To = Json_Data["In_Reply_To"]
    References = Json_Data["References"]
    From = Json_Data["From"]
    Date = Json_Data["Date"]
    Subject = Json_Data["Subject"]
    body = Json_Data["Body"]
    
    
    try:
        #result = call_openai_with_retry(prompt=body, max_retries=3, wait_time=5)
        total_tokens = 500
        approx_cost_usd = float(total_tokens / 1000) * 0.03  # Assuming a cost of $0.03 per 1000 tokens
        response = "Testas"	

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
            json_data = test_message_to_json_data(ID=ID, ThreadID=ThreadID, From="***REMOVED***", Date=Date, Subject=Subject, body=email_body, In_Reply_To=In_Reply_To, References=References) 
            #pirmiausiai pasirasem sau i |JSON| faila
            #write_json_data_to_json(json_data)

        except Exception as e:
            print(f"Error sending email: {e}")

    except OpenAI.error.Timeout as e:
        print("Request timed out.")
    except OpenAI.error.RateLimitError as e:
        print("Rate limit exceeded.")
    
def test_message_handler(msg):
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
    json_data = test_message_to_json_data(ID=ID, ThreadID=ThreadId, From=From, Date=Date, Subject=Subject, body=body, In_Reply_To=In_Reply_To, References=References) 

    #pirmiausiai pasirasem sau i |JSON| faila
    #write_json_data_to_json(json_data)

    return json_data

def test_message_to_json_data(ID, From, Date, Subject, body, ThreadID = None, In_Reply_To=None, References=None):

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