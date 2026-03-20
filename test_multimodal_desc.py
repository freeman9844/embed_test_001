import requests
import base64
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_ID: str = "jwlee-argolis-202104"
    LOCATION: str = "us-central1"
    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")), 
        env_file_encoding="utf-8"
    )

settings = Settings()

def get_token():
    credentials, _ = default()
    auth_request = AuthRequest()
    credentials.refresh(auth_request)
    return credentials.token

def generate_description_rest(video_bytes, model_id="gemini-1.5-flash-002"):
    """
    Generate video description using Gemini REST API.
    """
    token = get_token()
    project_id = settings.PROJECT_ID
    location = settings.LOCATION
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:generateContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    b64_data = base64.b64encode(video_bytes).decode('utf-8')
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {
                    "inlineData": {
                        "mimeType": "video/mp4",
                        "data": b64_data
                    }
                },
                {"text": "Describe this video segment in detail including actions and visuals."}
            ]
        }],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        print(f"Generate Error: {response.status_code} - {response.text}")
        return ""
    
    try:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Parse Error: {e}")
        return ""

def embed_text_005_rest(text, model_id="text-embedding-005"):
    """
    Generate text embedding using Vertex AI Predict REST endpoint.
    """
    token = get_token()
    project_id = settings.PROJECT_ID
    location = settings.LOCATION
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "instances": [{"content": text}],
        "parameters": {"outputDimensionality": 768}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
         print(f"Embed 005 Error: {response.status_code} - {response.text}")
         return []

    try:
         # Output format for :predict returns prediction array containing embeddings
         return response.json()['predictions'][0]['embeddings']['values']
    except Exception as e:
         print(f"Parse 005 Error: {e}")
         return []

# Test with a dummy file if any exists
segments_dir = "app/static/segments"
if os.path.exists(segments_dir):
     v_dirs = [d for d in os.listdir(segments_dir) if os.path.isdir(os.path.join(segments_dir, d))]
     if v_dirs:
          test_file = os.path.join(segments_dir, v_dirs[0], "segment_001.mp4")
          if os.path.exists(test_file):
               print(f"--- 🧪 Testing on {test_file} ---")
               with open(test_file, "rb") as f:
                    b = f.read()
               print("1. Testing Description Generation...")
               desc = generate_description_rest(b)
               print(f"Description Result:\n{desc}\n")
               
               if desc:
                    print("2. Testing Text Embedding 005...")
                    v = embed_text_005_rest(desc)
                    print(f"Embedding Vector Size: {len(v)}")
else:
     print("No static segments found for testing.")
