import os
import subprocess
import uuid
import glob
import time
import shutil
import asyncio
from typing import List, Dict, Any
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic_settings import BaseSettings, SettingsConfigDict
import asyncpg
import numpy as np
import requests
import base64
from contextlib import asynccontextmanager
from google.auth import default
from google.auth.transport.requests import Request as AuthRequest


from google.cloud import storage
from google import genai
from google.genai import types
from google.genai.errors import APIError

def vector_to_str(vec):
    """Converts a vector into pgvector string format '[1.0, 2.0]'"""
    if vec is None:
         return None
    if isinstance(vec, np.ndarray):
         vec = vec.tolist()
    return f"[{','.join(map(str, vec))}]"



# 1. Config & Settings
class Settings(BaseSettings):
    PROJECT_ID: str = "YOUR_PROJECT_ID"
    LOCATION: str = "global"

    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")), 
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# 2. Application Setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize AlloyDB Connection Pool
    conn_str = "postgresql://postgres:DefaultSearch_1234@34.64.97.194:5432/postgres"
    print("🔌 Initializing AlloyDB Connection Pool...")
    app.state.pool = await asyncpg.create_pool(conn_str, ssl="require", timeout=30, min_size=0, max_size=10)
    yield
    # Close pool on shutdown
    await app.state.pool.close()

app = FastAPI(title="Video Search with Gemini Embedding 2", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Initialize global tracking for upload/embedding process status
# { "video_id": { "status": "processing", "progress": 0, "logs": [] } }
process_status: Dict[str, Dict[str, Any]] = {}

def generate_description_rest(gcs_uri: str, model_id="gemini-3.1-flash-lite-preview"):
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

    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"fileData": {"mimeType": "video/mp4", "fileUri": gcs_uri}},
                {"text": "이 비디오 클립을 분석하여 묘사적인 한국어(Korean) 설명을 작성하세요.\n\n포함할 요소:\n1. 등장인물의 시각적 행동 및 움직임\n2. 주변 배경, 장소 및 사물의 디테일\n3. 화면에서 시각적으로 유추되는 긴장감이나 분위기\n\n규칙 (매우 중요):\n- '이 영상은', '이 클립은' 등의 불필요한 패키지 도입 어구를 사용하지 말고 바로 사실적 장면 묘사로 시작하세요.\n- 비디오에 나오는 영화 제목이나 브랜드 명칭을 직접 언급하지 마세요.\n- 출력은 200자 내외로 간결하게 한 단락 분량으로 작성하세요.\n- 보이지 않는 가상의 맥락이나 스토리를 지어내서 추측하지 마세요."}


            ]
        }],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
    }
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    if response.status_code != 200: 
         raise Exception(f"Generate Error {response.status_code}: {response.text}")
    try:
         res_json = response.json()
         candidate = res_json['candidates'][0]
         content = candidate.get('content', {})
         parts = content.get('parts', [])
         
         if parts:
              return parts[0]['text']
         else:
              print(f"⚠️ Parts missing in response Candidate. FinishReason: {candidate.get('finishReason')}")
              # Return empty description or partial if model returned other fields layout?
              return "비주얼 묘사 생성이 한도 도달 등으로 인해 도중 절삭되었습니다."
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
        "-threads", "0",
        "-vf", "scale=720:-2,fps=5",
        "-f", "segment",
        "-segment_time", "10",
        "-reset_timestamps", "1",
        output_pattern
    ]
    try:
         # Use DEVNULL for background streams to avoid pipe clogging OSError(5) Node creations
         result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
         return ""
    except subprocess.CalledProcessError as e:
         print(f"FFmpeg Error occurred")
         raise e
    except Exception as e:
         raise e

