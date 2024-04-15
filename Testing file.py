import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('API_KEY')
if not api_key:
    print("API key not loaded. Check your .env file and path.")
else:
    print("API key loaded successfully.")
