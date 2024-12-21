import sqlite3
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

# Example usage


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
