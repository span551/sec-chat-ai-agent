import requests, os
from dotenv import load_dotenv
load_dotenv()

r = requests.post(
    'https://openrouter.ai/api/v1/chat/completions',
    headers={
        'Authorization': f'Bearer {os.getenv("OPENROUTER_API_KEY")}',
        'Content-Type': 'application/json'
    },
    json={
        'model': 'mistralai/mistral-7b-instruct:free',
        'messages': [{'role': 'user', 'content': 'say hello'}],
        'max_tokens': 5
    }
)
print(r.json())