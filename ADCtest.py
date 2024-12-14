from google.auth import default

credentials, project = default()
print(f"Credentials: {credentials}")
print(f"Project ID: {project}")





#def process_new_emails(service, history_id):
    """
    Fetches and processes new emails based on the historyId and displays them in a table.

    Args:
        service: Authorized Gmail API service instance.
        history_id: The starting history ID for changes.
    """
    print(f"Processing new emails starting with historyId: {history_id}")

    try:
        response = service.users().history().list(userId='me', startHistoryId=history_id).execute()

        if 'history' not in response:
            print("No history records found in the response.")
            return

        new_messages = []
        for record in response['history']:
            if 'messages' in record:
                for message in record['messages']:
                    # Fetch the full message
                    full_message = service.users().messages().get(userId='me', id=message['id']).execute()
                    new_messages.append(full_message)

        if new_messages:
            print("\nNew Emails Received:")
            format_and_display_emails_table(new_messages)
        else:
            print("No new emails found in the history records.")
    except Exception as e:
        print(f"Error processing new emails: {e}")