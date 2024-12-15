from utils import decode_message
import json
import os

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

#DEPRECATED
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


def write_json_data_to_json(JSON_Body):

    Subject = JSON_Body['subject']

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