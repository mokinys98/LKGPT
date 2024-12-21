import sqlite3
import postgrest
from supabase import create_client, Client
import os

# Initialize Supabase
def initialize_supabase():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, key)
    return supabase

# Connect to Supabase
def connect_to_supabase():
    supabase = initialize_supabase()
    return supabase

# Test connection: Fetch data from a table
def test_connection(supabase):
    try:
        response = supabase.table("Test").select("*").execute()
        data = response.data
        return data
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return []
    
# Create a new entry in the database in a supabase
def create_entry(sender_email):
    supabase = connect_to_supabase()
    data = supabase.table("sender_statistics").insert({"sender_email": sender_email}).execute()
    return data

# Update sender statistics with supabase
def update_sender_statistics(sender_email, cost):
    supabase = connect_to_supabase()
    data = supabase.table("sender_statistics").select("*").eq("sender_email", sender_email).execute()
    
    if data.data:
        # Update existing record
        total_emails = data.data[0]["total_emails"] + 1
        total_cost = data.data[0]["total_cost"] + cost
        supabase.table("sender_statistics").update({"total_emails": total_emails, "total_cost": total_cost}).eq("sender_email", sender_email).execute()
    else:
        # Insert new record
        supabase.table("sender_statistics").insert({"sender_email": sender_email, "total_emails": 1, "total_cost": cost}).execute()

#Checks if the sender exists in the supabase database
def sender_exists(sender_email):
    # Connect to the Supabase
    supabase = connect_to_supabase()
    
    # Execute the query to find the sender
    data = supabase.table("sender_statistics").select("*").eq("sender_email", sender_email).execute()
    result = data.data
    
    # Return the result
    return result

# Fetches and displays all entries from a given Supabase table
def view_all_entries(supabase):
    """
    Fetches and displays all entries from a given Supabase table.

    Args:
        supabase (Client): Supabase client instance.

    """
    try:
        # Fetch all entries from the table
        data = supabase.table("sender_statistics").select("*").execute()
        rows = data.data

        # Fetch column names for better readability
        column_names = [key for key in rows[0].keys()]
        
        # Display the table contents
        print(f"Entries in table 'sender_statistics':")
        print(f"{' | '.join(column_names)}")
        print("-" * 50)
        for row in rows:
            print(" | ".join(map(str, row.values())))

    except Exception as e:
        print(f"Error accessing database: {e}")


#Sends a one-email info to supabase
def send_email_info(history_id, json_data):
    # Connect to Supabase
    supabase = connect_to_supabase()

    #Get all variables from JSON
    ID = json_data["ID"]
    ThreadID = json_data["ThreadID"]
    In_Reply_To = json_data["In_Reply_To"]
    References = json_data["References"]
    From = json_data["From"]
    Date = json_data["Date"]
    Subject = json_data["Subject"]
    body = json_data["Body"]
    Message_ID = json_data["Message_ID"]
    Thread_Index = json_data["Thread_Index"]
    Thread_Topic = json_data["Thread_Topic"]
    history_id = history_id

    try:    # Execute the query
        supabase.table("email_history").insert({"id": ID, "history_id": history_id, "threadid": ThreadID, "message_id": Message_ID, "sender_email": From, "date": Date, "subject": Subject, "body": body,"in_reply_to": In_Reply_To, "referencesnr": References, "thread_index": Thread_Index, "thread_topic": Thread_Topic }).execute()
    except postgrest.exceptions.APIError as e:
    # Check if the error is a duplicate key violation
        if e.code == '23505':
            print(f"Duplicate key error: {e.details}")
            # Handle the duplicate key case (e.g., skip, update, or log)
        else:
            # Re-raise the exception if it's a different APIError
            raise


if __name__ == '__main__':
    
    # Authenticate and retrieve the current user's UUID
    #session = supabase.auth.sign_in_with_password({"email": "***REMOVED***", "password": "***REMOVED***"})
    #print(session.user.id)  # Prints the user's UUID

    #view_all_entries("sender_statistics.db", "sender_statistics")
    data = test_connection(connect_to_supabase())
    data2 = sender_exists("Aurimas.Zvirblys@mil.lt")
    update_sender_statistics("no-reply@google.com", 0.01)
    print(data)
    print(data2)
