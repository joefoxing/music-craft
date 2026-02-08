from dotenv import load_dotenv
import os

# Load the prod environment file explicitly
load_dotenv('.env.prod')

db_url = os.environ.get('DATABASE_URL')
if db_url:
    # Mask password for security
    print(f"Prod DB URL: {db_url.split('@')[-1]}") 
else:
    print("DATABASE_URL not found in .env.prod")
