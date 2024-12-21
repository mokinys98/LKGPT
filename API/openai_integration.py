import os
import time
from dotenv import find_dotenv, load_dotenv
from openai import OpenAI
from Helpers.utils import decode_message
from google.cloud import pubsub_v1

load_dotenv(find_dotenv())
# Replace with your OpenAI API key
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def call_openai_with_retry(prompt, max_retries=3, wait_time=5):
    """
    Calls OpenAI's API with a retry mechanism.

    Args:
        prompt (str): The input prompt for OpenAI.
        max_retries (int): Maximum number of retries in case of failure.
        wait_time (int): Wait time (in seconds) between retries.

    Returns:
        str: The response from OpenAI.
    """
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}...")
            # Call OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            # If the call succeeds, return the response
            return response

        except Exception as e:
            print(f"Error: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Returning failure.")
                raise  # Re-raise the exception after max retries