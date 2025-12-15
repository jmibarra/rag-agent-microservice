import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY variable not found in .env file.")
    exit(1)

print(f"Using API Key: {api_key[:5]}...{api_key[-4:]}")

try:
    genai.configure(api_key=api_key)
    
    print("\n------------------------------------------------")
    print("AVAILABLE GEMINI MODELS (generateContent)")
    print("------------------------------------------------")
    
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            found = True
            print(f"Name: {m.name}")
            print(f"Display Name: {m.display_name}")
            print("-" * 20)
            
    if not found:
        print("No models found that support 'generateContent'.")

except Exception as e:
    print(f"\nError connecting to Google API: {e}")
