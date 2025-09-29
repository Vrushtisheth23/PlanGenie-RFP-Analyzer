# llm_interface_groq.py
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=os.getenv(GROQ_API_KEY),timeout=60)

def llm_generate(prompt, model="llama-3.3-70b-versatile", max_tokens=500):
    """Generate text using GROQ LLM API"""
    response =  client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content
