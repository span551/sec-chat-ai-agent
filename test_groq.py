from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

# Read key directly from sentiment_agent.py to confirm it matches
import re
content = open('agents/sentiment_agent.py').read()
key = re.search(r'gsk_\w+', content).group()
print(f"Using key: {key[:10]}...{key[-4:]}")

client = Groq(api_key=key)
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "say hello"}],
    max_tokens=5
)
print("SUCCESS:", response.choices[0].message.content)