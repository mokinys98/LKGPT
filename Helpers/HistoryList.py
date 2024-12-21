import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from LKGPT import config
from LKGPT.gmail_auth import authenticate_gmail_as_User

#Gets a History list of emails from Gmail, from specific history id
def get_history_list(service, history_id):
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
                history_id = int(record['id'])
                return history_id

    except Exception as e:
        print(f"An error occurred: {e}")
        return





if __name__ == '__main__':
    
    User = authenticate_gmail_as_User()
    config.set_a_global_user(User)

    get_history_list(User, 0)