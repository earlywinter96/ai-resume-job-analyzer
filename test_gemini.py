import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

print("GOOGLE_API_KEY value:", os.getenv("GOOGLE_API_KEY"))

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say exactly: Gemini API is working"
)

print(response.text)
