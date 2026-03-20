import os
import subprocess
import uuid
import glob
import time
import shutil
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings, SettingsConfigDict
import lancedb
import numpy as np
import requests
import base64
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest


from google import genai
from google.genai import types
from google.genai.errors import APIError



# 1. Config & Settings
class Settings(BaseSettings):
    PROJECT_ID: str = "YOUR_PROJECT_ID"
    LOCATION: str = "global"

    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")), 
        env_file_encoding="utf-8"
    )


settings = Settings()

# 2. Application Setup
app = FastAPI(title="Video Search with Gemini Embedding 2")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize LanceDB
DB_PATH = "app/database/lancedb"
db = lancedb.connect(DB_PATH)

# Initialize global tracking for upload/embedding process status
# { "video_id": { "status": "processing", "progress": 0, "logs": [] } }
process_status: Dict[str, Dict[str, Any]] = {}

def generate_description_rest(video_bytes, model_id="gemini-3.1-flash-lite-preview"):
    from google.auth import default
    from google.auth.transport.requests import Request as AuthRequest
    credentials, _ = default()
    auth_request = AuthRequest()
    credentials.refresh(auth_request)
    token = credentials.token
    project_id = settings.PROJECT_ID
    # Global Endpoint for preview models
    url = f"https://aiplatform.googleapis.com/v1/projects/{project_id}/locations/global/publishers/google/models/{model_id}:generateContent"
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    b64_data = base64.b64encode(video_bytes).decode('utf-8')
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"inlineData": {"mimeType": "video/mp4", "data": b64_data}},
                {"text": "Describe ONLY the visual actions, movements, and immediate events happening in this 10-second standalone clip. DO NOT summarize the movie or add general plot context not visible in this clip. Avoid repeated introductions.\n\nRules:\n1. Output MUST be strictly in Korean (한국어).\n2. Keep it EXTREMELY short and concise, maximum 1 or 2 lines."}


            ]
        }],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 300}
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200: 
         raise Exception(f"Generate Error {response.status_code}: {response.text}")
    try:
         return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e: 
         raise Exception(f"Parse Error {e} | Resp: {response.text}")

def embed_gemini_embedding_001_rest(text, model_id="gemini-embedding-001"):
    from google.auth import default
    from google.auth.transport.requests import Request as AuthRequest
    credentials, _ = default()
    auth_request = AuthRequest()
    credentials.refresh(auth_request)
    token = credentials.token
    project_id = settings.PROJECT_ID
    location = settings.LOCATION
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:predict"
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "instances": [{"content": text}]
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200: 
         raise Exception(f"Embed Gemini 001 Error {response.status_code}: {response.text}")
    try:
         # Response structure: {"predictions": [{"embeddings": {"values": [...]}}]}
         return response.json()['predictions'][0]['embeddings']['values']
    except Exception as e: 
         raise Exception(f"Parse Gemini 001 Error {e} | Resp: {response.text}")


# 3. LanceDB Table Setup
def get_table():
    try:
         return db.open_table("video_scenes_v4")
    except Exception:
         # Create table if not exists with dummy row for schema inference
         # Schema: [id, segment_index, start_time, end_time, video_name, embedding, description, text_embedding, url]
         dummy_embedding = [0.0] * 3072 
         dummy_text_embedding = [0.0] * 3072
         return db.create_table("video_scenes_v4", data=[{
             "id": "init",
             "segment_index": 0,
             "start_time": 0.0,
             "end_time": 0.0,
             "video_name": "init",
             "embedding": dummy_embedding,
             "description": "init",
             "text_embedding": dummy_text_embedding,
             "url": "init"
         }])



# Validate Vertex AI Settings
def get_vertex_client():
    if settings.PROJECT_ID == "YOUR_PROJECT_ID":
        raise ValueError("Please provide your Google Cloud Project ID in the .env file.")
    try:
        return genai.Client(
            vertexai=True,
            project=settings.PROJECT_ID,
            location=settings.LOCATION
        )
    except Exception as e:
         raise ValueError(f"Failed to initialize GenAI Vertex client: {e}")

