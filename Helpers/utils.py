import base64
import re


def decode_message(encoded_data):
    decoded_bytes = base64.urlsafe_b64decode(encoded_data)
    return decoded_bytes.decode('utf-8')

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

