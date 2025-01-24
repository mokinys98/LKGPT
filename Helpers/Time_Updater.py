import time
from datetime import datetime
from sql.sqldb import connect_to_supabase
import random

def update_database_entry():
    """
    Updates a database entry every X Random minutes.
    """
    supabase = connect_to_supabase()
    
    try:
        while True:
            # Get the current time
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            
            # Example: Update a specific row in the database
            print(f"Updating database entry at {current_time}")
            
            # Replace the logic below with your actual database update query
            supabase.table("Time").update(
                {"Time": current_time}
            ).eq("id", 1).execute()
            
            print(f"Database entry updated successfully.")
            
            # Wait for a random time between X and Y minutes
            wait_time = random.randint(5, 30)  # Replace 5 and 10 with your desired range
            print(f"Waiting for {wait_time} minutes before next update.")
            time.sleep(60 * wait_time)
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_database_entry()