def embed_content_rest(content_payload: Dict[str, Any], model_id: str = "gemini-embedding-2-preview"):
    """
    Calls Vertex AI :embedContent REST endpoint directly to bypass SDK bugs.
    """
    credentials, _ = default()
    auth_request = AuthRequest()

    credentials.refresh(auth_request)
    token = credentials.token

    project_id = settings.PROJECT_ID
    location = settings.LOCATION

    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model_id}:embedContent"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
         response = requests.post(url, headers=headers, json={"content": content_payload}, timeout=60)
         if response.status_code != 200:
              raise ValueError(f"Vertex AI (REST) Error {response.status_code}: {response.text}")
         
         data = response.json()
         if "embedding" in data and "values" in data["embedding"]:
              return data["embedding"]["values"]
         elif "embeddings" in data and len(data["embeddings"]) > 0:
              # Alternating batch response format check
              return data["embeddings"][0]["values"] if "values" in data["embeddings"][0] else []
         else:
              raise ValueError(f"Unexpected response format: {data}")
    except requests.exceptions.Timeout:
         raise TimeoutError("Vertex AI request timed out")
    except Exception as e:
         raise e

# 4. Background Processing Task
def run_ffmpeg_split(video_path: str, output_pattern: str):
    """
    Splits video into 10-second segments.
    """
    ffmpeg_bin = "./bin/ffmpeg"
    command = [
        ffmpeg_bin, "-i", video_path,
        "-f", "segment",
        "-segment_time", "10",
        "-reset_timestamps", "1",
        output_pattern

    ]
    try:
         result = subprocess.run(command, capture_output=True, text=True, check=True)
         return result.stdout
    except subprocess.CalledProcessError as e:
         print(f"FFmpeg Error: {e.stderr}")
         raise e

