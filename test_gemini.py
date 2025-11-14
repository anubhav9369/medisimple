import os
import google.generativeai as genai

# Option 1: Set API key directly (for testing)
API_KEY = "AIzaSyA34zfb1WbcqcQlbjyp7JkcsQVa7YOrsYQ"  # Replace with your actual key

# Option 2: Read from secrets file (uncomment to use)
# try:
#     with open(".streamlit/secrets.toml", "r") as f:
#         for line in f:
#             if line.startswith("GEMINI_API_KEY"):
#                 API_KEY = line.split("=")[1].strip().strip('"')
#                 break
# except Exception as e:
#     print(f"Error reading secrets file: {e}")

# Mask the key for display (show first 4 and last 4 characters)
masked_key = API_KEY[:4] + "*" * (len(API_KEY) - 8) + API_KEY[-4:] if len(API_KEY) > 8 else "*" * len(API_KEY)
print(f"Testing with API key: {masked_key}")

try:
    genai.configure(api_key=API_KEY)
    
    # Test with a simple request
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content("Hello")
    print("SUCCESS: API key is valid!")
    print("Response:", response.text)
    
except Exception as e:
    print("ERROR:", str(e))