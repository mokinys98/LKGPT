from google.cloud import pubsub_v1

import config
import time
import json
import threading

def setup_watch(service, topic_name):
    request = {
        "labelIds": ["INBOX"],  # Watch only the inbox
        "topicName": topic_name  # Pub/Sub topic name
    }
    response = service.users().watch(userId='me', body=request).execute()
    config.set_last_history_id(response.get('historyId'))
    print("Watch setup successful:", response)
    return response

def listen_for_notifications_with_service_account(subscription_name, sacredentials, service):
    """
    Listens for Pub/Sub notifications on a given subscription and processes them using a callback function.

    Args:
        subscription_name (str): The name of the Pub/Sub subscription.
        sacredentials: Credentials for the Pub/Sub subscriber client.
        service: The Gmail API service instance to pass to the callback.

    This function sets up a subscriber client to listen for messages on the specified Pub/Sub subscription.
    It continuously listens for incoming messages and processes them using the specified callback function.
    """
    # Initialize the Pub/Sub subscriber client with the provided credentials
    subscriber = pubsub_v1.SubscriberClient(credentials=sacredentials)

    # Construct the fully qualified subscription path
    subscription_path = subscriber.subscription_path('skilful-mercury-444620-s6', subscription_name)

    # Create the callback function to handle incoming messages
    callback = create_callback(service)

    # Start listening for messages on the specified subscription
    print(f"Listening for messages on {subscription_path}...")
    subscriber.subscribe(subscription_path, callback=callback)

    # Keep the program running to continue listening indefinitely
    while True:
        time.sleep(5)

# Lock for synchronizing callback execution
callback_lock = threading.Lock()

def create_callback(service):
    """
    Creates a callback function for the Pub/Sub subscriber.

    The callback function is called whenever a new message is received on the
    specified Pub/Sub subscription. It processes the message and updates the
    last_history_id variable.

    Args:
        service: The Gmail API service instance to pass to the callback.

    Returns:
        A callback function that takes a Pub/Sub message as an argument.
    """
    def callback(message):
        from Main import process_new_emails
        """
        Processes a Pub/Sub message.

        This function is called whenever a new message is received on the
        specified Pub/Sub subscription.

        Args:
            message: The Pub/Sub message to process.
        """
        
        print(f"Received Pub/Sub message: {message.data.decode('utf-8')}")
        message.ack()  # Acknowledge the message

        try:
            notification = json.loads(message.data.decode('utf-8'))
            pubsub_history_id = int(notification['historyId'])

            # Ignore older or already processed historyId
            if pubsub_history_id <= int(config.get_last_history_id):
                print(f"Ignoring older or already processed historyId: {pubsub_history_id}")
                return

            # Process new emails starting from the last_history_id
            process_new_emails(service, config.get_last_history_id)

            # Update the last_history_id after processing
            config.set_last_history_id(pubsub_history_id)

        except Exception as e:
            print(f"Error processing message: {e}")
    return callback