async def process_video_background(video_path: str, video_name: str, video_id: str, client):
    """
    Takes a saved clip, segments it, generates embeddings, and saves to LanceDB.
    """
    global process_status
    process_status[video_id] = {"status": "Processing", "progress": 10, "logs": ["Step 1: Starting segmentation"]}
    
    static_segments_dir = f"app/static/segments/{video_id}"
    os.makedirs(static_segments_dir, exist_ok=True)
    output_pattern = f"{static_segments_dir}/segment_%03d.mp4"

    try:
        # Step 1: Segmentation
        process_status[video_id]["logs"].append("Running FFmpeg split...")
        run_ffmpeg_split(video_path, output_pattern)
        segments = sorted(glob.glob(f"{static_segments_dir}/segment_*.mp4"))
        
        process_status[video_id]["status"] = "Embedding"
        process_status[video_id]["progress"] = 30
        process_status[video_id]["logs"].append(f"Found {len(segments)} segments. Generating embeddings.")

        table = get_table()
        data_to_insert = []
        segments_metadata = []

        # Step 2: Gemini Embeddings for each segment (Parallelized)
        import concurrent.futures

        def process_single_segment(index: int, segment_path: str):
            start_time = index * 10
            end_time = (index + 1) * 10
            try:
                with open(segment_path, "rb") as f:
                    video_bytes = f.read()

                b64_data = base64.b64encode(video_bytes).decode('utf-8')
                embedding_vector = embed_content_rest(content_payload={
                    "parts": [{"inlineData": {"mimeType": "video/mp4", "data": b64_data}}]
                })

                description_text = ""
                text_vector = [0.0]*3072

                if embedding_vector:
                    description_text = generate_description_rest(video_bytes)
                    if description_text:
                        text_vector = embed_gemini_embedding_001_rest(description_text)

                    insert_row = {
                        "id": str(uuid.uuid4()),
                        "segment_index": index,
                        "start_time": float(start_time),
                        "end_time": float(end_time),
                        "video_name": video_name,
                        "embedding": embedding_vector,
                        "description": description_text if description_text else "",
                        "text_embedding": text_vector if text_vector else [0.0]*3072,
                        "url": f"/static/segments/{video_id}/segment_{index:03d}.mp4"
                    }

                    metadata_row = {
                        "index": index,
                        "start_time": float(start_time),
                        "end_time": float(end_time),
                        "url": f"/static/segments/{video_id}/segment_{index:03d}.mp4",
                        "dimensions": len(embedding_vector),
                        "text_dimensions": len(text_vector) if text_vector else 0,
                        "description": description_text if description_text else "No description"
                    }
                    return {"insert": insert_row, "metadata": metadata_row}

            except Exception as e:
                print(f"Error on segment {index}: {e}")
            return None

        process_status[video_id]["logs"].append("Deploying parallel execution threads for embeddings...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_single_segment, i, p) for i, p in enumerate(segments)]
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                if res:
                    data_to_insert.append(res["insert"])
                    segments_metadata.append(res["metadata"])

        # Sort to preserve exact order layout
        data_to_insert.sort(key=lambda x: x["segment_index"])
        segments_metadata.sort(key=lambda x: x["index"])


        # Step 3: Insert to Vector DB
        if data_to_insert:
            process_status[video_id]["logs"].append("Saving to Vector DB...")
            try:
                 table.delete(f"video_name = '{video_name}'")
            except Exception: pass # If table was empty or not indexed
            
            table.add(data_to_insert)
            process_status[video_id]["status"] = "Completed"

            process_status[video_id]["progress"] = 100
            process_status[video_id]["segments_metadata"] = segments_metadata
        else:
             process_status[video_id]["status"] = "Failed"
             process_status[video_id]["logs"].append("No embeddings generated, failed.")

    except Exception as e:
         process_status[video_id]["status"] = "Failed"
         process_status[video_id]["logs"].append(f"General processing error: {e}")
         print(f"Background process error: {e}")
    finally:
         pass


# 5. Endpoint Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the main layout interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...)
):
    """
    Handles streaming upload and registers background processing task.
    """
    try:
         # Verification check for Vertex configuration upfront
         client = get_vertex_client()
    except ValueError as e:
         raise HTTPException(status_code=500, detail=str(e))

    video_id = str(uuid.uuid4())
    upload_dir = "app/database/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    video_path = f"{upload_dir}/{video_id}_{video.filename}"

    # Safe save
    with open(video_path, "wb") as f:
         f.write(await video.read())

    process_status[video_id] = {
         "status": "Queued",
         "progress": 0,
         "logs": ["Upload complete, queuing background task..."]
    }

    # Queue background processing
    background_tasks.add_task(process_video_background, video_path, video.filename, video_id, client)

    return JSONResponse(status_code=202, content={
         "status": "Accepted",
         "video_id": video_id,
         "filename": video.filename
    })

@app.post("/api/sample")
async def sample_video(background_tasks: BackgroundTasks):
    """
    Triggers processing using the pre-installed sample video.
    """
    try:
         client = get_vertex_client()
    except ValueError as e:
         raise HTTPException(status_code=500, detail=str(e))

    video_id = str(uuid.uuid4()) # Create a unique job id
    video_path = "app/static/samples/sample_test_video.mp4"
    filename = "sample_test_video.mp4"

    if not os.path.exists(video_path):
         raise HTTPException(status_code=404, detail="Sample video file not found on server")

    process_status[video_id] = {
         "status": "Queued",
         "progress": 0,
         "logs": ["Using pre-installed sample video, queuing task..."]
    }

    # Queue background processing
    background_tasks.add_task(process_video_background, video_path, filename, video_id, client)

    return JSONResponse(status_code=202, content={
         "status": "Accepted",
         "video_id": video_id,
         "filename": filename
    })