async def process_video_background(video_path: str, video_name: str, video_id: str, client, pool):
    """
    Takes a saved clip, segments it, generates embeddings, and saves to LanceDB.
    """
    global process_status
    process_status[video_id] = {"status": "Processing", "progress": 10, "logs": ["Step 1: Starting segmentation"]}
    
    static_segments_dir = f"app/static/segments/{video_id}"
    os.makedirs(static_segments_dir, exist_ok=True)
    output_pattern = f"{static_segments_dir}/segment_%03d.mp4"
    
    storage_client = storage.Client(project=settings.PROJECT_ID)

    try:
        # Step 1: Segmentation
        process_status[video_id]["logs"].append("Running FFmpeg split...")
        run_ffmpeg_split(video_path, output_pattern)
        segments = sorted(glob.glob(f"{static_segments_dir}/segment_*.mp4"))
        
        process_status[video_id]["status"] = "Embedding"
        process_status[video_id]["progress"] = 30
        process_status[video_id]["logs"].append(f"Found {len(segments)} segments. Generating embeddings.")

        # table = get_table() removed
        data_to_insert = []
        segments_metadata = []

        # Step 2: Gemini Embeddings for each segment (Parallelized)
        import concurrent.futures

        def process_single_segment(index: int, segment_path: str):
            start_time = index * 10
            end_time = (index + 1) * 10
            try:
                # 1. Upload segment to GCS first Node creations
                bucket_name = "jwlee-gcs-video-002"
                blob_name = f"segments/{video_id}/segment_{index:03d}.mp4"
                
                try:
                    bucket = storage_client.bucket(bucket_name)
                    blob = bucket.blob(blob_name)
                    blob.upload_from_filename(segment_path)
                except Exception as upload_err:
                    print(f"GCS Upload Failed for index {index}: {upload_err}")
                    raise upload_err

                gcs_url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
                # fileData uses gs:// string identifiers layout Creations
                gcs_uri = f"gs://{bucket_name}/{blob_name}"

                # 2. Call Vertex AI referencing gcs_uri Node creations
                embedding_vector = embed_content_rest(content_payload={
                    "parts": [{"fileData": {"mimeType": "video/mp4", "fileUri": gcs_uri}}]
                })

                description_text = ""
                text_vector = [0.0]*3072

                if embedding_vector:
                    description_text = generate_description_rest(gcs_uri)
                    if description_text:
                        text_vector = embed_content_rest(content_payload={"parts": [{"text": description_text}]})

                # Local Cleanup Item Node creations
                try: os.remove(segment_path)
                except: pass

                insert_row = {
                    "id": str(uuid.uuid4()),
                    "segment_index": index,
                    "start_time": float(start_time),
                    "end_time": float(end_time),
                    "video_name": video_name,
                    "embedding": embedding_vector,
                    "description": description_text if description_text else "",
                    "text_embedding": text_vector if text_vector else [0.0]*3072,
                    "url": gcs_url
                }

                metadata_row = {
                    "index": index,
                    "start_time": float(start_time),
                    "end_time": float(end_time),
                    "url": gcs_url,
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


        # Step 3: Insert to Vector DB (AlloyDB)
        if data_to_insert:
            process_status[video_id]["logs"].append("Saving to AlloyDB...")
            async with pool.acquire() as conn:
                try:
                    await conn.execute("DELETE FROM video_scenes_v4 WHERE video_name = $1", video_name)
                    
                    insert_sql = """
                    INSERT INTO video_scenes_v4 (id, segment_index, start_time, end_time, video_name, embedding, description, text_embedding, url)
                    VALUES ($1, $2, $3, $4, $5, $6::vector, $7, $8::vector, $9)
                    """
                    records = [
                        (r['id'], r['segment_index'], r['start_time'], r['end_time'], r['video_name'], vector_to_str(r['embedding']), r['description'], vector_to_str(r['text_embedding']), r['url'])
                        for r in data_to_insert
                    ]
                    await conn.executemany(insert_sql, records)
                except Exception as e:
                    print(f"AlloyDB Background Insert Error: {repr(e)}")
                    raise e

            process_status[video_id]["status"] = "Completed"

            process_status[video_id]["progress"] = 100
            process_status[video_id]["segments_metadata"] = segments_metadata
        else:
             process_status[video_id]["status"] = "Failed"
             process_status[video_id]["logs"].append("No embeddings generated, failed.")

    except Exception as e:
         process_status[video_id]["status"] = "Failed"
         process_status[video_id]["logs"].append(f"General processing error: {repr(e)}")
         print(f"Background process error: {repr(e)}")
    finally:
         pass


# 5. Endpoint Routes
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Renders the main layout interface."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/upload")
async def upload_video(
    request: Request,
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
    background_tasks.add_task(process_video_background, video_path, video.filename, video_id, client, request.app.state.pool)

    return JSONResponse(status_code=202, content={
         "status": "Accepted",
         "video_id": video_id,
         "filename": video.filename
    })

@app.post("/api/sample")
async def sample_video(request: Request, background_tasks: BackgroundTasks):
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
    background_tasks.add_task(process_video_background, video_path, filename, video_id, client, request.app.state.pool)

    return JSONResponse(status_code=202, content={
         "status": "Accepted",
         "video_id": video_id,
         "filename": filename
    })

@app.post("/api/clear_db")
async def clear_db(request: Request):
    try:
        async with request.app.state.pool.acquire() as conn:
            await conn.execute("DELETE FROM video_scenes_v4")
        process_status.clear()  # 메모리 상의 작업 상태까지 비웁니다 Node creations Node layout.
        return {"status": "success", "message": "Database cleared"}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{video_id}")

async def get_status(video_id: str):
    """Checks progress of video segmented indexing."""
    if video_id not in process_status:
        raise HTTPException(status_code=404, detail="Process track not found")
    return process_status[video_id]

@app.get("/api/search")
async def search_index(q: str, request: Request):
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
         text_vector = embed_content_rest(content_payload={"parts": [{"text": q}]})

         if not query_vector:
             raise HTTPException(status_code=500, detail="Failed to produce query embedding")

         # 2. Search AlloyDB
         results_v = []
         results_t = []
         results_fts = []

         async with request.app.state.pool.acquire() as conn:
              q_v_str = vector_to_str(query_vector)
              q_t_str = vector_to_str(text_vector) if text_vector else None

              single_sql = """
              WITH visual_ranks AS (
                  SELECT id, segment_index, start_time, end_time, video_name, description, url, 
                         ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) as rank
                  FROM video_scenes_v4 WHERE id != 'init' ORDER BY embedding <=> $1::vector LIMIT 10
              ),
              text_ranks AS (
                  SELECT id, segment_index, start_time, end_time, video_name, description, url, 
                         ROW_NUMBER() OVER (ORDER BY text_embedding <=> $2::vector) as rank
                  FROM video_scenes_v4 WHERE id != 'init' AND $2::vector IS NOT NULL ORDER BY text_embedding <=> $2::vector LIMIT 10
              ),
              fts_ranks AS (
                  SELECT id, segment_index, start_time, end_time, video_name, description, url, 
                         ROW_NUMBER() OVER (ORDER BY bigm_similarity(description, $3) DESC) as rank
                  FROM video_scenes_v4 WHERE id != 'init' AND description LIKE ANY($4::text[])
                  ORDER BY bigm_similarity(description, $3) DESC LIMIT 10
              ),
              merged_scores AS (
                  SELECT 
                      v.id,
                      1.25 * COALESCE(1.0 / (vr.rank + 60), 0) + 
                      1.0 * COALESCE(1.0 / (tr.rank + 60), 0) + 
                      1.0 * COALESCE(1.0 / (fr.rank + 60), 0) AS rrf_score
                  FROM video_scenes_v4 v
                  LEFT JOIN visual_ranks vr ON v.id = vr.id
                  LEFT JOIN text_ranks tr ON v.id = tr.id
                  LEFT JOIN fts_ranks fr ON v.id = fr.id
                  WHERE vr.id IS NOT NULL OR tr.id IS NOT NULL OR fr.id IS NOT NULL
                  ORDER BY rrf_score DESC LIMIT 1
              )
              SELECT 
                  (SELECT json_agg(vr) FROM visual_ranks vr) as results_v,
                  (SELECT json_agg(tr) FROM text_ranks tr) as results_t,
                  (SELECT json_agg(fr) FROM fts_ranks fr) as results_fts,
                  (SELECT json_build_object(
                      'id', v.id, 'segment_index', v.segment_index, 'start_time', v.start_time, 
                      'end_time', v.end_time, 'video_name', v.video_name, 'description', v.description, 'url', v.url,
                      'score', m.rrf_score
                   ) FROM video_scenes_v4 v JOIN merged_scores m USING(id)) as best_item;
              """

              keywords = q.split()
              lk_array = [f"%{k}%" for k in keywords]

              row = await conn.fetchrow(single_sql, q_v_str, q_t_str, q, lk_array)

         # 3. Process CTE Results Node creations
         if not row or not row['best_item']:
              return {"items": []}

         # Parse JSON outcomes Node creations
         import json
         # asyncpg might return strings or parsed objects depending on types setup node Creations
         def parse_json(val):
             if isinstance(val, str): return json.loads(val)
             return val if val else []

         results_v = parse_json(row['results_v'])
         results_t = parse_json(row['results_t'])
         results_fts = parse_json(row['results_fts'])
         best_item_raw = parse_json(row['best_item'])

         items = []
         if best_item_raw:
              items.append({
                  "video_name": best_item_raw['video_name'],
                  "segment_index": int(best_item_raw['segment_index']),
                  "start_time": float(best_item_raw['start_time']),
                  "end_time": float(best_item_raw['end_time']),
                  "score": float(best_item_raw['score']),
                  "description": best_item_raw.get("description", ""),
                  "url": best_item_raw.get("url", "")
              })

         diagnostics = {
              'results_v': [
                   {'segment_index': int(r['segment_index']), 'video_name': r.get('video_name',''), 'description': r.get('description','No description')[:80]} for r in results_v
              ] if results_v else [],
              'results_t': [
                   {'segment_index': int(r['segment_index']), 'video_name': r.get('video_name',''), 'description': r.get('description','No description')[:80]} for r in results_t
              ] if results_t else [],
              'results_fts': [
                   {'segment_index': int(r['segment_index']), 'video_name': r.get('video_name',''), 'description': r.get('description','No description')[:80]} for r in results_fts
              ] if results_fts else []
         }
         return {'query': q, 'results': items, 'diagnostics': diagnostics}

    except Exception as e:
         print(f"Search API Error: {repr(e)}")
         raise HTTPException(status_code=500, detail=repr(e))
