import lancedb
import requests
import base64
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    PROJECT_ID: str = "YOUR_PROJECT_ID"
    LOCATION: str = "global"
    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), ".env")), 
        env_file_encoding="utf-8"
    )

settings = Settings()

def embed_content_rest(content_payload, model_id="gemini-embedding-2-preview"):
    credentials, _ = default()
    auth_request = AuthRequest()
    credentials.refresh(auth_request)
    token = credentials.token
    project_id = settings.PROJECT_ID
    location = settings.LOCATION
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:embedContent"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json={"content": content_payload}, timeout=60)
    if response.status_code != 200: 
        print(f"Error: {response.status_code} - {response.text}")
        return []

    return response.json().get("embedding", {}).get("values", [])

DB_PATH = "app/database/lancedb"
db = lancedb.connect(DB_PATH)
table = db.open_table("video_scenes")

query_text = "액션 씬"
print(f"--- 🔍 Simulating Search for: '{query_text}' ---")
vector = embed_content_rest({"parts": [{"text": query_text}]})

if not vector:
    print("Failed to get embedding vector.")
else:
    results = table.search(vector).where("id != 'init'").limit(3).to_list()
    print(f"DEBUG: Found {len(results)} search index candidates.")
    for row in results:


         if row['id'] == 'init': continue
         print(f"✅ Match Found:")
         print(f"   - Video: {row['video_name']}")
         print(f"   - Time: {row['start_time']}s - {row['end_time']}s")
         print(f"   - Score (distance): {row.get('_distance', 'N/A')}")