@app.post("/api/clear_db")
async def clear_db():
    try:
         try:
              db.drop_table("video_scenes_v4")
         except Exception:
              pass # ignore if already not exists
         
         # Recreate table immediately with dummy row inference
         get_table()
         return {"status": "success", "message": "Database cleared and reinitialized"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{video_id}")

async def get_status(video_id: str):
    """Checks progress of video segmented indexing."""
    if video_id not in process_status:
        raise HTTPException(status_code=404, detail="Process track not found")
    return process_status[video_id]

@app.get("/api/search")
async def search_index(q: str):
    """
    Queries vector embeddings table using text query embedding
    """
    if not q:
        raise HTTPException(status_code=400, detail="Query text requires 'q' parameter")

    try:
         client = get_vertex_client()
    except ValueError as e:
         raise HTTPException(status_code=500, detail=str(e))

    try:
         # 2. Embed textual query
         query_vector = embed_content_rest(content_payload={"parts": [{"text": q}]})
         text_vector = embed_gemini_embedding_001_rest(q)

         if not query_vector:
             raise HTTPException(status_code=500, detail="Failed to produce query embedding")

         # 2. Search LanceDB
         table = get_table()
         results_v = table.search(query_vector, vector_column_name="embedding").where("id != 'init'").limit(10).to_list()

         
         results_t = []
         if text_vector:
              results_t = table.search(text_vector, vector_column_name="text_embedding").where("id != 'init'").limit(10).to_list()


         # 3. Reciprocal Rank Fusion (RRF)
         print(f"\n--- 🔍 RRF Search Debug: Query='{q}' ---")
         print(f"🎥 Video Search Results ({len(results_v)} items):")
         for r, row in enumerate(results_v):
              print(f"  Rank {r+1}: Seg={row['segment_index']} | {row.get('description','')[:40]}...")
         print(f"📝 Text Search Results ({len(results_t)} items):")
         for r, row in enumerate(results_t):
              print(f"  Rank {r+1}: Seg={row['segment_index']} | {row.get('description','')[:40]}...")

         rrf_scores = {}
         lookup_item = {}

         # Video ranking
         for rank, row in enumerate(results_v):
              item_id = row['id']
              score = 1.0 / (rank + 60)
              target_words = [w for w in q.split() if w not in ['장면', '모습', '영상', '사진']]
              if any(w.lower() in row.get('description', '').lower() for w in target_words):
                   score += 0.5 # Substring Match Bonus
              rrf_scores[item_id] = rrf_scores.get(item_id, 0) + score
              lookup_item[item_id] = row

         # Text ranking
         for rank, row in enumerate(results_t):
              item_id = row['id']
              score = 1.25 * (1.0 / (rank + 60))
              target_words = [w for w in q.split() if w not in ['장면', '모습', '영상', '사진']]
              if any(w.lower() in row.get('description', '').lower() for w in target_words):
                   score += 0.5 # Substring Match Bonus
              rrf_scores[item_id] = rrf_scores.get(item_id, 0) + score
              lookup_item[item_id] = row

         # Sort by RRF Score descending - Top 1 only
         sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:1]
         
         items = []
         for item_id, score in sorted_items:
              row = lookup_item[item_id]
              items.append({
                  "video_name": row['video_name'],
                  "segment_index": int(row['segment_index']),
                  "start_time": float(row['start_time']),
                  "end_time": float(row['end_time']),
                  "score": float(score),  # Higher is better for RRF
                  "description": row.get("description", ""),
                  "url": row.get("url", "")
              })




         diagnostics = {
              'results_v': [
                   {'segment_index': int(r['segment_index']), 'video_name': r.get('video_name',''), 'description': r.get('description','No description')[:80]} for r in results_v
              ],
              'results_t': [
                   {'segment_index': int(r['segment_index']), 'video_name': r.get('video_name',''), 'description': r.get('description','No description')[:80]} for r in results_t
              ]
         }
         return {'query': q, 'results': items, 'diagnostics': diagnostics}

    except Exception as e:
         print(f"Search API Error: {e}")
         raise HTTPException(status_code=500, detail=str(e))
