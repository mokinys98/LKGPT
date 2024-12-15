import sqlite3

# Initialize SQLite database
def initialize_database():
    conn = sqlite3.connect('sender_statistics.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sender_statistics (
            sender_email TEXT PRIMARY KEY,
            total_emails INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

# Create a new entry in the database
def create_entry(sender_email):
    conn = sqlite3.connect('sender_statistics.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO sender_statistics (sender_email) VALUES (?)', (sender_email,))
    conn.commit()
    conn.close()

# Update sender statistics
def update_sender_statistics(sender_email, cost):
    conn = sqlite3.connect('sender_statistics.db')
    cursor = conn.cursor()
    
    # Check if sender already exists
    cursor.execute('SELECT total_emails, total_cost FROM sender_statistics WHERE sender_email = ?', (sender_email,))
    result = cursor.fetchone()
    
    if result:
        # Update existing record
        total_emails = result[0] + 1
        total_cost = result[1] + cost
        cursor.execute('''
            UPDATE sender_statistics 
            SET total_emails = ?, total_cost = ?
            WHERE sender_email = ?
        ''', (total_emails, total_cost, sender_email))
    else:
        # Insert new record
        cursor.execute('''
            INSERT INTO sender_statistics (sender_email, total_emails, total_cost)
            VALUES (?, ?, ?)
        ''', (sender_email, 1, cost))
    
    conn.commit()
    conn.close()

#Checks if the sender exists in the database
def sender_exists(sender_email):
    """
    Checks if the sender exists in the sender_statistics database.

    Args:
        sender_email (str): The email address of the sender to check.

    Returns:
        tuple: The database record of the sender if it exists, otherwise None.
    """
    # Connect to the SQLite database
    conn = sqlite3.connect('sender_statistics.db')
    cursor = conn.cursor()
    
    # Execute the query to find the sender
    cursor.execute('SELECT * FROM sender_statistics WHERE sender_email = ?', (sender_email,))
    result = cursor.fetchone()
    
    # Close the database connection
    conn.close()
    
    # Return the result
    return result

def view_all_entries(database_path, table_name):
    """
    Fetches and displays all entries from a given SQLite table.

    Args:
        database_path (str): Path to the SQLite database file.
        table_name (str): Name of the table to view.

    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        
        # Fetch all entries from the table
        query = f"SELECT * FROM {table_name}"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Fetch column names for better readability
        column_names = [description[0] for description in cursor.description]
        
        # Display the table contents
        print(f"Entries in table '{table_name}':")
        print(f"{' | '.join(column_names)}")
        print("-" * 50)
        for row in rows:
            print(" | ".join(map(str, row)))

        # Close the connection
        conn.close()

    except sqlite3.Error as e:
        print(f"Error accessing database: {e}")

# Example usage


if __name__ == '__main__':
    initialize_database()
    view_all_entries("sender_statistics.db", "sender_statistics")