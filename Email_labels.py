
def get_all_labels(service):
    """
    Retrieves all labels from the user's inbox.

    Args:
        service: Authorized Gmail API service instance.

    Returns:
        list: A list of labels in the user's inbox.
    """
    try:
        labels = service.users().labels().list(userId="me").execute().get("labels", [])
        print("Labels retrieved:")
        for label in labels:
            print(f"ID: {label['id']}, Name: {label['name']}")
        return labels
    except Exception as e:
        print(f"Error retrieving labels: {e}")
        return []
    
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
