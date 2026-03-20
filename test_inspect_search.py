import lancedb
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

def embed_content_rest(content_payload, model_id="gemini-embedding-2-preview"):
    token = get_token()
    project_id = settings.PROJECT_ID
    location = settings.LOCATION
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:embedContent"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    response = requests.post(url, headers=headers, json={"content": content_payload}, timeout=60)
    if response.status_code != 200: return []
    return response.json().get("embedding", {}).get("values", [])

def embed_text_005_rest(text, model_id="text-embedding-005"):
    token = get_token()
    project_id = settings.PROJECT_ID
    location = settings.LOCATION
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"instances": [{"content": text}], "parameters": {"outputDimensionality": 768}}
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200: return []
    try:
         return response.json()['predictions'][0]['embeddings']['values']
    except Exception: return []

print("--- 🔬 Diagnosing /api/search API Logic ---")
q = "전투 장면"

try:
    print("1. Loading Vectors...")
    query_vector = embed_content_rest(content_payload={"parts": [{"text": q}]})
    text_vector = embed_text_005_rest(q)
    print(f"Video Vector dimension: {len(query_vector) if query_vector else 'FAIL'}")
    print(f"Text Vector dimension: {len(text_vector) if text_vector else 'FAIL'}")

    print("\n2. Querying LanceDB table...")
    db = lancedb.connect("app/database/lancedb")
    table = db.open_table("video_scenes_v2")

    results_v = table.search(query_vector).where("id != 'init'").limit(10).to_list()
    print(f"Video Search hits: {len(results_v)}")

    results_t = []
    if text_vector:
         results_t = table.search(text_vector, vector_column="text_embedding").where("id != 'init'").limit(10).to_list()
    print(f"Text Search hits: {len(results_t)}")

    print("\n3. RRF Combination Loop...")
    rrf_scores = {}
    lookup_item = {}

    for rank, row in enumerate(results_v):
         item_id = row['id']
         rrf_scores[item_id] = rrf_scores.get(item_id, 0) + (1.0 / (rank + 60))
         lookup_item[item_id] = row

    for rank, row in enumerate(results_t):
         item_id = row['id']
         rrf_scores[item_id] = rrf_scores.get(item_id, 0) + (1.0 / (rank + 60))
         lookup_item[item_id] = row

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"Combined outputs count: {len(sorted_items)}")

    items = []
    for item_id, score in sorted_items:
         row = lookup_item[item_id]
         items.append({
             "video_name": row['video_name'],
             "segment_index": int(row['segment_index']),
             "start_time": float(row['start_time']),
             "end_time": float(row['end_time']),
             "score": float(score),
             "description": row.get("description", "")
         })

    print("\nSUCCESS. Results payload:")
    print(items)

except Exception as e:
    print(f"\n❌ CRASHED: {e}")
